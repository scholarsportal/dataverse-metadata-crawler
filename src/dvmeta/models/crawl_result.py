"""Data model for the crawl result."""

from dataclasses import dataclass, field


@dataclass
class CrawlResult:
    """Collected data returned from the crawling pipeline."""

    meta_dict: dict = field(default_factory=dict)
    dataset_records: list[dict] = field(default_factory=list)
    permission_dict: dict = field(default_factory=dict)
    export_data: list = field(default_factory=list)
    failed_metadata_uris: dict = field(default_factory=dict)
    pid_dict_dd: dict = field(default_factory=dict)
    collections_tree_flatten: dict = field(default_factory=dict)
    dv_dict: dict = field(default_factory=dict)
