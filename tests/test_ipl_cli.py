"""Tests for IPL CLI entry point."""

from datetime import datetime
from unittest.mock import patch

from spoiler_guard.common import IST
from spoiler_guard.ipl_cli import main


class TestIplCli:
    def test_exits_when_no_token(self):
        with (
            patch("spoiler_guard.ipl_cli.HOTSTAR_USER_TOKEN", ""),
            patch("spoiler_guard.ipl_cli.sys.exit") as mock_exit,
            patch("spoiler_guard.ipl_cli.sys.argv", ["ipl"]),
        ):
            mock_exit.side_effect = SystemExit
            try:
                main()
            except SystemExit:
                pass
            mock_exit.assert_called_once_with(1)

    def test_defaults_to_today_ist(self):
        fake_now = datetime(2026, 4, 22, 10, 0, tzinfo=IST)
        with (
            patch("spoiler_guard.ipl_cli.datetime") as mock_dt,
            patch("spoiler_guard.ipl_cli.HOTSTAR_USER_TOKEN", "tok"),
            patch("spoiler_guard.ipl_cli.fetch_tray_content", return_value=[]),
            patch("spoiler_guard.ipl_cli.sys.exit") as mock_exit,
            patch("spoiler_guard.ipl_cli.sys.argv", ["ipl"]),
        ):
            mock_dt.now.return_value = fake_now
            mock_dt.strptime = datetime.strptime
            mock_exit.side_effect = SystemExit
            try:
                main()
            except SystemExit:
                pass
            mock_dt.now.assert_called_once_with(IST)
