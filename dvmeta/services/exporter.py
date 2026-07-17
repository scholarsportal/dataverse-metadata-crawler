"""Module to export metadata dictionaries to JSON files."""

from pathlib import Path

import orjson
from loguru import logger

from dvmeta.services.dir_manager import ExportDir
from dvmeta.services.dir_manager import get_dir
from dvmeta.services.timestamp import get_file_timestamp
from dvmeta.services.utils import gen_checksum


def export_json(data: dict, export_type: str, timestamp_enabled: bool = True) -> tuple[Path | None, str | None]:
    """Export data to a timestamped JSON file and log the result.

    Args:
        data: The data to export
        export_type: Type identifier, used as the filename prefix
        timestamp_enabled: Whether to include a timestamp in the filename
    Returns:
        Tuple of (json_path, checksum), or (None, None) if data is empty
    """
    file_name = f'{export_type}_{get_file_timestamp()}.json' if timestamp_enabled else f'{export_type}.json'
    json_file_path = get_dir(ExportDir.JSON) / file_name

    if isinstance(data, dict) and data:
        json_file_path.write_bytes(orjson.dumps(data, option=orjson.OPT_INDENT_2 | orjson.OPT_NON_STR_KEYS))
        checksum = gen_checksum(json_file_path)
        logger.info(f'Exported {json_file_path.name} to json file: {json_file_path}\nChecksum (SHA-256): {checksum}')
        return json_file_path, checksum

    logger.warning(f'{json_file_path.name} is empty, no json file is created.')
    return None, None
