"""Shared console utilities for CLI output."""

from __future__ import annotations

from contextvars import ContextVar
from functools import lru_cache
from typing import TYPE_CHECKING

from rich.console import Console

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
    width = Configuration().console.width  # ty: ignore[missing-argument]
    return Console(width=width, stderr=stderr)


def emit_active_server_banner() -> None:
    """Print the active Server Selection when configured for human output."""
    cfg = Configuration()  # ty: ignore[missing-argument]
    if not cfg.console.banner:
        return
    try:
        name = (
            cfg.servers[cfg.active.server].name
            if cfg.active.server is not None
            else None
        )
    except KeyError:
        name = None
    if name is None:
        name = "unknown"
    get_console().print(f"@{name}", style="dim underline")


def activate_cli_root(ctx: Context) -> None:
    """Mark callbacks dispatched by the root CLI until their context closes."""
    token = _CLI_ROOT_ACTIVE.set(True)
    ctx.call_on_close(lambda: _CLI_ROOT_ACTIVE.reset(token))


def emit_cli_active_server_banner() -> None:
    """Emit the banner only when a command runs through the root CLI."""
    if _CLI_ROOT_ACTIVE.get():
        emit_active_server_banner()
