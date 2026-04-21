"""Hotstar API client for fetching Premier League content."""

import hashlib
import hmac
import json
import time
from urllib.request import Request, urlopen

API_BASE = "https://api.hotstar.com/o/v1"

_AKAMAI_KEY = b"\x05\xfc\x1a\x01\xca\xc9\x4b\xc4\x12\xfc\x53\x12\x07\x75\xf9\xee"


def generate_auth(timestamp=None):
    """Generate the HMAC-SHA256 hotstarauth header value.

    Uses the Akamai token authentication scheme. The key is a client-side
    constant (not a secret) used by all Hotstar clients.
    """
    st = timestamp or int(time.time())
    exp = st + 6000
    auth = f"st={st}~exp={exp}~acl=/*"
    digest = hmac.new(_AKAMAI_KEY, auth.encode(), hashlib.sha256).hexdigest()
    return f"{auth}~hmac={digest}"


def hotstar_api_get(path, user_token, params=None):
    """Make an authenticated GET request to the Hotstar v1 API."""
    url = f"{API_BASE}/{path}"
    if params:
        query = "&".join(f"{k}={v}" for k, v in params.items())
        url = f"{url}?{query}"

    headers = {
        "User-Agent": "Mozilla/5.0",
        "x-country-code": "IN",
        "x-platform-code": "PCTV",
        "hotstarauth": generate_auth(),
        "x-hs-usertoken": user_token,
    }

    req = Request(url, headers=headers)
    with urlopen(req, timeout=15) as resp:
        return json.loads(resp.read().decode())


def fetch_tray_content(user_token, tray_id, size=20, offset=0):
    """Fetch content from a Hotstar editorial tray.

    Args:
        user_token: The userUP cookie value from config.
        tray_id: Editorial tray ID (e.g. "1271442198" for PL replays).
        size: Items per page.
        offset: Starting index for pagination.

    Returns:
        List of content items from the tray.
    """
    data = hotstar_api_get(
        "tray/find",
        user_token=user_token,
        params={"uqId": str(tray_id), "offset": str(offset), "size": str(size)},
    )
    return (
        data.get("body", {})
        .get("results", {})
        .get("assets", {})
        .get("items", [])
    )


def fetch_match_detail(user_token, content_id, si_match_id):
    """Fetch match detail including related trays (highlights, etc.).

    The match detail endpoint returns the match item plus trays of related
    content like highlights.

    Args:
        user_token: The userUP cookie value.
        content_id: The match content ID.
        si_match_id: The sports intelligence match ID.

    Returns:
        Dict with 'item' (match metadata) and 'trays' (related content).
    """
    data = hotstar_api_get(
        "match/detail",
        user_token=user_token,
        params={
            "id": str(content_id),
            "contentId": str(content_id),
            "siMatchId": str(si_match_id),
            "offset": "0",
            "size": "20",
            "tao": "0",
            "tas": "5",
        },
    )
    return data.get("body", {}).get("results", {})
