"""Module to manage the directories for exported files."""

from pathlib import Path

from custom_logging import CustomLogger


# Set up logging
logger = CustomLogger.get_logger(__name__)

class DirManager:
    """Class to manage directories and files in the data vault."""

    def __init__(self) -> None:
        """Initialize the class with the base directory for exported files."""
        self.export_base_dir = r'./exported_files'
        self.res_dir = r'./res'

    @staticmethod
    def _create_dir(path: Path) -> Path:
        """Helper method to create a directory if it doesn't exist.

        Args:
            path (Path): The path to the directory.

        Returns:
            str: The path to the directory.
        """
        if not Path.exists(path):
            Path(path).mkdir(parents=True, exist_ok=True)
        return path

    def json_files_dir(self) -> Path:
        """Create a new directory to store json files.

        Returns:
            Path: The path to the new directory.
        """
        return self._create_dir(Path(self.export_base_dir) / 'json_files')

    def log_files_dir(self) -> Path:
        """Create a new directory to store log files.

        Returns:
            Path: The path to the new directory.
        """
        return self._create_dir(Path(self.export_base_dir) / 'log_files')

    def csv_files_dir(self) -> Path:
        """Create a new directory to store csv files.

        Returns:
            Path: The path to the new directory.
        """
        return self._create_dir(Path(self.export_base_dir) / 'csv_files')
