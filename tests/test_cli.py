"""Tests for SonyLiv CLI entry point."""

from datetime import datetime
from unittest.mock import patch

from spoiler_guard.common import IST
from spoiler_guard.cli import main


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
