"""Configuration loader for sonyliv-util.

Reads config.toml from the project root. Falls back to defaults if the
file is missing or a key is absent.
"""

import tomllib
from pathlib import Path

_DEFAULTS = {
    "browser": {
        "name": "Google Chrome",
    },
    "sonyliv": {
        "tournament_id": "1700000773",
        "season": "2025-26",
    },
    "preferences": {
        "favourite_teams": ["chelsea"],
    },
}


def _find_config_path():
    """Walk up from this file's directory to find config.toml."""
    current = Path(__file__).resolve().parent
    for _ in range(5):
        candidate = current / "config.toml"
        if candidate.exists():
            return candidate
        current = current.parent
    return None


def load_config():
    """Load configuration from config.toml, merged with defaults."""
    config = {
        section: dict(values) for section, values in _DEFAULTS.items()
    }

    path = _find_config_path()
    if path is None:
        return config

    with open(path, "rb") as f:
        user_config = tomllib.load(f)

    for section, values in user_config.items():
        if section in config:
            config[section].update(values)
        else:
            config[section] = values

    return config


# Module-level config — loaded once on import.
_config = load_config()

# Browser
BROWSER_NAME = _config["browser"]["name"]

# SonyLiv
TOURNAMENT_ID = _config["sonyliv"]["tournament_id"]
SEASON = _config["sonyliv"]["season"]

# Preferences
FAVOURITE_TEAMS = _config["preferences"]["favourite_teams"]
