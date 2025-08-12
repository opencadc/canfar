"""CLI command to list canfar sessions."""

from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from typing import Annotated, get_args

import click
import humanize
import typer
from rich import box
from rich.console import Console
from rich.table import Table

from canfar.hooks.typer.aliases import AliasGroup
from canfar.models.session import FetchResponse
from canfar.models.types import Kind, Status
from canfar.sessions import AsyncSession

console = Console()

ps = typer.Typer(
    name="ps",
    no_args_is_help=False,
    cls=AliasGroup,
)


@ps.callback(invoke_without_command=True)
def show(
    everything: Annotated[
        bool,
        typer.Option(
            "--all", "-a", help="Show all sessions (default shows just running)."
        ),
    ] = False,
    quiet: Annotated[
        bool,
        typer.Option("--quiet", "-q", help="Only show session IDs."),
    ] = False,
    kind: Annotated[
        Kind | None,
        typer.Option(
            "--kind",
            "-k",
            click_type=click.Choice(list(get_args(Kind)), case_sensitive=True),
            metavar="|".join(get_args(Kind)),
            help="Filter by session kind.",
        ),
    ] = None,
    status: Annotated[
        Status | None,
        typer.Option(
            "--status",
            "-s",
            click_type=click.Choice(list(get_args(Status)), case_sensitive=True),
            metavar="|".join(get_args(Status)),
            help="Filter by session status.",
        ),
    ] = None,
    debug: Annotated[
        bool,
        typer.Option(
            "--debug",
            help="Enable debug logging.",
        ),
    ] = False,
) -> None:
    """Show sessions."""

    async def _list_sessions() -> None:
        """Asynchronous function to list sessions."""
        log_level = "DEBUG" if debug else "INFO"
        async with AsyncSession(loglevel=log_level) as session:
            sessions: list[FetchResponse] = []
            sessions = [
                FetchResponse.model_validate(item)
                for item in await session.fetch(kind=kind, status=status)
            ]
        sessions = sorted(sessions, key=lambda x: x.startTime, reverse=False)

        if quiet:
            for instance in sessions:
                console.print(instance.id)
            return

        table = Table(title="CANFAR Sessions", box=box.SIMPLE)
        table.add_column("SESSION ID", style="cyan")
        table.add_column("NAME", style="magenta")
        table.add_column("KIND", style="green")
        table.add_column("STATUS", style="green")
        table.add_column("IMAGE", style="blue")
        table.add_column("CREATED", style="yellow")

        running = 0
        for instance in sessions:
            if not everything and instance.status not in ["Pending", "Running"]:
                continue
            running += 1
            uptime = datetime.now(timezone.utc) - instance.startTime
            # Convert uptime to human readable format using strftime
            created = humanize.naturaldelta(uptime)

            table.add_row(
                instance.id,
                instance.name,
                instance.type,
                instance.status,
                instance.image,
                created,
            )

        if running == 0 and not everything:
            console.print("[yellow]No pending or running sessions found.[/yellow]")
            console.print("[dim]Use [italic]--all[/italic] to show all sessions.[/dim]")
        else:
            console.print(table)

    asyncio.run(_list_sessions())
