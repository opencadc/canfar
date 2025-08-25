"""CLI command to get information for canfar sessions."""

from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from typing import Annotated, Any

import humanize
import typer
from rich import box
from rich.console import Console
from rich.table import Table

from canfar.models.session import FetchResponse
from canfar.sessions import AsyncSession

console = Console()

info = typer.Typer(
    name="info",
    help="Get detailed information about sessions.",
    no_args_is_help=True,
)

ALL_FIELDS: dict[str, str] = {
    "id": "Session ID",
    "name": "Name",
    "status": "Status",
    "type": "Type",
    "image": "Image",
    "userid": "User ID",
    "startTime": "Start Time",
    "expiryTime": "Expiry Time",
    "connectURL": "Connect URL",
    "runAsUID": "UID",
    "runAsGID": "GID",
    "supplementalGroups": "Groups",
    "appid": "App ID",
}


def _format(field: str, value: Any) -> str:
    """Format the value for display."""
    if field == "startTime" and isinstance(value, datetime):
        return humanize.naturaltime(value)
    if field == "expiryTime" and isinstance(value, datetime):
        now = datetime.now(timezone.utc)
        return humanize.precisedelta(value - now, minimum_unit="hours")
    return str(value)


def _utilization(used: float | str, requested: float | str, unit: str) -> str:
    """Calculate and format resource utilization."""
    if requested == "<none>":
        requested = 0
    if "M" in str(used):
        used = float(str(used).replace("M", "")) / 1024
    if "M" in str(requested):
        requested = float(str(requested).replace("M", "")) / 1024
    req_val = float(str(requested).replace("G", ""))
    if req_val == 0:
        return "[italic]Not Requested[/italic]"
    usage = 0.0 if used == "<none>" else float(used)
    percentage = (usage / req_val) * 100
    return f"{percentage:.0f}% [italic]of {requested} {unit}[/italic]"


def _display(session_info: dict[str, Any]) -> None:
    """Display information for a single session."""
    data = FetchResponse.model_validate(session_info)
    table = Table(
        title=f"CANFAR Session Info for {data.id}",
        box=box.SIMPLE,
        show_header=False,
    )
    table.add_column("Field", style="bold magenta")
    table.add_column("Value", overflow="fold")
    for field, header in ALL_FIELDS.items():
        value = getattr(data, field)
        display_value = _format(field, value)
        table.add_row(header, display_value)
    cpu_usage = _utilization(data.cpuCoresInUse, data.requestedCPUCores, "core(s)")
    ram_usage = _utilization(data.ramInUse, data.requestedRAM, "GB")
    gpu_usage = _utilization(data.gpuRAMInUse, data.requestedGPUCores, "core(s)")

    table.add_row("CPU Usage", cpu_usage)
    table.add_row("RAM Usage", ram_usage)
    table.add_row("GPU Usage", gpu_usage)
    console.print(table)


async def _get_info(
    session_ids: list[str],
    debug: bool,
) -> None:
    """Get detailed information about one or more sessions."""
    log_level = "DEBUG" if debug else "INFO"
    async with AsyncSession(loglevel=log_level) as session:
        sessions_info = await session.info(ids=session_ids)
    if not sessions_info:
        console.print(
            "[yellow]No information found for the specified session(s).[/yellow]"
        )
        return
    for response in sessions_info:
        _display(response)


@info.callback(invoke_without_command=True)
def get_info(
    session_ids: Annotated[
        list[str],
        typer.Argument(help="One or more session IDs."),
    ],
    debug: Annotated[
        bool,
        typer.Option(
            "--debug",
            help="Enable debug logging.",
        ),
    ] = False,
) -> None:
    """Get detailed information about one or more sessions."""
    asyncio.run(_get_info(session_ids, debug))
