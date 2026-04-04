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

# SF6 Rank thresholds (LP required for each rank)
# Ranks below Master use LP; Master+ uses MR
RANK_THRESHOLDS = {
    "Rookie 1": 0,
    "Rookie 2": 1000,
    "Rookie 3": 2000,
    "Rookie 4": 3000,
    "Rookie 5": 4000,
    "Iron 1": 5000,
    "Iron 2": 5500,
    "Iron 3": 6000,
    "Iron 4": 6500,
    "Iron 5": 7000,
    "Bronze 1": 7500,
    "Bronze 2": 8000,
    "Bronze 3": 8500,
    "Bronze 4": 9000,
    "Bronze 5": 9500,
    "Silver 1": 10000,
    "Silver 2": 10500,
    "Silver 3": 11000,
    "Silver 4": 11500,
    "Silver 5": 12000,
    "Gold 1": 12500,
    "Gold 2": 13000,
    "Gold 3": 13500,
    "Gold 4": 14000,
    "Gold 5": 14500,
    "Platinum 1": 15000,
    "Platinum 2": 15500,
    "Platinum 3": 16000,
    "Platinum 4": 16500,
    "Platinum 5": 17000,
    "Diamond 1": 17500,
    "Diamond 2": 18500,
    "Diamond 3": 19500,
    "Diamond 4": 20500,
    "Diamond 5": 21500,
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
    return max(0, next_threshold - current_lp)
