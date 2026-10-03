"""Discover Canfar Server endpoints from IVOA registries."""

from __future__ import annotations

import logging
import time
from urllib.parse import urlsplit, urlunsplit

from httpx2 import AsyncClient, HTTPError, Timeout, TimeoutException

from canfar.models.registry import IVOARegistry, Server

log = logging.getLogger(__name__)

NAMES: dict[str, str] = {
    "ivo://canfar.net/src/skaha": "canSRC",
    "ivo://swesrc.chalmers.se/skaha": "sweSRC",
    "ivo://canfar.cam.uksrc.org/skaha": "ukCAM",
    "ivo://canfar.ral.uksrc.org/skaha": "ukRAL",
    "ivo://src.skach.org/skaha": "chSRC",
    "ivo://espsrc.iaa.csic.es/skaha": "espSRC",
    "ivo://canfar.itsrc.oact.inaf.it/skaha": "itaINAF",
    "ivo://shion-sp.mtk.nao.ac.jp/skaha": "jpSRC",
    "ivo://canfar.krsrc.kr/skaha": "krSRC",
    "ivo://canfar.ska.zverse.space/skaha": "cnSRC",
    "ivo://canfar.itsrc.ext.cineca.it/skaha": "itCINECA",
    "ivo://canfar.srcnet.skao.int/skaha": "skaSRC",
    "ivo://aussrc.org/skaha": "ausSRC",
    "ivo://cadc.nrc.ca/skaha": "canfar",
}
"""Server Names for known Science Platform URIs."""

OMIT = frozenset({("CADC", "ivo://canfar.net/src/skaha")})
"""(registry name, URI) records that discovery skips."""

DEVELOPMENT_MARKERS = (
    "dev",
    "development",
    "test",
    "demo",
    "stage",
    "staging",
    "rc-",
    "preprod",
)
"""URI or URL fragments that mark a development record."""


def client(timeout: int) -> AsyncClient:
    """Return the HTTP client that registry fetches and checks share."""
    return AsyncClient(timeout=Timeout(timeout), http2=True, follow_redirects=True)


async def fetch(
    http: AsyncClient,
    url: str,
    name: str,
    *,
    development: bool = False,
) -> IVOARegistry:
    """Fetch registry contents.

    Args:
        http: Shared discovery HTTP client.
        url: Registry URL.
        name: Common name for the registry.
        development: Whether this source contains development records.

    Returns:
        IVOARegistry: Registry contents, or the error when the fetch failed.
    """
    try:
        start_time = time.time()
        response = await http.get(url)
        response.raise_for_status()
        log.info("Fetched %s in %.2fs", name, time.time() - start_time)
    except HTTPError as error:
        return IVOARegistry(
            name=name,
            source=url,
            development=development,
            content="",
            success=False,
            error=str(error),
        )
    return IVOARegistry(
        name=name,
        source=url,
        development=development,
        content=response.text,
    )


def extract(
    registry: IVOARegistry,
    *,
    leaf: str | None,
    dev: bool = False,
) -> list[Server]:
    """Extract Science Platform and preferred VOSpace registry records.

    Args:
        registry: Fetched registry contents.
        leaf: Preferred VOSpace URI leaf for the Identity Provider.
        dev: Keep development records.

    Returns:
        list[Server]: Science Platform (``skaha``) and ``leaf`` records.
    """
    if not registry.success:
        return []

    endpoints: list[Server] = []
    for entry in registry.content.splitlines():
        line = entry.strip()
        if line.startswith("#") or "=" not in line:
            continue

        uri, url = (part.strip() for part in line.split("=", 1))
        record_leaf = uri.rpartition("/")[2]
        if record_leaf not in {"skaha", leaf}:
            continue
        base = _without_terminal_capabilities(url)
        if base is None or (registry.name, uri) in OMIT:
            continue
        development = any(
            marker in uri.lower() or marker in base.lower()
            for marker in DEVELOPMENT_MARKERS
        )
        if development and not dev:
            continue
        endpoints.append(
            Server(
                registry=registry.source or registry.name,
                development=registry.development or development,
                uri=uri,
                url=base,
                name=NAMES.get(uri) if record_leaf == "skaha" else None,
            )
        )
    return endpoints


async def check(http: AsyncClient, endpoint: Server) -> Server:
    """Record the endpoint's ``HEAD`` status, or why no response arrived."""
    try:
        response = await http.head(endpoint.url)
        endpoint.status = response.status_code
    except TimeoutException:
        endpoint.status = None
        endpoint.failure = "timeout"
    except HTTPError:
        endpoint.status = None
        endpoint.failure = "unreachable"
    return endpoint


def _without_terminal_capabilities(url: str) -> str | None:
    """Remove only a terminal ``/capabilities`` path component."""
    parsed = urlsplit(url)
    if not parsed.path.endswith("/capabilities"):
        return None
    return urlunsplit(parsed._replace(path=parsed.path.removesuffix("/capabilities")))
