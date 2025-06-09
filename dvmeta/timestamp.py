"""This module contains a class to manage timestamps."""
# ruff: noqa: DTZ005
from datetime import datetime

from custom_logging import CustomLogger


# Initialize the logger
logger = CustomLogger().get_logger(__name__)


class Timestamp:
    """A class to manage timestamps.

    Attributes:
        current_time (datetime): The current time.

    Methods:
        get_current_time: Returns the current time as a datetime object.
        get_display_time: Returns a string representation of the current time.
        get_file_timestamp: Returns a string representation of the current time for use in file names.
    """

    def __init__(self) -> None:
        """Initialize the class with the current time."""
        self.start_time = datetime.now()  # Get the time when the class is initialized
        self.current_time = self.start_time
        self.end_time = None

    @staticmethod
    def get_display_time(time_obj: datetime | None = None) -> str:
        """Returns a string representation of the time in the format: YYYY-MM-DD HH:MM:SS.

        Args:
            time_obj (datetime, optional): Time to format. Defaults to current time.

        Returns:
            str: A string representation of the time.
        """
        if time_obj is None:
            time_obj = datetime.now()
        return time_obj.strftime('%Y-%m-%d %H:%M:%S')

    @staticmethod
    def get_file_timestamp() -> str:
        """Returns a string representation of the current time in the format: YYYYMMDD-HHMMSS.

        Returns:
            str: A string representation of the current time for use in file names
        """
        return datetime.now().strftime('%Y%m%d-%H%M%S')

    def get_end_time(self) -> datetime:
        """Sets and returns the end time if not already set.

        Returns:
            datetime: The end time.
        """
        if self.end_time is None:
            self.end_time = datetime.now()
        return self.end_time

    def get_elapsed_time(self) -> str:
        """Returns the elapsed time since the start time.

        Returns:
            str: The elapsed time in seconds.
        """
        end = self.end_time if self.end_time else datetime.now()
        elapsed_time = end - self.start_time
        return str(elapsed_time)
