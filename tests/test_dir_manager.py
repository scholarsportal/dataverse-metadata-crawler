"""Test dvmeta/services/dir_manager.py."""

from pathlib import Path

import pytest

from dvmeta.services.dir_manager import EXPORT_BASE_DIR, ExportDir, get_dir


@pytest.mark.parametrize(
    ("export_dir", "expected_dir"),
    [(ExportDir.JSON, ExportDir.JSON.value), (ExportDir.LOG, ExportDir.LOG.value)],
)
def test_get_dir_returns_expected_dir(
    export_dir: ExportDir, expected_dir: str, tmp_path: Path
) -> None:
    """get_dir returns the expected directory name for each ExportDir enum value."""
    assert get_dir(export_dir) == EXPORT_BASE_DIR / expected_dir
    assert Path(get_dir(export_dir)).exists()  # Ensure the directory exists
