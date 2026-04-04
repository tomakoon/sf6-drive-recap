"""Reconstruct a session from recent matches and compute summary stats."""
from __future__ import annotations

from dataclasses import dataclass, field
from buckler.scraper import ProfileData, Match


@dataclass
class SessionStats:
    """Computed stats for a ranked session."""
    character: str = ""
    rank: str = ""
    wins: int = 0
    losses: int = 0
    win_rate: float = 0.0
    lp_delta: int = 0
    current_lp: int = 0
    master_rating: int = 0
    lp_to_next_rank: int | None = None
    notable_wins: list[str] = field(default_factory=list)  # e.g. "Master Cammy"
    notable_losses: list[str] = field(default_factory=list)
    characters_faced: list[str] = field(default_factory=list)
    match_count: int = 0
    rank_change: str | None = None  # "promoted", "demoted", or None
    previous_rank: str = ""


def reconstruct_session(
    profile: ProfileData,
    last_timestamp: str | None = None,
) -> tuple[SessionStats, list[Match]]:
    """
    Filter matches that are newer than last_timestamp and compute session stats.

    Returns (stats, session_matches) where session_matches are the matches
    included in this session (sorted oldest-first).
    """
    matches = profile.matches

    # Filter to only new matches
    if last_timestamp:
        matches = [m for m in matches if m.uploaded_at > last_timestamp]

    if not matches:
        return SessionStats(), []

    # Sort by upload time (oldest first)
    matches.sort(key=lambda m: m.uploaded_at)

    stats = SessionStats()
    stats.character = profile.character_name
    stats.rank = profile.rank_name
    stats.current_lp = profile.league_point
    stats.master_rating = profile.master_rating
    stats.match_count = len(matches)

    # Compute wins/losses
    stats.wins = sum(1 for m in matches if m.won)
    stats.losses = len(matches) - stats.wins
    stats.win_rate = (stats.wins / len(matches) * 100) if matches else 0.0

    # Compute LP delta
    # LP at first match vs current LP
    if matches:
        first_match_lp = matches[0].player.league_point
        stats.lp_delta = profile.league_point - first_match_lp

    # Characters faced
    faced = {}
    for m in matches:
        char = m.opponent.character_name
        if char:
            faced[char] = faced.get(char, 0) + 1
    stats.characters_faced = [f"{char} (x{count})" if count > 1 else char
                              for char, count in faced.items()]

    # Notable matches - wins against higher-ranked opponents, losses to lower-ranked
    for m in matches:
        opp_desc = f"{m.opponent.league_rank} {m.opponent.character_name}".strip()
        if not opp_desc:
            opp_desc = m.opponent.character_name or "Unknown"

        if m.won and _is_higher_rank(m.opponent.league_point, profile.league_point):
            stats.notable_wins.append(opp_desc)
        elif not m.won:
            stats.notable_losses.append(opp_desc)

    # Rank change detection: compare first match rank to current profile rank
    if matches:
        first_match_rank = matches[0].player.league_rank
        if first_match_rank and profile.rank_name and first_match_rank != profile.rank_name:
            from buckler.scraper import LEAGUE_RANKS
            rank_to_int = {v: k for k, v in LEAGUE_RANKS.items()}
            old_int = rank_to_int.get(first_match_rank, 0)
            new_int = rank_to_int.get(profile.rank_name, 0)
            if new_int > old_int:
                stats.rank_change = "promoted"
                stats.previous_rank = first_match_rank
            elif new_int < old_int:
                stats.rank_change = "demoted"
                stats.previous_rank = first_match_rank

    # LP to next rank
    from config import lp_to_next_rank
    stats.lp_to_next_rank = lp_to_next_rank(profile.league_point, profile.rank_name)

    return stats, matches


def _is_higher_rank(opponent_lp: int, my_lp: int) -> bool:
    """Simple heuristic: opponent is higher ranked if they have significantly more LP."""
    return opponent_lp > my_lp + 500
