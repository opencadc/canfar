"""Shared helpers for CLI machine output integration."""

from __future__ import annotations

from contextvars import ContextVar
from typing import TYPE_CHECKING, Annotated, Any

import typer

from canfar.cli.output import (
    OutputConflictError,
    OutputMode,
    _resolve_output_modes,
    write_stderr_error,
    write_stdout,
)

if TYPE_CHECKING:
    from canfar.errors import StructuredError

_collected_output_modes: ContextVar[list[OutputMode] | None] = ContextVar(
    "collected_output_modes",
    default=None,
)


def reset_output_modes() -> None:
    """Clear collected output modes for the current CLI invocation."""
    _collected_output_modes.set(None)


def _register_output_modes(modes: list[OutputMode]) -> None:
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
    local_modes: list[OutputMode] = []
    if json_output:
        local_modes.append(OutputMode.JSON)
    if yaml_output:
        local_modes.append(OutputMode.YAML)
    if local_modes:
        mode = _resolve_output_modes(local_modes)
        ctx.meta["output_mode"] = mode
        _register_output_modes([mode])


def resolve_output_mode(ctx: typer.Context) -> OutputMode:  # noqa: ARG001
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
        return OutputMode.HUMAN
    return _resolve_output_modes(modes)


def resolve_output_mode_or_exit(ctx: typer.Context) -> OutputMode:
    """Resolve output mode, exiting with code 2 on flag conflicts."""
    try:
        return resolve_output_mode(ctx)
    except OutputConflictError as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(exc.exit_code) from exc


def emit_machine_payload(ctx: typer.Context, payload: Any) -> None:
    """Write a validated DTO payload to stdout in machine mode.

    Args:
        ctx: Current Typer invocation context.
        payload: Pydantic DTO or serializable payload.
    """
    mode = resolve_output_mode(ctx)
    if mode is OutputMode.HUMAN:
        return
    write_stdout(payload, mode)


def emit_machine_error(ctx: typer.Context, error: StructuredError) -> None:
    """Write a structured error to stderr and exit in machine mode.

    Args:
        ctx: Current Typer invocation context.
        error: Structured error payload.
    """
    mode = resolve_output_mode(ctx)
    write_stderr_error(error, mode)
    raise typer.Exit(1)


def unsupported_machine_output(ctx: typer.Context) -> None:
    """Fail when machine output is requested for an unsupported command."""
    mode = resolve_output_mode_or_exit(ctx)
    if mode is OutputMode.HUMAN:
        return
    typer.echo("machine output not supported for this command yet", err=True)
    typer.echo("use default human output for now", err=True)
    raise typer.Exit(1)
