"""Private registry evidence and discovery-worker preparation."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from pathlib import Path

from pydantic import AnyHttpUrl

from canfar import get_logger
from canfar.auth.x509 import CertificateError
from canfar.exceptions.context import AuthContextError, AuthExpiredError
from canfar.idp import get_idp, registry_sources
from canfar.models.config import Configuration
from canfar.models.registry import IVOARegistrySearch
from canfar.models.registry import Server as RegistryResource
from canfar.utils.discover import Discover

log = get_logger(__name__)


class RegistryEvidenceError(RuntimeError):
    """Raised when strict registry evidence is missing or ambiguous."""


@dataclass(frozen=True)
class RegistryEvidence:
    """Registry resources plus acquisition outcome for one IDP inspection."""

    preferred_storage_leaf: str | None
    resources: tuple[RegistryResource, ...]
    errors: tuple[str, ...]
    available: bool


@dataclass(frozen=True)
class EnrichmentWorkers:
    """Isolated worker configs with one pre-materialized runtime credential."""

    configs: tuple[Configuration, ...]
    token: str | None = None
    certificate: Path | None = None


async def load_registry_evidence(
    idp: str,
    *,
    dev: bool,
    timeout: int,
    check_platforms: bool,
) -> RegistryEvidence:
    """Acquire and extract registry records through one shared pipeline."""
    idp_info = get_idp(idp)
    sources = registry_sources(idp, include_dev=dev)
    development_sources = set(idp_info.dev_registries)
    search = IVOARegistrySearch(
        registries=sources,
        preferred_storage_leaf=idp_info.preferred_storage_leaf,
    )
    async with Discover(search, timeout=timeout) as discovery:
        registries = await asyncio.gather(
            *(
                discovery.fetch(
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
            for resource in discovery.extract(registry, dev=dev)
        ]
        if check_platforms:
            endpoints = [
                resource for resource in resources if resource.uri.endswith("/skaha")
            ]
            await asyncio.gather(*(discovery.check(endpoint) for endpoint in endpoints))

    return RegistryEvidence(
        preferred_storage_leaf=idp_info.preferred_storage_leaf,
        resources=tuple(resources),
        errors=tuple(
            f"{registry.name}: {registry.error}"
            for registry in registries
            if not registry.success
        ),
        available=bool(successful),
    )


def _registry_namespace(uri: str) -> str:
    """Return the IVOA registry URI namespace before its resource leaf."""
    return uri.rpartition("/")[0]


def select_storage_resource(
    endpoint: RegistryResource,
    resources: list[RegistryResource],
    *,
    strict: bool,
) -> RegistryResource | None:
    """Pair an endpoint with one unambiguous same-environment VOSpace record."""
    candidates = [
        resource
        for resource in resources
        if _registry_namespace(resource.uri) == _registry_namespace(endpoint.uri)
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
            f"'{_registry_namespace(endpoint.uri)}'."
        )
        if strict:
            raise RegistryEvidenceError(message)
        log.debug("%s Omitting generated storage configuration.", message)
    return None


async def discover_storage_resource(
    server_uri: str | None,
    server_url: str | None,
    server_name: str | None,
    idp: str,
    *,
    dev: bool,
    timeout: int,
) -> RegistryResource | None:
    """Return fresh registry evidence for a server's primary VOSpace service."""
    if server_uri is None:
        message = "Server URI is required to inspect its VOSpace Service."
        raise RegistryEvidenceError(message)

    evidence = await load_registry_evidence(
        idp,
        dev=dev,
        timeout=timeout,
        check_platforms=False,
    )
    if not evidence.available:
        errors = "; ".join(evidence.errors)
        message = (
            f"Failed to inspect VOSpace registry records for IDP '{idp}': {errors}"
        )
        raise RegistryEvidenceError(message)

    endpoints = [
        resource
        for resource in evidence.resources
        if resource.uri == server_uri and resource.uri.endswith("/skaha")
    ]
    matching_urls = [
        endpoint
        for endpoint in endpoints
        if server_url is not None and endpoint.url == server_url
    ]
    if len(matching_urls) == 1:
        endpoint = matching_urls[0]
    elif len(endpoints) == 1:
        endpoint = endpoints[0]
    elif not endpoints:
        message = (
            f"No Science Platform registry record found for Server '{server_name}' "
            f"with URI '{server_uri}'."
        )
        raise RegistryEvidenceError(message)
    else:
        message = (
            f"Multiple Science Platform registry records found for Server "
            f"'{server_name}' with URI '{server_uri}'."
        )
        raise RegistryEvidenceError(message)

    storage_resources = [
        resource
        for resource in evidence.resources
        if resource.uri.endswith(f"/{evidence.preferred_storage_leaf}")
    ]
    return select_storage_resource(endpoint, storage_resources, strict=True)


async def prepare_enrichment_workers(
    config: Configuration | None,
    idp: str,
    *,
    endpoint: RegistryResource,
    count: int,
) -> EnrichmentWorkers | None:
    """Materialize credentials once, then isolate worker configuration state."""
    from canfar.client import HTTPClient  # noqa: PLC0415

    base_config = config or Configuration()
    client = HTTPClient(
        config=base_config,
        authentication_idp=idp,
        url=AnyHttpUrl(endpoint.url),
    )
    token: str | None = None
    certificate: Path | None = None
    if client.uses_runtime_credentials or client.authentication_record is not None:
        try:
            token, certfile = await client._materialize_credentials()  # noqa: SLF001
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
        certificate = Path(certfile) if certfile is not None else None

    values = base_config.model_dump(mode="python")
    configs = tuple(Configuration.model_validate(values) for _ in range(count))
    return EnrichmentWorkers(configs, token=token, certificate=certificate)
