"""Top-level login command for CANFAR CLI."""

from __future__ import annotations

from typing import TYPE_CHECKING, Annotated

import typer

from canfar import CONFIG_PATH
from canfar.cli._machine import unsupported_machine_output
from canfar.cli.login_auth import authenticate_for_cli
from canfar.cli.prompts import select_idp, select_server
from canfar.idp import get_idp, list_idps
from canfar.models.config import Configuration
from canfar.server import (
    ServerDiscoveryError,
    ServerFetchError,
    _discover_and_merge,
    _resolve_selector,
    _validate_server,
)
from canfar.utils.console import console

if TYPE_CHECKING:
    from canfar.models.auth import AuthenticationCredential


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
    config = Configuration()
    return any(credential.idp == idp for credential in config.authentication)


def _upsert_credential(
    config: Configuration,
    credential: AuthenticationCredential,
) -> None:
    """Insert or replace an authentication credential on ``config``.

    Args:
        config: Configuration being updated in memory.
        credential: Authentication credential to persist on save.
    """
    updated: list[AuthenticationCredential] = []
    replaced = False
    for existing in config.authentication:
        if existing.idp == credential.idp:
            updated.append(credential)
            replaced = True
        else:
            updated.append(existing)
    if not replaced:
        updated.append(credential)
    config.authentication = updated


def _login_flow(idp: str, *, force: bool = False) -> None:
    """Run the guided login flow for ``idp``.

    Authenticates interactively, discovers servers, selects a server, and
    atomically saves the active Authentication and Server pair.

    Args:
        idp: Canonical Identity Provider key.
        force: When ``True``, overwrite an existing saved Authentication record.
    """
    if _authentication_exists_on_disk(idp) and not force:
        console.print(
            f"[yellow]Authentication for '{idp}' already exists. "
            "Use --force to re-authenticate.[/yellow]"
        )
        raise typer.Exit(1)

    idp_info = get_idp(idp)
    try:
        credential = authenticate_for_cli(idp_info)
    except (ValueError, RuntimeError) as exc:
        console.print(f"[bold red]{exc}[/bold red]")
        raise typer.Exit(1) from exc

    config = Configuration()
    _upsert_credential(config, credential)

    try:
        _discover_and_merge(config, idp)
    except ServerDiscoveryError as exc:
        console.print(f"[bold red]{exc}[/bold red]")
        raise typer.Exit(1) from exc

    servers = [server for server in config.server if server.idp == idp]
    if not servers:
        console.print(f"[bold red]No servers discovered for IDP '{idp}'.[/bold red]")
        raise typer.Exit(1)

    selected = servers[0] if len(servers) == 1 else select_server(servers)

    if selected.uri is None:
        console.print("[bold red]Selected server has no URI.[/bold red]")
        raise typer.Exit(1)

    selector = str(selected.uri)
    resolved = _resolve_selector(config, selector, idp)
    if resolved is None:
        console.print(
            f"[bold red]Server '{selector}' not found for IDP '{idp}'.[/bold red]"
        )
        raise typer.Exit(1)

    try:
        validated = _validate_server(resolved)
    except ServerFetchError as exc:
        console.print(f"[bold red]{exc}[/bold red]")
        raise typer.Exit(1) from exc

    config._upsert_server(validated)  # noqa: SLF001
    config.active = config.active.model_copy(
        update={"authentication": idp, "server": validated.uri},
    )
    config.save()
    console.print("[green]✓[/green] Login completed successfully")


def register_login_command(app: typer.Typer) -> None:
    """Register the top-level ``login`` command on ``app``."""

    @app.command(
        "login",
        help="Login to CANFAR Science Platform",
    )
    def login_command(
        ctx: typer.Context,
        idp: Annotated[
            str | None,
            typer.Argument(help="Canonical Identity Provider key."),
        ] = None,
        force: Annotated[
            bool,
            typer.Option("-f", "--force", help="Force re-authentication."),
        ] = False,
    ) -> None:
        """Login to CANFAR Science Platform."""
        unsupported_machine_output(ctx)

        selected_idp = idp or select_idp(list_idps())
        try:
            get_idp(selected_idp)
        except KeyError as exc:
            console.print(f"[bold red]{exc}[/bold red]")
            raise typer.Exit(1) from exc

        _login_flow(selected_idp, force=force)
