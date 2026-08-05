"""Module to export metadata dictionaries to JSON files."""

import orjson
from loguru import logger

from dvmeta.services.dir_manager import ExportDir, get_dir
from dvmeta.services.timestamp import get_file_timestamp
from dvmeta.services.utils import gen_checksum


def export_json(
    data: dict, directory: ExportDir, name: str, *, timestamp_enabled: bool = True
) -> None:
    """Export data to a json file.

    Args:
        data (dict): The data to export.
        directory (ExportDir): The directory to export the file to.
        name (str): The name of the file to export.
        timestamp_enabled (bool): Whether to include a timestamp in the filename, by default True.
    """
    if not isinstance(data, dict) or not data:
        logger.warning(f"{name} content is empty, no json file is created.")
        return

    file_name = f"{name}_{get_file_timestamp()}.json" if timestamp_enabled else f"{name}.json"
    json_file_path = get_dir(directory) / file_name
    json_file_path.write_bytes(
        orjson.dumps(data, option=orjson.OPT_INDENT_2 | orjson.OPT_NON_STR_KEYS)
    )
    logger.info(
        f"Exported {json_file_path.name} to json file: {json_file_path}. Checksum (SHA-256): {gen_checksum(json_file_path)}"
    )
