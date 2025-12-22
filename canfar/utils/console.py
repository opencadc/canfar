"""Shared console utilities for CLI output."""

from __future__ import annotations

from functools import lru_cache
from typing import Any

from rich.console import Console

from canfar.models.config import Configuration


@lru_cache(maxsize=1)
def get_console() -> Console:
    """Get a Rich console configured from the user configuration.

    Returns:
        Console: Rich console instance.
    """
    cfg = Configuration()
    config: dict[str, Any] = cfg.model_dump(mode="python")
    width = config.get("console", {}).get("width", 120)
    active = config.get("active", "default")
    context = config.get("contexts", {}).get(active, {})
    server = context.get("server", {})
    name = server.get("name", "unknown")
    terminal = Console(width=width)
    terminal.print(f"@{name}", style="dim underline")
    return terminal


# Convenience instance for modules that just need a console
console: Console = get_console()
