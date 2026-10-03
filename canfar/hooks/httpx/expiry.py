"""HTTPX2 hook to check for authentication expiry."""

from __future__ import annotations

import logging
from functools import partial
from typing import TYPE_CHECKING, Callable

from canfar.auth import x509
from canfar.exceptions.context import AuthExpiredError

log = logging.getLogger(__name__)

if TYPE_CHECKING:
    from collections.abc import Awaitable

    from httpx2 import Request

    from canfar.client import HTTPClient


def _check_expiry(client: HTTPClient, _request: Request) -> None:
    """Reject a request whose saved Authentication Record is expired.

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

    credential = client.authentication_record
    if credential is None:
        return

    try:
        expired = credential.expired
    except x509.CertificateError as err:
        raise AuthExpiredError(context=credential.idp, reason=str(err)) from err

    if expired:
        reason = (
            "X.509 certificate expired."
            if credential.mode == "x509"
            else "OIDC access token expired."
        )
        raise AuthExpiredError(context=credential.idp, reason=reason)


async def _acheck_expiry(client: HTTPClient, request: Request) -> None:
    """Run the expiry check as an httpx2 async event hook."""
    _check_expiry(client, request)


def check(client: HTTPClient) -> Callable[[Request], None]:
    """Create a request hook that rejects expired saved credentials.

    Args:
        client (HTTPClient): The CANFAR client.
    """
    return partial(_check_expiry, client)


def acheck(client: HTTPClient) -> Callable[[Request], Awaitable[None]]:
    """Create an async request hook that rejects expired saved credentials.

    Args:
        client (HTTPClient): The CANFAR client.
    """
    return partial(_acheck_expiry, client)
