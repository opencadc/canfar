"""Request and failure helpers shared by the Session clients."""

from __future__ import annotations

import logging
import re
from typing import TYPE_CHECKING, Any, Literal, TypeVar

from canfar.exceptions.context import AuthContextError, AuthExpiredError
from canfar.exceptions.session import SessionRequestError
from canfar.hooks.httpx.auth import AuthenticationError

if TYPE_CHECKING:
    from collections.abc import Mapping

    from httpx2 import HTTPError, Response

# Failure records stay on the logger callers configure for the Session clients.
log = logging.getLogger("canfar.sessions")
_Result = TypeVar("_Result")


def _raise_authentication_failure(result: object) -> None:
    """Raise a collected Authentication failure, which belongs to the client.

    ``asyncio.gather(..., return_exceptions=True)`` collects one copy per task.
    Reporting it as a per-Session transport failure would hide that no request
    was sent, so the asynchronous client raises it as the synchronous one does.
    """
    if isinstance(result, AuthContextError | AuthExpiredError | AuthenticationError):
        raise result


def _task_result(
    operation: str,
    context: object,
    result: _Result | Exception,
) -> _Result | None:
    """Keep one failure and logging policy for collected transport results."""
    _raise_authentication_failure(result)
    if isinstance(result, Exception):
        # HTTPX2 response hooks already log the status and safe request context.
        log.error("%s: %s (%s)", operation, context, type(result).__name__)
        return None
    return result


def _raise_failures(
    operation: str,
    errors: Literal["ignore", "raise"],
    results: Any,
    failures: dict[str | int, HTTPError],
) -> None:
    """Raise the collected request failures when the error policy is ``raise``."""
    if errors == "raise" and failures:
        raise SessionRequestError(operation, results, failures)


def _destroy_failure(session_id: str, exc: BaseException | None = None) -> bool:
    """Log a failed Session deletion and preserve the false result policy."""
    msg = f"Failed to destroy session {session_id}"
    if exc is not None:
        msg += f": {exc}"
    # Both callers invoke this from their HTTPError handler; keep traceback logging.
    log.exception(msg)  # noqa: LOG004
    return False


def _renew(session_id: str, exc: BaseException | None = None) -> bool:
    """Log a failed Session renewal and preserve the false result policy."""
    msg = f"Failed to renew session {session_id}"
    if exc is not None:
        msg += f": {exc}"
    # Both callers invoke this from their HTTPError handler; keep traceback logging.
    log.exception(msg)  # noqa: LOG004
    return False


def _ids(value: str | list[str]) -> list[str]:
    """Normalize one or many Session identifiers without changing their order."""
    return [value] if isinstance(value, str) else value


def _session_url(session_id: str) -> str:
    """Build the endpoint path for one Session identifier."""
    return f"session/{session_id}"


def _response_session_id(response: Response) -> str:
    """Interpret a create response as a clean Session identifier."""
    return response.text.rstrip("\r\n")


def _session_name_pattern(selector: str) -> re.Pattern[str]:
    """Compile a regular expression or an anchored literal Session selector."""
    meta = frozenset(".^$*+?{}[]()|")
    if any(char in meta for char in selector):
        log.info("destroy_with using regex pattern: %s", selector)
        pattern = selector
    else:
        log.info("destroy_with using literal prefix: %s", selector)
        pattern = rf"^{re.escape(selector)}"
    try:
        return re.compile(pattern)
    except re.error as exc:
        msg = f"Invalid regex pattern '{selector}': {exc}"
        log.exception(msg)
        raise ValueError(msg) from exc


def _matching_session_ids(sessions: list[Any], regex: re.Pattern[str]) -> list[str]:
    """Return session IDs whose names match the compiled selector."""
    return [session["id"] for session in sessions if regex.search(session["name"])]


def connection_url(session: Mapping[str, Any]) -> str | None:
    """Return the URL only when a Session is ready for a connection."""
    value = session.get("connectURL")
    if session.get("status") != "Running" or not isinstance(value, str):
        return None
    return value or None
