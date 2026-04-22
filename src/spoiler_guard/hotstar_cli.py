"""CLI entry point for the spoiler-free Premier League launcher (Hotstar)."""

import argparse
import sys
from datetime import datetime, timedelta

from .common import IST, TYPE_LABELS, format_duration, open_in_browser
from .config import HOTSTAR_TRAY_ID, HOTSTAR_USER_TOKEN
from .hotstar_api import fetch_match_detail, fetch_tray_content
from .hotstar_match import (
    build_matches_from_replays,
    build_url,
    extract_highlights_from_detail,
)


def main():
    parser = argparse.ArgumentParser(
        description="Spoiler-free PL highlights launcher for Hotstar",
    )
    parser.add_argument(
        "--date",
        help="Match date in YYYY-MM-DD format (default: today and yesterday IST)",
        default=None,
    )
    args = parser.parse_args()

    # Validate auth
    if not HOTSTAR_USER_TOKEN:
        print("Hotstar user token not configured.")
        print("Set hotstar.user_token in config.toml with your userUP cookie value.")
        print("To find it: open hotstar.com, log in, DevTools > Application > Cookies > userUP")
        sys.exit(1)

    # Determine date range
    now_ist = datetime.now(IST)
    if args.date:
        try:
            target_date = datetime.strptime(args.date, "%Y-%m-%d").date()
        except ValueError:
            print(f"Invalid date format: {args.date}. Use YYYY-MM-DD.")
            sys.exit(1)
    else:
        target_date = now_ist.date()

    yesterday = target_date - timedelta(days=1)
    print(
        f"Looking for PL matches "
        f"({yesterday.strftime('%d %b')} – {target_date.strftime('%d %b %Y')})...\n"
    )

    # Fetch replay tray
    try:
        replay_items = fetch_tray_content(
            HOTSTAR_USER_TOKEN, HOTSTAR_TRAY_ID, size=50,
        )
    except Exception as e:
        print(f"Failed to fetch content: {e}")
        sys.exit(1)

    # Build match list from replays
    match_list = build_matches_from_replays(replay_items, target_date)

    if not match_list:
        print("No PL matches found for this date range.")
        print("Try a different date with: pl --date YYYY-MM-DD")
        sys.exit(0)

    # Fetch highlights for each match
    print(f"Found {len(match_list)} match(es), fetching highlights...\n")
    for match in match_list:
        try:
            detail = fetch_match_detail(
                HOTSTAR_USER_TOKEN,
                match["content_id"],
                match["si_match_id"],
            )
            highlights = extract_highlights_from_detail(detail, match["si_match_id"])
            # Prepend highlights before replay
            match["options"] = highlights + match["options"]
        except Exception:
            pass  # Keep the replay option even if highlights fetch fails

    # Display spoiler-free match list
    for i, match in enumerate(match_list, 1):
        print(f"  {i}. {match['home']} vs {match['away']}")

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
            for match in match_list:
                best = match["options"][0]
                url = build_url(best["content_id"])
                label = TYPE_LABELS.get(best["content_type"], best["content_type"])
                print(f"  Opening: {match['home']} vs {match['away']} — {label}", flush=True)
                open_in_browser(url)
            break
        else:
            try:
                idx = int(choice) - 1
                if 0 <= idx < len(match_list):
                    _select_content(match_list[idx])
                else:
                    print(f"  Invalid number. Choose 1-{len(match_list)}.")
            except ValueError:
                print("  Enter a number, 'a' for all, or 'q' to quit.")


def _select_content(match):
    """Show content options for a match and open the user's selection."""
    home, away = match["home"], match["away"]
    options = match["options"]

    if len(options) == 1:
        # Only one option — open directly
        opt = options[0]
        url = build_url(opt["content_id"])
        label = TYPE_LABELS.get(opt["content_type"], opt["content_type"])
        print(f"\n  Opening: {home} vs {away} — {label}", flush=True)
        open_in_browser(url)
        print()
        return

    print(f"\n  {home} vs {away}:")
    for i, opt in enumerate(options, 1):
        label = TYPE_LABELS.get(opt["content_type"], opt["content_type"])
        duration = format_duration(opt["duration"])
        print(f"    {i}. {label} ({duration})")

    print()
    while True:
        try:
            pick = input("  Pick content (number, or 'b' to go back): ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            print()
            return

        if pick == "b":
            print()
            return

        try:
            idx = int(pick) - 1
            if 0 <= idx < len(options):
                opt = options[idx]
                url = build_url(opt["content_id"])
                label = TYPE_LABELS.get(opt["content_type"], opt["content_type"])
                print(f"\n  Opening: {home} vs {away} — {label}", flush=True)
                open_in_browser(url)
                print()
                return
            else:
                print(f"  Invalid number. Choose 1-{len(options)}.")
        except ValueError:
            print(f"  Enter 1-{len(options)}, or 'b' to go back.")
