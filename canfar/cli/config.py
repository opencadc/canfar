"""Configuration Management."""

from __future__ import annotations

import json

import typer
import yaml
from pydantic_settings.exceptions import SettingsError

from canfar import CONFIG_PATH
from canfar.cli import output
from canfar.cli.machine import JsonOption, YamlOption, resolve_mode
from canfar.config.migration import ConfigResetRequiredError
from canfar.errors import ErrorCode, StructuredError
from canfar.hooks.typer.aliases import AliasGroup
from canfar.models.config import Configuration
from canfar.utils.console import get_console

config: typer.Typer = typer.Typer(
    cls=AliasGroup,
)


def _configuration_failure(error: Exception) -> StructuredError:
    """Convert an expected persisted-configuration failure."""
    if isinstance(error, ConfigResetRequiredError):
        code = error.code
        message = error.message
    else:
        code = ErrorCode.CONFIG_INVALID
        message = f"Configuration could not be loaded: {error}"
    return StructuredError(
        code=code,
        message=message,
        hint="Check the configuration file and retry.",
    )


@config.command("show", help="Display client configuration")
def show(
    json_output: JsonOption = False,
    yaml_output: YamlOption = False,
) -> None:
    """Display client configuration."""
    mode = resolve_mode(json_output, yaml_output)
    try:
        cfg = Configuration()  # ty: ignore[missing-argument]
    except (
        ConfigResetRequiredError,
        OSError,
        SettingsError,
        ValueError,
        yaml.YAMLError,
    ) as error:
        failure = _configuration_failure(error)
        if mode is output.OutputMode.HUMAN:
            get_console(stderr=True).print(
                f"[bold red]Error:[/bold red] {failure.message}"
            )
        else:
            output.to_stderr(failure, mode)
        raise typer.Exit(1) from error

    if not CONFIG_PATH.exists():
        get_console(stderr=True).print(
            f"[yellow]{CONFIG_PATH} does not exist, showing defaults.[/yellow]"
        )
    if mode is not output.OutputMode.HUMAN:
        output.to_stdout(cfg.model_dump(mode="json", exclude_none=False), mode)
        return

    if CONFIG_PATH.exists():
        get_console().print(f"[dim]{CONFIG_PATH} discovered[/dim]")
    get_console().print(
        cfg.model_dump(
            mode="python",
            exclude_none=True,
        )
    )


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
    try:
        cfg = Configuration()  # ty: ignore[missing-argument]
    except (
        ConfigResetRequiredError,
        OSError,
        SettingsError,
        ValueError,
        yaml.YAMLError,
    ) as err:
        failure = _configuration_failure(err)
        if mode is output.OutputMode.HUMAN:
            get_console(stderr=True).print(
                f"[bold red]Error:[/bold red] {failure.message}"
            )
        else:
            output.to_stderr(failure, mode)
        raise typer.Exit(1) from err

    try:
        value = cfg.get_value(key)
    except (AttributeError, KeyError, IndexError, TypeError, ValueError) as err:
        failure = StructuredError(
            code=ErrorCode.COMMAND_VALIDATION_FAILED,
            message=f"Configuration key '{key}' could not be read.",
            hint=str(err),
        )
        if mode is output.OutputMode.HUMAN:
            get_console(stderr=True).print(
                f"[bold red]Error:[/bold red] {failure.message}"
            )
        else:
            output.to_stderr(failure, mode)
        raise typer.Exit(1) from err

    if mode is not output.OutputMode.HUMAN:
        output.to_stdout(value, mode)
        return
    typer.echo(_format_value(value))


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
    cfg = Configuration()  # ty: ignore[missing-argument]
    try:
        parsed = yaml.safe_load(value)
        updated = cfg.set_value(key, parsed)
        updated.save()
    except (AttributeError, KeyError, IndexError, TypeError, ValueError) as err:
        get_console(stderr=True).print(f"[bold red]Error:[/bold red] {err}")
        raise typer.Exit(1) from err


@config.command("path", help="Local path of config")
def path() -> None:
    """Local path of config."""
    get_console().print(f"[green]{CONFIG_PATH}[/green]")
