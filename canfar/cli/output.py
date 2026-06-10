"""Machine output mode parsing and rendering for the CANFAR CLI."""

from __future__ import annotations

import json
import sys
from enum import Enum
from typing import Any

import yaml
from pydantic_core import to_jsonable_python

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


def _serialize_payload(data: Any) -> Any:
    """Convert supported payload types into JSON-compatible values.

    Args:
        data: Domain model, model list, or plain serializable value.

    Returns:
        JSON-compatible structure ready for rendering.
    """
    if isinstance(data, list):
        return [to_jsonable_python(item) for item in data]
    return to_jsonable_python(data)


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
