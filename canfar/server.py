"""Server selection and discovery seam for CANFAR."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import TYPE_CHECKING, Literal

from pydantic import AnyHttpUrl, AnyUrl

from canfar import get_logger
from canfar.config.selection import (
    get_active_server,
    get_remembered_server_for_idp,
    set_active_selection,
    upsert_server,
    with_active_selection,
)
from canfar.errors import ErrorCode, StructuredError
from canfar.idp import registry_sources
from canfar.models.config import Configuration
from canfar.models.http import Server
from canfar.models.registry import IVOARegistrySearch
from canfar.utils.discover import Discover

log = get_logger(__name__)

if TYPE_CHECKING:
    from canfar.models.registry import Server as DiscoveredServer


class ServerSelectorError(ValueError):
    """Raised when a server selector is ambiguous or not found."""

    def __init__(self, message: str, *, hint: str | None = None) -> None:
        super().__init__(message)
        self.hint = hint


class ServerDiscoveryError(RuntimeError):
    """Raised when server discovery fails for an Identity Provider."""

    def __init__(
        self,
        message: str,
        *,
        code: ErrorCode = ErrorCode.SERVER_DISCOVERY_FAILED,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.structured = StructuredError(code=code, message=message)


class ServerFetchError(RuntimeError):
    """Raised when server fetch or validation fails."""

    def __init__(
        self,
        message: str,
        *,
        code: ErrorCode = ErrorCode.TRANSPORT_FAILURE,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.structured = StructuredError(code=code, message=message)


class ServerSelectionRequiredError(RuntimeError):
    """Raised when activation needs the caller to choose a server."""

    def __init__(self, idp: str, servers: list[Server]) -> None:
        super().__init__(f"Select a server for IDP '{idp}'.")
        self.idp = idp
        self.servers = servers


@dataclass(frozen=True)
class ServerActivation:
    """Result from activating an Authentication and Server pair."""

    server: Server
    reason: Literal["active", "remembered", "single", "selected"]


def discover(
    idp: str,
    *,
    config: Configuration | None = None,
    dev: bool = False,
    timeout: int = 2,
    save: bool = True,
) -> list[Server]:
    """Discover, merge, and optionally persist servers for ``idp``.

    Args:
        idp: Canonical Identity Provider key.
        config: Configuration to update in place. Defaults to loading config.
        dev: Include development registries and endpoints during discovery.
        timeout: HTTP timeout in seconds for discovery requests.
        save: Persist the configuration after merging discovered servers.

    Returns:
        list[Server]: Newly discovered server records.

    Raises:
        ServerDiscoveryError: If discovery fails or finds no usable servers.
    """
    target_config = config or Configuration()
    discovered = asyncio.run(_discover_for_idp(idp, dev=dev, timeout=timeout))
    if not discovered:
        msg = f"No servers discovered for IDP '{idp}'."
        raise ServerDiscoveryError(
            msg,
            code=ErrorCode.SERVER_NONE_AVAILABLE,
        )
    for server in discovered:
        upsert_server(target_config, server)
    if save:
        target_config.save()
    return discovered


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
    target_config = config or Configuration()
    reason: Literal["active", "remembered", "single", "selected"]
    if selector is None:
        active_server = _active_server_for_idp(target_config, idp)
        if active_server is not None:
            set_active_selection(target_config, idp, active_server)
            target_config.save()
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
        if remembered is not None and remembered.uri is not None:
            selector = str(remembered.uri)
            reason = "remembered"
        elif len(servers) == 1 and servers[0].uri is not None:
            selector = str(servers[0].uri)
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
        timeout=timeout,
    )
    set_active_selection(target_config, idp, validated)
    target_config.save()
    return ServerActivation(server=validated, reason=reason)


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
    config = Configuration()
    active_idp = config.active.authentication
    servers = [server for server in config.server if server.idp == active_idp]
    if servers or not discover_if_empty:
        return servers

    discover(active_idp, config=config, dev=dev, timeout=timeout, save=False)
    config.save()
    return [server for server in config.server if server.idp == active_idp]


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
    config = Configuration()
    activate(
        config.active.authentication,
        selector,
        config=config,
        dev=dev,
        timeout=timeout,
    )


def _servers_for_idp(config: Configuration, idp: str) -> list[Server]:
    """Return saved servers belonging to ``idp``."""
    return [server for server in config.server if server.idp == idp]


def _active_server_for_idp(config: Configuration, idp: str) -> Server | None:
    if config.active.server is None:
        return None
    try:
        active_server = get_active_server(config)
    except KeyError:
        return None
    if active_server.idp != idp:
        return None
    return active_server


def _remembered_server_for_idp(
    config: Configuration,
    idp: str,
    servers: list[Server],
) -> Server | None:
    remembered = get_remembered_server_for_idp(config, idp)
    if remembered is None or remembered.uri is None:
        return None
    if not any(
        server.uri is not None and str(server.uri) == str(remembered.uri)
        for server in servers
    ):
        return None
    return remembered


def _resolve_selector(
    config: Configuration,
    selector: str,
    idp: str,
) -> Server | None:
    """Resolve a selector to a saved server for ``idp``.

    Args:
        config: Loaded configuration.
        selector: Server name or URI.
        idp: Canonical IDP key.

    Returns:
        Matching server record, or ``None`` when not found.

    Raises:
        ServerSelectorError: When ``selector`` matches multiple servers by name.
    """
    servers = _servers_for_idp(config, idp)
    uri_matches = [
        server
        for server in servers
        if server.uri is not None and str(server.uri) == selector
    ]
    if uri_matches:
        return uri_matches[0]

    name_matches = [
        server
        for server in servers
        if server.name is not None and server.name == selector
    ]
    if len(name_matches) == 1:
        return name_matches[0]
    if len(name_matches) > 1:
        uris = ", ".join(str(server.uri) for server in name_matches if server.uri)
        msg = f"Ambiguous server name '{selector}' for IDP '{idp}'."
        raise ServerSelectorError(
            msg,
            hint=f"Use a server URI. Matches: {uris}",
        )
    return None


async def _discover_for_idp(
    idp: str,
    *,
    dev: bool = False,
    timeout: int = 2,
) -> list[Server]:
    """Discover active servers for a single Identity Provider.

    Args:
        idp: Canonical IDP key.
        dev: Include development registries and endpoints.
        timeout: HTTP timeout in seconds for discovery requests.

    Returns:
        list[Server]: Validated HTTP server models for reachable endpoints.

    Raises:
        ServerDiscoveryError: If registry retrieval fails.
    """
    sources = registry_sources(idp, include_dev=dev)
    search = IVOARegistrySearch(registries=sources)
    async with Discover(search, timeout=timeout) as discovery:
        registries = await asyncio.gather(
            *(discovery.fetch(url, name) for url, name in sources.items())
        )
        successful_registries = [
            registry for registry in registries if registry.success
        ]
        if not successful_registries:
            errors = "; ".join(
                f"{registry.name}: {registry.error}" for registry in registries
            )
            msg = f"Failed to discover servers for IDP '{idp}': {errors}"
            raise ServerDiscoveryError(msg)

        endpoints = []
        for registry in successful_registries:
            endpoints.extend(await discovery.extract(registry, dev=dev))
        if not endpoints:
            return []

        checked = await asyncio.gather(
            *(discovery.check(endpoint) for endpoint in endpoints)
        )
        return [
            _discovered_to_server(endpoint, idp, timeout=timeout)
            for endpoint in checked
            if endpoint.status == 200
        ]


def _discovered_to_server(
    endpoint: DiscoveredServer,
    idp: str,
    *,
    timeout: int = 2,
) -> Server:
    """Convert a registry discovery record to a persisted HTTP server model.

    Args:
        endpoint: Discovered registry endpoint.
        idp: Canonical IDP key.
        timeout: HTTP timeout in seconds for VOSI capabilities requests.

    Returns:
        Server: Persisted server model with capabilities metadata when available.
    """
    server = Server(
        idp=idp,
        name=endpoint.name,
        uri=AnyUrl(endpoint.uri),
        url=AnyHttpUrl(endpoint.url),
    )
    return _enrich_from_capabilities(server, strict=False, timeout=timeout)


def _enrich_from_capabilities(
    server: Server,
    *,
    strict: bool = True,
    timeout: int = 2,
) -> Server:
    """Populate version and auth modes from VOSI capabilities when missing.

    Args:
        server: Server record to enrich.
        strict: When ``False``, return the original server if capabilities
            cannot be retrieved or parsed. Discovery uses non-strict mode so
            one malformed endpoint does not abort listing for an IDP.
        timeout: HTTP timeout in seconds for VOSI capabilities requests.

    Returns:
        Server: Copy with version and auth modes populated when discoverable.

    Raises:
        ServerFetchError: If ``strict`` is ``True`` and capabilities cannot
            be retrieved, parsed, or contain no session capabilities.
    """
    if server.url is None:
        msg = "Server URL is required to inspect capabilities."
        raise ServerFetchError(msg)

    if server.version and server.auths:
        return server.model_copy(deep=True)

    try:
        capabilities = server.capabilities(timeout=timeout)
    except Exception as exc:
        if strict:
            msg = f"Failed to fetch capabilities for {server.url}: {exc}"
            raise ServerFetchError(msg) from exc
        log.debug(
            "Skipping capability enrichment for %s during discovery: %s",
            server.url,
            exc,
        )
        return server.model_copy(deep=True)

    if not capabilities:
        if strict:
            msg = f"No session capabilities found for {server.url}."
            raise ServerFetchError(msg)
        log.debug(
            "No session capabilities found for %s during discovery; "
            "keeping registry metadata only.",
            server.url,
        )
        return server.model_copy(deep=True)

    primary = capabilities[0]
    return server.model_copy(
        update={
            "version": server.version or primary.get("version"),
            "auths": server.auths or primary.get("auth_modes"),
        },
        deep=True,
    )


def _validate_server(
    server: Server,
    *,
    config: Configuration | None = None,
    idp: str | None = None,
    timeout: int = 2,
) -> Server:
    """Fetch and validate a server before persisting it as active.

    Args:
        server: Candidate server record.
        config: Configuration to use while validating the candidate selection.
        idp: Authentication IDP to pair with the candidate server.
        timeout: HTTP timeout in seconds for validation requests.

    Returns:
        Server: Enriched, validated server model.

    Raises:
        ServerFetchError: If capability enrichment fails or URL/version are missing.
    """
    enriched = _enrich_from_capabilities(server, strict=True, timeout=timeout)
    if enriched.url is None or enriched.version is None:
        msg = "Server URL and version are required before activation."
        raise ServerFetchError(msg)

    base_config = config or Configuration()
    active_idp = idp or enriched.idp or base_config.active.authentication
    validation_config = with_active_selection(base_config, active_idp, enriched)
    return enriched.fetch(timeout=timeout, config=validation_config)
