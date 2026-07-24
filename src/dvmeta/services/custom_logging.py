"""Setup custom logging configuration with Loguru."""

from pathlib import Path

from loguru import logger

from dvmeta.models.log_level import LogLevel


def setup_logging(log_file_dir: Path | None = None, log_level: str = LogLevel.INFO) -> None:
    """Set up logging configuration for Loguru.

    Args:
        log_file_dir: Directory to write a debug.log file to, by default None.
        log_level: The logging level for console and file output, by default LogLevel.INFO.
    """
    logger.remove()

    console_log_format: str = (
        "<green>[{time:YYYY-MM-DD HH:mm:ss}]</green> - <level>{message}</level>"
    )

    logger.add(
        sink=lambda msg: print(msg, end=""),
        colorize=True,
        level=log_level,
        format=console_log_format,
    )

    if log_file_dir:
        log_file_path = Path(log_file_dir, "debug.log")
        log_file_path.parent.mkdir(parents=True, exist_ok=True)
        logger.add(
            sink=str(log_file_path),
            level=log_level,
            format="{time:YYYY-MM-DD HH:mm:ss} - {name} - {level} - {message}",
            encoding="utf-8",
        )
