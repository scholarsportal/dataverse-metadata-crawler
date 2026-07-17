"""Module to generate crawl report file."""

from pathlib import Path

from jinja2 import Template
from loguru import logger

from dvmeta.models.config import Config
from dvmeta.models.crawl_result import CrawlResult
from dvmeta.services.dir_manager import ExportDir
from dvmeta.services.dir_manager import get_dir
from dvmeta.services.timestamp import Timestamps
from dvmeta.services.timestamp import get_display_time
from dvmeta.services.timestamp import get_elapsed_time
from dvmeta.services.timestamp import get_file_timestamp
from dvmeta.services.utils import count_key
from dvmeta.services.utils import get_collection_files_count
from dvmeta.services.utils import get_collection_files_size


DEFAULT_REPORT_TEMPLATE: str = """--- Summary ---
Repository base URL: {{ config.base_url }}
Collection Name: {{ crawl_result.dv_dict.data.name }}
Collection Alias: {{ crawl_result.dv_dict.data.alias }}
Collection ID: {{ crawl_result.dv_dict.data.id }}
Dataset Version: {{ config.version }}

Start time: {{ start_time_display }}
End time: {{ end_time_display }}
Execution time: {{ elapsed_time }}

Total number of dataset crawled from the collection: {{ ds_metadata_num }}
Total number of permission metadata crawled from the collection: {{ permission_record_num }}

Total number of files in the collection: {{ file_num }}
Total size of files in the collection: {{ file_size }} bytes

{% if json_file_checksum_dict %}
Files saved:
{% for item in json_file_checksum_dict %}{% if item.path %}
Item type: {{ item.type }}
Item path: {{ item.path }}
Item checksum (SHA-256): {{ item.checksum }}
{% endif %}{% endfor %}
{% endif %}
--- End of Report ---
"""


def write_to_report(  # noqa:  PLR0913
    config: Config,
    timestamps: Timestamps,
    crawl_result: CrawlResult,
) -> None:
    """Write the crawl report to a file.

    Args:
        config (dict): Configuration dictionary
        timestamps (Timestamps): Timestamps object containing start and end times
        crawl_result (CrawlResult): Result object containing all crawled data
    """
    report = Template(read_template())
    rendered = report.render(
        config=config,
        crawl_result=crawl_result,
        start_time_display=get_display_time(timestamps.start_time),
        end_time_display=get_display_time(timestamps.end_time),
        elapsed_time=get_elapsed_time(timestamps.start_time, timestamps.end_time),
        ds_metadata_num=count_key(crawl_result.meta_dict),
        pid_dict_dd=count_key(crawl_result.pid_dict_dd),
        permission_record_num=count_key(crawl_result.permission_dict),
        file_num=get_collection_files_count(crawl_result.meta_dict),
        file_size=get_collection_files_size(crawl_result.meta_dict),
        json_file_checksum_dict=crawl_result.export_data,
    )

    log_file_path = get_dir(ExportDir.LOG) / f'report_{get_file_timestamp()}.txt'

    Path(log_file_path).write_text(rendered, encoding='utf-8')

    logger.info(f'The crawl report is saved at: {log_file_path}')


def read_template(template_path: str | Path = 'res/report_template.txt') -> str:
    """Read the crawl report template file from res directory.

    TODO: allow this to be set in a config file or command line argument.

    Returns:
        str: Content of the template file as string

    Raises:
        FileNotFoundError: If template file doesn't exist
    """
    report_template_path = Path(template_path)

    if not report_template_path.is_file():
        logger.warning(f'Crawl report template file not found at {report_template_path}. Using default template.')
        return DEFAULT_REPORT_TEMPLATE

    return report_template_path.read_text(encoding='utf-8')
