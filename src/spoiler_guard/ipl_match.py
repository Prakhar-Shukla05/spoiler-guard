"""Hotstar IPL match parsing and content grouping."""

import re
from datetime import datetime, timedelta


def parse_teams(title):
    """Extract team names from an IPL highlights title.

    Titles use the format "SRH vs DC: Highlights" or
    "SRH vs DC: 1st Inns, Highlights" — no scores.
    """
    if not title:
        return None, None

    match = re.match(r"^\s*(.+?)\s+vs\s+(.+?):", title, re.IGNORECASE)
    if match:
        return match.group(1).strip(), match.group(2).strip()

    return None, None


def classify_content_type(title):
    """Determine content type from title keywords.

    Returns a human-readable label like "Highlights" or "1st Inns Highlights".
    """
    if not title:
        return None

    # Extract the part after the colon
    colon_idx = title.find(":")
    if colon_idx == -1:
        return None

    qualifier = title[colon_idx + 1:].strip()
    if not qualifier:
        return None

    return qualifier


def parse_broadcast_date(item):
    """Extract match date from broadCastDate epoch timestamp."""
    ts = item.get("broadCastDate")
    if isinstance(ts, (int, float)) and ts > 0:
        return datetime.fromtimestamp(ts).date()
    return None


def is_recent(item_date, today):
    """Return True if the date is today or yesterday."""
    if item_date is None:
        return False
    yesterday = today - timedelta(days=1)
    return item_date in (today, yesterday)


def build_matches_from_tray(items, today):
    """Group IPL tray items by match, filtered to last 2 days.

    Returns a list of dicts with keys: home, away, options (list of
    content choices with content_type label, content_id, duration).
    """
    match_map = {}

    for item in items:
        # Only include full match highlights, skip innings highlights
        if item.get("contentType") != "SPORT_MATCH_HIGHLIGHTS":
            continue

        item_date = parse_broadcast_date(item)
        if not is_recent(item_date, today):
            continue

        title = item.get("title", "")
        home, away = parse_teams(title)
        if not home or not away:
            continue

        key = (home, away)
        if key not in match_map:
            match_map[key] = {
                "home": home,
                "away": away,
                "date": item_date,
                "content_id": item.get("contentId") or item.get("id"),
                "duration": item.get("duration", 0),
            }

    return list(match_map.values())


def build_url(content_id):
    """Build a Hotstar watch URL for IPL content."""
    return f"https://www.hotstar.com/in/sports/cricket/match/{content_id}"
