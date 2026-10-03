"""Private registry, transport, and VOSI implementation for Server discovery."""

from __future__ import annotations

import asyncio
import logging
from typing import TYPE_CHECKING
from xml.etree.ElementTree import ParseError

from defusedxml.common import DefusedXmlException
from httpx2 import HTTPError, TimeoutException, TransportError
from pydantic import AnyHttpUrl, AnyUrl, ValidationError

from canfar.auth.x509 import CertificateError
from canfar.errors import ErrorCode
from canfar.exceptions.context import AuthContextError, AuthExpiredError
from canfar.hooks.httpx.auth import AuthenticationError as HTTPAuthenticationError
from canfar.idp import get_idp
from canfar.models.config import Configuration
from canfar.models.http import Server, ServerResources, VOSpaceService
from canfar.models.registry import ProbeStatus, ServerProbe
from canfar.models.registry import Server as RegistryResource
from canfar.utils import registry, vosi
from canfar.utils.registry import RegistryEvidenceError

if TYPE_CHECKING:
    from collections.abc import Awaitable, Callable
    from pathlib import Path

log = logging.getLogger(__name__)

_STORAGE_RESOURCE_UNSET = object()


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


class ServerFetchError(RuntimeError):
    """Raised when server fetch or validation fails."""

    code = ErrorCode.TRANSPORT_FAILURE


def _merge_storage(
    known: dict[str, VOSpaceService],
    found: dict[str, VOSpaceService],
) -> dict[str, VOSpaceService]:
    """Merge discovered VOSpace Services into known ones, keyed by IVOA URI.

    Discovery names a new Service after its Server Name, so an existing Service
    configured under its registry leaf (``arc``) is refreshed in place instead
    of being duplicated under the Server Name on every rediscovery.
    """
    merged = dict(known)
    names = {str(service.uri): name for name, service in known.items()}
    for name, service in found.items():
        merged[names.get(str(service.uri), name)] = service
    return merged


async def _discover_for_idp(
    idp: str,
    *,
    config: Configuration | None = None,
    dev: bool = False,
    timeout: int = 2,
    on_probe: Callable[[ServerProbe], None] | None = None,
) -> list[Server]:
    """Discover active servers for a single Identity Provider.

    Each Science Platform endpoint runs its reachability check and, when
    reachable, its inspection independently, so one slow endpoint does not
    hold back the others. ``on_probe`` receives each endpoint as ``pending``
    once the registries list it, then again with its outcome as soon as it is
    known.
    """

    def report(probe: ServerProbe) -> None:
        if probe.status not in {"pending", "connected"}:
            log.debug("Server %s %s: %s", probe.name, probe.status, probe.detail)
        if on_probe is not None:
            on_probe(probe)

    evidence = await registry.evidence(idp, dev=dev, timeout=timeout)
    if not evidence.available:
        errors = "; ".join(evidence.errors)
        msg = f"Failed to discover servers for IDP '{idp}': {errors}"
        raise ServerDiscoveryError(msg)

    platforms = [
        resource for resource in evidence.resources if resource.uri.endswith("/skaha")
    ]
    if not platforms:
        return []
    for platform in platforms:
        report(_probe(platform, "pending"))

    storage_resources = [
        resource
        for resource in evidence.resources
        if resource.uri.endswith(f"/{evidence.leaf}")
    ]
    workers = await registry.workers(
        config,
        idp,
        endpoint=platforms[0],
        count=len(platforms),
    )
    token = workers.token if workers is not None else None
    certificate = workers.certificate if workers is not None else None
    configs = workers.configs if workers is not None else (None,) * len(platforms)

    async def inspect(
        check: Callable[[RegistryResource], Awaitable[RegistryResource]],
        endpoint: RegistryResource,
        worker_config: Configuration | None,
    ) -> Server | None:
        endpoint = await check(endpoint)
        if endpoint.status != 200:
            report(_failed_probe(endpoint))
            return None
        if worker_config is None:
            report(
                _probe(
                    endpoint,
                    "error",
                    "No usable credentials to inspect session capabilities.",
                )
            )
            return _registry_resource_to_server(endpoint, idp)
        server, probe = await asyncio.to_thread(
            _discovered_to_server,
            endpoint,
            idp,
            config=worker_config,
            token=token,
            certificate=certificate,
            timeout=timeout,
            storage_resource=registry.select_storage(
                endpoint,
                storage_resources,
                strict=False,
            ),
        )
        report(probe)
        return server

    async with registry.reachability(timeout) as check:
        servers = await asyncio.gather(
            *(
                inspect(check, platform, worker_config)
                for platform, worker_config in zip(platforms, configs, strict=True)
            )
        )
    return [server for server in servers if server is not None]


def _endpoint_name(endpoint: RegistryResource) -> str:
    """Return the Server Name discovery gives an endpoint, or its URI."""
    if endpoint.name:
        return endpoint.name
    try:
        return _host_slug(AnyUrl(endpoint.uri)) or endpoint.uri
    except ValidationError:
        return endpoint.uri


def _probe(
    endpoint: RegistryResource,
    status: ProbeStatus,
    detail: str | None = None,
) -> ServerProbe:
    """Describe one endpoint's discovery outcome."""
    return ServerProbe(
        name=_endpoint_name(endpoint),
        uri=endpoint.uri,
        url=endpoint.url,
        status=status,
        detail=detail,
    )


def _failed_probe(endpoint: RegistryResource) -> ServerProbe:
    """Describe an endpoint whose reachability check did not return HTTP 200."""
    if endpoint.status is not None:
        return _probe(endpoint, "error", f"HTTP {endpoint.status} from {endpoint.url}")
    if endpoint.failure == "timeout":
        return _probe(endpoint, "timeout", f"{endpoint.url} did not respond in time")
    return _probe(endpoint, "unreachable", f"{endpoint.url} could not be reached")


def _probe_status(error: BaseException | None) -> ProbeStatus:
    """Classify why a Server's session capabilities could not be read."""
    if isinstance(error, TimeoutException):
        return "timeout"
    if isinstance(error, TransportError):
        return "unreachable"
    return "error"


def _host_slug(uri: AnyUrl) -> str | None:
    """Return a Server Name slug derived from a URI host (dots -> hyphens)."""
    if uri.host is None:
        return None
    return uri.host.replace(".", "-")


async def _discover_storage(
    server: Server,
    idp: str,
    *,
    dev: bool,
    timeout: int,
) -> RegistryResource | None:
    """Return fresh registry evidence for a server's primary VOSpace service."""
    try:
        return await registry.discover_storage(
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
) -> tuple[Server, ServerProbe]:
    """Inspect one reachable registry endpoint as a Science Platform Server.

    Storage and resource failures keep the Server usable. A session
    capabilities failure keeps registry metadata only and classifies the
    endpoint as timed out, unreachable, or in error.

    Returns:
        The Server to merge and its discovery outcome.
    """
    base_config = config or Configuration()  # ty: ignore[missing-argument]
    server = _enrich_storage(
        _registry_resource_to_server(endpoint, idp),
        storage_resource=storage_resource,
        config=base_config,
        authentication_idp=idp,
        token=token,
        certificate=certificate,
        strict=False,
        timeout=timeout,
    )
    try:
        server = enrich(
            server,
            config=base_config,
            authentication_idp=idp,
            token=token,
            certificate=certificate,
            timeout=timeout,
        )
    except ServerFetchError as exc:
        return server, _probe(endpoint, _probe_status(exc.__cause__), str(exc))
    server = _fetch_resources(
        server,
        config=base_config,
        authentication_idp=idp,
        token=token,
        certificate=certificate,
        timeout=timeout,
    )
    return server, _probe(endpoint, "connected")


def enrich(
    server: Server,
    *,
    config: Configuration | None = None,
    authentication_idp: str | None = None,
    token: str | None = None,
    certificate: Path | None = None,
    strict: bool = True,
    timeout: int = 2,
    storage_resource: RegistryResource | None | object = _STORAGE_RESOURCE_UNSET,  # noqa: RUF036
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
            be partial.
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
        HTTPError,
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
        leaf = get_idp(authentication_idp).leaf
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
            HTTPError,
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
    service = VOSpaceService.model_validate(
        {"uri": storage_resource.uri, "url": storage_resource.url}
    )

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

    with HTTPClient.build(
        config=config,
        authentication_idp=authentication_idp,
        url=url,
        token=token,
        certificate=certificate,
        timeout=timeout,
        raise_http_errors=False,
    ) as client:
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
    """Fetch and validate a server before persisting it as active."""
    base_config = config or Configuration()  # ty: ignore[missing-argument]
    active_idp = idp or server.idp or base_config.active.authentication
    storage_resource = _configured_storage_resource(server)
    if storage_resource is None:
        storage_resource = asyncio.run(
            _discover_storage(
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
    token: str | None = None,
    certificate: Path | None = None,
) -> Server:
    """Return a Server with resources read from its context endpoint.

    A failing or unrecognizable context endpoint keeps the Server's current
    resources, which stay ``None`` until a usable payload has been read.
    """
    from canfar.context import Context  # noqa: PLC0415

    if server.url is None or server.version is None:
        msg = "Server URL and version are required for resource enrichment."
        raise ValueError(msg)
    try:
        with Context.build(
            config=config,
            authentication_idp=authentication_idp,
            url=AnyHttpUrl(f"{server.url}/{server.version}"),
            token=token,
            certificate=certificate,
            timeout=timeout,
            raise_http_errors=False,
        ) as context:
            # Do not send Container Registry credentials to every discovered Server.
            context.client.headers.pop("X-Skaha-Registry-Auth", None)
            resources = ServerResources.from_context(context.resources())
    except (
        HTTPError,
        OSError,
        ValueError,
        TypeError,
        AuthContextError,
        AuthExpiredError,
        HTTPAuthenticationError,
    ) as exc:
        log.debug("Keeping known resources for %s: %s", server.url, exc)
        return server
    return server.model_copy(update={"resources": resources}, deep=True)


def _store_discovered_servers(config: Configuration, servers: list[Server]) -> None:
    """Merge discovered Science Platform Servers through the editor boundary."""
    updated = dict(config.servers)
    for server in servers:
        if server.name is not None:
            updated[server.name] = server
    config.editor._set_top_level(servers=updated)  # noqa: SLF001


def discover(
    idp: str,
    *,
    config: Configuration | None = None,
    dev: bool = False,
    timeout: int = 2,
    save: bool = True,
    on_probe: Callable[[ServerProbe], None] | None = None,
) -> list[Server]:
    """Discover, merge, and optionally persist servers for ``idp``.

    Each connected Server also reads its session resource limits from its
    context endpoint.

    Args:
        idp: Canonical Identity Provider key.
        config: Configuration to update in place. Defaults to loading config.
        dev: Include development registries and endpoints during discovery.
        timeout: HTTP timeout in seconds for discovery requests.
        save: Persist the configuration after merging discovered servers.
        on_probe: Called with each Science Platform endpoint as ``pending``
            once the registries list it, then with its outcome (``connected``,
            ``timeout``, ``unreachable``, or ``error``) as soon as it is known.

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
            on_probe=on_probe,
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
                        update={
                            "storage": _merge_storage(known.storage, server.storage)
                        },
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
                updates["storage"] = _merge_storage(known.storage, server.storage)
            if server.resources is not None:
                updates["resources"] = server.resources
            merged_server = known.model_copy(update=updates, deep=True)
        canonical[name] = merged_server

    if not canonical:
        msg = f"No servers discovered for IDP '{idp}'."
        raise ServerDiscoveryError(msg, code=ErrorCode.SERVER_NONE_AVAILABLE)
    merged = [
        canonical[name]
        for name in sorted(canonical, key=lambda value: (value.casefold(), value))
    ]
    _store_discovered_servers(target_config, merged)
    if save:
        target_config.editor.save()
    return merged
