"""Machine output mode parsing and rendering for the CANFAR CLI."""

from __future__ import annotations

import json
import sys
from enum import Enum
from typing import TYPE_CHECKING, Any, NoReturn

import yaml
from pydantic_core import to_jsonable_python
from rich.markup import escape

from canfar.config.migration import ConfigResetRequiredError
from canfar.errors import ErrorCode, StructuredError
from canfar.exceptions.context import (
    AuthContextError,
    AuthExpiredError,
    AuthRequiredError,
)
from canfar.utils.console import get_console

if TYPE_CHECKING:
    from httpx2 import HTTPError

    from canfar.hooks.httpx.auth import AuthenticationError

    BoundaryError = (
        ConfigResetRequiredError
        | AuthExpiredError
        | AuthContextError
        | AuthenticationError
        | HTTPError
    )
    """Session boundary exceptions shared by ``create`` and ``ps``."""

OUTPUT_CONFLICT_EXIT_CODE = 2
"""Exit code for conflicting machine output flags."""


class OutputMode(str, Enum):
    """Supported CLI output modes."""

    HUMAN = "human"
    JSON = "json"
    YAML = "yaml"


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

    payload = to_jsonable_python(data)
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

    payload = error.model_dump(mode="json")
    if mode is OutputMode.JSON:
        return json.dumps(payload, ensure_ascii=False) + "\n"
    return yaml.safe_dump(payload, sort_keys=False, allow_unicode=True)


def boundary_failure(
    err: BoundaryError,
    *,
    transport_message: str = "Request to the Science Platform failed.",
) -> StructuredError:
    """Map a Session boundary exception to its structured error payload.

    Args:
        err: One of the expected create/ps boundary exceptions.
        transport_message: Human-facing summary used only for ``httpx2.HTTPError``.

    Returns:
        StructuredError describing the failure for both output streams.
    """
    from canfar.hooks.httpx.auth import AuthenticationError  # noqa: PLC0415

    if isinstance(err, ConfigResetRequiredError):
        return StructuredError(
            code=err.code,
            message=err.message,
            hint="Reset the configuration and log in again.",
        )
    if isinstance(err, AuthRequiredError):
        return StructuredError(
            code=ErrorCode.AUTHENTICATION_REQUIRED,
            message=str(err),
            hint=f"Run `canfar login {err.idp}` and retry.",
        )
    if isinstance(err, AuthExpiredError):
        return StructuredError(
            code=ErrorCode.AUTHENTICATION_EXPIRED,
            message=str(err),
            hint=f"Run `canfar login {err.idp}` to authenticate again, then retry.",
        )
    if isinstance(err, AuthContextError):
        return StructuredError(
            code=ErrorCode.AUTHENTICATION_CREDENTIAL_INVALID,
            message=str(err),
            hint="Check the active Authentication Record and retry.",
        )
    if isinstance(err, AuthenticationError):
        return StructuredError(
            code=ErrorCode.TRANSPORT_FAILURE,
            message=str(err),
            hint="Retry the command. If it still fails, check the Identity Provider.",
        )
    return StructuredError(
        code=ErrorCode.TRANSPORT_FAILURE,
        message=transport_message,
        hint="Check authentication and Science Platform connectivity, then retry.",
    )


def to_stdout(data: Any, mode: OutputMode) -> None:
    """Write rendered command data to stdout."""
    sys.stdout.write(render_stdout(data, mode))


def to_stderr(error: StructuredError, mode: OutputMode) -> None:
    """Write rendered structured error data to stderr."""
    sys.stderr.write(render_stderr_error(error, mode))


def fail(
    error: StructuredError,
    mode: OutputMode,
    human: str | None = None,
    *,
    code: int = 1,
) -> NoReturn:
    """Report a failed command on stderr in the selected mode, then exit.

    Args:
        error: Structured error written in JSON and YAML modes.
        mode: Effective CLI output mode.
        human: Rich markup printed in human mode instead of the error message.
        code: Process exit status.

    Raises:
        SystemExit: Always, with ``code``.
    """
    if mode is OutputMode.HUMAN:
        console = get_console(stderr=True)
        console.print(human or f"[bold red]{escape(error.message)}[/bold red]")
        if error.hint:
            console.print(f"[dim]{escape(error.hint)}[/dim]")
    else:
        to_stderr(error, mode)
    raise SystemExit(code)
