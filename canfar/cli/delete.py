"""CLI command to delete canfar sessions."""

from __future__ import annotations

import asyncio
from typing import Annotated

import typer
from rich.console import Console
from rich.prompt import Confirm

from canfar.hooks.typer.aliases import AliasGroup
from canfar.sessions import AsyncSession

console = Console()

delete = typer.Typer(
    name="delete",
    no_args_is_help=True,
    cls=AliasGroup,
)


@delete.callback(invoke_without_command=True)
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
    debug: Annotated[
        bool,
        typer.Option(
            "--debug",
            help="Enable debug logging.",
        ),
    ] = False,
) -> None:
    """Delete sessions by ID.

    Examples:
    canfar delete abc123
    canfar delete abc123 def456
    """
    if force:
        proceed: bool = True
    else:
        proceed = Confirm.ask(
            f"Confirm deletion of {len(session_ids)} session(s)?",
            console=console,
            default=False,
        )

    async def _delete() -> None:
        async with AsyncSession(loglevel="DEBUG" if debug else "INFO") as session:
            try:
                deleted = await session.destroy(ids=session_ids)
                console.print(
                    f"[bold green]Successfully deleted {deleted} "
                    f"session(s).[/bold green]"
                )
            except Exception as err:  # noqa: BLE001
                console.print(f"[bold red]Error during deletion: {err}[/bold red]")

    if proceed:
        asyncio.run(_delete())
