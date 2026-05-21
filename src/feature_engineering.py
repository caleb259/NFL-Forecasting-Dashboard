import pandas as pd


def create_team_game_rows(games):
    """
    Convert each game into two rows:
    one row for the home team and one row for the away team.
    """
    home_rows = games[
        [
            "season",
            "week",
            "game_id",
            "gameday",
            "home_team",
            "away_team",
            "home_score",
            "away_score",
        ]
    ].copy()

    home_rows = home_rows.rename(
        columns={
            "home_team": "team",
            "away_team": "opponent",
            "home_score": "points_scored",
            "away_score": "points_allowed",
        }
    )

    home_rows["is_home"] = 1

    away_rows = games[
        [
            "season",
            "week",
            "game_id",
            "gameday",
            "away_team",
            "home_team",
            "away_score",
            "home_score",
        ]
    ].copy()

    away_rows = away_rows.rename(
        columns={
            "away_team": "team",
            "home_team": "opponent",
            "away_score": "points_scored",
            "home_score": "points_allowed",
        }
    )

    away_rows["is_home"] = 0

    team_games = pd.concat([home_rows, away_rows], ignore_index=True)

    team_games["gameday"] = pd.to_datetime(team_games["gameday"])

    team_games = team_games.sort_values(
        ["team", "season", "week", "gameday"]
    ).reset_index(drop=True)

    return team_games


def add_team_results(team_games):
    """
    Add point differential and win/loss result for each team-game row.
    """
    team_games = team_games.copy()

    team_games["point_diff"] = (
        team_games["points_scored"] - team_games["points_allowed"]
    )

    team_games["team_won"] = (
        team_games["points_scored"] > team_games["points_allowed"]
    ).astype(int)

    return team_games


def add_season_long_pregame_features(team_games):
    """
    Add season-long pregame statistics for each team.

    These features only use games played before the current game.
    """
    team_games = team_games.copy()

    team_games["games_played_before"] = (
        team_games.groupby(["team", "season"]).cumcount()
    )

    team_games["points_scored_before"] = (
        team_games.groupby(["team", "season"])["points_scored"]
        .transform(lambda x: x.cumsum().shift(1))
    )

    team_games["points_allowed_before"] = (
        team_games.groupby(["team", "season"])["points_allowed"]
        .transform(lambda x: x.cumsum().shift(1))
    )

    team_games["point_diff_before"] = (
        team_games.groupby(["team", "season"])["point_diff"]
        .transform(lambda x: x.cumsum().shift(1))
    )

    team_games["wins_before"] = (
        team_games.groupby(["team", "season"])["team_won"]
        .transform(lambda x: x.cumsum().shift(1))
    )

    cols_to_fill = [
        "points_scored_before",
        "points_allowed_before",
        "point_diff_before",
        "wins_before",
    ]

    team_games[cols_to_fill] = team_games[cols_to_fill].fillna(0)

    team_games["avg_points_scored_before"] = 0.0
    team_games["avg_points_allowed_before"] = 0.0
    team_games["avg_point_diff_before"] = 0.0
    team_games["win_pct_before"] = 0.0

    mask = team_games["games_played_before"] > 0

    team_games.loc[mask, "avg_points_scored_before"] = (
        team_games.loc[mask, "points_scored_before"]
        / team_games.loc[mask, "games_played_before"]
    )

    team_games.loc[mask, "avg_points_allowed_before"] = (
        team_games.loc[mask, "points_allowed_before"]
        / team_games.loc[mask, "games_played_before"]
    )

    team_games.loc[mask, "avg_point_diff_before"] = (
        team_games.loc[mask, "point_diff_before"]
        / team_games.loc[mask, "games_played_before"]
    )

    team_games.loc[mask, "win_pct_before"] = (
        team_games.loc[mask, "wins_before"]
        / team_games.loc[mask, "games_played_before"]
    )

    return team_games


def add_recent_form_features(team_games, window=3):
    """
    Add recent-form rolling features.

    By default, this uses each team's last 3 games before the current game.
    """
    team_games = team_games.copy()

    team_games[f"last{window}_avg_points_scored"] = (
        team_games.groupby(["team", "season"])["points_scored"]
        .transform(lambda x: x.shift(1).rolling(window, min_periods=1).mean())
    )

    team_games[f"last{window}_avg_points_allowed"] = (
        team_games.groupby(["team", "season"])["points_allowed"]
        .transform(lambda x: x.shift(1).rolling(window, min_periods=1).mean())
    )

    team_games[f"last{window}_avg_point_diff"] = (
        team_games.groupby(["team", "season"])["point_diff"]
        .transform(lambda x: x.shift(1).rolling(window, min_periods=1).mean())
    )

    team_games[f"last{window}_win_pct"] = (
        team_games.groupby(["team", "season"])["team_won"]
        .transform(lambda x: x.shift(1).rolling(window, min_periods=1).mean())
    )

    recent_cols = [
        f"last{window}_avg_points_scored",
        f"last{window}_avg_points_allowed",
        f"last{window}_avg_point_diff",
        f"last{window}_win_pct",
    ]

    team_games[recent_cols] = team_games[recent_cols].fillna(0)

    return team_games


def create_home_away_features(team_games, window=3):
    """
    Create separate home and away feature tables.
    """
    feature_cols = [
        "game_id",
        "team",
        "games_played_before",
        "avg_points_scored_before",
        "avg_points_allowed_before",
        "avg_point_diff_before",
        "win_pct_before",
        f"last{window}_avg_points_scored",
        f"last{window}_avg_points_allowed",
        f"last{window}_avg_point_diff",
        f"last{window}_win_pct",
    ]

    home_features = team_games[team_games["is_home"] == 1][feature_cols].copy()

    home_features = home_features.rename(
        columns={
            "team": "home_team_check",
            "games_played_before": "home_games_played_before",
            "avg_points_scored_before": "home_avg_points_scored_before",
            "avg_points_allowed_before": "home_avg_points_allowed_before",
            "avg_point_diff_before": "home_avg_point_diff_before",
            "win_pct_before": "home_win_pct_before",
            f"last{window}_avg_points_scored": f"home_last{window}_avg_points_scored",
            f"last{window}_avg_points_allowed": f"home_last{window}_avg_points_allowed",
            f"last{window}_avg_point_diff": f"home_last{window}_avg_point_diff",
            f"last{window}_win_pct": f"home_last{window}_win_pct",
        }
    )

    away_features = team_games[team_games["is_home"] == 0][feature_cols].copy()

    away_features = away_features.rename(
        columns={
            "team": "away_team_check",
            "games_played_before": "away_games_played_before",
            "avg_points_scored_before": "away_avg_points_scored_before",
            "avg_points_allowed_before": "away_avg_points_allowed_before",
            "avg_point_diff_before": "away_avg_point_diff_before",
            "win_pct_before": "away_win_pct_before",
            f"last{window}_avg_points_scored": f"away_last{window}_avg_points_scored",
            f"last{window}_avg_points_allowed": f"away_last{window}_avg_points_allowed",
            f"last{window}_avg_point_diff": f"away_last{window}_avg_point_diff",
            f"last{window}_win_pct": f"away_last{window}_win_pct",
        }
    )

    return home_features, away_features


def add_difference_features(modeling_data, window=3):
    """
    Add difference features comparing home team values to away team values.
    """
    modeling_data = modeling_data.copy()

    modeling_data["avg_points_scored_diff"] = (
        modeling_data["home_avg_points_scored_before"]
        - modeling_data["away_avg_points_scored_before"]
    )

    modeling_data["avg_points_allowed_diff"] = (
        modeling_data["home_avg_points_allowed_before"]
        - modeling_data["away_avg_points_allowed_before"]
    )

    modeling_data["avg_point_diff_diff"] = (
        modeling_data["home_avg_point_diff_before"]
        - modeling_data["away_avg_point_diff_before"]
    )

    modeling_data["win_pct_diff"] = (
        modeling_data["home_win_pct_before"]
        - modeling_data["away_win_pct_before"]
    )

    modeling_data[f"last{window}_avg_points_scored_diff"] = (
        modeling_data[f"home_last{window}_avg_points_scored"]
        - modeling_data[f"away_last{window}_avg_points_scored"]
    )

    modeling_data[f"last{window}_avg_points_allowed_diff"] = (
        modeling_data[f"home_last{window}_avg_points_allowed"]
        - modeling_data[f"away_last{window}_avg_points_allowed"]
    )

    modeling_data[f"last{window}_avg_point_diff_diff"] = (
        modeling_data[f"home_last{window}_avg_point_diff"]
        - modeling_data[f"away_last{window}_avg_point_diff"]
    )

    modeling_data[f"last{window}_win_pct_diff"] = (
        modeling_data[f"home_last{window}_win_pct"]
        - modeling_data[f"away_last{window}_win_pct"]
    )

    return modeling_data


def create_modeling_dataset(game_results, window=3):
    """
    Create the full modeling dataset from clean game results.
    """
    games = game_results.copy()

    games["gameday"] = pd.to_datetime(games["gameday"])

    games = games.sort_values(["season", "week", "gameday"]).reset_index(drop=True)

    team_games = create_team_game_rows(games)
    team_games = add_team_results(team_games)
    team_games = add_season_long_pregame_features(team_games)
    team_games = add_recent_form_features(team_games, window=window)

    home_features, away_features = create_home_away_features(
        team_games,
        window=window,
    )

    modeling_data = games.merge(home_features, on="game_id", how="left")
    modeling_data = modeling_data.merge(away_features, on="game_id", how="left")

    modeling_data = modeling_data.drop(
        columns=["home_team_check", "away_team_check"]
    )

    modeling_data = add_difference_features(modeling_data, window=window)

    return modeling_data