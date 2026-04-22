# spoiler-guard

Spoiler-free sports highlights launcher for [SonyLiv](https://www.sonyliv.com/) (Champions League) and [Hotstar](https://www.hotstar.com/) (Premier League, IPL).

Both platforms spoil match results through thumbnails and titles before you can watch. This tool queries their APIs, presents matches with just team names (no scores, no thumbnails), and opens your selection directly in your browser — so you never see the result.

## How it works

### SonyLiv (Champions League)

1. Fetches an anonymous browsing token from SonyLiv's public API
2. Queries recent UCL content sorted by date
3. Groups results by match and selects the best available content:
   - **Favourite team matches** — full match replay (preferred), then extended highlights, then highlights
   - **Other matches** — extended highlights (preferred), then highlights
4. Displays a spoiler-free list showing only team names and content type
5. Opens your selection in the configured browser with `?watch=true` to auto-start playback

### Hotstar (Premier League)

1. Authenticates with Hotstar's API using your `userUP` cookie
2. Fetches PL replays from the editorial tray, then enriches each match with highlights from the match detail API
3. Filters to the last 2 days (today + yesterday IST)
4. Displays a spoiler-free match list — team names only, no scores
5. Two-level selection: pick a match, then choose between highlights and full match replay
6. Opens your selection in the configured browser

### Hotstar (IPL)

1. Authenticates with Hotstar's API using your `userUP` cookie
2. Fetches IPL highlights from the editorial tray, filtered to full match highlights only (no innings highlights)
3. Filters to the last 2 days (today + yesterday IST)
4. Displays a spoiler-free match list with team abbreviations and duration
5. Single-step selection: pick a match and it opens directly

## Setup

Requires [uv](https://docs.astral.sh/uv/). Works on macOS, Windows, and Linux.

```bash
# Clone and install
git clone <repo-url> && cd spoiler-guard
cp config.toml.example config.toml
uv sync
```

### Hotstar authentication

Hotstar requires your `userUP` cookie for API access (used by both PL and IPL):

1. Open [hotstar.com](https://www.hotstar.com/) in your browser and log in
2. Open DevTools (F12) → Application → Cookies → `hotstar.com`
3. Copy the value of the `userUP` cookie
4. Paste it into `config.toml` under `[hotstar] user_token`

SonyLiv requires no authentication — it uses anonymous API tokens.

### Browser extension (optional, recommended)

The included browser extension hides spoiler thumbnails, match scores in titles, and the seekbar/time display on football pages. It works on both SonyLiv and Hotstar.

**Chrome / Edge / Arc / Brave / Opera:**

1. Open `chrome://extensions` (or `edge://extensions` for Edge)
2. Enable **Developer mode** (top right)
3. Click **Load unpacked** and select the `browser-extension/chrome/` directory
4. Done — the extension activates on SonyLiv (`?watch=true` URLs) and Hotstar (`/sports/` pages)

**Firefox:**

1. Open `about:debugging#/runtime/this-firefox`
2. Click **Load Temporary Add-on...**
3. Select the `browser-extension/firefox/manifest.json` file
4. Done — same activation as above

## Usage

### Champions League

```
$ uv run ucl --date 2026-04-09
Looking for UCL matches on 09 Apr 2026...

  Fetching API token...
  Searching page 1/10... 47 new items

Found 2 match(es):

  1. PSG vs Liverpool — Extended Highlights (24m 51s)
  2. Barcelona vs Atletico — Extended Highlights (25m 52s)

Pick a match (number, 'a' for all, 'q' to quit): 1
  Opening: PSG vs Liverpool
```

### Premier League

```
$ uv run pl
Looking for PL matches (20 Apr – 21 Apr 2026)...

Found 4 match(es), fetching highlights...

  1. Manchester City vs Arsenal
  2. Everton vs Liverpool
  3. Aston Villa vs Sunderland
  4. Nottingham Forest vs Burnley

Pick a match (number, 'a' for all, 'q' to quit): 1

  Manchester City vs Arsenal:
    1. Highlights (7m 10s)
    2. Full Match Replay (2h 14m)

  Pick content (number, or 'b' to go back): 2
  Opening: Manchester City vs Arsenal — Full Match Replay
```

### IPL

```
$ uv run ipl
Looking for IPL matches (21 Apr – 22 Apr 2026)...

Found 1 match(es):

  1. SRH vs DC — Highlights (15m 16s)

Pick a match (number, 'a' for all, 'q' to quit): 1
  Opening: SRH vs DC
```

### Options

| Command | Tournament | Platform | Default date range |
|---------|-----------|----------|-------------------|
| `uv run ucl` | Champions League | SonyLiv | Today (IST) |
| `uv run pl` | Premier League | Hotstar | Today + yesterday (IST) |
| `uv run ipl` | IPL | Hotstar | Today + yesterday (IST) |

All commands accept `--date YYYY-MM-DD` to look up a specific date.

## Configuration

Copy `config.toml.example` to `config.toml` and edit. The file is gitignored since it contains the Hotstar auth token.

```toml
[platform]
os = "macos"

[browser]
name = "Google Chrome"

[sonyliv]
tournament_id = "1700000773"
season = "2025-26"

[preferences]
favourite_teams = ["chelsea"]

[hotstar]
tray_id = "1271442198"       # PL replays tray
ipl_tray_id = "1271615359"   # IPL highlights tray
user_token = ""               # Your Hotstar userUP cookie value
```

## Project structure

```
config.toml.example        # Template config (copy to config.toml)
browser-extension/
  chrome/
    manifest.json  # Chrome/Chromium extension manifest (Manifest V3)
    content.js     # Hides spoiler elements on SonyLiv and Hotstar
    overlay.css    # CSS rules for poster, thumbnail, seekbar hiding
  firefox/
    manifest.json  # Firefox manifest with gecko ID
    content.js     # → symlink to chrome/content.js
    overlay.css    # → symlink to chrome/overlay.css
src/spoiler_guard/
  __init__.py
  common.py          # Shared utilities (IST, format_duration, open_in_browser)
  config.py          # Loads config.toml, provides module-level constants
  sonyliv_api.py     # SonyLiv API client (token, content listing)
  sonyliv_match.py   # SonyLiv match parsing, content selection, URL building
  sonyliv_cli.py     # UCL CLI entry point (uv run ucl)
  hotstar_api.py     # Hotstar API client (HMAC auth, tray/match fetching)
  hotstar_match.py   # PL match parsing, score stripping, grouping
  hotstar_cli.py     # PL CLI entry point (uv run pl)
  ipl_match.py       # IPL match parsing and grouping
  ipl_cli.py         # IPL CLI entry point (uv run ipl)
tests/
  test_common.py, test_config.py
  test_sonyliv_api.py, test_sonyliv_match.py, test_sonyliv_cli.py
  test_hotstar_api.py, test_hotstar_match.py, test_hotstar_cli.py
  test_ipl_match.py, test_ipl_cli.py
```

## Requirements

- [uv](https://docs.astral.sh/uv/) (handles Python installation automatically)
- macOS, Windows, or Linux (set `platform.os` in `config.toml`)
- A browser with active SonyLiv and/or Hotstar subscriptions logged in
- Network access to `apiv2.sonyliv.com` and/or `api.hotstar.com`

## Limitations

### SonyLiv
- The API returns at most 50 items per page. The tool paginates up to 10 pages (500 items) to find older matches, but very old content may still be unreachable.
- The `objectSubtype` API filter only works reliably for `HIGHLIGHTS`. Other subtypes (`FULL_MATCH`, `SPORTS_CLIPS`) are filtered client-side from unfiltered results.
- Season-specific: update `tournament_id` and `season` in `config.toml` when a new UCL season starts.
- SonyLiv briefly flashes the match thumbnail while the video buffers — install the browser extension to hide it.

### Hotstar (PL)
- Requires a valid `userUP` cookie which expires periodically — you'll need to re-copy it from DevTools when it does.
- Hotstar's client-side router rewrites the URL to include the match score (e.g. `/crystal-palace-0-0-west-ham/`). The extension hides the score on the page itself, but the address bar may still show it.
- The replay tray only contains recent matches. Older content may not be available.
- Season-specific: update `tray_id` in `config.toml` when a new PL season starts.

### Hotstar (IPL)
- Same `userUP` cookie requirement as PL.
- Only full match highlights are shown (innings highlights are filtered out).
- Season-specific: update `ipl_tray_id` in `config.toml` when a new IPL season starts.
