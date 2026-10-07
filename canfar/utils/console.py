"""Shared console utilities for CLI output."""

from __future__ import annotations

from contextvars import ContextVar
from functools import lru_cache
from typing import TYPE_CHECKING

from rich.console import Console

from canfar.config.migration import ConfigResetRequiredError
from canfar.models.config import Configuration

if TYPE_CHECKING:
    from typer.models import Context

_CLI_ROOT_ACTIVE: ContextVar[bool] = ContextVar("canfar_cli_root_active", default=False)


@lru_cache(maxsize=2)
def get_console(*, stderr: bool = False) -> Console:
    """Get a Rich console configured from the user configuration.

    Args:
        stderr: Write diagnostics to stderr instead of command data to stdout.

    Returns:
        Rich console instance sized from user configuration.
    """
    try:
        width = Configuration().console.width  # ty: ignore[missing-argument]
    except (ConfigResetRequiredError, ValueError):
        # The error for an unreadable config file prints through this console.
        width = None
    return Console(width=width, stderr=stderr)


def activate_cli_root(ctx: Context) -> None:
    """Mark callbacks dispatched by the root CLI until their context closes."""
    token = _CLI_ROOT_ACTIVE.set(True)
    ctx.call_on_close(lambda: _CLI_ROOT_ACTIVE.reset(token))


def emit_cli_active_server_banner() -> None:
    """Print the active Server Selection when a command runs through the root CLI.

    Configuration validation guarantees that an active Server Name is saved.
    """
    if not _CLI_ROOT_ACTIVE.get():
        return
    cfg = Configuration()  # ty: ignore[missing-argument]
    if cfg.console.banner:
        get_console().print(f"@{cfg.active.server or 'unknown'}", style="dim underline")
