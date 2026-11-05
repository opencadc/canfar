"""Container Registry credential commands for CANFAR CLI."""

from __future__ import annotations

import sys
from typing import Annotated, NoReturn

import typer
from pydantic import SecretStr, ValidationError
from rich import box
from rich.markup import escape
from rich.prompt import Prompt
from rich.table import Table

from canfar.cli import output
from canfar.cli.machine import OutputOption, resolve_mode
from canfar.config.migration import ConfigResetRequiredError
from canfar.errors import ErrorCode, StructuredError
from canfar.models.config import Configuration
from canfar.models.registry import (
    DEFAULT_REGISTRY_HOST,
    RegistryCredential,
    env_credential,
    parse_host,
)
from canfar.utils.console import get_console

registry = typer.Typer(
    name="registry",
    help="Manage container registry credentials.",
    no_args_is_help=True,
    rich_markup_mode="rich",
)

Host = Annotated[
    str,
    typer.Argument(help="Container Registry host, such as images.canfar.net."),
]


def _invalid(message: str, hint: str) -> NoReturn:
    output.fail(
        StructuredError(
            code=ErrorCode.COMMAND_VALIDATION_FAILED, message=message, hint=hint
        ),
        output.OutputMode.HUMAN,
    )


def _host(value: str) -> str:
    try:
        return parse_host(value)
    except ValueError as err:
        _invalid(str(err), "Pass a host such as images.canfar.net.")


def _configuration(mode: output.OutputMode) -> Configuration:
    try:
        return Configuration()  # ty: ignore[missing-argument]
    except ConfigResetRequiredError as err:
        output.fail(output.boundary_failure(err), mode)


def _read_secret(from_stdin: bool, interactive: bool) -> str:
    if from_stdin:
        return sys.stdin.readline().rstrip("\r\n")
    if interactive:
        return Prompt.ask("Secret", password=True, console=get_console())
    return ""


@registry.command("login")
def login_command(
    host: Host = DEFAULT_REGISTRY_HOST,
    username: Annotated[
        str | None,
        typer.Option(
            "-u", "--username", help="Registry username. Prompted when omitted."
        ),
    ] = None,
    secret_stdin: Annotated[
        bool,
        typer.Option(
            "--secret-stdin",
            help="Read the secret, such as a Harbor CLI secret, from stdin.",
        ),
    ] = False,
) -> None:
    """Save a registry credential for private images.

    The secret comes from a hidden prompt or from stdin, never from an argument.
    The credential is not checked against the registry.
    """
    key = _host(host)
    interactive = sys.stdin.isatty()
    if username is None:
        if not interactive:
            _invalid("A username is required.", "Pass --username.")
        username = Prompt.ask("Username", console=get_console())
    secret = _read_secret(secret_stdin, interactive)
    if not secret:
        _invalid("A secret is required.", "Pipe it with --secret-stdin.")
    try:
        credential = RegistryCredential(username=username, secret=SecretStr(secret))
    except ValidationError:
        _invalid(
            "The username and secret must each be 1 to 255 characters.",
            "Check the credential and retry.",
        )

    config = _configuration(output.OutputMode.HUMAN)
    config.editor.set("registries", {**config.registries, key: credential})
    config.editor.save()
    get_console().print(
        f"[green]✓[/green] Saved credential for [bold]{escape(key)}[/bold] "
        f"as [bold]{escape(username)}[/bold]."
    )


@registry.command("logout")
def logout_command(host: Host = DEFAULT_REGISTRY_HOST) -> None:
    """Remove the saved registry credential for a host."""
    key = _host(host)
    config = _configuration(output.OutputMode.HUMAN)
    console = get_console()
    if key in config.registries:
        remaining = {
            name: cred for name, cred in config.registries.items() if name != key
        }
        config.editor.set("registries", remaining)
        config.editor.save()
        console.print(
            f"[green]✓[/green] Removed credential for [bold]{escape(key)}[/bold]."
        )
    else:
        console.print(f"Not logged in to {escape(key)}.")
    if env_credential() is not None:
        get_console(stderr=True).print(
            "[yellow]CANFAR_REGISTRY__USERNAME and CANFAR_REGISTRY__SECRET "
            "still supply a credential for hosts you have not saved.[/yellow]"
        )


@registry.command("ls")
def list_command(output_format: OutputOption = None) -> None:
    """List registry credentials without their secrets."""
    mode = resolve_mode(output_format)
    config = _configuration(mode)
    rows = [
        {"host": host, "username": credential.username, "source": "saved"}
        for host, credential in config.registries.items()
    ]
    credential = env_credential()
    if credential is not None:
        rows.append({"host": "*", "username": credential.username, "source": "env"})
    if mode is not output.OutputMode.HUMAN:
        output.to_stdout(rows, mode)
        return
    if not rows:
        get_console().print(
            "No registry credentials. Run `canfar registry login HOST` to add one."
        )
        return
    table = Table(title="Registry Credentials", box=box.SIMPLE)
    table.add_column("Host", style="magenta")
    table.add_column("Username", style="cyan")
    table.add_column("Source", style="green")
    for row in rows:
        table.add_row(row["host"], row["username"], row["source"])
    get_console().print(table)
