"""Shared console utilities for CLI output."""

from __future__ import annotations

from functools import lru_cache

from rich.console import Console

from canfar.models.config import Configuration


@lru_cache(maxsize=1)
def get_console() -> Console:
    """Return a Rich console configured from the user configuration."""
    try:
        config = Configuration()
        kwargs = config.console or {}
        return Console(**kwargs)
    except TypeError as err:
        basic = Console()
        basic.print(f"[bold red]Error parsing console config: {err}[/bold red]")
        return basic


# Convenience instance for modules that just need a console
console: Console = get_console()
