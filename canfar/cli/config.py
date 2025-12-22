"""Configuration Management."""

from __future__ import annotations

import json

import typer
import yaml
from pydantic import BaseModel

from canfar import CONFIG_PATH
from canfar.hooks.typer.aliases import AliasGroup
from canfar.models.config import Configuration
from canfar.utils.console import console

config: typer.Typer = typer.Typer(
    cls=AliasGroup,
)


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


def _format_value(value: object) -> str:
    """Format a value for display.

    Args:
        value (object): Value to format.

    Returns:
        str: Formatted value.
    """
    if isinstance(value, BaseModel):
        return json.dumps(value.model_dump(mode="json", exclude_none=True), indent=2)
    if isinstance(value, (dict, list)):
        return json.dumps(value, indent=2, default=str)
    if value is None:
        return "null"
    return str(value)


@config.command("get")
def get(
    key: str = typer.Argument(
        ...,
        help="Config key to get in dot notation.",
    ),
) -> None:
    """Retrieve a config value.

    canfar config get console.width
    canfar config get contexts.active
    """
    try:
        cfg = Configuration()
        value = cfg.get_value(key)
        typer.echo(_format_value(value))
    except (AttributeError, KeyError, IndexError, TypeError, ValueError) as err:
        console.print(f"[bold red]Error:[/bold red] {err}")
        raise typer.Exit(1) from err


@config.command("set")
def set_value(
    key: str = typer.Argument(..., help="Config key to set in dot notation."),
    value: str = typer.Argument(..., help="Value to set."),
) -> None:
    """Set a config value.

    canfar config set console.width 130
    canfar config set contexts.active default
    """
    cfg = Configuration()
    try:
        parsed = yaml.safe_load(value)
        updated = cfg.set_value(key, parsed)
        updated.save()
    except (AttributeError, KeyError, IndexError, TypeError, ValueError) as err:
        console.print(f"[bold red]Error:[/bold red] {err}")
        raise typer.Exit(1) from err


@config.command("path")
def path() -> None:
    """Displays the path to the configuration file."""
    console.print(f"[green]{CONFIG_PATH}[/green]")
