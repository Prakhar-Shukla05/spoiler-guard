"""Tests for match parsing and content selection logic."""

from datetime import date

from spoiler_guard.match import (
    build_url,
    find_matches,
    is_favourite_team_match,
    parse_date_from_title,
    parse_teams,
    select_best_content,
)


class TestParseTeams:
    def test_standard_title(self):
        home, away = parse_teams(
            "PSG vs Liverpool - Quarter-Final - Leg 1 - Highlights - 9 Apr 2026"
        )
        assert home == "PSG"
        assert away == "Liverpool"

    def test_extended_highlights_title(self):
        home, away = parse_teams(
            "Barcelona vs Atletico - Extended Highlights - 9 Apr 2026"
        )
        assert home == "Barcelona"
        assert away == "Atletico"

    def test_replay_title(self):
        home, away = parse_teams(
            "Sporting CP vs Arsenal - Quarter-Final - Leg 1 - Replay - 8 Mar 2026"
        )
        assert home == "Sporting CP"
        assert away == "Arsenal"

    def test_leading_whitespace(self):
        home, away = parse_teams(
            " Barcelona vs Atletico - Quarter-Final - Leg 1 - Highlights - 9 Apr 2026"
        )
        assert home == "Barcelona"
        assert away == "Atletico"

    def test_no_vs_returns_none(self):
        home, away = parse_teams("Top Goals Of The Week - Quarter-Final - Leg 1")
        assert home is None
        assert away is None

    def test_empty_string(self):
        home, away = parse_teams("")
        assert home is None
        assert away is None

    def test_multi_word_team_names(self):
        home, away = parse_teams(
            "Real Madrid vs Bayern Munich - Highlights - 8 Apr 2026"
        )
        assert home == "Real Madrid"
        assert away == "Bayern Munich"


class TestParseDateFromTitle:
    def test_single_digit_day(self):
        d = parse_date_from_title(
            "PSG vs Liverpool - Highlights - 9 Apr 2026"
        )
        assert d == date(2026, 4, 9)

    def test_double_digit_day(self):
        d = parse_date_from_title(
            "Sporting CP vs Arsenal - Replay - 08 Mar 2026"
        )
        assert d == date(2026, 3, 8)

    def test_no_date_returns_none(self):
        d = parse_date_from_title("Top Goals Of The Week - Quarter-Final")
        assert d is None

    def test_empty_string_returns_none(self):
        d = parse_date_from_title("")
        assert d is None

    def test_trailing_whitespace(self):
        d = parse_date_from_title("PSG vs Liverpool - Highlights - 9 Apr 2026  ")
        assert d == date(2026, 4, 9)


class TestIsFavouriteTeamMatch:
    def test_chelsea_home(self):
        assert is_favourite_team_match("Chelsea", "Real Madrid") is True

    def test_chelsea_away(self):
        assert is_favourite_team_match("Bayern", "Chelsea") is True

    def test_case_insensitive(self):
        assert is_favourite_team_match("CHELSEA", "PSG") is True

    def test_not_chelsea(self):
        assert is_favourite_team_match("PSG", "Liverpool") is False

    def test_none_home(self):
        assert is_favourite_team_match(None, "Chelsea") is False

    def test_none_away(self):
        assert is_favourite_team_match("Chelsea", None) is False

    def test_chelsea_in_longer_name(self):
        assert is_favourite_team_match("Chelsea FC", "Arsenal") is True


class TestBuildUrl:
    def test_includes_content_id(self):
        url = build_url(1090525436)
        assert "1090525436" in url

    def test_includes_watch_true(self):
        url = build_url(123)
        assert "?watch=true" in url

    def test_includes_tournament_id(self):
        url = build_url(123)
        assert "1700000773" in url

    def test_starts_with_https(self):
        url = build_url(123)
        assert url.startswith("https://www.sonyliv.com/")


def _make_item(episode_title, subtype, content_id=1, duration=500):
    """Helper to create a mock SonyLiv API content item."""
    return {
        "id": content_id,
        "metadata": {
            "episodeTitle": episode_title,
            "objectSubtype": subtype,
            "duration": duration,
        },
    }


class TestFindMatches:
    def test_groups_by_team_pair(self):
        items = [
            _make_item(
                "PSG vs Liverpool - Highlights - 9 Apr 2026",
                "HIGHLIGHTS", content_id=1, duration=500,
            ),
            _make_item(
                "PSG vs Liverpool - Extended Highlights - 9 Apr 2026",
                "HIGHLIGHTS", content_id=2, duration=1500,
            ),
        ]
        matches = find_matches(items, date(2026, 4, 9))
        assert ("PSG", "Liverpool") in matches
        assert len(matches[("PSG", "Liverpool")]) == 2

    def test_filters_by_date(self):
        items = [
            _make_item(
                "PSG vs Liverpool - Highlights - 9 Apr 2026",
                "HIGHLIGHTS",
            ),
            _make_item(
                "Barcelona vs Atletico - Highlights - 8 Apr 2026",
                "HIGHLIGHTS",
            ),
        ]
        matches = find_matches(items, date(2026, 4, 9))
        assert len(matches) == 1
        assert ("PSG", "Liverpool") in matches

    def test_classifies_extended_highlights(self):
        items = [
            _make_item(
                "PSG vs Liverpool - Extended Highlights - 9 Apr 2026",
                "HIGHLIGHTS", content_id=1,
            ),
        ]
        matches = find_matches(items, date(2026, 4, 9))
        assert matches[("PSG", "Liverpool")][0]["content_type"] == "extended_highlights"

    def test_classifies_regular_highlights(self):
        items = [
            _make_item(
                "PSG vs Liverpool - Highlights - 9 Apr 2026",
                "HIGHLIGHTS",
            ),
        ]
        matches = find_matches(items, date(2026, 4, 9))
        assert matches[("PSG", "Liverpool")][0]["content_type"] == "highlights"

    def test_classifies_full_match(self):
        items = [
            _make_item(
                "PSG vs Liverpool - Replay - 9 Apr 2026",
                "FULL_MATCH", duration=6000,
            ),
        ]
        matches = find_matches(items, date(2026, 4, 9))
        assert matches[("PSG", "Liverpool")][0]["content_type"] == "full_match"

    def test_skips_sports_clips(self):
        items = [
            _make_item(
                "Liverpool vs PSG - Preview - 9 Apr 2026",
                "SPORTS_CLIPS",
            ),
        ]
        matches = find_matches(items, date(2026, 4, 9))
        assert len(matches) == 0

    def test_skips_items_without_team_names(self):
        items = [
            _make_item(
                "Top Goals Of The Week - 9 Apr 2026",
                "HIGHLIGHTS",
            ),
        ]
        matches = find_matches(items, date(2026, 4, 9))
        assert len(matches) == 0

    def test_empty_items(self):
        matches = find_matches([], date(2026, 4, 9))
        assert matches == {}


class TestSelectBestContent:
    def test_prefers_extended_over_regular(self):
        items = [
            {"content_type": "highlights", "duration": 500, "content_id": 1},
            {"content_type": "extended_highlights", "duration": 1500, "content_id": 2},
        ]
        best = select_best_content(items, is_favourite=False)
        assert best["content_type"] == "extended_highlights"

    def test_falls_back_to_highlights(self):
        items = [
            {"content_type": "highlights", "duration": 500, "content_id": 1},
        ]
        best = select_best_content(items, is_favourite=False)
        assert best["content_type"] == "highlights"

    def test_chelsea_prefers_full_match(self):
        items = [
            {"content_type": "highlights", "duration": 500, "content_id": 1},
            {"content_type": "extended_highlights", "duration": 1500, "content_id": 2},
            {"content_type": "full_match", "duration": 6000, "content_id": 3},
        ]
        best = select_best_content(items, is_favourite=True)
        assert best["content_type"] == "full_match"

    def test_chelsea_falls_back_to_extended(self):
        items = [
            {"content_type": "highlights", "duration": 500, "content_id": 1},
            {"content_type": "extended_highlights", "duration": 1500, "content_id": 2},
        ]
        best = select_best_content(items, is_favourite=True)
        assert best["content_type"] == "extended_highlights"

    def test_non_chelsea_ignores_full_match(self):
        items = [
            {"content_type": "full_match", "duration": 6000, "content_id": 1},
        ]
        best = select_best_content(items, is_favourite=False)
        assert best is None

    def test_picks_longest_when_multiple(self):
        items = [
            {"content_type": "highlights", "duration": 400, "content_id": 1},
            {"content_type": "highlights", "duration": 600, "content_id": 2},
        ]
        best = select_best_content(items, is_favourite=False)
        assert best["content_id"] == 2

    def test_returns_none_for_empty_list(self):
        best = select_best_content([], is_favourite=False)
        assert best is None
