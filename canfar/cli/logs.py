"""CLI command to get logs for canfar sessions."""

from __future__ import annotations

import asyncio
from typing import Annotated

import typer
from rich.console import Console

from canfar.sessions import AsyncSession

console = Console()

logs = typer.Typer(
    name="logs",
    help="Get logs for sessions.",
    no_args_is_help=True,
)


@logs.callback(invoke_without_command=True)
def get_logs(
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
    """Get logs from the science platform server."""

    async def _get_logs() -> None:
        log_level = "DEBUG" if debug else "INFO"
        async with AsyncSession(loglevel=log_level) as session:
            try:
                all_logs = await session.logs(ids=session_ids)
            except Exception as e:
                console.print(f"[bold red]Error:[/bold red] Could not fetch logs. {e}")
                raise typer.Exit(1) from e

        if not all_logs:
            console.print(
                "[yellow]No logs found for the specified session(s).[/yellow]"
            )
            return

        for session_id, log_text in all_logs.items():
            console.print(
                f"\n[bold magenta] Logs for session {session_id} [/bold magenta]\n"
            )
            console.print(log_text)

    asyncio.run(_get_logs())
