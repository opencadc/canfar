"""Typer group extensions for aliases and terminal command dispatch."""

from __future__ import annotations

import re
from typing import TYPE_CHECKING, Any, TypeVar

from typer import Context
from typer.core import TyperGroup

if TYPE_CHECKING:
    from collections.abc import Callable, Mapping

    from typer._click.core import Command
    from typer._click.core import Context as ClickContext

ROOT_CHILD_ARGS_META_KEY = "canfar.root_child_args"
_BEFORE_COMMAND_META_KEY = "canfar.before_command"
_Value = TypeVar("_Value")


def set_before_command(
    ctx: Context,
    callback: Callable[[Mapping[str, object]], None],
) -> None:
    """Run a callback after terminal command parsing and before its handler."""
    ctx.meta[_BEFORE_COMMAND_META_KEY] = callback


def _run_before_command(ctx: Context) -> None:
    callback = ctx.meta.pop(_BEFORE_COMMAND_META_KEY, None)
    if callback is not None:
        callback(ctx.params)


class _BeforeCommandContext(Context):
    """Run the pending hook immediately before a terminal command callback."""

    def invoke(
        self,
        callback: Callable[..., _Value],
        /,
        *args: Any,
        **kwargs: Any,
    ) -> _Value:
        if not isinstance(self.command, TyperGroup) or self.invoked_subcommand is None:
            _run_before_command(self)
        return super().invoke(callback, *args, **kwargs)


def _install_before_command_context(command: Command) -> None:
    command.context_class = _BeforeCommandContext
    if isinstance(command, TyperGroup):
        for child in command.commands.values():
            _install_before_command_context(child)


class AliasGroup(TyperGroup):
    """Typer group with command aliases and one-shot terminal hooks."""

    _CMD_SPLIT_P = re.compile(r" ?[,|] ?")
    context_class = _BeforeCommandContext

    def parse_args(self, ctx: ClickContext, args: list[str]) -> list[str]:
        """Preserve the root command's parsed child arguments for setup errors."""
        child_args = super().parse_args(ctx, args)
        if ctx.parent is None:
            ctx.meta[ROOT_CHILD_ARGS_META_KEY] = list(child_args)
        return child_args

    def get_command(self, ctx: ClickContext, cmd_name: str) -> Command | None:
        """Retrieve a command by name, supporting aliases.

        Args:
            ctx (Context): The Click context.
            cmd_name (str): The command name or alias.

        Returns:
            Command | None: The matched command or None if not found.
        """
        cmd_name = self._group_cmd_name(cmd_name)
        command = super().get_command(ctx, cmd_name)
        if command is not None:
            _install_before_command_context(command)
        return command

    def _group_cmd_name(self, default: str) -> str:
        for cmd in self.commands.values():
            name: str = getattr(cmd, "name", "")
            if name and default in self._CMD_SPLIT_P.split(name):
                return name
        return default
