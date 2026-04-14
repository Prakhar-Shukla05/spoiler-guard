# sonyliv-util

Spoiler-free Champions League highlights launcher for [SonyLiv](https://www.sonyliv.com/).

SonyLiv highlights the winning team in video thumbnails, spoiling the result before you can watch. This tool queries the SonyLiv API, presents matches with just team names (no scores, no thumbnails), and opens your selection directly in your browser with autoplay enabled — so you never see the spoiler thumbnail.

## How it works

1. Fetches an anonymous browsing token from SonyLiv's public API
2. Queries recent UCL content sorted by date
3. Groups results by match and selects the best available content:
   - **Favourite team matches** — full match replay (preferred), then extended highlights, then highlights
   - **Other matches** — extended highlights (preferred), then highlights
4. Displays a spoiler-free list showing only team names and content type
5. Opens your selection in the configured browser with `?watch=true` to auto-start playback

## Setup

Requires [uv](https://docs.astral.sh/uv/) and macOS.

```bash
# Clone and install
git clone <repo-url> && cd sonyLivUtil
uv sync

# Run
uv run sonyliv

# Or with a specific date
uv run sonyliv --date 2026-04-09
```

## Usage

```
$ uv run sonyliv --date 2026-04-09
Looking for UCL matches on 09 Apr 2026...

Found 2 match(es):

  1. PSG vs Liverpool — Extended Highlights (24m 51s)
  2. Barcelona vs Atletico — Extended Highlights (25m 52s)

Enter match number (or 'a' for all, 'q' to quit): 1
  Opening: PSG vs Liverpool
```

### Options

| Flag | Description | Default |
|------|-------------|---------|
| `--date YYYY-MM-DD` | Match date to look up | Yesterday (IST) |

## Configuration

All settings are in `config.toml` at the project root:

```toml
[browser]
# Application name passed to `open -a` on macOS.
# Examples: "Google Chrome", "Firefox", "Safari", "Arc"
name = "Google Chrome"

[sonyliv]
# SonyLiv's internal tournament ID for the UCL season.
# Update this when a new season starts.
tournament_id = "1700000773"

# Season string used in the SonyLiv URL path.
season = "2025-26"

[preferences]
# Teams for which a full match replay is preferred over highlights.
favourite_teams = ["chelsea"]
```

## Project structure

```
config.toml                # All user-configurable settings
src/sonyliv_util/
  __init__.py
  config.py    # Loads config.toml, provides module-level constants
  api.py       # SonyLiv API client (token, content listing)
  match.py     # Match parsing, content selection, URL building
  cli.py       # CLI entry point and interactive UI
tests/
  test_config.py
  test_api.py
  test_match.py
  test_cli.py
```

## Requirements

- [uv](https://docs.astral.sh/uv/) (handles Python installation automatically)
- macOS (uses `open -a` to launch the browser)
- A browser with an active SonyLiv subscription logged in
- Network access to `apiv2.sonyliv.com`

## Limitations

- The API returns at most 50 items per request. If SonyLiv publishes more than 50 content items between matchdays, older matches may not appear. Use `--date` to target specific dates.
- The `objectSubtype` API filter only works reliably for `HIGHLIGHTS`. Other subtypes (`FULL_MATCH`, `SPORTS_CLIPS`) are filtered client-side from unfiltered results.
- Season-specific: update `tournament_id` and `season` in `config.toml` when a new UCL season starts.
