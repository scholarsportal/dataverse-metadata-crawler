"""The possible log levels for the application."""

from enum import StrEnum


class LogLevel(StrEnum):
    """Enum for log levels used in the application."""

    TRACE = "TRACE"
    DEBUG = "DEBUG"
    INFO = "INFO"
    SUCCESS = "SUCCESS"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"
