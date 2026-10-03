"""Science Platform server commands for CANFAR CLI."""

from __future__ import annotations

from typing import TYPE_CHECKING, Annotated

import typer
from rich import box
from rich.table import Table
from rich.text import Text

from canfar.authentication import AuthenticationError
from canfar.authentication import show as auth_show
from canfar.cli import output
from canfar.cli.machine import OutputOption, resolve_mode
from canfar.config.migration import ConfigResetRequiredError
from canfar.errors import ErrorCode, StructuredError
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
from canfar.utils.console import emit_cli_active_server_banner, get_console

if TYPE_CHECKING:
    from canfar.models.http import ResourceRange, Server, SessionResources

server = typer.Typer(
    name="server",
    help="Manage science platform servers.",
    no_args_is_help=True,
)

_UNKNOWN = "[dim]unknown[/dim]"


def _range_cell(bounds: ResourceRange | None, unit: str = "") -> str:
    """Format an inclusive resource range, or mark it unknown."""
    if bounds is None:
        return _UNKNOWN
    return f"{bounds} {unit}".rstrip()


def _mode(resources: SessionResources) -> str:
    """Format the CPU and memory bounds of one Resource Allocation Mode."""
    return (
        f"{_range_cell(resources.cores, 'cores')}\n{_range_cell(resources.ram, 'GB')}"
    )


def _resource_cells(item: Server) -> tuple[str, str, str, str]:
    """Return the flexible, fixed, GPU, and Session limit cells for one Server."""
    resources = item.resources
    if resources is None:
        return _UNKNOWN, _UNKNOWN, _UNKNOWN, _UNKNOWN
    gpus = resources.gpus
    return (
        _mode(resources.flexible),
        _mode(resources.fixed),
        "none" if gpus is not None and gpus.max == 0 else _range_cell(gpus),
        _UNKNOWN if resources.sessions is None else str(resources.sessions),
    )


def _render_server_list_table(servers: list[Server]) -> None:
    """Render known servers for the active IDP in human mode."""
    if not servers:
        get_console(stderr=True).print(
            "[yellow]No compatible servers available for active IDP.[/yellow]"
        )
        return

    table = Table(
        title="Known Servers",
        caption=(
            "[italic]Flexible[/italic] resources allow dynamic allocation based on "
            "availability.\n"
            "[italic]Fixed[/italic] resources guarantee allocation.\n"
            "[italic]Sessions[/italic] limit per user."
        ),
        caption_style="dim",
        caption_justify="left",
        show_lines=True,
        box=box.SIMPLE,
    )
    table.add_column("Name", style="magenta")
    table.add_column("URI / URL", style="cyan")
    table.add_column("Version", style="green")
    table.add_column("Flexible")
    table.add_column("Fixed")
    table.add_column("GPUs")
    table.add_column("Sessions")

    for item in servers:
        uri = str(item.uri) if item.uri is not None else "N/A"
        url = str(item.url) if item.url is not None else "N/A"
        table.add_row(
            item.name or "N/A",
            Text.assemble(uri, "\n", (url, "blue")),
            item.version or "N/A",
            *_resource_cells(item),
        )
    get_console().print(table)


@server.command("ls")
def server_list_command(
    output_format: OutputOption = None,
) -> None:
    """List servers for the active Identity Provider."""
    mode = resolve_mode(output_format)

    try:
        auth_show()
        servers = server_list()
    except ConfigResetRequiredError as exc:
        output.fail(output.boundary_failure(exc), mode)
    except AuthenticationError as exc:
        output.fail(exc.error, mode)
    except ServerDiscoveryError as exc:
        output.fail(
            StructuredError(
                code=exc.code,
                message=str(exc),
                hint="Verify registry connectivity and retry.",
            ),
            mode,
        )

    if mode is not output.OutputMode.HUMAN:
        if not servers:
            output.fail(
                StructuredError(
                    code=ErrorCode.SERVER_NONE_AVAILABLE,
                    message="No compatible servers available for active IDP.",
                    hint="Run canfar login to discover servers.",
                ),
                mode,
            )
        output.to_stdout(servers, mode)
        return

    emit_cli_active_server_banner()
    _render_server_list_table(servers)


@server.command("use")
def server_use_command(
    selector: Annotated[str, typer.Argument(help="Server name or URI.")],
) -> None:
    """Select the active server by name or URI."""
    emit_cli_active_server_banner()
    try:
        server_use(selector)
    except ServerSelectorError as exc:
        get_console(stderr=True).print(f"[bold red]{exc}[/bold red]")
        if exc.hint:
            get_console(stderr=True).print(exc.hint)
        raise typer.Exit(1) from exc
    except (ServerDiscoveryError, ServerFetchError) as exc:
        get_console(stderr=True).print(f"[bold red]{exc}[/bold red]")
        raise typer.Exit(1) from exc

    get_console().print(
        f"[green]✓[/green] Active server set to [bold]{selector}[/bold]"
    )
