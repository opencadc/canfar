"""Shared console utilities for CLI output."""

from __future__ import annotations

from contextvars import ContextVar
from functools import lru_cache

from rich.console import Console

from canfar.models.config import Configuration

_banner_emitted: ContextVar[bool] = ContextVar("cli_banner_emitted", default=False)


def reset_banner_state() -> None:
    """Reset CLI banner emission state for a new invocation."""
    _banner_emitted.set(False)


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
    except Exception:  # noqa: BLE001
        width = 120
    return Console(width=width, stderr=stderr)


def emit_active_server_banner() -> None:
    """Print the active server banner once per CLI invocation in human mode."""
    if _banner_emitted.get():
        return
    _banner_emitted.set(True)
    cfg = Configuration()  # ty: ignore[missing-argument]
    try:
        name = cfg.get_active_server().name
    except KeyError:
        name = "unknown"
    get_console().print(f"@{name}", style="dim underline")
