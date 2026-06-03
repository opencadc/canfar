"""CANFAR Authentication API."""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING, Literal, NoReturn

from pydantic import AnyHttpUrl, AnyUrl, BaseModel, ConfigDict, Field

from canfar.errors import ErrorCode, StructuredError
from canfar.idp import IdpInfo, get_idp
from canfar.models.auth import (
    AuthenticationCredential,
    OIDCCredential,
    X509Credential,
)
from canfar.models.config import Configuration
from canfar.models.http import Server
from canfar.models.registry import IVOARegistrySearch
from canfar.models.registry import Server as RegistryServer
from canfar.utils.discover import Discover

if TYPE_CHECKING:
    import builtins
    from collections.abc import Mapping

AuthMode = Literal["x509", "oidc"]


class Authentication(BaseModel):
    """CANFAR Authentication record."""

    model_config = ConfigDict(extra="forbid")

    idp: str = Field(description="Canonical Identity Provider key.")
    name: str = Field(description="Human-readable IDP name.")
    mode: AuthMode = Field(description="Authentication mode.")
    expiry: float | None = Field(
        default=None,
        description="Credential expiry as Unix timestamp when applicable.",
    )
    active: bool = Field(description="Whether this record is active.")
    server: str | None = Field(
        default=None,
        description="Selected server URI reference when available.",
    )


class AuthenticationError(Exception):
    """Authentication operation failed."""

    error: StructuredError

    def __init__(self, error: StructuredError | Mapping[str, object]) -> None:
        """Validate and attach a structured error payload.

        Args:
            error: Structured error fields or a validated model instance.
        """
        self.error = StructuredError.model_validate(error)
        super().__init__(self.error.message)


def _authentication_error(
    *,
    code: ErrorCode,
    message: str,
    hint: str | None = None,
) -> AuthenticationError:
    """Build a validated authentication failure."""
    return AuthenticationError(
        StructuredError(code=code, message=message, hint=hint),
    )


def _fail(
    *,
    code: ErrorCode,
    message: str,
    hint: str | None = None,
) -> NoReturn:
    """Raise ``AuthenticationError`` with a validated structured payload."""
    raise _authentication_error(code=code, message=message, hint=hint)


def login(idp: str, force: bool = False) -> None:
    """Authenticate IDP, discover servers, save records.

    Skips work when auth already saved and ``force`` is false. Does not change
    active auth or server selection.

    Args:
        idp: Canonical Identity Provider key.
        force: Re-authenticate and rediscover when true.

    Raises:
        KeyError: Unknown IDP key.
        AuthenticationError: Credential or discovery failure.
    """
    idp_info = get_idp(idp)
    config = Configuration()

    if _has_authentication(config, idp) and not force:
        return

    credential = _authenticate(idp_info)
    servers = asyncio.run(_discover_servers(idp_info))

    _upsert_credential(config, credential)
    for server in servers:
        config._upsert_server(server)  # noqa: SLF001
    config.save()


def use(idp: str) -> None:
    """Set active authentication to ``idp``.

    Clears active server when it is incompatible with ``idp``.

    Args:
        idp: Canonical Identity Provider key.

    Raises:
        KeyError: Unknown IDP key.
        AuthenticationError: Saved authentication missing for ``idp``.
    """
    get_idp(idp)
    config = Configuration()

    try:
        config.get_credential(idp)
    except KeyError as exc:
        raise _authentication_error(
            code=ErrorCode.AUTHENTICATION_REQUIRED,
            message=f"Authentication for IDP '{idp}' is not configured.",
            hint="Run canfar.login() for this IDP before selecting it.",
        ) from exc

    remembered = config.get_remembered_server_for_idp(idp)
    if remembered is not None:
        config.set_active_selection(idp, remembered)
    else:
        selections = config._server_selection_history()  # noqa: SLF001
        config.active.authentication = idp
        if not _active_server_compatible(config, idp):
            config.active.server = None
        config.active.servers = selections

    config.save()


def list() -> builtins.list[Authentication]:  # noqa: A001
    """Return saved authentication records.

    Returns:
        Authentication records for configured IDPs. Order not guaranteed.
    """
    config = Configuration()
    return [
        _authentication_for_credential(config, cred) for cred in config.authentication
    ]


def remove(idp: str, *, force: bool = False) -> None:
    """Remove authentication and servers for ``idp``.

    Args:
        idp: Canonical Identity Provider key.
        force: Allow removing the active authentication record.

    Raises:
        KeyError: Unknown IDP key.
        AuthenticationError: Missing auth or active auth removed without force.
    """
    get_idp(idp)
    config = Configuration()

    if not _has_authentication(config, idp):
        _fail(
            code=ErrorCode.AUTHENTICATION_REQUIRED,
            message=f"Authentication for IDP '{idp}' is not configured.",
            hint="Nothing to remove for this IDP.",
        )

    if config.active.authentication == idp and not force:
        _fail(
            code=ErrorCode.AUTHENTICATION_REQUIRED,
            message=f"Cannot remove active authentication '{idp}' without --force.",
            hint="Use --force or switch authentication before removing.",
        )

    config.authentication = [
        credential for credential in config.authentication if credential.idp != idp
    ]
    config.server = [server for server in config.server if server.idp != idp]
    config.active.servers.pop(idp, None)

    if config.active.authentication == idp:
        if config.authentication:
            config.active.authentication = config.authentication[0].idp
            config.active.server = None
        else:
            config.active = config.active.model_copy(
                update={"authentication": "cadc", "server": None}
            )

    config.save()


def purge(*, force: bool = False) -> None:
    """Reset authentication and server state.

    Preserves registry and console settings.

    Args:
        force: Required to perform the purge.

    Raises:
        AuthenticationError: ``force`` is false.
    """
    if not force:
        _fail(
            code=ErrorCode.AUTHENTICATION_REQUIRED,
            message="Authentication purge requires --force.",
            hint="Re-run with --force to reset authentication and server state.",
        )

    config = Configuration()
    registry = config.registry.model_copy(deep=True)
    console = config.console.model_copy(deep=True)
    fresh = Configuration(registry=registry, console=console)
    fresh.save()


def show() -> Authentication:
    """Return the active authentication record.

    Returns:
        Active authentication record.

    Raises:
        AuthenticationError: Active authentication is not configured.
    """
    config = Configuration()
    try:
        credential = config.get_credential(config.active.authentication)
    except KeyError as exc:
        raise _authentication_error(
            code=ErrorCode.AUTHENTICATION_REQUIRED,
            message=(
                f"Active authentication '{config.active.authentication}' "
                "is not configured."
            ),
            hint="Run canfar.login() to configure authentication.",
        ) from exc

    return _authentication_for_credential(config, credential)


def _has_authentication(config: Configuration, idp: str) -> bool:
    return any(credential.idp == idp for credential in config.authentication)


def _active_server_compatible(config: Configuration, idp: str) -> bool:
    if config.active.server is None:
        return False
    try:
        server = config.get_active_server()
    except KeyError:
        return False
    return server.idp == idp


def _authentication_for_credential(
    config: Configuration,
    credential: AuthenticationCredential,
) -> Authentication:
    idp_info = get_idp(credential.idp)
    active = config.active.authentication == credential.idp
    server_ref: str | None = None

    if active and config.active.server is not None:
        try:
            server = config.get_active_server()
        except KeyError:
            server_ref = str(config.active.server)
        else:
            if server.idp == credential.idp:
                server_ref = str(config.active.server)

    expiry = _credential_expiry(credential)
    return Authentication(
        idp=credential.idp,
        name=idp_info.name,
        mode=credential.mode,
        expiry=expiry,
        active=active,
        server=server_ref,
    )


def _credential_expiry(credential: AuthenticationCredential) -> float | None:
    if credential.mode == "x509":
        return credential.expiry or None
    access_expiry = credential.expiry.access
    return access_expiry or None


def _upsert_credential(
    config: Configuration,
    credential: AuthenticationCredential,
) -> None:
    updated: builtins.list[AuthenticationCredential] = []
    replaced = False
    for existing in config.authentication:
        if existing.idp == credential.idp:
            updated.append(credential)
            replaced = True
        else:
            updated.append(existing)
    if not replaced:
        updated.append(credential)
    config.authentication = updated


def _authenticate(idp_info: IdpInfo) -> AuthenticationCredential:
    if idp_info.auth_mode == "x509":
        return _authenticate_x509(idp_info.key)
    return _authenticate_oidc(idp_info.key)


def _authenticate_x509(idp: str) -> X509Credential:
    from canfar.auth import x509  # noqa: PLC0415

    try:
        info = x509.inspect()
    except (FileNotFoundError, ValueError) as exc:
        raise _authentication_error(
            code=ErrorCode.AUTHENTICATION_CREDENTIAL_MISSING,
            message=f"No usable X509 credential found for IDP '{idp}'.",
            hint="Obtain a certificate before calling canfar.login().",
        ) from exc

    return X509Credential(
        idp=idp,
        path=info["path"],
        expiry=float(info["expiry"] or 0.0),
    )


def _authenticate_oidc(idp: str) -> OIDCCredential:
    _fail(
        code=ErrorCode.AUTHENTICATION_CREDENTIAL_MISSING,
        message=f"OIDC authentication for IDP '{idp}' requires interactive login.",
        hint="Use the CLI login flow for first-time OIDC authentication.",
    )


async def _discover_servers(idp_info: IdpInfo) -> builtins.list[Server]:
    registry_config = IVOARegistrySearch(
        registries={str(idp_info.registry_url): idp_info.name}
    )
    async with Discover(registry_config) as discovery:
        results = await discovery.servers()

    servers: builtins.list[Server] = []
    for endpoint in results.endpoints:
        if endpoint.status != 200:
            continue
        servers.append(_registry_server_to_config_server(endpoint, idp_info))
    return servers


def _registry_server_to_config_server(
    endpoint: RegistryServer,
    idp_info: IdpInfo,
) -> Server:
    name = endpoint.name
    if name is None:
        name = f"{idp_info.name}-{endpoint.uri.rsplit('/', maxsplit=1)[-1]}"
    return Server(
        idp=idp_info.key,
        name=name,
        uri=AnyUrl(endpoint.uri),
        url=AnyHttpUrl(endpoint.url),
    )


__all__ = [
    "Authentication",
    "AuthenticationError",
    "list",
    "login",
    "purge",
    "remove",
    "show",
    "use",
]
