"""Post to Mastodon via REST API."""

import httpx
from config import MASTODON_INSTANCE, MASTODON_ACCESS_TOKEN


def post_status(text: str, visibility: str = "public") -> dict:
    """
    Post a status to Mastodon.

    Args:
        text: The status text.
        visibility: One of 'public', 'unlisted', 'private', 'direct'.

    Returns:
        The API response as a dict.

    Raises:
        httpx.HTTPStatusError: If the request fails.
    """
    url = f"{MASTODON_INSTANCE}/api/v1/statuses"
    headers = {"Authorization": f"Bearer {MASTODON_ACCESS_TOKEN}"}
    payload = {
        "status": text,
        "visibility": visibility,
        "language": "en",
    }

    resp = httpx.post(url, headers=headers, data=payload, timeout=30)
    resp.raise_for_status()
    return resp.json()
