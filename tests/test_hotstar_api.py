"""Tests for Hotstar API client."""

import hashlib
import hmac
import json
from unittest.mock import MagicMock, patch

from spoiler_guard.hotstar_api import (
    API_BASE,
    _AKAMAI_KEY,
    fetch_match_detail,
    fetch_tray_content,
    generate_auth,
    hotstar_api_get,
)


class TestGenerateAuth:
    def test_format(self):
        auth = generate_auth(timestamp=1000000)
        assert auth.startswith("st=1000000~exp=1006000~acl=/*~hmac=")

    def test_hmac_is_valid_sha256(self):
        auth = generate_auth(timestamp=1000000)
        parts = dict(p.split("=", 1) for p in auth.split("~"))
        assert len(parts["hmac"]) == 64

    def test_hmac_matches_expected(self):
        ts = 1000000
        auth = generate_auth(timestamp=ts)
        message = f"st={ts}~exp={ts + 6000}~acl=/*"
        expected = hmac.new(_AKAMAI_KEY, message.encode(), hashlib.sha256).hexdigest()
        assert auth.endswith(expected)

    def test_uses_current_time_by_default(self):
        with patch("spoiler_guard.hotstar_api.time.time", return_value=2000000.0):
            auth = generate_auth()
        assert auth.startswith("st=2000000~exp=2006000~")


def _mock_urlopen(response_data):
    """Create a mock urlopen context manager returning JSON data."""
    mock_resp = MagicMock()
    mock_resp.read.return_value = json.dumps(response_data).encode()
    mock_resp.__enter__ = lambda s: s
    mock_resp.__exit__ = MagicMock(return_value=False)
    return mock_resp


class TestHotstarApiGet:
    def test_builds_url_with_params(self):
        with patch("spoiler_guard.hotstar_api.urlopen", return_value=_mock_urlopen({})) as mock:
            hotstar_api_get("tray/find", "tok", params={"uqId": "123", "size": "20"})
            called_req = mock.call_args[0][0]
            assert "tray/find?uqId=123&size=20" in called_req.full_url

    def test_builds_url_without_params(self):
        with patch("spoiler_guard.hotstar_api.urlopen", return_value=_mock_urlopen({})) as mock:
            hotstar_api_get("some/path", "tok")
            called_req = mock.call_args[0][0]
            assert called_req.full_url == f"{API_BASE}/some/path"

    def test_sends_required_headers(self):
        with patch("spoiler_guard.hotstar_api.urlopen", return_value=_mock_urlopen({})) as mock:
            hotstar_api_get("path", "my-token-123")
            called_req = mock.call_args[0][0]
            assert called_req.get_header("X-country-code") == "IN"
            assert called_req.get_header("X-platform-code") == "PCTV"
            assert called_req.get_header("X-hs-usertoken") == "my-token-123"
            assert called_req.get_header("Hotstarauth").startswith("st=")

    def test_returns_parsed_json(self):
        data = {"body": {"results": {}}}
        with patch("spoiler_guard.hotstar_api.urlopen", return_value=_mock_urlopen(data)):
            result = hotstar_api_get("path", "tok")
        assert result == data


class TestFetchTrayContent:
    def test_passes_uqid_and_pagination(self):
        response = {"body": {"results": {"assets": {"items": []}}}}
        with patch("spoiler_guard.hotstar_api.urlopen", return_value=_mock_urlopen(response)) as mock:
            fetch_tray_content("tok", "1271442198", size=20, offset=10)
            called_req = mock.call_args[0][0]
            assert "uqId=1271442198" in called_req.full_url
            assert "offset=10" in called_req.full_url
            assert "size=20" in called_req.full_url

    def test_returns_items_list(self):
        items = [{"contentId": 1}, {"contentId": 2}]
        response = {"body": {"results": {"assets": {"items": items}}}}
        with patch("spoiler_guard.hotstar_api.urlopen", return_value=_mock_urlopen(response)):
            result = fetch_tray_content("tok", "123")
        assert result == items

    def test_returns_empty_list_on_missing_keys(self):
        with patch("spoiler_guard.hotstar_api.urlopen", return_value=_mock_urlopen({})):
            result = fetch_tray_content("tok", "123")
        assert result == []


class TestFetchMatchDetail:
    def test_passes_match_params(self):
        response = {"body": {"results": {}}}
        with patch("spoiler_guard.hotstar_api.urlopen", return_value=_mock_urlopen(response)) as mock:
            fetch_match_detail("tok", 12345, "67890")
            called_req = mock.call_args[0][0]
            assert "id=12345" in called_req.full_url
            assert "contentId=12345" in called_req.full_url
            assert "siMatchId=67890" in called_req.full_url

    def test_returns_results(self):
        results = {"item": {"title": "Test"}, "trays": {"items": []}}
        response = {"body": {"results": results}}
        with patch("spoiler_guard.hotstar_api.urlopen", return_value=_mock_urlopen(response)):
            result = fetch_match_detail("tok", 1, "1")
        assert result == results
