"""Authentication management commands for CANFAR CLI."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import TYPE_CHECKING, Annotated

import humanize
import typer
from rich import box
from rich.prompt import Confirm, Prompt
from rich.table import Table

from canfar.authentication import (
    AuthenticationError,
)
from canfar.authentication import (
    list as auth_list,
)
from canfar.authentication import (
    purge as auth_purge,
)
from canfar.authentication import (
    remove as auth_remove,
)
from canfar.authentication import (
    show as auth_show,
)
from canfar.cli import output
from canfar.cli.dto_maps import authentication_list_dto, authentication_show_dto
from canfar.cli.machine import (
    output_mode_callback,
    resolve_output_mode_or_exit,
    unsupported_machine_output,
)
from canfar.hooks.typer.aliases import AliasGroup
from canfar.idp import get_idp
from canfar.models.config import Configuration
from canfar.server import (
    ServerDiscoveryError,
    ServerFetchError,
    ServerSelectionRequiredError,
    ServerSelectorError,
)
from canfar.server import (
    activate as activate_server,
)
from canfar.utils.console import console

if TYPE_CHECKING:
    from canfar.models.http import Server

auth = typer.Typer(
    name="auth",
    help="Manage authentication providers.",
    no_args_is_help=False,
    invoke_without_command=True,
    rich_markup_mode="rich",
    cls=AliasGroup,
)


def _format_expiry(expiry: float | None) -> str:
    """Format credential expiry for human-readable CLI output.

    Args:
        expiry: Credential expiry as Unix timestamp when applicable.

    Returns:
        Humanized relative time, or ``N/A`` when expiry is unknown.
    """
    if expiry is None:
        return "N/A"
    when = datetime.fromtimestamp(expiry, tz=timezone.utc)
    return humanize.naturaltime(when)


def _print_auth_switched(idp: str) -> None:
    """Print confirmation after switching active authentication."""
    console.print(
        f"[green]✓[/green] Switched active authentication to [bold]{idp}[/bold]",
    )


def _prompt_server_selector(servers: list[Server]) -> str:
    """Prompt until the user selects a server URI or list index."""
    if len(servers) == 1 and servers[0].uri is not None:
        selector = str(servers[0].uri)
        console.print(
            f"[green]✓[/green] Auto-selected server {servers[0].name or selector}",
        )
        return selector

    console.print("[bold blue]Select compatible server[/bold blue]")
    for index, server in enumerate(servers, start=1):
        label = server.name or str(server.uri)
        console.print(f"  {index}. {label} ({server.uri})")
    while True:
        choice = Prompt.ask("Server URI or number")
        uri_matches = [item for item in servers if str(item.uri) == choice]
        if uri_matches:
            return choice
        try:
            selected = servers[int(choice) - 1]
        except (ValueError, IndexError):
            console.print("[red]Enter a valid server URI or number.[/red]")
            continue
        if selected.uri is None:
            console.print("[red]Enter a valid server URI or number.[/red]")
            continue
        return str(selected.uri)


def _render_auth_show_table() -> None:
    """Render the active Authentication summary for human output."""
    try:
        summary = auth_show()
    except AuthenticationError as exc:
        console.print(f"[bold red]{exc.error.message}[/bold red]")
        if exc.error.hint:
            console.print(exc.error.hint)
        raise typer.Exit(1) from exc

    table = Table(title="Active Authentication", show_lines=True, box=box.SIMPLE)
    table.add_column("Field", style="cyan")
    table.add_column("Value", style="magenta")
    table.add_row("IDP", summary.idp)
    table.add_row("Name", summary.name)
    table.add_row("Mode", summary.mode)
    table.add_row("Expiry", _format_expiry(summary.expiry))
    table.add_row("Server", summary.server or "N/A")
    console.print(table)


def _render_auth_list_table() -> None:
    """Render saved Authentication records for human output."""
    summaries = auth_list()
    table = Table(
        title="Saved Authentication Records",
        show_lines=True,
        box=box.SIMPLE,
    )
    table.add_column("Active", justify="center", style="cyan")
    table.add_column("IDP", style="magenta")
    table.add_column("Mode", justify="center", style="green")
    table.add_column("Server", style="blue")

    for summary in summaries:
        table.add_row(
            "✅" if summary.active else "",
            summary.idp,
            summary.mode,
            summary.server or "N/A",
        )
    console.print(table)


@auth.callback(invoke_without_command=True)
def auth_default(
    ctx: typer.Context,
    json_output: Annotated[
        bool,
        typer.Option("--json", help="Emit machine-readable JSON on stdout."),
    ] = False,
    yaml_output: Annotated[
        bool,
        typer.Option("--yaml", help="Emit machine-readable YAML on stdout."),
    ] = False,
) -> None:
    """Active authentication state."""
    if ctx.invoked_subcommand in {"show", "ls"} and (json_output or yaml_output):
        typer.echo(
            "Place --json or --yaml after the command that emits machine output.",
            err=True,
        )
        raise typer.Exit(output.OUTPUT_CONFLICT_EXIT_CODE)
    output_mode_callback(ctx, json_output, yaml_output)
    if ctx.invoked_subcommand is not None:
        return

    mode = resolve_output_mode_or_exit(ctx)
    if mode is not output.OutputMode.HUMAN:
        try:
            summary = auth_show()
        except AuthenticationError as exc:
            output.to_stderr(exc.error, mode)
            raise typer.Exit(1) from exc
        output.to_stdout(authentication_show_dto(summary), mode)
        return

    _render_auth_show_table()


@auth.command("show")
def auth_show_command(
    ctx: typer.Context,
    json_output: Annotated[
        bool,
        typer.Option("--json", help="Emit machine-readable JSON on stdout."),
    ] = False,
    yaml_output: Annotated[
        bool,
        typer.Option("--yaml", help="Emit machine-readable YAML on stdout."),
    ] = False,
) -> None:
    """Active authentication state."""
    output_mode_callback(ctx, json_output, yaml_output)
    mode = resolve_output_mode_or_exit(ctx)
    if mode is not output.OutputMode.HUMAN:
        try:
            summary = auth_show()
        except AuthenticationError as exc:
            output.to_stderr(exc.error, mode)
            raise typer.Exit(1) from exc
        output.to_stdout(authentication_show_dto(summary), mode)
        return
    _render_auth_show_table()


@auth.command("ls")
def auth_list_command(
    ctx: typer.Context,
    json_output: Annotated[
        bool,
        typer.Option("--json", help="Emit machine-readable JSON on stdout."),
    ] = False,
    yaml_output: Annotated[
        bool,
        typer.Option("--yaml", help="Emit machine-readable YAML on stdout."),
    ] = False,
) -> None:
    """Available auth providers."""
    output_mode_callback(ctx, json_output, yaml_output)
    mode = resolve_output_mode_or_exit(ctx)
    summaries = auth_list()
    if mode is not output.OutputMode.HUMAN:
        output.to_stdout(authentication_list_dto(summaries), mode)
        return
    _render_auth_list_table()


@auth.command("login")
def auth_login_command(
    ctx: typer.Context,
    idp: Annotated[
        str | None,
        typer.Argument(help="Canonical Identity Provider key."),
    ] = None,
    force: Annotated[
        bool,
        typer.Option("-f", "--force", help="Force re-authentication."),
    ] = False,
    debug: Annotated[
        bool,
        typer.Option("--debug", help="Enable debug logging."),
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
    ] = 2,
) -> None:
    """Alias for canfar login."""
    from canfar import get_logger, set_log_level  # noqa: PLC0415
    from canfar.cli.login import _login_flow  # noqa: PLC0415
    from canfar.cli.prompts import select_idp  # noqa: PLC0415
    from canfar.idp import list_idps  # noqa: PLC0415

    console.print(
        "\n[red]Deprecation Notice:[/red]"
        "\n[yellow]canfar auth login[/yellow] will be removed soon."
        " Use [green][bold]canfar login[/bold][/green] instead.\n"
    )
    unsupported_machine_output(ctx)
    if debug:
        set_log_level("DEBUG")
        get_logger(__name__).debug("Debug logging enabled")
    selected_idp = idp or select_idp(list_idps())
    _login_flow(selected_idp, force=force, dev=dev, timeout=timeout)


@auth.command("use")
def auth_use_command(
    ctx: typer.Context,
    idp: Annotated[str, typer.Argument(help="Canonical Identity Provider key.")],
) -> None:
    """Switch auth provider."""
    unsupported_machine_output(ctx)
    config = Configuration()

    try:
        get_idp(idp)
        config.get_credential(idp)
    except KeyError as exc:
        console.print(f"[bold red]{exc}[/bold red]")
        raise typer.Exit(1) from exc

    try:
        activation = activate_server(idp, config=config)
    except ServerSelectionRequiredError as exc:
        selector = _prompt_server_selector(exc.servers)
        try:
            activation = activate_server(idp, selector, config=config)
        except (ServerDiscoveryError, ServerFetchError, ServerSelectorError) as err:
            console.print(f"[bold red]{err}[/bold red]")
            raise typer.Exit(1) from err
    except (ServerDiscoveryError, ServerFetchError, ServerSelectorError) as exc:
        console.print(f"[bold red]{exc}[/bold red]")
        raise typer.Exit(1) from exc

    if activation.reason in {"remembered", "single"}:
        selector = str(activation.server.uri) if activation.server.uri else ""
        console.print(
            f"[green]✓[/green] Auto-selected server "
            f"{activation.server.name or selector}",
        )
    _print_auth_switched(idp)


@auth.command("rm")
def auth_remove_command(
    ctx: typer.Context,
    idp: Annotated[str, typer.Argument(help="Canonical Identity Provider key.")],
    force: Annotated[
        bool,
        typer.Option("-f", "--force", help="Remove active authentication."),
    ] = False,
) -> None:
    """Remove auth and associated servers."""
    unsupported_machine_output(ctx)
    config = Configuration()
    if config.active.authentication == idp and not force:
        should_remove = Confirm.ask(
            f"Remove active authentication '{idp}'?",
            default=False,
        )
        if not should_remove:
            console.print("[yellow]Removal cancelled[/yellow]")
            raise typer.Exit(0)
        force = True

    try:
        auth_remove(idp, force=force)
    except AuthenticationError as exc:
        console.print(f"[bold red]{exc.error.message}[/bold red]")
        if exc.error.hint:
            console.print(exc.error.hint)
        raise typer.Exit(1) from exc
    except KeyError as exc:
        console.print(f"[bold red]{exc}[/bold red]")
        raise typer.Exit(1) from exc

    console.print(f"[green]✓[/green] Removed authentication for [bold]{idp}[/bold]")


@auth.command("purge")
def auth_purge_command(
    ctx: typer.Context,
    force: Annotated[
        bool,
        typer.Option("--force", help="Required to reset authentication state."),
    ] = False,
) -> None:
    """Remove all auths and servers."""
    unsupported_machine_output(ctx)
    if not force:
        console.print("[bold red]Authentication purge requires --force.[/bold red]")
        raise typer.Exit(1)

    try:
        auth_purge(force=True)
    except AuthenticationError as exc:
        console.print(f"[bold red]{exc.error.message}[/bold red]")
        raise typer.Exit(1) from exc

    console.print("[green]✓[/green] Authentication and server state reset")
