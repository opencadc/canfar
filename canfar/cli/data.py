"""Mount the upstream data command application."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import typer
from typer.core import TyperGroup
from typer.main import get_group

if TYPE_CHECKING:
    from typer._click.core import Command, Context

_DATA_GROUP_META_KEY = "canfar.data_group"
_DATA_ARGS_META_KEY = "canfar.data_args"

_OPERANDS = (
    "Name every path IDENTIFIER:/PATH, for example vault:/home/USER/data.fits; "
    "use local:/PATH for files on this computer, such as local:/tmp/."
)
"""Operand syntax that the upstream commands' own help does not explain."""

_LOCAL_HINT = (
    "Hint: name files on this computer local:/PATH, for example local:/tmp/. "
    "Run `canfar data COMMAND --help` for the configured identifiers."
)


def group() -> TyperGroup:
    """Build the released upstream application with CANFAR policy.

    Each upstream command's help ends with the operand syntax and the
    configured Storage Identifiers.

    Returns:
        TyperGroup: The upstream command group bound to configured sources.
    """
    # fsspec and the storage CLI load only when `canfar data` runs.
    from fsspec_cli import App  # noqa: PLC0415

    from canfar.storage import _sources  # noqa: PLC0415

    sources = _sources()
    commands = get_group(
        App(
            sources,
            capabilities={"recursion": {"copy": True, "remove": False}},
        ).typer_app
    )
    epilog = f"{_OPERANDS} Identifiers: {', '.join(sources)}."
    for command in commands.commands.values():
        command.epilog = epilog
    return commands


def _looks_local(argument: str) -> bool:
    """Return whether an operand looks like a bare path on this computer."""
    if argument.startswith(("/", "~", ".")):
        return True
    head, _, _ = argument.partition("/")
    return bool(head) and "/" in argument and ":" not in head


class _DataGroup(TyperGroup):
    """Resolve the embedded app lazily so imports perform no configuration I/O."""

    @staticmethod
    def _delegate(ctx: Context) -> TyperGroup:
        resolved = ctx.meta.get(_DATA_GROUP_META_KEY)
        if resolved is None:
            resolved = group()
            ctx.meta[_DATA_GROUP_META_KEY] = resolved
        assert isinstance(resolved, TyperGroup)
        return resolved

    def list_commands(self, ctx: Context) -> list[str]:
        """List the unchanged upstream commands."""
        return self._delegate(ctx).list_commands(ctx)

    def get_command(self, ctx: Context, cmd_name: str) -> Command | None:
        """Resolve an unchanged upstream command."""
        return self._delegate(ctx).get_command(ctx, cmd_name)

    def parse_args(self, ctx: Context, args: list[str]) -> list[str]:
        """Remember the arguments so a usage error can point at a local path."""
        ctx.meta[_DATA_ARGS_META_KEY] = list(args)
        return super().parse_args(ctx, args)

    def invoke(self, ctx: Context) -> Any:
        """Run the command, adding a hint when a bare local path was rejected."""
        try:
            return super().invoke(ctx)
        except typer.Exit as exit_:
            arguments = ctx.meta.get(_DATA_ARGS_META_KEY, [])
            operands = (
                arguments[: arguments.index("--")] if "--" in arguments else arguments
            )
            if exit_.exit_code == 2 and any(map(_looks_local, operands)):
                typer.echo(_LOCAL_HINT, err=True)
            raise


data = typer.Typer(
    cls=_DataGroup,
    help="Operate on configured data sources.",
    epilog=_OPERANDS,
    add_completion=False,
    no_args_is_help=True,
)
