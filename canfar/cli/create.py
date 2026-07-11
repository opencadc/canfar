"""CLI command to create canfar sessions."""

from __future__ import annotations

from typing import TYPE_CHECKING, Annotated, Any, get_args

import click
import typer

from canfar.cli._run import run
from canfar.cli.machine import maybe_emit_banner
from canfar.cli.output import OutputMode
from canfar.hooks.typer.aliases import AliasGroup
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
            get_console(stderr=True).print(
                f"[bold red]Error:[/bold red] Invalid env variable: {item}"
            )
            raise typer.Exit(1)
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
) -> None:
    """Launch a new session.

    Examples:
    canfar create notebook skaha/base-notebook:latest
    canfar create notebook images.canfar.net/skaha/base-notebook:latest
    canfar create headless skaha/base-notebook:latest -- python3 /path/to/script.py
    """
    maybe_emit_banner(OutputMode.HUMAN)
    cmd = None
    args = ""
    environment = _parse_environment(env)

    if command and len(command) > 0:
        cmd = command[0]
        args = " ".join(command[1:])

    async def _create() -> None:
        """Create the requested session(s) on the science platform server."""
        async with AsyncSession() as session:
            try:
                session_ids = await session.create(
                    name=name,
                    image=image,
                    cores=cpu,
                    ram=memory,
                    kind=kind,
                    gpu=gpu,
                    cmd=cmd or None,
                    args=args or None,
                    env=environment or None,
                    replicas=replicas,
                )
                if session_ids:
                    if len(session_ids) > 1:
                        get_console().print(
                            f"[bold green]Successfully created {len(session_ids)} "
                            f"sessions named '{name}':[/bold green]"
                        )
                        for session_id in session_ids:
                            get_console().print(f"  - {session_id}")
                        return

                    get_console().print(
                        f"[bold green]Successfully created session "
                        f"'{name}' (ID: {session_ids[0]})[/bold green]"
                    )
                    return
                get_console(stderr=True).print(
                    "[bold red]Failed to create session(s).[/bold red]"
                )
                get_console(stderr=True).print(
                    "[dim]No session IDs were returned. Run "
                    "`canfar --log-level debug create` for library logs, or set a "
                    "longer client timeout (environment variable CANFAR_TIMEOUT, in "
                    "seconds) if the image pull or platform is slow."
                    "[/dim]"
                )
            except KeyboardInterrupt:
                get_console(stderr=True).print(
                    "\n[bold yellow]Operation cancelled by user.[/bold yellow]"
                )
                raise typer.Exit(130) from KeyboardInterrupt
            except Exception as err:  # noqa: BLE001
                get_console(stderr=True).print(f"[bold red]Error: {err}[/bold red]")
                get_console(stderr=True).print_exception()
            raise typer.Exit(1)

    if dry or debug:
        details_console = get_console() if dry else get_console(stderr=True)
        details_console.print("[dim]Debug: Parsed parameters:[/dim]")
        details_console.print(f"[dim]  Kind: {kind}[/dim]")
        details_console.print(f"[dim]  Image: {image}[/dim]")
        details_console.print(f"[dim]  Name: {name}[/dim]")
        details_console.print(f"[dim]  CPUs: {cpu}[/dim]")
        details_console.print(f"[dim]  Memory: {memory}GB[/dim]")
        details_console.print(f"[dim]  GPU: {gpu}[/dim]")
        details_console.print(f"[dim]  Env: {environment}[/dim]")
        details_console.print(f"[dim]  Replicas: {replicas}[/dim]")
        details_console.print(f"[dim]  Command: {cmd}[/dim]")
        details_console.print(f"[dim]  Arguments: {args}[/dim]")
    if dry:
        get_console().print("[yellow]Dry run complete.[/yellow]")
        return

    run(_create())
