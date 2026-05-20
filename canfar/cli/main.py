"""Command Line Interface for Science Platform."""

from __future__ import annotations

import typer

from canfar.cli.auth import auth
from canfar.cli.config import config
from canfar.cli.create import create
from canfar.cli.delete import delete
from canfar.cli.events import events
from canfar.cli.image import image
from canfar.cli.info import info
from canfar.cli.logs import logs
from canfar.cli.open import open_command
from canfar.cli.prune import prune
from canfar.cli.ps import ps
from canfar.cli.stats import stats
from canfar.cli.version import version
from canfar.cli.storage import storage_cli
from canfar.exceptions.context import AuthContextError, AuthExpiredError
from canfar.hooks.typer.aliases import AliasGroup
from canfar.utils.console import console


def callback(ctx: typer.Context) -> None:
    """Main callback that handles no subcommand case."""
    if ctx.invoked_subcommand is None:
        # No subcommand was invoked, show help and exit cleanly
        console.print(ctx.get_help())
        raise typer.Exit(0)


cli: typer.Typer = typer.Typer(
    name="canfar",
    help="CANFAR Science Platform",
    no_args_is_help=False,  # Disable automatic help to handle manually
    add_completion=True,
    pretty_exceptions_show_locals=True,
    pretty_exceptions_enable=True,
    pretty_exceptions_short=True,
    epilog="For more information, visit https://opencadc.github.io/canfar/latest/",
    rich_markup_mode="rich",
    rich_help_panel="CANFAR CLI Commands",
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

# Aliases

cli.add_typer(
    create,
    name="run | launch",
    help="Aliases for create.",
    no_args_is_help=True,
    rich_help_panel="Aliases",
)

cli.add_typer(
    delete,
    name="del",
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
    image,
    name="image",
    help="Manage images",
    no_args_is_help=True,
    rich_help_panel="Image Management",
)

cli.add_typer(
    storage_cli,
    name="storage",
    help="Manage files in Cavern storage",
    no_args_is_help=True,
    rich_help_panel="File Management",
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
    except AuthExpiredError as err:
        console.print(err)
        console.print("Authenticate with [italic cyan] canfar auth login[/italic cyan]")
    except AuthContextError as err:
        console.print(err)


if __name__ == "__main__":
    main()
