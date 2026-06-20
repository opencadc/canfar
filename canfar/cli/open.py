"""CLI command to open canfar sessions in a web browser."""

from __future__ import annotations

import webbrowser
from typing import Annotated

import typer

from canfar.cli._run import run
from canfar.cli.machine import maybe_emit_banner
from canfar.cli.output import OutputMode
from canfar.sessions import AsyncSession

open_command = typer.Typer(
    name="open",
    help="Open sessions in a browser.",
    no_args_is_help=True,
)


@open_command.callback(invoke_without_command=True)
def open_sessions(
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
    """Open one or more sessions in a web browser."""
    maybe_emit_banner(OutputMode.HUMAN)

    async def _open_sessions() -> None:
        """Look up the requested sessions and open their connect URLs."""
        log_level = "DEBUG" if debug else "INFO"
        async with AsyncSession(loglevel=log_level) as session:
            sessions_info = await session.info(ids=session_ids)
        if not sessions_info:
            typer.echo("No information found for the specified session(s).")
            return

        for session_info in sessions_info:
            connect_url = session_info.get("connectURL")
            if connect_url:
                webbrowser.open_new_tab(connect_url)
                typer.echo(f"Opening session {session_info.get('id')} in a new tab.")
            else:
                typer.echo(f"No connectURL found for session {session_info.get('id')}.")

    run(_open_sessions())
