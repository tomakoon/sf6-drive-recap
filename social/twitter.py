"""Post to X/Twitter via API v2 with OAuth 1.0a (stdlib only)."""
from __future__ import annotations

import hashlib
import hmac
import json
import time
import urllib.parse
import uuid

import httpx
from config import (
    TWITTER_CONSUMER_KEY,
    TWITTER_CONSUMER_SECRET,
    TWITTER_ACCESS_TOKEN,
    TWITTER_ACCESS_TOKEN_SECRET,
)

TWITTER_API = "https://api.x.com/2/tweets"


def _percent_encode(s: str) -> str:
    return urllib.parse.quote(str(s), safe="")


def _build_oauth_header(method: str, url: str) -> str:
    """Build OAuth 1.0a Authorization header using HMAC-SHA1."""
    oauth_params = {
        "oauth_consumer_key": TWITTER_CONSUMER_KEY,
        "oauth_nonce": uuid.uuid4().hex,
        "oauth_signature_method": "HMAC-SHA1",
        "oauth_timestamp": str(int(time.time())),
        "oauth_token": TWITTER_ACCESS_TOKEN,
        "oauth_version": "1.0",
    }

    # Build signature base string (only OAuth params, no body for JSON requests)
    sorted_params = sorted(oauth_params.items())
    param_string = "&".join(f"{_percent_encode(k)}={_percent_encode(v)}" for k, v in sorted_params)
    base_string = f"{method}&{_percent_encode(url)}&{_percent_encode(param_string)}"

    # Build signing key
    signing_key = f"{_percent_encode(TWITTER_CONSUMER_SECRET)}&{_percent_encode(TWITTER_ACCESS_TOKEN_SECRET)}"

    # HMAC-SHA1 signature
    signature = hmac.new(
        signing_key.encode(), base_string.encode(), hashlib.sha1
    ).digest()

    import base64
    oauth_params["oauth_signature"] = base64.b64encode(signature).decode()

    # Build header string
    header_parts = [f'{_percent_encode(k)}="{_percent_encode(v)}"' for k, v in sorted(oauth_params.items())]
    return "OAuth " + ", ".join(header_parts)


def post_status(text: str) -> dict:
    """
    Post a tweet to X/Twitter.

    Returns:
        The API response as a dict (contains data.id).

    Raises:
        httpx.HTTPStatusError: If the request fails.
    """
    auth_header = _build_oauth_header("POST", TWITTER_API)

    resp = httpx.post(
        TWITTER_API,
        headers={
            "Authorization": auth_header,
            "Content-Type": "application/json",
        },
        json={"text": text},
        timeout=30,
    )
    if resp.status_code != 201:
        print(f"  [twitter] Status: {resp.status_code}")
        print(f"  [twitter] Response: {resp.text}")
    resp.raise_for_status()
    return resp.json()
