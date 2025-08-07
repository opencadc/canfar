"""Login command for Science Platform CLI."""

from __future__ import annotations

import asyncio
from typing import Annotated

import typer
from pydantic import AnyHttpUrl, AnyUrl
from rich import box
from rich.console import Console
from rich.prompt import Confirm
from rich.table import Table

from skaha import CONFIG_PATH, get_logger, set_log_level
from skaha.auth import oidc, x509
from skaha.hooks.typer.aliases import AliasGroup
from skaha.models.auth import (
    OIDC,
    X509,
    Client,
    Endpoint,
    Expiry,
    Token,
)
from skaha.models.config import AuthContext, Configuration
from skaha.models.http import Server
from skaha.utils.discover import servers

console = Console()
log = get_logger(__name__)


auth = typer.Typer(
    name="auth",
    help="Authentication Commands",
    no_args_is_help=True,
    rich_help_panel="Authentication",
    cls=AliasGroup,
)


@auth.command("login")
def login(
    force: Annotated[
        bool,
        typer.Option(
            "--force",
            help="Force re-authentication",
        ),
    ] = False,
    debug: Annotated[
        bool,
        typer.Option(
            "--debug",
            help="Enable debug logging",
        ),
    ] = False,
    dead: Annotated[
        bool,
        typer.Option(
            "--dead",
            help="Include dead servers in discovery",
        ),
    ] = False,
    dev: Annotated[
        bool,
        typer.Option(
            "--dev",
            help="Include dev servers in discovery",
        ),
    ] = False,
    details: Annotated[
        bool,
        typer.Option(
            "--details",
            help="Include server details in discovery",
        ),
    ] = False,
    discovery_url: Annotated[
        str,
        typer.Option(
            "--discovery-url",
            "-d",
            help="OIDC Discovery URL",
        ),
    ] = "https://ska-iam.stfc.ac.uk/.well-known/openid-configuration",
) -> None:
    """Login to Science Platform.

    This command will guide you through the authentication process,
    automatically discovering the upstream server and choosing the
    appropriate authentication method based on the server's configuration.
    """
    if debug:
        set_log_level("DEBUG")
        log.debug("Debug logging enabled")

    try:
        console.print("[bold blue]Starting Science Platform Login[/bold blue]")
        config = Configuration()
        if not force and not config.context.expired and config.context.server:
            console.print("[green]✓[/green] Credentials valid")
            console.print(
                f"[green]✓[/green] Authenticated with {config.context.server.name} @ "
                f"{config.context.server.url}"
            )
            console.print("[dim] Use --force to re-authenticate.[dim]")
            return

        # Run discovery and get selected server
        selected = asyncio.run(servers(dev=dev, dead=dead, details=details))
        log.debug("Selected server: %s", selected)
        server: Server = Server(
            name=f"{selected.registry}-{selected.name}",
            uri=AnyUrl(selected.uri),
            url=AnyHttpUrl(selected.url),
            version="v0",
        )

        # Step 7-8: Choose authentication method based on registry
        context: AuthContext
        if selected.registry.upper() == "CADC":
            console.print("[bold blue]X509 Certificate Authentication[/bold blue]")
            # Create new X509 context with server information
            x509_context = X509(server=server, expiry=0.0)
            # Authenticate and get updated context
            context = x509.authenticate(x509_context)
        else:
            console.print(
                f"[bold blue]OIDC Authentication for {selected.url}[/bold blue]"
            )
            # Create new OIDC context with server and discovery information
            oidc_context = OIDC(
                server=server,
                endpoints=Endpoint(discovery=discovery_url),
                client=Client(),
                token=Token(),
                expiry=Expiry(),
            )
            # Authenticate and get updated context
            context = asyncio.run(oidc.authenticate(oidc_context))

        # Add the new context to the configuration
        name = server.name or f"{selected.registry}-{selected.name}"
        config.contexts[name] = context
        config.active = name

        console.print("[green]✓[/green] Saving configuration")
        config.save()
        console.print("[bold green]Login completed successfully![/bold green]")

    except Exception as error:
        console.print(f"[bold red]Login failed: {error}[/bold red]")
        raise typer.Exit(1) from error


@auth.command("list, ls")
def show() -> None:
    """Show all available auth contexts."""
    config = Configuration()
    table = Table(
        title="Available Authentication Contexts",
        show_lines=True,
        box=box.SIMPLE,
    )
    table.add_column("Active", justify="center", style="cyan")
    table.add_column("Name", style="magenta")
    table.add_column("Auth Mode", justify="center", style="green")
    table.add_column("Server URL", style="blue")

    for name, context in config.contexts.items():
        is_active = "✅" if name == config.active else ""
        table.add_row(
            is_active,
            name,
            context.mode,
            str(context.server.url) if context.server else "N/A",
        )
    console.print(table)


@auth.command("switch, use")
def switch_context(
    context: Annotated[
        str,
        typer.Argument(help="The name of the context to activate."),
    ],
) -> None:
    """Switch the active auth context."""
    config = Configuration()
    if context not in config.contexts:
        console.print(
            f"[bold red]Context [italic]{context}[/italic] not found.[/bold red]"
        )
        console.print(f"Available contexts are: {list(config.contexts.keys())}")
        raise typer.Exit(1)

    config.active = context
    config.save()
    console.print(f"[green]✓[/green] Switched active context to [bold]{context}[/bold]")


@auth.command("remove, rm")
def remove_context(
    context: Annotated[
        str,
        typer.Argument(help="The name of the context to remove."),
    ],
) -> None:
    """Remove specific auth context."""
    try:
        config = Configuration()
    except Exception as error:
        console.print(f"[bold red]Error: {error}[/bold red]")
        raise typer.Exit(1) from error

    if context not in config.contexts:
        console.print(f"[bold red]Error:[/bold red] Context '{context}' not found.")
        console.print(f"Available contexts are: {list(config.contexts.keys())}")
        raise typer.Exit(1)

    if context == "default":
        console.print(
            "[bold red]Cannot remove the default context. Its always there![/bold red] "
        )
        raise typer.Exit(1)

    if context == config.active:
        console.print(
            f"[bold red]Cannot remove the active context '{context}'[/bold red] ."
        )
        console.print(
            "Please switch to another context first with 'skaha auth switch <CONTEXT>'."
        )
        raise typer.Exit(1)

    del config.contexts[context]
    config.save()
    console.print(f"[green]✓[/green] Removed context [bold]{context}[/bold]")


@auth.command("purge")
def purge(
    confirm: Annotated[
        bool,
        typer.Option(
            "--yes",
            "-y",
            help="Skip confirmation prompt",
        ),
    ] = False,
) -> None:
    """Remove all auth contexts."""
    if not confirm:
        should_purge = Confirm.ask(
            "This will remove all stored authentication credentials. Continue?"
        )
        if not should_purge:
            console.print("[yellow]Logout cancelled[/yellow]")
            raise typer.Exit(0)

    try:
        # Delete the configuration file entirely
        CONFIG_PATH.unlink()
        console.print("[green]✓[/green] Authentication credentials cleared")
    except FileNotFoundError:
        console.print("[yellow]No configuration found to clear[/yellow]")
    except Exception as error:
        console.print(f"[bold red]Error during purge: {error}[/bold red]")
        raise typer.Exit(1) from error


if __name__ == "__main__":
    auth()
