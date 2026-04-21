"""Tests for Hotstar match parsing and content grouping."""

from datetime import date

from spoiler_guard.hotstar_match import (
    build_matches_from_replays,
    build_url,
    extract_highlights_from_detail,
    is_recent,
    parse_broadcast_date,
    parse_teams_from_highlights,
    parse_teams_from_replay,
)


class TestParseTeamsFromReplay:
    def test_standard_format(self):
        home, away = parse_teams_from_replay("Crystal Palace vs West Ham: Replay")
        assert home == "Crystal Palace"
        assert away == "West Ham"

    def test_multi_word_teams(self):
        home, away = parse_teams_from_replay("Manchester City vs Arsenal: Replay")
        assert home == "Manchester City"
        assert away == "Arsenal"

    def test_leading_whitespace(self):
        home, away = parse_teams_from_replay("  Arsenal vs Chelsea: Replay")
        assert home == "Arsenal"
        assert away == "Chelsea"

    def test_empty_string(self):
        assert parse_teams_from_replay("") == (None, None)

    def test_none(self):
        assert parse_teams_from_replay(None) == (None, None)

    def test_non_replay_title(self):
        assert parse_teams_from_replay("Arsenal vs Chelsea - Highlights") == (None, None)

    def test_highlights_title(self):
        assert parse_teams_from_replay("Manchester City 2-1 Arsenal") == (None, None)


class TestParseTeamsFromHighlights:
    def test_score_format(self):
        home, away = parse_teams_from_highlights("Manchester City 2-1 Arsenal")
        assert home == "Manchester City"
        assert away == "Arsenal"

    def test_high_scores(self):
        home, away = parse_teams_from_highlights("Aston Villa 4-3 Sunderland")
        assert home == "Aston Villa"
        assert away == "Sunderland"

    def test_nil_nil(self):
        home, away = parse_teams_from_highlights("Chelsea 0-0 Liverpool")
        assert home == "Chelsea"
        assert away == "Liverpool"

    def test_vs_format_fallback(self):
        home, away = parse_teams_from_highlights("Arsenal vs Chelsea")
        assert home == "Arsenal"
        assert away == "Chelsea"

    def test_empty_string(self):
        assert parse_teams_from_highlights("") == (None, None)

    def test_none(self):
        assert parse_teams_from_highlights(None) == (None, None)

    def test_no_teams(self):
        assert parse_teams_from_highlights("Top Goals Of The Week") == (None, None)


class TestParseBroadcastDate:
    def test_epoch_timestamp(self):
        # 2026-04-19 ~20:10 IST
        item = {"broadCastDate": 1776609600}
        d = parse_broadcast_date(item)
        assert d is not None

    def test_missing_field(self):
        assert parse_broadcast_date({}) is None

    def test_zero_timestamp(self):
        assert parse_broadcast_date({"broadCastDate": 0}) is None


class TestIsRecent:
    def test_today(self):
        today = date(2026, 4, 21)
        assert is_recent(today, today) is True

    def test_yesterday(self):
        today = date(2026, 4, 21)
        assert is_recent(date(2026, 4, 20), today) is True

    def test_two_days_ago(self):
        today = date(2026, 4, 21)
        assert is_recent(date(2026, 4, 19), today) is False

    def test_none_date(self):
        assert is_recent(None, date(2026, 4, 21)) is False


def _make_replay_item(title, content_id=1, duration=8000, broadcast_ts=1776609600, si_match_id="12345"):
    return {
        "title": title,
        "contentId": content_id,
        "duration": duration,
        "broadCastDate": broadcast_ts,
        "siMatchId": si_match_id,
    }


class TestBuildMatchesFromReplays:
    def test_builds_match_with_replay_option(self):
        # broadCastDate 1776609600 ≈ 2026-04-19 in IST
        items = [_make_replay_item("Arsenal vs Chelsea: Replay", content_id=100)]
        matches = build_matches_from_replays(items, date(2026, 4, 19))
        assert len(matches) == 1
        assert matches[0]["home"] == "Arsenal"
        assert matches[0]["away"] == "Chelsea"
        assert matches[0]["options"][0]["content_type"] == "full_match"
        assert matches[0]["options"][0]["content_id"] == 100

    def test_filters_by_date(self):
        items = [_make_replay_item("Arsenal vs Chelsea: Replay", broadcast_ts=1776609600)]
        # Use a date far from the broadcast timestamp
        matches = build_matches_from_replays(items, date(2026, 4, 25))
        assert len(matches) == 0

    def test_includes_yesterday(self):
        items = [_make_replay_item("Arsenal vs Chelsea: Replay", broadcast_ts=1776609600)]
        item_date = parse_broadcast_date(items[0])
        # Use the day after the broadcast date
        from datetime import timedelta
        tomorrow = item_date + timedelta(days=1)
        matches = build_matches_from_replays(items, tomorrow)
        assert len(matches) == 1

    def test_skips_non_replay_titles(self):
        items = [_make_replay_item("Manchester City 2-1 Arsenal")]
        matches = build_matches_from_replays(items, date(2026, 4, 19))
        assert len(matches) == 0

    def test_preserves_si_match_id(self):
        items = [_make_replay_item("Arsenal vs Chelsea: Replay", si_match_id="999")]
        matches = build_matches_from_replays(items, date(2026, 4, 19))
        assert matches[0]["si_match_id"] == "999"

    def test_empty_items(self):
        assert build_matches_from_replays([], date(2026, 4, 21)) == []


class TestExtractHighlightsFromDetail:
    def test_extracts_highlights(self):
        detail = {
            "trays": {
                "items": [
                    {
                        "title": "Recent From Match",
                        "assets": {
                            "items": [
                                {
                                    "title": "Man City 2-1 Arsenal",
                                    "contentId": 200,
                                    "contentType": "SPORT_MATCH_HIGHLIGHTS",
                                    "highlight": True,
                                    "duration": 430,
                                },
                            ],
                        },
                    },
                ],
            },
        }
        highlights = extract_highlights_from_detail(detail)
        assert len(highlights) == 1
        assert highlights[0]["content_type"] == "highlights"
        assert highlights[0]["content_id"] == 200
        assert highlights[0]["duration"] == 430

    def test_skips_non_highlights(self):
        detail = {
            "trays": {
                "items": [
                    {
                        "title": "Popular",
                        "assets": {
                            "items": [
                                {
                                    "title": "Preview",
                                    "contentId": 300,
                                    "contentType": "SPORT",
                                    "highlight": False,
                                    "duration": 90,
                                },
                            ],
                        },
                    },
                ],
            },
        }
        assert extract_highlights_from_detail(detail) == []

    def test_empty_trays(self):
        assert extract_highlights_from_detail({}) == []
        assert extract_highlights_from_detail({"trays": {}}) == []
        assert extract_highlights_from_detail({"trays": {"items": []}}) == []


class TestBuildUrl:
    def test_includes_content_id(self):
        url = build_url(1234567890)
        assert "1234567890" in url

    def test_starts_with_https(self):
        url = build_url(123)
        assert url.startswith("https://www.hotstar.com/")

    def test_includes_sports_path(self):
        url = build_url(123)
        assert "/sports/" in url
