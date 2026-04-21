"""Tests for shared utilities."""

from unittest.mock import patch

from spoiler_guard.common import format_duration, open_in_browser


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
            patch("spoiler_guard.common.PLATFORM", "macos"),
            patch("spoiler_guard.common.BROWSER_NAME", "Firefox"),
            patch("spoiler_guard.common.subprocess.run") as mock_run,
        ):
            open_in_browser("https://example.com")
            mock_run.assert_called_once_with(
                ["open", "-a", "Firefox", "https://example.com"],
                check=True,
            )

    def test_windows_calls_cmd_start(self):
        with (
            patch("spoiler_guard.common.PLATFORM", "windows"),
            patch("spoiler_guard.common.BROWSER_NAME", "chrome"),
            patch("spoiler_guard.common.subprocess.run") as mock_run,
        ):
            open_in_browser("https://example.com")
            mock_run.assert_called_once_with(
                ["cmd", "/c", "start", "", "chrome", "https://example.com"],
                check=True,
            )

    def test_linux_calls_browser_directly(self):
        with (
            patch("spoiler_guard.common.PLATFORM", "linux"),
            patch("spoiler_guard.common.BROWSER_NAME", "google-chrome"),
            patch("spoiler_guard.common.subprocess.run") as mock_run,
        ):
            open_in_browser("https://example.com")
            mock_run.assert_called_once_with(
                ["google-chrome", "https://example.com"],
                check=True,
            )

    def test_linux_falls_back_to_xdg_open(self):
        with (
            patch("spoiler_guard.common.PLATFORM", "linux"),
            patch("spoiler_guard.common.BROWSER_NAME", ""),
            patch("spoiler_guard.common.subprocess.run") as mock_run,
        ):
            open_in_browser("https://example.com")
            mock_run.assert_called_once_with(
                ["xdg-open", "https://example.com"],
                check=True,
            )

    def test_unknown_platform_uses_webbrowser(self):
        with (
            patch("spoiler_guard.common.PLATFORM", "freebsd"),
            patch("spoiler_guard.common.subprocess.run") as mock_run,
            patch("spoiler_guard.common.webbrowser.open") as mock_wb,
        ):
            open_in_browser("https://example.com")
            mock_run.assert_not_called()
            mock_wb.assert_called_once_with("https://example.com")

    def test_falls_back_to_webbrowser_on_error(self):
        with (
            patch(
                "spoiler_guard.common.subprocess.run",
                side_effect=FileNotFoundError,
            ),
            patch("spoiler_guard.common.webbrowser.open") as mock_wb,
        ):
            open_in_browser("https://example.com")
            mock_wb.assert_called_once_with("https://example.com")
