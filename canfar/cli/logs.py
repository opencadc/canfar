"""CLI command to get logs for canfar sessions."""

from __future__ import annotations

import asyncio
from typing import Annotated

import typer
from httpx2 import HTTPError, HTTPStatusError
from rich.errors import MarkupError
from rich.markup import escape

from canfar.exceptions.session import SessionRequestError
from canfar.sessions import AsyncSession
from canfar.utils.console import emit_cli_active_server_banner, get_console


def _failure(error: HTTPError) -> str:
    """Describe one failed log request with the Server's status and reason."""
    if not isinstance(error, HTTPStatusError):
        return type(error).__name__
    reason = error.response.text.strip()
    return f"HTTP {error.response.status_code}" + (f": {reason}" if reason else "")


def get_logs(
    session_ids: Annotated[
        list[str],
        typer.Argument(help="One or more session IDs."),
    ],
    replica: Annotated[
        int | None,
        typer.Option(
            "--replica",
            help="Replica index of a batch, from 0. A batch needs it.",
            min=0,
        ),
    ] = None,
) -> None:
    """Get logs from the science platform server."""
    emit_cli_active_server_banner()

    async def _get_logs() -> None:
        """Fetch logs for the requested sessions and render them."""
        failures: dict[str | int, HTTPError] = {}
        async with AsyncSession(errors="raise") as session:
            try:
                all_logs = await session.logs(ids=session_ids, replica=replica)
            except SessionRequestError as err:
                all_logs, failures = err.results, err.errors
            except Exception as e:
                get_console(stderr=True).print(
                    f"[bold red]Error:[/bold red] Could not fetch logs. {e}"
                )
                raise typer.Exit(1) from e

        if not all_logs and not failures:
            get_console(stderr=True).print(
                "[yellow]No logs found for the specified session(s).[/yellow]"
            )
            return

        for session_id, log_text in (all_logs or {}).items():
            console = get_console()
            console.print(
                f"\n[bold magenta] Logs for session {session_id} [/bold magenta]\n"
            )
            try:
                rendered_logs = console.render_str(log_text)
            except MarkupError:
                rendered_logs = console.render_str(log_text, markup=False)
            console.print(rendered_logs)

        for session_id, error in failures.items():
            get_console(stderr=True).print(
                f"[bold red]Error:[/bold red] Could not fetch logs for session "
                f"{escape(str(session_id))}. {escape(_failure(error))}"
            )
        if failures:
            raise typer.Exit(1)

    asyncio.run(_get_logs())
