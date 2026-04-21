"""Hotstar Premier League match parsing and content grouping."""

import re
from datetime import datetime, timedelta


def parse_teams_from_replay(title):
    """Extract team names from a Hotstar replay title.

    Replay titles use the format "Team1 vs Team2: Replay" — no scores.
    """
    if not title:
        return None, None

    match = re.match(r"^\s*(.+?)\s+vs\s+(.+?):\s*Replay\s*$", title, re.IGNORECASE)
    if match:
        return match.group(1).strip(), match.group(2).strip()

    return None, None


def parse_teams_from_highlights(title):
    """Extract team names from a Hotstar highlights title, stripping scores.

    Highlights titles contain scores: "Manchester City 2-1 Arsenal"
    """
    if not title:
        return None, None

    # Match "Team1 score-score Team2"
    match = re.match(r"^\s*(.+?)\s+(\d+)\s*-\s*(\d+)\s+(.+?)\s*$", title)
    if match:
        return match.group(1).strip(), match.group(4).strip()

    # Fallback: "Team1 vs Team2" without scores
    match = re.match(r"^\s*(.+?)\s+vs\s+(.+?)(?:\s*[:|]|\s*$)", title, re.IGNORECASE)
    if match:
        return match.group(1).strip(), match.group(2).strip()

    return None, None


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


def build_matches_from_replays(replay_items, today):
    """Build a match list from replay tray items, filtered to last 2 days.

    Returns a list of dicts with keys: home, away, replay (content option),
    content_id, si_match_id (for fetching highlights later).
    """
    matches = []

    for item in replay_items:
        item_date = parse_broadcast_date(item)
        if not is_recent(item_date, today):
            continue

        home, away = parse_teams_from_replay(item.get("title", ""))
        if not home or not away:
            continue

        matches.append({
            "home": home,
            "away": away,
            "date": item_date,
            "content_id": item.get("contentId") or item.get("id"),
            "si_match_id": item.get("siMatchId"),
            "options": [{
                "content_type": "full_match",
                "content_id": item.get("contentId") or item.get("id"),
                "duration": item.get("duration", 0),
            }],
        })

    return matches


def extract_highlights_from_detail(match_detail, si_match_id=None):
    """Extract highlights content from a match detail response.

    The match detail has trays with related content. Filters to highlights
    matching the same siMatchId to avoid picking up highlights from other
    matches. Deduplicates by content ID.

    Returns a list of content options (highlights items).
    """
    highlights = []
    seen_ids = set()

    trays = match_detail.get("trays", {}).get("items", [])
    for tray in trays:
        for item in tray.get("assets", {}).get("items", []):
            content_type = item.get("contentType", "")
            if content_type != "SPORT_MATCH_HIGHLIGHTS" or not item.get("highlight"):
                continue

            # Filter to same match if siMatchId provided
            if si_match_id and str(item.get("siMatchId", "")) != str(si_match_id):
                continue

            cid = item.get("contentId") or item.get("id")
            if cid in seen_ids:
                continue
            seen_ids.add(cid)

            highlights.append({
                "content_type": "highlights",
                "content_id": cid,
                "duration": item.get("duration", 0),
            })

    return highlights


def build_url(content_id):
    """Build a Hotstar watch URL for a content item.

    Hotstar's SPA router requires two path segments after /sports/ before
    the content ID. The slug text is cosmetic — only the ID matters.
    """
    return f"https://www.hotstar.com/in/sports/football/match/{content_id}"
