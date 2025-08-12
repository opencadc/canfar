"""Comprehensive tests for the logging module."""

from __future__ import annotations

import logging
import tempfile
import threading
from pathlib import Path
from typing import TYPE_CHECKING
from unittest.mock import Mock, patch

import pytest
from rich.logging import RichHandler

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
    configure_logging,
    enable_debug,
    get_logger,
    set_log_level,
)

if TYPE_CHECKING:
    from collections.abc import Generator


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

        # Check formatter
        formatter = file_handler.formatter
        assert hasattr(formatter, "_fmt")
        assert formatter._fmt == FORMAT  # type: ignore[attr-defined] # noqa: SLF001


class TestConvenienceFunctions:
    """Test the convenience functions."""

    def test_configure_logging_calls_global_logger(self) -> None:
        """Test that configure_logging calls the global logger."""
        with patch("canfar.utils.logging._canfar_logger.configure") as mock_configure:
            configure_logging(loglevel=logging.DEBUG, filelog=True)
            mock_configure.assert_called_once_with(loglevel=logging.DEBUG, filelog=True)

    def test_get_logger_without_name(self) -> None:
        """Test get_logger without name returns main logger."""
        with patch.object(
            CanfarLogger, "logger", new_callable=lambda: Mock()
        ) as mock_logger:
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

    def test_file_logging_permission_error(self, temp_log_dir: Path) -> None:
        """Test handling of file permission errors."""
        # Create a directory where we can't write
        readonly_dir = temp_log_dir / "readonly"
        readonly_dir.mkdir()
        readonly_dir.chmod(0o444)  # Read-only

        log_file = readonly_dir / "test.log"

        logger = CanfarLogger()

        try:
            with (
                patch("canfar.utils.logging.LOGFILE_PATH", log_file),
                pytest.raises(PermissionError),
            ):
                # Currently the logging module raises PermissionError
                # This test documents the current behavior
                logger.configure(filelog=True)

        finally:
            logger._cleanup_handlers()  # noqa: SLF001
            # Restore permissions for cleanup
            readonly_dir.chmod(0o755)

    def test_cleanup_with_no_handlers(self) -> None:
        """Test cleanup when no handlers exist."""
        logger = CanfarLogger()

        # Should not raise an exception
        logger._cleanup_handlers()  # noqa: SLF001

        assert logger._rich_handler is None  # noqa: SLF001
        assert logger._file_handler is None  # noqa: SLF001
