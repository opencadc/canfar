"""Functional tests for stdlib CANFAR logging."""

from __future__ import annotations

import json
import logging
from contextlib import ExitStack
from logging.handlers import RotatingFileHandler
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


def _emit_exception_log(logger: logging.Logger) -> None:
    """Emit one exception record for the JSONL formatter contract."""
    try:
        json.loads("not-json")
    except json.JSONDecodeError:
        logger.exception("operation failed")


def _clear_handlers() -> None:
    """Release handlers through the stdlib logger boundary."""
    logger = logging.getLogger(LOGGER_NAME)
    for handler in logger.handlers[:]:
        handler.close()
        logger.removeHandler(handler)


@pytest.fixture
def canfar_logger() -> Generator[CanfarLogger]:
    """Fresh CanfarLogger cleaned after each test."""
    logger = CanfarLogger()
    _clear_handlers()
    yield logger
    _clear_handlers()


def test_configure_rich_stderr_defaults(canfar_logger: CanfarLogger) -> None:
    """Default configure attaches Rich stderr logging and stops propagation."""
    canfar_logger.configure()

    logger = canfar_logger.logger
    rich_handlers = [h for h in logger.handlers if isinstance(h, RichHandler)]
    assert logger.level == logging.INFO
    assert len(rich_handlers) == 1
    assert not logger.propagate


def test_reconfigure_replaces_handlers(canfar_logger: CanfarLogger) -> None:
    """Reconfiguration replaces previous handlers."""
    canfar_logger.configure(loglevel=logging.INFO)
    first = next(
        handler
        for handler in canfar_logger.logger.handlers
        if isinstance(handler, RichHandler)
    )
    canfar_logger.configure(loglevel=logging.DEBUG)
    second = next(
        handler
        for handler in canfar_logger.logger.handlers
        if isinstance(handler, RichHandler)
    )
    assert second is not first
    assert second in canfar_logger.logger.handlers
    assert first not in canfar_logger.logger.handlers


def test_separate_logger_lifecycles_do_not_accumulate_handlers(
    tmp_path: Path,
) -> None:
    """Repeated application lifecycles leave one stderr/file sink pair."""
    first = CanfarLogger()
    second = CanfarLogger()
    try:
        first.configure(loglevel=logging.INFO, log_file=tmp_path / "first.jsonl")
        second.configure(loglevel=logging.INFO, log_file=tmp_path / "second.jsonl")

        logger = logging.getLogger(LOGGER_NAME)
        assert len([h for h in logger.handlers if isinstance(h, RichHandler)]) == 1
        files = [h for h in logger.handlers if isinstance(h, RotatingFileHandler)]
        assert len(files) == 1
        assert files[0].baseFilename.endswith("second.jsonl")
    finally:
        _clear_handlers()


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
        get_logger("jsonl").info("hello")
        for handler in get_logger().handlers:
            handler.flush()

        event = json.loads(log_file.read_text(encoding="utf-8"))
        assert event["level"] == "INFO"
        assert event["logger"] == "canfar.jsonl"
        assert event["message"] == "hello"
        assert set(event.keys()) == {"timestamp", "level", "logger", "message"}
    finally:
        _clear_handlers()


def test_jsonl_file_sink_includes_exception_text(tmp_path: Path) -> None:
    """Exception diagnostics remain available as one escaped JSONL field."""
    log_file = tmp_path / "exception.jsonl"
    try:
        configure_logging(loglevel="INFO", log_file=log_file)
        _emit_exception_log(get_logger("jsonl"))
        for handler in get_logger().handlers:
            handler.flush()

        event = json.loads(log_file.read_text(encoding="utf-8"))
        assert "exception" in event
        assert "JSONDecodeError" in event["exception"]
    finally:
        _clear_handlers()


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
        _clear_handlers()


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
    handlers = [
        candidate
        for candidate in logger.logger.handlers
        if isinstance(candidate, RotatingFileHandler)
    ]
    assert len(handlers) == 1
    handler = handlers[0]
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
        _clear_handlers()
