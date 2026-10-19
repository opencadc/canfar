"""CLI command to display cluster statistics."""

from __future__ import annotations

import asyncio

from rich import box
from rich.table import Table

from canfar.models.config import Configuration
from canfar.sessions import AsyncSession
from canfar.utils.console import emit_cli_active_server_banner, get_console


def get_stats() -> None:
    """Display cluster-wide usage and status statistics."""
    emit_cli_active_server_banner()

    async def _get_stats() -> None:
        """Fetch cluster-wide statistics and render them."""
        async with AsyncSession() as session:
            data = await session.stats()

        # Main table
        table = Table(
            title="CANFAR Platform Load",
            box=box.SIMPLE,
            show_header=True,
            header_style="bold blue",
        )

        table.add_column("CPU", justify="center")
        table.add_column("RAM", justify="center")

        # Nested table for Cores
        cores = data.get("cores", {})
        cores_table = Table(box=box.MINIMAL, show_header=False)
        cores_table.add_column("Metric", justify="left")
        cores_table.add_column("Value", justify="left")
        cores_table.add_row("Usage", f"{int(cores.get('requestedCPUCores', -1))}")
        cores_table.add_row("Total", f"{int(cores.get('cpuCoresAvailable', -1))}")

        # Nested table for RAM
        ram = data.get("ram", {})
        ram_table = Table(box=box.MINIMAL, show_header=False)
        ram_table.add_column("Metric", justify="left")
        ram_table.add_column("Value", justify="left")
        ram_table.add_row("Usage", f"{ram.get('requestedRAM', 'N/A')}")
        ram_table.add_row("Total", f"{ram.get('ramAvailable', 'N/A')}")

        columns = [cores_table, ram_table]
        if "gpu" in data:
            gpu = data["gpu"]
            table.add_column("GPU", justify="center")
            gpu_table = Table(box=box.MINIMAL, show_header=False)
            gpu_table.add_column("Metric", justify="left")
            gpu_table.add_column("Value", justify="left")
            gpu_table.add_row("Usage", str(gpu.get("requestedGPU", "N/A")))
            gpu_table.add_row("Total", str(gpu.get("gpuAvailable", "N/A")))
            columns.append(gpu_table)
        table.add_row(*columns)

        get_console().print(table)
        config = Configuration()  # ty: ignore[missing-argument]
        server = config.servers.get(config.active.server or "")
        resources = server.resources if server is not None else None
        get_console().print("\n[bold]Maximum Resource Requests[/bold]\n")
        for label, mode in (
            ("Fixed", resources.fixed if resources is not None else None),
            ("Flexible", resources.flexible if resources is not None else None),
        ):
            if mode is None:
                get_console().print(f"{label}: unknown")
                continue
            max_cores = mode.cores.max if mode.cores is not None else "unknown"
            max_ram = mode.ram.max if mode.ram is not None else "unknown"
            get_console().print(f"{label}: {max_cores} Cores & {max_ram} GB")

    asyncio.run(_get_stats())
