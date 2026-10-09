"""CLI command to prune canfar sessions."""

from __future__ import annotations

import asyncio
from typing import Annotated, get_args

import typer

from canfar.models.types import Pruneable, Status
from canfar.sessions import AsyncSession
from canfar.utils.console import emit_cli_active_server_banner, get_console


def prune_sessions(
    prefix: Annotated[
        str,
        typer.Argument(
            ...,
            help=(
                "Prefix or regex pattern to match session names. "
                "Quote patterns with shell metacharacters (e.g. '*', '?')."
            ),
            metavar="PREFIX",
        ),
    ],
    kind: Annotated[
        Pruneable,
        typer.Argument(
            metavar="|".join(get_args(Pruneable)),
            help="Filter by session kind.",
        ),
    ] = "headless",
    status: Annotated[
        Status,
        typer.Argument(
            metavar="|".join(get_args(Status)),
            help="Filter by session status.",
        ),
    ] = "Succeeded",
) -> None:
    """Delete sessions by criteria.

    Examples:
    canfar prune session-name headless Succeeded
    canfar prune 'session.*' notebook Running
    """
    emit_cli_active_server_banner()

    async def _prune() -> None:
        """Delete matching sessions from the science platform server."""
        async with AsyncSession(errors="ignore") as session:
            response = await session.destroy_with(
                prefix=prefix, kind=kind, status=status
            )
            get_console().print(
                f"[bold green] Deleted {len(response)} sessions.[/bold green]"
            )

    asyncio.run(_prune())
