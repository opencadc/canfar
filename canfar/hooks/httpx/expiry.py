"""HTTPx hook to check for authentication expiry."""

from __future__ import annotations

from typing import TYPE_CHECKING, Callable

from canfar import get_logger
from canfar.auth import x509
from canfar.exceptions.context import AuthExpiredError

log = get_logger(__name__)

if TYPE_CHECKING:
    from collections.abc import Awaitable

    import httpx

    from canfar.client import HTTPClient


def _check_expiry(client: HTTPClient) -> None:
    """Shared expiry-check core for both sync and async hooks.

    Raises:
        AuthExpiredError: if the saved Authentication Record is expired or its
            X.509 certificate cannot be loaded.
    """
    if client.uses_runtime_credentials:
        log.debug(
            "Skipping saved Authentication Record expiry check; "
            "runtime credentials are active."
        )
        return

    try:
        expired = client.config.context.expired
    except x509.CertificateError as err:
        raise AuthExpiredError(
            context=client.config.context.mode, reason=str(err)
        ) from err

    if expired:
        raise AuthExpiredError(
            context=client.config.context.mode, reason="auth expired"
        )


def check(client: HTTPClient) -> Callable[[httpx.Request], None]:
    """Create a hook to check for authentication expiry.

    Args:
        client (HTTPClient): The CANFAR client.

    """

    def hook(request: httpx.Request) -> None:  # noqa: ARG001
        """Check if the active Authentication credential is expired.

        Args:
            request (httpx.Request): The request.

        Raises:
            AuthExpiredError: If the active Authentication credential is expired.

        """
        _check_expiry(client)

    return hook


def acheck(client: HTTPClient) -> Callable[[httpx.Request], Awaitable[None]]:
    """Create an async hook to check for authentication expiry.

    This returns an async callable suitable for httpx's async event hooks.

    Args:
        client (HTTPClient): The CANFAR client.
    """

    async def hook(request: httpx.Request) -> None:  # noqa: ARG001
        """Check if the active Authentication credential is expired.

        Args:
            request (httpx.Request): The request.

        Raises:
            AuthExpiredError: If the active Authentication credential is expired.
        """
        # No await needed: _check_expiry is synchronous; async is only required
        # by the httpx async event-hook signature.
        _check_expiry(client)

    return hook
