"""CLI command to create Skaha sessions."""

from __future__ import annotations

import asyncio
from typing import Annotated, Any, get_args

import click
import typer
from rich.console import Console

from skaha.hooks.typer.aliases import AliasGroup
from skaha.models.types import Kind
from skaha.session import AsyncSession
from skaha.utils import funny

console = Console()


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
        return "Usage: skaha create [OPTIONS] KIND IMAGE -- CMD [ARGS]... "


create = typer.Typer(
    name="create",
    no_args_is_help=True,
    cls=AliasGroup,
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
            click_type=click.Choice(list(get_args(Kind)), case_sensitive=True),
            metavar="|".join(list(get_args(Kind))),
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
    cpu: Annotated[int, typer.Option("--cpu", "-c", help="Number of CPU cores.")] = 1,
    memory: Annotated[
        int, typer.Option("--memory", "-m", help="Amount of RAM in GB.")
    ] = 2,
    gpu: Annotated[
        int | None, typer.Option("--gpu", "-g", help="Number of GPUs.")
    ] = None,
    env: Annotated[
        list[str] | None,
        typer.Option(
            "--env", "-e", help="Environment variables (e.g., --env KEY=VALUE)."
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
            help="Perform a dry run without actually creating the session.",
        ),
    ] = False,
) -> None:
    """Launch a new session.

    Examples:
    skaha create notebook skaha/base-notebook:latest
    skaha create notebook images.canfar.net/skaha/base-notebook:latest
    skaha create headless skaha/base-notebook:latest -- python3 -V
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
