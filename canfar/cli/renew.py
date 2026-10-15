"""CLI command to renew canfar sessions."""

from __future__ import annotations

import asyncio
from typing import Annotated

import typer

from canfar.sessions import AsyncSession
from canfar.utils.console import emit_cli_active_server_banner, get_console


def renew_sessions(
    session_ids: Annotated[
        list[str],
        typer.Argument(help="One or more session IDs to renew."),
    ],
) -> None:
    """Renew sessions by ID.

    Examples:
    canfar renew abc123
    canfar renew abc123 def456
    """
    emit_cli_active_server_banner()

    async def _renew() -> None:
        """Renew the requested sessions on the science platform server."""
        async with AsyncSession(errors="ignore") as session:
            try:
                results = await session.renew(ids=session_ids)
                succeeded = [sid for sid, ok in results.items() if ok]
                failed = [sid for sid, ok in results.items() if not ok]
                if succeeded:
                    get_console().print(
                        f"[bold green]Successfully renewed {len(succeeded)} "
                        f"session(s).[/bold green]"
                    )
                if failed:
                    get_console(stderr=True).print(
                        f"[bold red]Failed to renew {len(failed)} "
                        f"session(s): {', '.join(failed)}[/bold red]"
                    )
            except Exception as err:  # noqa: BLE001
                get_console(stderr=True).print(
                    f"[bold red]Error during renewal: {err}[/bold red]"
                )

    asyncio.run(_renew())
