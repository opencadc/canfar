"""AliasGroup for extending command aliases in Typer."""

from __future__ import annotations

import re
from typing import TYPE_CHECKING

from typer.core import TyperGroup

if TYPE_CHECKING:
    from click.core import Command, Context


class AliasGroup(TyperGroup):
    """AliasGroup to handle command aliases in Typer.

    Args:
        TyperGroup (TyperGroup): Base class for grouping commands in Typer.
    """

    _CMD_SPLIT_P = re.compile(r" ?[,|] ?")

    def get_command(self, ctx: Context, cmd_name: str) -> Command | None:
        """Retrieve a command by name, supporting aliases.

        Args:
            ctx (Context): The Click context.
            cmd_name (str): The command name or alias.

        Returns:
            Command | None: The matched command or None if not found.
        """
        cmd_name = self._group_cmd_name(cmd_name)
        return super().get_command(ctx, cmd_name)

    def _group_cmd_name(self, default: str) -> str:
        for cmd in self.commands.values():
            name: str = getattr(cmd, "name", "")
            if name and default in self._CMD_SPLIT_P.split(name):
                return name
        return default
