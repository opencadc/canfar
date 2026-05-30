"""Interactive credential acquisition for CLI login flows."""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING

from canfar.auth import oidc, x509
from canfar.models.auth import (
    OIDC,
    X509,
    AuthenticationCredential,
    Client,
    Endpoint,
    Expiry,
    OIDCCredential,
    Token,
    X509Credential,
)
from canfar.models.http import Server

if TYPE_CHECKING:
    from canfar.idp import IdpInfo


def authenticate_for_cli(
    idp_info: IdpInfo,
    *,
    timeout: int | None = None,
) -> AuthenticationCredential:
    """Acquire Authentication credentials interactively for CLI login.

    Args:
        idp_info: Built-in Identity Provider metadata.
        timeout: HTTP timeout in seconds for OIDC requests.

    Returns:
        Saved-ready authentication credential without embedded server.

    Raises:
        ValueError: If credential acquisition fails.
        RuntimeError: If OIDC discovery URL is missing for an OIDC IDP.
    """
    if idp_info.auth_mode == "x509":
        return _authenticate_x509(idp_info.key)
    return _authenticate_oidc(idp_info, timeout=timeout)


def _authenticate_x509(idp: str) -> X509Credential:
    """Run interactive X509 certificate acquisition.

    Args:
        idp: Canonical Identity Provider key.

    Returns:
        X509 credential record for config v1.
    """
    context = x509.authenticate(X509(expiry=0.0))
    return X509Credential(
        idp=idp,
        path=context.path,
        expiry=context.expiry,
    )


def _authenticate_oidc(
    idp_info: IdpInfo,
    *,
    timeout: int | None = None,
) -> OIDCCredential:
    """Run interactive OIDC device authorization for an IDP.

    Args:
        idp_info: Built-in Identity Provider metadata.
        timeout: HTTP timeout in seconds for OIDC requests.

    Returns:
        OIDC credential record for config v1.

    Raises:
        RuntimeError: If the IDP has no configured OIDC discovery URL.
    """
    if idp_info.oidc_discovery_url is None:
        msg = f"OIDC discovery URL is not configured for IDP '{idp_info.key}'."
        raise RuntimeError(msg)

    legacy = OIDC(
        endpoints=Endpoint(discovery=str(idp_info.oidc_discovery_url)),
        client=Client(),
        token=Token(),
        expiry=Expiry(),
        server=Server(),
    )
    updated = asyncio.run(oidc.authenticate(legacy, timeout=timeout))
    return OIDCCredential(
        idp=idp_info.key,
        endpoints=updated.endpoints,
        client=updated.client,
        token=updated.token,
        expiry=updated.expiry,
    )
