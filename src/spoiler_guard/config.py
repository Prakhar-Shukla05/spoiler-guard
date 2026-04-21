"""Configuration loader for spoiler-guard.

Reads config.toml from the project root. Falls back to defaults if the
file is missing or a key is absent.
"""

import tomllib
from pathlib import Path

_DEFAULTS = {
    "platform": {
        "os": "macos",
    },
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
    "hotstar": {
        "tray_id": "1271442198",
        "user_token": "",
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
    config = {}
    for key, value in _DEFAULTS.items():
        config[key] = dict(value) if isinstance(value, dict) else value

    path = _find_config_path()
    if path is None:
        return config

    with open(path, "rb") as f:
        user_config = tomllib.load(f)

    for key, value in user_config.items():
        if key in config and isinstance(config[key], dict) and isinstance(value, dict):
            config[key].update(value)
        else:
            config[key] = value

    return config


# Module-level config — loaded once on import.
_config = load_config()

# Platform
PLATFORM = _config["platform"]["os"]

# Browser
BROWSER_NAME = _config["browser"]["name"]

# SonyLiv
TOURNAMENT_ID = _config["sonyliv"]["tournament_id"]
SEASON = _config["sonyliv"]["season"]

# Preferences
FAVOURITE_TEAMS = _config["preferences"]["favourite_teams"]

# Hotstar
HOTSTAR_TRAY_ID = _config["hotstar"]["tray_id"]
HOTSTAR_USER_TOKEN = _config["hotstar"]["user_token"]
