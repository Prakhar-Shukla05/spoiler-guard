"""CLI entry point for the spoiler-free IPL highlights launcher (Hotstar)."""

import argparse
import sys
from datetime import datetime, timedelta

from .common import IST, format_duration, open_in_browser
from .config import HOTSTAR_IPL_TRAY_ID, HOTSTAR_USER_TOKEN
from .hotstar_api import fetch_tray_content
from .ipl_match import build_matches_from_tray, build_url


def main():
    parser = argparse.ArgumentParser(
        description="Spoiler-free IPL highlights launcher for Hotstar",
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
        f"Looking for IPL matches "
        f"({yesterday.strftime('%d %b')} – {target_date.strftime('%d %b %Y')})...\n"
    )

    # Fetch highlights tray
    try:
        items = fetch_tray_content(
            HOTSTAR_USER_TOKEN, HOTSTAR_IPL_TRAY_ID, size=50,
        )
    except Exception as e:
        print(f"Failed to fetch content: {e}")
        sys.exit(1)

    # Build match list
    match_list = build_matches_from_tray(items, target_date)

    if not match_list:
        print("No IPL matches found for this date range.")
        print("Try a different date with: ipl --date YYYY-MM-DD")
        sys.exit(0)

    # Display spoiler-free match list
    print(f"Found {len(match_list)} match(es):\n")
    for i, match in enumerate(match_list, 1):
        duration = format_duration(match["duration"])
        print(f"  {i}. {match['home']} vs {match['away']} — Highlights ({duration})")

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
                url = build_url(match["content_id"])
                print(f"  Opening: {match['home']} vs {match['away']}", flush=True)
                open_in_browser(url)
            break
        else:
            try:
                idx = int(choice) - 1
                if 0 <= idx < len(match_list):
                    match = match_list[idx]
                    url = build_url(match["content_id"])
                    print(f"\n  Opening: {match['home']} vs {match['away']}", flush=True)
                    open_in_browser(url)
                    print()
                else:
                    print(f"  Invalid number. Choose 1-{len(match_list)}.")
            except ValueError:
                print("  Enter a number, 'a' for all, or 'q' to quit.")
