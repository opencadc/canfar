"""CLI command to get events for canfar sessions."""

from __future__ import annotations

import asyncio
import re
from typing import Annotated

import typer
from rich import box
from rich.console import Console
from rich.table import Table

from canfar.sessions import AsyncSession

console = Console()

events = typer.Typer(
    name="events",
    help="List events for sessions.",
    no_args_is_help=False,
)


@events.callback(invoke_without_command=True)
def get_events(
    session_ids: Annotated[
        list[str],
        typer.Argument(help="One or more session IDs."),
    ],
    debug: Annotated[
        bool,
        typer.Option(
            "--debug",
            help="Enable debug logging.",
        ),
    ] = False,
) -> None:
    """Get events from the science platform server."""

    async def _get_events() -> None:
        log_level = "DEBUG" if debug else "INFO"
        async with AsyncSession(loglevel=log_level) as session:
            all_events = await session.events(ids=session_ids)

        if not all_events:
            console.print(
                "[yellow]No events found for the specified session(s).[/yellow]"
            )
            return

        for event in all_events:
            for session_id, event_text in event.items():
                table = Table(
                    title=f"[blue]Server events for [bold]{session_id}[/bold] [/blue]",
                    show_header=True,
                    header_style="bold magenta",
                    box=box.SIMPLE,
                )
                table.add_column("Type")
                table.add_column("Reason")
                table.add_column("Message")
                table.add_column("First-Seen")
                table.add_column("Last-Seen")

                # Split the event text into lines and skip the header
                lines = event_text.strip().split("\n")[1:]
                for line in lines:
                    # Use regex to split the line by multiple spaces
                    parts = re.split(r"\s{2,}", line)
                    if len(parts) == 5:
                        table.add_row(*parts)

                console.print(table)

    asyncio.run(_get_events())
