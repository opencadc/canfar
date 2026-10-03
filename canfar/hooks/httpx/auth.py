"""HTTPX2 authentication hooks for automatic OIDC token refresh.

This module provides httpx2 event hooks that automatically handle authentication
expiry and refresh for different authentication modes:

- **X509 Mode**: Requires explicit interactive login when certificates expire
- **OIDC Mode**: Automatically refreshes access tokens using refresh tokens
- **User-provided credentials**: Bypasses automatic refresh

``HTTPClient`` installs these hooks on the httpx2 clients it builds.

Note:
    The hooks modify the request before it's sent, updating headers and
    authentication credentials as needed. They also save updated configuration
    to disk when credentials are refreshed.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Callable

from canfar.auth import oidc
from canfar.exceptions.context import AuthRequiredError
from canfar.models.auth import OIDCCredential

if TYPE_CHECKING:
    from collections.abc import Awaitable, MutableMapping

    from httpx2 import Request
    from pydantic import SecretStr

    from canfar.client import HTTPClient

log = logging.getLogger(__name__)


class AuthenticationError(Exception):
    """Exception raised when authentication refresh fails."""


RefreshParameters = tuple[str, str, str, str]


def _refresh(
    client: HTTPClient,
) -> tuple[OIDCCredential, RefreshParameters | None] | None:
    """Resolve the saved OIDC record and prepare its refresh inputs.

    Runtime credentials take precedence, so they skip refresh.
    """
    credential = (
        None if client.uses_runtime_credentials else client.authentication_record
    )
    if not isinstance(credential, OIDCCredential):
        log.debug("Skipping auth refresh without a saved OIDC record.")
        return None
    if credential.access_usable:
        return credential, None
    parameters = oidc._refresh(credential)  # noqa: SLF001
    if parameters is None:
        reason = (
            "OIDC client secret expired."
            if credential.client.secret_expired
            else "OIDC refresh credentials are missing or expired."
        )
        raise AuthRequiredError(credential.idp, reason)
    return credential, parameters


def _apply_access_header(
    token: SecretStr,
    httpx_client_headers: MutableMapping[str, str],
    request: Request,
) -> None:
    """Apply one access token to the active client and outgoing request."""
    header = f"Bearer {token.get_secret_value()}"
    httpx_client_headers["Authorization"] = header
    request.headers["Authorization"] = header


def refresh(client: HTTPClient) -> Callable[[Request], None]:
    """Create an authentication refresh hook for httpx2 clients.

    Args:
        client (HTTPClient): The HTTPClient instance.

    Returns:
        Callable[[httpx2.Request], None]: The auth hook function.
    """

    def hook(request: Request) -> None:
        """Synchronous refresh hook for httpx2 clients.

        Args:
            request (httpx2.Request): The outgoing HTTP request.
        """
        prepared = _refresh(client)
        if prepared is None:
            return
        credential, parameters = prepared
        if parameters is None:
            if credential.token.access is not None:
                _apply_access_header(
                    credential.token.access,
                    client.client.headers,
                    request,
                )
            log.debug("Skipping auth refresh, access token is not expired.")
            return
        token_url, identity, client_secret, refresh_token = parameters

        try:
            log.debug("Starting synchronous OIDC token refresh.")
            token = oidc.sync_refresh(
                url=token_url,
                identity=identity,
                secret=client_secret,
                token=refresh_token,
            )
            log.debug("Synchronous OIDC token refresh successful.")
            updated = oidc._persist(  # noqa: SLF001
                client.config, credential, token
            )
            log.debug("Authentication refreshed and configuration saved.")

            assert updated.token.access is not None
            _apply_access_header(updated.token.access, client.client.headers, request)
            log.debug("HTTP request headers updated with new token.")
            log.info("OIDC Access Token Refreshed.")

        except oidc.ReauthenticationRequiredError as err:
            raise AuthRequiredError(credential.idp, str(err)) from None
        except (ValueError, OSError):
            msg = "Failed to refresh OIDC token"
            raise AuthenticationError(msg) from None

    return hook


def arefresh(client: HTTPClient) -> Callable[[Request], Awaitable[None]]:
    """Create an asynchronous authentication refresh hook for httpx2 clients.

    Args:
        client (HTTPClient): The HTTPClient instance.

    Returns:
        Callable[[httpx2.Request], Awaitable[None]]: The async auth hook.
    """

    async def ahook(request: Request) -> None:
        """Asynchronous refresh hook for httpx2 clients.

        Args:
            request (httpx2.Request): The outgoing HTTP request.
        """
        previous = client.authentication_record
        if isinstance(previous, OIDCCredential) and previous.expired:
            log.debug("Starting asynchronous OIDC token refresh.")
        credential = await client._refresh_oidc()  # noqa: SLF001
        if credential is None:
            return
        if credential.token.access is not None:
            _apply_access_header(
                credential.token.access,
                client.asynclient.headers,
                request,
            )
        if credential == previous:
            log.debug("Skipping auth refresh, access token is not expired.")
            return
        log.debug("Asynchronous OIDC token refresh successful.")
        log.debug("HTTP request headers updated with new token.")
        log.info("OIDC Access Token Refreshed.")

    return ahook
