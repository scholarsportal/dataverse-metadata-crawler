"""Test services/spreadsheet.py."""

import csv
from pathlib import Path

import pytest

from dvmeta.models.config import Config
from dvmeta.services import spreadsheet as spreadsheet_module
from dvmeta.services.spreadsheet import Spreadsheet

CITATION_BLOCK = {
    "displayName": "Citation Metadata",
    "name": "citation",
    "fields": [{"typeName": "title", "multiple": False, "typeClass": "primitive", "value": "Test Dataset"}],
}

VERSION_FIELDS = {
    "id": 999,
    "datasetId": 42,
    "versionState": "RELEASED",
    "datasetPersistentId": "doi:10.5072/FK2/ABCDEF",
    "datasetType": "dataset",
    "storageIdentifier": "file://10.5072/FK2/ABCDEF",
    "internalVersionNumber": 1,
    "latestVersionPublishingState": "RELEASED",
    "lastUpdateTime": "2024-01-01T00:00:00Z",
    "createTime": "2024-01-01T00:00:00Z",
    "fileAccessRequest": False,
    "metadataBlocks": {"citation": CITATION_BLOCK},
    "files": [],
}

# GET /api/datasets/:id -> data wraps the version under "latestVersion".
WRAPPED = {
    "status": "OK",
    "data": {
        "id": 42,
        "identifier": "FK2/ABCDEF",
        "persistentUrl": "https://doi.org/10.5072/FK2/ABCDEF",
        "protocol": "doi",
        "authority": "10.5072",
        "separator": "/",
        "publisher": "Test",
        "storageIdentifier": "file://10.5072/FK2/ABCDEF",
        "latestVersion": VERSION_FIELDS,
    },
}

# GET /api/datasets/:id/versions/:versionId -> data IS the version, unwrapped.
UNWRAPPED = {"status": "OK", "data": VERSION_FIELDS}


@pytest.fixture(autouse=True)
def _patch_get_dir(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """Redirect the CSV export to tmp_path instead of the real export dir."""
    monkeypatch.setattr(spreadsheet_module, "get_dir", lambda _directory: tmp_path)


@pytest.mark.parametrize("payload", [WRAPPED, UNWRAPPED], ids=["wrapped", "unwrapped"])
def test_make_csv_file_handles_both_dataset_json_shapes(payload: dict) -> None:
    """make_csv_file must not crash whether `data` wraps the version or is the version itself."""
    csv_path, _checksum = Spreadsheet(Config()).make_csv_file(
        {"42": payload}, timestamp_enabled=False
    )

    with csv_path.open(encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    assert len(rows) == 1
    assert rows[0]["ID"] == "42"
    assert rows[0]["DatasetTitle"] == "Test Dataset"
