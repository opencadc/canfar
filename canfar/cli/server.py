"""Science Platform server commands for CANFAR CLI."""

from __future__ import annotations

from typing import Annotated

import typer
from rich import box
from rich.table import Table

from canfar.authentication import AuthenticationError
from canfar.authentication import show as auth_show
from canfar.cli import output
from canfar.cli.dto_maps import server_list_dto
from canfar.cli.machine import (
    output_mode_callback,
    resolve_output_mode_or_exit,
    unsupported_machine_output,
)
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
    """List servers for the active Identity Provider."""
    output_mode_callback(ctx, json_output, yaml_output)
    mode = resolve_output_mode_or_exit(ctx)

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
        output.to_stdout(server_list_dto(servers), mode)
        return

    _render_server_list_table()


@server.command("use")
def server_use_command(
    ctx: typer.Context,
    selector: Annotated[str, typer.Argument(help="Server name or URI.")],
) -> None:
    """Select the active server by name or URI."""
    unsupported_machine_output(ctx)
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
