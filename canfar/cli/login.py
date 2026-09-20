"""Top-level login command for CANFAR CLI."""

from __future__ import annotations

from typing import Annotated

import httpx
import typer

from canfar.cli.login_auth import authenticate_for_cli
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
from canfar.utils.console import emit_cli_active_server_banner, get_console


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
        force: Obtain a new X.509 certificate even when the current one is valid.
        dev: Include development registries and endpoints during server discovery.
        timeout: HTTP timeout in seconds for login HTTP requests.
    """
    idp_info = get_idp(idp)
    try:
        credential = authenticate_for_cli(idp_info, timeout=timeout, force=force)
    except (
        PermissionError,
        TimeoutError,
        ValueError,
        RuntimeError,
        httpx.HTTPError,
    ) as exc:
        get_console(stderr=True).print(f"[bold red]{exc}[/bold red]")
        raise typer.Exit(1) from exc

    config = Configuration()  # ty: ignore[missing-argument]
    config.editor.set(f"authentication.{credential.idp}", credential)

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
            typer.Option(
                "-f", "--force", help="Obtain a new CADC certificate even if valid."
            ),
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
        emit_cli_active_server_banner()
        selected_idp = idp or select_idp(list_idps())
        try:
            get_idp(selected_idp)
        except KeyError as exc:
            get_console(stderr=True).print(f"[bold red]{exc}[/bold red]")
            raise typer.Exit(1) from exc

        _login_flow(selected_idp, force=force, dev=dev, timeout=timeout)
