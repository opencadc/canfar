"""Comprehensive tests for the logging module."""

from __future__ import annotations

import json
import logging
import os
import re
import tempfile
import threading
from contextlib import ExitStack
from pathlib import Path
from typing import TYPE_CHECKING
from unittest.mock import Mock, patch

import pytest
from rich.logging import RichHandler

from canfar.errors import ErrorCode
from canfar.utils.logging import (
    CONFIG_DIR,
    CONFIG_PATH,
    FORMAT,
    LOG_LEVEL,
    LOGFILE_PATH,
    LOGGER_NAME,
    MAX_LOGFILE_COUNT,
    MAX_LOGFILE_SIZE,
    RICH_FORMAT,
    CanfarLogger,
    InvalidLoggingEnvironmentError,
    LoggingLevel,
    configure_logging,
    enable_debug,
    get_logger,
    set_log_level,
)

if TYPE_CHECKING:
    from collections.abc import Generator


def _raise_secret_error(secret: str) -> None:
    msg = f"refresh_token={secret}"
    raise RuntimeError(msg)


_PEM_VALUE_FIELD = "private-key".replace("-", "_")
_SERVICE_VALUE_FIELD = "api-key".replace("-", "_")
_OTLP_ENDPOINT_ENV_VAR = "CANFAR_OTEL_EXPORTER_OTLP_ENDPOINT"
_OTLP_ENDPOINT_EXPECTED = (
    "absolute http(s) base URL without credentials, query, or fragment"
)


class TestCanfarLogger:
    """Test cases for the CanfarLogger class."""

    @pytest.fixture
    def canfar_logger(self) -> Generator[CanfarLogger]:
        """Create a fresh CanfarLogger instance for testing."""
        logger = CanfarLogger()
        yield logger
        # Cleanup after test
        logger._cleanup_handlers()  # noqa: SLF001
        logger._configured = False  # noqa: SLF001

    @pytest.fixture
    def temp_log_dir(self) -> Generator[Path]:
        """Create a temporary directory for log files."""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield Path(temp_dir)

    def test_logger_property_lazy_initialization(
        self, canfar_logger: CanfarLogger
    ) -> None:
        """Test that logger property initializes lazily."""
        assert canfar_logger._logger is None  # noqa: SLF001
        logger = canfar_logger.logger
        assert canfar_logger._logger is not None  # noqa: SLF001
        assert isinstance(logger, logging.Logger)
        assert logger.name == LOGGER_NAME

    def test_logger_property_returns_same_instance(
        self, canfar_logger: CanfarLogger
    ) -> None:
        """Test that logger property returns the same instance."""
        logger1 = canfar_logger.logger
        logger2 = canfar_logger.logger
        assert logger1 is logger2

    def test_configure_basic_setup(self, canfar_logger: CanfarLogger) -> None:
        """Test basic configuration with default parameters."""
        canfar_logger.configure()

        logger = canfar_logger.logger
        assert logger.level == logging.INFO
        assert len(logger.handlers) == 1
        assert isinstance(logger.handlers[0], RichHandler)
        assert not logger.propagate
        assert canfar_logger._configured  # noqa: SLF001

    def test_configure_with_string_loglevel(self, canfar_logger: CanfarLogger) -> None:
        """Test configuration with string log level."""
        canfar_logger.configure(loglevel="DEBUG")

        logger = canfar_logger.logger
        assert logger.level == logging.DEBUG
        assert logger.handlers[0].level == logging.DEBUG

    def test_configure_with_int_loglevel(self, canfar_logger: CanfarLogger) -> None:
        """Test configuration with integer log level."""
        canfar_logger.configure(loglevel=logging.WARNING)

        logger = canfar_logger.logger
        assert logger.level == logging.WARNING
        assert logger.handlers[0].level == logging.WARNING

    def test_configure_with_file_logging(
        self, canfar_logger: CanfarLogger, temp_log_dir: Path
    ) -> None:
        """Test configuration with file logging enabled."""
        log_file = temp_log_dir / "test.log"

        with patch("canfar.utils.logging.LOGFILE_PATH", log_file):
            canfar_logger.configure(filelog=True)

        logger = canfar_logger.logger
        assert len(logger.handlers) == 2  # Rich handler + file handler

        # Check file handler
        file_handler = None
        for handler in logger.handlers:
            if hasattr(handler, "baseFilename"):  # RotatingFileHandler
                file_handler = handler
                break

        assert file_handler is not None
        assert hasattr(file_handler, "baseFilename")
        assert file_handler.baseFilename == str(log_file)  # type: ignore[attr-defined]
        assert canfar_logger._file_handler is file_handler  # noqa: SLF001

    def test_explicit_file_path_wins_over_legacy_file_logging(
        self,
        canfar_logger: CanfarLogger,
        temp_log_dir: Path,
    ) -> None:
        """An explicit sink target wins when the legacy switch is also enabled."""
        legacy = temp_log_dir / "legacy.jsonl"
        explicit = temp_log_dir / "explicit.jsonl"

        with patch("canfar.utils.logging.LOGFILE_PATH", legacy):
            canfar_logger.configure(filelog=True, log_file=explicit)

        assert explicit.is_file()
        assert not legacy.exists()

    def test_configure_reconfiguration_cleans_handlers(
        self, canfar_logger: CanfarLogger
    ) -> None:
        """Test that reconfiguration cleans up existing handlers."""
        # First configuration
        canfar_logger.configure(loglevel=logging.INFO)
        first_handler = canfar_logger.logger.handlers[0]

        # Reconfigure
        canfar_logger.configure(loglevel=logging.DEBUG)

        # Should have new handler, old one should be cleaned up
        assert len(canfar_logger.logger.handlers) == 1
        assert canfar_logger.logger.handlers[0] is not first_handler

    def test_setup_file_logging_creates_directory(
        self, canfar_logger: CanfarLogger, temp_log_dir: Path
    ) -> None:
        """Test that file logging setup creates necessary directories."""
        log_file = temp_log_dir / "nested" / "dir" / "test.log"

        canfar_logger._setup_file_logging(  # noqa: SLF001
            log_file, MAX_LOGFILE_SIZE, MAX_LOGFILE_COUNT, logging.INFO
        )

        assert log_file.parent.exists()
        assert canfar_logger._file_handler is not None  # noqa: SLF001

    def test_cleanup_handlers_removes_all_handlers(
        self, canfar_logger: CanfarLogger
    ) -> None:
        """Test that cleanup removes all handlers."""
        canfar_logger.configure(filelog=True)
        logger = canfar_logger.logger

        # Should have handlers
        assert len(logger.handlers) > 0
        assert canfar_logger._rich_handler is not None  # noqa: SLF001

        canfar_logger._cleanup_handlers()  # noqa: SLF001

        # Should have no handlers
        assert len(logger.handlers) == 0
        assert canfar_logger._rich_handler is None  # noqa: SLF001
        assert canfar_logger._file_handler is None  # noqa: SLF001

    def test_set_level_with_string(self, canfar_logger: CanfarLogger) -> None:
        """Test setting log level with string."""
        canfar_logger.configure()
        canfar_logger.set_level("ERROR")

        logger = canfar_logger.logger
        assert logger.level == logging.ERROR
        for handler in logger.handlers:
            assert handler.level == logging.ERROR

    def test_set_level_with_int(self, canfar_logger: CanfarLogger) -> None:
        """Test setting log level with integer."""
        canfar_logger.configure()
        canfar_logger.set_level(logging.CRITICAL)

        logger = canfar_logger.logger
        assert logger.level == logging.CRITICAL
        for handler in logger.handlers:
            assert handler.level == logging.CRITICAL

    def test_get_child_logger_with_prefix(self, canfar_logger: CanfarLogger) -> None:
        """Test getting child logger with canfar prefix."""
        child = canfar_logger.get_child_logger("canfar.test.module")
        assert child.name == "canfar.test.module"

    def test_get_child_logger_without_prefix(self, canfar_logger: CanfarLogger) -> None:
        """Test getting child logger without canfar prefix."""
        child = canfar_logger.get_child_logger("test.module")
        assert child.name == "canfar.test.module"

    def test_enable_debug_mode(self, canfar_logger: CanfarLogger) -> None:
        """Test enabling debug mode."""
        canfar_logger.configure()
        canfar_logger.enable_debug_mode()

        logger = canfar_logger.logger
        assert logger.level == logging.DEBUG

        # Check that formatter was updated for debug mode
        if canfar_logger._rich_handler and canfar_logger._rich_handler.formatter:  # noqa: SLF001
            formatter = canfar_logger._rich_handler.formatter  # noqa: SLF001
            assert hasattr(formatter, "_fmt")
            assert "%(funcName)s" in formatter._fmt  # type: ignore[attr-defined] # noqa: SLF001
            assert "%(lineno)d" in formatter._fmt  # type: ignore[attr-defined] # noqa: SLF001

    def test_thread_safety_configuration(self, canfar_logger: CanfarLogger) -> None:
        """Test that configuration is thread-safe."""
        results: list[bool] = []

        def configure_logger() -> None:
            canfar_logger.configure()
            results.append(canfar_logger._configured)  # noqa: SLF001

        # Create multiple threads that configure simultaneously
        threads = [threading.Thread(target=configure_logger) for _ in range(5)]

        for thread in threads:
            thread.start()

        for thread in threads:
            thread.join()

        # All should have succeeded
        assert all(results)
        assert canfar_logger._configured  # noqa: SLF001

    def test_rich_handler_configuration(self, canfar_logger: CanfarLogger) -> None:
        """Test Rich handler is configured correctly."""
        canfar_logger.configure()

        rich_handler = canfar_logger._rich_handler  # noqa: SLF001
        assert rich_handler is not None
        assert isinstance(rich_handler, RichHandler)
        # RichHandler has these attributes but they might be private or different names
        # Just verify it's a RichHandler instance and has basic functionality
        assert hasattr(rich_handler, "console")
        assert hasattr(rich_handler, "emit")

    def test_file_handler_configuration(
        self, canfar_logger: CanfarLogger, temp_log_dir: Path
    ) -> None:
        """Test file handler is configured correctly."""
        log_file = temp_log_dir / "test.log"

        with patch("canfar.utils.logging.LOGFILE_PATH", log_file):
            canfar_logger.configure(filelog=True)

        file_handler = canfar_logger._file_handler  # noqa: SLF001
        assert file_handler is not None
        assert hasattr(file_handler, "maxBytes")
        assert hasattr(file_handler, "backupCount")
        assert file_handler.maxBytes == MAX_LOGFILE_SIZE  # type: ignore[attr-defined]
        assert file_handler.backupCount == MAX_LOGFILE_COUNT  # type: ignore[attr-defined]
        assert file_handler.formatter is not None


class TestConvenienceFunctions:
    """Test the convenience functions."""

    def test_configure_logging_calls_global_logger(self) -> None:
        """Runtime setup keeps telemetry local and configures the global logger."""
        configured = Mock()
        with (
            patch("canfar.utils.logging._canfar_logger.configure") as mock_configure,
            patch("logfire.configure", return_value=configured) as configure_logfire,
            patch("canfar.utils.logging._instrument_httpx", None),
        ):
            result = configure_logging(loglevel=logging.DEBUG, filelog=True)

            assert result is LoggingLevel.DEBUG
            mock_configure.assert_called_once()
            configure_logfire.assert_called_once()

    @pytest.mark.parametrize(
        ("endpoint", "expected"),
        [
            (None, {}),
            (
                "https://collector.example:4318/otel/v1",
                {
                    "OTEL_EXPORTER_OTLP_ENDPOINT": (
                        "https://collector.example:4318/otel/v1"
                    ),
                    "OTEL_TRACES_EXPORTER": "otlp",
                    "OTEL_METRICS_EXPORTER": "none",
                    "OTEL_LOGS_EXPORTER": "none",
                },
            ),
        ],
    )
    def test_configure_logging_uses_only_canfar_telemetry_environment(
        self,
        monkeypatch: pytest.MonkeyPatch,
        endpoint: str | None,
        expected: dict[str, str],
    ) -> None:
        """Only a valid CANFAR endpoint reaches upstream configuration."""
        ambient = {
            "LOGFIRE_TOKEN": "ambient-logfire-token",
            "LOGFIRE_SEND_TO_LOGFIRE": "true",
            "OTEL_EXPORTER_OTLP_ENDPOINT": "https://ambient.invalid",
            "OTEL_TRACES_EXPORTER": "console",
            "OTEL_METRICS_EXPORTER": "console",
            "OTEL_LOGS_EXPORTER": "console",
            "OTEL_PYTHON_HTTPX_EXCLUDED_URLS": ".*",
        }
        for key, value in ambient.items():
            monkeypatch.setenv(key, value)
        if endpoint is None:
            monkeypatch.delenv(_OTLP_ENDPOINT_ENV_VAR, raising=False)
        else:
            monkeypatch.setenv(_OTLP_ENDPOINT_ENV_VAR, endpoint)
        before = {
            key: value
            for key, value in os.environ.items()
            if key.startswith(("LOGFIRE_", "OTEL_"))
        }
        observed: dict[str, str] = {}

        def configure_upstream(**kwargs: object) -> Mock:
            del kwargs
            observed.update(
                {
                    key: value
                    for key, value in os.environ.items()
                    if key.startswith(("LOGFIRE_", "OTEL_"))
                }
            )
            return Mock()

        with (
            patch("logfire.configure", side_effect=configure_upstream),
            patch("canfar.utils.logging._canfar_logger.configure"),
            patch("canfar.utils.logging._instrument_httpx", None),
        ):
            configure_logging(loglevel="ERROR")

        assert observed == expected
        assert {
            key: value
            for key, value in os.environ.items()
            if key.startswith(("LOGFIRE_", "OTEL_"))
        } == before

    def test_configure_logging_preserves_telemetry_changes_made_during_setup(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Upstream setup does not erase telemetry changes made during its call."""
        monkeypatch.setenv(
            _OTLP_ENDPOINT_ENV_VAR,
            "https://collector.example:4318/otel",
        )
        monkeypatch.setenv("OTEL_TRACES_EXPORTER", "console")

        def configure_upstream(**kwargs: object) -> Mock:
            del kwargs
            assert os.environ["OTEL_TRACES_EXPORTER"] == "otlp"
            os.environ["OTEL_TRACES_EXPORTER"] = "zipkin"
            os.environ["OTEL_RESOURCE_ATTRIBUTES"] = "service.name=host"
            return Mock()

        with (
            patch("logfire.configure", side_effect=configure_upstream),
            patch("canfar.utils.logging._canfar_logger.configure"),
            patch("canfar.utils.logging._instrument_httpx", None),
        ):
            configure_logging(loglevel="ERROR")

        assert os.environ["OTEL_TRACES_EXPORTER"] == "zipkin"
        assert os.environ["OTEL_RESOURCE_ATTRIBUTES"] == "service.name=host"

    def test_configure_logging_restores_ambient_telemetry_after_failure(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Upstream failure restores every hidden ambient setting exactly."""
        ambient = {
            "LOGFIRE_TOKEN": "ambient-logfire-token",
            "OTEL_EXPORTER_OTLP_ENDPOINT": "https://ambient.invalid/path",
            "OTEL_INSTRUMENTATION_HTTP_CAPTURE_HEADERS_CLIENT_REQUEST": ".*",
        }
        for key, value in ambient.items():
            monkeypatch.setenv(key, value)
        before = {
            key: value
            for key, value in os.environ.items()
            if key.startswith(("LOGFIRE_", "OTEL_"))
        }

        def fail_upstream(**kwargs: object) -> None:
            del kwargs
            assert not any(key.startswith(("LOGFIRE_", "OTEL_")) for key in os.environ)
            msg = "upstream configuration failed"
            raise RuntimeError(msg)

        with (
            patch("logfire.configure", side_effect=fail_upstream),
            pytest.raises(RuntimeError, match="upstream configuration failed"),
        ):
            configure_logging(loglevel="ERROR")

        assert {
            key: value
            for key, value in os.environ.items()
            if key.startswith(("LOGFIRE_", "OTEL_"))
        } == before

    @pytest.mark.parametrize(
        "value",
        [
            "collector.example:4318",
            "ftp://collector.example/otel",
            "ftp://collector.example/client_secret=opaque",
            "https:///otel",
            "https://user:password@collector.example/otel",
            "https://collector.example/otel?token=value",
            "https://collector.example/otel#fragment",
            " https://collector.example/otel",
            "https://collector.example:99999/otel",
            "https://collector.example:/otel",
        ],
    )
    def test_invalid_otlp_endpoint_fails_before_upstream_configuration(
        self,
        monkeypatch: pytest.MonkeyPatch,
        value: str,
    ) -> None:
        """Known-invalid endpoint shapes fail before Logfire configuration."""
        monkeypatch.setenv(_OTLP_ENDPOINT_ENV_VAR, value)

        with (
            patch("logfire.configure") as configure_upstream,
            pytest.raises(InvalidLoggingEnvironmentError) as caught,
        ):
            configure_logging(loglevel="ERROR")

        configure_upstream.assert_not_called()
        assert caught.value.error.env_var == _OTLP_ENDPOINT_ENV_VAR
        assert caught.value.error.provided_value == "<redacted>"
        assert caught.value.error.expected == [_OTLP_ENDPOINT_EXPECTED]
        assert "opaque" not in str(caught.value)

    def test_get_logger_without_name(self) -> None:
        """Test get_logger without name returns main logger."""
        with patch.object(CanfarLogger, "logger", new_callable=Mock) as mock_logger:
            result = get_logger()
            assert result is mock_logger

    def test_get_logger_with_name(self) -> None:
        """Test get_logger with name returns child logger."""
        with patch(
            "canfar.utils.logging._canfar_logger.get_child_logger"
        ) as mock_get_child:
            get_logger("test.module")
            mock_get_child.assert_called_once_with("test.module")

    def test_set_log_level_calls_global_logger(self) -> None:
        """Test that set_log_level calls the global logger."""
        with patch("canfar.utils.logging._canfar_logger.set_level") as mock_set_level:
            set_log_level(logging.WARNING)
            mock_set_level.assert_called_once_with(logging.WARNING)

    def test_enable_debug_calls_global_logger(self) -> None:
        """Test that enable_debug calls the global logger."""
        with patch(
            "canfar.utils.logging._canfar_logger.enable_debug_mode"
        ) as mock_enable_debug:
            enable_debug()
            mock_enable_debug.assert_called_once()


class TestConstants:
    """Test module constants."""

    def test_config_paths(self) -> None:
        """Test that config paths are correctly defined."""
        assert Path.home() / ".canfar" == CONFIG_DIR
        assert CONFIG_PATH == CONFIG_DIR / "config.yaml"
        assert LOGFILE_PATH == CONFIG_DIR / "client.log"

    def test_logger_name(self) -> None:
        """Test logger name constant."""
        assert LOGGER_NAME == "canfar"

    def test_log_level_constant(self) -> None:
        """Test log level constant."""
        assert LOG_LEVEL == 10  # DEBUG level

    def test_format_constants(self) -> None:
        """Test format string constants."""
        assert "%(asctime)s" in FORMAT
        assert "%(name)s" in FORMAT
        assert "%(levelname)s" in FORMAT
        assert "%(funcName)s" in FORMAT
        assert "%(lineno)d" in FORMAT
        assert "%(message)s" in FORMAT
        assert RICH_FORMAT == "%(message)s"

    def test_file_rotation_constants(self) -> None:
        """Test file rotation constants."""
        assert MAX_LOGFILE_SIZE == 10 * 1024 * 1024  # 10MB
        assert MAX_LOGFILE_COUNT == 10


class TestLoggingIntegration:
    """Integration tests for logging functionality."""

    @pytest.fixture
    def temp_log_dir(self) -> Generator[Path]:
        """Create a temporary directory for log files."""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield Path(temp_dir)

    def test_actual_logging_output(self, temp_log_dir: Path) -> None:
        """Test that actual log messages are written correctly."""
        log_file = temp_log_dir / "integration_test.log"

        # Create a fresh logger instance
        logger = CanfarLogger()

        try:
            with patch("canfar.utils.logging.LOGFILE_PATH", log_file):
                logger.configure(loglevel=logging.DEBUG, filelog=True)

            # Log some messages
            test_logger = logger.logger
            test_logger.debug("Debug message")
            test_logger.info("Info message")
            test_logger.warning("Warning message")
            test_logger.error("Error message")

            # Force flush handlers
            for handler in test_logger.handlers:
                handler.flush()

            # Check file content
            assert log_file.exists()
            content = log_file.read_text()
            assert "Debug message" in content
            assert "Info message" in content
            assert "Warning message" in content
            assert "Error message" in content

        finally:
            logger._cleanup_handlers()  # noqa: SLF001

    def test_json_lines_rotate_with_a_test_only_small_size(
        self,
        temp_log_dir: Path,
    ) -> None:
        """The stdlib rotating handler preserves JSON Lines across rollover."""
        log_file = temp_log_dir / "rotating.jsonl"
        logger = CanfarLogger()

        try:
            with patch("canfar.utils.logging.MAX_LOGFILE_SIZE", 256):
                logger.configure(loglevel=logging.INFO, log_file=log_file)
            for index in range(8):
                logger.logger.info("rotation-event-%d %s", index, "x" * 80)
            for handler in logger.logger.handlers:
                handler.flush()

            files = sorted(temp_log_dir.glob("rotating.jsonl*"))
            assert log_file in files
            assert temp_log_dir / "rotating.jsonl.1" in files
            events = [
                json.loads(line)
                for path in files
                for line in path.read_text(encoding="utf-8").splitlines()
            ]
            assert events
            assert all(
                set(event) == {"timestamp", "level", "logger", "message"}
                for event in events
            )
            assert all(
                event["message"].startswith("rotation-event-") for event in events
            )
        finally:
            logger._cleanup_handlers()  # noqa: SLF001

    def test_child_logger_inheritance(self) -> None:
        """Test that child loggers inherit configuration from parent."""
        logger = CanfarLogger()

        try:
            logger.configure(loglevel=logging.WARNING)

            # Get child logger
            child = logger.get_child_logger("test.module")

            # Child should inherit level from parent
            assert child.getEffectiveLevel() == logging.WARNING

        finally:
            logger._cleanup_handlers()  # noqa: SLF001

    def test_log_level_filtering(self, temp_log_dir: Path) -> None:
        """Test that log level filtering works correctly."""
        log_file = temp_log_dir / "level_test.log"

        logger = CanfarLogger()

        try:
            with patch("canfar.utils.logging.LOGFILE_PATH", log_file):
                logger.configure(loglevel=logging.WARNING, filelog=True)

            test_logger = logger.logger
            test_logger.debug("Debug message - should not appear")
            test_logger.info("Info message - should not appear")
            test_logger.warning("Warning message - should appear")
            test_logger.error("Error message - should appear")

            # Force flush
            for handler in test_logger.handlers:
                handler.flush()

            content = log_file.read_text()
            assert "Debug message" not in content
            assert "Info message" not in content
            assert "Warning message" in content
            assert "Error message" in content

        finally:
            logger._cleanup_handlers()  # noqa: SLF001

    def test_exception_logging(self, temp_log_dir: Path) -> None:
        """Test that exceptions are logged correctly."""
        log_file = temp_log_dir / "exception_test.log"

        logger = CanfarLogger()

        try:
            with patch("canfar.utils.logging.LOGFILE_PATH", log_file):
                logger.configure(loglevel=logging.DEBUG, filelog=True)

            test_logger = logger.logger

            def _raise_test_exception() -> None:
                msg = "Test exception"
                raise ValueError(msg)

            try:
                _raise_test_exception()
            except ValueError:
                test_logger.exception("An error occurred")

            # Force flush
            for handler in test_logger.handlers:
                handler.flush()

            content = log_file.read_text()
            assert "An error occurred" in content
            assert "ValueError: Test exception" in content
            assert "Traceback" in content

        finally:
            logger._cleanup_handlers()  # noqa: SLF001

    def test_public_runtime_writes_secret_safe_json_lines_and_stderr(
        self,
        temp_log_dir: Path,
        capsys: pytest.CaptureFixture[str],
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """One public event is safe, correlated, and parseable in both sinks."""
        log_file = temp_log_dir / "events.jsonl"
        secrets = {
            "access": "access-jsonl-sentinel-01",
            "refresh": "refresh-jsonl-sentinel-02",
            "client_secret": "client-secret-jsonl-sentinel-03",
            "password": "password-jsonl-sentinel-04",
            "cookie": "cookie-jsonl-sentinel-05",
            "certificate": "certificate-jsonl-sentinel-06",
            "private_key": "private-key-jsonl-sentinel-07",
            "pem": "pem-jsonl-sentinel-08",
        }
        message = "\n".join(
            (
                "unicode café 🍁",
                f"Authorization: Bearer {secrets['access']}",
                f"client_secret={secrets['client_secret']}",
                f"password={secrets['password']}",
                f"Cookie: session={secrets['cookie']}",
                f"certificate={secrets['certificate']}",
                f"private_key={secrets['private_key']}",
                f"pem={secrets['pem']}",
            )
        )
        monkeypatch.delenv(_OTLP_ENDPOINT_ENV_VAR, raising=False)

        try:
            configure_logging(loglevel="DEBUG", log_file=log_file)
            logger = get_logger("jsonl")
            try:
                _raise_secret_error(secrets["refresh"])
            except RuntimeError:
                logger.exception(
                    message,
                    extra={
                        "event_code": "logging.contract",
                        "request_id": "request-123",
                        "trace_id": "trace-456",
                        "span_id": "span-789",
                    },
                )
            for handler in get_logger().handlers:
                handler.flush()

            raw = log_file.read_text(encoding="utf-8")
            lines = raw.splitlines()
            events = [json.loads(line) for line in lines]
            assert len(events) == 1
            event = events[0]
            assert set(event) == {
                "timestamp",
                "level",
                "logger",
                "message",
                "event_code",
                "request_id",
                "trace_id",
                "span_id",
                "exception",
            }
            assert re.fullmatch(
                r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{3}Z",
                event["timestamp"],
            )
            assert event["level"] == "ERROR"
            assert event["logger"] == "canfar.jsonl"
            assert event["message"].startswith("unicode café 🍁")
            assert event["event_code"] == "logging.contract"
            assert event["request_id"] == "request-123"
            assert event["trace_id"] == "trace-456"
            assert event["span_id"] == "span-789"
            assert "Traceback" in event["exception"]
            assert len(lines) == 1
            assert "\\n" in raw

            stderr = capsys.readouterr().err
            assert "unicode café 🍁" in stderr
            output = stderr + raw
            assert "<redacted>" in output
            assert all(secret not in output for secret in secrets.values())
        finally:
            for handler in get_logger().handlers[:]:
                handler.close()
                get_logger().removeHandler(handler)

    def test_json_lines_omit_non_string_correlation_values(
        self,
        temp_log_dir: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Nested correlation data cannot violate the flat redacted schema."""
        log_file = temp_log_dir / "flat.jsonl"
        secret = "nested-correlation-secret-sentinel"
        monkeypatch.delenv(_OTLP_ENDPOINT_ENV_VAR, raising=False)

        try:
            configure_logging(loglevel="INFO", log_file=log_file)
            get_logger("jsonl").info(
                "flat-event",
                extra={"request_id": {"password": secret}},
            )
            for handler in get_logger().handlers:
                handler.flush()

            raw = log_file.read_text(encoding="utf-8")
            event = json.loads(raw)
            assert "request_id" not in event
            assert secret not in raw
        finally:
            for handler in get_logger().handlers[:]:
                handler.close()
                get_logger().removeHandler(handler)

    def test_all_handlers_redact_sensitive_messages_and_exceptions(
        self,
        temp_log_dir: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Console and current file logs share one secret-redaction policy."""
        log_file = temp_log_dir / "redacted.log"
        secrets = {
            "access": "access-sentinel-11",
            "refresh": "refresh-sentinel-12",
            "client_secret": "client-secret-sentinel-13",
            "password": "password-sentinel-14",
            "cookie": "cookie-sentinel-15",
            "certificate": "certificate-sentinel-16",
            "x509": "x509-sentinel-17",
            _PEM_VALUE_FIELD: "private-key-sentinel-18",
            "pem": "pem-sentinel-19",
            "extra": "extra-sentinel-20",
            "extra_access": "extra-access-sentinel-21",
            "extra_cookie": "extra-cookie-sentinel-22",
            "basic": "basic-sentinel-23",
            "digest": "digest-sentinel-24",
            "proxy": "proxy-sentinel-25",
            "cookie_second": "cookie-second-sentinel-26",
            "unterminated_pem": "unterminated-pem-sentinel-27",
            "credential": "credential-sentinel-28",
            _SERVICE_VALUE_FIELD: "api-key-sentinel-29",
            "secret": "generic-secret-sentinel-30",
            "passphrase": "passphrase-sentinel-31",
            "pwd": "pwd-sentinel-32",
        }
        pem_kind = "PRIVATE"
        pem_kind += " KEY"
        pem_begin = f"-----BEGIN {pem_kind}-----"
        pem_end = f"-----END {pem_kind}-----"
        message = "\n".join(
            (
                f"Authorization: Bearer {secrets['access']}",
                f"Authorization: Basic {secrets['basic']}",
                f'Authorization: Digest response="{secrets["digest"]}"',
                f"Proxy-Authorization: Basic {secrets['proxy']}",
                (
                    f"Cookie: first={secrets['cookie']}; "
                    f"second={secrets['cookie_second']}"
                ),
                f"access_token={secrets['access']}",
                f"refresh_token={secrets['refresh']}",
                f"client_secret={secrets['client_secret']}",
                f"password={secrets['password']}",
                f"credential={secrets['credential']}",
                f"{_SERVICE_VALUE_FIELD}={secrets[_SERVICE_VALUE_FIELD]}",
                f"secret={secrets['secret']}",
                f"passphrase={secrets['passphrase']}",
                f"pwd={secrets['pwd']}",
                f"certificate={secrets['certificate']}",
                f"x509={secrets['x509']}",
                f"{_PEM_VALUE_FIELD}={secrets[_PEM_VALUE_FIELD]}",
                (f"{pem_begin}\n{secrets['pem']}\n{pem_end}"),
                (f"{pem_begin}\n{secrets['unterminated_pem']}"),
            )
        )
        logger = CanfarLogger()

        try:
            with (
                patch("canfar.utils.logging.LOGFILE_PATH", log_file),
                patch(
                    "canfar.utils.logging.FORMAT",
                    (f"{FORMAT} - %(provider_detail)s - %(access_token)s - %(cookie)s"),
                ),
            ):
                logger.configure(loglevel=logging.DEBUG, filelog=True)

            logger.logger.error(
                "unsafe message: %s",
                message,
                extra={
                    "provider_detail": f"password={secrets['extra']}",
                    "access_token": secrets["extra_access"],
                    "cookie": secrets["extra_cookie"],
                },
            )
            try:
                _raise_secret_error(secrets["refresh"])
            except RuntimeError:
                logger.logger.exception(
                    "unsafe exception client_secret=%s",
                    secrets["client_secret"],
                    extra={
                        "provider_detail": f"password={secrets['extra']}",
                        "access_token": secrets["extra_access"],
                        "cookie": secrets["extra_cookie"],
                    },
                )

            for handler in logger.logger.handlers:
                handler.flush()

            output = capsys.readouterr().err + log_file.read_text()
            assert "<redacted>" in output
            assert all(secret not in output for secret in secrets.values())
        finally:
            logger._cleanup_handlers()  # noqa: SLF001

    def test_concurrent_logging(self, temp_log_dir: Path) -> None:
        """Test that concurrent logging works correctly."""
        log_file = temp_log_dir / "concurrent_test.log"

        logger = CanfarLogger()

        try:
            with patch("canfar.utils.logging.LOGFILE_PATH", log_file):
                logger.configure(loglevel=logging.INFO, filelog=True)

            test_logger = logger.logger

            def log_messages(thread_id: int) -> None:
                for i in range(10):
                    test_logger.info("Thread %d - Message %d", thread_id, i)

            # Create multiple threads
            threads = [
                threading.Thread(target=log_messages, args=(i,)) for i in range(3)
            ]

            for thread in threads:
                thread.start()

            for thread in threads:
                thread.join()

            # Force flush
            for handler in test_logger.handlers:
                handler.flush()

            content = log_file.read_text()
            lines = content.strip().split("\n")

            # Should have 30 log messages (3 threads x 10 messages)
            message_lines = [
                line for line in lines if "Thread" in line and "Message" in line
            ]
            assert len(message_lines) == 30

        finally:
            logger._cleanup_handlers()  # noqa: SLF001


class TestErrorHandling:
    """Test error handling in logging configuration."""

    @pytest.fixture
    def temp_log_dir(self) -> Generator[Path]:
        """Create a temporary directory for log files."""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield Path(temp_dir)

    def test_invalid_log_level_string(self) -> None:
        """Test handling of invalid log level string."""
        logger = CanfarLogger()

        try:
            with pytest.raises(AttributeError):
                logger.configure(loglevel="INVALID_LEVEL")
        finally:
            logger._cleanup_handlers()  # noqa: SLF001

    @pytest.mark.parametrize("failure", ["write", "rollover"])
    def test_runtime_file_failure_disables_only_that_sink_and_warns_once(
        self,
        temp_log_dir: Path,
        capsys: pytest.CaptureFixture[str],
        failure: str,
    ) -> None:
        """Write and rollover errors disable the file sink without recursion."""
        logger = CanfarLogger()
        warning_writer = Mock()
        logger.configure(
            loglevel=logging.CRITICAL,
            log_file=temp_log_dir / f"{failure}.jsonl",
            warning_writer=warning_writer,
        )
        handler = logger._file_handler  # noqa: SLF001
        assert handler is not None

        try:
            with ExitStack() as stack:
                if failure == "write":
                    failing_call = stack.enter_context(
                        patch(
                            "logging.FileHandler.emit",
                            side_effect=OSError("synthetic write failure"),
                        )
                    )
                else:
                    stack.enter_context(
                        patch.object(handler, "shouldRollover", return_value=True)
                    )
                    failing_call = stack.enter_context(
                        patch.object(
                            handler,
                            "doRollover",
                            side_effect=OSError("synthetic rollover failure"),
                        )
                    )

                logger.logger.critical("critical-event-one")
                logger.logger.critical("critical-event-two")

            stderr = capsys.readouterr().err
            assert failing_call.call_count == 1
            assert stderr.count("critical-event-one") == 1
            assert stderr.count("critical-event-two") == 1
            assert ErrorCode.LOGGING_FILE_SINK_UNAVAILABLE.value not in stderr
            warning_writer.assert_called_once()
            assert (
                warning_writer.call_args.args[0].code
                == ErrorCode.LOGGING_FILE_SINK_UNAVAILABLE.value
            )
        finally:
            logger._cleanup_handlers()  # noqa: SLF001

    def test_cleanup_with_no_handlers(self) -> None:
        """Test cleanup when no handlers exist."""
        logger = CanfarLogger()

        # Should not raise an exception
        logger._cleanup_handlers()  # noqa: SLF001

        assert logger._rich_handler is None  # noqa: SLF001
        assert logger._file_handler is None  # noqa: SLF001
