"""CLI command to open canfar sessions in a web browser."""

from __future__ import annotations

import webbrowser
from typing import Annotated

import typer

from canfar.cli._run import run
from canfar.sessions import AsyncSession, connection_url

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
) -> None:
    """Open one or more sessions in a web browser."""

    async def _open_sessions() -> None:
        """Look up the requested sessions and open their connect URLs."""
        async with AsyncSession() as session:
            sessions_info = await session.info(ids=session_ids)
        if not sessions_info:
            typer.echo("No information found for the specified session(s).", err=True)
            return

        for session_info in sessions_info:
            connect_url = connection_url(session_info)
            if connect_url:
                webbrowser.open_new_tab(connect_url)
                typer.echo(f"Opening session {session_info.get('id')} in a new tab.")
            elif session_info.get("connectURL"):
                typer.echo(
                    f"Session {session_info.get('id')} is not ready to connect "
                    f"(status: {session_info.get('status', 'unknown')}).",
                    err=True,
                )
            else:
                typer.echo(
                    f"No connectURL found for session {session_info.get('id')}.",
                    err=True,
                )

    run(_open_sessions())
