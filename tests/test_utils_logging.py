"""Comprehensive tests for the logging module."""

from __future__ import annotations

import json
import logging
import os
import re
from contextlib import ExitStack
from typing import TYPE_CHECKING
from unittest.mock import Mock, patch

import pytest
from rich.logging import RichHandler

from canfar.errors import ErrorCode
from canfar.utils.logging import (
    LOGGER_NAME,
    MAX_LOGFILE_COUNT,
    MAX_LOGFILE_SIZE,
    CanfarLogger,
    InvalidLoggingEnvironmentError,
    LoggingLevel,
    configure_logging,
    get_logger,
)

if TYPE_CHECKING:
    from collections.abc import Generator
    from pathlib import Path


def _raise_secret_error(secret: str) -> None:
    """Raise a deterministic exception containing the supplied secret."""
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

    def test_configure_basic_setup(self, canfar_logger: CanfarLogger) -> None:
        """Test basic configuration with default parameters."""
        canfar_logger.configure()

        logger = canfar_logger.logger
        assert logger.level == logging.INFO
        assert len(logger.handlers) == 1
        assert isinstance(logger.handlers[0], RichHandler)
        assert not logger.propagate
        assert canfar_logger._configured  # noqa: SLF001

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
            result = configure_logging(loglevel=logging.DEBUG)

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

    def test_get_logger_returns_root_and_prefixed_child_names(self) -> None:
        """Public logger lookup returns canonical CANFAR logger names."""
        assert get_logger().name == "canfar"
        assert get_logger("test.module").name == "canfar.test.module"


class TestConstants:
    """Test module constants."""

    def test_logger_name(self) -> None:
        """Test logger name constant."""
        assert LOGGER_NAME == "canfar"

    def test_file_rotation_constants(self) -> None:
        """Test file rotation constants."""
        assert MAX_LOGFILE_SIZE == 10 * 1024 * 1024  # 10MB
        assert MAX_LOGFILE_COUNT == 10


class TestLoggingIntegration:
    """Integration tests for logging functionality."""

    def test_json_lines_rotate_with_a_test_only_small_size(
        self,
        tmp_path: Path,
    ) -> None:
        """The stdlib rotating handler preserves JSON Lines across rollover."""
        log_file = tmp_path / "rotating.jsonl"
        logger = CanfarLogger()

        try:
            with patch("canfar.utils.logging.MAX_LOGFILE_SIZE", 256):
                logger.configure(loglevel=logging.INFO, log_file=log_file)
            for index in range(8):
                logger.logger.info("rotation-event-%d %s", index, "x" * 80)
            for handler in logger.logger.handlers:
                handler.flush()

            files = sorted(tmp_path.glob("rotating.jsonl*"))
            assert log_file in files
            assert tmp_path / "rotating.jsonl.1" in files
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

    def test_public_runtime_writes_secret_safe_json_lines_and_stderr(
        self,
        tmp_path: Path,
        capsys: pytest.CaptureFixture[str],
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """One public event is safe, correlated, and parseable in both sinks."""
        log_file = tmp_path / "events.jsonl"
        sentinel = "jsonl-secret-sentinel-01"
        message = f"unicode café 🍁\nAuthorization: Bearer {sentinel}"
        monkeypatch.delenv(_OTLP_ENDPOINT_ENV_VAR, raising=False)

        try:
            configure_logging(loglevel="DEBUG", log_file=log_file)
            logger = get_logger("jsonl")
            try:
                _raise_secret_error(sentinel)
            except RuntimeError:
                # Intentional clear-text input for the redaction contract below.
                logger.exception(  # codeql[py/clear-text-logging-sensitive-data]
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
            assert sentinel not in output
        finally:
            for handler in get_logger().handlers[:]:
                handler.close()
                get_logger().removeHandler(handler)

    def test_json_lines_omit_non_string_correlation_values(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Nested correlation data cannot violate the flat redacted schema."""
        log_file = tmp_path / "flat.jsonl"
        sentinel = "nested-correlation-secret-sentinel"
        monkeypatch.delenv(_OTLP_ENDPOINT_ENV_VAR, raising=False)

        try:
            configure_logging(loglevel="INFO", log_file=log_file)
            # Nested non-string correlation values must be omitted, not serialized.
            get_logger("jsonl").info(  # codeql[py/clear-text-logging-sensitive-data]
                "flat-event",
                extra={"request_id": {"nested": sentinel}},
            )
            for handler in get_logger().handlers:
                handler.flush()

            raw = log_file.read_text(encoding="utf-8")
            event = json.loads(raw)
            assert "request_id" not in event
            assert sentinel not in raw
        finally:
            for handler in get_logger().handlers[:]:
                handler.close()
                get_logger().removeHandler(handler)

    def test_all_handlers_redact_sensitive_messages_and_exceptions(
        self,
        tmp_path: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Console and current file logs share one secret-redaction policy."""
        log_file = tmp_path / "redacted.log"
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
                f"password={secrets['extra']}",
                f"access_token={secrets['extra_access']}",
                f"cookie={secrets['extra_cookie']}",
                f"certificate={secrets['certificate']}",
                f"x509={secrets['x509']}",
                f"{_PEM_VALUE_FIELD}={secrets[_PEM_VALUE_FIELD]}",
                (f"{pem_begin}\n{secrets['pem']}\n{pem_end}"),
                (f"{pem_begin}\n{secrets['unterminated_pem']}"),
            )
        )
        logger = CanfarLogger()

        try:
            logger.configure(loglevel=logging.DEBUG, log_file=log_file)

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


class TestErrorHandling:
    """Test error handling in logging configuration."""

    @pytest.mark.parametrize("failure", ["write", "rollover"])
    def test_runtime_file_failure_disables_only_that_sink_and_warns_once(
        self,
        tmp_path: Path,
        capsys: pytest.CaptureFixture[str],
        failure: str,
    ) -> None:
        """Write and rollover errors disable the file sink without recursion."""
        logger = CanfarLogger()
        warning_writer = Mock()
        logger.configure(
            loglevel=logging.CRITICAL,
            log_file=tmp_path / f"{failure}.jsonl",
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
