"""HTTPx hook to check for authentication expiry."""

from __future__ import annotations

from typing import TYPE_CHECKING, Callable

from canfar.exceptions.context import AuthExpiredError

if TYPE_CHECKING:
    from collections.abc import Awaitable

    import httpx

    from canfar.client import HTTPClient


def check(client: HTTPClient) -> Callable[[httpx.Request], None]:
    """Create a hook to check for authentication expiry.

    Args:
        client (HTTPClient): The CANFAR client.

    """

    def hook(request: httpx.Request) -> None:  # noqa: ARG001
        """Check if the authentication context is expired.

        Args:
            request (httpx.Request): The request.

        Raises:
            AuthExpiredError: If the authentication context is expired.

        """
        if client.config.context.expired:
            raise AuthExpiredError(
                context=client.config.context.mode, reason="auth expired"
            )

    return hook


def acheck(client: HTTPClient) -> Callable[[httpx.Request], Awaitable[None]]:
    """Create an async hook to check for authentication expiry.

    This returns an async callable suitable for httpx's async event hooks.

    Args:
        client (HTTPClient): The CANFAR client.
    """

    async def hook(request: httpx.Request) -> None:  # noqa: ARG001
        """Check if the authentication context is expired.

        Args:
            request (httpx.Request): The request.

        Raises:
            AuthExpiredError: If the authentication context is expired.
        """
        if client.config.context.expired:
            raise AuthExpiredError(
                context=client.config.context.mode, reason="auth expired"
            )

    return hook
