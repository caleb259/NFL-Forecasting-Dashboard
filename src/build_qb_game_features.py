import pandas as pd


def build_qb_game_features(games, selections, ratings):
    keys = ["game_id", "team", "horizon", "cutoff"]

    # Explicitly select pregame fields. Target-game actual starters
    # and game outcomes are not included.
    selection_columns = keys + [
        "listed_qb",
        "listed_qb_id",
        "status",
        "snapshot_age_hours",
        "previous_qb_id",
        "previous_game_age_days",
    ]
    rating_columns = keys + [
        "prior_passing_games",
        "prior_attempts_plus_sacks",
        "adjusted_anya",
    ]

    teams = selections[selection_columns].merge(
        ratings[rating_columns],
        on=keys,
        how="left",
        validate="one_to_one",
    )

    listed = teams["listed_qb_id"].astype("string")
    previous = teams["previous_qb_id"].astype("string")

    # Missing information stays unknown rather than becoming False.
    teams["signals_disagree"] = listed.ne(previous).astype("boolean")

    game_columns = ["game_id", "home_team", "away_team"]

    if games["game_id"].duplicated().any():
        raise ValueError("Duplicate game IDs in schedules.")

    teams = teams.merge(
        games[game_columns],
        on="game_id",
        how="left",
        validate="many_to_one",
    )

    is_home = teams["team"].eq(teams["home_team"])
    is_away = teams["team"].eq(teams["away_team"])

    if not (is_home ^ is_away).all():
        raise ValueError("A selection does not match exactly one game side.")

    row_keys = ["game_id", "horizon", "cutoff"]
    side_columns = [
        "team",
        "listed_qb",
        "listed_qb_id",
        "status",
        "snapshot_age_hours",
        "previous_qb_id",
        "previous_game_age_days",
        "signals_disagree",
        "prior_passing_games",
        "prior_attempts_plus_sacks",
        "adjusted_anya",
    ]

    def get_side(mask, prefix):
        return teams.loc[mask, row_keys + side_columns].rename(
            columns={
                column: f"{prefix}_{column}"
                for column in side_columns
            }
        )

    table = get_side(is_home, "home").merge(
        get_side(is_away, "away"),
        on=row_keys,
        how="outer",
        validate="one_to_one",
        indicator=True,
    )

    if table["_merge"].ne("both").any():
        raise ValueError("A game/cutoff is missing one team's selection.")

    table = table.drop(columns="_merge")

    if table.duplicated(["game_id", "horizon"]).any():
        raise ValueError("Multiple rows for the same game and horizon.")

    expected = pd.MultiIndex.from_product(
        [
            games["game_id"],
            ["Seven days before", "24 hours before"],
        ],
        names=["game_id", "horizon"],
    )
    actual = pd.MultiIndex.from_frame(
        table[["game_id", "horizon"]]
    )

    if len(expected.difference(actual)) or len(actual.difference(expected)):
        raise ValueError("Game/horizon coverage does not match expectations.")

    table["qb_rating_diff"] = (
        table["home_adjusted_anya"] - table["away_adjusted_anya"]
    )

    table["both_ratings_available"] = table[
        ["home_adjusted_anya", "away_adjusted_anya"]
    ].notna().all(axis=1)

    return table.sort_values(
        ["cutoff", "game_id"]
    ).reset_index(drop=True)