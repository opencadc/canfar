"""HTTPx hook to check for authentication expiry."""

from __future__ import annotations

from typing import TYPE_CHECKING, Callable, Awaitable

from skaha.exceptions.context import AuthExpiredError

if TYPE_CHECKING:
    import httpx

    from skaha.client import SkahaClient


def check(client: SkahaClient) -> Callable[[httpx.Request], None]:
    """Create a hook to check for authentication expiry.

    Args:
        client (SkahaClient): The Skaha client.

    """

    def hook(request: httpx.Request) -> None:
        """Check if the authentication context is expired.

        Args:
            request (httpx.Request): The request.

        Raises:
            AuthExpiredError: If the authentication context is expired.

        """
        if client.config.context.expired:
            raise AuthExpiredError(context=client.config.context.mode, reason="auth expired")
    return hook

def acheck(client: SkahaClient) -> Callable[[httpx.Request], Awaitable[None]]:
    """Create an async hook to check for authentication expiry.

    This returns an async callable suitable for httpx's async event hooks.

    Args:
        client (SkahaClient): The Skaha client.
    """

    async def hook(request: httpx.Request) -> None:
        """Check if the authentication context is expired.

        Args:
            request (httpx.Request): The request.

        Raises:
            AuthExpiredError: If the authentication context is expired.
        """

        if client.config.context.expired:
            raise AuthExpiredError(context=client.config.context.mode, reason="auth expired")

    return hook
