from __future__ import annotations

import os
from dotenv import load_dotenv

load_dotenv()

# Buckler / CAPCOM ID
CAPCOM_EMAIL = os.getenv("CAPCOM_EMAIL", "")
CAPCOM_PASSWORD = os.getenv("CAPCOM_PASSWORD", "")

# Mastodon
MASTODON_INSTANCE = os.getenv("MASTODON_INSTANCE", "")
MASTODON_ACCESS_TOKEN = os.getenv("MASTODON_ACCESS_TOKEN", "")

# Bluesky
BLUESKY_HANDLE = os.getenv("BLUESKY_HANDLE", "")
BLUESKY_APP_PASSWORD = os.getenv("BLUESKY_APP_PASSWORD", "")

# X/Twitter
TWITTER_CONSUMER_KEY = os.getenv("TWITTER_CONSUMER_KEY", "")
TWITTER_CONSUMER_SECRET = os.getenv("TWITTER_CONSUMER_SECRET", "")
TWITTER_ACCESS_TOKEN = os.getenv("TWITTER_ACCESS_TOKEN", "")
TWITTER_ACCESS_TOKEN_SECRET = os.getenv("TWITTER_ACCESS_TOKEN_SECRET", "")

# Buckler URLs
BUCKLER_BASE_URL = "https://www.streetfighter.com/6/buckler"

# Local state file for session tracking
STATE_FILE = os.path.join(os.path.dirname(__file__), ".session_state.json")

# SF6 Rank thresholds (LP required to enter each rank)
# Source: community-documented values (sf6-ranked-guide)
# Buckler returns Arabic numerals ("Platinum 4"), guide uses Roman ("Platinum IV")
# We store Arabic format to match Buckler's output.
RANK_THRESHOLDS = {
    "Rookie 1": 0,
    "Rookie 2": 200,
    "Rookie 3": 400,
    "Rookie 4": 600,
    "Rookie 5": 800,
    "Iron 1": 1000,
    "Iron 2": 1400,
    "Iron 3": 1800,
    "Iron 4": 2200,
    "Iron 5": 2600,
    "Bronze 1": 3000,
    "Bronze 2": 3400,
    "Bronze 3": 3800,
    "Bronze 4": 4200,
    "Bronze 5": 4600,
    "Silver 1": 5000,
    "Silver 2": 5800,
    "Silver 3": 6600,
    "Silver 4": 7400,
    "Silver 5": 8200,
    "Gold 1": 9000,
    "Gold 2": 9800,
    "Gold 3": 10600,
    "Gold 4": 11400,
    "Gold 5": 12200,
    "Platinum 1": 13000,
    "Platinum 2": 14200,
    "Platinum 3": 15400,
    "Platinum 4": 16600,
    "Platinum 5": 17800,
    "Diamond 1": 19000,
    "Diamond 2": 20200,
    "Diamond 3": 21400,
    "Diamond 4": 22600,
    "Diamond 5": 23800,
    "Master": 25000,
}


def lp_to_next_rank(current_lp: int, current_rank: str) -> int | None:
    """Calculate LP remaining to reach the next rank. Returns None if Master+."""
    if current_rank.startswith("Master"):
        return None
    ranks = list(RANK_THRESHOLDS.keys())
    try:
        idx = ranks.index(current_rank)
    except ValueError:
        return None
    if idx + 1 >= len(ranks):
        return None
    next_threshold = RANK_THRESHOLDS[ranks[idx + 1]]
    remaining = next_threshold - current_lp
    return remaining if remaining > 0 else None
