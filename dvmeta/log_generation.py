"""Module to generate log file."""
from pathlib import Path

import utils
from custom_logging import CustomLogger
from dirmanager import DirManager
from jinja2 import Template
from timestamp import Timestamp
from utils import count_files_size


# Initialize the logger
logger = CustomLogger().get_logger(__name__)


def write_to_log(  # noqa:  PLR0913
    config: dict,
    start_time_display: str,
    end_time_display: str,
    elapsed_time: str,
    meta_dict: dict,
    collections_tree_flatten: dict,
    failed_metadata_ids: dict,
    pid_dict_dd: dict,
    json_file_checksum_dict: dict,
) -> None:
    """Write the crawl log to a file.

    Args:
        config (dict): Configuration dictionary
        start_time_display (str): Start time of the crawl
        end_time_display (str): End time of the crawl
        elapsed_time (str): Elapsed time of the crawl
        meta_dict (dict): Metadata dictionary
        collections_tree_flatten (dict): Flattened collections tree
        failed_metadata_ids (dict): Dictionary of failed metadata IDs
        pid_dict_dd (dict): Dictionary of deacessioned/draft datasets
        json_file_checksum_dict (dict): Dictionary of JSON file checksums

    Returns:
        str: Path to the log file
    """
    report = Template(read_template())
    rendered = report.render(config=config,
                             start_time_display=start_time_display,
                             end_time_display=end_time_display,
                             elapsed_time=elapsed_time,
                             meta_dict=utils.count_key(meta_dict),
                             collections_tree_flatten=utils.count_key(collections_tree_flatten),
                             pid_dict_dd=utils.count_key(pid_dict_dd),
                             failed_metadata_ids=utils.count_key(failed_metadata_ids),
                             file_num=count_files_size(meta_dict)[0],
                             file_size=count_files_size(meta_dict)[1],
                             json_file_checksum_dict=json_file_checksum_dict
                             )

    log_file_path = f'{DirManager().log_files_dir()}/log_{Timestamp().get_file_timestamp()}.txt'

    with Path(log_file_path).open('w', encoding='utf-8') as file:
        file.write(rendered)

    return logger.print(f'The crawl log is saved at: {log_file_path}')


def read_template() -> str:
    """Read the log template file from res directory.

    Returns:
        str: Content of the template file as string

    Raises:
        FileNotFoundError: If template file doesn't exist
    """
    with Path('res/log_template.txt').open(encoding='utf-8') as file:
        return file.read()
