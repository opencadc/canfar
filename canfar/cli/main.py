"""Command Line Interface for Science Platform."""

from __future__ import annotations

from typing import Annotated

import typer

from canfar.cli._machine import output_mode_callback, reset_output_modes
from canfar.cli.auth import auth
from canfar.cli.config import config
from canfar.cli.context import context
from canfar.cli.create import create
from canfar.cli.delete import delete
from canfar.cli.events import events
from canfar.cli.image import image
from canfar.cli.info import info
from canfar.cli.login import register_login_command
from canfar.cli.logs import logs
from canfar.cli.open import open_command
from canfar.cli.output import OutputConflictError
from canfar.cli.prune import prune
from canfar.cli.ps import ps
from canfar.cli.server import server
from canfar.cli.stats import stats
from canfar.cli.version import version
from canfar.exceptions.context import AuthContextError, AuthExpiredError
from canfar.hooks.typer.aliases import AliasGroup
from canfar.utils.console import console


def callback(
    ctx: typer.Context,
    json_output: Annotated[
        bool,
        typer.Option("--json", help="Emit machine-readable JSON on stdout."),
    ] = False,
    yaml_output: Annotated[
        bool,
        typer.Option("--yaml", help="Emit machine-readable YAML on stdout."),
    ] = False,
) -> None:
    """Main callback that handles no subcommand case."""
    reset_output_modes()
    try:
        output_mode_callback(ctx, json_output, yaml_output)
    except OutputConflictError as exc:
        console.print(f"[bold red]{exc}[/bold red]")
        raise typer.Exit(exc.exit_code) from exc

    if ctx.invoked_subcommand is None:
        console.print(ctx.get_help())
        raise typer.Exit(0)


cli: typer.Typer = typer.Typer(
    name="canfar",
    help="CANFAR Science Platform",
    no_args_is_help=False,
    add_completion=True,
    pretty_exceptions_show_locals=True,
    pretty_exceptions_enable=True,
    pretty_exceptions_short=True,
    epilog="For more information, visit https://opencadc.github.io/canfar/latest/",
    rich_markup_mode="rich",
    rich_help_panel="CANFAR CLI Commands",
    callback=callback,
    invoke_without_command=True,
    cls=AliasGroup,
)

register_login_command(cli)

cli.add_typer(
    auth,
    name="auth",
    help="Manage Authentication state.",
    no_args_is_help=False,
    rich_help_panel="Auth Management",
)

cli.add_typer(
    auth,
    name="authentication",
    help="Alias for auth.",
    no_args_is_help=False,
    rich_help_panel="Aliases",
    hidden=True,
)

cli.add_typer(
    server,
    name="server",
    help="Manage Science Platform server selection.",
    no_args_is_help=True,
    rich_help_panel="Auth Management",
)

cli.add_typer(
    context,
    name="context",
    help="Inspect Authentication and Server routing state.",
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
    reset_output_modes()
    try:
        cli()
    except AuthExpiredError as err:
        console.print(err)
        console.print("Authenticate with [italic cyan]canfar login[/italic cyan]")
    except AuthContextError as err:
        console.print(err)
    finally:
        reset_output_modes()


if __name__ == "__main__":
    main()
