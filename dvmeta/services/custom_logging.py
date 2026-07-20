"""Setup custom logging configuration with Loguru."""

from pathlib import Path

from loguru import logger

from dvmeta.models.log_level import LogLevel


def setup_logging(log_file_dir: Path | None = None, log_level: str = LogLevel.INFO) -> None:
    """Set up logging configuration for Loguru.

    Parameters
    ----------
    log_file_dir : Path | None, optional
        Directory to save log files. If None, logs will only be printed to console. By default, None.
    log_level : str, optional
        Logging level for both console and file handlers. By default, LogLevel.INFO.
    """
    # Remove existing handlers
    logger.remove()

    # Add the console log format with color
    console_log_format: str = (
        "<green>[{time:YYYY-MM-DD HH:mm:ss}]</green> - <level>{message}</level>"
    )

    # Add the console handler
    logger.add(
        sink=lambda msg: print(msg, end=""),
        colorize=True,
        level=log_level,
        format=console_log_format,
    )

    # Add the file handler if log_file_dir is provided
    if log_file_dir:
        log_file_path = Path(log_file_dir, "debug.log")
        log_file_path.parent.mkdir(parents=True, exist_ok=True)
        logger.add(
            sink=str(log_file_path),
            level=log_level,
            format="{time:YYYY-MM-DD HH:mm:ss} - {name} - {level} - {message}",
            encoding="utf-8",
        )
