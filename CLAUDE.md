# spoiler-guard

Spoiler-free Champions League highlights launcher for SonyLiv. Queries the SonyLiv API, presents matches with just team names (no scores or thumbnails), and opens the video in the browser with autoplay.

## Quick reference

```bash
uv run sonyliv                      # yesterday's matches (IST)
uv run sonyliv --date 2026-04-09    # specific date
uv run python -m pytest             # run tests (66 tests)
```

## Project layout

```
config.toml                         # user-configurable settings (platform, browser, tournament, favourite teams)
src/spoiler_guard/
  config.py                         # loads config.toml, exposes module-level constants
  api.py                            # SonyLiv API client — token + content listing (stdlib only, no requests)
  match.py                          # match parsing, content selection, URL building
  cli.py                            # CLI entry point, interactive UI, browser launching
browser-extension/
  chrome/                           # Manifest V3 extension — hides spoiler thumbnails via MutationObserver
  firefox/                          # content.js and overlay.css are symlinks to chrome/
tests/
  test_api.py, test_cli.py, test_config.py, test_match.py
```

## Architecture notes

- **Zero dependencies** — uses only Python stdlib (`urllib.request`, `json`, `tomllib`, `argparse`, `subprocess`). No third-party packages.
- **Config resolution** — `config.py` walks up from its own directory to find `config.toml`, merges with hardcoded defaults. Config is loaded once at import time as module-level constants.
- **API quirk** — the `objectSubtype` filter only works reliably for `HIGHLIGHTS`. Other subtypes (`FULL_MATCH`, `SPORTS_CLIPS`) must be filtered client-side from unfiltered results.
- **Pagination** — API caps at 50 items/page. CLI paginates up to 10 pages (500 items), stopping early when target-date matches are found or no new items appear.
- **Content selection** — tiered priority per match: favourite teams get full_match > extended_highlights > highlights; others get extended_highlights > highlights. Ties broken by longest duration.
- **Browser extension** — Chrome and Firefox share the same `content.js` and `overlay.css` (Firefox uses symlinks). The extension activates only on SonyLiv pages with `?watch=true`.

## Conventions

- Python 3.13+, managed by uv with hatchling build backend
- Entry point: `sonyliv = spoiler_guard.cli:main` (defined in pyproject.toml)
- Tests use pytest, no mocking of the database/API in unit tests — tests cover parsing and selection logic with constructed data
- `config.toml` is the single source of user configuration; defaults live in `config.py._DEFAULTS`
- IST (UTC+5:30) is used for "yesterday" date calculation since SonyLiv is an Indian platform
