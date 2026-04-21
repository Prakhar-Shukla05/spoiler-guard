"""Tests for CLI utilities."""

from datetime import datetime, timedelta, timezone
from unittest.mock import patch

from spoiler_guard.cli import IST, format_duration, main, open_in_browser


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
    def test_macos_calls_open_a(self):
        with (
            patch("spoiler_guard.cli.PLATFORM", "macos"),
            patch("spoiler_guard.cli.BROWSER_NAME", "Firefox"),
            patch("spoiler_guard.cli.subprocess.run") as mock_run,
        ):
            open_in_browser("https://example.com")
            mock_run.assert_called_once_with(
                ["open", "-a", "Firefox", "https://example.com"],
                check=True,
            )

    def test_windows_calls_cmd_start(self):
        with (
            patch("spoiler_guard.cli.PLATFORM", "windows"),
            patch("spoiler_guard.cli.BROWSER_NAME", "chrome"),
            patch("spoiler_guard.cli.subprocess.run") as mock_run,
        ):
            open_in_browser("https://example.com")
            mock_run.assert_called_once_with(
                ["cmd", "/c", "start", "", "chrome", "https://example.com"],
                check=True,
            )

    def test_linux_calls_browser_directly(self):
        with (
            patch("spoiler_guard.cli.PLATFORM", "linux"),
            patch("spoiler_guard.cli.BROWSER_NAME", "google-chrome"),
            patch("spoiler_guard.cli.subprocess.run") as mock_run,
        ):
            open_in_browser("https://example.com")
            mock_run.assert_called_once_with(
                ["google-chrome", "https://example.com"],
                check=True,
            )

    def test_linux_falls_back_to_xdg_open(self):
        with (
            patch("spoiler_guard.cli.PLATFORM", "linux"),
            patch("spoiler_guard.cli.BROWSER_NAME", ""),
            patch("spoiler_guard.cli.subprocess.run") as mock_run,
        ):
            open_in_browser("https://example.com")
            mock_run.assert_called_once_with(
                ["xdg-open", "https://example.com"],
                check=True,
            )

    def test_unknown_platform_uses_webbrowser(self):
        with (
            patch("spoiler_guard.cli.PLATFORM", "freebsd"),
            patch("spoiler_guard.cli.subprocess.run") as mock_run,
            patch("spoiler_guard.cli.webbrowser.open") as mock_wb,
        ):
            open_in_browser("https://example.com")
            mock_run.assert_not_called()
            mock_wb.assert_called_once_with("https://example.com")

class TestDefaultDate:
    def test_defaults_to_today_ist(self):
        fake_now = datetime(2026, 4, 15, 2, 30, tzinfo=IST)
        with (
            patch("spoiler_guard.cli.datetime") as mock_dt,
            patch("spoiler_guard.cli.get_token", return_value="tok"),
            patch("spoiler_guard.cli.fetch_ucl_content", return_value=[]),
            patch("spoiler_guard.cli.sys.exit") as mock_exit,
            patch("spoiler_guard.cli.sys.argv", ["sonyliv"]),
        ):
            mock_dt.now.return_value = fake_now
            mock_dt.strptime = datetime.strptime
            mock_exit.side_effect = SystemExit
            try:
                main()
            except SystemExit:
                pass
            mock_dt.now.assert_called_once_with(IST)


class TestOpenInBrowser:
    def test_falls_back_to_webbrowser_on_error(self):
        with (
            patch(
                "spoiler_guard.cli.subprocess.run",
                side_effect=FileNotFoundError,
            ),
            patch("spoiler_guard.cli.webbrowser.open") as mock_wb,
        ):
            open_in_browser("https://example.com")
            mock_wb.assert_called_once_with("https://example.com")
