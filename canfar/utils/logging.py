"""CANFAR logging: stdlib logging with Rich stderr and optional JSONL file sink."""

from __future__ import annotations

import json
import logging
import logging.handlers
import os
import sys
import threading
from contextlib import contextmanager, suppress
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import TYPE_CHECKING
from urllib.parse import urlsplit, urlunsplit

from rich.console import Console
from rich.logging import RichHandler
from rich.traceback import install as install_rich_traceback

from canfar.errors import ErrorCode, LoggingEnvironmentError, StructuredError

if TYPE_CHECKING:
    from collections.abc import Callable, Iterator

LOGGER_NAME = "canfar"
LIBRARY_LOGGER_NAMES = ("vosfs", "fsspec_cli")
"""Storage libraries behind ``canfar data`` whose records follow CANFAR's level."""
_LOCK = threading.Lock()

MAX_LOGFILE_SIZE = 10 * 1024 * 1024  # 10MB
MAX_LOGFILE_COUNT = 10

LOG_LEVEL_ENV_VAR = "CANFAR_LOGLEVEL"


class LoggingLevel(str, Enum):
    """Logging levels accepted by the CLI and CANFAR environment policy."""

    CRITICAL = "critical"
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"
    DEBUG = "debug"


DEFAULT_LOG_LEVEL = LoggingLevel.CRITICAL
VERBOSITY_LEVELS = (
    LoggingLevel.CRITICAL,
    LoggingLevel.INFO,
    LoggingLevel.DEBUG,
)
"""Levels for no ``-v``, ``-v`` (progress), and ``-vv`` or more (debugging)."""


class InvalidLoggingEnvironmentError(ValueError):
    """A known CANFAR logging environment variable has an invalid value."""

    def __init__(
        self,
        provided_value: str,
        *,
        env_var: str = LOG_LEVEL_ENV_VAR,
        expected: list[str] | None = None,
    ) -> None:
        expected = expected or [level.value for level in LoggingLevel]
        self.error = LoggingEnvironmentError(
            code=ErrorCode.LOGGING_INVALID_ENV_VALUE,
            message=f"Invalid value for {env_var}.",
            hint=f"Use one of: {', '.join(expected)}.",
            env_var=env_var,
            provided_value=provided_value,
            expected=expected,
        )
        details = (
            f"{self.error.code} env_var={self.error.env_var} "
            f"provided_value={self.error.provided_value} "
            f"expected={','.join(self.error.expected)}"
        )
        super().__init__(details)


class InvalidLogFilePathError(ValueError):
    """The requested file sink target is not a file path."""

    def __init__(self) -> None:
        self.error = StructuredError(
            code=ErrorCode.LOGGING_INVALID_FILE_PATH,
            message="Invalid log file path.",
            hint="Choose a file path other than '-' or an existing directory.",
        )
        message = f"{self.error.code}: {self.error.message} {self.error.hint}"
        super().__init__(message)


def _resolve_log_file_path(log_file: Path) -> Path:
    """Resolve and validate one explicitly requested file sink path."""
    if str(log_file) == "-":
        raise InvalidLogFilePathError
    resolved = log_file if log_file.is_absolute() else Path.cwd() / log_file
    try:
        is_directory = resolved.is_dir()
    except OSError:
        is_directory = False
    if is_directory:
        raise InvalidLogFilePathError
    return resolved


def _warn_file_sink_unavailable(
    warning_writer: Callable[[StructuredError], None] | None = None,
) -> None:
    """Emit the stable sink warning without routing back through logging."""
    error = StructuredError(
        code=ErrorCode.LOGGING_FILE_SINK_UNAVAILABLE,
        message="File logging is unavailable.",
        hint="Logging continues on stderr.",
    )
    if warning_writer is not None:
        warning_writer(error)
        return
    with suppress(OSError):
        sys.stderr.write(f"{error.code}: {error.message}\n")


def safe_url(value: object) -> str:
    """Return a URL without user information, query parameters, or fragments."""
    parts = urlsplit(str(value))
    netloc = parts.netloc.rsplit("@", 1)[-1]
    return urlunsplit((parts.scheme, netloc, parts.path, "", ""))


class _JSONLinesFormatter(logging.Formatter):
    """Format one logging event as one UTF-8 JSON object."""

    def format(self, record: logging.LogRecord) -> str:
        timestamp = datetime.fromtimestamp(record.created, timezone.utc)
        payload: dict[str, object] = {
            "timestamp": timestamp.isoformat(timespec="milliseconds").replace(
                "+00:00", "Z"
            ),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        diagnostics = [value for value in (record.exc_text, record.stack_info) if value]
        if diagnostics:
            payload["exception"] = "\n".join(diagnostics)
        return json.dumps(payload, ensure_ascii=False, separators=(",", ":"))


class _ResilientRotatingFileHandler(logging.handlers.RotatingFileHandler):
    """Disable this sink after its first runtime failure."""

    _disabled = False
    warning_writer: Callable[[StructuredError], None] | None = None

    def emit(self, record: logging.LogRecord) -> None:
        if not self._disabled:
            super().emit(record)

    def handleError(  # noqa: N802
        self,
        record: logging.LogRecord,  # noqa: ARG002
    ) -> None:
        self._disabled = True
        with suppress(OSError):
            self.close()
        _warn_file_sink_unavailable(self.warning_writer)


def _resolve_log_level(
    loglevel: int | str | LoggingLevel | None,
    verbosity: int,
) -> LoggingLevel:
    """Resolve CLI, environment, and packaged logging-level precedence."""
    if loglevel is not None:
        if isinstance(loglevel, LoggingLevel):
            return loglevel
        if isinstance(loglevel, int):
            loglevel = logging.getLevelName(loglevel)
        try:
            return LoggingLevel(str(loglevel).lower())
        except ValueError as err:
            msg = f"Invalid log level: {loglevel}"
            raise ValueError(msg) from err

    if verbosity:
        return VERBOSITY_LEVELS[min(verbosity, len(VERBOSITY_LEVELS) - 1)]

    env_level = os.environ.get(LOG_LEVEL_ENV_VAR)
    if env_level is None:
        return DEFAULT_LOG_LEVEL
    try:
        return LoggingLevel(env_level.lower())
    except ValueError as err:
        raise InvalidLoggingEnvironmentError(env_level) from err


_rich_handler: RichHandler | None = None
"""The stderr handler that ``configure_logging`` installed, if any."""


def _loggers() -> list[logging.Logger]:
    """Return the CANFAR logger and the storage library loggers it routes."""
    return [logging.getLogger(name) for name in (LOGGER_NAME, *LIBRARY_LOGGER_NAMES)]


def _file_handler(
    logfile: Path,
    level: int,
    warning_writer: Callable[[StructuredError], None] | None,
) -> logging.Handler | None:
    """Return a rotating JSON Lines file handler, or None when the path is unusable."""
    try:
        logfile.parent.mkdir(parents=True, exist_ok=True)
        handler = _ResilientRotatingFileHandler(
            filename=logfile,
            maxBytes=MAX_LOGFILE_SIZE,
            backupCount=MAX_LOGFILE_COUNT,
            encoding="utf-8",
        )
    except OSError:
        _warn_file_sink_unavailable(warning_writer)
        return None
    handler.warning_writer = warning_writer
    handler.setLevel(level)
    handler.setFormatter(_JSONLinesFormatter())
    return handler


@contextmanager
def logs_through(console: Console) -> Iterator[None]:
    """Write CANFAR's stderr log records through ``console`` for a while.

    A Rich live display on ``console`` stays intact only when everything else
    written to stderr goes through that same console.
    """
    handler = _rich_handler
    if handler is None:
        yield
        return
    previous, handler.console = handler.console, console
    try:
        yield
    finally:
        handler.console = previous


def configure_logging(
    loglevel: int | str | LoggingLevel | None = None,
    *,
    verbosity: int = 0,
    log_file: Path | None = None,
    warning_writer: Callable[[StructuredError], None] | None = None,
) -> LoggingLevel:
    """Configure Rich stderr logging and an optional rotating JSONL file sink.

    The CANFAR and storage library loggers share the handlers; configuring
    again replaces them. The level comes from ``loglevel``, then
    ``verbosity``, then ``CANFAR_LOGLEVEL``, then the packaged default.

    Returns:
        The resolved logging level.
    """
    global _rich_handler  # noqa: PLW0603 - logging configuration is process-wide.

    resolved = _resolve_log_level(loglevel, verbosity)
    target = _resolve_log_file_path(log_file) if log_file is not None else None
    level: int = getattr(logging, resolved.value.upper())
    with _LOCK:
        install_rich_traceback(show_locals=False, suppress=[])
        for logger in _loggers():
            for handler in logger.handlers[:]:
                handler.close()
                logger.removeHandler(handler)
        _rich_handler = RichHandler(
            console=Console(stderr=True),
            show_path=True,
            show_time=True,
            enable_link_path=True,
            rich_tracebacks=True,
            tracebacks_show_locals=False,
        )
        _rich_handler.setLevel(level)
        _rich_handler.setFormatter(logging.Formatter("%(message)s"))
        handlers: list[logging.Handler] = [_rich_handler]
        if target is not None and (
            file_handler := _file_handler(target, level, warning_writer)
        ):
            handlers.append(file_handler)
        for logger in _loggers():
            logger.setLevel(level)
            for handler in handlers:
                logger.addHandler(handler)
            logger.propagate = False
    return resolved


def get_logger(name: str | None = None) -> logging.Logger:
    """Return a CANFAR logger, optionally nested under ``canfar``."""
    if name is None:
        name = LOGGER_NAME
    elif not name.startswith(LOGGER_NAME):
        name = f"{LOGGER_NAME}.{name}"
    return logging.getLogger(name)
