"""Module to manage the directories for exported files."""

from enum import StrEnum
from pathlib import Path


EXPORT_BASE_DIR = Path('./exported_files')
RES_DIR = Path('./res')


class ExportDir(StrEnum):
    """Enum to represent the different types of export directories."""

    JSON = 'json_files'
    LOG = 'log_files'
    CSV = 'csv_files'


def get_dir(name: ExportDir) -> Path:
    """Return the path to the requested export directory, creating it if it doesn't exist.

    Args:
        name (ExportDir): The name of the directory to retrieve.

    Returns:
        Path: The path to the requested directory.
    """
    path = EXPORT_BASE_DIR / name
    path.mkdir(parents=True, exist_ok=True)
    return path
