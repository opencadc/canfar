"""Command Line Interface for Science Platform."""

from __future__ import annotations

from pathlib import Path  # noqa: TC003 - Typer resolves callback annotations at runtime
from typing import TYPE_CHECKING, Annotated

import typer

from canfar.cli import output
from canfar.cli.auth import auth
from canfar.cli.config import config
from canfar.cli.create import create
from canfar.cli.data import data
from canfar.cli.delete import delete
from canfar.cli.events import events
from canfar.cli.image import image
from canfar.cli.info import info
from canfar.cli.login import register_login_command
from canfar.cli.logs import logs
from canfar.cli.open import open_command
from canfar.cli.prune import prune
from canfar.cli.ps import ps
from canfar.cli.server import server
from canfar.cli.stats import stats
from canfar.cli.version import version
from canfar.config.migration import ConfigResetRequiredError
from canfar.exceptions.context import AuthContextError, AuthExpiredError
from canfar.hooks.typer.aliases import (
    ROOT_CHILD_ARGS_META_KEY,
    AliasGroup,
    set_before_command,
)
from canfar.utils.console import emit_active_server_banner, get_console
from canfar.utils.logging import (
    InvalidLogFilePathError,
    InvalidLoggingEnvironmentError,
    LoggingLevel,
    configure_logging,
)

if TYPE_CHECKING:
    from collections.abc import Mapping

    from canfar.errors import StructuredError


def _leaf_output_mode(args: list[str]) -> output.OutputMode:
    """Infer an already-parsed leaf machine flag for root setup failures."""
    if "--json" in args:
        return output.OutputMode.JSON
    if "--yaml" in args:
        return output.OutputMode.YAML
    return output.OutputMode.HUMAN


def _emit_banner_for_command(params: Mapping[str, object]) -> None:
    """Emit the active-server banner for a parsed human-output command."""
    if params.get("json_output") or params.get("yaml_output"):
        return
    emit_active_server_banner()


def callback(
    ctx: typer.Context,
    log_level: Annotated[
        LoggingLevel | None,
        typer.Option(
            "--log-level",
            case_sensitive=False,
            help="Set the logging level.",
        ),
    ] = None,
    verbose: Annotated[
        int,
        typer.Option(
            "-v",
            count=True,
            help="Increase logging verbosity; repeat up to four times.",
        ),
    ] = 0,
    log_file: Annotated[
        Path | None,
        typer.Option(
            "--log-file",
            help="Write JSON Lines logs to this file.",
        ),
    ] = None,
) -> None:
    """Main callback that handles no subcommand case."""
    child_args: list[str] = ctx.meta.get(ROOT_CHILD_ARGS_META_KEY, [])
    if "--" in child_args:
        child_args = child_args[: child_args.index("--")]
    setup_mode = _leaf_output_mode(child_args)

    def warning_writer(error: StructuredError) -> None:
        if setup_mode is output.OutputMode.HUMAN:
            typer.echo(f"{error.code}: {error.message}", err=True)
        else:
            output.to_stderr(error, setup_mode)

    try:
        configure_logging(
            loglevel=log_level,
            verbosity=verbose,
            log_file=log_file,
            warning_writer=warning_writer,
        )
    except (InvalidLoggingEnvironmentError, InvalidLogFilePathError) as err:
        if setup_mode is output.OutputMode.HUMAN:
            typer.echo(str(err), err=True)
        else:
            output.to_stderr(err.error, setup_mode)
        raise typer.Exit(2) from err

    if ctx.invoked_subcommand is None:
        get_console().print(ctx.get_help())
        raise typer.Exit(0)
    if ctx.invoked_subcommand != "data":
        set_before_command(ctx, _emit_banner_for_command)


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
    help="Manage authentication providers.",
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
    help="Manage science platform servers.",
    no_args_is_help=True,
    rich_help_panel="Auth Management",
)

cli.add_typer(
    data,
    name="data",
    rich_help_panel="Data Management",
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
    try:
        cli()
    except AuthExpiredError as err:
        get_console(stderr=True).print(err)
        get_console(stderr=True).print(
            "Authenticate with [italic cyan]canfar login[/italic cyan]"
        )
    except AuthContextError as err:
        get_console(stderr=True).print(err)
    except ConfigResetRequiredError as err:
        get_console(stderr=True).print(err)
        raise typer.Exit(1) from err


if __name__ == "__main__":
    main()
