"""CANFAR Authentication API."""

from __future__ import annotations

import asyncio
import sys
from typing import TYPE_CHECKING, NoReturn

import httpx

import canfar.server as server_service
from canfar.auth import oidc
from canfar.errors import ErrorCode, StructuredError
from canfar.idp import IdpInfo, get_idp
from canfar.models.auth import (
    Authentication,
    AuthenticationCredential,
    AuthMode,
    Client,
    DeviceAuthorization,
    Endpoint,
    Expiry,
    OIDCCredential,
    Token,
    X509Credential,
)
from canfar.models.config import (
    Configuration,
    default_active,
    default_authentication,
    default_servers,
)

if TYPE_CHECKING:
    import builtins
    from collections.abc import Mapping


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


_OIDC_DEVICE_LOGIN_ERRORS = (
    PermissionError,
    TimeoutError,
    TypeError,
    ValueError,
    httpx.HTTPError,
)


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
    config = Configuration()  # ty: ignore[missing-argument]

    if _has_authentication(config, idp) and not force:
        return

    credential = _authenticate(idp_info)
    config.editor.set(f"authentication.{credential.idp}", credential)
    server_service.discover(idp, config=config, save=False)
    config.editor.save()


async def alogin(idp: str, force: bool = False) -> None:
    """Authenticate an IDP from an existing asynchronous event loop.

    The OIDC protocol uses native asynchronous HTTP and polling. Synchronous
    X.509 inspection and Science Platform discovery run in worker threads so
    this API does not block the caller's event loop.

    Args:
        idp: Canonical Identity Provider key.
        force: Re-authenticate and rediscover when true.

    Raises:
        KeyError: Unknown IDP key.
        AuthenticationError: Credential or discovery failure.
    """
    idp_info = get_idp(idp)
    config = Configuration()  # ty: ignore[missing-argument]

    if _has_authentication(config, idp) and not force:
        return

    credential = await _authenticate_async(idp_info)
    editor = config.editor
    editor.set(f"authentication.{credential.idp}", credential)
    await asyncio.to_thread(
        server_service.discover,
        idp,
        config=config,
        save=False,
    )
    await asyncio.to_thread(editor.save)


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
    config = Configuration()  # ty: ignore[missing-argument]

    try:
        _authentication_record(config, idp)
    except KeyError as exc:
        raise _authentication_error(
            code=ErrorCode.AUTHENTICATION_REQUIRED,
            message=f"Authentication for IDP '{idp}' is not configured.",
            hint="Run canfar.login() for this IDP before selecting it.",
        ) from exc

    server_service.activate_authentication(idp, config=config)


def list() -> builtins.list[Authentication]:  # noqa: A001
    """Return saved authentication records.

    Returns:
        Authentication records for configured IDPs. Order not guaranteed.
    """
    config = Configuration()  # ty: ignore[missing-argument]
    return [
        _authentication_for_credential(config, cred)
        for cred in config.authentication.values()
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
    config = Configuration()  # ty: ignore[missing-argument]

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

    _remove_authentication(config, idp)


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

    config = Configuration()  # ty: ignore[missing-argument]
    _purge_authentication(config)


def show() -> Authentication:
    """Return the active authentication record.

    Returns:
        Active authentication record.

    Raises:
        AuthenticationError: Active authentication is not configured.
    """
    config = Configuration()  # ty: ignore[missing-argument]
    try:
        credential = _authentication_record(config, config.active.authentication)
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
    return idp in config.authentication


def _authentication_record(
    config: Configuration,
    idp: str,
) -> AuthenticationCredential:
    """Return a saved Authentication Record by its IDP key."""
    try:
        return config.authentication[idp]
    except KeyError as exc:
        msg = f"Authentication record for IDP '{idp}' not found."
        raise KeyError(msg) from exc


def _remove_authentication(config: Configuration, idp: str) -> None:
    """Remove one Authentication Record and its associated Server state."""
    authentication = dict(config.authentication)
    authentication.pop(idp, None)
    if not authentication:
        _purge_authentication(config)
        return

    servers = {
        name: server for name, server in config.servers.items() if server.idp != idp
    }
    selections = {
        selected_idp: name
        for selected_idp, name in config.active.servers.items()
        if selected_idp != idp and name in servers
    }
    active = config.active.model_copy(update={"servers": selections})
    if active.authentication == idp:
        active = active.model_copy(
            update={
                "authentication": next(iter(authentication)),
                "server": None,
            },
        )
    elif active.server not in servers:
        active = active.model_copy(update={"server": None})

    editor = config.editor
    editor._set_top_level(  # noqa: SLF001
        active=active,
        authentication=authentication,
        servers=servers,
    )
    editor.save()


def _purge_authentication(config: Configuration) -> None:
    """Reset Authentication and Server state while preserving other settings."""
    editor = config.editor
    editor._set_top_level(  # noqa: SLF001
        active=default_active.model_copy(deep=True),
        authentication={
            key: credential.model_copy(deep=True)
            for key, credential in default_authentication.items()
        },
        servers={
            name: server.model_copy(deep=True)
            for name, server in default_servers.items()
        },
    )
    editor.save()


def _authentication_for_credential(
    config: Configuration,
    credential: AuthenticationCredential,
) -> Authentication:
    idp_info = get_idp(credential.idp)
    active = config.active.authentication == credential.idp
    server_ref: str | None = None

    if active and config.active.server is not None:
        try:
            server = config.servers[config.active.server]
        except KeyError:
            server_ref = config.active.server
        else:
            if server.idp == credential.idp:
                server_ref = config.active.server

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


def _authenticate(idp_info: IdpInfo) -> AuthenticationCredential:
    if idp_info.auth_mode == "x509":
        return _authenticate_x509(idp_info.key)
    return _authenticate_oidc(idp_info)


async def _authenticate_async(idp_info: IdpInfo) -> AuthenticationCredential:
    """Acquire one Authentication Record without blocking an event loop."""
    if idp_info.auth_mode == "x509":
        return await asyncio.to_thread(_authenticate_x509, idp_info.key)
    return await _authenticate_oidc_async(idp_info)


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


def _print_device_challenge(challenge: DeviceAuthorization) -> None:
    """Print only user-facing device authorization data to the terminal."""
    lines = [f"Verification URL: {challenge.verification_uri}"]
    if challenge.verification_uri_complete is not None:
        lines.append(
            f"Verification URL (complete): {challenge.verification_uri_complete}"
        )
    lines.append(f"Device code: {challenge.user_code.get_secret_value()}")
    sys.stdout.write(
        "\n".join(lines) + "\n",
    )
    sys.stdout.flush()


def _oidc_credential(idp: str, info: IdpInfo) -> OIDCCredential:
    """Build an empty OIDC Authentication Record from IDP metadata."""
    if info.oidc_discovery_url is None:
        msg = f"OIDC discovery URL is not configured for IDP '{idp}'."
        raise RuntimeError(msg)
    if info.oidc_issuer is None:
        msg = f"OIDC issuer is not configured for IDP '{idp}'."
        raise RuntimeError(msg)
    return OIDCCredential(
        idp=idp,
        endpoints=Endpoint(discovery=str(info.oidc_discovery_url)),
        client=Client(),
        token=Token(),
        expiry=Expiry(),
    )


def _raise_oidc_authentication_error(exc: Exception) -> NoReturn:
    """Translate an OIDC device-login failure into a structured error."""
    raise _authentication_error(
        code=ErrorCode.AUTHENTICATION_CREDENTIAL_MISSING,
        message=f"OIDC authentication failed: {exc}",
        hint="Complete the device authorization before it expires.",
    ) from exc


def _authenticate_oidc(info: IdpInfo) -> OIDCCredential:
    """Acquire one OIDC Authentication Record with native sync I/O."""
    credential = _oidc_credential(info.key, info)
    try:
        return oidc.sync_authenticate_credential(
            credential,
            expected_issuer=str(info.oidc_issuer),
            on_challenge=_print_device_challenge,
        )
    except _OIDC_DEVICE_LOGIN_ERRORS as exc:
        _raise_oidc_authentication_error(exc)


async def _authenticate_oidc_async(info: IdpInfo) -> OIDCCredential:
    """Acquire one OIDC Authentication Record with native async I/O."""
    credential = _oidc_credential(info.key, info)
    try:
        return await oidc.authenticate_credential(
            credential,
            expected_issuer=str(info.oidc_issuer),
            on_challenge=_print_device_challenge,
        )
    except _OIDC_DEVICE_LOGIN_ERRORS as exc:
        _raise_oidc_authentication_error(exc)


__all__ = [
    "AuthMode",
    "Authentication",
    "AuthenticationError",
    "alogin",
    "list",
    "login",
    "purge",
    "remove",
    "show",
    "use",
]
