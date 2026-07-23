"""Private adapters for configured VOSpace Services."""

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import TYPE_CHECKING, Any

from canfar.client import HTTPClient
from canfar.exceptions.context import AuthContextError
from canfar.models.config import Configuration

if TYPE_CHECKING:
    from collections.abc import AsyncIterator
    from pathlib import Path

    from fsspec.spec import AbstractFileSystem
    from fsspec_cli import AsyncFilesystemSource
    from pydantic import SecretStr


def _vospace_source(
    storage_name: str,
    *,
    token: str | SecretStr | None = None,
    certificate: Path | None = None,
) -> AsyncFilesystemSource:
    """Return a fresh authenticated async filesystem source."""

    @asynccontextmanager
    async def source() -> AsyncIterator[AbstractFileSystem]:
        config = Configuration()  # ty: ignore[missing-argument]
        endpoint, idp = config._resolve_storage(storage_name)  # noqa: SLF001
        try:
            client_kwargs: dict[str, Any] = {
                "config": config,
                "authentication_idp": idp,
                "url": endpoint,
            }
            if token is not None:
                client_kwargs["token"] = token
            if certificate is not None:
                client_kwargs["certificate"] = certificate
            client = HTTPClient(
                **client_kwargs,
            )
            token_value, certfile = await client._materialize_credentials()  # noqa: SLF001
        except (KeyError, OSError, TypeError, ValueError):
            reason = "Credential cannot be used. Run 'canfar login' for this IDP."
            raise AuthContextError(idp, reason) from None

        from vosfs import VOSpaceFileSystem  # noqa: PLC0415

        if token_value is not None:
            filesystem = VOSpaceFileSystem(
                endpoint,
                token=token_value,
                asynchronous=True,
                skip_instance_cache=True,
            )
        else:
            assert certfile is not None
            filesystem = VOSpaceFileSystem(
                endpoint,
                certfile=certfile,
                asynchronous=True,
                skip_instance_cache=True,
            )
        try:
            yield filesystem
        finally:
            await filesystem.aclose()

    return source
