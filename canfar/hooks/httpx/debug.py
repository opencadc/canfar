"""HTTPX2 hooks that log request URLs and response bodies at DEBUG."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from httpx2 import Request, Response

log = logging.getLogger(__name__)


def request(req: Request) -> None:
    """Log the outgoing request method and URL."""
    log.debug("%s %s", req.method, req.url)


async def arequest(req: Request) -> None:
    """Log the outgoing request method and URL (async)."""
    log.debug("%s %s", req.method, req.url)


def response(resp: Response) -> None:
    """Log the response status code and body."""
    if not log.isEnabledFor(logging.DEBUG):
        return
    resp.read()
    log.debug("HTTP STATUS CODE -> %s\n%s", resp.status_code, resp.text)


async def aresponse(resp: Response) -> None:
    """Log the response status code and body (async)."""
    if not log.isEnabledFor(logging.DEBUG):
        return
    await resp.aread()
    log.debug("HTTP STATUS CODE -> %s\n%s", resp.status_code, resp.text)
