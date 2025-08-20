"""Discover Canfar Server endpoints from IVOA registries."""

from __future__ import annotations

import asyncio
import time

import httpx
from rich.console import Console
from typing_extensions import Self

from canfar.models.registry import (
    IVOARegistry,
    IVOARegistrySearch,
    Server,
    ServerResults,
)
from canfar.utils import display


class Discover:
    """Optimized server discovery with single HTTP client and Pydantic models."""

    def __init__(
        self, config: IVOARegistrySearch, timeout: int = 2, max_connections: int = 100
    ) -> None:
        """Initialize with configuration and connection limits."""
        self.config = config
        self.timeout = timeout

        # Single HTTP client for all operations
        self.client = httpx.AsyncClient(
            timeout=httpx.Timeout(timeout),
            limits=httpx.Limits(
                max_keepalive_connections=max_connections,
                max_connections=max_connections,
                keepalive_expiry=30.0,
            ),
            http2=True,
            follow_redirects=True,
        )

        self.console = Console()

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
            self.console.print(f"[dim]Fetched {name} in {elapsed:.2f}s[/dim]")

            return IVOARegistry(name=name, content=response.text, success=True)
        except (httpx.HTTPError, httpx.TimeoutException, httpx.RequestError) as error:
            error_msg = str(error)
            self.console.print(f"[red]Failed to fetch {name}: {error_msg}[/red]")
            return IVOARegistry(name=name, content="", success=False, error=error_msg)

    async def extract(self, registry: IVOARegistry, dev: bool = False) -> list[Server]:
        """Extract capabilities endpoints from registry content asynchronously."""
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
        except (httpx.HTTPError, httpx.TimeoutException):
            endpoint.status = None
        return endpoint

    async def servers(self, dev: bool = False) -> ServerResults:
        """Discover all servers with maximum parallelization."""
        results = ServerResults()
        start_time = time.time()

        # Step 1: Fetch all registries in parallel
        registry_start = time.time()
        if dev:
            self.console.print("[dim] Retrieving dev registries...[/dim]")
            registry_tasks = [
                self.fetch(url, name) for url, name in self.config.registries.items()
            ]
        else:
            registry_tasks = [
                self.fetch(url, name)
                for url, name in self.config.registries.items()
                if "dev" not in name.lower()
            ]
        registry_results = await asyncio.gather(*registry_tasks)
        results.registry_fetch_time = time.time() - registry_start

        # Step 2: Extract all endpoints from all registries
        all_endpoints: list[Server] = []
        for registry_result in registry_results:
            endpoints = await self.extract(registry_result, dev)
            all_endpoints.extend(endpoints)
        results.found = len(all_endpoints)

        if not all_endpoints:
            results.total_time = time.time() - start_time
            return results

        # Step 3: Check all endpoints in parallel using single client
        check_start = time.time()
        checked_endpoints = await asyncio.gather(
            *[self.check(endpoint) for endpoint in all_endpoints]
        )
        results.endpoint_check_time = time.time() - check_start

        # Step 4: Add all endpoints to results
        for endpoint in checked_endpoints:
            results.add(endpoint)

        results.checked = len(checked_endpoints)
        results.total_time = time.time() - start_time

        self.console.print(
            f"[bold green]Discovery completed in {results.total_time:.2f}s "
            f"({results.successful}/{results.checked} active)[/bold green]"
        )

        return results


async def servers(
    dev: bool = False,
    dead: bool = False,
    details: bool = False,
    timeout: int = 3,
) -> Server:
    """Find and select a Canfar Server.

    Args:
        dev: Include development servers. Defaults to False.
        dead: Show only inactive endpoints (status=None). Defaults to False.
        details: Show detailed URI and URL information. Defaults to False.
        timeout: HTTP request timeout. Defaults to 2.

    Returns:
        ServerInfo: The selected server info.
    """
    config = IVOARegistrySearch()

    async with Discover(config, timeout=timeout, max_connections=100) as discovery:
        results = await discovery.servers(dev=dev)
        return await display.servers(results, show_dead=dead, show_details=details)


if __name__ == "__main__":
    # Test with active endpoints and details
    server = asyncio.run(servers())
