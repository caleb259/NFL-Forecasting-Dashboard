from pathlib import Path

import pandas as pd
from sklearn.linear_model import LogisticRegression

from data_loader import load_game_results
from feature_engineering import create_modeling_dataset
from train_model import add_elo_features
from evaluate_predictions import evaluate
from season_carryover import apply_scoring_carryover


PROJECT_ROOT = Path(__file__).resolve().parents[1]
GAMES_PATH = PROJECT_ROOT / "data/processed/game_results_2018_2025.csv"

TEST_SEASONS = [2025]

FEATURES = [
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


def main():
    games = load_game_results(GAMES_PATH)

    games = games.loc[
        games["season"].between(2018, max(TEST_SEASONS))
    ].copy()

    if games.empty:
        raise ValueError("No games were found for the backtest.")

    if games["game_id"].duplicated().any():
        raise ValueError("The game data contains duplicate game IDs.")

    if games[["home_score", "away_score"]].isna().any().any():
        raise ValueError("The historical data contains incomplete games.")

    print("Building historical pregame features...")

    # Keep ties here so their scores and Elo updates remain in history.
    modeling_data = create_modeling_dataset(games)
    modeling_data = add_elo_features(modeling_data, games)

    if modeling_data[FEATURES].isna().any().any():
        raise ValueError("Some model features are missing.")

    # Exclude ties only after creating the historical features.
    decisive_games = modeling_data.loc[
        modeling_data["home_score"] != modeling_data["away_score"]
    ].copy()

    decisive_games["home_team_won"] = (
        decisive_games["home_score"] > decisive_games["away_score"]
    ).astype(int)

    carryover_datasets = {
        weight: apply_scoring_carryover(
            decisive_games, games, carryover_weight=weight
        )
        for weight in [0, 4]
    }

    for weight, dataset in carryover_datasets.items():
        if dataset[FEATURES].isna().any().any():
            raise ValueError(f"Missing features for carryover weight {weight}.")

    season_results = []
    prediction_history = []

    for test_season in TEST_SEASONS:
        training = decisive_games.loc[
            decisive_games["season"].between(2018, test_season - 1)
        ].copy()

        testing = decisive_games.loc[
            decisive_games["season"] == test_season
        ].copy()

        if training.empty or testing.empty:
            raise ValueError(f"Missing training or test data for {test_season}.")

        print(
            f"Training on 2018–{test_season - 1}; "
            f"testing on {test_season} "
            f"({len(testing)} games)..."
        )

        probability_sets = {}

        for weight, dataset in carryover_datasets.items():
            # Use exactly the same training and test games for each version.
            variant_training = dataset.loc[training.index]
            variant_testing = dataset.loc[testing.index]

            model = LogisticRegression(max_iter=1000)
            model.fit(
                variant_training[FEATURES],
                variant_training["home_team_won"],
            )

            name = (
                "Original features (weight 0)"
                if weight == 0
                else f"Carryover weight {weight}"
            )

            probability_sets[name] = pd.Series(
                model.predict_proba(variant_testing[FEATURES])[:, 1],
                index=testing.index,
            )

        home_win_rate = training["home_team_won"].mean()

        probability_sets["Elo alone"] = testing["elo_home_win_prob"]
        probability_sets["Home-win baseline"] = pd.Series(
            home_win_rate, index=testing.index
        )

        for name, probabilities in probability_sets.items():
            result = evaluate(
                name,
                testing["home_team_won"],
                probabilities,
            )
            result["Season"] = test_season
            result["Games"] = len(testing)
            season_results.append(result)

            prediction_history.append(pd.DataFrame({
                "Approach": name,
                "Season": test_season,
                "Week": testing['week'].to_numpy(),
                "Actual": testing["home_team_won"].to_numpy(),
                "Probability": probabilities.to_numpy(),
            }))

    formatters = {
        "Accuracy": "{:.2%}".format,
        "Brier score": "{:.4f}".format,
        "Log loss": "{:.4f}".format,
    }

    season_table = pd.DataFrame(season_results)[
        ["Season", "Games", "Approach", "Accuracy", "Brier score", "Log loss"]
    ]

    print("\nResults by test season:\n")
    print(season_table.to_string(index=False, formatters=formatters))

    # Pool the actual predictions rather than average rounded season scores.
    history = pd.concat(prediction_history, ignore_index=True)
    pooled_results = []

    for name, rows in history.groupby("Approach", sort=False):
        result = evaluate(name, rows["Actual"], rows["Probability"])
        result["Games"] = len(rows)
        pooled_results.append(result)

    pooled_table = pd.DataFrame(pooled_results)[
        ["Games", "Approach", "Accuracy", "Brier score", "Log loss"]
    ]

    print("\nCombined results across 2025:\n")
    print(pooled_table.to_string(index=False, formatters=formatters))

    early_history = history.loc[history["Week"].between(1, 4)]
    early_results = []

    for name, rows in early_history.groupby("Approach", sort=False):
        result = evaluate(name, rows["Actual"], rows["Probability"])
        result["Games"] = len(rows)
        early_results.append(result)

    early_table = pd.DataFrame(early_results)[
        ["Games", "Approach", "Accuracy", "Brier score", "Log loss"]
    ]

    print("\nWeeks 1–4 across 2025:\n")
    print(early_table.to_string(index=False, formatters=formatters))

    print("\nTies excluded from classifier training and evaluation.")
    print("Historical features still include information from tied games.")
    print("No prediction files were changed.")


if __name__ == "__main__":
    main()