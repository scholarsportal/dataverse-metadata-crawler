"""Test config.py."""

import pytest

from dvmeta.models.config import Config


@pytest.mark.parametrize(
    ("env_var", "expected"),
    [
        ("api_token", "test_token"),
        ("api_key", "test_token"),
        ("API_TOKEN", "test_token"),
        ("API_KEY", "test_token"),
    ],
)
def test_config_api_token_aliases(monkeypatch, env_var, expected):
    """Test that the Config model correctly handles different aliases for the api_token field."""
    monkeypatch.setenv(env_var, "test_token")
    config = Config()
    assert config.api_token == expected
