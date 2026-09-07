import math
import unittest

import pandas as pd

from audit_qb_passing_history import calculate_qb_rating


def make_game(player_id, gameday, yards, sacks=0, sack_yards=0):
    return {
        "player_id": player_id,
        "game_date": pd.Timestamp(gameday).date(),
        "attempts": 10,
        "passing_yards": yards,
        "passing_tds": 0,
        "passing_interceptions": 0,
        "sacks_suffered": sacks,
        "sack_yards_lost": sack_yards,
    }


class QBRatingChecks(unittest.TestCase):
    def setUp(self):
        self.cutoff = pd.Timestamp("2025-09-10 16:00:00Z")
        self.passing = pd.DataFrame([
            make_game("QB_A", "2025-09-07", 80),
            make_game("QB_B", "2025-09-07", 40),
        ])

    def test_sack_losses_reduce_rating(self):
        before = calculate_qb_rating(
            self.passing, "QB_A", self.cutoff
        )

        changed = self.passing.copy()
        changed.loc[0, "sacks_suffered"] = 1
        changed.loc[0, "sack_yards_lost"] = -8

        after = calculate_qb_rating(
            changed, "QB_A", self.cutoff
        )

        # 80 passing yards minus 8 sack yards, over 11 plays.
        self.assertAlmostEqual(after["raw_anya"], 72 / 11)
        self.assertLess(after["raw_anya"], before["raw_anya"])
        self.assertLess(
            after["adjusted_anya"], before["adjusted_anya"]
        )

    def test_zero_history_uses_league_average(self):
        rating = calculate_qb_rating(
            self.passing, "QB_NEW", self.cutoff
        )

        self.assertEqual(rating["prior_passing_games"], 0)
        self.assertEqual(rating["prior_attempts_plus_sacks"], 0)
        self.assertTrue(math.isnan(rating["raw_anya"]))
        self.assertAlmostEqual(rating["league_anya"], 6.0)
        self.assertAlmostEqual(rating["adjusted_anya"], 6.0)
        self.assertAlmostEqual(rating["anya_above_league"], 0.0)

    def test_adjustment_moves_both_directions_toward_average(self):
        for player_id, raw in [("QB_A", 8.0), ("QB_B", 4.0)]:
            with self.subTest(player_id=player_id):
                rating = calculate_qb_rating(
                    self.passing, player_id, self.cutoff
                )

                self.assertAlmostEqual(rating["raw_anya"], raw)
                self.assertAlmostEqual(rating["league_anya"], 6.0)
                self.assertGreater(
                    rating["adjusted_anya"], min(raw, 6.0)
                )
                self.assertLess(
                    rating["adjusted_anya"], max(raw, 6.0)
                )

    def test_cutoff_day_and_future_games_cannot_change_rating(self):
        # In Eastern time, this is still September 9.
        cutoff = pd.Timestamp("2025-09-10 02:00:00Z")
        before = calculate_qb_rating(
            self.passing, "QB_A", cutoff
        )

        # Include both the selected QB and other league players.
        extra = pd.DataFrame([
            make_game("QB_A", "2025-09-09", 900),
            make_game("QB_C", "2025-09-09", 800),
            make_game("QB_A", "2025-09-11", 700),
            make_game("QB_C", "2025-09-11", 600),
        ])
        expanded = pd.concat(
            [self.passing, extra], ignore_index=True
        )

        after = calculate_qb_rating(expanded, "QB_A", cutoff)
        self.assertEqual(before, after)

        # Changing those excluded statistics must also have no effect.
        expanded.loc[2:, "passing_yards"] = -500
        changed = calculate_qb_rating(expanded, "QB_A", cutoff)
        self.assertEqual(before, changed)


if __name__ == "__main__":
    unittest.main(verbosity=2)