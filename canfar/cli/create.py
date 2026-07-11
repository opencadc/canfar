"""CLI command to create canfar sessions."""

from __future__ import annotations

from typing import TYPE_CHECKING, Annotated, Any, get_args

import click
import typer
from pydantic import ValidationError

from canfar.cli import output
from canfar.cli._run import run
from canfar.cli.machine import (
    JsonOption,
    YamlOption,
    maybe_emit_banner,
    resolve_mode,
)
from canfar.errors import ErrorCode, StructuredError
from canfar.hooks.typer.aliases import AliasGroup
from canfar.models.session import CreateRequest
from canfar.models.types import Kind
from canfar.sessions import AsyncSession
from canfar.utils import funny
from canfar.utils.console import get_console

if TYPE_CHECKING:
    from typer._click.core import Context

kinds: list[str] = list(get_args(Kind))
# Remove desktop-app from the list of kinds for usage message since,
# they can only be created from within a desktop session.
kinds.remove("desktop-app")


class CreateUsageMessage(AliasGroup):
    """Custom usage message for prune command.

    Args:
        typer (TyperGroup): Base class for grouping commands in Typer.
    """

    def get_usage(self, ctx: Context) -> str:  # noqa: ARG002
        """Get the usage message for the prune command.

        Args:
            ctx (typer.Context): The Typer context.

        Returns:
            str: The usage message.
        """
        return "Usage: canfar create [OPTIONS] KIND IMAGE [-- CMD [ARGS]...]"


create = typer.Typer(
    name="create",
    no_args_is_help=True,
    cls=CreateUsageMessage,
)


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


@create.callback(
    invoke_without_command=True,
    context_settings={
        "help_option_names": ["-h", "--help"],
        "allow_interspersed_args": True,
    },
)
def creation(
    kind: Annotated[
        Kind,
        typer.Argument(
            ...,
            click_type=click.Choice(kinds, case_sensitive=True),  # ty: ignore[invalid-argument-type]
            metavar="|".join(kinds),
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
            help="Number of CPU cores.",
            show_default="flexible: ≤8 cores",
        ),
    ] = None,
    memory: Annotated[
        int | None,
        typer.Option(
            "--memory",
            "-m",
            help="Amount of RAM in GB.",
            show_default="flexible: ≤32 GB",
        ),
    ] = None,
    gpu: Annotated[
        int | None, typer.Option("--gpu", "-g", help="Number of GPUs.")
    ] = None,
    env: Annotated[
        list[str] | None,
        typer.Option(
            "--env", "-e", help="Set environment variables.", metavar="KEY=VALUE"
        ),
    ] = None,
    replicas: Annotated[
        int, typer.Option("--replicas", "-r", help="Number of replicas to create.")
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
    json_output: JsonOption = False,
    yaml_output: YamlOption = False,
) -> None:
    """Launch a new session.

    Examples:
    canfar create notebook skaha/base-notebook:latest
    canfar create notebook images.canfar.net/skaha/base-notebook:latest
    canfar create headless skaha/base-notebook:latest -- python3 /path/to/script.py
    """
    mode = resolve_mode(json_output, yaml_output)
    maybe_emit_banner(mode)
    if dry and mode is not output.OutputMode.HUMAN:
        typer.echo(
            "Incompatible flags: --dry-run cannot be used with --json or --yaml.",
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
            gpus=gpu,
            cmd=cmd or None,
            args=args or None,
            env=environment or None,
            replicas=replicas,
        )
    except ValueError as err:
        if mode is output.OutputMode.HUMAN:
            get_console(stderr=True).print(f"[bold red]Error: {err}[/bold red]")
            if isinstance(err, ValidationError):
                get_console(stderr=True).print_exception()
        else:
            output.to_stderr(
                StructuredError(
                    code=ErrorCode.COMMAND_VALIDATION_FAILED,
                    message="Session request validation failed.",
                    hint="Check the create arguments and retry.",
                ),
                mode,
            )
        raise typer.Exit(1) from err

    async def _create() -> None:
        """Create the requested session(s) on the science platform server."""
        try:
            async with AsyncSession() as session:
                session_ids = await session.create(request)
        except KeyboardInterrupt:
            if mode is output.OutputMode.HUMAN:
                get_console(stderr=True).print(
                    "\n[bold yellow]Operation cancelled by user.[/bold yellow]"
                )
            else:
                output.to_stderr(
                    StructuredError(
                        code=ErrorCode.COMMAND_CANCELLED,
                        message="Operation cancelled by user.",
                        hint="Retry the command when ready.",
                    ),
                    mode,
                )
            raise typer.Exit(130) from KeyboardInterrupt
        except Exception as err:
            if mode is output.OutputMode.HUMAN:
                get_console(stderr=True).print(f"[bold red]Error: {err}[/bold red]")
                get_console(stderr=True).print_exception()
            else:
                output.to_stderr(
                    StructuredError(
                        code=ErrorCode.TRANSPORT_FAILURE,
                        message="Unable to create session(s).",
                        hint=(
                            "Check authentication and Science Platform "
                            "connectivity, then retry."
                        ),
                    ),
                    mode,
                )
            raise typer.Exit(1) from err

        if session_ids:
            if mode is not output.OutputMode.HUMAN:
                return output.to_stdout(session_ids, mode)
            if len(session_ids) > 1:
                return get_console().print(
                    f"[bold green]Successfully created {len(session_ids)} "
                    f"sessions named '{name}':[/bold green]\n"
                    + "\n".join(f"  - {session_id}" for session_id in session_ids)
                )

            return get_console().print(
                f"[bold green]Successfully created session "
                f"'{name}' (ID: {session_ids[0]})[/bold green]"
            )

        failure = StructuredError(
            code=ErrorCode.TRANSPORT_FAILURE,
            message="Failed to create session(s).",
            hint=(
                "No session IDs were returned. Run `canfar --log-level debug create` "
                "for library logs, or set a longer client timeout (environment "
                "variable CANFAR_TIMEOUT, in seconds) if the image pull or platform "
                "is slow."
            ),
        )
        if mode is not output.OutputMode.HUMAN:
            output.to_stderr(failure, mode)
        else:
            get_console(stderr=True).print(
                f"[bold red]{failure.message}[/bold red]\n[dim]{failure.hint}[/dim]"
            )
        raise typer.Exit(1)

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
    if not dry:
        run(_create())
