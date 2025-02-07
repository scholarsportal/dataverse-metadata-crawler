"""The command line interface for dvmeta."""
import asyncio
import sys

import func
import typer
import utils
from log_generation import write_to_log
from metadatacrawler import MetaDataCrawler
from spreadsheet import Spreadsheet
from typing_extensions import Annotated


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
        callback=func.version_type,
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
        False, '--spreadsheet', '-s', help='Output a CSV file of the metadata of datasets'
    ),
):
    """A Python CLI tool for extracting and exporting metadata from Dataverse repositories to JSON and CSV formats."""
    # Load the environment variables
    config: dict = func.load_env()

    config['COLLECTION_ALIAS'] = collection_alias
    config['VERSION'] = version
    config['API_KEY'] = (auth if auth else config['API_KEY'])  # Reassign the API_KEY and replace it specified in the .env file, if provided in the CLI interface

    # Check if -s flag is provided without -d flag
    func.validate_spreadsheet(spreadsheet, dvdfds_matadata)

    # Start time
    start_time_obj, start_time_display = utils.Timestamp().get_current_time(), utils.Timestamp().get_display_time()
    print(f'Start time: {start_time_display}\n')

    # Check if either dvdfds_matadata or permission is provided
    if not dvdfds_matadata and not permission:
        print(
            'Please provide the type of metadata to crawl. Use -d or/and -p flag for crawling metadata of datasets or permission metadata, respectively.'
        )
        sys.exit(1)

    # Check if the authentication token is provided if the permission metadata is requested to be crawled
    if permission and config.get('API_KEY') is None or config.get('API_KEY') == 'None':
        print('Error: Crawling permission metadata requires API Token. Please provide the API Token.Exiting...')
        sys.exit(1)

    # Check the connection to the dataverse repository
    connection_status, auth_status = func.check_connection(config)
    if not connection_status:
        sys.exit(1)
    if not auth_status:
        config['API_KEY'] = None
        if permission:
            print('[WARNING]: Crawling permission metadata requires valid API Token. The script will skip crawling permission metadata\n')
            permission = False

    # Initialize the crawler
    metadata_crawler = MetaDataCrawler(config)

    # Crawl the collection tree metadata
    response = metadata_crawler.get_collections_tree(collection_alias)
    if response is None:
        print('Error: Failed to retrieve collections tree. The API request returned None.')
        sys.exit(1)

    collections_tree = response.json()

    # Add collection id and alias to config
    if collections_tree['status'] == 'OK':
        config['COLLECTION_ID'], config['COLLECTION_ALIAS'], config['COLLECTION_NAME'] = (
            collections_tree['data']['id'],
            collections_tree['data']['alias'],
            collections_tree['data']['name'],
        )

    else:
        print(f"Collection alias '{collection_alias}' is not found in the repository. Exiting...")
        sys.exit(1)

    # Start the main function
    print('Starting the main crawling function...\n')

    async def main_crawler():
        # Initialize empty dict and list to store metadata
        ds_dict = {'datasetPersistentId': []}
        failed_metadata_ids = []
        json_file_checksum_dict = []
        permission_dict = {}

        # Flatten the collections tree
        collections_tree_flatten = utils.flatten_collection(collections_tree)
        print('Flattened the collections tree...\n')

        # Add collection id to collection_id_list
        collection_id_list = [item['id'] for item in collections_tree_flatten.values()]

        # Add root collection id to collection_id_list
        collection_id_list.append(config['COLLECTION_ID'])

        print('Getting basic metadata of datasets in across dataverses (incl. all children)...\n')
        dataverse_contents, failed_dataverse_contents = await metadata_crawler.get_dataverse_contents(collection_id_list)

        # Add pathIds and path to dataverse_contents from collections_tree_flatten
        dataverse_contents = func.add_path_to_dataverse_contents(dataverse_contents, collections_tree_flatten)

        # Get URIs in collections_tree_flatten and append them to ds_dict, and return empty dataverse to empty_dv
        empty_dv_dict, ds_dict = func.get_pids(dataverse_contents, config)

        # Optional arguments
        meta_dict = {}
        failed_metadata_uris = []
        pid_dict_dd = {}
        if dvdfds_matadata:
            # Export dataverse_contents
            print('Crawling Representation and File metadata of datasets...\n')
            pid_list = [item['datasetPersistentId'] for item in ds_dict.values()]
            meta_dict, failed_metadata_uris = await metadata_crawler.get_datasets_meta(pid_list)

            # Replace the key with the Data #TEMPORARY FIX
            meta_dict = func.replace_key_with_dataset_id(meta_dict)

            # Add the path_info to the metadata
            meta_dict, pid_dict_dd = func.add_path_info(meta_dict, ds_dict)

            # Remove the deaccessioned/draft datasets from the pid_dict_dd for the failed_metadata_uris
            failed_metadata_uris = func.rm_dd_from_failed_uris(failed_metadata_uris, pid_dict_dd)

            # Export the updated pid_dict_dd (Which contains deaccessioned/draft datasets) to a JSON file
            pid_dict_json, pid_dict_checksum = utils.orjson_export(pid_dict_dd, 'pid_dict_dd')
            json_file_checksum_dict.append(
                {
                    'type': 'Hierarchical Information of Datasets(deaccessioned/draft)',
                    'path': pid_dict_json,
                    'checksum': pid_dict_checksum,
                }
            )

            if failed:
                failed_metadata_uris_json, failed_metadata_uris_checksum = utils.orjson_export(
                    failed_metadata_uris, 'failed_metadata_uris'
                )
                json_file_checksum_dict.append(
                    {
                        'type': 'PIDs of Datasets Failed to be crawled (Representation & File)',
                        'path': failed_metadata_uris_json,
                        'checksum': failed_metadata_uris_checksum,
                    }
                )

        if permission:
            print('\nCrawling Permission metadata of datasets...\n')
            ds_id_list = [item['datasetId'] for item in ds_dict.values()]
            permission_dict, failed_permission_uris = await (metadata_crawler.get_datasets_permissions(ds_id_list))

            if not dvdfds_matadata:  # Delay the merging of permission metadata until the representation/file metadata is crawled
                # Export the permission metadata to a JSON file
                permission_json_file_path, permission_json_checksum = utils.orjson_export(
                    permission_dict, 'permission_dict'
                )
                json_file_checksum_dict.append(
                    {
                        'type': 'Dataset Metadata (Permission)',
                        'path': permission_json_file_path,
                        'checksum': permission_json_checksum,
                    }
                )
                print(
                    f'Successfully crawled permission metadata for {utils.count_key(permission_dict)} datasets in total.\n'
                )

                # Export the pid_dict to a JSON file, if dfdfds_metadata is not provided
                pid_dict_json, pid_dict_checksum = utils.orjson_export(ds_dict, 'pid_dict')
                json_file_checksum_dict.append(
                    {
                        'type': 'Hierarchical Information of Datasets',
                        'path': pid_dict_json,
                        'checksum': pid_dict_checksum,
                    }
                )

        # Combine the metadata and permission metadata, if both are provided
        # Else write dummy permission metadata to the metadata
        meta_dict = func.add_permission_info(meta_dict, permission_dict if isinstance(permission_dict, dict) and permission_dict else None)

        if meta_dict:
            # Export the metadata to a JSON file
            meta_json_file_path, meta_json_checksum = utils.orjson_export(meta_dict, 'ds_metadata')
            json_file_checksum_dict.append(
                {
                    'type': 'Dataset Metadata (Representation, File & Permission)',
                    'path': meta_json_file_path,
                    'checksum': meta_json_checksum,
                }
            )
            print(f'Successfully crawled {utils.count_key(meta_dict)} metadata of dataset representation and file in total.\n')

        if empty_dv:
            empty_dv_json, empty_dv_checksum = utils.orjson_export(empty_dv_dict, 'empty_dv')
            json_file_checksum_dict.append(
                {'type': 'Empty Dataverses', 'path': empty_dv_json, 'checksum': empty_dv_checksum}
            )

        if spreadsheet:
            # Export the metadata to a CSV file
            csv_file_path, csv_file_checksum = Spreadsheet(config).make_csv_file(meta_dict)
            json_file_checksum_dict.append(
                {'type': 'Dataset Metadata CSV', 'path': csv_file_path, 'checksum': csv_file_checksum}
            )

        return meta_dict, json_file_checksum_dict, failed_metadata_uris, pid_dict_dd, collections_tree_flatten

    meta_dict, json_file_checksum_dict, failed_metadata_uris, pid_dict_dd, collections_tree_flatten = asyncio.run(main_crawler())

    # End time
    end_time_obj, end_time_display = utils.Timestamp().get_current_time(), utils.Timestamp().get_display_time()
    print(f'End time: {end_time_display}\n')

    # Print the elapsed time for the crawling process
    elapsed_time = end_time_obj - start_time_obj
    print(f'Elapsed time: {elapsed_time}\n')

    if log:
        # Write to log
        write_to_log(config,
                     start_time_display,
                     end_time_display,
                     elapsed_time,
                     meta_dict,
                     collections_tree_flatten,
                     failed_metadata_uris,
                     pid_dict_dd,
                     json_file_checksum_dict)

    print('✅ Crawling process completed successfully.\n')

if __name__ == '__main__':
    app()
