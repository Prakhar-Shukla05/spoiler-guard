"""Tests for configuration loading."""

import tomllib
from pathlib import Path
from unittest.mock import mock_open, patch

from sonyliv_util.config import _DEFAULTS, load_config


class TestLoadConfig:
    def test_returns_defaults_when_no_config_file(self):
        with patch("sonyliv_util.config._find_config_path", return_value=None):
            config = load_config()

        assert config["platform"]["os"] == "macos"
        assert config["browser"]["name"] == "Google Chrome"
        assert config["sonyliv"]["tournament_id"] == "1700000773"
        assert config["sonyliv"]["season"] == "2025-26"
        assert config["preferences"]["favourite_teams"] == ["chelsea"]

    def test_overrides_defaults_with_config_file(self):
        toml_content = b"""
[browser]
name = "Firefox"

[preferences]
favourite_teams = ["arsenal", "chelsea"]
"""
        fake_path = Path("/fake/config.toml")
        with (
            patch("sonyliv_util.config._find_config_path", return_value=fake_path),
            patch("builtins.open", mock_open(read_data=toml_content)),
        ):
            config = load_config()

        assert config["browser"]["name"] == "Firefox"
        assert config["preferences"]["favourite_teams"] == ["arsenal", "chelsea"]
        # Unmodified defaults are preserved
        assert config["sonyliv"]["tournament_id"] == "1700000773"

    def test_preserves_unspecified_sections(self):
        toml_content = b"""
[browser]
name = "Safari"
"""
        fake_path = Path("/fake/config.toml")
        with (
            patch("sonyliv_util.config._find_config_path", return_value=fake_path),
            patch("builtins.open", mock_open(read_data=toml_content)),
        ):
            config = load_config()

        assert config["browser"]["name"] == "Safari"
        assert config["sonyliv"]["tournament_id"] == "1700000773"
        assert config["preferences"]["favourite_teams"] == ["chelsea"]

    def test_defaults_contain_all_required_keys(self):
        assert "platform" in _DEFAULTS
        assert "os" in _DEFAULTS["platform"]
        assert "browser" in _DEFAULTS
        assert "name" in _DEFAULTS["browser"]
        assert "sonyliv" in _DEFAULTS
        assert "tournament_id" in _DEFAULTS["sonyliv"]
        assert "season" in _DEFAULTS["sonyliv"]
        assert "preferences" in _DEFAULTS
        assert "favourite_teams" in _DEFAULTS["preferences"]
