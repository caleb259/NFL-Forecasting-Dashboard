import pandas as pd

from feature_engineering import create_team_game_rows


def apply_scoring_carryover(modeling_data, game_results, carryover_weight):
    """
    Blend previous-season scoring averages with current-season results.

    carryover_weight represents how many games of weight to give
    the previous season.

    Only season-long scoring features are changed.
    """
    if carryover_weight < 0:
        raise ValueError("carryover_weight cannot be negative.")

    result = modeling_data.copy()

    # A weight of zero reproduces the original features exactly.
    if carryover_weight == 0:
        return result

    # Create one historical row per team per game.
    team_games = create_team_game_rows(game_results)

    # Calculate each team's completed season scoring averages.
    previous_averages = (
        team_games.groupby(["team", "season"])[
            ["points_scored", "points_allowed"]
        ]
        .mean()
        .reset_index()
    )

    # Shift the season label forward:
    # 2020 averages can be used for 2021 games, never 2020 games.
    previous_averages["season"] += 1

    previous_lookup = previous_averages.set_index(["team", "season"])

    for side in ["home", "away"]:
        lookup_keys = pd.MultiIndex.from_arrays(
            [result[f"{side}_team"], result["season"]],
            names=["team", "season"],
        )

        prior = previous_lookup.reindex(lookup_keys)

        # Match the modeling table's row index for safe arithmetic.
        prior.index = result.index

        games_played = result[f"{side}_games_played_before"]

        for statistic in ["points_scored", "points_allowed"]:
            feature = f"{side}_avg_{statistic}_before"
            previous_average = prior[statistic]
            has_previous_season = previous_average.notna()

            # Recover the current-season total from the existing
            # pregame average and number of games already played.
            current_total = result[feature] * games_played

            blended_average = (
                previous_average * carryover_weight + current_total
            ) / (carryover_weight + games_played)

            # Without prior-season data, retain the original feature.
            result.loc[has_previous_season, feature] = (
                blended_average.loc[has_previous_season]
            )

        # Keep point differential consistent with the scoring averages.
        result[f"{side}_avg_point_diff_before"] = (
            result[f"{side}_avg_points_scored_before"]
            - result[f"{side}_avg_points_allowed_before"]
        )

    # Rebuild the three home-minus-away inputs used by the model.
    for statistic in ["points_scored", "points_allowed", "point_diff"]:
        result[f"avg_{statistic}_diff"] = (
            result[f"home_avg_{statistic}_before"]
            - result[f"away_avg_{statistic}_before"]
        )

    return result

def apply_upcoming_scoring_carryover(
    upcoming_features, completed_games, carryover_weight=4
):
    """
    Build scoring inputs from completed games available at forecast time,
    then apply the same carryover calculation used in historical training.

    completed_games must contain only results available at that time.
    """
    result = upcoming_features.copy()

    if result.empty:
        return result

    team_games = create_team_game_rows(completed_games)

    current_stats = (
        team_games.groupby(["team", "season"])
        .agg(
            games_played=("game_id", "count"),
            avg_points_scored=("points_scored", "mean"),
            avg_points_allowed=("points_allowed", "mean"),
        )
    )

    for side in ["home", "away"]:
        lookup_keys = pd.MultiIndex.from_arrays(
            [result[f"{side}_team"], result["season"]],
            names=["team", "season"],
        )

        stats = current_stats.reindex(lookup_keys).copy()
        stats.index = result.index

        # Before the opener, there are zero current-season games.
        # The shared helper will supply previous-season carryover.
        result[f"{side}_games_played_before"] = (
            stats["games_played"].fillna(0)
        )

        result[f"{side}_avg_points_scored_before"] = (
            stats["avg_points_scored"].fillna(0)
        )

        result[f"{side}_avg_points_allowed_before"] = (
            stats["avg_points_allowed"].fillna(0)
        )

        result[f"{side}_avg_point_diff_before"] = (
            result[f"{side}_avg_points_scored_before"]
            - result[f"{side}_avg_points_allowed_before"]
        )

    # Recalculate differences even when carryover_weight is zero.
    for statistic in ["points_scored", "points_allowed", "point_diff"]:
        result[f"avg_{statistic}_diff"] = (
            result[f"home_avg_{statistic}_before"]
            - result[f"away_avg_{statistic}_before"]
        )

    return apply_scoring_carryover(
        result,
        completed_games,
        carryover_weight=carryover_weight,
    )