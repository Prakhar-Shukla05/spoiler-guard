"""Shared utilities for spoiler-guard CLI entry points."""

import subprocess
import webbrowser
from datetime import timedelta, timezone

from .config import BROWSER_NAME, PLATFORM

IST = timezone(timedelta(hours=5, minutes=30))

TYPE_LABELS = {
    "full_match": "Full Match Replay",
    "extended_highlights": "Extended Highlights",
    "highlights": "Highlights",
}


def format_duration(seconds):
    """Format seconds into a human-readable duration."""
    minutes = seconds // 60
    secs = seconds % 60
    if minutes >= 60:
        hours = minutes // 60
        minutes = minutes % 60
        return f"{hours}h {minutes}m"
    return f"{minutes}m {secs}s"


def open_in_browser(url):
    """Open URL in the configured browser on the configured platform."""
    try:
        if PLATFORM == "macos":
            subprocess.run(["open", "-a", BROWSER_NAME, url], check=True)
        elif PLATFORM == "windows":
            subprocess.run(["cmd", "/c", "start", "", BROWSER_NAME, url], check=True)
        elif PLATFORM == "linux":
            if BROWSER_NAME:
                subprocess.run([BROWSER_NAME, url], check=True)
            else:
                subprocess.run(["xdg-open", url], check=True)
        else:
            webbrowser.open(url)
    except (subprocess.CalledProcessError, FileNotFoundError):
        webbrowser.open(url)
