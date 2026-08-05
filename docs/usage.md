# CLI

Crawler that crawls metadata of datasets in a Dataverse collection and exports the metadata to JSON and spreadsheet.

## Usage

```console
$ [OPTIONS] COMMAND [ARGS]...
```

## Global Options

| Option | Value / Type | Description |
| --- | --- | --- |
| -a, --auth | <str> | Authentication token to access the dataverse repository. The environment variable API_TOKEN will always override this option. [env var: API_TOKEN] |
| -r, --report / --no-report |  | Output summary report file of the crawl. [default: report] |
| -c, --collection_alias | <str> | Name of the collection to crawl [required] |
| -v, --version | <str> | The dataset version to crawl. Options are: &quot;draft&quot; - the draft version, if any &quot;latest&quot; - either a draft (if exists) or the latest published version &quot;latest-published&quot; - the latest published version &quot;x.y&quot; - a specific version, where x is the major version number and y is the minor version number &quot;x&quot; - same as &quot;x.0&quot; Note that the version apply only to individual datasets. The publication-status option can be used to filter datasets by their publication status. For example, if you want the get all published datasets but with the draft version, you can use --publication-status Published --version draft. But this option will also return datasets that is published, but does not have a draft version. [default: latest] |
| -debug, --debug-log |  | Enable debug logging to a file. This will create a log file in the logs directory |
| --log-level | <TRACE\|DEBUG\|INFO\|SUCCESS\|WARNING\|ERROR\|CRITICAL> | The logging level for console and file output. Options are: TRACE, DEBUG, INFO, SUCCESS, WARNING, ERROR, CRITICAL. Defaults to LOG_LEVEL in .env, else INFO. |
| -m, --metadata-source | <str> | The source of the metadata to crawl. This option can be used to exclude harvested datasets (that does not host directly on the installation). |
| -ps, --publication-status | <Draft\|Published\|Unpublished> | The publication status of the datasets to look for. Common values are &quot;Published&quot;, &quot;Draft&quot;, &quot;Unpublished&quot;, &quot;Deaccessioned&quot;. Depends on the installation. |
| -sl, --semaphore-limit | <int> | The maximum number of concurrent tasks when crawling datasets. Please adjust this number based on the expected load on the dataverse repository. Might need some trial and error to find the optimal number. [default: 5] |
| -ts, --timestamp / --no-timestamp |  | Whether to include timestamp in the exported JSON filenames. [default: timestamp] |
| -p, --permission / --no-permission |  | Whether to include permission metadata in the exported JSON files. This will make additional API calls to fetch the permission metadata for each dataset. [default: no-permission] |
| --install-completion |  | Install completion for the current shell. |
| --show-completion |  | Show completion for the current shell, to copy it or customize the installation. |
| --help |  | Show this message and exit. |

## Commands

| Command | Description |
| --- | --- |
| search | Search for datasets in the collection. |
| crawl-metadata | Crawl dataset metadata. |
| crawl-permission | Crawl dataset permissions. |
| export-spreadsheet | Export the dataset metadata (and... |
| run-all | Run the full crawl process: search, crawl... |

## `search`

Search for datasets in the collection.

```console
$ search [OPTIONS]
```

| Option | Value / Type | Description |
| --- | --- | --- |
| --help |  | Show this message and exit. |

## `crawl-metadata`

Crawl dataset metadata.

```console
$ crawl-metadata [OPTIONS]
```

| Option | Value / Type | Description |
| --- | --- | --- |
| --help |  | Show this message and exit. |

## `crawl-permission`

Crawl dataset permissions.

```console
$ crawl-permission [OPTIONS]
```

| Option | Value / Type | Description |
| --- | --- | --- |
| --help |  | Show this message and exit. |

## `export-spreadsheet`

Export the dataset metadata (and permissions if available) to spreadsheet.

```console
$ export-spreadsheet [OPTIONS]
```

| Option | Value / Type | Description |
| --- | --- | --- |
| --help |  | Show this message and exit. |

## `run-all`

Run the full crawl process: search, crawl metadata, crawl permissions, export spreadsheet.

Export the metadata (with permissions if available) to JSON and spreadsheet.

```console
$ run-all [OPTIONS]
```

| Option | Value / Type | Description |
| --- | --- | --- |
| --help |  | Show this message and exit. |
