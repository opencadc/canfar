"""HTTPX2 hooks that log each response at INFO and full exchanges at DEBUG."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from canfar.utils.logging import safe_url

if TYPE_CHECKING:
    from httpx2 import Request, Response

log = logging.getLogger(__name__)


def request(req: Request) -> None:
    """Log the outgoing request method and URL."""
    log.debug("%s %s", req.method, req.url)


async def arequest(req: Request) -> None:
    """Log the outgoing request method and URL (async)."""
    log.debug("%s %s", req.method, req.url)


def _summary(resp: Response) -> None:
    """Log one line per response, without credentials or query values."""
    request = resp.request
    log.info("%s %s -> %s", request.method, safe_url(request.url), resp.status_code)


def response(resp: Response) -> None:
    """Log the response status at INFO, and its body at DEBUG."""
    _summary(resp)
    if not log.isEnabledFor(logging.DEBUG):
        return
    resp.read()
    log.debug("HTTP STATUS CODE -> %s\n%s", resp.status_code, resp.text)


async def aresponse(resp: Response) -> None:
    """Log the response status at INFO, and its body at DEBUG (async)."""
    _summary(resp)
    if not log.isEnabledFor(logging.DEBUG):
        return
    await resp.aread()
    log.debug("HTTP STATUS CODE -> %s\n%s", resp.status_code, resp.text)
