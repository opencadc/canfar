"""Science Platform server commands for CANFAR CLI."""

from __future__ import annotations

from typing import Annotated

import typer
from rich import box
from rich.table import Table

from canfar.authentication import AuthenticationError
from canfar.authentication import show as auth_show
from canfar.cli import output
from canfar.cli.machine import JsonOption, YamlOption, maybe_emit_banner, resolve_mode
from canfar.errors import ErrorCode, StructuredError
from canfar.hooks.typer.aliases import AliasGroup
from canfar.server import (
    ServerDiscoveryError,
    ServerFetchError,
    ServerSelectorError,
)
from canfar.server import (
    list_servers as server_list,
)
from canfar.server import (
    use as server_use,
)
from canfar.utils.console import console

server = typer.Typer(
    name="server",
    help="Manage science platform servers.",
    no_args_is_help=True,
    cls=AliasGroup,
)


def _render_server_list_table() -> None:
    """Render known servers for the active IDP in human mode."""
    try:
        auth_show()
    except AuthenticationError as exc:
        console.print(f"[bold red]{exc.error.message}[/bold red]")
        if exc.error.hint:
            console.print(exc.error.hint)
        raise typer.Exit(1) from exc

    try:
        servers = server_list()
    except ServerDiscoveryError as exc:
        console.print(f"[bold red]{exc}[/bold red]")
        raise typer.Exit(1) from exc

    if not servers:
        console.print(
            "[yellow]No compatible servers available for active IDP.[/yellow]"
        )
        return

    table = Table(title="Known Servers", show_lines=True, box=box.SIMPLE)
    table.add_column("Name", style="magenta")
    table.add_column("URI", style="cyan")
    table.add_column("URL", style="blue")
    table.add_column("Version", style="green")

    for item in servers:
        table.add_row(
            item.name or "N/A",
            str(item.uri) if item.uri is not None else "N/A",
            str(item.url) if item.url is not None else "N/A",
            item.version or "N/A",
        )
    console.print(table)


@server.command("list, ls")
def server_list_command(
    json_output: JsonOption = False,
    yaml_output: YamlOption = False,
) -> None:
    """List servers for the active Identity Provider."""
    mode = resolve_mode(json_output, yaml_output)
    maybe_emit_banner(mode)

    try:
        auth_show()
        servers = server_list()
    except AuthenticationError as exc:
        if mode is not output.OutputMode.HUMAN:
            output.to_stderr(exc.error, mode)
        else:
            console.print(f"[bold red]{exc.error.message}[/bold red]")
            if exc.error.hint:
                console.print(exc.error.hint)
        raise typer.Exit(1) from exc
    except ServerDiscoveryError as exc:
        error = StructuredError(
            code=exc.code,
            message=str(exc),
            hint="Verify registry connectivity and retry.",
        )
        if mode is not output.OutputMode.HUMAN:
            output.to_stderr(error, mode)
        else:
            console.print(f"[bold red]{exc}[/bold red]")
        raise typer.Exit(1) from exc

    if mode is not output.OutputMode.HUMAN:
        if not servers:
            output.to_stderr(
                StructuredError(
                    code=ErrorCode.SERVER_NONE_AVAILABLE,
                    message="No compatible servers available for active IDP.",
                    hint="Run canfar login to discover servers.",
                ),
                mode,
            )
            raise typer.Exit(1)
        output.to_stdout(servers, mode)
        return

    _render_server_list_table()


@server.command("use")
def server_use_command(
    selector: Annotated[str, typer.Argument(help="Server name or URI.")],
) -> None:
    """Select the active server by name or URI."""
    maybe_emit_banner(output.OutputMode.HUMAN)
    try:
        server_use(selector)
    except ServerSelectorError as exc:
        console.print(f"[bold red]{exc}[/bold red]")
        if exc.hint:
            console.print(exc.hint)
        raise typer.Exit(1) from exc
    except (ServerDiscoveryError, ServerFetchError) as exc:
        console.print(f"[bold red]{exc}[/bold red]")
        raise typer.Exit(1) from exc

    console.print(f"[green]✓[/green] Active server set to [bold]{selector}[/bold]")
