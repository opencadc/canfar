"""Configuration Management."""

from __future__ import annotations

import json

import typer
import yaml

from canfar import CONFIG_PATH
from canfar.cli import output
from canfar.cli.machine import JsonOption, YamlOption, maybe_emit_banner, resolve_mode
from canfar.hooks.typer.aliases import AliasGroup
from canfar.models.config import Configuration
from canfar.utils.console import console

config: typer.Typer = typer.Typer(
    cls=AliasGroup,
)


@config.command("show", help="Display client configuration")
def show(
    json_output: JsonOption = False,
    yaml_output: YamlOption = False,
) -> None:
    """Display client configuration."""
    mode = resolve_mode(json_output, yaml_output)
    maybe_emit_banner(mode)
    try:
        cfg = Configuration()
        if mode is not output.OutputMode.HUMAN:
            output.to_stdout(cfg.model_dump(mode="json", exclude_none=False), mode)
            return

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
    """Format a JSON-safe config value for human display."""
    if isinstance(value, (dict, list)):
        return json.dumps(value, indent=2)
    if value is None:
        return "null"
    return str(value)


@config.command("get")
def get(
    key: str = typer.Argument(
        ...,
        help="Config key to get in dot notation.",
    ),
    json_output: JsonOption = False,
    yaml_output: YamlOption = False,
) -> None:
    """Retrieve a config value.

    canfar config get console.width
    canfar config get active.server
    canfar config get servers.canfar.url
    """
    mode = resolve_mode(json_output, yaml_output)
    maybe_emit_banner(mode)
    try:
        cfg = Configuration()
        value = cfg.get_value(key)
        if mode is not output.OutputMode.HUMAN:
            output.to_stdout(value, mode)
            return
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
    canfar config set active.authentication cadc
    canfar config set servers.canfar.url https://ws-uv.canfar.net/skaha
    """
    maybe_emit_banner(output.OutputMode.HUMAN)
    cfg = Configuration()
    try:
        parsed = yaml.safe_load(value)
        updated = cfg.set_value(key, parsed)
        updated.save()
    except (AttributeError, KeyError, IndexError, TypeError, ValueError) as err:
        console.print(f"[bold red]Error:[/bold red] {err}")
        raise typer.Exit(1) from err


@config.command("path", help="Local path of config")
def path() -> None:
    """Local path of config."""
    maybe_emit_banner(output.OutputMode.HUMAN)
    console.print(f"[green]{CONFIG_PATH}[/green]")
