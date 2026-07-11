"""CLI command to list canfar sessions."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import TYPE_CHECKING, Annotated, get_args

import click
import httpx
import humanize
import typer
from pydantic import ValidationError
from rich import box
from rich.table import Table

from canfar.cli import output
from canfar.cli._run import run
from canfar.cli.machine import JsonOption, YamlOption, maybe_emit_banner, resolve_mode
from canfar.config.migration import ConfigResetRequiredError
from canfar.errors import ErrorCode, StructuredError
from canfar.exceptions.context import AuthContextError, AuthExpiredError
from canfar.hooks.typer.aliases import AliasGroup
from canfar.models.session import FetchResponse
from canfar.models.types import Kind, Status
from canfar.sessions import AsyncSession
from canfar.utils.console import get_console

if TYPE_CHECKING:
    from typing import NoReturn

ps = typer.Typer(
    name="ps",
    no_args_is_help=False,
    cls=AliasGroup,
)


async def _fetch_sessions(
    kind: Kind | None,
    status: Status | None,
) -> list[dict[str, str]]:
    """Fetch sessions at the external Science Platform boundary."""
    async with AsyncSession() as session:
        return await session.fetch(kind=kind, status=status)


def _raise_fetch_failure(
    error: Exception,
    failure: StructuredError,
    mode: output.OutputMode,
) -> NoReturn:
    """Render one expected fetch failure and preserve exit code one."""
    if mode is output.OutputMode.HUMAN:
        get_console(stderr=True).print(f"[bold red]Error:[/bold red] {failure.message}")
    else:
        output.to_stderr(failure, mode)
    raise typer.Exit(1) from error


def _fetch_session_payloads(
    kind: Kind | None,
    status: Status | None,
    mode: output.OutputMode,
) -> list[dict[str, str]]:
    """Fetch session payloads and map expected boundary failures."""
    try:
        return run(_fetch_sessions(kind, status))
    except ConfigResetRequiredError as err:
        _raise_fetch_failure(
            err,
            StructuredError(
                code=err.code,
                message=err.message,
                hint="Reset the configuration and log in again.",
            ),
            mode,
        )
    except AuthExpiredError as err:
        _raise_fetch_failure(
            err,
            StructuredError(
                code=ErrorCode.AUTHENTICATION_EXPIRED,
                message=str(err),
                hint="Authenticate again and retry.",
            ),
            mode,
        )
    except AuthContextError as err:
        _raise_fetch_failure(
            err,
            StructuredError(
                code=ErrorCode.AUTHENTICATION_CREDENTIAL_INVALID,
                message=str(err),
                hint="Check the active Authentication Record and retry.",
            ),
            mode,
        )
    except httpx.HTTPError as err:
        _raise_fetch_failure(
            err,
            StructuredError(
                code=ErrorCode.TRANSPORT_FAILURE,
                message="Unable to list sessions.",
                hint=(
                    "Check authentication and Science Platform connectivity, "
                    "then retry."
                ),
            ),
            mode,
        )


def _sanitize_sessions(
    payloads: list[dict[str, str]],
) -> tuple[list[FetchResponse], list[str]]:
    """Validate and sort session payloads while collecting anomalies."""
    sessions: list[FetchResponse] = []
    anomalies: list[str] = []
    for payload in payloads:
        try:
            session = FetchResponse.model_validate(payload)
        except ValidationError as err:
            typer.echo(f"Error: {err}", err=True)
            continue
        sessions.append(session)
        anomalies.extend(session.anomalies)

    sessions.sort(
        key=lambda item: item.startTime or datetime.max.replace(tzinfo=timezone.utc)
    )
    return sessions, anomalies


def _session_table(sessions: list[FetchResponse]) -> Table:
    """Build the human-readable session table."""
    table = Table(title="CANFAR Sessions", box=box.SIMPLE)
    table.add_column("SESSION ID", style="cyan")
    table.add_column("NAME", style="magenta")
    table.add_column("KIND", style="green")
    table.add_column("STATUS", style="green")
    table.add_column("IMAGE", style="blue")
    table.add_column("CREATED", style="yellow")

    for session in sessions:
        created = "unknown"
        if session.startTime:
            uptime = datetime.now(timezone.utc) - session.startTime
            created = humanize.naturaldelta(uptime)
        table.add_row(
            session.id,
            session.name or session.id,
            session.type,
            session.status,
            session.image,
            created,
        )
    return table


def _render_human_sessions(
    sessions: list[FetchResponse],
    anomalies: list[str],
    *,
    quiet: bool,
    everything: bool,
    debug: bool,
) -> None:
    """Render one human-mode view of the visible session sequence."""
    if quiet:
        for session in sessions:
            get_console().print(session.id)
        return

    if not sessions and not everything:
        get_console(stderr=True).print(
            "[yellow]No pending or running sessions found.[/yellow]"
        )
        get_console(stderr=True).print(
            "[dim]Use [italic]--all[/italic] to show all sessions.[/dim]"
        )
    else:
        get_console().print(_session_table(sessions))

    if anomalies and debug:
        get_console(stderr=True).print("[yellow]Session Response Warnings:[/yellow]")
        for message in dict.fromkeys(anomalies):
            get_console(stderr=True).print(f"[dim]- {message}[/dim]")


@ps.callback(invoke_without_command=True)
def show(
    everything: Annotated[
        bool,
        typer.Option(
            "--all", "-a", help="Show all sessions (default shows just running)."
        ),
    ] = False,
    quiet: Annotated[
        bool,
        typer.Option("--quiet", "-q", help="Only show session IDs."),
    ] = False,
    kind: Annotated[
        Kind | None,
        typer.Option(
            "--kind",
            "-k",
            click_type=click.Choice(list(get_args(Kind)), case_sensitive=True),  # ty: ignore[invalid-argument-type]
            metavar="|".join(get_args(Kind)),
            help="Filter by session kind.",
        ),
    ] = None,
    status: Annotated[
        Status | None,
        typer.Option(
            "--status",
            "-s",
            click_type=click.Choice(list(get_args(Status)), case_sensitive=True),  # ty: ignore[invalid-argument-type]
            metavar="|".join(get_args(Status)),
            help="Filter by session status.",
        ),
    ] = None,
    debug: Annotated[
        bool,
        typer.Option(
            "--debug",
            help="Show Session response warnings.",
        ),
    ] = False,
    json_output: JsonOption = False,
    yaml_output: YamlOption = False,
) -> None:
    """Show sessions."""
    mode = resolve_mode(json_output, yaml_output)
    maybe_emit_banner(mode)

    if quiet and mode is not output.OutputMode.HUMAN:
        typer.echo(
            "Incompatible flags: --quiet is human-only and cannot be used with "
            "--json or --yaml.",
            err=True,
        )
        raise typer.Exit(output.OUTPUT_CONFLICT_EXIT_CODE)

    sessions, anomalies = _sanitize_sessions(
        _fetch_session_payloads(kind, status, mode)
    )

    visible = [
        instance
        for instance in sessions
        if everything or instance.status in ["Pending", "Running"]
    ]

    if mode is not output.OutputMode.HUMAN:
        output.to_stdout(visible, mode)
        return

    _render_human_sessions(
        visible,
        anomalies,
        quiet=quiet,
        everything=everything,
        debug=debug,
    )
