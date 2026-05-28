"""Combined Authentication and Server context commands."""

from __future__ import annotations

from typing import Annotated

import typer
from rich import box
from rich.table import Table

from canfar.cli._machine import (
    output_mode_callback,
    resolve_output_mode_or_exit,
    unsupported_machine_output,
)
from canfar.cli.dto_maps import context_show_dto
from canfar.cli.output import OutputMode, write_stdout
from canfar.hooks.typer.aliases import AliasGroup
from canfar.platform_state import list_pairs
from canfar.platform_state import show as context_show
from canfar.utils.console import console

context = typer.Typer(
    name="context",
    help="Inspect active Authentication and Server routing state.",
    no_args_is_help=True,
    cls=AliasGroup,
)


def _render_context_show() -> None:
    """Render active Authentication and Server state for human output."""
    authentication, server = context_show()
    table = Table(title="Active Context", show_lines=True, box=box.SIMPLE)
    table.add_column("Component", style="cyan")
    table.add_column("Value", style="magenta")

    if authentication is None:
        table.add_row("Authentication", "Not configured")
    else:
        table.add_row("IDP", authentication.idp)
        table.add_row("Mode", authentication.mode)
        table.add_row("Server URI", authentication.server or "N/A")

    if server is None:
        table.add_row("Server", "Not selected")
    else:
        table.add_row("Server Name", server.name or "N/A")
        table.add_row("Server URL", str(server.url) if server.url else "N/A")
    console.print(table)


def _render_context_list() -> None:
    """Render compatible Authentication and Server pairs for human output."""
    pairs = list_pairs()
    table = Table(
        title="Compatible Authentication and Server Pairs",
        show_lines=True,
        box=box.SIMPLE,
    )
    table.add_column("Active", justify="center", style="cyan")
    table.add_column("IDP", style="magenta")
    table.add_column("Mode", style="green")
    table.add_column("Server", style="blue")

    for authentication, server, active in pairs:
        table.add_row(
            "✅" if active else "",
            authentication.idp,
            authentication.mode,
            (server.name or str(server.uri)) if server is not None else "N/A",
        )
    console.print(table)


@context.command("show")
def context_show_command(
    ctx: typer.Context,
    json_output: Annotated[
        bool,
        typer.Option("--json", help="Emit machine-readable JSON on stdout."),
    ] = False,
    yaml_output: Annotated[
        bool,
        typer.Option("--yaml", help="Emit machine-readable YAML on stdout."),
    ] = False,
) -> None:
    """Show active Authentication and Server state."""
    output_mode_callback(ctx, json_output, yaml_output)
    mode = resolve_output_mode_or_exit(ctx)
    authentication, server = context_show()

    if mode is not OutputMode.HUMAN:
        write_stdout(context_show_dto(authentication, server), mode)
        return
    _render_context_show()


@context.command("list, ls")
def context_list_command(
    ctx: typer.Context,
    json_output: Annotated[
        bool,
        typer.Option("--json", help="Emit machine-readable JSON on stdout."),
    ] = False,
    yaml_output: Annotated[
        bool,
        typer.Option("--yaml", help="Emit machine-readable YAML on stdout."),
    ] = False,
) -> None:
    """List compatible Authentication and Server pairs."""
    output_mode_callback(ctx, json_output, yaml_output)
    unsupported_machine_output(ctx)
    _render_context_list()
