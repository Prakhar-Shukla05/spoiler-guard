"""Tests for IPL match parsing and content grouping."""

from datetime import date

from spoiler_guard.ipl_match import (
    build_matches_from_tray,
    build_url,
    is_recent,
    parse_broadcast_date,
    parse_teams,
)


class TestParseTeams:
    def test_highlights_format(self):
        home, away = parse_teams("SRH vs DC: Highlights")
        assert home == "SRH"
        assert away == "DC"

    def test_innings_format(self):
        home, away = parse_teams("GT vs MI: 1st Inns, Highlights")
        assert home == "GT"
        assert away == "MI"

    def test_full_team_names(self):
        home, away = parse_teams("Chennai Super Kings vs Mumbai Indians: Highlights")
        assert home == "Chennai Super Kings"
        assert away == "Mumbai Indians"

    def test_empty_string(self):
        assert parse_teams("") == (None, None)

    def test_none(self):
        assert parse_teams(None) == (None, None)

    def test_no_colon(self):
        assert parse_teams("SRH vs DC") == (None, None)


class TestParseBroadcastDate:
    def test_epoch_timestamp(self):
        item = {"broadCastDate": 1776609600}
        d = parse_broadcast_date(item)
        assert d is not None

    def test_missing_field(self):
        assert parse_broadcast_date({}) is None

    def test_zero(self):
        assert parse_broadcast_date({"broadCastDate": 0}) is None


class TestIsRecent:
    def test_today(self):
        today = date(2026, 4, 22)
        assert is_recent(today, today) is True

    def test_yesterday(self):
        today = date(2026, 4, 22)
        assert is_recent(date(2026, 4, 21), today) is True

    def test_two_days_ago(self):
        today = date(2026, 4, 22)
        assert is_recent(date(2026, 4, 20), today) is False

    def test_none(self):
        assert is_recent(None, date(2026, 4, 22)) is False


def _make_item(title, content_id=1, duration=500, broadcast_ts=1776868800,
               content_type="SPORT_MATCH_HIGHLIGHTS"):
    """Helper — broadcast_ts default is ~2026-04-22 IST."""
    return {
        "title": title,
        "contentId": content_id,
        "duration": duration,
        "broadCastDate": broadcast_ts,
        "contentType": content_type,
    }


class TestBuildMatchesFromTray:
    def test_builds_match(self):
        items = [
            _make_item("SRH vs DC: Highlights", content_id=1, duration=900),
        ]
        matches = build_matches_from_tray(items, date(2026, 4, 22))
        assert len(matches) == 1
        assert matches[0]["home"] == "SRH"
        assert matches[0]["away"] == "DC"
        assert matches[0]["content_id"] == 1
        assert matches[0]["duration"] == 900

    def test_skips_innings_highlights(self):
        items = [
            _make_item("SRH vs DC: Highlights", content_id=1),
            _make_item("SRH vs DC: 1st Inns, Highlights", content_id=2,
                       content_type="SPORT"),
        ]
        matches = build_matches_from_tray(items, date(2026, 4, 22))
        assert len(matches) == 1
        assert matches[0]["content_id"] == 1

    def test_filters_by_date(self):
        items = [
            _make_item("SRH vs DC: Highlights", broadcast_ts=1776868800),
        ]
        matches = build_matches_from_tray(items, date(2026, 4, 25))
        assert len(matches) == 0

    def test_multiple_matches(self):
        items = [
            _make_item("SRH vs DC: Highlights", content_id=1),
            _make_item("GT vs MI: Highlights", content_id=2),
        ]
        matches = build_matches_from_tray(items, date(2026, 4, 22))
        assert len(matches) == 2

    def test_empty_items(self):
        assert build_matches_from_tray([], date(2026, 4, 22)) == []


class TestBuildUrl:
    def test_includes_content_id(self):
        url = build_url(1540066390)
        assert "1540066390" in url

    def test_includes_cricket_path(self):
        url = build_url(123)
        assert "/cricket/" in url

    def test_starts_with_https(self):
        url = build_url(123)
        assert url.startswith("https://www.hotstar.com/")
