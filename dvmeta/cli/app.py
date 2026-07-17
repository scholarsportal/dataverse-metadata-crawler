"""The command-line interface (CLI) application for the Dataverse Metadata Crawler."""

import asyncio
from dataclasses import dataclass
from typing import Any

import typer
from loguru import logger

from dvmeta.cli.options import TyperOptions
from dvmeta.cli.utils import spinner
from dvmeta.cli.validation import validate_connection
from dvmeta.crawler.crawler import MetaDataCrawler
from dvmeta.crawler.utils import get_pids_from_search_response
from dvmeta.crawler.utils import get_start_parameters
from dvmeta.crawler.utils import get_total_count_from_response
from dvmeta.crawler.utils import merge_oaiore_to_meta_dict
from dvmeta.crawler.utils import merge_permission_to_meta_dict
from dvmeta.crawler.utils import parse_search_response
from dvmeta.models.config import Config
from dvmeta.models.crawl_result import CrawlResult
from dvmeta.models.log_level import LogLevel
from dvmeta.models.search_params import DataverseSearchParams
from dvmeta.models.search_params import ItemType
from dvmeta.services.custom_logging import setup_logging
from dvmeta.services.dir_manager import ExportDir
from dvmeta.services.dir_manager import get_dir
from dvmeta.services.exporter import export_json
from dvmeta.services.report_generation import write_to_report
from dvmeta.services.spreadsheet import Spreadsheet
from dvmeta.services.timestamp import Timestamps
from dvmeta.services.timestamp import get_current_time


setup_logging()  # Initialize logging at the module level to ensure it's set up before any commands are run

app = typer.Typer()


@dataclass
class CLIState:
    config: Config | None = None
    timestamps: Timestamps | None = None
    crawler: MetaDataCrawler | None = None
    collections_tree: Any | None = None
    collection_data: Any | None = None
    crawl_result: CrawlResult | None = None
    report: bool = True
    permission: bool = False
    publication_status: str | None = None

    skip_export: bool = False
    auth_status: bool = False

    dataset_records: Any | None = None
    dataset_ids: list[str] | None = None

    timestamps_enabled: bool = True


@app.callback()
def main(  # noqa: PLR0913, PLR0917
    ctx: typer.Context,
    auth: str = TyperOptions.auth,
    report: bool = TyperOptions.report,
    collection_alias: str = TyperOptions.collection_alias,
    version: str = TyperOptions.version,
    debug_log: bool = TyperOptions.debug_log,
    log_level: LogLevel | None = TyperOptions.log_level,
    metadata_source: str = TyperOptions.metadata_source,
    publication_status: str = TyperOptions.publication_status,
    semaphore_limit: int = TyperOptions.semaphore_limit,
    timestamp_enabled: bool = TyperOptions.timestamp_enabled,
) -> None:
    """Step 1: load config and validate inputs. Runs before every subcommand."""
    config = Config()
    log_level = log_level or config.log_level  # CLI flag wins over LOG_LEVEL in .env
    setup_logging(
        get_dir(ExportDir.LOG) if debug_log else None, log_level=log_level
    )  # Reconfigure logging if debug_log is set, otherwise use default configuration

    state = CLIState()
    state.timestamps = Timestamps(start_time=get_current_time())
    state.timestamps_enabled = timestamp_enabled

    config.collection_alias = collection_alias
    config.version = version
    config.api_token = auth if auth else config.api_token
    config.metadata_source = metadata_source
    config.semaphore_limit = semaphore_limit

    state.auth_status = validate_connection(config)
    config.api_token = (
        None if not state.auth_status else config.api_token
    )  # Remove the API token if authentication failed

    state.config = config
    state.report = report
    state.publication_status = publication_status
    state.crawl_result = CrawlResult()
    ctx.obj = state


def get_state(ctx: typer.Context) -> CLIState:
    """Retrieve the CLI state from the Typer context."""
    state = ctx.obj
    if state is None:
        msg = 'CLI state not initialized'
        raise typer.BadParameter(msg)
    return state


@app.command()
def search(ctx: typer.Context) -> None:
    """Search for datasets in the collection."""
    state = get_state(ctx)

    assert state.config is not None
    assert state.crawl_result is not None

    base_search_params = DataverseSearchParams(
        q='*',
        type=[ItemType.DATASET],
        subtree=state.config.collection_alias,
        fq=[
            f'metadataSource:"{state.config.metadata_source}"' if state.config.metadata_source else None,
            f'publicationStatus:"{state.publication_status}"' if state.publication_status else None,
        ],
        show_collections=True,
        query_entities=False,
        show_entity_ids=True,
    )

    with spinner():
        state.crawler = MetaDataCrawler(state.config)

        # First get the total count of the search result
        total_count_rsp = state.crawler.get_search_result(
            base_search_params=base_search_params,
        )

        total_count = get_total_count_from_response(total_count_rsp)

        start_parameters = get_start_parameters(total_count, per_page=1000)

        state.crawl_result.dataset_records = asyncio.run(
            state.crawler.get_dataverse_ds_records_async(start_parameters, search_params=base_search_params)
        )

        state.dataset_ids = parse_search_response(state.crawl_result.dataset_records)

        state.crawl_result.dv_dict = state.crawler.get_dataverse_collection_records()
        logger.info(
            f'Search for datasets in collection "{state.config.collection_alias}" completed. Found {len(state.dataset_ids)} datasets.'  # noqa: E501
        )


@app.command()
def crawl_metadata(ctx: typer.Context) -> None:
    """Crawl dataset metadata."""
    state = get_state(ctx)

    assert state.crawler is not None
    assert state.config is not None

    if state.dataset_ids is None:
        search(ctx)

    with spinner():
        crawler = state.crawler
        dataset_ids = state.dataset_ids
        pids = list(get_pids_from_search_response(state.crawl_result.dataset_records).values())

        async def _fetch_all() -> tuple[dict, dict]:
            return await asyncio.gather(
                crawler.get_dataset_metadata(pids, version=state.config.version),
                crawler.get_oaiore_metadata(pids),
            )

        meta_dict, oaiore_metadata = asyncio.run(_fetch_all())

        # Merge OAI-ORE metadata into the meta_dict
        state.crawl_result.meta_dict = merge_oaiore_to_meta_dict(meta_dict, oaiore_metadata)

        if not state.skip_export:
            export_json(state.crawl_result.meta_dict, export_type='ds_metadata')

        if state.report:
            state.timestamps.end_time = get_current_time()
            write_to_report(state.config, state.timestamps, state.crawl_result)

        logger.info(
            f'Dataset metadata crawl for collection "{state.config.collection_alias}" completed. Crawled {len(state.crawl_result.meta_dict)} datasets.'
        )


@app.command()
def crawl_permission(ctx: typer.Context) -> None:
    """Crawl dataset permissions."""
    state = get_state(ctx)

    if state.dataset_ids is None:
        search(ctx)

    with spinner():
        if not state.auth_status:
            msg = 'API Token authentication failed or not provided. Skipping permission crawl.'
            logger.warning(msg)
            return
        assert state.crawler is not None
        assert state.dataset_ids is not None
        assert state.config is not None
        assert state.crawl_result is not None

        state.crawl_result.permission_dict = asyncio.run(state.crawler.get_dataset_permissions(state.dataset_ids))

        if not state.skip_export:
            export_json(state.crawl_result.permission_dict, export_type='permission')

        logger.info(
            f'Permission metadata for collection "{state.config.collection_alias}" completed. Crawled {len(state.crawl_result.permission_dict)} records.'  # noqa: E501
        )


@app.command()
def export_spreadsheet(ctx: typer.Context) -> None:
    """Export the dataset metadata (and permissions if available) to spreadsheet."""
    state = get_state(ctx)

    with spinner():
        if state.crawl_result is None or state.crawl_result.meta_dict is None:
            crawl_metadata(ctx)

        if state.permission and state.crawl_result.permission_dict is None:
            crawl_permission(ctx)

        assert state.crawl_result is not None
        assert state.crawl_result.meta_dict is not None
        assert state.config is not None

        spreadsheet = Spreadsheet(state.config)
        spreadsheet.make_csv_file(state.crawl_result.meta_dict)


@app.command()
def run_all(ctx: typer.Context) -> None:
    """Run the full crawl process: search -> crawl metadata -> crawl permissions -> export spreadsheet. Export the metadata (with permissions if available) to JSON and spreadsheet."""  # noqa: E501, W505
    state = get_state(ctx)
    state.skip_export = True
    report = state.report
    state.report = False  # Defer report write until the full pipeline completes

    search(ctx)
    crawl_metadata(ctx)
    crawl_permission(ctx)

    assert state.crawl_result is not None
    if state.crawl_result.permission_dict:
        state.crawl_result.meta_dict = merge_permission_to_meta_dict(
            state.crawl_result.meta_dict, state.crawl_result.permission_dict
        )

    export_json(state.crawl_result.meta_dict, export_type='ds_metadata')
    export_spreadsheet(ctx)

    if report:
        assert state.config is not None
        assert state.timestamps is not None
        state.timestamps.end_time = get_current_time()
        write_to_report(state.config, state.timestamps, state.crawl_result)


if __name__ == '__main__':
    app()
