"""Configuration Management."""

from __future__ import annotations

import typer
from rich.console import Console

from canfar import CONFIG_PATH
from canfar.hooks.typer.aliases import AliasGroup
from canfar.models.config import Configuration

config: typer.Typer = typer.Typer(
    cls=AliasGroup,
)
console = Console(width=120)


@config.command("show | list | ls")
def show() -> None:
    """Displays the current configuration."""
    try:
        cfg = Configuration()
        exists: bool = CONFIG_PATH.exists()
        msg = f"{'discovered' if exists else 'does not exist, showing defaults.'}"
        console.print(f"[dim]{CONFIG_PATH} {msg}[/dim]")
        console.print(
            cfg.model_dump(
                mode="python",
                exclude_none=True,
            )
        )
    except Exception as error:
        console.print(f"[bold red]Error: {error}[/bold red]")
        raise typer.Exit(1) from error


@config.command("path")
def path() -> None:
    """Displays the path to the configuration file."""
    console.print(f"[green]{CONFIG_PATH}[/green]")
