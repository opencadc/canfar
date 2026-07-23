"""Server selection and discovery seam for CANFAR."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Literal
from xml.etree.ElementTree import ParseError

import httpx
from defusedxml.common import DefusedXmlException
from pydantic import AnyHttpUrl, AnyUrl, ValidationError

from canfar import get_logger
from canfar._discovery import (
    RegistryEvidenceError,
    discover_storage_resource,
    load_registry_evidence,
    prepare_enrichment_workers,
    select_storage_resource,
)
from canfar.auth.x509 import CertificateError
from canfar.errors import ErrorCode, StructuredError
from canfar.exceptions.context import AuthContextError, AuthExpiredError
from canfar.hooks.httpx.auth import AuthenticationError as HTTPAuthenticationError
from canfar.idp import get_idp
from canfar.models.config import Configuration
from canfar.models.http import (
    DEFAULT_SERVER_CORES,
    DEFAULT_SERVER_GPUS,
    DEFAULT_SERVER_RAM_GB,
    Server,
    VOSpaceService,
)
from canfar.models.registry import Server as RegistryResource
from canfar.utils import vosi

if TYPE_CHECKING:
    from pathlib import Path

log = get_logger(__name__)

_STORAGE_RESOURCE_UNSET = object()


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
                if server.storage:
                    known = known.model_copy(
                        update={"storage": {**known.storage, **server.storage}},
                        deep=True,
                    )
                canonical[name] = known
            continue
        merged_server = server
        if known is not None:
            updates = server.model_dump(
                include={"idp", "name", "uri", "url", "version", "auths"},
                exclude_none=True,
            )
            if server.storage:
                updates["storage"] = {**known.storage, **server.storage}
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
        dev=dev,
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
    evidence = await load_registry_evidence(
        idp,
        dev=dev,
        timeout=timeout,
        check_platforms=True,
    )
    if not evidence.available:
        errors = "; ".join(evidence.errors)
        msg = f"Failed to discover servers for IDP '{idp}': {errors}"
        raise ServerDiscoveryError(msg)

    endpoints = [
        resource
        for resource in evidence.resources
        if resource.uri.endswith("/skaha") and resource.status == 200
    ]
    if not endpoints:
        return []

    storage_resources = [
        resource
        for resource in evidence.resources
        if resource.uri.endswith(f"/{evidence.preferred_storage_leaf}")
    ]
    workers = await prepare_enrichment_workers(
        config,
        idp,
        endpoint=endpoints[0],
        count=len(endpoints),
    )
    if workers is None:
        return [_registry_resource_to_server(endpoint, idp) for endpoint in endpoints]

    return list(
        await asyncio.gather(
            *(
                asyncio.to_thread(
                    _discovered_to_server,
                    endpoint,
                    idp,
                    config=worker_config,
                    token=workers.token,
                    certificate=workers.certificate,
                    timeout=timeout,
                    storage_resource=_select_storage_resource(
                        endpoint,
                        storage_resources,
                        strict=False,
                    ),
                )
                for endpoint, worker_config in zip(
                    endpoints,
                    workers.configs,
                    strict=True,
                )
            )
        )
    )


def _host_slug(uri: AnyUrl) -> str | None:
    """Return a Server Name slug derived from a URI host (dots -> hyphens)."""
    if uri.host is None:
        return None
    return uri.host.replace(".", "-")


def _select_storage_resource(
    endpoint: RegistryResource,
    resources: list[RegistryResource],
    *,
    strict: bool,
) -> RegistryResource | None:
    """Map private registry ambiguity to the public server fetch error."""
    try:
        return select_storage_resource(endpoint, resources, strict=strict)
    except RegistryEvidenceError as exc:
        raise ServerFetchError(str(exc)) from exc


async def _discover_storage_resource(
    server: Server,
    idp: str,
    *,
    dev: bool,
    timeout: int,
) -> RegistryResource | None:
    """Return fresh registry evidence for a server's primary VOSpace service."""
    try:
        return await discover_storage_resource(
            str(server.uri) if server.uri is not None else None,
            str(server.url) if server.url is not None else None,
            server.name,
            idp,
            dev=dev,
            timeout=timeout,
        )
    except RegistryEvidenceError as exc:
        raise ServerFetchError(str(exc)) from exc


def _configured_storage_resource(server: Server) -> RegistryResource | None:
    """Convert the persisted primary VOSpace service to inspection evidence."""
    if server.name is None:
        return None
    service = server.storage.get(server.name)
    if service is None:
        return None
    return RegistryResource(
        registry="configuration",
        uri=str(service.uri),
        url=str(service.url),
    )


def _registry_resource_to_server(endpoint: RegistryResource, idp: str) -> Server:
    """Convert registry endpoint identity without performing capability I/O."""
    uri = AnyUrl(endpoint.uri)
    return Server(
        idp=idp,
        name=endpoint.name or _host_slug(uri),
        uri=uri,
        url=AnyHttpUrl(endpoint.url),
    )


def _discovered_to_server(
    endpoint: RegistryResource,
    idp: str,
    *,
    config: Configuration | None = None,
    token: str | None = None,
    certificate: Path | None = None,
    timeout: int = 2,
    storage_resource: RegistryResource | None = None,
) -> Server:
    """Convert a registry discovery record to a persisted HTTP server model.

    The registry-provided name wins as the Server Name; endpoints without a
    registry name are named by a slug of the URI host.

    Args:
        endpoint: Discovered registry endpoint.
        idp: Canonical IDP key.
        config: Configuration whose Authentication Record authorizes enrichment.
        token: Pre-materialized runtime bearer token for worker isolation.
        certificate: Pre-materialized runtime certificate for worker isolation.
        timeout: HTTP timeout in seconds for VOSI capabilities requests.
        storage_resource: Same-namespace preferred VOSpace registry record, if any.

    Returns:
        Server: Persisted server model with capabilities metadata when available.
    """
    server = _registry_resource_to_server(endpoint, idp)
    return enrich(
        server,
        config=config,
        token=token,
        certificate=certificate,
        strict=False,
        timeout=timeout,
        storage_resource=storage_resource,
    )


def enrich(
    server: Server,
    *,
    config: Configuration | None = None,
    authentication_idp: str | None = None,
    token: str | None = None,
    certificate: Path | None = None,
    strict: bool = True,
    timeout: int = 2,
    storage_resource: RegistryResource | None | object = _STORAGE_RESOURCE_UNSET,
) -> Server:
    """Return a validated Server enriched from its VOSI capabilities.

    Args:
        server: Server record to enrich.
        config: Configuration whose Authentication Record should authorize the
            capability request. The transient selector does not change or persist
            Authentication or Server Selection.
        authentication_idp: Optional Authentication Record selector. Defaults to
            the Server IDP, then the active Authentication.
        token: Optional runtime bearer token for capability requests.
        certificate: Optional runtime certificate for capability requests.
        strict: When ``False``, keep usable registry and existing storage data
            when session or storage capabilities cannot be retrieved or parsed.
            Other successful enrichment may still be returned, so the result can
            be partial. Discovery uses non-strict mode so one malformed endpoint
            does not abort listing for an IDP.
        timeout: HTTP timeout in seconds for VOSI capabilities requests.
        storage_resource: Retained same-namespace VOSpace registry record. Passing
            ``None`` records that the preferred resource was absent; omitting the
            argument leaves storage outside this inspection.

    Returns:
        Server: Copy with version and auth modes populated when discoverable.

    Raises:
        ServerFetchError: If ``strict`` is ``True`` and capabilities cannot
            be retrieved, parsed, or contain no session capabilities.
    """
    base_config = config or Configuration()  # ty: ignore[missing-argument]
    active_idp = authentication_idp or server.idp or base_config.active.authentication
    if storage_resource is not _STORAGE_RESOURCE_UNSET:
        server = _enrich_storage(
            server,
            storage_resource=(
                storage_resource
                if isinstance(storage_resource, RegistryResource)
                else None
            ),
            config=base_config,
            authentication_idp=active_idp,
            token=token,
            certificate=certificate,
            strict=strict,
            timeout=timeout,
        )
    if server.url is None:
        msg = "Server URL is required to inspect capabilities."
        raise ServerFetchError(msg)
    try:
        capabilities = vosi.capabilities(
            xml=_fetch_capabilities(
                server.url,
                config=base_config,
                authentication_idp=active_idp,
                token=token,
                certificate=certificate,
                timeout=timeout,
            )
        )
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


def _enrich_storage(
    server: Server,
    *,
    storage_resource: RegistryResource | None,
    config: Configuration,
    authentication_idp: str,
    token: str | None,
    certificate: Path | None,
    strict: bool,
    timeout: int,
) -> Server:
    """Validate and attach one retained primary VOSpace registry resource."""
    error: BaseException | None = None
    if storage_resource is None:
        leaf = get_idp(authentication_idp).preferred_storage_leaf
        subject = f"same-namespace '{leaf}' registry record"
        error = ValueError(
            f"No {subject} found for Science Platform Server '{server.name}'."
        )
    else:
        subject = storage_resource.uri
        try:
            xml = _fetch_capabilities(
                AnyHttpUrl(storage_resource.url),
                config=config,
                authentication_idp=authentication_idp,
                token=token,
                certificate=certificate,
                timeout=timeout,
            )
            valid = vosi.is_vospace_service(xml)
        except (
            httpx.HTTPError,
            OSError,
            AuthContextError,
            AuthExpiredError,
            CertificateError,
            HTTPAuthenticationError,
            ParseError,
            DefusedXmlException,
            ValueError,
        ) as exc:
            error = exc
        else:
            if not valid:
                error = ValueError(
                    "required VOSpace node capability is missing or malformed"
                )
            elif server.name is None:
                error = ValueError("Science Platform Server has no Server Name")

    if error is not None:
        message = (
            f"Failed to inspect VOSpace Service '{subject}' for Science "
            f"Platform Server '{server.name}': {error}"
        )
        return _keep_or_raise(
            server,
            strict=strict,
            error=message,
            cause=error,
            debug="Skipping VOSpace Service %s during discovery: %s",
            args=(subject, error),
        )
    assert storage_resource is not None
    assert server.name is not None
    service = VOSpaceService(uri=storage_resource.uri, url=storage_resource.url)

    return server.model_copy(
        update={"storage": {**server.storage, server.name: service}},
        deep=True,
    )


def _fetch_capabilities(
    url: AnyHttpUrl,
    *,
    config: Configuration,
    authentication_idp: str,
    token: str | None = None,
    certificate: Path | None = None,
    timeout: int,
) -> str:
    """Fetch one VOSI capabilities document through the existing HTTP seam."""
    from canfar.client import HTTPClient  # noqa: PLC0415

    client_kwargs: dict[str, Any] = {
        "config": config,
        "authentication_idp": authentication_idp,
        "url": url,
        "timeout": timeout,
        "raise_http_errors": False,
    }
    if token is not None:
        client_kwargs["token"] = token
    if certificate is not None:
        client_kwargs["certificate"] = certificate
    with HTTPClient(**client_kwargs) as client:
        request_client = client.client
        request_client.headers["Accept"] = "application/xml"
        request_client.headers.pop("Content-Type", None)
        request_client.headers.pop("X-Skaha-Registry-Auth", None)
        response = request_client.get("capabilities")
        response.raise_for_status()
        return response.text


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
    dev: bool = False,
    timeout: int = 2,
) -> Server:
    """Fetch and validate a server before persisting it as active.

    Args:
        server: Candidate server record.
        config: Configuration to use while validating the candidate selection.
        idp: Authentication IDP to pair with the candidate server.
        dev: Include development registry evidence during validation.
        timeout: HTTP timeout in seconds for validation requests.

    Returns:
        Server: Enriched, validated server model.

    Raises:
        ServerFetchError: If capability enrichment fails or URL/version are missing.
    """
    base_config = config or Configuration()  # ty: ignore[missing-argument]
    active_idp = idp or server.idp or base_config.active.authentication
    storage_resource = _configured_storage_resource(server)
    if storage_resource is None:
        storage_resource = asyncio.run(
            _discover_storage_resource(
                server,
                active_idp,
                dev=dev,
                timeout=timeout,
            )
        )
    enriched = enrich(
        server,
        config=base_config,
        authentication_idp=active_idp,
        strict=True,
        timeout=timeout,
        storage_resource=storage_resource,
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
