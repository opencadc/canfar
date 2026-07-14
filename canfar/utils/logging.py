"""CANFAR logging: stdlib logging with Rich stderr and optional JSONL file sink."""

from __future__ import annotations

import json
import logging
import logging.handlers
import os
import sys
import threading
from contextlib import suppress
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
    from collections.abc import Callable

LOGGER_NAME = "canfar"
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
    LoggingLevel.ERROR,
    LoggingLevel.WARNING,
    LoggingLevel.INFO,
    LoggingLevel.DEBUG,
)


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
        for name in ("event_code", "request_id", "trace_id", "span_id"):
            value = getattr(record, name, None)
            if isinstance(value, str):
                payload[name] = value
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


class CanfarLogger:
    """Configure stdlib logging for the CANFAR logger name."""

    _configured = False
    _rich_handler: RichHandler | None = None

    def __init__(self) -> None:
        """Initialize per-instance file-handler state."""
        self._file_handler: logging.handlers.RotatingFileHandler | None = None

    @property
    def logger(self) -> logging.Logger:
        """Return the CANFAR root logger."""
        return logging.getLogger(LOGGER_NAME)

    def configure(
        self,
        loglevel: int | str = logging.INFO,
        *,
        log_file: Path | None = None,
        warning_writer: Callable[[StructuredError], None] | None = None,
    ) -> None:
        """Configure Rich stderr logging and an optional rotating JSONL file sink."""
        target = _resolve_log_file_path(log_file) if log_file is not None else None
        with _LOCK:
            install_rich_traceback(show_locals=False, suppress=[])
            if self._configured:
                self._cleanup_handlers()
            if isinstance(loglevel, str):
                loglevel = getattr(logging, loglevel.upper())
            logger = self.logger
            logger.setLevel(loglevel)
            self._rich_handler = RichHandler(
                console=Console(stderr=True),
                show_path=True,
                show_time=True,
                enable_link_path=True,
                rich_tracebacks=True,
                tracebacks_show_locals=False,
            )
            self._rich_handler.setLevel(loglevel)
            self._rich_handler.setFormatter(logging.Formatter("%(message)s"))
            logger.addHandler(self._rich_handler)

            if target is not None:
                self._setup_file_logging(
                    target,
                    MAX_LOGFILE_SIZE,
                    MAX_LOGFILE_COUNT,
                    int(loglevel),
                    warning_writer,
                )

            logger.propagate = False
            self._configured = True

    def _setup_file_logging(
        self,
        logfile: Path,
        size: int,
        count: int,
        level: int,
        warning_writer: Callable[[StructuredError], None] | None = None,
    ) -> None:
        """Attach a rotating JSON Lines file handler when the path is usable."""
        try:
            logfile.parent.mkdir(parents=True, exist_ok=True)
            self._file_handler = _ResilientRotatingFileHandler(
                filename=logfile,
                maxBytes=size,
                backupCount=count,
                encoding="utf-8",
            )
        except OSError:
            self._file_handler = None
            _warn_file_sink_unavailable(warning_writer)
            return
        self._file_handler.warning_writer = warning_writer
        self._file_handler.setLevel(level)
        self._file_handler.setFormatter(_JSONLinesFormatter())
        self.logger.addHandler(self._file_handler)

    def _cleanup_handlers(self) -> None:
        """Remove existing handlers to allow reconfiguration."""
        logger = self.logger
        for handler in logger.handlers[:]:
            handler.close()
            logger.removeHandler(handler)
        self._rich_handler = None
        self._file_handler = None


_canfar_logger = CanfarLogger()


def configure_logging(
    loglevel: int | str | LoggingLevel | None = None,
    *,
    verbosity: int = 0,
    log_file: Path | None = None,
    warning_writer: Callable[[StructuredError], None] | None = None,
) -> LoggingLevel:
    """Configure logging explicitly using CLI, environment, and packaged policy."""
    level = _resolve_log_level(loglevel, verbosity)
    _canfar_logger.configure(
        loglevel=level.value,
        log_file=log_file,
        warning_writer=warning_writer,
    )
    return level


def get_logger(name: str | None = None) -> logging.Logger:
    """Return a CANFAR logger, optionally nested under ``canfar``."""
    if name is None:
        name = LOGGER_NAME
    elif not name.startswith(LOGGER_NAME):
        name = f"{LOGGER_NAME}.{name}"
    return logging.getLogger(name)
