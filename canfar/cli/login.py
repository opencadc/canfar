"""Top-level login command for CANFAR CLI."""

from __future__ import annotations

from typing import Annotated

import typer

from canfar import CONFIG_PATH
from canfar.cli import output
from canfar.cli.login_auth import authenticate_for_cli
from canfar.cli.machine import maybe_emit_banner
from canfar.cli.prompts import select_idp, select_server
from canfar.idp import get_idp, list_idps
from canfar.models.config import Configuration
from canfar.server import (
    ServerDiscoveryError,
    ServerFetchError,
    ServerSelectorError,
    activate,
    discover,
)
from canfar.utils.console import get_console


def _authentication_exists_on_disk(idp: str) -> bool:
    """Return whether persisted Authentication exists for an IDP.

    In-memory default placeholder credentials are ignored until a config file
    has been written to disk.

    Args:
        idp: Canonical Identity Provider key.

    Returns:
        True when ``idp`` is saved in the on-disk configuration file.
    """
    if not CONFIG_PATH.exists():
        return False
    config = Configuration()  # ty: ignore[missing-argument]
    return idp in config.authentication


def _login_flow(
    idp: str,
    *,
    force: bool = False,
    dev: bool = False,
    timeout: int = 10,
) -> None:
    """Run the guided login flow for ``idp``.

    Authenticates interactively, discovers servers, selects a server, and
    atomically saves the active Authentication and Server pair.

    Args:
        idp: Canonical Identity Provider key.
        force: When ``True``, overwrite an existing saved Authentication record.
        dev: Include development registries and endpoints during server discovery.
        timeout: HTTP timeout in seconds for login HTTP requests.
    """
    if _authentication_exists_on_disk(idp) and not force:
        get_console(stderr=True).print(
            f"[yellow]Authentication for '{idp}' already exists. "
            "Use --force to re-authenticate.[/yellow]"
        )
        raise typer.Exit(1)

    idp_info = get_idp(idp)
    try:
        credential = authenticate_for_cli(idp_info, timeout=timeout)
    except (ValueError, RuntimeError) as exc:
        get_console(stderr=True).print(f"[bold red]{exc}[/bold red]")
        raise typer.Exit(1) from exc

    config = Configuration()  # ty: ignore[missing-argument]
    config.upsert_credential(credential)

    try:
        servers = discover(
            idp,
            config=config,
            dev=dev,
            timeout=timeout,
            save=False,
        )
    except ServerDiscoveryError as exc:
        get_console(stderr=True).print(f"[bold red]{exc}[/bold red]")
        raise typer.Exit(1) from exc

    if not servers:
        get_console(stderr=True).print(
            f"[bold red]No servers discovered for IDP '{idp}'.[/bold red]"
        )
        raise typer.Exit(1)

    selected = servers[0] if len(servers) == 1 else select_server(servers)

    if selected.uri is None:
        get_console(stderr=True).print(
            "[bold red]Selected server has no URI.[/bold red]"
        )
        raise typer.Exit(1)

    selector = str(selected.uri)
    try:
        activate(idp, selector, config=config, dev=dev, timeout=timeout)
    except (ServerFetchError, ServerSelectorError) as exc:
        get_console(stderr=True).print(f"[bold red]{exc}[/bold red]")
        raise typer.Exit(1) from exc

    get_console().print("[green]✓[/green] Login completed successfully")


def register_login_command(app: typer.Typer) -> None:
    """Register the top-level ``login`` command on ``app``."""

    @app.command(
        "login",
        help="Login to CANFAR Science Platform.",
        rich_help_panel="Auth Management",
    )
    def login_command(
        idp: Annotated[
            str | None,
            typer.Argument(help="Canonical Identity Provider key."),
        ] = None,
        force: Annotated[
            bool,
            typer.Option("-f", "--force", help="Force re-authentication."),
        ] = False,
        dev: Annotated[
            bool,
            typer.Option("--dev", help="Include dev servers in discovery."),
        ] = False,
        timeout: Annotated[
            int,
            typer.Option(
                "-t",
                "--timeout",
                help="Timeout for HTTP requests during login.",
                min=1,
            ),
        ] = 10,
    ) -> None:
        """Login to CANFAR Science Platform."""
        maybe_emit_banner(output.OutputMode.HUMAN)
        selected_idp = idp or select_idp(list_idps())
        try:
            get_idp(selected_idp)
        except KeyError as exc:
            get_console(stderr=True).print(f"[bold red]{exc}[/bold red]")
            raise typer.Exit(1) from exc

        _login_flow(selected_idp, force=force, dev=dev, timeout=timeout)
