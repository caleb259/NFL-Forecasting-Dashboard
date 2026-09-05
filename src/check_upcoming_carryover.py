import pandas as pd
from pandas.testing import assert_frame_equal

from check_season_carryover import make_example_games
from feature_engineering import create_modeling_dataset
from elo import create_elo_features, get_latest_elos
from predict_upcoming import (
    CURRENT_SEASON,
    MODEL_FEATURES,
    build_team_state,
    create_upcoming_features,
)
from season_carryover import (
    apply_scoring_carryover,
    apply_upcoming_scoring_carryover,
)
from train_model import add_elo_features


def main():
    games = make_example_games()

    # Align the fictional seasons with the forecasting script's settings.
    year_offset = CURRENT_SEASON - 2020
    games["season"] += year_offset
    games["gameday"] = (
        pd.to_datetime(games["gameday"])
        + pd.DateOffset(years=year_offset)
    )

    historical_features = create_modeling_dataset(games)
    historical_features = add_elo_features(historical_features, games)

    scoring_columns = [
        f"{side}_avg_{statistic}_before"
        for side in ["home", "away"]
        for statistic in ["points_scored", "points_allowed", "point_diff"]
    ] + [
        "avg_points_scored_diff",
        "avg_points_allowed_diff",
        "avg_point_diff_diff",
    ]

    comparison_columns = list(dict.fromkeys(
        scoring_columns + MODEL_FEATURES
    ))

    current_games = games.loc[games["season"] == CURRENT_SEASON]

    for weight in [0, 4]:
        expected_features = apply_scoring_carryover(
            historical_features, games, weight
        ).set_index("game_id")

        for _, game in current_games.iterrows():
            # Only earlier results are available to the upcoming path.
            completed = games.loc[
                games["gameday"] < game["gameday"]
            ].copy()

            upcoming = games.loc[
                games["game_id"] == game["game_id"]
            ].copy()

            # Remove outcomes so this really represents an unplayed game.
            upcoming = upcoming.drop(
                columns=["home_team_won", "home_point_diff"]
            )
            upcoming[["home_score", "away_score"]] = float("nan")

            elo_features = create_elo_features(completed)
            latest_elos = get_latest_elos(elo_features)
            elo_lookup = dict(zip(
                latest_elos["team"],
                latest_elos["elo_rating"],
            ))

            team_states = build_team_state(completed, elo_lookup)

            actual_features = create_upcoming_features(
                upcoming, team_states
            )
            actual_features = apply_upcoming_scoring_carryover(
                actual_features,
                completed,
                carryover_weight=weight,
            ).set_index("game_id")

            game_id = game["game_id"]

            assert_frame_equal(
                expected_features.loc[[game_id], comparison_columns],
                actual_features.loc[[game_id], comparison_columns],
                check_dtype=False,
                check_exact=False,
                rtol=1e-10,
                atol=1e-10,
            )

            print(f"PASS: {game_id}, carryover weight {weight}")

    print("\nAll six full-feature comparisons passed.")
    print("No forecasts were generated and no data files were changed.")


if __name__ == "__main__":
    main()