"""Command Line Interface for Science Platform."""

from __future__ import annotations

from pathlib import Path  # noqa: TC003 - Typer resolves callback annotations at runtime
from typing import TYPE_CHECKING, Annotated

import typer
from typer.core import TyperCommand, TyperGroup

from canfar.cli import output
from canfar.cli.auth import auth
from canfar.cli.config import config
from canfar.cli.create import creation
from canfar.cli.data import data
from canfar.cli.delete import delete_sessions
from canfar.cli.events import get_events
from canfar.cli.image import image
from canfar.cli.info import get_info
from canfar.cli.login import register_login_command
from canfar.cli.logs import get_logs
from canfar.cli.open import open_sessions
from canfar.cli.prune import prune_sessions
from canfar.cli.ps import show as show_sessions
from canfar.cli.server import server
from canfar.cli.stats import get_stats
from canfar.cli.version import callback as version_callback
from canfar.config.migration import ConfigResetRequiredError
from canfar.exceptions.context import AuthContextError, AuthExpiredError
from canfar.utils.console import activate_cli_root, get_console
from canfar.utils.logging import (
    InvalidLogFilePathError,
    InvalidLoggingEnvironmentError,
    LoggingLevel,
    configure_logging,
)

if TYPE_CHECKING:
    from typer._click.core import Context as ClickContext

    from canfar.errors import StructuredError


_ROOT_CHILD_ARGS_META_KEY = "canfar.root_child_args"


def _leaf_output_mode(args: list[str]) -> output.OutputMode:
    """Infer a leaf output option before root setup has completed."""
    for index, arg in enumerate(args):
        if arg == "--":
            break
        if arg in {"-o", "--output"} and index + 1 < len(args):
            value = args[index + 1]
            if value in {"json", "yaml"}:
                return output.OutputMode(value)
        if arg.startswith("--output=") and arg.removeprefix("--output=") in {
            "json",
            "yaml",
        }:
            return output.OutputMode(arg.removeprefix("--output="))
        if arg.startswith("-o") and arg not in {"-o", "--output"}:
            value = arg.removeprefix("-o")
            if value in {"json", "yaml"}:
                return output.OutputMode(value)
    return output.OutputMode.HUMAN


class _RootTyperGroup(TyperGroup):
    """Capture child argv so root setup can infer a leaf output mode."""

    def parse_args(self, ctx: ClickContext, args: list[str]) -> list[str]:
        """Record unconsumed child arguments without changing dispatch."""
        child_args = super().parse_args(ctx, args)
        if ctx.parent is None:
            ctx.meta[_ROOT_CHILD_ARGS_META_KEY] = list(child_args)
        return child_args


_LEAF_USAGE = {
    "create": "Usage: canfar create [OPTIONS] KIND IMAGE [-- CMD [ARGS]...]",
    "prune": "Usage: canfar prune [OPTIONS] PREFIX KIND STATUS COMMAND [ARGS]...",
}


class _LeafUsageCommand(TyperCommand):
    """Keep root leaf usage text aligned with delimiter-bearing commands."""

    def get_usage(self, ctx: ClickContext) -> str:
        """Return the canonical usage line for a leaf with custom syntax."""
        name = self.name or ""
        if name in _LEAF_USAGE:
            return _LEAF_USAGE[name]
        return super().get_usage(ctx)


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
    activate_cli_root(ctx)
    child_args: list[str] = ctx.meta.get(_ROOT_CHILD_ARGS_META_KEY, [])
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
    cls=_RootTyperGroup,
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

cli.command(
    "create",
    cls=_LeafUsageCommand,
    context_settings={
        "help_option_names": ["-h", "--help"],
        "allow_interspersed_args": True,
    },
    help="Launch a new session.",
    no_args_is_help=True,
    rich_help_panel="Session Management",
)(creation)

cli.command(
    "ps",
    help="Show sessions.",
    rich_help_panel="Session Management",
)(show_sessions)
cli.command(
    "events",
    help="List events for sessions.",
    rich_help_panel="Session Management",
)(get_events)
cli.command(
    "info",
    help="Show session info",
    rich_help_panel="Session Management",
)(get_info)
cli.command(
    "open",
    help="Open sessions in a browser",
    context_settings={"help_option_names": ["-h", "--help"]},
    no_args_is_help=True,
    rich_help_panel="Session Management",
)(open_sessions)
cli.command(
    "logs",
    help="Show session logs",
    rich_help_panel="Session Management",
)(get_logs)
cli.command(
    "delete",
    help="Delete sessions by ID.",
    no_args_is_help=True,
    rich_help_panel="Session Management",
)(delete_sessions)
cli.command(
    "prune",
    cls=_LeafUsageCommand,
    context_settings={"help_option_names": ["-h", "--help"]},
    help="Delete sessions by criteria.",
    no_args_is_help=True,
    rich_help_panel="Session Management",
)(prune_sessions)
cli.command(
    "stats",
    help="Show cluster stats",
    rich_help_panel="Cluster Information",
)(get_stats)

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
cli.command(
    "version",
    help="View client info",
    rich_help_panel="Client Info",
)(version_callback)


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
