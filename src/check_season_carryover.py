import pandas as pd
from pandas.testing import assert_frame_equal

from feature_engineering import create_modeling_dataset
from season_carryover import apply_scoring_carryover


def make_example_games():
    """Create two fictional teams with easy-to-check scoring history."""
    games = pd.DataFrame([
        # Team A averages 24 scored and 12 allowed in 2019.
        [2019, 1, "previous_1", "2019-09-01", "A", "B", 20, 10],
        [2019, 2, "previous_2", "2019-09-08", "A", "B", 28, 14],

        # Team A scores 35 and allows 17 in its 2020 opener.
        [2020, 1, "current_1", "2020-09-01", "A", "B", 35, 17],
        [2020, 2, "current_2", "2020-09-08", "A", "B", 21, 24],
        [2020, 3, "current_3", "2020-09-15", "A", "B", 14, 28],
    ], columns=[
        "season", "week", "game_id", "gameday",
        "home_team", "away_team", "home_score", "away_score",
    ])

    games["home_team_won"] = (
        games["home_score"] > games["away_score"]
    ).astype(int)
    games["home_point_diff"] = games["home_score"] - games["away_score"]

    return games


def check_close(actual, expected, description):
    if abs(actual - expected) > 1e-10:
        raise AssertionError(
            f"{description}: expected {expected}, got {actual}"
        )


def main():
    games = make_example_games()
    original = create_modeling_dataset(games)

    original_snapshot = original.copy(deep=True)
    games_snapshot = games.copy(deep=True)

    blended = apply_scoring_carryover(original, games, 4)
    by_game = blended.set_index("game_id")

    # 1. Before the opener, use last season's scoring averages.
    opener = by_game.loc["current_1"]

    check_close(
        opener["home_avg_points_scored_before"], 24,
        "Opening-game scoring average",
    )
    check_close(
        opener["home_avg_points_allowed_before"], 12,
        "Opening-game points allowed",
    )
    check_close(
        opener["away_avg_points_scored_before"], 12,
        "Away team's opening-game scoring average",
    )
    check_close(
        opener["avg_points_scored_diff"], 12,
        "Opening-game home-minus-away scoring difference",
    )

    print("PASS: Opening games use previous-season scoring averages.")

    # 2. After one game, combine four games of prior weight with one result.
    second_game = by_game.loc["current_2"]

    check_close(
        second_game["home_avg_points_scored_before"],
        (24 * 4 + 35) / 5,
        "Scoring blend after one game",
    )
    check_close(
        second_game["home_avg_points_allowed_before"],
        (12 * 4 + 17) / 5,
        "Defensive blend after one game",
    )
    check_close(
        second_game["home_avg_point_diff_before"],
        ((24 - 12) * 4 + (35 - 17)) / 5,
        "Point-differential blend after one game",
    )

    print("PASS: Scoring and point differential blend correctly.")

    # 3. Weight zero must preserve the original table exactly.
    zero_weight = apply_scoring_carryover(original, games, 0)
    assert_frame_equal(zero_weight, original)

    print("PASS: Weight zero preserves the original features.")

    # 4. Without an earlier season, retain the original features.
    first_season = original["season"] == 2019
    assert_frame_equal(
        blended.loc[first_season],
        original.loc[first_season],
    )

    print("PASS: Missing previous-season history preserves original features.")

    # 5. The helper must not modify either input table.
    assert_frame_equal(original, original_snapshot)
    assert_frame_equal(games, games_snapshot)

    print("PASS: Input tables remain unchanged.")

    # 6. Only the intended nine scoring columns may change.
    changed_columns = {
        f"{side}_avg_{statistic}_before"
        for side in ["home", "away"]
        for statistic in ["points_scored", "points_allowed", "point_diff"]
    }
    changed_columns.update({
        "avg_points_scored_diff",
        "avg_points_allowed_diff",
        "avg_point_diff_diff",
    })

    unchanged_columns = [
        column for column in original.columns
        if column not in changed_columns
    ]

    assert_frame_equal(
        blended[unchanged_columns],
        original[unchanged_columns],
    )

    print("PASS: Other features remain unchanged.")

    # 7. Changing game 2 and game 3 outcomes must not affect pregame
    # scoring features for game 1 or game 2.
    altered_games = games.copy(deep=True)
    future_mask = altered_games["game_id"].isin(["current_2", "current_3"])

    altered_games.loc[future_mask, "home_score"] = 70
    altered_games.loc[future_mask, "away_score"] = 0
    altered_games["home_team_won"] = (
        altered_games["home_score"] > altered_games["away_score"]
    ).astype(int)
    altered_games["home_point_diff"] = (
        altered_games["home_score"] - altered_games["away_score"]
    )

    altered_features = create_modeling_dataset(altered_games)
    altered_blend = apply_scoring_carryover(
        altered_features, altered_games, 4
    ).set_index("game_id")

    earlier_games = ["current_1", "current_2"]
    scoring_columns = sorted(changed_columns)

    assert_frame_equal(
        by_game.loc[earlier_games, scoring_columns],
        altered_blend.loc[earlier_games, scoring_columns],
    )

    # Confirm the changed game 2 result DOES affect game 3's pregame average.
    check_close(
        altered_blend.loc["current_3", "home_avg_points_scored_before"],
        (24 * 4 + 35 + 70) / 6,
        "Updating only after a result is available",
    )

    print("PASS: Current/future outcomes do not leak into earlier scoring features.")
    print("\nAll carryover checks passed. No project data was changed.")


if __name__ == "__main__":
    main()