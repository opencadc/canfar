"""Shared console utilities for CLI output."""

from __future__ import annotations

from functools import lru_cache

from rich.console import Console

from canfar.models.config import Configuration


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
        name = cfg.get_active_server().name
    except KeyError:
        name = "unknown"
    get_console().print(f"@{name}", style="dim underline")
