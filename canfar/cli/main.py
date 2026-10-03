"""Command Line Interface for Science Platform."""

from __future__ import annotations

import importlib
import sys
from dataclasses import dataclass, field
from pathlib import Path  # noqa: TC003 - Typer resolves callback annotations at runtime
from typing import TYPE_CHECKING, Annotated, Any

import typer
from typer.core import TyperCommand, TyperGroup
from typer.main import get_group

from canfar.cli import output
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
    from typer._click import HelpFormatter
    from typer._click.core import Command
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
    """Load root commands on demand and capture child argv for root setup.

    Each command's module is imported only when that command runs, so a
    command does not pay for the dependencies of the others. Root help lists
    commands from their registered summaries without importing them.
    """

    _listing = False

    def parse_args(self, ctx: ClickContext, args: list[str]) -> list[str]:
        """Record unconsumed child arguments without changing dispatch."""
        child_args = super().parse_args(ctx, args)
        if ctx.parent is None:
            ctx.meta[_ROOT_CHILD_ARGS_META_KEY] = list(child_args)
        return child_args

    def list_commands(self, ctx: ClickContext) -> list[str]:
        """List registered commands in registration order."""
        return list(dict.fromkeys([*_COMMANDS, *super().list_commands(ctx)]))

    def get_command(self, ctx: ClickContext, cmd_name: str) -> Command | None:
        """Return a command, importing its module the first time it is used."""
        lazy = _COMMANDS.get(cmd_name)
        if lazy is not None and cmd_name not in self.commands:
            if self._listing:
                return lazy.summary(cmd_name)
            self.add_command(lazy.load(cmd_name), cmd_name)
        return super().get_command(ctx, cmd_name)

    def format_help(self, ctx: ClickContext, formatter: HelpFormatter) -> None:
        """Render root help from command summaries."""
        self._listing = True
        try:
            super().format_help(ctx, formatter)
        finally:
            self._listing = False


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


class _CreateCommand(_LeafUsageCommand):
    """Validate and describe resource options with the active Server's limits."""

    def parse_args(self, ctx: ClickContext, args: list[str]) -> list[str]:
        """Apply saved Server limits before parsing, help included."""
        from canfar.cli.create import apply_server_limits  # noqa: PLC0415

        apply_server_limits(self.params)
        return super().parse_args(ctx, args)


@dataclass(frozen=True)
class _LazyCommand:
    """A root command whose module is imported only when the command is used.

    Attributes:
        target: ``module:attribute`` of a command function or Typer application.
        help: Short help, also shown in root help before the module loads.
        panel: Root help panel that groups the command.
        group: Whether ``target`` is a Typer application of subcommands.
        options: Further ``Typer.command`` or ``Typer.add_typer`` settings.
    """

    target: str
    help: str
    panel: str
    group: bool = False
    options: dict[str, Any] = field(default_factory=dict)

    def summary(self, name: str) -> TyperCommand:
        """Return a stand-in that lists the command without importing it."""
        return TyperCommand(name, help=self.help, rich_help_panel=self.panel)

    def load(self, name: str) -> Command:
        """Import the command and build it as a root registration would."""
        module, _, attribute = self.target.partition(":")
        target = getattr(importlib.import_module(module), attribute)
        host = typer.Typer(rich_markup_mode="rich")
        settings: dict[str, Any] = {
            "help": self.help,
            "rich_help_panel": self.panel,
            **self.options,
        }
        if self.group:
            host.add_typer(target, name=name, **settings)
        else:
            host.command(name, **settings)(target)
        return get_group(host).commands[name]


_HELP_OPTIONS = {"help_option_names": ["-h", "--help"]}

_COMMANDS: dict[str, _LazyCommand] = {
    "login": _LazyCommand(
        "canfar.cli.login:login_command",
        "Login to CANFAR Science Platform.",
        "Auth Management",
    ),
    "auth": _LazyCommand(
        "canfar.cli.auth:auth",
        "Manage authentication providers.",
        "Auth Management",
        group=True,
        options={"no_args_is_help": False},
    ),
    "server": _LazyCommand(
        "canfar.cli.server:server",
        "Manage science platform servers.",
        "Auth Management",
        group=True,
        options={"no_args_is_help": True},
    ),
    "data": _LazyCommand(
        "canfar.cli.data:data",
        "Operate on configured data sources.",
        "Data Management",
        group=True,
    ),
    "create": _LazyCommand(
        "canfar.cli.create:creation",
        "Launch a new session.",
        "Session Management",
        options={
            "cls": _CreateCommand,
            "context_settings": {**_HELP_OPTIONS, "allow_interspersed_args": True},
            "no_args_is_help": True,
        },
    ),
    "ps": _LazyCommand("canfar.cli.ps:show", "Show sessions.", "Session Management"),
    "events": _LazyCommand(
        "canfar.cli.events:get_events",
        "List events for sessions.",
        "Session Management",
    ),
    "info": _LazyCommand(
        "canfar.cli.info:get_info", "Show session info", "Session Management"
    ),
    "open": _LazyCommand(
        "canfar.cli.open:open_sessions",
        "Open sessions in a browser",
        "Session Management",
        options={"context_settings": _HELP_OPTIONS, "no_args_is_help": True},
    ),
    "logs": _LazyCommand(
        "canfar.cli.logs:get_logs", "Show session logs", "Session Management"
    ),
    "delete": _LazyCommand(
        "canfar.cli.delete:delete_sessions",
        "Delete sessions by ID.",
        "Session Management",
        options={"no_args_is_help": True},
    ),
    "prune": _LazyCommand(
        "canfar.cli.prune:prune_sessions",
        "Delete sessions by criteria.",
        "Session Management",
        options={
            "cls": _LeafUsageCommand,
            "context_settings": _HELP_OPTIONS,
            "no_args_is_help": True,
        },
    ),
    "stats": _LazyCommand(
        "canfar.cli.stats:get_stats", "Show cluster stats", "Cluster Information"
    ),
    "image": _LazyCommand(
        "canfar.cli.image:image",
        "Manage images",
        "Image Management",
        group=True,
        options={"no_args_is_help": True},
    ),
    "config": _LazyCommand(
        "canfar.cli.config:config",
        "Manage client config",
        "Client Info",
        group=True,
        options={"no_args_is_help": True},
    ),
    "version": _LazyCommand(
        "canfar.cli.version:callback", "View client info", "Client Info"
    ),
}
"""Root commands in help order, imported only when used."""


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
            help="Show progress with -v, and debugging detail with -vv.",
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


def main() -> None:
    """Main entry point.

    Raises:
        SystemExit: With status 1 when a command ends on a boundary error that
            it did not render itself.
    """
    try:
        cli()
    except Exception as err:
        # The HTTP authentication hook is imported only by commands that use it.
        from canfar.hooks.httpx.auth import AuthenticationError  # noqa: PLC0415

        boundary = (
            AuthExpiredError,
            AuthContextError,
            ConfigResetRequiredError,
            AuthenticationError,
        )
        if not isinstance(err, boundary):
            raise
        output.fail(output.boundary_failure(err), _leaf_output_mode(sys.argv[1:]))


if __name__ == "__main__":
    main()
