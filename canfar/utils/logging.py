# canfar/logging.py
"""Unified logging configuration for the CANFAR client library.

This module provides a centralized logging configuration using Python's
logging library with Rich for enhanced console output. It follows best
practices for library logging.

Best Practices Implemented:
1. Use a single named logger for the entire library
2. Lazy logger initialization to avoid import-time side effects
3. Rich integration for beautiful console output
4. Optional file logging with rotation
5. Performance optimizations (lazy formatting, level checks)
6. Proper exception handling and context
7. Thread-safe configuration
"""

from __future__ import annotations

import json
import logging
import logging.handlers
import os
import re
import sys
import threading
import traceback
from contextlib import contextmanager, suppress
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import TYPE_CHECKING
from urllib.parse import urlsplit, urlunsplit

from rich.console import Console
from rich.logging import RichHandler
from rich.traceback import install as install_rich_traceback

from canfar import CONFIG_DIR, CONFIG_PATH  # noqa: F401
from canfar.errors import ErrorCode, LoggingEnvironmentError, StructuredError

if TYPE_CHECKING:
    from collections.abc import Callable, Iterator

    from httpx import AsyncClient, Client
    from logfire import LevelName
    from logfire.integrations.httpx import RequestInfo, ResponseInfo
    from opentelemetry.trace import Span

LOGFILE_PATH: Path = CONFIG_DIR / "client.log"
LOG_LEVEL: int = 10
# Library logger name - all modules should use this as root
LOGGER_NAME = "canfar"
# Thread lock for configuration safety
_LOCK = threading.Lock()
_TELEMETRY_ENV_LOCK = threading.RLock()
_instrument_httpx: Callable[..., None] | None = None

# Default configuration
FORMAT = (
    "%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s"
)
RICH_FORMAT = "%(message)s"
MAX_LOGFILE_SIZE = 10 * 1024 * 1024  # 10MB
MAX_LOGFILE_COUNT = 10

LOG_LEVEL_ENV_VAR = "CANFAR_LOGLEVEL"
OTLP_ENDPOINT_ENV_VAR = "CANFAR_OTEL_EXPORTER_OTLP_ENDPOINT"
_OTLP_ENDPOINT_EXPECTED = (
    "absolute http(s) base URL without credentials, query, or fragment"
)
_TELEMETRY_ENV_PREFIXES = ("LOGFIRE_", "OTEL_")


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
_LOGFIRE_LEVELS: dict[LoggingLevel, LevelName] = {
    LoggingLevel.CRITICAL: "fatal",
    LoggingLevel.ERROR: "error",
    LoggingLevel.WARNING: "warning",
    LoggingLevel.INFO: "info",
    LoggingLevel.DEBUG: "debug",
}

_SENSITIVE_NAME_FRAGMENT = (
    r"(?:access[._ -]?token|refresh[._ -]?token|client[._ -]?secret|password|"
    r"passwd|passphrase|pwd|credential|api[._ -]?key|secret|cookie|set-cookie|"
    r"authorization|proxy-authorization|x509|certificate|private[._ -]?key|pem)"
)
_SCRUBBING_PATTERNS = (_SENSITIVE_NAME_FRAGMENT,)
_REQUEST_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:/-]{0,127}$")
_PEM_BLOCK = re.compile(
    r"-----BEGIN [^-]*(?:PRIVATE KEY|CERTIFICATE)-----.*?"
    r"(?:-----END [^-]*(?:PRIVATE KEY|CERTIFICATE)-----|$)",
    re.IGNORECASE | re.DOTALL,
)
_BEARER_VALUE = re.compile(r"(?P<prefix>\bBearer\s+)[^\s,;]+", re.IGNORECASE)
_SENSITIVE_HEADER_VALUE = re.compile(
    r"(?P<prefix>['\"]?(?:authorization|proxy-authorization|cookie|set-cookie)"
    r"['\"]?\s*(?::|=)\s*)(?:\"[^\r\n]*\"|'[^\r\n]*'|[^\r\n]*)",
    re.IGNORECASE,
)
_SENSITIVE_VALUE = re.compile(
    rf"(?P<prefix>['\"]?{_SENSITIVE_NAME_FRAGMENT}['\"]?\s*(?::|=)\s*)"
    r"(?:\"[^\"]*\"|'[^']*'|[^\s,;]+)",
    re.IGNORECASE,
)
_SENSITIVE_FIELD = re.compile(_SENSITIVE_NAME_FRAGMENT, re.IGNORECASE)


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


def _resolve_otlp_endpoint() -> str | None:
    """Validate and return the explicit CANFAR OTLP endpoint, if present."""
    value = os.environ.get(OTLP_ENDPOINT_ENV_VAR)
    if value is None:
        return None

    try:
        parts = urlsplit(value)
        port = parts.port
        valid = (
            not any(character.isspace() for character in value)
            and parts.scheme.lower() in {"http", "https"}
            and parts.hostname is not None
            and parts.username is None
            and parts.password is None
            and "?" not in value
            and "#" not in value
            and not parts.netloc.endswith(":")
            and (port is None or port > 0)
        )
    except ValueError:
        valid = False

    if not valid:
        provided_value = "<redacted>"
        raise InvalidLoggingEnvironmentError(
            provided_value,
            env_var=OTLP_ENDPOINT_ENV_VAR,
            expected=[_OTLP_ENDPOINT_EXPECTED],
        )
    return value


@contextmanager
def _telemetry_environment(endpoint: str | None = None) -> Iterator[None]:
    """Briefly quarantine telemetry env during explicit setup/client creation.

    The upstream env-only API requires a short process-global mutation, so
    unrelated readers can briefly observe the quarantined state.
    """
    mapped = (
        {
            "OTEL_EXPORTER_OTLP_ENDPOINT": endpoint,
            "OTEL_TRACES_EXPORTER": "otlp",
            "OTEL_METRICS_EXPORTER": "none",
            "OTEL_LOGS_EXPORTER": "none",
        }
        if endpoint is not None
        else {}
    )
    with _TELEMETRY_ENV_LOCK:
        previous = {
            key: value
            for key, value in os.environ.items()
            if key.startswith(_TELEMETRY_ENV_PREFIXES)
        }
        for key in tuple(os.environ):
            if key.startswith(_TELEMETRY_ENV_PREFIXES):
                os.environ.pop(key)
        os.environ.update(mapped)
        try:
            yield
        finally:
            for key, value in mapped.items():
                if os.environ.get(key) == value:
                    os.environ.pop(key)
            for key, value in previous.items():
                os.environ.setdefault(key, value)


def safe_url(value: object) -> str:
    """Return a URL without user information, query parameters, or fragments."""
    parts = urlsplit(str(value))
    netloc = parts.netloc.rsplit("@", 1)[-1]
    return urlunsplit((parts.scheme, netloc, parts.path, "", ""))


def redact_text(value: str) -> str:
    """Redact common Authentication and certificate secrets from text."""
    value = _PEM_BLOCK.sub("<redacted>", value)
    value = _SENSITIVE_HEADER_VALUE.sub(r"\g<prefix><redacted>", value)
    value = _BEARER_VALUE.sub(r"\g<prefix><redacted>", value)
    return _SENSITIVE_VALUE.sub(r"\g<prefix><redacted>", value)


class _RedactingFilter(logging.Filter):
    """Sanitize a record only when a configured handler emits it."""

    def filter(self, record: logging.LogRecord) -> bool:
        record.msg = redact_text(record.getMessage())
        record.args = ()
        if record.exc_info:
            record.exc_text = redact_text(
                "".join(traceback.format_exception(*record.exc_info))
            )
            record.exc_info = None
        if record.stack_info:
            record.stack_info = redact_text(record.stack_info)
        for key, value in tuple(record.__dict__.items()):
            if isinstance(value, str):
                record.__dict__[key] = (
                    "<redacted>"
                    if _SENSITIVE_FIELD.fullmatch(key)
                    else redact_text(value)
                )
        return True


_REDACTION_FILTER = _RedactingFilter()


class _JSONLinesFormatter(logging.Formatter):
    """Format one redacted logging event as one UTF-8 JSON object."""

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


def _httpx_request_hook(span: Span, request: RequestInfo) -> None:
    """Overwrite native URL attributes with a safe request URL."""
    url = safe_url(request.url)
    span.set_attribute("url.full", url)
    span.set_attribute("http.url", url)


def _httpx_response_hook(
    span: Span,
    request: RequestInfo,
    response: ResponseInfo,
) -> None:
    """Capture one validated response request identifier."""
    del request
    if response.headers is None:
        return
    value = response.headers.get("x-request-id")
    if value and _REQUEST_ID.fullmatch(value):
        span.set_attribute("request_id", value)


def instrument_httpx(client: Client | AsyncClient) -> None:
    """Instrument one cached client after explicit logging configuration."""
    if _instrument_httpx is None:
        return
    with _telemetry_environment():
        from canfar.utils.telemetry import (  # noqa: PLC0415
            safe_httpx_tracer_provider,
        )

        _instrument_httpx(
            client,
            capture_all=False,
            capture_headers=False,
            capture_request_body=False,
            capture_response_body=False,
            request_hook=_httpx_request_hook,
            response_hook=_httpx_response_hook,
            tracer_provider=safe_httpx_tracer_provider(),
        )


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
    """Centralized logger configuration for the CANFAR client.

    This class manages the configuration of logging for the entire library,
    providing a unified interface for setting up console and file logging
    with Rich integration.
    """

    _configured = False
    _rich_handler: RichHandler | None = None

    def __init__(self) -> None:
        """Constructor."""
        self._logger: logging.Logger | None = None
        self._file_handler: logging.handlers.RotatingFileHandler | None = None

    @property
    def logger(self) -> logging.Logger:
        """CANFAR Logger.

        Returns:
            logging.Logger: logging object.
        """
        if self._logger is None:
            self._logger = logging.getLogger(LOGGER_NAME)
        return self._logger

    def configure(
        self,
        loglevel: int | str = logging.INFO,
        filelog: bool = False,
        *,
        log_file: Path | None = None,
        warning_writer: Callable[[StructuredError], None] | None = None,
    ) -> None:
        """Configure the CANFAR logger with Rich support and optional file logging.

        Args:
            loglevel (int | str, optional): Logging level. Defaults to logging.INFO.
            filelog (bool, optional): Whether to enable file logging. Defaults to False.
            log_file: Explicit file sink path. Overrides the legacy ``filelog`` path.
            warning_writer: Optional sink for structured file-logging warnings.
        """
        target = log_file if log_file is not None else LOGFILE_PATH if filelog else None
        if target is not None:
            target = _resolve_log_file_path(target)
        with _LOCK:
            install_rich_traceback(show_locals=False, suppress=[])
            if self._configured:
                # Allow reconfiguration but clean up existing handlers
                self._cleanup_handlers()
            # Convert string level to int if needed
            if isinstance(loglevel, str):
                loglevel = getattr(logging, loglevel.upper())
            # Configure the main logger
            logger = self.logger
            logger.setLevel(loglevel)
            # Setup Rich console handler
            self._rich_handler = RichHandler(
                console=Console(stderr=True),
                show_path=True,
                show_time=True,
                enable_link_path=True,
                rich_tracebacks=True,
                tracebacks_show_locals=False,
            )
            self._rich_handler.setLevel(loglevel)
            self._rich_handler.addFilter(_REDACTION_FILTER)

            # Rich handler uses a simpler format since Rich adds the styling
            formatter = logging.Formatter(RICH_FORMAT)
            self._rich_handler.setFormatter(formatter)
            logger.addHandler(self._rich_handler)

            # Setup file logging if requested
            if target is not None:
                self._setup_file_logging(
                    target,
                    MAX_LOGFILE_SIZE,
                    MAX_LOGFILE_COUNT,
                    int(loglevel),
                    warning_writer,
                )

            # Prevent propagation to root logger to avoid duplicate messages
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
        """Setup rotating file handler for logging."""
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
        self._file_handler.addFilter(_REDACTION_FILTER)
        self._file_handler.setFormatter(_JSONLinesFormatter())
        self.logger.addHandler(self._file_handler)

    def _cleanup_handlers(self) -> None:
        """Remove existing handlers to allow reconfiguration."""
        logger = self.logger

        # Remove all existing handlers
        for handler in logger.handlers[:]:
            handler.close()
            logger.removeHandler(handler)

        self._rich_handler = None
        self._file_handler = None

    def set_level(self, level: int | str) -> None:
        """Change the logging level for all handlers.

        Args:
            level: New logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL or int)
        """
        if isinstance(level, str):
            level = getattr(logging, level.upper())

        logger = self.logger
        logger.setLevel(level)

        # Update all handler levels
        for handler in logger.handlers:
            handler.setLevel(level)

    def get_child_logger(self, name: str) -> logging.Logger:
        """Get a child logger for a specific module.

        Args:
            name: Module name (will be prefixed with 'canfar')

        Returns:
            Child logger that inherits configuration from parent
        """
        if not name.startswith(LOGGER_NAME):
            name = f"{LOGGER_NAME}.{name}"
        return logging.getLogger(name)

    def enable_debug_mode(self) -> None:
        """Enable debug mode with detailed logging."""
        self.set_level(logging.DEBUG)

        # Add more detailed formatting for debug mode
        if self._rich_handler:
            debug_formatter = logging.Formatter(
                "%(name)s:%(funcName)s:%(lineno)d - %(message)s"
            )
            self._rich_handler.setFormatter(debug_formatter)


# Global logger instance
_canfar_logger = CanfarLogger()


# Convenience functions for easy access
def configure_logging(
    loglevel: int | str | LoggingLevel | None = None,
    filelog: bool = False,
    *,
    verbosity: int = 0,
    log_file: Path | None = None,
    warning_writer: Callable[[StructuredError], None] | None = None,
) -> LoggingLevel:
    """Configure logging explicitly using CLI, environment, and packaged policy."""
    global _instrument_httpx  # noqa: PLW0603

    level = _resolve_log_level(loglevel, verbosity)
    endpoint = _resolve_otlp_endpoint()

    with _telemetry_environment(endpoint):
        # Logfire is intentionally imported and configured only at this runtime seam.
        import logfire  # noqa: PLC0415

        from canfar.utils.telemetry import install_w3c_propagator  # noqa: PLC0415

        configured = logfire.configure(
            send_to_logfire=False,
            console=False,
            metrics=False,
            scrubbing=logfire.ScrubbingOptions(extra_patterns=_SCRUBBING_PATTERNS),
            inspect_arguments=False,
            distributed_tracing=False,
            min_level=_LOGFIRE_LEVELS[level],
        )
        install_w3c_propagator()
    _instrument_httpx = configured.instrument_httpx
    _canfar_logger.configure(
        loglevel=level.value,
        filelog=filelog,
        log_file=log_file,
        warning_writer=warning_writer,
    )
    return level


def get_logger(name: str | None = None) -> logging.Logger:
    """Get a CANFAR logger instance.

    Args:
        name: Optional module name for child logger

    Returns:
        Logger instance
    """
    if name is None:
        return _canfar_logger.logger
    return _canfar_logger.get_child_logger(name)


def set_log_level(level: int | str) -> None:
    """Set logging level for all Canfar loggers."""
    _canfar_logger.set_level(level)


def enable_debug() -> None:
    """Enable debug mode with detailed logging."""
    _canfar_logger.enable_debug_mode()
