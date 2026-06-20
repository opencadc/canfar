"""CLI command to prune canfar sessions."""

from __future__ import annotations

from typing import TYPE_CHECKING, Annotated, get_args

import click
import typer
import typer.core

from canfar.cli._run import run
from canfar.cli.machine import maybe_emit_banner
from canfar.cli.output import OutputMode
from canfar.models.types import Pruneable, Status
from canfar.sessions import AsyncSession
from canfar.utils.console import console

if TYPE_CHECKING:
    from typer._click.core import Context


class PruneUsageMessage(typer.core.TyperGroup):
    """Custom usage message for prune command.

    Args:
        typer (TyperGroup): Base class for grouping commands in Typer.
    """

    def get_usage(self, ctx: Context) -> str:  # noqa: ARG002
        """Get the usage message for the prune command.

        Args:
            ctx (typer.Context): The Typer context.

        Returns:
            str: The usage message.
        """
        return "Usage: canfar prune [OPTIONS] PREFIX KIND STATUS COMMAND [ARGS]..."


prune = typer.Typer(
    name="prune",
    no_args_is_help=True,
)


@prune.callback(
    invoke_without_command=True,
    context_settings={"help_option_names": ["-h", "--help"]},
    cls=PruneUsageMessage,
)
def prune_sessions(
    prefix: Annotated[
        str,
        typer.Argument(
            ...,
            help="Prefix or regex pattern to match session names.",
            metavar="PREFIX",
        ),
    ],
    kind: Annotated[
        Pruneable,
        typer.Argument(
            click_type=click.Choice(list(get_args(Pruneable)), case_sensitive=True),
            metavar="|".join(get_args(Pruneable)),
            help="Filter by session kind.",
        ),
    ] = "headless",
    status: Annotated[
        Status,
        typer.Argument(
            click_type=click.Choice(list(get_args(Status)), case_sensitive=True),
            metavar="|".join(get_args(Status)),
            help="Filter by session status.",
        ),
    ] = "Succeeded",
    debug: Annotated[
        bool,
        typer.Option("--debug", help="Enable debug logging."),
    ] = False,
) -> None:
    """Delete sessions by criteria.

    Examples:
    canfar prune session-name headless Succeeded
    canfar prune session.* notebook Running
    """
    maybe_emit_banner(OutputMode.HUMAN)

    async def _prune() -> None:
        """Delete matching sessions from the science platform server."""
        log_level = "DEBUG" if debug else "INFO"
        async with AsyncSession(loglevel=log_level) as session:
            response = await session.destroy_with(
                prefix=prefix, kind=kind, status=status
            )
            console.print(
                f"[bold green] Deleted {len(response)} sessions.[/bold green]"
            )

    run(_prune())
