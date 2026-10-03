"""Registry evidence acquisition and discovery-worker preparation."""

from __future__ import annotations

import asyncio
import logging
from contextlib import asynccontextmanager
from functools import partial
from pathlib import Path
from typing import TYPE_CHECKING

from pydantic import AnyHttpUrl, BaseModel, ConfigDict

from canfar.auth.x509 import CertificateError
from canfar.exceptions.context import AuthContextError, AuthExpiredError
from canfar.idp import get_idp, registry_sources
from canfar.models.config import Configuration
from canfar.models.registry import (
    Server as RegistryResource,  # noqa: TC001 - Pydantic resolves field annotations at runtime
)
from canfar.utils import discover

if TYPE_CHECKING:
    from collections.abc import AsyncIterator, Awaitable, Callable

log = logging.getLogger(__name__)


class RegistryEvidenceError(RuntimeError):
    """Raised when strict registry evidence is missing or ambiguous."""


class RegistryEvidence(BaseModel):
    """Registry resources plus acquisition outcome for one IDP inspection.

    Attributes:
        leaf: Preferred primary VOSpace registry URI leaf.
        resources: Registry resources extracted from every successful registry.
        errors: Human-readable failures keyed by registry name.
        available: Whether at least one registry responded successfully.
    """

    model_config = ConfigDict(frozen=True)

    leaf: str | None
    resources: tuple[RegistryResource, ...]
    errors: tuple[str, ...]
    available: bool


class Workers(BaseModel):
    """Isolated worker configs with one pre-materialized runtime credential.

    Attributes:
        configs: One isolated Configuration per concurrent worker.
        token: Materialized bearer token, when the credential provides one.
        certificate: Materialized X.509 certificate path, when applicable.
    """

    model_config = ConfigDict(frozen=True)

    configs: tuple[Configuration, ...]
    token: str | None = None
    certificate: Path | None = None


async def evidence(
    idp: str,
    *,
    dev: bool,
    timeout: int,
) -> RegistryEvidence:
    """Acquire and extract registry records through one shared pipeline.

    Args:
        idp: Canonical Identity Provider key.
        dev: Include development registries and endpoints during discovery.
        timeout: HTTP timeout in seconds for registry requests.

    Returns:
        RegistryEvidence: Extracted resources plus the acquisition outcome.
    """
    idp_info = get_idp(idp)
    sources = registry_sources(idp, include_dev=dev)
    development_sources = set(idp_info.dev_registries)
    async with discover.client(timeout) as http:
        registries = await asyncio.gather(
            *(
                discover.fetch(
                    http,
                    url,
                    name,
                    development=url in development_sources,
                )
                for url, name in sources.items()
            )
        )
    successful = [registry for registry in registries if registry.success]
    resources = [
        resource
        for registry in successful
        for resource in discover.extract(registry, leaf=idp_info.leaf, dev=dev)
    ]

    return RegistryEvidence(
        leaf=idp_info.leaf,
        resources=tuple(resources),
        errors=tuple(
            f"{registry.name}: {registry.error}"
            for registry in registries
            if not registry.success
        ),
        available=bool(successful),
    )


@asynccontextmanager
async def reachability(
    timeout: int,
) -> AsyncIterator[Callable[[RegistryResource], Awaitable[RegistryResource]]]:
    """Open one HTTP client that checks Science Platform reachability.

    Args:
        timeout: HTTP timeout in seconds for each check.

    Yields:
        A check that sends ``HEAD`` to a record's URL and records the HTTP
        ``status``, or the ``failure`` (``timeout`` or ``unreachable``) when no
        response arrives.
    """
    async with discover.client(timeout) as http:
        yield partial(discover.check, http)


def select_storage(
    endpoint: RegistryResource,
    resources: list[RegistryResource],
    *,
    strict: bool,
) -> RegistryResource | None:
    """Pair an endpoint with one unambiguous same-environment VOSpace record.

    Args:
        endpoint: Science Platform registry record to pair.
        resources: Candidate VOSpace registry records.
        strict: Raise instead of logging when the pairing is ambiguous.

    Returns:
        RegistryResource | None: The single paired record, or None.

    Raises:
        RegistryEvidenceError: If ``strict`` and the pairing is ambiguous.
    """
    namespace = endpoint.uri.rpartition("/")[0]
    candidates = [
        resource
        for resource in resources
        if resource.uri.rpartition("/")[0] == namespace
        and resource.development == endpoint.development
    ]
    same_registry = [
        resource for resource in candidates if resource.registry == endpoint.registry
    ]
    preferred = same_registry or candidates
    if len(preferred) == 1:
        return preferred[0]
    if len(preferred) > 1:
        message = (
            "Multiple preferred VOSpace registry records found for Science "
            f"Platform Server '{endpoint.name or endpoint.uri}' in namespace "
            f"'{namespace}'."
        )
        if strict:
            raise RegistryEvidenceError(message)
        log.debug("%s Omitting generated storage configuration.", message)
    return None


async def discover_storage(
    uri: str | None,
    url: str | None,
    name: str | None,
    idp: str,
    *,
    dev: bool,
    timeout: int,
) -> RegistryResource | None:
    """Return fresh registry evidence for a Server's primary VOSpace Service.

    Args:
        uri: IVOA URI of the Science Platform Server.
        url: URL of the Science Platform Server, used to disambiguate.
        name: Server Name, used only for diagnostics.
        idp: Canonical Identity Provider key.
        dev: Include development registries and endpoints during discovery.
        timeout: HTTP timeout in seconds for registry requests.

    Returns:
        RegistryResource | None: The paired VOSpace record, or None.

    Raises:
        RegistryEvidenceError: If the URI is missing, the registry is
            unavailable, or the Server record is missing or ambiguous.
    """
    if uri is None:
        message = "Server URI is required to inspect its VOSpace Service."
        raise RegistryEvidenceError(message)

    found = await evidence(idp, dev=dev, timeout=timeout)
    if not found.available:
        errors = "; ".join(found.errors)
        message = (
            f"Failed to inspect VOSpace registry records for IDP '{idp}': {errors}"
        )
        raise RegistryEvidenceError(message)

    endpoints = [
        resource
        for resource in found.resources
        if resource.uri == uri and resource.uri.endswith("/skaha")
    ]
    matching_urls = [
        endpoint for endpoint in endpoints if url is not None and endpoint.url == url
    ]
    if len(matching_urls) == 1:
        endpoint = matching_urls[0]
    elif len(endpoints) == 1:
        endpoint = endpoints[0]
    elif not endpoints:
        message = (
            f"No Science Platform registry record found for Server '{name}' "
            f"with URI '{uri}'."
        )
        raise RegistryEvidenceError(message)
    else:
        message = (
            f"Multiple Science Platform registry records found for Server "
            f"'{name}' with URI '{uri}'."
        )
        raise RegistryEvidenceError(message)

    storage_resources = [
        resource
        for resource in found.resources
        if resource.uri.endswith(f"/{found.leaf}")
    ]
    return select_storage(endpoint, storage_resources, strict=True)


async def workers(
    config: Configuration | None,
    idp: str,
    *,
    endpoint: RegistryResource,
    count: int,
) -> Workers | None:
    """Materialize credentials once, then isolate worker configuration state.

    Args:
        config: Configuration to derive workers from. Defaults to loading config.
        idp: Canonical Identity Provider key.
        endpoint: Science Platform registry record used to build the client.
        count: Number of isolated worker configurations to produce.

    Returns:
        Workers | None: Workers, or None when credentials are absent
        or unusable.
    """
    from canfar.client import HTTPClient  # noqa: PLC0415

    base_config = config or Configuration()  # ty: ignore[missing-argument]
    client = HTTPClient.build(
        config=base_config,
        authentication_idp=idp,
        url=AnyHttpUrl(endpoint.url),
    )
    token: str | None = None
    certificate: Path | None = None
    if client.uses_runtime_credentials or client.authentication_record is not None:
        try:
            credential = await client._materialize_credentials()  # noqa: SLF001
        except (
            KeyError,
            OSError,
            AuthContextError,
            AuthExpiredError,
            CertificateError,
            TypeError,
            ValueError,
        ) as exc:
            log.debug("Skipping capability enrichment for IDP %s: %s", idp, exc)
            return None
        token = credential.token
        certificate = (
            Path(credential.certificate) if credential.certificate is not None else None
        )

    values = base_config.model_dump(mode="python")
    configs = tuple(Configuration.model_validate(values) for _ in range(count))
    return Workers(configs=configs, token=token, certificate=certificate)
