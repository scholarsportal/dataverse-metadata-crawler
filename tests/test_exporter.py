"""Test services/exporter.py."""

import json
from pathlib import Path

import pytest

from dvmeta.services import exporter
from dvmeta.services.dir_manager import ExportDir
from dvmeta.services.exporter import export_json

FIXTURE: dict = {"name": "test"}


@pytest.fixture(autouse=True)
def _patch_get_dir(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """Redirect exported files to tmp_path instead of the real export dir."""
    monkeypatch.setattr(exporter, "get_dir", lambda _directory: tmp_path)


@pytest.mark.parametrize(
    ("data", "name", "timestamp_enabled"),
    [(FIXTURE, "test_export", True), (FIXTURE, "test_export_no_timestamp", False)],
)
def test_export_json_writes_file(
    tmp_path: Path, data: dict, name: str, *, timestamp_enabled: bool
) -> None:
    """export_json writes a json file with the expected content and name."""
    export_json(data, ExportDir.JSON, name, timestamp_enabled=timestamp_enabled)

    files = list(tmp_path.glob(f"{name}*.json"))
    assert len(files) == 1
    assert json.loads(files[0].read_bytes()) == data
    assert (files[0].name == f"{name}.json") is not timestamp_enabled


def test_export_json_skips_empty_data(tmp_path: Path) -> None:
    """export_json does not create a file when data is empty."""
    export_json({}, ExportDir.JSON, "test_export_empty")

    assert list(tmp_path.glob("*.json")) == []
