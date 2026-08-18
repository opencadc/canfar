"""Server selection and discovery seam for CANFAR."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict

from canfar._server_discovery import (
    ServerDiscoveryError,  # noqa: F401
    ServerFetchError,  # noqa: F401
    _validate_server,
    discover,
    enrich,  # noqa: F401
)
from canfar.models.config import Configuration
from canfar.models.http import Server  # noqa: TC001


class ServerSelectorError(ValueError):
    """Raised when a server selector is ambiguous or not found."""

    def __init__(self, message: str, *, hint: str | None = None) -> None:
        super().__init__(message)
        self.hint = hint


class ServerSelectionRequiredError(RuntimeError):
    """Raised when activation needs the caller to choose a server."""

    def __init__(self, idp: str, servers: list[Server]) -> None:
        super().__init__(f"Select a server for IDP '{idp}'.")
        self.idp = idp
        self.servers = servers


class ServerActivation(BaseModel):
    """Result from activating an Authentication and Server pair.

    Attributes:
        server: The activated Science Platform Server.
        reason: Why this Server was chosen.
    """

    model_config = ConfigDict(frozen=True)

    server: Server
    reason: Literal["active", "remembered", "single", "selected"]


def activate(
    idp: str,
    selector: str | None = None,
    *,
    config: Configuration | None = None,
    dev: bool = False,
    timeout: int = 2,
) -> ServerActivation:
    """Discover, validate, remember, and activate a server for ``idp``.

    When ``selector`` is omitted, activation reuses the active server if it
    already belongs to ``idp``, then the remembered server for ``idp``, then a
    single available server. Multiple choices raise ``ServerSelectionRequiredError``
    so the caller can prompt and retry with an explicit selector.

    Args:
        idp: Canonical Identity Provider key.
        selector: Optional server name, URI, or prompt choice.
        config: Configuration to update in place. Defaults to loading config.
        dev: Include development registries and endpoints during discovery.
        timeout: HTTP timeout in seconds for discovery and validation requests.

    Returns:
        ServerActivation: Activated server plus selection reason.

    Raises:
        ServerSelectionRequiredError: If multiple servers require user selection.
        ServerSelectorError: If an explicit selector is invalid.
        ServerDiscoveryError: If discovery fails before usable data is produced.
        ServerFetchError: If fetch or validation fails before save.
    """
    target_config = config or Configuration()  # ty: ignore[missing-argument]
    reason: Literal["active", "remembered", "single", "selected"]
    if selector is None:
        active_server = _active_server_for_idp(target_config, idp)
        if active_server is not None:
            _store_active_selection(target_config, idp, active_server)
            target_config.editor.save()
            return ServerActivation(server=active_server, reason="active")

        servers = _servers_for_idp(target_config, idp)
        if not servers:
            servers = discover(
                idp,
                config=target_config,
                dev=dev,
                timeout=timeout,
                save=False,
            )

        remembered = _remembered_server_for_idp(target_config, idp, servers)
        if remembered is not None and remembered.name is not None:
            selector = remembered.name
            reason = "remembered"
        elif len(servers) == 1 and servers[0].name is not None:
            selector = servers[0].name
            reason = "single"
        else:
            raise ServerSelectionRequiredError(idp, servers)
    else:
        reason = "selected"

    resolved = _resolve_selector(target_config, selector, idp)
    if resolved is None:
        discover(
            idp,
            config=target_config,
            dev=dev,
            timeout=timeout,
            save=False,
        )
        resolved = _resolve_selector(target_config, selector, idp)
    if resolved is None:
        msg = f"Server '{selector}' not found for IDP '{idp}'."
        raise ServerSelectorError(
            msg,
            hint="Use a server URI or run discovery with `canfar server ls`.",
        )

    validated = _validate_server(
        resolved,
        config=target_config,
        idp=idp,
        dev=dev,
        timeout=timeout,
    )
    _store_active_selection(target_config, idp, validated)
    target_config.editor.save()
    return ServerActivation(server=validated, reason=reason)


def activate_authentication(
    idp: str,
    *,
    config: Configuration | None = None,
) -> None:
    """Activate an Authentication Record and its remembered Server Selection."""
    target_config = config or Configuration()  # ty: ignore[missing-argument]
    if idp not in target_config.authentication:
        msg = f"Authentication record for IDP '{idp}' not found."
        raise KeyError(msg)
    servers = _servers_for_idp(target_config, idp)
    remembered = _remembered_server_for_idp(target_config, idp, servers)
    if remembered is not None:
        _store_active_selection(target_config, idp, remembered)
    else:
        active_server = _active_server_for_idp(target_config, idp)
        active = target_config.active.model_copy(
            update={
                "authentication": idp,
                "server": active_server.name if active_server is not None else None,
                "servers": _server_selection_history(target_config),
            },
        )
        target_config.editor.set("active", active)
    target_config.editor.save()


def list_servers(
    *,
    discover_if_empty: bool = True,
    dev: bool = False,
    timeout: int = 2,
) -> list[Server]:
    """Return known servers scoped to the active Identity Provider.

    When no servers are saved for the active IDP and ``discover_if_empty`` is
    ``True``, registry discovery runs once and discovered servers are persisted.

    Args:
        discover_if_empty: Whether to discover servers when none are saved.
        dev: Include development registries and endpoints during discovery.
        timeout: HTTP timeout in seconds for discovery requests.

    Returns:
        list[Server]: Saved server records for the active IDP.

    Raises:
        ServerDiscoveryError: If discovery fails before usable data is produced.
    """
    config = Configuration()  # ty: ignore[missing-argument]
    active_idp = config.active.authentication
    servers = [server for server in config.servers.values() if server.idp == active_idp]
    if servers or not discover_if_empty:
        return servers

    discover(active_idp, config=config, dev=dev, timeout=timeout, save=False)
    config.editor.save()
    return [server for server in config.servers.values() if server.idp == active_idp]


def use(selector: str, *, dev: bool = False, timeout: int = 2) -> None:
    """Select and persist the active server by name or URI.

    Resolves ``selector`` within servers for the active IDP. When no known
    server matches, discovery runs once for the active IDP before retrying.
    Fetches and validates server settings before saving; on failure the
    previous active server is left unchanged.

    Args:
        selector: Server display name or IVOA URI.
        dev: Include development registries and endpoints during discovery.
        timeout: HTTP timeout in seconds for discovery and validation requests.

    Raises:
        ServerSelectorError: If ``selector`` is ambiguous or still not found.
        ServerDiscoveryError: If discovery fails before usable data is produced.
        ServerFetchError: If fetch or validation fails before save.
    """
    config = Configuration()  # ty: ignore[missing-argument]
    activate(
        config.active.authentication,
        selector,
        config=config,
        dev=dev,
        timeout=timeout,
    )


def _servers_for_idp(config: Configuration, idp: str) -> list[Server]:
    """Return saved servers belonging to ``idp``."""
    return [server for server in config.servers.values() if server.idp == idp]


def _active_server_for_idp(config: Configuration, idp: str) -> Server | None:
    if config.active.server is None:
        return None
    active_server = config.servers.get(config.active.server)
    if active_server is None:
        return None
    if active_server.idp != idp:
        return None
    return active_server


def _remembered_server_for_idp(
    config: Configuration,
    idp: str,
    servers: list[Server],
) -> Server | None:
    name = _server_selection_history(config).get(idp)
    if name is None:
        return None
    remembered = config.servers.get(name)
    if remembered is None or remembered.idp != idp:
        return None
    if not any(server.name == name for server in servers):
        return None
    return remembered


def _server_selection_history(config: Configuration) -> dict[str, str]:
    """Return remembered Server Selections seeded by the active pair."""
    selections = dict(config.active.servers)
    active_name = config.active.server
    if active_name is None:
        return selections

    active_server = config.servers.get(active_name)
    if (
        active_server is not None
        and active_server.idp == config.active.authentication
        and active_server.name is not None
    ):
        selections[config.active.authentication] = active_server.name
    return selections


def _store_active_selection(
    config: Configuration,
    idp: str,
    server: Server,
) -> None:
    """Store a Server Selection and its history through the editor boundary."""
    if server.name is None:
        msg = "Server name is required for active selection."
        raise ValueError(msg)

    selected = server.model_copy(update={"idp": idp}, deep=True)
    servers = {**config.servers, server.name: selected}
    selections = _server_selection_history(config)
    selections[idp] = server.name
    active = config.active.model_copy(
        update={
            "authentication": idp,
            "server": server.name,
            "servers": selections,
        },
    )
    config.editor._set_top_level(  # noqa: SLF001
        servers=servers,
        active=active,
    )


def _resolve_selector(
    config: Configuration,
    selector: str,
    idp: str,
) -> Server | None:
    """Resolve a selector to a saved server for ``idp``.

    Server Name is the configuration identity, so name matches win; URI
    matching remains as a fallback. Names are unique dict keys, so a name
    selector can match at most one server.

    Args:
        config: Loaded configuration.
        selector: Server name or IVOA URI.
        idp: Canonical IDP key.

    Returns:
        Matching server record, or ``None`` when not found.
    """
    servers = _servers_for_idp(config, idp)
    for server in servers:
        if server.name == selector:
            return server
    for server in servers:
        if server.uri is not None and str(server.uri) == selector:
            return server
    return None
