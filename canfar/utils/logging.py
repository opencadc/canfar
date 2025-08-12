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

import logging
import logging.handlers
import threading
from pathlib import Path

from rich.console import Console
from rich.logging import RichHandler
from rich.traceback import install as install_rich_traceback

CONFIG_DIR: Path = Path.home() / ".canfar"
CONFIG_PATH: Path = CONFIG_DIR / "config.yaml"
LOGFILE_PATH: Path = CONFIG_DIR / "client.log"
LOG_LEVEL: int = 10
# Library logger name - all modules should use this as root
LOGGER_NAME = "canfar"
# Thread lock for configuration safety
_LOCK = threading.Lock()

# Default configuration
FORMAT = (
    "%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s"
)
RICH_FORMAT = "%(message)s"
MAX_LOGFILE_SIZE = 10 * 1024 * 1024  # 10MB
MAX_LOGFILE_COUNT = 10

# Install rich traceback handling globally for better error display
install_rich_traceback(show_locals=False, suppress=[])


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
        self._console = Console()
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
    ) -> None:
        """Configure the CANFAR logger with Rich support and optional file logging.

        Args:
            loglevel (int | str, optional): Logging level. Defaults to logging.INFO.
            filelog (bool, optional): Whether to enable file logging. Defaults to False.
        """
        with _LOCK:
            if self._configured:
                # Allow reconfiguration but clean up existing handlers
                self._cleanup_handlers()
            # Convert string level to int if needed
            if isinstance(loglevel, str):
                loglevel = getattr(logging, loglevel.upper())
            # Configure the main logger
            logger = self.logger
            logger.setLevel(loglevel)
            # Use provided console or create new one
            console = self._console
            # Setup Rich console handler
            self._rich_handler = RichHandler(
                console=console,
                show_path=True,
                show_time=True,
                enable_link_path=True,
                rich_tracebacks=True,
                tracebacks_show_locals=True,
            )
            self._rich_handler.setLevel(loglevel)

            # Rich handler uses a simpler format since Rich adds the styling
            formatter = logging.Formatter(RICH_FORMAT)
            self._rich_handler.setFormatter(formatter)
            logger.addHandler(self._rich_handler)

            # Setup file logging if requested
            if filelog:
                self._setup_file_logging(
                    LOGFILE_PATH,
                    MAX_LOGFILE_SIZE,
                    MAX_LOGFILE_COUNT,
                    int(loglevel),
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
    ) -> None:
        """Setup rotating file handler for logging."""
        # Ensure log directory exists
        logfile.parent.mkdir(parents=True, exist_ok=True)

        # Use RotatingFileHandler for automatic log rotation
        self._file_handler = logging.handlers.RotatingFileHandler(
            filename=logfile,
            maxBytes=size,
            backupCount=count,
            encoding="utf-8",
        )
        self._file_handler.setLevel(level)
        # File handler uses detailed format
        file_formatter = logging.Formatter(FORMAT)
        self._file_handler.setFormatter(file_formatter)
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
def configure_logging(loglevel: int | str, filelog: bool = False) -> None:
    """Configure CANFAR logging. See CanfarLogger.configure for parameters."""
    _canfar_logger.configure(loglevel=loglevel, filelog=filelog)


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
