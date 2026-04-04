"""Persist the last known match timestamp to avoid re-posting sessions."""
from __future__ import annotations

import json
from pathlib import Path

from config import STATE_FILE


def load_last_match_timestamp() -> str | None:
    """Load the timestamp of the last match we processed."""
    path = Path(STATE_FILE)
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text())
        return data.get("last_match_timestamp")
    except (json.JSONDecodeError, KeyError):
        return None


def save_last_match_timestamp(timestamp: str):
    """Save the timestamp of the most recent match we processed."""
    path = Path(STATE_FILE)
    path.write_text(json.dumps({"last_match_timestamp": timestamp}, indent=2))
