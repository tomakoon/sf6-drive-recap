"""Format session stats into social media post text."""
from __future__ import annotations

from session.reconstructor import SessionStats


def format_mastodon_post(stats: SessionStats) -> str:
    """Format a Mastodon post (up to 500 chars)."""
    return _format_post(stats, max_chars=500)


def format_bluesky_post(stats: SessionStats) -> str:
    """Format a Bluesky post (up to 300 graphemes)."""
    return _format_post(stats, max_chars=300)


def format_twitter_post(stats: SessionStats) -> str:
    """Format an X/Twitter post (up to 280 characters)."""
    return _format_post(stats, max_chars=280)


def _format_post(stats: SessionStats, max_chars: int) -> str:
    """Build the post text, trimming if needed to fit the character limit."""
    if stats.match_count == 0:
        return "SF6 session log\nNo new matches found."

    lines = []

    # Header: character only (rank shown on LP line instead)
    char_display = stats.character or "Unknown"
    lines.append(f"SF6 session log \u2014 {char_display}")

    # W/L and LP delta
    win_rate = f"{stats.win_rate:.0f}%"
    lp_sign = "+" if stats.lp_delta >= 0 else ""
    lines.append(f"{stats.wins}W / {stats.losses}L ({win_rate}) | {lp_sign}{stats.lp_delta} LP")

    # Notable matches — commented out for now, revisit later
    # notable_line = _build_notable_line(stats)
    # if notable_line:
    #     lines.append(notable_line)

    # Rank change (with blank lines around it for emphasis)
    if stats.rank_change == "promoted":
        lines.append("")
        lines.append(f"Promoted to {stats.rank}!")
        lines.append("")
    elif stats.rank_change == "demoted":
        lines.append("")
        lines.append(f"Demoted to {stats.rank}")
        lines.append("")

    # Current LP / MR — include rank in parentheses unless there's a rank change event
    show_rank = not stats.rank_change
    rank_display = stats.rank or "Unknown"
    if stats.master_rating and stats.master_rating > 0:
        if show_rank:
            lines.append(f"Current MR: {stats.master_rating:,} ({rank_display})")
        else:
            lines.append(f"Current MR: {stats.master_rating:,}")
    else:
        if show_rank:
            lines.append(f"Current LP: {stats.current_lp:,} ({rank_display})")
        else:
            lines.append(f"Current LP: {stats.current_lp:,}")

    # LP to next rank
    if stats.lp_to_next_rank is not None:
        lines.append(f"To next rank: {stats.lp_to_next_rank:,} LP remaining")

    # Hashtags (with blank line before)
    lines.append("")
    lines.append("#SF6 #StreetFighter6 #FGC #DriveRecap")

    post = "\n".join(lines)

    # Trim if too long - drop LP-to-next-rank first
    if len(post) > max_chars:
        lines = [l for l in lines if not l.startswith("To next rank")]
        post = "\n".join(lines)

    return post[:max_chars]


def _build_notable_line(stats: SessionStats) -> str | None:
    """Build the 'Notable:' line from wins and losses."""
    parts = []

    if stats.notable_wins:
        win_str = ", ".join(stats.notable_wins[:2])
        parts.append(f"beat a {win_str}")

    if stats.notable_losses:
        loss_str = ", ".join(stats.notable_losses[:1])
        parts.append(f"dropped one to {loss_str}")

    if not parts:
        return None

    return "Notable: " + ", ".join(parts)
