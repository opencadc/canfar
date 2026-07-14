"""Server selection and discovery seam for CANFAR."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import TYPE_CHECKING, Literal
from xml.etree.ElementTree import ParseError

import httpx
from defusedxml.common import DefusedXmlException
from pydantic import AnyHttpUrl, AnyUrl, ValidationError

from canfar import get_logger
from canfar.auth.x509 import CertificateError
from canfar.errors import ErrorCode, StructuredError
from canfar.exceptions.context import AuthContextError, AuthExpiredError
from canfar.hooks.httpx.auth import AuthenticationError as HTTPAuthenticationError
from canfar.idp import registry_sources
from canfar.models.config import Configuration
from canfar.models.http import (
    DEFAULT_SERVER_CORES,
    DEFAULT_SERVER_GPUS,
    DEFAULT_SERVER_RAM_GB,
    Server,
)
from canfar.models.registry import IVOARegistrySearch
from canfar.utils import vosi
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
    target_config = config or Configuration()  # ty: ignore[missing-argument]
    discovered = asyncio.run(
        _discover_for_idp(
            idp,
            config=target_config,
            dev=dev,
            timeout=timeout,
        )
    )
    known_servers = dict(target_config.servers)
    canonical: dict[str, Server] = {}
    for server in sorted(
        discovered,
        key=lambda item: (
            item.name is None,
            (item.name or "").casefold(),
            str(item.uri or ""),
            str(item.url or ""),
        ),
    ):
        name = server.name
        if name is None:
            continue
        known = canonical.get(name, known_servers.get(name))
        if server.version is None or not server.auths:
            if known is not None and known.version is not None and known.auths:
                canonical[name] = known
            continue
        merged_server = server
        if known is not None:
            updates = server.model_dump(
                include={"idp", "name", "uri", "url", "version", "auths"},
                exclude_none=True,
            )
            merged_server = known.model_copy(update=updates, deep=True)
        canonical[name] = merged_server

    if not canonical:
        msg = f"No servers discovered for IDP '{idp}'."
        raise ServerDiscoveryError(
            msg,
            code=ErrorCode.SERVER_NONE_AVAILABLE,
        )
    merged = [
        canonical[name]
        for name in sorted(canonical, key=lambda value: (value.casefold(), value))
    ]
    target_config.upsert_servers(merged)
    if save:
        target_config.save()
    return merged


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
            target_config.set_active_selection(idp, active_server)
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
    target_config.set_active_selection(idp, validated)
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
    config = Configuration()  # ty: ignore[missing-argument]
    active_idp = config.active.authentication
    servers = [server for server in config.servers.values() if server.idp == active_idp]
    if servers or not discover_if_empty:
        return servers

    discover(active_idp, config=config, dev=dev, timeout=timeout, save=False)
    config.save()
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
    try:
        active_server = config.get_active_server()
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
    remembered = config.get_remembered_server_for_idp(idp)
    if remembered is None or remembered.uri is None:
        return None
    if remembered.name is None:
        return None
    if not any(server.name == remembered.name for server in servers):
        return None
    return remembered


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


async def _discover_for_idp(
    idp: str,
    *,
    config: Configuration | None = None,
    dev: bool = False,
    timeout: int = 2,
) -> list[Server]:
    """Discover active servers for a single Identity Provider.

    Args:
        idp: Canonical IDP key.
        config: Configuration whose Authentication Record authorizes enrichment.
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
            endpoints.extend(discovery.extract(registry, dev=dev))
        if not endpoints:
            return []

        checked = await asyncio.gather(
            *(discovery.check(endpoint) for endpoint in endpoints)
        )
        return [
            _discovered_to_server(
                endpoint,
                idp,
                config=config,
                timeout=timeout,
            )
            for endpoint in checked
            if endpoint.status == 200
        ]


def _host_slug(uri: AnyUrl) -> str | None:
    """Return a Server Name slug derived from a URI host (dots -> hyphens)."""
    if uri.host is None:
        return None
    return uri.host.replace(".", "-")


def _discovered_to_server(
    endpoint: DiscoveredServer,
    idp: str,
    *,
    config: Configuration | None = None,
    timeout: int = 2,
) -> Server:
    """Convert a registry discovery record to a persisted HTTP server model.

    The registry-provided name wins as the Server Name; endpoints without a
    registry name are named by a slug of the URI host.

    Args:
        endpoint: Discovered registry endpoint.
        idp: Canonical IDP key.
        config: Configuration whose Authentication Record authorizes enrichment.
        timeout: HTTP timeout in seconds for VOSI capabilities requests.

    Returns:
        Server: Persisted server model with capabilities metadata when available.
    """
    uri = AnyUrl(endpoint.uri)
    server = Server(
        idp=idp,
        name=endpoint.name or _host_slug(uri),
        uri=uri,
        url=AnyHttpUrl(endpoint.url),
    )
    return enrich(
        server,
        config=config,
        strict=False,
        timeout=timeout,
    )


def enrich(
    server: Server,
    *,
    config: Configuration | None = None,
    authentication_idp: str | None = None,
    strict: bool = True,
    timeout: int = 2,
) -> Server:
    """Return a validated Server enriched from its VOSI capabilities.

    Args:
        server: Server record to enrich.
        config: Configuration whose Authentication Record should authorize the
            capability request. The transient selector does not change or persist
            Authentication or Server Selection.
        authentication_idp: Optional Authentication Record selector. Defaults to
            the Server IDP, then the active Authentication.
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

    base_config = config or Configuration()  # ty: ignore[missing-argument]
    active_idp = authentication_idp or server.idp or base_config.active.authentication
    try:
        from canfar.client import HTTPClient  # noqa: PLC0415

        with HTTPClient(
            config=base_config,
            authentication_idp=active_idp,
            url=server.url,
            timeout=timeout,
            raise_http_errors=False,
        ) as client:
            request_client = client.client
            request_client.headers["Accept"] = "application/xml"
            request_client.headers.pop("Content-Type", None)
            request_client.headers.pop("X-Skaha-Registry-Auth", None)
            response = request_client.get("capabilities")
            response.raise_for_status()
            capabilities = vosi.capabilities(xml=response.text)
    except (
        httpx.HTTPError,
        OSError,
        AuthContextError,
        AuthExpiredError,
        CertificateError,
        HTTPAuthenticationError,
        ParseError,
        DefusedXmlException,
    ) as exc:
        return _keep_or_raise(
            server,
            strict=strict,
            error=f"Failed to fetch capabilities for {server.url}: {exc}",
            cause=exc,
            debug="Skipping capability enrichment for %s during discovery: %s",
            args=(server.url, exc),
        )

    primary = next(
        (
            capability
            for capability in capabilities
            if capability.get("version") and capability.get("auth_modes")
        ),
        None,
    )
    if primary is None:
        return _keep_or_raise(
            server,
            strict=strict,
            error=f"No complete session capabilities found for {server.url}.",
            debug=(
                "No complete session capabilities found for %s during discovery; "
                "keeping registry metadata only."
            ),
            args=(server.url,),
        )

    try:
        return Server.model_validate(
            {
                **server.model_dump(mode="python"),
                "url": primary["baseurl"],
                "version": primary["version"],
                "auths": primary["auth_modes"],
            }
        )
    except ValidationError as exc:
        return _keep_or_raise(
            server,
            strict=strict,
            error=f"Invalid capabilities for {server.url}: {exc}",
            cause=exc,
            debug=(
                "Ignoring invalid capability enrichment for %s during discovery: %s"
            ),
            args=(server.url, exc),
        )


def _keep_or_raise(
    server: Server,
    *,
    strict: bool,
    error: str,
    debug: str,
    args: tuple[object, ...] = (),
    cause: BaseException | None = None,
) -> Server:
    """Raise on strict enrich failures; otherwise keep the original server."""
    if strict:
        raise ServerFetchError(error) from cause
    log.debug(debug, *args)
    return server.model_copy(deep=True)


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
    base_config = config or Configuration()  # ty: ignore[missing-argument]
    active_idp = idp or server.idp or base_config.active.authentication
    enriched = enrich(
        server,
        config=base_config,
        authentication_idp=active_idp,
        strict=True,
        timeout=timeout,
    )
    if enriched.url is None or enriched.version is None:
        msg = "Server URL and version are required before activation."
        raise ServerFetchError(msg)

    return _fetch_resources(
        enriched,
        timeout=timeout,
        config=base_config,
        authentication_idp=active_idp,
    )


def _fetch_resources(
    server: Server,
    *,
    config: Configuration,
    authentication_idp: str,
    timeout: int,
) -> Server:
    """Return a Server populated from its authenticated context endpoint."""
    from canfar.client import HTTPClient  # noqa: PLC0415

    if server.url is None or server.version is None:
        msg = "Server URL and version are required for resource enrichment."
        raise ValueError(msg)
    client = HTTPClient(
        config=config,
        authentication_idp=authentication_idp,
        url=AnyHttpUrl(f"{server.url}/{server.version}"),
        timeout=timeout,
        raise_http_errors=False,
    )
    try:
        with client:
            response = client.client.get("context")
            response.raise_for_status()
            data = dict(response.json())

        cores_data = data.get("cores") or {}
        ram_data = data.get("memoryGB") or {}
        gpus_data = data.get("gpus") or {}
        cores = cores_data.get("defaultLimit")
        ram = ram_data.get("defaultLimit")
        gpu_options = gpus_data.get("options") or []
        return Server.model_validate(
            {
                **server.model_dump(mode="python"),
                "cores": cores if cores is not None else DEFAULT_SERVER_CORES,
                "ram": ram if ram is not None else DEFAULT_SERVER_RAM_GB,
                "gpus": max(gpu_options) if gpu_options else DEFAULT_SERVER_GPUS,
            }
        )
    except (httpx.HTTPError, OSError, ValueError, TypeError):
        return server.model_copy(
            update={
                "cores": DEFAULT_SERVER_CORES,
                "ram": DEFAULT_SERVER_RAM_GB,
                "gpus": DEFAULT_SERVER_GPUS,
            },
            deep=True,
        )
