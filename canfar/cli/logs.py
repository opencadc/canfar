"""CLI command to get logs for canfar sessions."""

from __future__ import annotations

import asyncio
from typing import Annotated

import typer
from rich.errors import MarkupError

from canfar.sessions import AsyncSession
from canfar.utils.console import emit_cli_active_server_banner, get_console


def get_logs(
    session_ids: Annotated[
        list[str],
        typer.Argument(help="One or more session IDs."),
    ],
) -> None:
    """Get logs from the science platform server."""
    emit_cli_active_server_banner()

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
            console = get_console()
            console.print(
                f"\n[bold magenta] Logs for session {session_id} [/bold magenta]\n"
            )
            try:
                rendered_logs = console.render_str(log_text)
            except MarkupError:
                rendered_logs = console.render_str(log_text, markup=False)
            console.print(rendered_logs)

    asyncio.run(_get_logs())
