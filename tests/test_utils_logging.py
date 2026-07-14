"""Functional tests for stdlib CANFAR logging."""

from __future__ import annotations

import json
import logging
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
    safe_url,
)

if TYPE_CHECKING:
    from collections.abc import Generator
    from pathlib import Path


@pytest.fixture
def canfar_logger() -> Generator[CanfarLogger]:
    """Fresh CanfarLogger cleaned after each test."""
    logger = CanfarLogger()
    yield logger
    logger._cleanup_handlers()  # noqa: SLF001
    logger._configured = False  # noqa: SLF001


def test_configure_rich_stderr_defaults(canfar_logger: CanfarLogger) -> None:
    """Default configure attaches one Rich stderr handler and stops propagation."""
    canfar_logger.configure()

    logger = canfar_logger.logger
    assert logger.level == logging.INFO
    assert len(logger.handlers) == 1
    assert isinstance(logger.handlers[0], RichHandler)
    assert not logger.propagate
    assert canfar_logger._configured  # noqa: SLF001


def test_reconfigure_replaces_handlers(canfar_logger: CanfarLogger) -> None:
    """Reconfiguration replaces previous handlers."""
    canfar_logger.configure(loglevel=logging.INFO)
    first = canfar_logger.logger.handlers[0]
    canfar_logger.configure(loglevel=logging.DEBUG)
    assert len(canfar_logger.logger.handlers) == 1
    assert canfar_logger.logger.handlers[0] is not first


@pytest.mark.parametrize(
    ("kwargs", "expected"),
    [
        ({"loglevel": "DEBUG"}, LoggingLevel.DEBUG),
        ({"verbosity": 2}, LoggingLevel.WARNING),
        ({}, LoggingLevel.CRITICAL),
    ],
)
def test_configure_logging_resolves_precedence(
    monkeypatch: pytest.MonkeyPatch,
    kwargs: dict[str, object],
    expected: LoggingLevel,
) -> None:
    """CLI level beats verbosity; unset falls back to packaged critical."""
    monkeypatch.delenv("CANFAR_LOGLEVEL", raising=False)
    with patch("canfar.utils.logging._canfar_logger.configure") as configure:
        assert configure_logging(**kwargs) is expected  # type: ignore[arg-type]
        configure.assert_called_once()


def test_invalid_canfar_loglevel_fails_fast(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Invalid CANFAR_LOGLEVEL raises a structured environment error."""
    monkeypatch.setenv("CANFAR_LOGLEVEL", "chatty")
    with pytest.raises(InvalidLoggingEnvironmentError) as caught:
        configure_logging()
    assert caught.value.error.env_var == "CANFAR_LOGLEVEL"
    assert caught.value.error.provided_value == "chatty"


def test_get_logger_names() -> None:
    """Logger lookup returns the canfar root and prefixed children."""
    assert get_logger().name == LOGGER_NAME
    assert get_logger("sessions").name == "canfar.sessions"
    assert MAX_LOGFILE_SIZE == 10 * 1024 * 1024
    assert MAX_LOGFILE_COUNT == 10


def test_safe_url_strips_userinfo_query_and_fragment() -> None:
    """Error helpers can share a URL sanitizer without logging secrets."""
    assert (
        safe_url("https://user:pass@example.com/path?token=secret#frag")
        == "https://example.com/path"
    )


def test_jsonl_file_sink_writes_flat_events(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Public configure_logging writes one JSON object per line to --log-file."""
    log_file = tmp_path / "events.jsonl"
    monkeypatch.delenv("CANFAR_LOGLEVEL", raising=False)
    try:
        configure_logging(loglevel="INFO", log_file=log_file)
        get_logger("jsonl").info(
            "hello",
            extra={
                "event_code": "logging.contract",
                "request_id": "request-123",
                "trace_id": "trace-456",
                "span_id": "span-789",
            },
        )
        for handler in get_logger().handlers:
            handler.flush()

        event = json.loads(log_file.read_text(encoding="utf-8"))
        assert event["level"] == "INFO"
        assert event["logger"] == "canfar.jsonl"
        assert event["message"] == "hello"
        assert event["event_code"] == "logging.contract"
        assert event["request_id"] == "request-123"
        assert event["trace_id"] == "trace-456"
        assert event["span_id"] == "span-789"
        assert "timestamp" in event
    finally:
        for handler in get_logger().handlers[:]:
            handler.close()
            get_logger().removeHandler(handler)


def test_jsonl_omits_non_string_correlation_fields(tmp_path: Path) -> None:
    """Non-string correlation extras stay out of the flat JSONL schema."""
    log_file = tmp_path / "flat.jsonl"
    logger = CanfarLogger()
    try:
        logger.configure(loglevel=logging.INFO, log_file=log_file)
        logger.logger.info("flat-event", extra={"request_id": {"nested": "x"}})
        for handler in logger.logger.handlers:
            handler.flush()
        event = json.loads(log_file.read_text(encoding="utf-8"))
        assert "request_id" not in event
    finally:
        logger._cleanup_handlers()  # noqa: SLF001


def test_jsonl_rotates_with_small_max_size(tmp_path: Path) -> None:
    """Rotating handler keeps JSON Lines across rollover."""
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
    finally:
        logger._cleanup_handlers()  # noqa: SLF001


@pytest.mark.parametrize("failure", ["write", "rollover"])
def test_file_sink_failure_keeps_stderr_and_warns_once(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    failure: str,
) -> None:
    """Write/rollover errors disable only the file sink."""
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
                failing = stack.enter_context(
                    patch(
                        "logging.FileHandler.emit",
                        side_effect=OSError("synthetic write failure"),
                    )
                )
            else:
                stack.enter_context(
                    patch.object(handler, "shouldRollover", return_value=True)
                )
                failing = stack.enter_context(
                    patch.object(
                        handler,
                        "doRollover",
                        side_effect=OSError("synthetic rollover failure"),
                    )
                )
            logger.logger.critical("critical-event-one")
            logger.logger.critical("critical-event-two")

        stderr = capsys.readouterr().err
        assert failing.call_count == 1
        assert stderr.count("critical-event-one") == 1
        assert stderr.count("critical-event-two") == 1
        warning_writer.assert_called_once()
        assert (
            warning_writer.call_args.args[0].code
            == ErrorCode.LOGGING_FILE_SINK_UNAVAILABLE.value
        )
    finally:
        logger._cleanup_handlers()  # noqa: SLF001
