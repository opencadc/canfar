"""CLI command to create canfar sessions."""

from __future__ import annotations

import asyncio
from typing import Annotated, Any, get_args

import click
import typer
from rich.console import Console

from canfar.hooks.typer.aliases import AliasGroup
from canfar.models.types import Kind
from canfar.sessions import AsyncSession
from canfar.utils import funny

console = Console()

kinds: list[str] = list(get_args(Kind))
# Remove desktop-app from the list of kinds for usage message since,
# they can only be created from within a desktop session.
kinds.remove("desktop-app")


class CreateUsageMessage(AliasGroup):
    """Custom usage message for prune command.

    Args:
        typer (TyperGroup): Base class for grouping commands in Typer.
    """

    def get_usage(self, ctx: click.core.Context) -> str:  # noqa: ARG002
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
            click_type=click.Choice(kinds, case_sensitive=True),
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
            help="Enable debug logging.",
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
    cmd = None
    args = ""
    environment: dict[str, Any] = {}

    if command and len(command) > 0:
        cmd = command[0]
        args = " ".join(command[1:])

    if env:
        for item in env:
            if "=" not in item:
                console.print(
                    f"[bold red]Error:[/bold red] Invalid env variable: {item}"
                )
                raise typer.Exit(1)
            key, value = item.split("=", 1)
            environment[key] = value

    async def _create() -> None:
        log_level = "DEBUG" if debug else "INFO"
        async with AsyncSession(loglevel=log_level) as session:
            try:
                session_ids = await session.create(
                    name=name,
                    image=image,
                    cores=cpu,
                    ram=memory,
                    kind=kind,
                    gpu=gpu,
                    cmd=cmd if cmd else None,
                    args=args if args else None,
                    env=environment if environment else None,
                    replicas=replicas,
                )
                if session_ids:
                    if len(session_ids) > 1:
                        console.print(
                            f"[bold green]Successfully created {len(session_ids)} "
                            f"sessions named '{name}':[/bold green]"
                        )
                        for session_id in session_ids:
                            console.print(f"  - {session_id}")
                        return

                    console.print(
                        f"[bold green]Successfully created session "
                        f"'{name}' (ID: {session_ids[0]})[/bold green]"
                    )
                    return
                console.print("[bold red]Failed to create session(s).[/bold red]")
            except KeyboardInterrupt:
                console.print(
                    "\n[bold yellow]Operation cancelled by user.[/bold yellow]"
                )
                raise typer.Exit(130) from KeyboardInterrupt
            except Exception as err:  # noqa: BLE001
                console.print(f"[bold red]Error: {err}[/bold red]")
                console.print_exception()
            raise typer.Exit(1)

    if dry or debug:
        console.print("[dim]Debug: Parsed parameters:[/dim]")
        console.print(f"[dim]  Kind: {kind}[/dim]")
        console.print(f"[dim]  Image: {image}[/dim]")
        console.print(f"[dim]  Name: {name}[/dim]")
        console.print(f"[dim]  CPUs: {cpu}[/dim]")
        console.print(f"[dim]  Memory: {memory}GB[/dim]")
        console.print(f"[dim]  GPU: {gpu}[/dim]")
        console.print(f"[dim]  Env: {environment}[/dim]")
        console.print(f"[dim]  Replicas: {replicas}[/dim]")
        console.print(f"[dim]  Command: {cmd}[/dim]")
        console.print(f"[dim]  Arguments: {args}[/dim]")
    if dry:
        console.print("[yellow]Dry run complete.[/yellow]")
        return

    asyncio.run(_create())
