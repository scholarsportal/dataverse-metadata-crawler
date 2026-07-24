"""Test dataverse-metadata-crawler CLI."""

from typer.testing import CliRunner

from dvmeta import app

runner = CliRunner()


def test_cli_help() -> None:
    """Test that the CLI help command works."""
    result = runner.invoke(app.app, ["--help"])
    assert result.exit_code == 0
    assert "Usage:" in result.output
