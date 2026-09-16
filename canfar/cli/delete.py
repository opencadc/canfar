"""CLI command to delete canfar sessions."""

from __future__ import annotations

from typing import Annotated

import typer
from rich.prompt import Confirm

from canfar.cli._run import run
from canfar.sessions import AsyncSession
from canfar.utils.console import emit_cli_active_server_banner, get_console


def delete_sessions(
    session_ids: Annotated[
        list[str],
        typer.Argument(help="One or more session IDs to delete."),
    ],
    force: Annotated[
        bool,
        typer.Option(
            "--force",
            "-f",
            help="Force deletion without confirmation.",
        ),
    ] = False,
) -> None:
    """Delete sessions by ID.

    Examples:
    canfar delete abc123
    canfar delete abc123 def456
    """
    emit_cli_active_server_banner()
    if force:
        proceed: bool = True
    else:
        proceed = Confirm.ask(
            f"Confirm deletion of {len(session_ids)} session(s)?",
            console=get_console(),
            default=False,
        )

    async def _delete() -> None:
        """Delete the requested sessions from the science platform server."""
        async with AsyncSession() as session:
            try:
                deleted = await session.destroy(ids=session_ids)
                get_console().print(
                    f"[bold green]Successfully deleted {deleted} "
                    f"session(s).[/bold green]"
                )
            except Exception as err:  # noqa: BLE001
                get_console(stderr=True).print(
                    f"[bold red]Error during deletion: {err}[/bold red]"
                )

    if proceed:
        run(_delete())
