"""Tests for CLI utilities."""

from unittest.mock import patch

from sonyliv_util.cli import format_duration, open_in_browser


class TestFormatDuration:
    def test_seconds_only(self):
        assert format_duration(45) == "0m 45s"

    def test_minutes_and_seconds(self):
        assert format_duration(507) == "8m 27s"

    def test_hours(self):
        assert format_duration(5857) == "1h 37m"

    def test_exact_hour(self):
        assert format_duration(3600) == "1h 0m"

    def test_zero(self):
        assert format_duration(0) == "0m 0s"

    def test_large_duration(self):
        assert format_duration(7200) == "2h 0m"


class TestOpenInBrowser:
    def test_calls_open_with_configured_browser(self):
        with (
            patch("sonyliv_util.cli.BROWSER_NAME", "Firefox"),
            patch("sonyliv_util.cli.subprocess.run") as mock_run,
        ):
            open_in_browser("https://example.com")
            mock_run.assert_called_once_with(
                ["open", "-a", "Firefox", "https://example.com"],
                check=True,
            )

    def test_falls_back_to_webbrowser_on_error(self):
        with (
            patch(
                "sonyliv_util.cli.subprocess.run",
                side_effect=FileNotFoundError,
            ),
            patch("sonyliv_util.cli.webbrowser.open") as mock_wb,
        ):
            open_in_browser("https://example.com")
            mock_wb.assert_called_once_with("https://example.com")
