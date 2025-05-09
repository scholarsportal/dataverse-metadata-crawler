"""This module defines a custom logger for the package."""
# ruff: noqa: ANN401
import logging
from pathlib import Path
from typing import Any

from rich.logging import RichHandler


class CustomLogger:
    """Custom logger class that extends the standard logging module."""
    # Custom log level between INFO (20) and WARNING (30)
    PRINT_LEVEL = 25

    # Setup done flag to prevent multiple initializations
    _setup_done = False

    @staticmethod
    def setup_logging(log_file_dir: Path | None = None, log_level=logging.INFO) -> None:
        """Setup the root logger configuration once for the entire application."""
        if CustomLogger._setup_done:
            return

        # Add the custom level name
        logging.addLevelName(CustomLogger.PRINT_LEVEL, 'PRINT')

        # Define a custom print method for the Logger class
        def print_log(self, message: Any, *args, **kwargs):  # noqa
            """Log a message with the custom PRINT level."""
            if self.isEnabledFor(CustomLogger.PRINT_LEVEL):
                self._log(CustomLogger.PRINT_LEVEL, message, args, **kwargs)

        # Attach the method to Logger class
        logging.Logger.print = print_log  # type: ignore

        # Configure root logger
        root_logger = logging.getLogger()
        root_logger.setLevel(logging.NOTSET)

        # Remove any existing handlers to prevent duplicates
        for handler in root_logger.handlers[:]:
            root_logger.removeHandler(handler)

        # Create formatter
        console_formatter = logging.Formatter(fmt='%(asctime)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
        file_formatter = logging.Formatter(fmt='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                                      datefmt='%Y-%m-%d %H:%M:%S')

        # Create console handler using the RichHandler
        console_handler = RichHandler(
            level=CustomLogger.PRINT_LEVEL,
            rich_tracebacks=True,
            show_time=True,
            show_path=False,
            show_level=False,
            omit_repeated_times=False,
            markup=True,
            log_time_format='[%Y-%m-%d %H:%M:%S]'
        )

        root_logger.addHandler(console_handler)

        # Create file handler if log_file_dir is provided
        if log_file_dir:
            log_file_path = Path(log_file_dir, 'debug.log')
            log_file_path.parent.mkdir(parents=True, exist_ok=True)
            file_handler = logging.FileHandler(filename=str(log_file_path),
                                              mode='a', encoding='utf-8')
            file_handler.setFormatter(file_formatter)
            file_handler.setLevel(logging.NOTSET)
            root_logger.addHandler(file_handler)

        CustomLogger._setup_done = True

    @staticmethod
    def get_logger(name: str) -> 'CustomLoggerWrapper':
        """Get a logger with the specified name."""
        return CustomLoggerWrapper(logging.getLogger(name))


class CustomLoggerWrapper:
    """Wrapper around logger to provide clean interface."""

    def __init__(self, logger: logging.Logger) -> None:
        """Initialize the logger wrapper with a specific logger."""
        self.logger = logger

    def print(self, message: Any) -> None:
        """Log a message with the custom PRINT level."""
        self.logger.print(message)  # type: ignore

    def info(self, message: Any) -> None:
        """Log a message with INFO level."""
        self.logger.info(message)

    def warning(self, message: Any) -> None:
        """Log a message with WARNING level."""
        self.logger.warning(message)

    def error(self, message: Any) -> None:
        """Log a message with ERROR level."""
        self.logger.error(message)

    def critical(self, message: Any) -> None:
        """Log a message with CRITICAL level."""
        self.logger.critical(message)

    def debug(self, message: Any) -> None:
        """Log a message with DEBUG level."""
        self.logger.debug(message)
