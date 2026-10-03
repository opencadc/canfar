"""CLI command to create canfar sessions."""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING, Annotated, Any, cast, get_args

import typer
from httpx2 import HTTPError
from pydantic import ValidationError
from rich.markup import escape
from typer.core import TyperOption

from canfar.cli import output
from canfar.cli.machine import OutputOption, maximum, resolve_mode
from canfar.config.migration import ConfigResetRequiredError
from canfar.errors import ErrorCode, StructuredError
from canfar.exceptions.context import AuthContextError, AuthExpiredError
from canfar.hooks.httpx.auth import AuthenticationError
from canfar.models.config import Configuration
from canfar.models.http import ServerResources
from canfar.models.session import CreateRequest
from canfar.models.types import Pruneable
from canfar.sessions import AsyncSession
from canfar.utils import funny
from canfar.utils.console import emit_cli_active_server_banner, get_console

if TYPE_CHECKING:
    from typer._click.core import Parameter
    from typer._click.types import IntRange

    from canfar.models.http import ResourceRange

Creatable = Pruneable
"""Session kinds the CLI creates; desktop-app starts only inside a desktop."""


def _parse_environment(env: list[str] | None) -> dict[str, Any]:
    """Parse repeated ``KEY=VALUE`` options for the session request."""
    environment: dict[str, Any] = {}
    for item in env or []:
        if "=" not in item:
            message = f"Invalid env variable: {item}"
            raise ValueError(message)
        key, value = item.split("=", 1)
        environment[key] = value
    return environment


# Client bounds from ``CreateRequest``; saved Server limits narrow the first three.
_MAX_CORES = maximum(CreateRequest, "cores")
_MAX_RAM_GB = maximum(CreateRequest, "ram")
_MAX_GPUS = maximum(CreateRequest, "gpus")
_MAX_REPLICAS = maximum(CreateRequest, "replicas")

_CPU_HELP = "Number of CPU cores."
_MEMORY_HELP = "Amount of RAM in GB."


def _active_resources() -> ServerResources | None:
    """Return the active Server's saved limits, when known.

    Limits are saved during discovery and Server Selection.
    """
    try:
        config = Configuration()  # ty: ignore[missing-argument]
    except (ConfigResetRequiredError, ValueError):
        return None
    name = config.active.server
    server = config.servers.get(name) if name is not None else None
    return server.resources if server is not None else None


def apply_server_limits(params: list[Parameter]) -> None:
    """Narrow ``--cpu``, ``--memory``, and ``--gpu`` to the active Server.

    Runs before ``create`` parses its arguments, so Typer both validates
    requests against, and shows in help, the ranges of the Server a new
    Session would use, with its flexible range as the default. Unknown limits
    keep the client bounds and the generic default.
    """
    resources = _active_resources()
    if resources is None:
        resources = ServerResources()
    options = {param.name: param for param in params if isinstance(param, TyperOption)}
    _narrow(options["cpu"], resources.fixed.cores, _MAX_CORES)
    _narrow(options["memory"], resources.fixed.ram, _MAX_RAM_GB)
    _narrow(options["gpu"], resources.gpus, _MAX_GPUS)
    options["cpu"].help = _with_default(_CPU_HELP, resources.flexible.cores)
    options["memory"].help = _with_default(_MEMORY_HELP, resources.flexible.ram)


def _narrow(option: TyperOption, bounds: ResourceRange | None, maximum: int) -> None:
    """Accept the values both the client and the Server allow in ``option``.

    A Server that offers none, such as no GPUs, accepts only ``0``.
    """
    low, high = 1, maximum
    if bounds is not None:
        low, high = max(low, bounds.min), min(high, bounds.max)
        if low > high:
            low = high = 0
    option.type = cast("type[IntRange]", type(option.type))(min=low, max=high)


def _with_default(text: str, bounds: ResourceRange | None) -> str:
    """Append the flexible burst limit as the default, styled like Typer's.

    Typer wraps a string ``show_default`` in parentheses, so the default is
    part of the Rich markup help instead.
    """
    flexible = (
        f"flexible ≤ {bounds.max}"
        if bounds is not None
        else "flexible, set by the Server"
    )
    return f"{text} [dim]{escape(f'[default: {flexible}]')}[/dim]"


async def _create_sessions(request: CreateRequest) -> list[str]:
    """Create the requested Sessions on the selected Science Platform Server."""
    async with AsyncSession() as session:
        return await session.create(request)


def _render_create_result(
    session_ids: list[str],
    name: str,
    mode: output.OutputMode,
) -> None:
    """Render the result of a Session creation request."""
    if session_ids:
        if mode is not output.OutputMode.HUMAN:
            output.to_stdout(session_ids, mode)
        elif len(session_ids) > 1:
            get_console().print(
                f"[bold green]Successfully created {len(session_ids)} "
                f"sessions named '{name}':[/bold green]\n"
                + "\n".join(f"  - {session_id}" for session_id in session_ids)
            )
        else:
            get_console().print(
                f"[bold green]Successfully created session "
                f"'{name}' (ID: {session_ids[0]})[/bold green]"
            )
        return

    failure = StructuredError(
        code=ErrorCode.TRANSPORT_FAILURE,
        message="Failed to create session(s).",
        hint=(
            "No session IDs were returned. Run `canfar --log-level debug create` "
            "for library logs, or set a longer client timeout (environment "
            "variable CANFAR_TIMEOUT, in seconds) for slow HTTP responses. "
            "Check `canfar ps --all` before retrying: a request may have been "
            "accepted even if its response was lost. For accepted IDs, use "
            "`canfar events SESSION_ID` to inspect image pulls or admission."
        ),
    )
    output.fail(failure, mode)


def creation(  # noqa: PLR0917
    kind: Annotated[
        Creatable,
        typer.Argument(
            ...,
            metavar="|".join(get_args(Creatable)),
            help="Session Kind.",
        ),
    ],
    image: Annotated[
        str,
        typer.Argument(help="Container Image."),
    ],
    command: Annotated[
        list[str] | None,
        typer.Argument(help="Runtime Command + Arguments.", metavar="CMD [ARGS]..."),
    ] = None,
    name: Annotated[
        str, typer.Option("--name", "-n", help="Name of the session.")
    ] = funny.name(),
    cpu: Annotated[
        int | None,
        typer.Option(
            "--cpu",
            "-c",
            help=_with_default(_CPU_HELP, None),
            min=1,
            max=_MAX_CORES,
        ),
    ] = None,
    memory: Annotated[
        int | None,
        typer.Option(
            "--memory",
            "-m",
            help=_with_default(_MEMORY_HELP, None),
            min=1,
            max=_MAX_RAM_GB,
        ),
    ] = None,
    gpu: Annotated[
        int | None,
        typer.Option("--gpu", "-g", help="Number of GPUs.", min=1, max=_MAX_GPUS),
    ] = None,
    env: Annotated[
        list[str] | None,
        typer.Option(
            "--env", "-e", help="Set environment variables.", metavar="KEY=VALUE"
        ),
    ] = None,
    replicas: Annotated[
        int,
        typer.Option(
            "--replicas",
            "-r",
            help="Number of replicas to create.",
            min=1,
            max=_MAX_REPLICAS,
        ),
    ] = 1,
    debug: Annotated[
        bool,
        typer.Option(
            "--debug",
            help="Print parsed Session request details.",
        ),
    ] = False,
    dry: Annotated[
        bool,
        typer.Option(
            "--dry-run",
            help="Dry run. Parse parameters and exit.",
        ),
    ] = False,
    output_format: OutputOption = None,
) -> None:
    """Launch a new session.

    Examples:
    canfar create notebook skaha/base-notebook:latest
    canfar create notebook images.canfar.net/skaha/base-notebook:latest
    canfar create headless skaha/base-notebook:latest -- python3 /path/to/script.py
    """
    mode = resolve_mode(output_format)
    if mode is output.OutputMode.HUMAN:
        emit_cli_active_server_banner()
    if dry and mode is not output.OutputMode.HUMAN:
        typer.echo(
            "Incompatible flags: --dry-run cannot be used with --output json or "
            "--output yaml.",
            err=True,
        )
        raise typer.Exit(output.OUTPUT_CONFLICT_EXIT_CODE)

    cmd, args = (command[0], " ".join(command[1:])) if command else (None, "")

    try:
        environment = _parse_environment(env)
        request = CreateRequest(
            name=name,
            image=image,
            cores=cpu,
            ram=memory,
            kind=kind,
            gpus=gpu or None,
            cmd=cmd or None,
            args=args or None,
            env=environment or None,
            replicas=replicas,
        )
    except ValueError as err:
        if isinstance(err, ValidationError) and mode is output.OutputMode.HUMAN:
            get_console(stderr=True).print_exception()
        output.fail(
            StructuredError(
                code=ErrorCode.COMMAND_VALIDATION_FAILED,
                message="Session request validation failed.",
                hint="Check the create arguments and retry.",
            ),
            mode,
            f"[bold red]Error: {escape(str(err))}[/bold red]",
        )

    if dry or debug:
        (get_console() if dry else get_console(stderr=True)).print(
            "[dim]Debug: Parsed parameters:[/dim]\n"
            f"[dim]  Kind: {kind}[/dim]\n"
            f"[dim]  Image: {image}[/dim]\n"
            f"[dim]  Name: {name}[/dim]\n"
            f"[dim]  CPUs: {cpu}[/dim]\n"
            f"[dim]  Memory: {memory}GB[/dim]\n"
            f"[dim]  GPU: {gpu}[/dim]\n"
            f"[dim]  Env: {environment}[/dim]\n"
            f"[dim]  Replicas: {replicas}[/dim]\n"
            f"[dim]  Command: {cmd}[/dim]\n"
            f"[dim]  Arguments: {args}[/dim]"
            + ("\n[yellow]Dry run complete.[/yellow]" if dry else "")
        )
    if dry:
        return

    try:
        session_ids = asyncio.run(_create_sessions(request))
    except KeyboardInterrupt:
        output.fail(
            StructuredError(
                code=ErrorCode.COMMAND_CANCELLED,
                message="Operation cancelled by user.",
                hint="Retry the command when ready.",
            ),
            mode,
            "\n[bold yellow]Operation cancelled by user.[/bold yellow]",
            code=130,
        )
    except (
        ConfigResetRequiredError,
        AuthExpiredError,
        AuthContextError,
        AuthenticationError,
        HTTPError,
    ) as err:
        output.fail(
            output.boundary_failure(
                err, transport_message="Unable to create session(s)."
            ),
            mode,
            f"[bold red]Error: {escape(str(err))}[/bold red]",
        )

    _render_create_result(session_ids, name, mode)
