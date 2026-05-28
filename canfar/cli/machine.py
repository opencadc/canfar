"""Shared helpers for CLI machine output integration."""

from __future__ import annotations

from contextvars import ContextVar
from typing import TYPE_CHECKING, Annotated, Any

import typer

from canfar.cli import output
from canfar.utils.console import emit_active_server_banner, reset_banner_state

if TYPE_CHECKING:
    from canfar.errors import StructuredError

_collected_output_modes: ContextVar[list[output.OutputMode] | None] = ContextVar(
    "collected_output_modes",
    default=None,
)
_invoke_argv: ContextVar[list[str] | None] = ContextVar("cli_invoke_argv", default=None)


def reset() -> None:
    """Reset CLI machine-output invocation state."""
    _collected_output_modes.set(None)
    reset_banner_state()


def set_invoke_argv(argv: list[str]) -> None:
    """Store raw CLI tokens for the current invocation."""
    _invoke_argv.set(list(argv))


def get_invoke_argv() -> list[str] | None:
    """Return raw CLI tokens for the current invocation."""
    return _invoke_argv.get()


def maybe_emit_cli_banner(ctx: typer.Context) -> None:
    """Print the active-server banner when machine output was not requested."""
    argv = get_invoke_argv()
    if argv is None:
        return
    try:
        mode = output.parse(argv, ctx=ctx)
    except output.OutputConflictError:
        return
    if mode is output.OutputMode.HUMAN:
        emit_active_server_banner()


def _register_output_modes(modes: list[output.OutputMode]) -> None:
    if not modes:
        return
    collected = list(_collected_output_modes.get() or [])
    collected.extend(modes)
    _collected_output_modes.set(collected)


def output_mode_callback(
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
    """Store leaf-level machine output flags on the Typer context.

    Args:
        ctx: Current Typer invocation context.
        json_output: Whether ``--json`` was supplied at this level.
        yaml_output: Whether ``--yaml`` was supplied at this level.
    """
    local_modes: list[output.OutputMode] = []
    if json_output:
        local_modes.append(output.OutputMode.JSON)
    if yaml_output:
        local_modes.append(output.OutputMode.YAML)
    if local_modes:
        mode = output.resolve(local_modes)
        ctx.meta["output_mode"] = mode
        _register_output_modes([mode])


def resolve_output_mode(ctx: typer.Context) -> output.OutputMode:  # noqa: ARG001
    """Resolve the effective output mode for a command invocation.

    Args:
        ctx: Current Typer invocation context.

    Returns:
        Effective output mode for the invocation.

    Raises:
        OutputConflictError: If conflicting machine modes were selected.
    """
    modes = list(_collected_output_modes.get() or [])
    if not modes:
        return output.OutputMode.HUMAN
    return output.resolve(modes)


def resolve_output_mode_or_exit(ctx: typer.Context) -> output.OutputMode:
    """Resolve output mode, exiting with code 2 on flag conflicts."""
    try:
        return resolve_output_mode(ctx)
    except output.OutputConflictError as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(exc.exit_code) from exc


def emit_machine_payload(ctx: typer.Context, payload: Any) -> None:
    """Write a validated DTO payload to stdout in machine mode.

    Args:
        ctx: Current Typer invocation context.
        payload: Pydantic DTO or serializable payload.
    """
    mode = resolve_output_mode(ctx)
    if mode is output.OutputMode.HUMAN:
        return
    output.to_stdout(payload, mode)


def emit_machine_error(ctx: typer.Context, error: StructuredError) -> None:
    """Write a structured error to stderr and exit in machine mode.

    Args:
        ctx: Current Typer invocation context.
        error: Structured error payload.
    """
    mode = resolve_output_mode(ctx)
    output.to_stderr(error, mode)
    raise typer.Exit(1)


def unsupported_machine_output(ctx: typer.Context) -> None:
    """Fail when machine output is requested for an unsupported command."""
    mode = resolve_output_mode_or_exit(ctx)
    if mode is output.OutputMode.HUMAN:
        return
    typer.echo("machine output not supported for this command yet", err=True)
    typer.echo("use default human output for now", err=True)
    raise typer.Exit(1)
