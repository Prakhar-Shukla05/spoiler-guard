"""Tests for the SonyLiv API client."""

import json
from unittest.mock import MagicMock, patch
from urllib.request import Request

from sonyliv_util.api import (
    API_BASE,
    api_get,
    fetch_ucl_content,
    get_token,
)
from sonyliv_util.config import TOURNAMENT_ID


def _mock_urlopen(response_data):
    """Create a mock urlopen context manager returning given JSON data."""
    mock_resp = MagicMock()
    mock_resp.read.return_value = json.dumps(response_data).encode()
    mock_resp.__enter__ = lambda s: s
    mock_resp.__exit__ = MagicMock(return_value=False)
    return mock_resp


class TestApiGet:
    def test_builds_url_without_params(self):
        mock_resp = _mock_urlopen({"ok": True})
        with patch("sonyliv_util.api.urlopen", return_value=mock_resp) as mock_open:
            result = api_get("1.4/A/ENG/WEB/ALL/GETTOKEN")

            called_req = mock_open.call_args[0][0]
            assert isinstance(called_req, Request)
            assert called_req.full_url == f"{API_BASE}/1.4/A/ENG/WEB/ALL/GETTOKEN"
            assert result == {"ok": True}

    def test_builds_url_with_params(self):
        mock_resp = _mock_urlopen({"items": []})
        with patch("sonyliv_util.api.urlopen", return_value=mock_resp) as mock_open:
            api_get("1.4/R/ENG/WEB/IN/TRAY/SEARCH/VOD", params={"from": "0", "to": "9"})

            called_req = mock_open.call_args[0][0]
            assert "from=0" in called_req.full_url
            assert "to=9" in called_req.full_url

    def test_includes_security_token_header(self):
        mock_resp = _mock_urlopen({})
        with patch("sonyliv_util.api.urlopen", return_value=mock_resp) as mock_open:
            api_get("some/path", token="my-jwt-token")

            called_req = mock_open.call_args[0][0]
            assert called_req.get_header("Security_token") == "my-jwt-token"

    def test_omits_security_token_when_none(self):
        mock_resp = _mock_urlopen({})
        with patch("sonyliv_util.api.urlopen", return_value=mock_resp) as mock_open:
            api_get("some/path")

            called_req = mock_open.call_args[0][0]
            assert "Security_token" not in called_req.headers


class TestGetToken:
    def test_returns_result_obj(self):
        mock_resp = _mock_urlopen({"resultObj": "fake-jwt-token-123"})
        with patch("sonyliv_util.api.urlopen", return_value=mock_resp):
            token = get_token()
            assert token == "fake-jwt-token-123"


class TestFetchUclContent:
    def test_returns_containers(self):
        mock_resp = _mock_urlopen({
            "resultObj": {
                "total": 1,
                "containers": [{"id": 123, "metadata": {"episodeTitle": "Test"}}],
            }
        })
        with patch("sonyliv_util.api.urlopen", return_value=mock_resp):
            items = fetch_ucl_content("token123")
            assert len(items) == 1
            assert items[0]["id"] == 123

    def test_includes_subtype_filter_when_provided(self):
        mock_resp = _mock_urlopen({"resultObj": {"containers": []}})
        with patch("sonyliv_util.api.urlopen", return_value=mock_resp) as mock_open:
            fetch_ucl_content("token", subtype="HIGHLIGHTS")

            called_req = mock_open.call_args[0][0]
            assert "filter_objectSubtype=HIGHLIGHTS" in called_req.full_url

    def test_omits_subtype_filter_when_none(self):
        mock_resp = _mock_urlopen({"resultObj": {"containers": []}})
        with patch("sonyliv_util.api.urlopen", return_value=mock_resp) as mock_open:
            fetch_ucl_content("token", subtype=None)

            called_req = mock_open.call_args[0][0]
            assert "filter_objectSubtype" not in called_req.full_url

    def test_caps_count_at_50(self):
        mock_resp = _mock_urlopen({"resultObj": {"containers": []}})
        with patch("sonyliv_util.api.urlopen", return_value=mock_resp) as mock_open:
            fetch_ucl_content("token", count=100)

            called_req = mock_open.call_args[0][0]
            assert "to=49" in called_req.full_url

    def test_includes_tournament_id(self):
        mock_resp = _mock_urlopen({"resultObj": {"containers": []}})
        with patch("sonyliv_util.api.urlopen", return_value=mock_resp) as mock_open:
            fetch_ucl_content("token")

            called_req = mock_open.call_args[0][0]
            assert f"filter_parentId={TOURNAMENT_ID}" in called_req.full_url

    def test_passes_offset_to_from_and_to(self):
        mock_resp = _mock_urlopen({"resultObj": {"containers": []}})
        with patch("sonyliv_util.api.urlopen", return_value=mock_resp) as mock_open:
            fetch_ucl_content("token", count=50, offset=100)

            called_req = mock_open.call_args[0][0]
            assert "from=100" in called_req.full_url
            assert "to=149" in called_req.full_url

    def test_returns_empty_list_on_missing_containers(self):
        mock_resp = _mock_urlopen({"resultObj": {}})
        with patch("sonyliv_util.api.urlopen", return_value=mock_resp):
            items = fetch_ucl_content("token")
            assert items == []
