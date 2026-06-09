"""Configuration Management."""

from __future__ import annotations

import json
from typing import Any

import typer
import yaml
from pydantic import BaseModel

from canfar import CONFIG_PATH
from canfar.cli import output
from canfar.cli.machine import JsonOption, YamlOption, maybe_emit_banner, resolve_mode
from canfar.hooks.typer.aliases import AliasGroup
from canfar.models.config import Configuration
from canfar.utils.console import console

config: typer.Typer = typer.Typer(
    cls=AliasGroup,
)

_SENSITIVE_GET_SUFFIXES = (
    "client.secret",
    "token.access",
    "token.refresh",
)
_REDACTED_VALUE = "**********"


def _mask(mapping: dict[str, Any], key: str) -> None:
    """Mask a secret value in place, preserving the key and null values."""
    if mapping.get(key) is not None:
        mapping[key] = _REDACTED_VALUE


def _redact_config_for_machine(cfg: Configuration) -> dict[str, Any]:
    """Return Configuration data safe for machine output with stable keys."""
    data = cfg.model_dump(mode="json", exclude_none=False)
    for auth in data.get("authentication", []):
        if auth.get("mode") != "oidc":
            continue
        client = auth.get("client")
        if isinstance(client, dict):
            _mask(client, "secret")
        token = auth.get("token")
        if isinstance(token, dict):
            _mask(token, "access")
            _mask(token, "refresh")
    return data


def _is_sensitive_config_path(key: str) -> bool:
    """Return whether a dotted config path resolves to a secret value."""
    lowered = key.lower()
    return any(
        lowered == suffix or lowered.endswith(f".{suffix}")
        for suffix in _SENSITIVE_GET_SUFFIXES
    )


def _machine_safe_value(key: str, value: object) -> object:
    """Mask sensitive values before machine output."""
    if value is None or not _is_sensitive_config_path(key):
        return value
    return _REDACTED_VALUE


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
            output.to_stdout(_redact_config_for_machine(cfg), mode)
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
    json_output: JsonOption = False,
    yaml_output: YamlOption = False,
) -> None:
    """Retrieve a config value.

    canfar config get console.width
    canfar config get active.server
    """
    mode = resolve_mode(json_output, yaml_output)
    maybe_emit_banner(mode)
    try:
        cfg = Configuration()
        value = cfg.get_value(key)
        if mode is not output.OutputMode.HUMAN:
            output.to_stdout(_machine_safe_value(key, value), mode)
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
