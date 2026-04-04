"""Fetch match data from Buckler's Boot Camp.

Scraping approach based on cfn-tracker (github.com/williamsjokvist/cfn-tracker):
- Navigate to /profile/{cfn}/battlelog/rank
- Parse #__NEXT_DATA__ script tag (Next.js SSR data)
- Data model matches cfn-tracker's model.go field names exactly
"""
from __future__ import annotations

import json
from pathlib import Path
from dataclasses import dataclass, field
from playwright.sync_api import BrowserContext

_DEBUG_DIR = Path(__file__).parent.parent / ".debug"
BUCKLER_BATTLELOG_URL = "https://www.streetfighter.com/6/buckler/profile/{sid}/battlelog/rank"


@dataclass
class PlayerInfo:
    """Info about a player in a match."""
    fighter_id: str = ""
    short_id: int = 0
    character_name: str = ""
    league_point: int = 0
    master_rating: int = 0
    league_rank: str = ""
    round_results: list[int] = field(default_factory=list)
    is_winner: bool = False


@dataclass
class Match:
    """A single ranked match."""
    replay_id: str = ""
    uploaded_at: str = ""
    player: PlayerInfo = field(default_factory=PlayerInfo)
    opponent: PlayerInfo = field(default_factory=PlayerInfo)
    won: bool = False


@dataclass
class ProfileData:
    """Player profile and recent matches from Buckler."""
    cfn_name: str = ""
    character_name: str = ""
    league_point: int = 0
    master_rating: int = 0
    rank_name: str = ""
    matches: list[Match] = field(default_factory=list)


def fetch_battle_log(
    context: BrowserContext,
    cfn_name: str,
    short_id: str = "",
    last_timestamp: str | None = None,
) -> ProfileData:
    """
    Navigate to the ranked battlelog page and parse __NEXT_DATA__.
    Fetches multiple pages if needed to capture all matches since last_timestamp.
    """
    _DEBUG_DIR.mkdir(parents=True, exist_ok=True)
    sid = short_id or cfn_name
    base_url = BUCKLER_BATTLELOG_URL.format(sid=sid)

    page = context.new_page()
    profile = None
    all_matches: list[Match] = []
    page_num = 1

    while True:
        url = base_url if page_num == 1 else f"{base_url}?page={page_num}"
        print(f"  [scraper] Fetching page {page_num}: {url}")
        page.goto(url, wait_until="networkidle", timeout=30000)
        page.wait_for_load_state("networkidle")

        if page_num == 1:
            page.screenshot(path=str(_DEBUG_DIR / "05_battlelog.png"), full_page=True)

        page_props = _extract_page_props(page, page_num)
        if page_props is None:
            break

        # Parse profile info from first page only
        if profile is None:
            profile = _parse_profile(page_props)

        # Parse matches from this page
        page_matches = _parse_matches(page_props, profile.cfn_name)
        current_page = page_props.get("current_page", 1)
        total_pages = page_props.get("total_page", 1)
        print(f"  [scraper] Page {current_page}/{total_pages}: {len(page_matches)} matches")

        if not page_matches:
            break

        all_matches.extend(page_matches)

        # Check if we've gone far enough back in time
        # Matches are newest-first from Buckler, so the last match on this page is the oldest
        oldest_on_page = page_matches[-1].uploaded_at
        if last_timestamp and oldest_on_page <= last_timestamp:
            print(f"  [scraper] Reached matches from previous session, stopping pagination")
            break

        # Check if there are more pages
        if current_page >= total_pages:
            break

        page_num += 1

    page.close()

    if profile is None:
        raise RuntimeError("Could not parse profile data from Buckler.")

    profile.matches = all_matches
    print(f"  [scraper] Total matches fetched: {len(all_matches)} across {page_num} page(s)")
    return profile


def _extract_page_props(page, page_num: int) -> dict | None:
    """Extract pageProps from __NEXT_DATA__ on the current page."""
    next_data_el = page.locator("script#__NEXT_DATA__")
    if next_data_el.count() == 0:
        if page_num == 1:
            raise RuntimeError(
                "Could not find #__NEXT_DATA__ on battlelog page. "
                "Check .debug/05_battlelog.png — you may be logged out or CloudFront-blocked."
            )
        return None

    raw = next_data_el.first.inner_text()
    next_data = json.loads(raw)

    if page_num == 1:
        (_DEBUG_DIR / "next_data.json").write_text(
            json.dumps(next_data, indent=2, default=str)[:500000]
        )

    page_props = next_data.get("props", {}).get("pageProps", {})
    status_code = page_props.get("common", {}).get("statusCode", 0)
    if status_code != 200:
        if page_num == 1:
            raise RuntimeError(f"Buckler returned status {status_code}. Check .debug/next_data.json")
        return None

    return page_props


def _parse_profile(page_props: dict) -> ProfileData:
    """Parse player profile info from pageProps."""
    banner = page_props.get("fighter_banner_info", {})
    personal = banner.get("personal_info", {})
    fav_league = banner.get("favorite_character_league_info", {})
    rank_info = fav_league.get("league_rank_info", {})

    return ProfileData(
        cfn_name=personal.get("fighter_id", ""),
        character_name=banner.get("favorite_character_name", ""),
        league_point=fav_league.get("league_point", 0),
        master_rating=fav_league.get("master_rating", 0),
        rank_name=rank_info.get("league_rank_name", ""),
    )


def _parse_matches(page_props: dict, cfn_name: str) -> list[Match]:
    """Parse replay_list from a single page of pageProps."""
    matches = []
    for replay in page_props.get("replay_list", []):
        match = _parse_replay(replay, cfn_name)
        if match:
            matches.append(match)
    return matches


def _parse_replay(replay: dict, my_cfn: str) -> Match | None:
    """Parse a single replay using cfn-tracker's exact field names."""
    try:
        p1 = replay.get("player1_info", {})
        p2 = replay.get("player2_info", {})

        p1_id = p1.get("player", {}).get("fighter_id", "")
        p2_id = p2.get("player", {}).get("fighter_id", "")

        if p1_id == my_cfn:
            me_data, opp_data = p1, p2
        elif p2_id == my_cfn:
            me_data, opp_data = p2, p1
        else:
            me_data, opp_data = p1, p2

        me = _parse_player_info(me_data)
        opp = _parse_player_info(opp_data)

        me_rounds = sum(1 for r in me.round_results if r > 0)
        opp_rounds = sum(1 for r in opp.round_results if r > 0)

        return Match(
            replay_id=replay.get("replay_id", ""),
            uploaded_at=str(replay.get("uploaded_at", "")),
            player=me,
            opponent=opp,
            won=me_rounds > opp_rounds,
        )
    except Exception:
        return None


def _parse_player_info(data: dict) -> PlayerInfo:
    """Parse player info using cfn-tracker's model.go field names."""
    player = data.get("player", {})
    rank_int = data.get("league_rank", 0)
    return PlayerInfo(
        fighter_id=player.get("fighter_id", ""),
        short_id=player.get("short_id", 0),
        character_name=data.get("playing_character_name", data.get("character_name", "")),
        league_point=data.get("league_point", 0),
        master_rating=data.get("master_rating", 0),
        league_rank=league_rank_name(rank_int),
        round_results=data.get("round_results", []),
    )


# Mapping derived from Buckler data: rank 29 = Platinum 4, so ranks are 1-indexed
# with 5 tiers per league (Rookie=1-5, Iron=6-10, ..., Master=36+)
LEAGUE_RANKS = {
    1: "Rookie 1", 2: "Rookie 2", 3: "Rookie 3", 4: "Rookie 4", 5: "Rookie 5",
    6: "Iron 1", 7: "Iron 2", 8: "Iron 3", 9: "Iron 4", 10: "Iron 5",
    11: "Bronze 1", 12: "Bronze 2", 13: "Bronze 3", 14: "Bronze 4", 15: "Bronze 5",
    16: "Silver 1", 17: "Silver 2", 18: "Silver 3", 19: "Silver 4", 20: "Silver 5",
    21: "Gold 1", 22: "Gold 2", 23: "Gold 3", 24: "Gold 4", 25: "Gold 5",
    26: "Platinum 1", 27: "Platinum 2", 28: "Platinum 3", 29: "Platinum 4", 30: "Platinum 5",
    31: "Diamond 1", 32: "Diamond 2", 33: "Diamond 3", 34: "Diamond 4", 35: "Diamond 5",
    36: "Master",
}


def league_rank_name(rank_int: int) -> str:
    """Convert league_rank integer to human-readable rank name."""
    return LEAGUE_RANKS.get(rank_int, f"Rank {rank_int}")
