"""Top-level login command for CANFAR CLI."""

from __future__ import annotations

import logging
from contextlib import contextmanager
from typing import TYPE_CHECKING, Annotated

import typer
from httpx2 import HTTPError
from rich.console import Console
from rich.live import Live

from canfar.cli.discovery import REFRESH_PER_SECOND, DiscoveryGrid
from canfar.cli.login_auth import authenticate_for_cli
from canfar.cli.machine import maximum
from canfar.cli.prompts import select_idp, select_server
from canfar.client import HTTPClient
from canfar.errors import ErrorCode
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
from canfar.utils.logging import get_logger, logs_through

if TYPE_CHECKING:
    from collections.abc import Iterator

    from canfar.models.http import Server

_MAX_TIMEOUT = maximum(HTTPClient, "timeout")
"""Largest HTTP timeout in seconds that ``HTTPClient`` accepts."""


def _retry_command(idp: str, *, dev: bool, timeout: int) -> str | None:
    """Return the login command with a doubled timeout, if it can still grow."""
    longer = min(timeout * 2, _MAX_TIMEOUT)
    if longer <= timeout:
        return None
    return f"canfar login {idp}{' --dev' if dev else ''} --timeout {longer}"


@contextmanager
def _live_output(console: Console) -> Iterator[None]:
    """Fit ``console`` to the terminal and send log records through it.

    A live view redraws by moving the cursor up its own lines, so it must not
    be wider than the terminal.
    """
    width = console.width
    if console.is_terminal:
        console.width = min(width, Console(stderr=True).width)
    try:
        with logs_through(console):
            yield
    finally:
        console.width = width


def _discover_live(
    idp: str,
    *,
    config: Configuration,
    dev: bool,
    timeout: int,
) -> list[Server]:
    """Discover Servers while a live grid on stderr shows each one's state.

    Server Names label the squares when logging is at INFO or more verbose.
    """
    grid = DiscoveryGrid(
        idp,
        timeout=timeout,
        names=get_logger().isEnabledFor(logging.INFO),
        retry=_retry_command(idp, dev=dev, timeout=timeout),
    )
    console = get_console(stderr=True)
    with _live_output(console):
        try:
            # The transient view redraws on terminals only; the result prints once.
            with Live(
                grid,
                console=console,
                refresh_per_second=REFRESH_PER_SECOND,
                transient=True,
            ):
                return discover(
                    idp,
                    config=config,
                    dev=dev,
                    timeout=timeout,
                    save=False,
                    on_probe=grid.update,
                )
        finally:
            grid.finish()
            console.print(grid)


def _login_flow(
    idp: str,
    *,
    force: bool = False,
    dev: bool = False,
    timeout: int = 10,
) -> None:
    """Run the guided login flow for ``idp``.

    Authenticates interactively, discovers servers and shows which ones
    connected, selects a server, and atomically saves the active
    Authentication and Server pair.

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
        HTTPError,
    ) as exc:
        get_console(stderr=True).print(f"[bold red]{exc}[/bold red]")
        raise typer.Exit(1) from exc

    config = Configuration()  # ty: ignore[missing-argument]
    config.editor.set(f"authentication.{credential.idp}", credential)

    try:
        servers = _discover_live(idp, config=config, dev=dev, timeout=timeout)
    except ServerDiscoveryError as exc:
        console = get_console(stderr=True)
        console.print(f"[bold red]{exc}[/bold red]")
        retry = _retry_command(idp, dev=dev, timeout=timeout)
        if exc.code is ErrorCode.SERVER_DISCOVERY_FAILED and retry is not None:
            console.print(
                "Check your network connection, or if the registry is slow, run "
                f"[bold]{retry}[/bold]"
            )
        raise typer.Exit(1) from exc

    # Discovery raises rather than return no Servers; the prompt returns one
    # with a URI.
    selector = str(select_server(servers).uri)
    try:
        activate(idp, selector, config=config, dev=dev, timeout=timeout)
    except (ServerFetchError, ServerSelectorError) as exc:
        get_console(stderr=True).print(f"[bold red]{exc}[/bold red]")
        raise typer.Exit(1) from exc

    get_console().print("[green]✓[/green] Login completed successfully")


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
            max=_MAX_TIMEOUT,
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
