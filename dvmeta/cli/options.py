"""Typer options with types and defaults for the CLI application."""

import typer

from dvmeta.cli.validation import validate_version_type
from dvmeta.models.log_level import LogLevel


class TyperOptions:
    """Helper class for Typer options with types and defaults."""

    auth: str = typer.Option(
        None,
        '--auth',
        '-a',
        help='Authentication token to access the dataverse repository. The environment variable API_TOKEN will always override this option.',  # noqa: E501
        hide_input=True,
        envvar='API_TOKEN',
    )
    report: bool = typer.Option(True, '--report/--no-report', '-r', help='Output summary report file of the crawl.')
    collection_alias: str = typer.Option(
        ...,
        '--collection_alias',
        '-c',
        help='Name of the collection to crawl',
        allow_dash=True,
        prompt_required=True,
    )
    version: str = typer.Option(
        'latest',
        '--version',
        '-v',
        help=(
            'The dataset version to crawl. Options are:'
            '  "draft" - the draft version, if any'
            '  "latest" - either a draft (if exists) or the latest published version'
            '  "latest-published" - the latest published version'
            '  "x.y" - a specific version, where x is the major version number and y is the minor version number'
            '  "x" - same as "x.0"'
        ),
        prompt_required=False,
        callback=validate_version_type,
    )
    debug_log: bool = typer.Option(
        False,
        '--debug-log',
        '-debug',
        help='Enable debug logging to a file. This will create a log file in the logs directory ',
    )
    log_level: LogLevel = typer.Option(
        None,
        '--log-level',
        help=f'The logging level for console and file output. Options are: {", ".join(LogLevel.__members__.keys())}. Defaults to LOG_LEVEL in .env, else INFO.',  # noqa: E501
    )
    metadata_source: str = typer.Option(
        None,
        '--metadata-source',
        '-m',
        help='The source of the metadata to crawl. This option can be used to exclude harvested datasets (that does not host directly on the installation).',  # noqa: E501
    )
    publication_status: str = typer.Option(
        None,
        '--publication-status',
        '-ps',
        help='The publication status of the datasets to crawl. Common values are "Published", "Draft", "Unpublished", "Deaccessioned". Depends on the installation.',  # noqa: E501
    )
    semaphore_limit: int = typer.Option(
        5,
        '--semaphore-limit',
        '-sl',
        help='The maximum number of concurrent tasks when crawling datasets. Please adjust this number based on the expected load on the dataverse repository. Might need some trial and error to find the optimal number.',  # noqa: E501
    )
    timestamp_enabled: bool = typer.Option(
        True,
        '--timestamp/--no-timestamp',
        '-ts',
        help='Whether to include timestamp in the exported JSON filenames.',
    )
