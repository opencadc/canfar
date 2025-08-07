"""Command Line Interface for Science Platform."""

from __future__ import annotations

import typer
from rich.console import Console

from skaha.cli.auth import auth
from skaha.cli.config import config
from skaha.cli.create import create
from skaha.cli.delete import delete
from skaha.cli.events import events
from skaha.cli.info import info
from skaha.cli.logs import logs
from skaha.cli.open import open_command
from skaha.cli.prune import prune
from skaha.cli.ps import ps
from skaha.cli.stats import stats
from skaha.cli.version import version
from skaha.exceptions.context import AuthContextError
from skaha.hooks.typer.aliases import AliasGroup

console = Console()


def callback(ctx: typer.Context) -> None:
    """Main callback that handles no subcommand case."""
    if ctx.invoked_subcommand is None:
        # No subcommand was invoked, show help and exit cleanly
        console.print(ctx.get_help())
        raise typer.Exit(0)


cli: typer.Typer = typer.Typer(
    name="skaha",
    help="Command Line Interface for Science Platform.",
    no_args_is_help=False,  # Disable automatic help to handle manually
    add_completion=True,
    pretty_exceptions_show_locals=True,
    pretty_exceptions_enable=True,
    pretty_exceptions_short=True,
    epilog="For more information, visit https://shinybrar.github.io/skaha/latest/",
    rich_markup_mode="rich",
    rich_help_panel="Skaha CLI Commands",
    callback=callback,
    invoke_without_command=True,  # Allow callback to be called without subcommand
    cls=AliasGroup,
)

cli.add_typer(
    auth,
    name="auth",
    help="Authenticate with Science Platform",
    no_args_is_help=True,
    rich_help_panel="Auth Management",
)

cli.add_typer(
    create,
    no_args_is_help=True,
    rich_help_panel="Session Management",
)

cli.add_typer(
    ps,
    no_args_is_help=False,
    rich_help_panel="Session Management",
)
cli.add_typer(
    events,
    no_args_is_help=False,
    rich_help_panel="Session Management",
)

cli.add_typer(
    info,
    help="Show session info",
    no_args_is_help=False,
    rich_help_panel="Session Management",
)

cli.add_typer(
    open_command,
    name="open",
    help="Open sessions in a browser",
    no_args_is_help=True,
    rich_help_panel="Session Management",
)

cli.add_typer(
    logs,
    help="Show session logs",
    no_args_is_help=False,
    rich_help_panel="Session Management",
)

cli.add_typer(
    delete,
    no_args_is_help=True,
    rich_help_panel="Session Management",
)

cli.add_typer(
    prune,
    no_args_is_help=True,
    rich_help_panel="Session Management",
)

cli.add_typer(
    create,
    name="run | launch",
    help="Aliases for create.",
    no_args_is_help=True,
    rich_help_panel="Aliases",
)

cli.add_typer(
    ps,
    name="get | ls | ps",
    help="Aliases for ps.",
    no_args_is_help=False,
    rich_help_panel="Aliases",
)

cli.add_typer(
    delete,
    name="del | rm",
    help="Aliases for delete.",
    no_args_is_help=True,
    rich_help_panel="Aliases",
)

cli.add_typer(
    stats,
    help="Show cluster stats",
    no_args_is_help=False,
    rich_help_panel="Cluster Information",
)


cli.add_typer(
    config,
    name="config",
    help="Manage client config",
    no_args_is_help=True,
    rich_help_panel="Client Info",
)
cli.add_typer(
    version,
    name="version",
    help="View client info",
    no_args_is_help=False,
    rich_help_panel="Client Info",
)


def main() -> None:
    """Main entry point."""
    try:
        cli()
    except AuthContextError as err:
        console.print(err)


if __name__ == "__main__":
    main()
