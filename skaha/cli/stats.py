"""CLI command to display cluster statistics."""

from __future__ import annotations

import asyncio
from typing import Annotated

import typer
from rich import box
from rich.console import Console
from rich.table import Table

from skaha.session import AsyncSession

console = Console()

stats = typer.Typer(
    name="stats",
    help="Display cluster-wide statistics.",
    no_args_is_help=False,
)


@stats.callback(invoke_without_command=True)
def get_stats(
    debug: Annotated[
        bool,
        typer.Option(
            "--debug",
            help="Enable debug logging.",
        ),
    ] = False,
) -> None:
    """Display cluster-wide usage and status statistics."""

    async def _get_stats() -> None:
        log_level = "DEBUG" if debug else "INFO"
        async with AsyncSession(loglevel=log_level) as session:
            data = await session.stats()

        # Main table
        table = Table(
            title="Skaha Cluster Usage Statistics",
            box=box.SIMPLE,
            show_header=True,
            header_style="bold blue",
        )
        table.add_column("Instances", justify="center")
        table.add_column("CPU", justify="center")
        table.add_column("RAM", justify="center")

        # Nested table for Instances
        instances = data.get("instances", {})
        instances_table = Table(box=box.MINIMAL, show_header=False)
        instances_table.add_column("Kind", justify="left")
        instances_table.add_column("Count", justify="left")
        # Change DesktopApp to Desktop in the instances table
        if "desktopApp" in instances:
            instances["Desktops"] = instances.pop("desktopApp")

        for key, value in instances.items():
            if key == "total":
                pass
            else:
                instances_table.add_row(key.capitalize(), str(value))
        if "total" in instances:
            instances_table.add_row(
                "Total", str(instances["total"]), style="bold italic"
            )

        # Nested table for Cores
        cores = data.get("cores", {})
        cores_table = Table(box=box.MINIMAL, show_header=False)
        cores_table.add_column("Metric", justify="left")
        cores_table.add_column("Value", justify="left")
        cores_table.add_row("Requested", f"{cores.get('requestedCPUCores', 'N/A')}")
        cores_table.add_row("Available", f"{cores.get('cpuCoresAvailable', 'N/A')}")

        # Nested table for RAM
        ram = data.get("ram", {})
        ram_table = Table(box=box.MINIMAL, show_header=False)
        ram_table.add_column("Metric", justify="left")
        ram_table.add_column("Value", justify="left")
        ram_table.add_row("Requested", f"{ram.get('requestedRAM', 'N/A')}")
        ram_table.add_row("Available", f"{ram.get('ramAvailable', 'N/A')}")

        # Add the first row with nested tables
        table.add_row(instances_table, cores_table, ram_table)

        # Add the second row with max session size
        max_cpu = cores.get("maxCPUCores", {}).get("cpuCores", "N/A")
        max_ram = ram.get("maxRAM", {}).get("ram", "N/A")
        console.print(table)
        console.print(
            f"[bold]Maximum Requests Size:[/bold] {max_cpu} Cores or {max_ram} RAM"
        )
        console.print(
            "[dim]Based on best-case scenario, and may not be achievable.[/dim]"
        )

    asyncio.run(_get_stats())
