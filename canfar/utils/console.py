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


@lru_cache(maxsize=1)
def get_console() -> Console:
    """Get a Rich console configured from the user configuration.

    Returns:
        Rich console instance sized from user configuration.
    """
    cfg = Configuration()
    return Console(width=cfg.console.width)


def emit_active_server_banner() -> None:
    """Print the active server banner once per CLI invocation in human mode."""
    if _banner_emitted.get():
        return
    _banner_emitted.set(True)
    cfg = Configuration()
    try:
        name = cfg.get_active_server().name
    except KeyError:
        name = "unknown"
    console.print(f"@{name}", style="dim underline")


# Convenience instance for modules that just need a console
console: Console = get_console()
