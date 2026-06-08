"""Machine output mode parsing and rendering for the CANFAR CLI."""

from __future__ import annotations

import json
import sys
from enum import Enum
from typing import TYPE_CHECKING, Any, cast

import yaml
from pydantic import BaseModel

from canfar.models.dto.base import dto_dump

if TYPE_CHECKING:
    import typer

from canfar.errors import (
    StructuredError,
    structured_error_to_json,
    structured_error_to_yaml,
)

OUTPUT_CONFLICT_EXIT_CODE = 2
"""Exit code for conflicting machine output flags."""


class OutputMode(str, Enum):
    """Supported CLI output modes."""

    HUMAN = "human"
    JSON = "json"
    YAML = "yaml"


_OUTPUT_FLAG_TOKENS: dict[str, OutputMode] = {
    "--json": OutputMode.JSON,
    "--yaml": OutputMode.YAML,
}


class OutputConflictError(Exception):
    """Raised when conflicting machine output flags are supplied."""

    code = "output.conflict"
    exit_code = OUTPUT_CONFLICT_EXIT_CODE

    def __init__(self) -> None:
        super().__init__(
            "Conflicting machine output flags: use only one of --json or --yaml."
        )


def _collect_output_modes(tokens: list[str]) -> list[OutputMode]:
    """Collect machine output modes from a token sequence.

    Args:
        tokens: CLI tokens containing zero or more ``--json`` or ``--yaml`` flags.

    Returns:
        Output modes in the order they appear in ``tokens``.
    """
    modes: list[OutputMode] = []
    for token in tokens:
        mode = _OUTPUT_FLAG_TOKENS.get(token)
        if mode is not None:
            modes.append(mode)
    return modes


def has_output_flag(argv: list[str]) -> bool:
    """Return whether raw CLI tokens contain a machine-output flag."""
    return any(token in _OUTPUT_FLAG_TOKENS for token in argv)


def _modes_from_context(ctx: typer.Context) -> list[OutputMode]:
    """Collect output modes stored on a Typer context chain."""
    modes: list[OutputMode] = []
    current: typer.Context | None = ctx
    while current is not None:
        mode = current.meta.get("output_mode")
        if isinstance(mode, OutputMode):
            modes.append(mode)
        current = cast("typer.Context | None", current.parent)
    return modes


def resolve(modes: list[OutputMode]) -> OutputMode:
    """Resolve collected output modes to a single effective mode.

    Args:
        modes: Output modes collected from supported flag placements.

    Returns:
        The effective output mode.

    Raises:
        OutputConflictError: If more than one distinct machine mode was found.
    """
    machine_modes = [mode for mode in modes if mode is not OutputMode.HUMAN]
    if not machine_modes:
        return OutputMode.HUMAN

    unique_modes = list(dict.fromkeys(machine_modes))
    if len(unique_modes) > 1:
        raise OutputConflictError
    return unique_modes[0]


def parse_suffix(argv: list[str]) -> OutputMode | None:
    """Parse machine output flags from the leaf argv suffix.

    Leaf flags appear after the command path, for example
    ``canfar auth ls --json``.

    Args:
        argv: Command arguments excluding the program name.

    Returns:
        The selected machine output mode, or ``None`` when no leaf flags are
        present.
    """
    suffix: list[str] = []
    for token in reversed(argv):
        if token not in _OUTPUT_FLAG_TOKENS:
            break
        suffix.insert(0, token)
    modes = _collect_output_modes(suffix)
    if not modes:
        return None
    return resolve(modes)


def parse(
    argv: list[str] | None = None,
    *,
    ctx: typer.Context | None = None,
) -> OutputMode:
    """Resolve the effective CLI output mode from argv and Typer context.

    Supported flag placement is the leaf suffix only. Root and intermediate
    group placement are ignored here; Typer rejects unsupported root flags.
    Duplicate same-mode flags are idempotent; different modes raise
    :class:`OutputConflictError`.

    Args:
        argv: Command arguments excluding the program name.
        ctx: Optional Typer context whose parent chain may carry output modes.

    Returns:
        The effective output mode.

    Raises:
        OutputConflictError: If conflicting machine output flags were supplied.
    """
    modes: list[OutputMode] = []
    if ctx is not None:
        modes.extend(_modes_from_context(ctx))
    if argv is not None:
        suffix_mode = parse_suffix(argv)
        if suffix_mode is not None:
            modes.append(suffix_mode)
    return resolve(modes)


def _serialize_payload(data: Any) -> Any:
    """Convert supported payload types into JSON-compatible values."""
    if isinstance(data, BaseModel):
        return dto_dump(data)
    return data


def render_stdout(data: Any, mode: OutputMode) -> str:
    """Render command data for stdout in the selected output mode.

    Args:
        data: Command payload to render.
        mode: Effective CLI output mode.

    Returns:
        Rendered stdout payload. Human mode returns an empty string because
        human rendering uses the existing console helpers elsewhere.
    """
    if mode is OutputMode.HUMAN:
        return ""

    payload = _serialize_payload(data)
    if mode is OutputMode.JSON:
        return json.dumps(payload, indent=2) + "\n"
    return yaml.safe_dump(payload, sort_keys=False)


def render_stderr_error(error: StructuredError, mode: OutputMode) -> str:
    """Render a structured error payload for stderr.

    Args:
        error: Structured error to render.
        mode: Effective CLI output mode.

    Returns:
        Rendered stderr payload. Human mode returns plain-text message content.
    """
    if mode is OutputMode.HUMAN:
        lines = [error.message]
        if error.hint:
            lines.append(error.hint)
        return "\n".join(lines) + "\n"

    if mode is OutputMode.JSON:
        return structured_error_to_json(error) + "\n"
    return structured_error_to_yaml(error)


def to_stdout(data: Any, mode: OutputMode) -> None:
    """Write rendered command data to stdout."""
    sys.stdout.write(render_stdout(data, mode))


def to_stderr(error: StructuredError, mode: OutputMode) -> None:
    """Write rendered structured error data to stderr."""
    sys.stderr.write(render_stderr_error(error, mode))
