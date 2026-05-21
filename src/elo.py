import pandas as pd


BASE_ELO = 1500
K_FACTOR = 20
HOME_FIELD_ADVANTAGE = 55


def expected_home_win_prob(home_elo, away_elo, home_field_advantage=HOME_FIELD_ADVANTAGE):
    """
    Calculate the expected probability that the home team wins based on Elo ratings.
    """
    adjusted_home_elo = home_elo + home_field_advantage
    elo_diff = adjusted_home_elo - away_elo

    expected_prob = 1 / (1 + 10 ** (-elo_diff / 400))

    return expected_prob


def create_elo_features(
    games,
    base_elo=BASE_ELO,
    k_factor=K_FACTOR,
    home_field_advantage=HOME_FIELD_ADVANTAGE
):
    """
    Create pregame Elo features for each game.

    Parameters:
        games: DataFrame with game results.
        base_elo: Starting Elo rating for each team.
        k_factor: Controls how much Elo changes after each game.
        home_field_advantage: Elo boost given to the home team.

    Returns:
        DataFrame with Elo features for each game.
    """

    games = games.copy()

    games["gameday"] = pd.to_datetime(games["gameday"])

    games = games.sort_values(
        ["season", "week", "gameday"]
    ).reset_index(drop=True)

    team_elos = {}
    elo_rows = []

    for _, row in games.iterrows():
        home_team = row["home_team"]
        away_team = row["away_team"]

        home_score = row["home_score"]
        away_score = row["away_score"]

        home_elo_before = team_elos.get(home_team, base_elo)
        away_elo_before = team_elos.get(away_team, base_elo)

        home_expected = expected_home_win_prob(
            home_elo_before,
            away_elo_before,
            home_field_advantage
        )

        away_expected = 1 - home_expected

        if home_score > away_score:
            home_result = 1
            away_result = 0
        elif home_score < away_score:
            home_result = 0
            away_result = 1
        else:
            home_result = 0.5
            away_result = 0.5

        home_elo_after = home_elo_before + k_factor * (
            home_result - home_expected
        )

        away_elo_after = away_elo_before + k_factor * (
            away_result - away_expected
        )

        elo_rows.append(
            {
                "game_id": row["game_id"],
                "season": row["season"],
                "week": row["week"],
                "gameday": row["gameday"],
                "home_team": home_team,
                "away_team": away_team,
                "home_elo_before": home_elo_before,
                "away_elo_before": away_elo_before,
                "elo_diff": home_elo_before - away_elo_before,
                "home_elo_with_hfa_diff": (
                    home_elo_before + home_field_advantage
                ) - away_elo_before,
                "elo_home_win_prob": home_expected,
                "home_elo_after": home_elo_after,
                "away_elo_after": away_elo_after,
            }
        )

        team_elos[home_team] = home_elo_after
        team_elos[away_team] = away_elo_after

    elo_features = pd.DataFrame(elo_rows)

    return elo_features


def get_latest_elos(elo_features):
    """
    Create a latest Elo ratings table from Elo feature output.
    """

    home_elos = elo_features[
        ["gameday", "home_team", "home_elo_after"]
    ].rename(
        columns={
            "home_team": "team",
            "home_elo_after": "elo_rating"
        }
    )

    away_elos = elo_features[
        ["gameday", "away_team", "away_elo_after"]
    ].rename(
        columns={
            "away_team": "team",
            "away_elo_after": "elo_rating"
        }
    )

    all_elos = pd.concat([home_elos, away_elos], ignore_index=True)

    latest_elos = (
        all_elos.sort_values("gameday")
        .groupby("team")
        .tail(1)
        .sort_values("elo_rating", ascending=False)
        .reset_index(drop=True)
    )

    return latest_elos