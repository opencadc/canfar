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

from typing import TYPE_CHECKING, Callable

from canfar import get_logger
from canfar.auth import oidc
from canfar.models.auth import OIDCCredential

if TYPE_CHECKING:
    from collections.abc import Awaitable, MutableMapping

    import httpx
    from pydantic import SecretStr

    from canfar.client import HTTPClient

log = get_logger(__name__)


class AuthenticationError(Exception):
    """Exception raised when authentication refresh fails."""


RefreshParameters = tuple[str, str, str, str]


def _get_oidc_credential(client: HTTPClient) -> OIDCCredential | None:
    """Return the selected canonical OIDC record unless runtime auth wins."""
    if client.uses_runtime_credentials:
        return None
    credential = client.authentication_record
    return credential if isinstance(credential, OIDCCredential) else None


def _refresh(
    client: HTTPClient,
) -> tuple[OIDCCredential, RefreshParameters | None] | None:
    """Resolve one OIDC record and prepare its refresh inputs."""
    credential = _get_oidc_credential(client)
    if credential is None:
        log.debug("Skipping auth refresh without a saved OIDC record.")
        return None
    if not credential.expired:
        return credential, None
    parameters = oidc._refresh(credential)  # noqa: SLF001
    if parameters is None:
        log.warning("OIDC Authentication Record cannot be refreshed.")
        return None
    return credential, parameters


def _apply_access_header(
    token: SecretStr,
    httpx_client_headers: MutableMapping[str, str],
    request: httpx.Request,
) -> None:
    """Apply one access token to the active client and outgoing request."""
    header = f"Bearer {token.get_secret_value()}"
    httpx_client_headers["Authorization"] = header
    request.headers["Authorization"] = header


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

        except (ValueError, OSError):
            msg = "Failed to refresh OIDC token"
            raise AuthenticationError(msg) from None

    return hook


def arefresh(client: HTTPClient) -> Callable[[httpx.Request], Awaitable[None]]:
    """Create an asynchronous authentication refresh hook for httpx clients.

    Args:
        client (HTTPClient): The HTTPClient instance.

    Returns:
        Callable[[httpx.Request], Awaitable[None]]: The async auth hook.
    """

    async def ahook(request: httpx.Request) -> None:
        """Asynchronous refresh hook for httpx clients.

        Args:
            request (httpx.Request): The outgoing HTTP request.
        """
        previous = client.authentication_record
        if isinstance(previous, OIDCCredential) and previous.expired:
            log.debug("Starting asynchronous OIDC token refresh.")
        try:
            credential = await client._refresh_oidc()  # noqa: SLF001
        except (ValueError, OSError):
            msg = "Failed to refresh OIDC token"
            raise AuthenticationError(msg) from None
        if credential is None:
            return
        if credential == previous:
            if credential.token.access is not None:
                _apply_access_header(
                    credential.token.access,
                    client.asynclient.headers,
                    request,
                )
            log.debug("Skipping auth refresh, access token is not expired.")
            return
        log.debug("Asynchronous OIDC token refresh successful.")
        if credential.token.access is not None:
            _apply_access_header(
                credential.token.access,
                client.asynclient.headers,
                request,
            )
        log.debug("HTTP request headers updated with new token.")
        log.info("OIDC Access Token Refreshed.")

    return ahook
