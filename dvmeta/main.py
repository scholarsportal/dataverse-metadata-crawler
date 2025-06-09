"""The command line interface for dvmeta."""
import asyncio

import typer
import utils
from cli_validation import validate_api_token_presence
from cli_validation import validate_basic_input
from cli_validation import validate_collection_data
from cli_validation import validate_collections_tree
from cli_validation import validate_connection
from cli_validation import validate_spreadsheet_option
from cli_validation import validate_version_type
from custom_logging import CustomLogger
from dirmanager import DirManager
from export_manager import ExportManager
from log_generation import write_to_log
from metadatacrawler import MetaDataCrawler
from parsing import Parsing
from spreadsheet import Spreadsheet
from timestamp import Timestamp


app = typer.Typer()


@app.command()
def main(
    auth: str = typer.Option(
        None,
        '--auth',
        '-a',
        help='Authentication token to access the dataverse repository',
        hide_input=True,
        envvar='API_KEY',
    ),
    log: bool = typer.Option(True, '--log/--no-log', '-l', help='Output log file'),
    dvdfds_matadata: bool = typer.Option(
        False, '--dvdfds_metadata', '-d', help='Output JSON file of metadata of dataverse, dataset and datafiles'
    ),
    permission: bool = typer.Option(
        False,
        '--permission',
        '-p',
        help='Output JSON file that stores permission metadata of all datasets in the repository',
    ),
    collection_alias: str = typer.Option(
        ..., '--collection_alias', '-c', help='Name of the collection to crawl', allow_dash=True, prompt_required=True
    ),
    version: str = typer.Option(
        ...,
        '--version',
        '-v',
        help=(
            'The dataset version to crawl. Options are:\n'
            "  'draft' - the draft version, if any\n"
            "  'latest' - either a draft (if exists) or the latest published version\n"
            "  'latest-published' - the latest published version\n"
            "  'x.y' - a specific version, where x is the major version number and y is the minor version number\n"
            "  'x' - same as 'x.0'"
        ),
        prompt_required=True,
        callback=validate_version_type,
    ),
    empty_dv: bool = typer.Option(
        False,
        '--emptydv',
        '-e',
        help='Output JSON file that stores all dataverses that does have contain datasets (but might include child dataverses and their child dataverses might have datasets)',
    ),
    failed: bool = typer.Option(
        False, '--failed', '-f', help='Output JSON file that stores dataverses/datasets failed to be crawled'
    ),
    spreadsheet: bool = typer.Option(
        False, '--spreadsheet', '-s', help='Output a CSV file of the metadata of datasets',
    ),
    debug_log: bool = typer.Option(
        False, '--debug-log', '-debug',
        help='Enable debug logging. This will create a debug log file in the log_files directory.')):
    """A Python CLI tool for extracting and exporting metadata from Dataverse repositories to JSON and CSV formats."""
    # Initialize the custom logger in the cli
    CustomLogger.setup_logging(DirManager().log_files_dir()) if debug_log else CustomLogger.setup_logging()
    logger = CustomLogger.get_logger(__name__)

    # Create a start time stamp
    timestamp = Timestamp()

    # Load the environment variables
    config: dict = utils.load_env()

    config['COLLECTION_ALIAS'] = collection_alias
    config['VERSION'] = version
    config['API_KEY'] = (auth if auth else config['API_KEY'])  # Reassign the API_KEY and replace it specified in the .env file, if provided in the CLI interface

    # Check if -s flag is provided without -d flag
    validate_spreadsheet_option(spreadsheet, dvdfds_matadata)

    # Check if either dvdfds_matadata or permission is provided
    validate_basic_input(dvdfds_matadata, permission)

    # Check if the authentication token is provided if the permission metadata is requested to be crawled
    validate_api_token_presence(permission, config)

    # Check the connection to the dataverse repository
    auth_status = validate_connection(config)
    config['API_KEY'] = None if not auth_status else config['API_KEY']  # Set the API_KEY to None if the connection is not authenticated

    # Initialize the crawler
    metadata_crawler = MetaDataCrawler(config)

    # Crawl the collection tree metadata
    collections_tree = validate_collections_tree(metadata_crawler.get_collections_tree(collection_alias))

    # Add collection id and alias to config
    collection_data = validate_collection_data(collections_tree)

    # Update config with validated collection data
    config = utils.update_config_with_collection_data(config, collection_data)

    # Start the main function
    logger.print('Starting the main crawling function...')

    async def main_crawler():
        # Initialize empty dict and list to store metadata
        permission_dict = {}

        # Initialize the Parsing class
        parsing = Parsing(config, collections_tree)

        logger.print('Getting basic metadata of datasets in across dataverses (incl. all children)...')
        dataverse_contents, failed_dataverse_contents = await metadata_crawler.get_dataverse_contents(parsing.collection_id_list)

        # Add pathIds and path to dataverse_contents from collections_tree_flatten
        dataverse_contents = parsing.add_path_to_dataverse_contents(dataverse_contents)

        # Get URIs in collections_tree_flatten and append them to ds_dict, and return empty dataverse to empty_dv
        empty_dv_dict, ds_dict = parsing.get_pids()

        # Optional arguments
        meta_dict = {}
        failed_metadata_uris = []
        pid_dict_dd = {}

        # Initialize the ExportManager
        export_manager = ExportManager()

        if dvdfds_matadata:
            # Export dataverse_contents
            logger.print('Crawling Representation and File metadata of datasets...')
            pid_list = [item['datasetPersistentId'] for item in ds_dict.values()]
            meta_dict, failed_metadata_uris = await metadata_crawler.get_datasets_meta(pid_list)

            # Replace the key with the Data #! TEMPORARY FIX
            parsing.replace_key_with_dataset_id(meta_dict)

            # Add the path_info to the metadata
            meta_dict, pid_dict_dd = parsing.add_path_info(ds_dict)

            # Remove the deaccessioned/draft datasets from the pid_dict_dd for the failed_metadata_uris
            failed_metadata_uris = parsing.rm_dd_from_failed_uris(failed_metadata_uris, pid_dict_dd)

            # Export the updated pid_dict_dd (Which contains deaccessioned/draft datasets) to a JSON file
            export_manager.export(pid_dict_dd, 'pid_dict_dd')

            if failed:
                export_manager.export(failed_metadata_uris, 'failed_metadata_uris')

        if permission:
            logger.print('Crawling Permission metadata of datasets...')
            ds_id_list = [item['datasetId'] for item in ds_dict.values()]
            permission_dict, failed_permission_uris = await (metadata_crawler.get_datasets_permissions(ds_id_list))

            if not dvdfds_matadata:  # Delay the merging of permission metadata until the representation/file metadata is crawled
                # Export the permission metadata to a JSON file
                export_manager.export(permission_dict, 'permission_dict')
                logger.print(
                    f'Successfully crawled permission metadata for {utils.count_key(permission_dict)} datasets in total.'
                )

                # Export the pid_dict to a JSON file, if dfdfds_metadata is not provided
                export_manager.export(ds_dict, 'pid_dict')

        # Combine the metadata and permission metadata, if both are provided
        # Else write dummy permission metadata to the metadata
        meta_dict = parsing.add_permission_info(meta_dict, permission_dict)

        if meta_dict:
            # Export the metadata to a JSON file
            export_manager.export(meta_dict, 'ds_metadata')
            logger.print(f'Successfully crawled {utils.count_key(meta_dict)} metadata of dataset representation and file in total.')

        if empty_dv:
            export_manager.export(empty_dv_dict, 'empty_dv')

        if spreadsheet:
            # Export the metadata to a CSV file
            csv_file_path, csv_file_checksum = Spreadsheet(config).make_csv_file(meta_dict)
            export_manager.add_spreadsheet_record(csv_file_path, csv_file_checksum)

        return meta_dict, export_manager.get_tracking_data(), failed_metadata_uris, pid_dict_dd, parsing.collections_tree_flatten

    meta_dict, export_manager_data, failed_metadata_uris, pid_dict_dd, collections_tree_flatten = asyncio.run(main_crawler())

    if log:
        # Write to log
        write_to_log(config,
                     timestamp.get_display_time(timestamp.start_time),
                     timestamp.get_display_time(timestamp.end_time),
                     timestamp.get_elapsed_time(),
                     meta_dict,
                     collections_tree_flatten,
                     failed_metadata_uris,
                     pid_dict_dd,
                     export_manager_data)

    logger.print('✅ Crawling process completed successfully.')

if __name__ == '__main__':
    app()
