from pathlib import Path

import pandas as pd
from sklearn.metrics import accuracy_score, brier_score_loss, log_loss


PROJECT_ROOT = Path(__file__).resolve().parents[1]

PREDICTIONS_PATH = (
    PROJECT_ROOT
    / "data/predictions/best_logistic_regression_predictions.csv"
)
GAMES_PATH = PROJECT_ROOT / "data/processed/game_results_2018_2025.csv"


def evaluate(name, actual, probabilities):
    """Measure winner accuracy and probability quality."""
    probabilities = pd.to_numeric(probabilities, errors="raise")

    if probabilities.isna().any() or not probabilities.between(0, 1).all():
        raise ValueError(f"{name} contains missing or invalid probabilities.")

    predicted_home_win = (probabilities >= 0.5).astype(int)

    return {
        "Approach": name,
        "Accuracy": accuracy_score(actual, predicted_home_win),
        "Brier score": brier_score_loss(actual, probabilities),
        "Log loss": log_loss(actual, probabilities, labels=[0, 1]),
    }


def main():
    predictions = pd.read_csv(PREDICTIONS_PATH)
    games = pd.read_csv(GAMES_PATH)

    if predictions["game_id"].duplicated().any():
        raise ValueError("The prediction file contains duplicate games.")

    if not predictions["season"].eq(2025).all():
        raise ValueError("This evaluation expects only 2025 predictions.")

    if predictions[["home_score", "away_score"]].isna().any().any():
        raise ValueError("Some test games do not have final scores.")

    # Estimate the constant baseline using training seasons only.
    training_games = games.loc[
        games["season"].between(2018, 2024)
    ].dropna(subset=["home_score", "away_score"])

    training_games = training_games.loc[
        training_games["home_score"] != training_games["away_score"]
    ]

    if training_games.empty:
        raise ValueError("No completed, non-tied training games were found.")

    home_win_rate = (
        training_games["home_score"] > training_games["away_score"]
    ).mean()

    ties = predictions["home_score"] == predictions["away_score"]
    test_games = predictions.loc[~ties].copy()

    if test_games.empty:
        raise ValueError("No non-tied test games were found.")

    # Derive the actual outcome from scores rather than saved winner labels.
    actual = (
        test_games["home_score"] > test_games["away_score"]
    ).astype(int)

    baseline_probabilities = pd.Series(
        home_win_rate, index=test_games.index
    )

    results = pd.DataFrame([
        evaluate(
            "Current model",
            actual,
            test_games["home_win_probability"],
        ),
        evaluate(
            "Elo alone",
            actual,
            test_games["elo_home_win_prob"],
        ),
        evaluate(
            "Constant home-win baseline",
            actual,
            baseline_probabilities,
        ),
    ])

    print(f"\nTest season: 2025")
    print(f"Games evaluated: {len(test_games)}")
    print(f"Tied games excluded: {int(ties.sum())}")
    print(f"Training home-win rate: {home_win_rate:.2%}\n")

    print(results.to_string(
        index=False,
        formatters={
            "Accuracy": "{:.2%}".format,
            "Brier score": "{:.4f}".format,
            "Log loss": "{:.4f}".format,
        },
    ))

    period_results = []

    periods = {
        "Weeks 1–4": test_games["week"].between(1, 4),
        "Weeks 5–18": test_games["week"].between(5, 18),
        "Postseason": test_games["week"] > 18,
    }

    for period, mask in periods.items():
        subset = test_games.loc[mask]

        if subset.empty:
            continue

        subset_actual = (
            subset["home_score"] > subset["away_score"]
        ).astype(int)

        for name, column in [
            ("Current model", "home_win_probability"),
            ("Elo alone", "elo_home_win_prob"),
        ]:
            result = evaluate(name, subset_actual, subset[column])
            result["Period"] = period
            result["Games"] = len(subset)
            period_results.append(result)

    period_table = pd.DataFrame(period_results)[
        ["Period", "Games", "Approach", "Accuracy", "Brier score", "Log loss"]
    ]

    print("\nPerformance by season period:\n")
    print(period_table.to_string(
        index=False,
        formatters={
            "Accuracy": "{:.2%}".format,
            "Brier score": "{:.4f}".format,
            "Log loss": "{:.4f}".format,
        },
    ))
    
    print("\nHigher accuracy is better.")
    print("Lower Brier score and log loss are better.")


if __name__ == "__main__":
    main()