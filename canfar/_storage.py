"""Private adapters for configured VOSpace Services."""

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import TYPE_CHECKING, cast

from canfar.auth import oidc, x509
from canfar.client import HTTPClient
from canfar.exceptions.context import AuthContextError
from canfar.models.auth import OIDCCredential, X509Credential
from canfar.models.config import Configuration

if TYPE_CHECKING:
    from collections.abc import AsyncIterator
    from pathlib import Path
    from typing import NoReturn

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
        config = Configuration()
        endpoint, idp = _resolve_storage(config, storage_name)
        credentials = await _materialize_credentials(
            config,
            idp,
            endpoint,
            token=token,
            certificate=certificate,
        )

        from vosfs import VOSpaceFileSystem  # noqa: PLC0415

        if token_value := credentials.get("token"):
            filesystem = VOSpaceFileSystem(
                endpoint,
                token=token_value,
                asynchronous=True,
                skip_instance_cache=True,
            )
        else:
            filesystem = VOSpaceFileSystem(
                endpoint,
                certfile=credentials["certfile"],
                asynchronous=True,
                skip_instance_cache=True,
            )
        try:
            yield filesystem
        finally:
            await filesystem.aclose()

    return source


def _resolve_storage(config: Configuration, storage_name: str) -> tuple[str, str]:
    """Resolve one Storage Name to its endpoint and parent server IDP."""
    for server in config.servers.values():
        service = server.storage.get(storage_name)
        if service is not None:
            if server.idp is None:
                msg = (
                    f"Storage Name '{storage_name}' belongs to a Science Platform "
                    "Server without an IDP."
                )
                raise ValueError(msg)
            return str(service.url), server.idp
    msg = f"Storage Name '{storage_name}' is not configured."
    raise KeyError(msg)


async def _materialize_credentials(
    config: Configuration,
    idp: str,
    endpoint: str,
    *,
    token: str | SecretStr | None,
    certificate: Path | None,
) -> dict[str, str]:
    """Return only literal credential material accepted by vosfs."""
    try:
        client = HTTPClient(
            config=config,
            authentication_idp=idp,
            url=endpoint,
            token=token,
            certificate=certificate,
        )
        if client.token is not None:
            return {"token": client.token.get_secret_value()}
        if client.certificate is not None:
            return {"certfile": x509.valid(client.certificate)}

        credential = client.authentication_record
        if isinstance(credential, X509Credential):
            if credential.path is None:
                _fail_authentication(idp)
            return {"certfile": cast("str", x509.inspect(credential.path)["path"])}
        if not isinstance(credential, OIDCCredential):
            _fail_authentication(idp)

        if credential.expired:
            parameters = _refresh_parameters(credential)
            refreshed = await oidc.refresh(*parameters)
            credential = oidc._persist_refreshed_credential(  # noqa: SLF001
                config,
                credential,
                refreshed,
            )
        if credential.token.access is None:
            _fail_authentication(idp)
        return {"token": credential.token.access.get_secret_value()}
    except (KeyError, OSError, TypeError, ValueError):
        _fail_authentication(idp)


def _fail_authentication(idp: str) -> NoReturn:
    """Raise the fixed secret-safe authentication failure."""
    reason = "Credential cannot be used. Run 'canfar login' for this IDP."
    raise AuthContextError(idp, reason) from None


def _refresh_parameters(credential: OIDCCredential) -> tuple[str, str, str, str]:
    """Return literal refresh inputs for an eligible Authentication Record."""
    if not credential.refreshable:
        raise ValueError
    return (
        cast("str", credential.endpoints.token),
        cast("str", credential.client.identity),
        cast("SecretStr", credential.client.secret).get_secret_value(),
        cast("SecretStr", credential.token.refresh).get_secret_value(),
    )
