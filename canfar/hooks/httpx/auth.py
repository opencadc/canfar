"""HTTPx authentication hooks for automatic token refresh and certificate renewal.

This module provides httpx event hooks that automatically handle authentication
expiry and refresh for different authentication modes:

- **X509/Default Mode**: Automatically renews certificates when expired
- **OIDC Mode**: Automatically refreshes access tokens using refresh tokens
- **User-provided credentials**: Bypasses automatic refresh

The hooks are designed to be used with httpx clients to provide seamless
authentication management without requiring manual intervention.

Usage:
    ```python
    from canfar.client import HTTPClient
    from canfar.hooks.httpx.auth import create_auth_hook

    client = HTTPClient()
    auth_hook = create_auth_hook(client)

    # The hook is automatically applied to the client's httpx instances
    ```

Note:
    The hooks modify the request before it's sent, updating headers and
    authentication credentials as needed. They also save updated configuration
    to disk when credentials are refreshed.
"""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING, Callable, cast

from pydantic import SecretStr

from canfar import get_logger
from canfar.auth import oidc
from canfar.models.auth import OIDCCredential
from canfar.utils import jwt

if TYPE_CHECKING:
    from collections.abc import Awaitable, MutableMapping

    import httpx

    from canfar.client import HTTPClient

log = get_logger(__name__)


class AuthenticationError(Exception):
    """Exception raised when authentication refresh fails."""


def _get_oidc_credential(client: HTTPClient) -> OIDCCredential | None:
    """Return the selected canonical OIDC record unless runtime auth wins."""
    if client.uses_runtime_credentials:
        return None
    credential = client.authentication_record
    return credential if isinstance(credential, OIDCCredential) else None


def _apply_access_header(
    token: SecretStr,
    httpx_client_headers: MutableMapping[str, str],
    request: httpx.Request,
) -> None:
    """Apply one access token to the active client and outgoing request."""
    header = f"Bearer {token.get_secret_value()}"
    httpx_client_headers["Authorization"] = header
    request.headers["Authorization"] = header


def _refresh_parameters(
    credential: OIDCCredential,
) -> tuple[str, str, str, str] | None:
    """Return complete refresh inputs when the record is eligible."""
    if not credential.refreshable:
        return None
    token_url = cast("str", credential.endpoints.token)
    identity = cast("str", credential.client.identity)
    client_secret = cast("SecretStr", credential.client.secret)
    refresh_token = cast("SecretStr", credential.token.refresh)
    return (
        token_url,
        identity,
        client_secret.get_secret_value(),
        refresh_token.get_secret_value(),
    )


def _apply_refreshed_token(
    client: HTTPClient,
    credential: OIDCCredential,
    token: SecretStr,
    httpx_client_headers: MutableMapping[str, str],
    request: httpx.Request,
) -> None:
    """Persist a refreshed access token to config, headers, and the outgoing request.

    Shared by both ``refresh`` (sync) and ``arefresh`` (async); only the
    source of ``token`` (sync vs. async network call) and the target of
    ``httpx_client_headers`` (``client.client.headers`` for sync vs.
    ``client.asynclient.headers`` for async) differ between the two callers.

    Args:
        client: The CANFAR HTTPClient whose config is updated.
        credential: The current OIDC Authentication Record.
        token: The new access token returned by the OIDC provider.
        httpx_client_headers: The header mapping of the underlying httpx client.
        request: The outgoing httpx request whose Authorization header is updated.
    """
    access_value = token.get_secret_value()
    updated = credential.model_copy(
        update={
            "token": credential.token.model_copy(
                update={"access": SecretStr(access_value)}
            ),
            "expiry": credential.expiry.model_copy(
                update={"access": jwt.expiry(access_value)}
            ),
        }
    )

    client.config.update_credential(updated)
    client.config.save()
    log.debug("Authentication refreshed and configuration saved.")

    _apply_access_header(token, httpx_client_headers, request)
    log.debug("HTTP request headers updated with new token.")
    log.info("OIDC Access Token Refreshed.")


def refresh(client: HTTPClient) -> Callable[[httpx.Request], None]:
    """Create an authentication refresh hook for httpx clients.

    Args:
        client (HTTPClient): The HTTPClient instance.

    Returns:
        Callable[[httpx.Request], None]: The auth hook function.
    """

    def hook(request: httpx.Request) -> None:
        """Synchronous refresh hook for httpx clients.

        Args:
            request (httpx.Request): The outgoing HTTP request.
        """
        credential = _get_oidc_credential(client)
        if credential is None:
            log.debug("Skipping auth refresh without a saved OIDC record.")
            return

        # Skip if the access token is not expired
        if not credential.expired:
            if credential.token.access is not None:
                _apply_access_header(
                    credential.token.access,
                    client.client.headers,
                    request,
                )
            log.debug("Skipping auth refresh, access token is not expired.")
            return

        parameters = _refresh_parameters(credential)
        if parameters is None:
            log.warning("OIDC Authentication Record cannot be refreshed.")
            return
        token_url, identity, client_secret, refresh_token = parameters

        try:
            log.debug("Starting synchronous OIDC token refresh.")
            token: SecretStr = oidc.sync_refresh(
                url=token_url,
                identity=identity,
                secret=client_secret,
                token=refresh_token,
            )
            log.debug("Synchronous OIDC token refresh successful.")
            _apply_refreshed_token(
                client,
                credential,
                token,
                client.client.headers,
                request,
            )

        except Exception as err:
            msg = f"Failed to refresh OIDC token: {err}"
            log.exception(msg)
            raise AuthenticationError(msg) from err

    return hook


def arefresh(client: HTTPClient) -> Callable[[httpx.Request], Awaitable[None]]:
    """Create an asynchronous authentication refresh hook for httpx clients.

    Args:
        client (HTTPClient): The HTTPClient instance.

    Returns:
        Callable[[httpx.Request], Awaitable[None]]: The async auth hook.
    """
    lock = asyncio.Lock()

    async def ahook(request: httpx.Request) -> None:
        """Asynchronous refresh hook for httpx clients.

        Args:
            request (httpx.Request): The outgoing HTTP request.
        """
        async with lock:
            credential = _get_oidc_credential(client)
            if credential is None:
                log.debug("Skipping auth refresh without a saved OIDC record.")
                return

            if not credential.expired:
                if credential.token.access is not None:
                    _apply_access_header(
                        credential.token.access,
                        client.asynclient.headers,
                        request,
                    )
                return

            parameters = _refresh_parameters(credential)
            if parameters is None:
                log.warning("OIDC Authentication Record cannot be refreshed.")
                return
            token_url, identity, client_secret, refresh_token = parameters

            try:
                log.debug("Starting asynchronous OIDC token refresh.")
                token: SecretStr = await oidc.refresh(
                    url=token_url,
                    identity=identity,
                    secret=client_secret,
                    token=refresh_token,
                )
                log.debug("Asynchronous OIDC token refresh successful.")
                _apply_refreshed_token(
                    client,
                    credential,
                    token,
                    client.asynclient.headers,
                    request,
                )

            except Exception as err:
                msg = f"Failed to refresh OIDC token: {err}"
                log.exception(msg)
                raise AuthenticationError(msg) from err

    return ahook
