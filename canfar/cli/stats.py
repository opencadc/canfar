"""CLI command to display cluster statistics."""

from __future__ import annotations

import typer
from rich import box
from rich.table import Table

from canfar.cli._run import run
from canfar.cli.machine import maybe_emit_banner
from canfar.cli.output import OutputMode
from canfar.sessions import AsyncSession
from canfar.utils.console import get_console

stats = typer.Typer(
    name="stats",
    help="Display cluster-wide statistics.",
    no_args_is_help=False,
)


@stats.callback(invoke_without_command=True)
def get_stats() -> None:
    """Display cluster-wide usage and status statistics."""
    maybe_emit_banner(OutputMode.HUMAN)

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

        # Add the first row with nested tables
        table.add_row(cores_table, ram_table)

        get_console().print(table)
        get_console().print(
            "[bold]Maximum Requests Size:[/bold] 16 Cores & 192.0 GB RAM"
        )
        get_console(stderr=True).print(
            "[dim]Based on best-case scenario, and may not be achievable.[/dim]"
        )

    run(_get_stats())
