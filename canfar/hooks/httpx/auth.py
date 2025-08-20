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

import time
from typing import TYPE_CHECKING, Callable

from canfar import get_logger
from canfar.auth import oidc
from canfar.models.auth import OIDC
from canfar.utils import jwt

if TYPE_CHECKING:
    from collections.abc import Awaitable

    import httpx
    from pydantic import SecretStr

    from canfar.client import HTTPClient

log = get_logger(__name__)


class AuthenticationError(Exception):
    """Exception raised when authentication refresh fails."""


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
        ctx = client.config.context
        if not isinstance(ctx, OIDC):
            log.debug("Skipping auth refresh for non-OIDC context.")
            return

        # Skip if the access token is not expired
        if not ctx.expired:
            log.debug("Skipping auth refresh, access token is not expired.")
            return

        if not ctx.valid:
            log.warning("OIDC context is not valid.")
            return

        if not ctx.token.refresh or (
            ctx.expiry.refresh and ctx.expiry.refresh < time.time()
        ):
            log.warning("OIDC refresh token is missing or expired.")
            return

        try:
            log.debug("Starting synchronous OIDC token refresh.")
            token: SecretStr = oidc.sync_refresh(
                url=str(ctx.endpoints.token),
                identity=str(ctx.client.identity),
                secret=str(ctx.client.secret),
                token=str(ctx.token.refresh),
            )
            log.debug("Synchronous OIDC token refresh successful.")

            # Create a new context with the updated token
            data = ctx.model_dump()
            data["token"]["access"] = token.get_secret_value()
            data["expiry"]["access"] = jwt.expiry(token.get_secret_value())
            context = OIDC(**data)

            # Update the configuration and save it
            client.config.contexts[client.config.active] = context
            client.config.save()
            log.debug("Authentication refreshed and configuration saved.")

            # Update headers
            header = f"Bearer {token.get_secret_value()}"
            client.client.headers["Authorization"] = header
            request.headers["Authorization"] = header
            log.debug("HTTP request headers updated with new token.")
            log.info("OIDC Access Token Refreshed.")

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

    async def ahook(request: httpx.Request) -> None:
        """Asynchronous refresh hook for httpx clients.

        Args:
            request (httpx.Request): The outgoing HTTP request.
        """
        ctx = client.config.context
        if not isinstance(ctx, OIDC):
            log.debug("Skipping auth refresh for non-OIDC context.")
            return

        if not ctx.expired:
            return

        if not ctx.token.refresh or (
            ctx.expiry.refresh and ctx.expiry.refresh < time.time()
        ):
            log.warning("OIDC refresh token is missing or expired.")
            return

        try:
            log.debug("Starting asynchronous OIDC token refresh.")
            token: SecretStr = await oidc.refresh(
                url=str(ctx.endpoints.token),
                identity=str(ctx.client.identity),
                secret=str(ctx.client.secret),
                token=str(ctx.token.refresh),
            )
            log.debug("Asynchronous OIDC token refresh successful.")

            # Create a new context with the updated token
            data = ctx.model_dump()
            data["token"]["access"] = token.get_secret_value()
            data["expiry"]["access"] = jwt.expiry(token.get_secret_value())
            context = OIDC(**data)

            # Update the configuration and save it
            client.config.contexts[client.config.active] = context
            client.config.save()
            log.debug("Authentication refreshed and configuration saved.")

            # Update headers
            header = f"Bearer {token.get_secret_value()}"
            client.asynclient.headers["Authorization"] = header
            request.headers["Authorization"] = header
            log.debug("HTTP request headers updated with new token.")
            log.info("OIDC Access Token Refreshed.")

        except Exception as err:
            msg = f"Failed to refresh OIDC token: {err}"
            log.exception(msg)
            raise AuthenticationError(msg) from err

    return ahook
