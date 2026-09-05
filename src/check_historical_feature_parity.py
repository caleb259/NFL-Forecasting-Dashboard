from pathlib import Path

import pandas as pd
from pandas.testing import assert_frame_equal

from data_loader import load_game_results
from feature_engineering import create_modeling_dataset
from train_model import add_elo_features
from elo import create_elo_features, get_latest_elos
from predict_upcoming import (
    MODEL_FEATURES,
    build_team_state,
    create_upcoming_features,
)
from season_carryover import (
    apply_scoring_carryover,
    apply_upcoming_scoring_carryover,
)


def main():
    root = Path(__file__).resolve().parents[1]
    games = load_game_results(
        root / "data/processed/game_results_2018_2025.csv"
    )
    games["gameday"] = pd.to_datetime(games["gameday"])
    games = games.sort_values(["season", "week", "gameday"])

    historical = create_modeling_dataset(games)
    historical = add_elo_features(historical, games)
    historical = apply_scoring_carryover(historical, games, 4)

    season_games = historical.loc[historical["season"] == 2025]

    cases = {
        "Season opener": season_games["week"] == 1,
        "Unequal games played": (
            season_games["home_games_played_before"]
            != season_games["away_games_played_before"]
        ),
        "Late season": season_games["week"].between(16, 18),
        "Playoffs": season_games["week"] > 18,
    }

    checked = 0

    for description, mask in cases.items():
        examples = season_games.loc[mask].head(2)

        if examples.empty:
            raise AssertionError(f"No examples found for: {description}")

        for _, game in examples.iterrows():
            game_id = game["game_id"]

            # Reconstruct the information available before this game day.
            completed = games.loc[
                games["gameday"] < game["gameday"]
            ].copy()

            upcoming = games.loc[games["game_id"] == game_id].copy()
            upcoming = upcoming.drop(
                columns=["home_team_won", "home_point_diff"],
                errors="ignore",
            )
            upcoming[["home_score", "away_score"]] = float("nan")

            elo_history = create_elo_features(completed)
            latest = get_latest_elos(elo_history)
            elo_lookup = dict(zip(latest["team"], latest["elo_rating"]))

            states = build_team_state(
                completed,
                elo_lookup,
                season=int(game["season"]),
            )

            upcoming_features = create_upcoming_features(upcoming, states)
            upcoming_features = apply_upcoming_scoring_carryover(
                upcoming_features, completed, carryover_weight=4
            )

            expected = historical.set_index("game_id").loc[
                [game_id], MODEL_FEATURES
            ]
            actual = upcoming_features.set_index("game_id").loc[
                [game_id], MODEL_FEATURES
            ]

            assert_frame_equal(
                expected,
                actual,
                check_dtype=False,
                check_exact=False,
                rtol=1e-9,
                atol=1e-9,
            )

            checked += 1
            print(f"PASS: {description} — {game_id}")

    print(f"\nAll {checked} real-game comparisons passed.")
    print("No models were trained and no forecast files were changed.")


if __name__ == "__main__":
    main()