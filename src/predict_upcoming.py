import os
import pandas as pd
import nfl_data_py as nfl

from sklearn.linear_model import LogisticRegression, Ridge
from sklearn.metrics import accuracy_score

from data_loader import save_csv, create_game_results_from_schedules
from feature_engineering import create_modeling_dataset
from elo import create_elo_features, get_latest_elos, expected_home_win_prob


TRAIN_START_SEASON = 2018
CURRENT_SEASON = 2026
PREVIOUS_SEASON = 2025

PREDICTION_OUTPUT_PATH = "data/predictions/upcoming_2026_predictions.csv"
RECORD_OUTPUT_PATH = "data/predictions/projected_2026_records.csv"


MODEL_FEATURES = [
    "avg_points_scored_diff",
    "avg_points_allowed_diff",
    "avg_point_diff_diff",
    "win_pct_diff",
    "last3_avg_points_scored_diff",
    "last3_avg_points_allowed_diff",
    "last3_avg_point_diff_diff",
    "last3_win_pct_diff",
    "elo_diff",
    "home_elo_with_hfa_diff",
    "elo_home_win_prob",
    "strength_of_schedule_diff",
    "current_opponent_win_pct_diff",
]


def load_schedules():
    """
    Load NFL schedule data from 2018 through the upcoming season.
    """
    seasons = list(range(TRAIN_START_SEASON, CURRENT_SEASON + 1))

    print(f"Loading schedules for seasons: {seasons}")
    schedules = nfl.import_schedules(seasons)

    return schedules


def prepare_completed_games(schedules):
    """
    Keep only completed games and create the clean game results dataset.
    """
    completed_schedules = schedules.dropna(
        subset=["home_score", "away_score"]
    ).copy()

    game_results = create_game_results_from_schedules(completed_schedules)

    return game_results


def add_elo_to_modeling_data(modeling_data, game_results):
    """
    Create and merge Elo features into the modeling dataset.
    """
    elo_features = create_elo_features(game_results)

    elo_cols = [
        "game_id",
        "home_elo_before",
        "away_elo_before",
        "elo_diff",
        "home_elo_with_hfa_diff",
        "elo_home_win_prob",
    ]

    modeling_data = modeling_data.merge(
        elo_features[elo_cols],
        on="game_id",
        how="left"
    )

    return modeling_data, elo_features


def train_models(modeling_data):
    """
    Train the win probability model and the predicted margin model.
    """
    modeling_data = modeling_data.dropna(subset=MODEL_FEATURES).copy()

    X = modeling_data[MODEL_FEATURES]
    y_win = modeling_data["home_team_won"]
    y_margin = modeling_data["home_point_diff"]

    win_model = LogisticRegression(max_iter=1000)
    margin_model = Ridge(alpha=1.0)

    win_model.fit(X, y_win)
    margin_model.fit(X, y_margin)

    win_pred = win_model.predict(X)
    training_accuracy = accuracy_score(y_win, win_pred)

    print(f"Training accuracy on completed games: {training_accuracy:.2%}")

    return win_model, margin_model


def create_team_game_rows(game_results):
    """
    Convert completed games into one row per team per game.
    Used for creating current team state for upcoming predictions.
    """
    home_rows = game_results[
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

    away_rows = game_results[
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
        ["season", "week", "gameday"]
    ).reset_index(drop=True)

    team_games["point_diff"] = (
        team_games["points_scored"] - team_games["points_allowed"]
    )

    team_games["team_won"] = (
        team_games["points_scored"] > team_games["points_allowed"]
    ).astype(int)

    return team_games


def build_team_state(game_results, latest_elos):
    """
    Build the current team state used for upcoming game predictions.

    If a team has completed games in 2026, use 2026 stats.
    If not, use 2025 final stats as preseason carryover.
    """
    team_games = create_team_game_rows(game_results)

    team_states = {}

    all_teams = sorted(
        set(team_games["team"].unique())
    )

    for team in all_teams:
        team_rows = team_games[team_games["team"] == team].copy()

        current_rows = team_rows[team_rows["season"] == CURRENT_SEASON].copy()

        if len(current_rows) > 0:
            rows_to_use = current_rows
            state_season = CURRENT_SEASON
        else:
            rows_to_use = team_rows[team_rows["season"] == PREVIOUS_SEASON].copy()
            state_season = PREVIOUS_SEASON

        rows_to_use = rows_to_use.sort_values(["week", "gameday"])

        if len(rows_to_use) == 0:
            team_states[team] = {
                "state_season": state_season,
                "games_played": 0,
                "avg_points_scored_before": 0,
                "avg_points_allowed_before": 0,
                "avg_point_diff_before": 0,
                "win_pct_before": 0,
                "last3_avg_points_scored": 0,
                "last3_avg_points_allowed": 0,
                "last3_avg_point_diff": 0,
                "last3_win_pct": 0,
                "strength_of_schedule_before": 0,
                "elo_rating": 1500,
            }
            continue

        last3 = rows_to_use.tail(3)

        # Opponent strength is based on opponent win percentage in the same state season.
        season_rows = team_games[team_games["season"] == state_season].copy()

        team_win_pcts = (
            season_rows.groupby("team")["team_won"]
            .mean()
            .to_dict()
        )

        opponent_strengths = [
            team_win_pcts.get(opponent, 0)
            for opponent in rows_to_use["opponent"]
        ]

        strength_of_schedule = (
            sum(opponent_strengths) / len(opponent_strengths)
            if opponent_strengths
            else 0
        )

        elo_rating = latest_elos.get(team, 1500)

        team_states[team] = {
            "state_season": state_season,
            "games_played": len(rows_to_use),
            "avg_points_scored_before": rows_to_use["points_scored"].mean(),
            "avg_points_allowed_before": rows_to_use["points_allowed"].mean(),
            "avg_point_diff_before": rows_to_use["point_diff"].mean(),
            "win_pct_before": rows_to_use["team_won"].mean(),
            "last3_avg_points_scored": last3["points_scored"].mean(),
            "last3_avg_points_allowed": last3["points_allowed"].mean(),
            "last3_avg_point_diff": last3["point_diff"].mean(),
            "last3_win_pct": last3["team_won"].mean(),
            "strength_of_schedule_before": strength_of_schedule,
            "elo_rating": elo_rating,
        }

    return team_states


def get_team_state(team_states, team):
    """
    Safely return team state.
    """
    return team_states.get(
        team,
        {
            "state_season": PREVIOUS_SEASON,
            "games_played": 0,
            "avg_points_scored_before": 0,
            "avg_points_allowed_before": 0,
            "avg_point_diff_before": 0,
            "win_pct_before": 0,
            "last3_avg_points_scored": 0,
            "last3_avg_points_allowed": 0,
            "last3_avg_point_diff": 0,
            "last3_win_pct": 0,
            "strength_of_schedule_before": 0,
            "elo_rating": 1500,
        },
    )


def create_upcoming_features(upcoming_games, team_states):
    """
    Create model features for upcoming 2026 games.
    """
    feature_rows = []

    for _, row in upcoming_games.iterrows():
        home_team = row["home_team"]
        away_team = row["away_team"]

        home_state = get_team_state(team_states, home_team)
        away_state = get_team_state(team_states, away_team)

        home_elo = home_state["elo_rating"]
        away_elo = away_state["elo_rating"]

        elo_diff = home_elo - away_elo
        home_elo_with_hfa_diff = (home_elo + 55) - away_elo
        elo_home_win_prob = expected_home_win_prob(home_elo, away_elo)

        feature_rows.append(
            {
                "season": row["season"],
                "week": row["week"],
                "game_id": row["game_id"],
                "gameday": row["gameday"],
                "weekday": row.get("weekday", None),
                "home_team": home_team,
                "away_team": away_team,
                "home_score": row.get("home_score", None),
                "away_score": row.get("away_score", None),

                "home_avg_points_scored_before": home_state["avg_points_scored_before"],
                "away_avg_points_scored_before": away_state["avg_points_scored_before"],
                "home_avg_points_allowed_before": home_state["avg_points_allowed_before"],
                "away_avg_points_allowed_before": away_state["avg_points_allowed_before"],
                "home_avg_point_diff_before": home_state["avg_point_diff_before"],
                "away_avg_point_diff_before": away_state["avg_point_diff_before"],
                "home_win_pct_before": home_state["win_pct_before"],
                "away_win_pct_before": away_state["win_pct_before"],

                "home_last3_avg_points_scored": home_state["last3_avg_points_scored"],
                "away_last3_avg_points_scored": away_state["last3_avg_points_scored"],
                "home_last3_avg_points_allowed": home_state["last3_avg_points_allowed"],
                "away_last3_avg_points_allowed": away_state["last3_avg_points_allowed"],
                "home_last3_avg_point_diff": home_state["last3_avg_point_diff"],
                "away_last3_avg_point_diff": away_state["last3_avg_point_diff"],
                "home_last3_win_pct": home_state["last3_win_pct"],
                "away_last3_win_pct": away_state["last3_win_pct"],

                "home_strength_of_schedule_before": home_state["strength_of_schedule_before"],
                "away_strength_of_schedule_before": away_state["strength_of_schedule_before"],

                "home_elo_before": home_elo,
                "away_elo_before": away_elo,
                "elo_diff": elo_diff,
                "home_elo_with_hfa_diff": home_elo_with_hfa_diff,
                "elo_home_win_prob": elo_home_win_prob,
            }
        )

    upcoming_features = pd.DataFrame(feature_rows)

    upcoming_features["avg_points_scored_diff"] = (
        upcoming_features["home_avg_points_scored_before"]
        - upcoming_features["away_avg_points_scored_before"]
    )

    upcoming_features["avg_points_allowed_diff"] = (
        upcoming_features["home_avg_points_allowed_before"]
        - upcoming_features["away_avg_points_allowed_before"]
    )

    upcoming_features["avg_point_diff_diff"] = (
        upcoming_features["home_avg_point_diff_before"]
        - upcoming_features["away_avg_point_diff_before"]
    )

    upcoming_features["win_pct_diff"] = (
        upcoming_features["home_win_pct_before"]
        - upcoming_features["away_win_pct_before"]
    )

    upcoming_features["last3_avg_points_scored_diff"] = (
        upcoming_features["home_last3_avg_points_scored"]
        - upcoming_features["away_last3_avg_points_scored"]
    )

    upcoming_features["last3_avg_points_allowed_diff"] = (
        upcoming_features["home_last3_avg_points_allowed"]
        - upcoming_features["away_last3_avg_points_allowed"]
    )

    upcoming_features["last3_avg_point_diff_diff"] = (
        upcoming_features["home_last3_avg_point_diff"]
        - upcoming_features["away_last3_avg_point_diff"]
    )

    upcoming_features["last3_win_pct_diff"] = (
        upcoming_features["home_last3_win_pct"]
        - upcoming_features["away_last3_win_pct"]
    )

    upcoming_features["strength_of_schedule_diff"] = (
        upcoming_features["home_strength_of_schedule_before"]
        - upcoming_features["away_strength_of_schedule_before"]
    )

    # Home team's current opponent is the away team, and away team's current opponent is the home team.
    upcoming_features["current_opponent_win_pct_diff"] = (
        upcoming_features["away_win_pct_before"]
        - upcoming_features["home_win_pct_before"]
    )

    return upcoming_features


def create_predictions(upcoming_features, win_model, margin_model):
    """
    Predict winners, win probabilities, and margins for upcoming games.
    """
    X_upcoming = upcoming_features[MODEL_FEATURES]

    predicted_home_win = win_model.predict(X_upcoming)
    home_win_probability = win_model.predict_proba(X_upcoming)[:, 1]
    predicted_home_margin = margin_model.predict(X_upcoming)

    predictions = upcoming_features.copy()

    predictions["predicted_home_win"] = predicted_home_win
    predictions["home_win_probability"] = home_win_probability
    predictions["away_win_probability"] = 1 - home_win_probability
    predictions["predicted_home_margin"] = predicted_home_margin.round(1)

    predictions["predicted_winner"] = predictions.apply(
        lambda row: row["home_team"]
        if row["predicted_home_win"] == 1
        else row["away_team"],
        axis=1,
    )

    predictions["predicted_margin_abs"] = (
        predictions["predicted_home_margin"].abs().round(1)
    )

    predictions["predicted_margin_text"] = predictions.apply(
        lambda row: (
            f"{row['home_team']} by {row['predicted_margin_abs']}"
            if row["predicted_home_margin"] >= 0
            else f"{row['away_team']} by {row['predicted_margin_abs']}"
        ),
        axis=1,
    )

    predictions["status"] = "Pending"

    display_cols = [
        "season",
        "week",
        "game_id",
        "gameday",
        "weekday",
        "home_team",
        "away_team",
        "predicted_winner",
        "home_win_probability",
        "away_win_probability",
        "predicted_home_margin",
        "predicted_margin_text",
        "status",
        "home_elo_before",
        "away_elo_before",
        "elo_diff",
        "home_elo_with_hfa_diff",
        "elo_home_win_prob",
        "home_strength_of_schedule_before",
        "away_strength_of_schedule_before",
        "strength_of_schedule_diff",
        "current_opponent_win_pct_diff",
    ]

    return predictions[display_cols]


def create_projected_records(predictions, schedules):
    """
    Create projected records using actual completed 2026 games plus predicted upcoming games.

    Projected record:
        Uses hard predicted winners for future games.

    Expected record:
        Uses win probabilities for future games.
    """
    teams = sorted(
        set(schedules["home_team"].dropna().unique()).union(
            set(schedules["away_team"].dropna().unique())
        )
    )

    records = {
        team: {
            "team": team,
            "actual_wins": 0,
            "actual_losses": 0,
            "projected_wins": 0,
            "projected_losses": 0,
            "expected_wins": 0.0,
            "expected_losses": 0.0,
        }
        for team in teams
    }

    completed_2026 = schedules[
        (schedules["season"] == CURRENT_SEASON)
        & schedules["home_score"].notna()
        & schedules["away_score"].notna()
    ].copy()

    for _, row in completed_2026.iterrows():
        home_team = row["home_team"]
        away_team = row["away_team"]

        if row["home_score"] > row["away_score"]:
            winner = home_team
            loser = away_team
        else:
            winner = away_team
            loser = home_team

        records[winner]["actual_wins"] += 1
        records[winner]["projected_wins"] += 1
        records[winner]["expected_wins"] += 1

        records[loser]["actual_losses"] += 1
        records[loser]["projected_losses"] += 1
        records[loser]["expected_losses"] += 1

    for _, row in predictions.iterrows():
        home_team = row["home_team"]
        away_team = row["away_team"]

        home_prob = row["home_win_probability"]
        away_prob = row["away_win_probability"]

        if row["predicted_winner"] == home_team:
            predicted_loser = away_team
        else:
            predicted_loser = home_team

        records[row["predicted_winner"]]["projected_wins"] += 1
        records[predicted_loser]["projected_losses"] += 1

        records[home_team]["expected_wins"] += home_prob
        records[home_team]["expected_losses"] += away_prob

        records[away_team]["expected_wins"] += away_prob
        records[away_team]["expected_losses"] += home_prob

    records_df = pd.DataFrame(records.values())

    records_df["expected_wins"] = records_df["expected_wins"].round(1)
    records_df["expected_losses"] = records_df["expected_losses"].round(1)

    records_df = records_df.sort_values(
        ["projected_wins", "expected_wins"],
        ascending=False
    ).reset_index(drop=True)

    return records_df


def main():
    schedules = load_schedules()

    # Save a copy of the 2026 schedule locally for reference.
    schedules_2026 = schedules[schedules["season"] == CURRENT_SEASON].copy()
    save_csv(schedules_2026, "data/processed/schedules_2026.csv")

    completed_games = prepare_completed_games(schedules)

    print("Creating modeling dataset from completed games...")
    modeling_data = create_modeling_dataset(completed_games)

    print("Creating Elo features...")
    modeling_data, elo_features = add_elo_to_modeling_data(
        modeling_data,
        completed_games
    )

    print("Training win probability and margin models...")
    win_model, margin_model = train_models(modeling_data)

    print("Building team state...")
    latest_elos_df = get_latest_elos(elo_features)
    latest_elos = dict(
        zip(latest_elos_df["team"], latest_elos_df["elo_rating"])
    )

    team_states = build_team_state(completed_games, latest_elos)

    upcoming_games = schedules[
        (schedules["season"] == CURRENT_SEASON)
        & schedules["home_score"].isna()
        & schedules["away_score"].isna()
    ].copy()

    upcoming_games = upcoming_games.sort_values(
        ["week", "gameday"]
    ).reset_index(drop=True)

    print(f"Upcoming games found: {len(upcoming_games)}")

    print("Creating upcoming game features...")
    upcoming_features = create_upcoming_features(
        upcoming_games,
        team_states
    )

    print("Creating upcoming predictions...")
    predictions = create_predictions(
        upcoming_features,
        win_model,
        margin_model
    )

    print("Creating projected records...")
    projected_records = create_projected_records(
        predictions,
        schedules_2026
    )

    save_csv(predictions, PREDICTION_OUTPUT_PATH)
    save_csv(projected_records, RECORD_OUTPUT_PATH)

    print()
    print(f"Saved upcoming predictions to {PREDICTION_OUTPUT_PATH}")
    print(f"Saved projected records to {RECORD_OUTPUT_PATH}")
    print()
    print(predictions.head())
    print()
    print(projected_records.head(10))


if __name__ == "__main__":
    main()