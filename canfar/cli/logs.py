"""CLI command to get logs for canfar sessions."""

from __future__ import annotations

from typing import Annotated

import typer

from canfar.cli._run import run
from canfar.cli.machine import maybe_emit_banner
from canfar.cli.output import OutputMode
from canfar.sessions import AsyncSession
from canfar.utils.console import get_console

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
) -> None:
    """Get logs from the science platform server."""
    maybe_emit_banner(OutputMode.HUMAN)

    async def _get_logs() -> None:
        """Fetch logs for the requested sessions and render them."""
        async with AsyncSession() as session:
            try:
                all_logs = await session.logs(ids=session_ids)
            except Exception as e:
                get_console(stderr=True).print(
                    f"[bold red]Error:[/bold red] Could not fetch logs. {e}"
                )
                raise typer.Exit(1) from e

        if not all_logs:
            get_console(stderr=True).print(
                "[yellow]No logs found for the specified session(s).[/yellow]"
            )
            return

        for session_id, log_text in all_logs.items():
            get_console().print(
                f"\n[bold magenta] Logs for session {session_id} [/bold magenta]\n"
            )
            get_console().print(log_text)

    run(_get_logs())
