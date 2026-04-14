"""SonyLiv API client for fetching UCL content metadata."""

import json
from urllib.request import Request, urlopen

from .config import TOURNAMENT_ID

API_BASE = "https://apiv2.sonyliv.com/AGL"


def api_get(path, token=None, params=None):
    """Make a GET request to the SonyLiv API."""
    url = f"{API_BASE}/{path}"
    if params:
        query = "&".join(f"{k}={v}" for k, v in params.items())
        url = f"{url}?{query}"

    headers = {"User-Agent": "Mozilla/5.0"}
    if token:
        headers["security_token"] = token

    req = Request(url, headers=headers)
    with urlopen(req, timeout=15) as resp:
        return json.loads(resp.read().decode())


def get_token():
    """Get an anonymous session token from SonyLiv.

    SonyLiv requires a security_token header on all API requests. This token
    is freely available — no credentials needed. It expires after ~15 days.
    """
    data = api_get("1.4/A/ENG/WEB/ALL/GETTOKEN")
    return data["resultObj"]


def fetch_ucl_content(token, subtype=None, count=50, offset=0):
    """Fetch UCL content with pagination support.

    The API caps responses at 50 items per page. The objectSubtype filter
    only works reliably for "HIGHLIGHTS" — other values return unfiltered
    results.

    Args:
        token: Anonymous session token from get_token().
        subtype: Optional content subtype filter (e.g. "HIGHLIGHTS").
        count: Number of items to fetch (max 50 per page).
        offset: Starting index for pagination.
    """
    page_size = min(count, 50)
    params = {
        "filter_parentId": TOURNAMENT_ID,
        "filter_contentType": "VOD",
        "from": str(offset),
        "to": str(offset + page_size - 1),
        "sortOrder": "desc",
        "orderBy": "creationDate",
    }
    if subtype:
        params["filter_objectSubtype"] = subtype

    data = api_get("1.4/R/ENG/WEB/IN/TRAY/SEARCH/VOD", token=token, params=params)
    return data.get("resultObj", {}).get("containers", [])
