"""Tests for formatter.post_formatter."""
from __future__ import annotations

import sys
import os
import unittest

# Ensure project root is on the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from session.reconstructor import SessionStats
from formatter.post_formatter import format_mastodon_post, format_bluesky_post


class TestPostFormatterNoRankChange(unittest.TestCase):
    """Format output when rank stays the same."""

    def setUp(self):
        self.stats = SessionStats(
            character="Chun-Li",
            rank="Platinum 4",
            wins=5,
            losses=5,
            win_rate=50.0,
            lp_delta=88,
            current_lp=16620,
            lp_to_next_rank=380,
            match_count=10,
        )

    def test_header_line(self):
        post = format_mastodon_post(self.stats)
        self.assertTrue(post.startswith("SF6 session log \u2014 Chun-Li"))

    def test_header_no_rank(self):
        post = format_mastodon_post(self.stats)
        first_line = post.split("\n")[0]
        self.assertNotIn("Platinum", first_line)

    def test_win_loss_line(self):
        post = format_mastodon_post(self.stats)
        self.assertIn("5W / 5L (50%) | +88 LP", post)

    def test_no_promotion_or_demotion_line(self):
        post = format_mastodon_post(self.stats)
        self.assertNotIn("Promoted", post)
        self.assertNotIn("Demoted", post)

    def test_current_lp_with_rank(self):
        post = format_mastodon_post(self.stats)
        self.assertIn("Current LP: 16,620 (Platinum 4)", post)

    def test_to_next_rank(self):
        post = format_mastodon_post(self.stats)
        self.assertIn("To next rank: 380 LP remaining", post)

    def test_hashtags(self):
        post = format_mastodon_post(self.stats)
        self.assertIn("#SF6 #StreetFighter6 #FGC #DriveRecap", post)

    def test_hashtags_have_blank_line_before(self):
        post = format_mastodon_post(self.stats)
        self.assertIn("\n\n#SF6 #StreetFighter6", post)

    def test_no_emoji(self):
        post = format_mastodon_post(self.stats)
        self.assertNotIn("\U0001f3ae", post)


class TestPostFormatterPromoted(unittest.TestCase):
    """Format output when player is promoted."""

    def setUp(self):
        self.stats = SessionStats(
            character="Chun-Li",
            rank="Platinum 5",
            wins=7,
            losses=3,
            win_rate=70.0,
            lp_delta=210,
            current_lp=17050,
            lp_to_next_rank=450,
            match_count=10,
            rank_change="promoted",
            previous_rank="Platinum 4",
        )

    def test_promoted_line_present(self):
        post = format_mastodon_post(self.stats)
        self.assertIn("Promoted to Platinum 5!", post)

    def test_promoted_before_current_lp(self):
        post = format_mastodon_post(self.stats)
        promo_idx = post.index("Promoted")
        lp_idx = post.index("Current LP")
        self.assertLess(promo_idx, lp_idx)

    def test_promoted_has_exclamation(self):
        post = format_mastodon_post(self.stats)
        line = [l for l in post.split("\n") if "Promoted" in l][0]
        self.assertTrue(line.endswith("!"))

    def test_promoted_has_blank_lines_around(self):
        post = format_mastodon_post(self.stats)
        self.assertIn("\n\nPromoted to Platinum 5!\n\n", post)

    def test_promoted_lp_line_no_rank(self):
        """When promoted, rank is already shown in the promotion line — don't repeat it."""
        post = format_mastodon_post(self.stats)
        lp_line = [l for l in post.split("\n") if "Current LP" in l][0]
        self.assertNotIn("Platinum", lp_line)


class TestPostFormatterDemoted(unittest.TestCase):
    """Format output when player is demoted."""

    def setUp(self):
        self.stats = SessionStats(
            character="Chun-Li",
            rank="Platinum 3",
            wins=2,
            losses=8,
            win_rate=20.0,
            lp_delta=-320,
            current_lp=15680,
            lp_to_next_rank=820,
            match_count=10,
            rank_change="demoted",
            previous_rank="Platinum 4",
        )

    def test_demoted_line_present(self):
        post = format_mastodon_post(self.stats)
        self.assertIn("Demoted to Platinum 3", post)

    def test_demoted_no_exclamation(self):
        post = format_mastodon_post(self.stats)
        line = [l for l in post.split("\n") if "Demoted" in l][0]
        self.assertFalse(line.endswith("!"))

    def test_negative_lp_delta(self):
        post = format_mastodon_post(self.stats)
        self.assertIn("-320 LP", post)

    def test_demoted_before_current_lp(self):
        post = format_mastodon_post(self.stats)
        demo_idx = post.index("Demoted")
        lp_idx = post.index("Current LP")
        self.assertLess(demo_idx, lp_idx)

    def test_demoted_has_blank_lines_around(self):
        post = format_mastodon_post(self.stats)
        self.assertIn("\n\nDemoted to Platinum 3\n\n", post)

    def test_demoted_lp_line_no_rank(self):
        """When demoted, rank is already shown in the demotion line — don't repeat it."""
        post = format_mastodon_post(self.stats)
        lp_line = [l for l in post.split("\n") if "Current LP" in l][0]
        self.assertNotIn("Platinum", lp_line)


class TestPostFormatterEmptySession(unittest.TestCase):
    """Format output when no matches are found."""

    def test_empty_session(self):
        stats = SessionStats()
        post = format_mastodon_post(stats)
        self.assertIn("No new matches found", post)
        self.assertTrue(post.startswith("SF6 session log"))


class TestPostFormatterMasterRank(unittest.TestCase):
    """Format output for Master rank (MR instead of LP, no next rank)."""

    def setUp(self):
        self.stats = SessionStats(
            character="Ken",
            rank="Master",
            wins=6,
            losses=4,
            win_rate=60.0,
            lp_delta=0,
            current_lp=25000,
            master_rating=1604,
            lp_to_next_rank=None,
            match_count=10,
        )

    def test_shows_mr_not_lp(self):
        post = format_mastodon_post(self.stats)
        self.assertIn("Current MR: 1,604 (Master)", post)
        self.assertNotIn("Current LP:", post)

    def test_no_next_rank_line(self):
        post = format_mastodon_post(self.stats)
        self.assertNotIn("To next rank", post)


class TestBlueskyCharLimit(unittest.TestCase):
    """Bluesky posts must stay within 300 graphemes."""

    def test_bluesky_within_limit(self):
        stats = SessionStats(
            character="Chun-Li",
            rank="Platinum 4",
            wins=5,
            losses=5,
            win_rate=50.0,
            lp_delta=88,
            current_lp=16620,
            lp_to_next_rank=380,
            match_count=10,
            rank_change="promoted",
            previous_rank="Platinum 3",
        )
        post = format_bluesky_post(stats)
        self.assertLessEqual(len(post), 300)

    def test_mastodon_within_limit(self):
        stats = SessionStats(
            character="Chun-Li",
            rank="Platinum 4",
            wins=5,
            losses=5,
            win_rate=50.0,
            lp_delta=88,
            current_lp=16620,
            lp_to_next_rank=380,
            match_count=10,
            rank_change="promoted",
            previous_rank="Platinum 3",
        )
        post = format_mastodon_post(stats)
        self.assertLessEqual(len(post), 500)


if __name__ == "__main__":
    unittest.main()
