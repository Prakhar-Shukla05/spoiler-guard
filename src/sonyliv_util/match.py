"""Match parsing and content selection logic."""

import re
from datetime import datetime

from .config import FAVOURITE_TEAMS, SEASON, TOURNAMENT_ID

# SonyLiv URL pattern — the slug before the content ID is cosmetic,
# only the numeric ID at the end matters for routing. SonyLiv auto-redirects
# to the canonical URL.
SONYLIV_URL_TEMPLATE = (
    "https://www.sonyliv.com/sports/"
    "uefa-champions-league-{season}-{tournament_id}/"
    "match-{content_id}?watch=true"
)


def parse_teams(episode_title):
    """Extract home and away team names from the episode title.

    Titles follow patterns like:
        "PSG vs Liverpool - Quarter-Final - Leg 1 - Highlights - 9 Apr 2026"
        "Barcelona vs Atletico - Extended Highlights - 9 Apr 2026"
    """
    match = re.match(r"^\s*(.+?)\s+vs\s+(.+?)\s*-", episode_title)
    if match:
        return match.group(1).strip(), match.group(2).strip()
    return None, None


def parse_date_from_title(episode_title):
    """Extract date from the end of the episode title.

    Looks for patterns like "9 Apr 2026" or "08 Mar 2026" at the end.
    """
    match = re.search(r"(\d{1,2}\s+\w{3}\s+\d{4})\s*$", episode_title)
    if match:
        try:
            return datetime.strptime(match.group(1), "%d %b %Y").date()
        except ValueError:
            pass
    return None


def is_favourite_team_match(home, away):
    """Check if a favourite team is playing in this match."""
    if not home or not away:
        return False
    combined = f"{home} {away}".lower()
    return any(team in combined for team in FAVOURITE_TEAMS)


def build_url(content_id):
    """Build a SonyLiv watch URL for a content item.

    The ?watch=true parameter triggers autoplay, which avoids showing the
    spoiler-laden thumbnail before the video starts.
    """
    return SONYLIV_URL_TEMPLATE.format(
        season=SEASON,
        tournament_id=TOURNAMENT_ID,
        content_id=content_id,
    )


def find_matches(items, target_date):
    """Group content items by match (team pair) for a given date.

    Returns a dict keyed by (home, away) with lists of content items,
    each annotated with its type (extended_highlights, highlights, full_match).
    """
    matches = {}

    for item in items:
        meta = item.get("metadata", {})
        episode_title = meta.get("episodeTitle", "")
        subtype = meta.get("objectSubtype", "")

        item_date = parse_date_from_title(episode_title)
        if item_date != target_date:
            continue

        home, away = parse_teams(episode_title)
        if not home or not away:
            continue

        if subtype == "FULL_MATCH":
            content_type = "full_match"
        elif subtype == "HIGHLIGHTS" and "extended" in episode_title.lower():
            content_type = "extended_highlights"
        elif subtype == "HIGHLIGHTS":
            content_type = "highlights"
        else:
            continue

        key = (home, away)
        if key not in matches:
            matches[key] = []

        matches[key].append({
            "content_type": content_type,
            "content_id": item.get("id"),
            "episode_title": episode_title,
            "duration": meta.get("duration", 0),
        })

    return matches


def select_best_content(items, is_favourite):
    """Select the best content item for a match based on a tiered approach.

    For favourite teams: full match replay > extended highlights > highlights.
    For others: extended highlights > highlights.
    """
    priority = (
        ["full_match", "extended_highlights", "highlights"]
        if is_favourite
        else ["extended_highlights", "highlights"]
    )

    for content_type in priority:
        candidates = [i for i in items if i["content_type"] == content_type]
        if candidates:
            return max(candidates, key=lambda x: x["duration"])

    return None
