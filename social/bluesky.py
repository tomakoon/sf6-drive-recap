"""Post to Bluesky via AT Protocol."""

import re
from datetime import datetime, timezone
import httpx
from config import BLUESKY_HANDLE, BLUESKY_APP_PASSWORD

BSKY_API = "https://bsky.social/xrpc"


def _create_session() -> dict:
    """Authenticate and return session data (accessJwt, did)."""
    resp = httpx.post(
        f"{BSKY_API}/com.atproto.server.createSession",
        json={
            "identifier": BLUESKY_HANDLE,
            "password": BLUESKY_APP_PASSWORD,
        },
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json()


def _parse_hashtag_facets(text: str) -> list[dict]:
    """
    Parse hashtags in text and return Bluesky facets for them.
    Facets use byte offsets into the UTF-8 encoded text.
    """
    facets = []
    text_bytes = text.encode("utf-8")

    for match in re.finditer(r"#(\w+)", text):
        tag = match.group(1)
        # Find byte positions
        start_char = match.start()
        end_char = match.end()
        byte_start = len(text[:start_char].encode("utf-8"))
        byte_end = len(text[:end_char].encode("utf-8"))

        facets.append({
            "index": {
                "byteStart": byte_start,
                "byteEnd": byte_end,
            },
            "features": [
                {
                    "$type": "app.bsky.richtext.facet#tag",
                    "tag": tag,
                }
            ],
        })

    return facets


def post_status(text: str) -> dict:
    """
    Post a status to Bluesky.

    Returns:
        The API response as a dict (uri, cid).

    Raises:
        httpx.HTTPStatusError: If the request fails.
    """
    session = _create_session()

    now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

    post_record = {
        "$type": "app.bsky.feed.post",
        "text": text,
        "createdAt": now,
        "langs": ["en"],
    }

    # Add hashtag facets
    facets = _parse_hashtag_facets(text)
    if facets:
        post_record["facets"] = facets

    resp = httpx.post(
        f"{BSKY_API}/com.atproto.repo.createRecord",
        headers={"Authorization": f"Bearer {session['accessJwt']}"},
        json={
            "repo": session["did"],
            "collection": "app.bsky.feed.post",
            "record": post_record,
        },
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json()
