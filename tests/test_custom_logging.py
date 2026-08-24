"""Test the custom logging functionality of the dataverse-metadata-crawler."""

from pathlib import Path

import pytest
from loguru import logger

from dvmeta.services.custom_logging import setup_logging


@pytest.fixture(autouse=True)
def _reset_logger():
    """Loguru's logger is a global singleton; restore default state after each test."""
    yield
    logger.remove()
    logger.add(lambda msg: print(msg, end=""))


def test_setup_logging_writes_to_console(capsys: pytest.CaptureFixture) -> None:
    """Console sink is always added and receives log messages."""
    setup_logging()
    logger.info("hello console")
    captured = capsys.readouterr()
    assert "hello console" in captured.out


def test_setup_logging_no_file_by_default(tmp_path: Path) -> None:
    """No debug.log is created when log_file_dir is not given."""
    setup_logging()
    assert not (tmp_path / "debug.log").exists()


def test_setup_logging_writes_log_file(tmp_path: Path) -> None:
    """A debug.log file is created and receives log messages."""
    setup_logging(log_file_dir=tmp_path)
    logger.info("hello file")
    log_file = tmp_path / "debug.log"
    assert log_file.exists()
    assert "hello file" in log_file.read_text()


def test_setup_logging_creates_missing_dirs(tmp_path: Path) -> None:
    """Missing parent directories for log_file_dir are created."""
    nested_dir = tmp_path / "nested" / "logs"
    setup_logging(log_file_dir=nested_dir)
    assert nested_dir.exists()


def test_setup_logging_respects_log_level(tmp_path: Path) -> None:
    """Messages below the configured level are filtered out."""
    setup_logging(log_file_dir=tmp_path, log_level="WARNING")
    logger.info("should be filtered")
    logger.warning("should appear")
    content = (tmp_path / "debug.log").read_text()
    assert "should be filtered" not in content
    assert "should appear" in content
