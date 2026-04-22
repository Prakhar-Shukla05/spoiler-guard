"""CLI entry point for the spoiler-free UCL highlights launcher."""

import argparse
import sys
from datetime import datetime

from .sonyliv_api import fetch_ucl_content, get_token
from .common import IST, TYPE_LABELS, format_duration, open_in_browser
from .sonyliv_match import (
    build_url,
    find_matches,
    is_favourite_team_match,
    select_best_content,
)


def main():
    parser = argparse.ArgumentParser(
        description="Spoiler-free UCL highlights launcher for SonyLiv",
    )
    parser.add_argument(
        "--date",
        help="Match date in YYYY-MM-DD format (default: yesterday IST)",
        default=None,
    )
    args = parser.parse_args()

    # Determine target date
    if args.date:
        try:
            target_date = datetime.strptime(args.date, "%Y-%m-%d").date()
        except ValueError:
            print(f"Invalid date format: {args.date}. Use YYYY-MM-DD.")
            sys.exit(1)
    else:
        now_ist = datetime.now(IST)
        target_date = now_ist.date()

    print(f"Looking for UCL matches on {target_date.strftime('%d %b %Y')}...\n")

    # Get anonymous API token
    try:
        token = get_token()
    except Exception as e:
        print(f"Failed to get SonyLiv token: {e}")
        sys.exit(1)

    # Fetch content with pagination. The API returns 50 items per page and
    # the objectSubtype filter only works reliably for HIGHLIGHTS. Fetch
    # both filtered highlights and unfiltered content (for FULL_MATCH),
    # paginating until we find matches for the target date or exhaust
    # a reasonable search depth.
    MAX_PAGES = 10
    PAGE_SIZE = 50

    seen_ids = set()
    combined = []
    matches = {}

    try:
        for page in range(MAX_PAGES):
            offset = page * PAGE_SIZE
            highlights = fetch_ucl_content(
                token, subtype="HIGHLIGHTS", count=PAGE_SIZE, offset=offset,
            )
            all_recent = fetch_ucl_content(
                token, subtype=None, count=PAGE_SIZE, offset=offset,
            )

            new_items = 0
            for item in highlights + all_recent:
                cid = item.get("id")
                if cid not in seen_ids:
                    seen_ids.add(cid)
                    combined.append(item)
                    new_items += 1

            matches = find_matches(combined, target_date)

            if matches or new_items == 0:
                break

    except Exception as e:
        print(f"Failed to fetch content: {e}")
        sys.exit(1)

    # Select best content per match
    match_list = []
    for (home, away), items in matches.items():
        favourite = is_favourite_team_match(home, away)
        best = select_best_content(items, favourite)
        if best:
            match_list.append((home, away, favourite, best))

    if not match_list:
        print("No UCL highlights found for this date.")
        print("Try a different date with: ucl --date YYYY-MM-DD")
        sys.exit(0)

    # Display matches — spoiler-free, just team names
    print(f"Found {len(match_list)} match(es):\n")

    for i, (home, away, favourite, best) in enumerate(match_list, 1):
        label = TYPE_LABELS[best["content_type"]]
        duration = format_duration(best["duration"])
        marker = " [Favourite]" if favourite else ""
        print(f"  {i}. {home} vs {away} — {label} ({duration}){marker}")

    # Interactive selection
    print()
    while True:
        try:
            choice = input("Pick a match (number, 'a' for all, 'q' to quit): ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            print()
            break

        if choice == "q":
            break
        elif choice == "a":
            for home, away, _, best in match_list:
                url = build_url(best["content_id"])
                print(f"  Opening: {home} vs {away}", flush=True)
                open_in_browser(url)
            break
        else:
            try:
                idx = int(choice) - 1
                if 0 <= idx < len(match_list):
                    home, away, _, best = match_list[idx]
                    url = build_url(best["content_id"])
                    print(f"\n  Opening: {home} vs {away}", flush=True)
                    open_in_browser(url)
                    print()
                else:
                    print(f"  Invalid number. Choose 1-{len(match_list)}.")
            except ValueError:
                print("  Enter a number, 'a' for all, or 'q' to quit.")
