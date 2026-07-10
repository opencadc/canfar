"""Discover Canfar Server endpoints from IVOA registries."""

from __future__ import annotations

import time

import httpx
from typing_extensions import Self

from canfar.models.registry import (
    IVOARegistry,
    IVOARegistrySearch,
    Server,
)
from canfar.utils.console import get_console


class Discover:
    """Optimized server discovery with single HTTP client and Pydantic models."""

    def __init__(self, config: IVOARegistrySearch, timeout: int = 2) -> None:
        """Initialize registry discovery."""
        self.config = config
        self.client = httpx.AsyncClient(
            timeout=httpx.Timeout(timeout),
            http2=True,
            follow_redirects=True,
        )

    async def __aenter__(self) -> Self:
        """Async context manager entry method.

        Returns:
            Discover: The instance of this class.
        """
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: object,
    ) -> None:
        """Async context manager exit method - cleans up HTTP client.

        Args:
            exc_type: The exception type if an exception was raised in the context.
            exc_val: The exception value if an exception was raised in the context.
            exc_tb: The traceback if an exception was raised in the context.
        """
        await self.client.aclose()

    async def fetch(self, url: str, name: str) -> IVOARegistry:
        """Fetch registry contents.

        Args:
            url (str): Registry URL.
            name (str): Common name for the registry.

        Returns:
            RegistryInfo: Registry information.
        """
        try:
            start_time = time.time()
            response = await self.client.get(url)
            response.raise_for_status()
            elapsed = time.time() - start_time
            get_console(stderr=True).print(
                f"[dim]Fetched {name} in {elapsed:.2f}s[/dim]"
            )

            return IVOARegistry(name=name, content=response.text, success=True)
        except httpx.HTTPError as error:
            error_msg = str(error)
            return IVOARegistry(name=name, content="", success=False, error=error_msg)

    def extract(self, registry: IVOARegistry, dev: bool = False) -> list[Server]:
        """Extract capabilities endpoints from registry content."""
        if not registry.success or not registry.content:
            return []

        endpoints: list[Server] = []

        for entry in registry.content.splitlines():
            line = entry.strip()
            if line.startswith("#") or not line or "=" not in line:
                continue

            uri, url = line.split("=", 1)
            uri, url = uri.strip(), url.strip()

            if url.endswith("/skaha/capabilities") and uri.endswith("/skaha"):
                url = url.replace("/capabilities", "")
                # Apply exclusion filters
                if not dev and any(
                    word in uri.lower() or word in url.lower()
                    for word in self.config.excluded
                ):
                    continue

                # Apply omit filters
                if (registry.name, uri) in self.config.omit:
                    continue
                endpoint = Server(
                    registry=registry.name,
                    uri=uri,
                    url=url,
                    name=self.config.names.get(uri),
                )
                endpoints.append(endpoint)

        return endpoints

    async def check(self, endpoint: Server) -> Server:
        """Check endpoint status using HEAD request."""
        try:
            response = await self.client.head(endpoint.url)
            endpoint.status = response.status_code
        except httpx.HTTPError:
            endpoint.status = None
        return endpoint
