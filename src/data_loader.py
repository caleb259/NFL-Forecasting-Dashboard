import os
import pandas as pd
import nfl_data_py as nfl


def load_csv(filepath):
    """
    Load a CSV file into a pandas DataFrame.
    """
    return pd.read_csv(filepath)


def save_csv(df, filepath):
    """
    Save a DataFrame to a CSV file.
    Creates the folder path if it does not already exist.
    """
    folder = os.path.dirname(filepath)

    if folder:
        os.makedirs(folder, exist_ok=True)

    df.to_csv(filepath, index=False)


def load_game_results(filepath="data/processed/game_results_2018_2025.csv"):
    """
    Load the processed game results dataset.
    """
    return load_csv(filepath)


def load_modeling_data(filepath="data/processed/modeling_dataset_expanded_2018_2025.csv"):
    """
    Load the expanded modeling dataset.
    """
    return load_csv(filepath)


def load_predictions(filepath="data/predictions/best_logistic_regression_predictions.csv"):
    """
    Load saved model predictions.
    """
    return load_csv(filepath)


def import_schedules(seasons):
    """
    Import NFL schedule data from nfl_data_py.

    Example:
        seasons = list(range(2018, 2026))
        schedules = import_schedules(seasons)
    """
    return nfl.import_schedules(seasons)


def create_game_results_from_schedules(schedules):
    """
    Create a clean game results dataset from NFL schedule data.
    Keeps only completed games and creates the home_team_won target.
    """
    completed_games = schedules.dropna(
        subset=["home_score", "away_score"]
    ).copy()

    completed_games["home_team_won"] = (
        completed_games["home_score"] > completed_games["away_score"]
    ).astype(int)

    game_results = completed_games[
        [
            "season",
            "week",
            "game_id",
            "gameday",
            "home_team",
            "away_team",
            "home_score",
            "away_score",
            "home_team_won",
        ]
    ].copy()

    game_results["home_point_diff"] = (
        game_results["home_score"] - game_results["away_score"]
    )

    return game_results