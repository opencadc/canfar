"""Explicit access to configured VOSpace Services and the local filesystem."""

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import TYPE_CHECKING

from fsspec.asyn import get_loop, sync
from fsspec.implementations.asyn_wrapper import AsyncFileSystemWrapper
from fsspec.implementations.local import LocalFileSystem

from canfar.client import HTTPClient
from canfar.exceptions.context import AuthContextError
from canfar.models.config import Configuration
from canfar.models.http import LOCAL

if TYPE_CHECKING:
    from collections.abc import AsyncIterator
    from pathlib import Path

    from fsspec.spec import AbstractFileSystem
    from fsspec_cli import AsyncFilesystemSource
    from pydantic import SecretStr
    from vosfs import VOSpaceFileSystem

    from canfar.models.auth import RuntimeCredential
    from canfar.models.http import Server, VOSpaceService

__all__ = ["filesystem", "identifiers"]

_LISTINGS_EXPIRY_SECONDS = 30
"""Seconds a cached directory listing stays valid on one filesystem."""

_LISTINGS_MAX_PATHS = 1000
"""Maximum directory listings retained by one filesystem."""


def _configured(
    config: Configuration,
) -> dict[str, tuple[Server, VOSpaceService]]:
    """Return the private Storage Identifier to service mapping."""
    return {
        identifier: (server, service)
        for server in config.servers.values()
        for identifier, service in server.storage.items()
    }


def _service(config: Configuration, identifier: str) -> tuple[str, str]:
    """Return a service endpoint and its parent server's IDP."""
    try:
        server, service = _configured(config)[identifier]
    except KeyError:
        msg = f"Storage Identifier '{identifier}' is not configured."
        raise KeyError(msg) from None
    if server.idp is None:
        msg = (
            f"Storage Identifier '{identifier}' belongs to a Science Platform "
            "Server without an IDP."
        )
        raise ValueError(msg)
    return str(service.url), server.idp


async def _resolve(
    identifier: str,
    token: str | SecretStr | None = None,
    certificate: Path | str | None = None,
) -> tuple[str, RuntimeCredential]:
    """Resolve one Storage Identifier to its endpoint and a usable credential.

    Args:
        identifier: Storage Identifier of the configured VOSpace Service.
        token: Runtime bearer token, preferred over any saved credential.
        certificate: Runtime X.509 certificate path.

    Returns:
        tuple[str, RuntimeCredential]: The endpoint and its credential.

    Raises:
        AuthContextError: If the credential cannot be materialized.
    """
    config = Configuration()  # ty: ignore[missing-argument]
    endpoint, idp = _service(config, identifier)
    try:
        client = HTTPClient.build(
            config=config,
            authentication_idp=idp,
            url=endpoint,
            token=token,
            certificate=certificate,
        )
        credential = await client._materialize_credentials()  # noqa: SLF001
    except (KeyError, OSError, TypeError, ValueError):
        reason = "Credential cannot be used. Run 'canfar login' for this IDP."
        raise AuthContextError(idp, reason) from None
    return endpoint, credential


def _build(
    endpoint: str,
    credential: RuntimeCredential,
    *,
    asynchronous: bool,
) -> VOSpaceFileSystem:
    """Construct one VOSpace filesystem for an endpoint and credential.

    Args:
        endpoint: URL of the VOSpace Service.
        credential: Materialized token or certificate for that Service.
        asynchronous: Build the filesystem in fsspec's asynchronous mode.

    Returns:
        VOSpaceFileSystem: A ready, authenticated VOSpace filesystem.
    """
    from vosfs import VOSpaceFileSystem as _VOSpaceFileSystem  # noqa: PLC0415

    # Passed explicitly rather than unpacked so the credential kwarg stays typed.
    if credential.token is not None:
        return _VOSpaceFileSystem(
            endpoint,
            token=credential.token,
            asynchronous=asynchronous,
            skip_instance_cache=True,
            use_listings_cache=True,
            listings_expiry_time=_LISTINGS_EXPIRY_SECONDS,
            max_paths=_LISTINGS_MAX_PATHS,
        )
    return _VOSpaceFileSystem(
        endpoint,
        certfile=credential.certificate,
        asynchronous=asynchronous,
        skip_instance_cache=True,
        use_listings_cache=True,
        listings_expiry_time=_LISTINGS_EXPIRY_SECONDS,
        max_paths=_LISTINGS_MAX_PATHS,
    )


def _vospace(
    identifier: str,
    *,
    token: str | SecretStr | None = None,
    certificate: Path | str | None = None,
) -> AsyncFilesystemSource:
    """Return a fresh authenticated async filesystem source.

    Args:
        identifier: Storage Identifier of the configured VOSpace Service.
        token: Runtime bearer token, preferred over any saved credential.
        certificate: Runtime X.509 certificate path.

    Returns:
        AsyncFilesystemSource: Factory yielding one authenticated filesystem.
    """

    @asynccontextmanager
    async def source() -> AsyncIterator[AbstractFileSystem]:
        endpoint, credential = await _resolve(identifier, token, certificate)
        filesystem = _build(endpoint, credential, asynchronous=True)
        try:
            yield filesystem
        finally:
            await filesystem.aclose()

    return source


@asynccontextmanager
async def _local() -> AsyncIterator[AbstractFileSystem]:
    """Yield a fresh asynchronous wrapper around the local filesystem.

    Yields:
        AbstractFileSystem: An async-wrapped local filesystem.
    """
    yield AsyncFileSystemWrapper(
        LocalFileSystem(skip_instance_cache=True),
        asynchronous=True,
    )


def _sources() -> dict[str, AsyncFilesystemSource]:
    """Build the mapped storage sources for one data command invocation.

    Every configured VOSpace Service is mapped by its Storage Identifier, plus
    the always-available ``local`` filesystem.

    Returns:
        dict[str, AsyncFilesystemSource]: Sources keyed by Storage Identifier.
    """
    config = Configuration()  # ty: ignore[missing-argument]
    mapped: dict[str, AsyncFilesystemSource] = {
        identifier: _vospace(identifier)
        for identifier in _configured(config)
    }
    mapped[LOCAL] = _local
    return mapped


def identifiers() -> list[str]:
    """Return every Storage Identifier this configuration can address.

    Returns:
        list[str]: Configured Storage Identifiers plus the reserved ``local``.
    """
    config = Configuration()  # ty: ignore[missing-argument]
    return [*sorted(_configured(config)), LOCAL]


def filesystem(
    identifier: str,
    *,
    token: str | SecretStr | None = None,
    certificate: Path | str | None = None,
) -> AbstractFileSystem:
    """Return a synchronous filesystem for one Storage Identifier.

    Args:
        identifier: Storage Identifier, or ``local`` for the running machine.
        token: Runtime bearer token, preferred over any saved credential.
        certificate: Runtime X.509 certificate path.

    Returns:
        AbstractFileSystem: A ready, authenticated filesystem.

    Raises:
        KeyError: If ``identifier`` is not configured.
        AuthContextError: If the saved credential cannot be used.
    """
    if identifier == LOCAL:
        return LocalFileSystem(skip_instance_cache=True)
    # fsspec's background loop, so this works inside a running loop too.
    endpoint, credential = sync(get_loop(), _resolve, identifier, token, certificate)
    return _build(endpoint, credential, asynchronous=False)
