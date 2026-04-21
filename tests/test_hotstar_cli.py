"""Tests for Hotstar CLI entry point."""

from datetime import datetime
from unittest.mock import patch

from spoiler_guard.common import IST
from spoiler_guard.hotstar_cli import main


class TestHotstarCli:
    def test_exits_when_no_token(self):
        with (
            patch("spoiler_guard.hotstar_cli.HOTSTAR_USER_TOKEN", ""),
            patch("spoiler_guard.hotstar_cli.sys.exit") as mock_exit,
            patch("spoiler_guard.hotstar_cli.sys.argv", ["hotstar"]),
        ):
            mock_exit.side_effect = SystemExit
            try:
                main()
            except SystemExit:
                pass
            mock_exit.assert_called_once_with(1)

    def test_defaults_to_today_ist(self):
        fake_now = datetime(2026, 4, 21, 10, 0, tzinfo=IST)
        with (
            patch("spoiler_guard.hotstar_cli.datetime") as mock_dt,
            patch("spoiler_guard.hotstar_cli.HOTSTAR_USER_TOKEN", "tok"),
            patch("spoiler_guard.hotstar_cli.fetch_tray_content", return_value=[]),
            patch("spoiler_guard.hotstar_cli.sys.exit") as mock_exit,
            patch("spoiler_guard.hotstar_cli.sys.argv", ["hotstar"]),
        ):
            mock_dt.now.return_value = fake_now
            mock_dt.strptime = datetime.strptime
            mock_exit.side_effect = SystemExit
            try:
                main()
            except SystemExit:
                pass
            mock_dt.now.assert_called_once_with(IST)

    def test_respects_date_argument(self):
        with (
            patch("spoiler_guard.hotstar_cli.HOTSTAR_USER_TOKEN", "tok"),
            patch("spoiler_guard.hotstar_cli.fetch_tray_content", return_value=[]),
            patch("spoiler_guard.hotstar_cli.sys.exit") as mock_exit,
            patch("spoiler_guard.hotstar_cli.sys.argv", ["hotstar", "--date", "2026-04-15"]),
            patch("spoiler_guard.hotstar_cli.datetime") as mock_dt,
        ):
            mock_dt.now.return_value = datetime(2026, 4, 21, 10, 0, tzinfo=IST)
            mock_dt.strptime = datetime.strptime
            mock_exit.side_effect = SystemExit
            try:
                main()
            except SystemExit:
                pass
            # Should exit 0 (no matches found), not 1 (error)
            mock_exit.assert_called_with(0)
