"""CLI command to get information for canfar sessions."""

from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from typing import Annotated, Any

import humanize
import typer
from pydantic import ValidationError
from rich import box
from rich.table import Table

from canfar.models.session import FetchResponse
from canfar.sessions import AsyncSession
from canfar.utils.console import console

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
    if value in (None, "", []):
        return "[italic]Unknown[/italic]"
    if field == "startTime" and isinstance(value, datetime):
        return humanize.naturaltime(value)
    if field == "expiryTime" and isinstance(value, datetime):
        now = datetime.now(timezone.utc)
        return humanize.precisedelta(value - now, minimum_unit="hours")
    return str(value)


def _utilization(
    data: FetchResponse,
    used_field: str,
    requested_field: str,
    unit: str,
) -> str:
    """Calculate and format resource utilization."""
    used = getattr(data, used_field)
    requested = getattr(data, requested_field)
    requested_display = requested

    if not data.isFixedResources:
        if used in (None, "<none>", "", []):
            return "[italic]Unknown[/italic]"
        return f"{used} {unit}"

    if requested in (None, "<none>", "", []):
        requested = 0
    if used in (None, "<none>", "", []):
        used = 0

    def _to_number(value: float | str) -> float:
        """Best-effort conversion of resource strings to floats."""
        if isinstance(value, (int, float)):
            return float(value)
        text = str(value).strip()
        if text in {"", "<none>"}:
            return 0.0
        multiplier = 1.0
        if text.endswith(("Mi", "mi")):
            multiplier = 1 / 1024
            text = text[:-2]
        elif text.endswith(("M", "m")):
            multiplier = 1 / 1024 if text.endswith("M") else 1 / 1000
            text = text[:-1]
        elif text.endswith(("Gi", "gi")):
            multiplier = 1.0
            text = text[:-2]
        elif text.endswith("G"):
            multiplier = 1.0
            text = text[:-1]
        try:
            return float(text or 0) * multiplier
        except ValueError:
            return 0.0

    req_val = _to_number(requested)
    if req_val == 0:
        return "[italic]Not Requested[/italic]"
    usage = _to_number(used)
    percentage = (usage / req_val) * 100
    display = requested_display if requested_display not in (None, "", []) else req_val
    return f"{percentage:.0f}% [italic]of {display} {unit}[/italic]"


def _display(session_info: dict[str, Any], debug: bool = False) -> None:
    """Display information for a single session."""
    try:
        data = FetchResponse.model_validate(session_info)
    except ValidationError as err:
        session_id = str(session_info.get("id", "<unknown>"))
        details = err.errors()[0]["msg"] if err.errors() else str(err)
        fallback = {
            "id": session_id,
            "type": str(session_info.get("type", "Unknown") or "Unknown"),
            "status": str(session_info.get("status", "Unknown") or "Unknown"),
            "name": session_info.get("name") or session_id,
            "isFixedResources": session_info.get("isFixedResources", True),
        }
        data = FetchResponse.model_validate(fallback)
        data.anomalies.append(
            f"{session_id}: encountered validation issues ({details})"
        )

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
    cpu_usage = _utilization(data, "cpuCoresInUse", "requestedCPUCores", "core(s)")
    ram_usage = _utilization(data, "ramInUse", "requestedRAM", "GB")
    gpu_usage = _utilization(data, "gpuRAMInUse", "requestedGPUCores", "core(s)")

    table.add_row("CPU Usage", cpu_usage)
    table.add_row("RAM Usage", ram_usage)
    table.add_row("GPU Usage", gpu_usage)
    console.print(table)

    if debug and data.anomalies:
        console.print("[yellow]Session Response Warnings:[/yellow]")
        for note in dict.fromkeys(data.anomalies):
            console.print(f"[dim]- {note}[/dim]")


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
        _display(response, debug=debug)


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
