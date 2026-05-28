"""Shared console utilities for CLI output."""

from __future__ import annotations

from functools import lru_cache

from rich.console import Console

from canfar.models.config import Configuration


@lru_cache(maxsize=1)
def get_console() -> Console:
    """Get a Rich console configured from the user configuration.

    Returns:
        Rich console instance with active server name banner when available.
    """
    cfg = Configuration()
    width = cfg.console.width
    active_server = cfg.get_active_server()
    name = active_server.name if active_server is not None else "unknown"
    terminal = Console(width=width)
    terminal.print(f"@{name}", style="dim underline")
    return terminal


# Convenience instance for modules that just need a console
console: Console = get_console()
