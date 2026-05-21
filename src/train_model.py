import os
import pandas as pd

from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, classification_report


def load_data(filepath):
    """Load the modeling dataset."""
    return pd.read_csv(filepath)


def split_data(modeling_data):
    """Split data into training seasons and testing season."""
    train_data = modeling_data[
        modeling_data["season"].between(2018, 2024)
    ].copy()

    test_data = modeling_data[
        modeling_data["season"] == 2025
    ].copy()

    return train_data, test_data


def train_model(X_train, y_train):
    """Train the logistic regression model."""
    model = LogisticRegression(max_iter=1000)
    model.fit(X_train, y_train)

    return model


def create_predictions(test_data, y_pred, y_prob):
    """Create a results table with predicted and actual winners."""
    results = test_data[
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

    results["predicted_home_win"] = y_pred
    results["home_win_probability"] = y_prob

    results["predicted_winner"] = results.apply(
        lambda row: row["home_team"]
        if row["predicted_home_win"] == 1
        else row["away_team"],
        axis=1,
    )

    results["actual_winner"] = results.apply(
        lambda row: row["home_team"]
        if row["home_team_won"] == 1
        else row["away_team"],
        axis=1,
    )

    results["correct_prediction"] = (
        results["predicted_winner"] == results["actual_winner"]
    )

    return results


def main():
    data_path = "data/processed/modeling_dataset_expanded_2018_2025.csv"
    output_path = "data/predictions/best_logistic_regression_predictions.csv"

    features = [
        "avg_points_scored_diff",
        "avg_points_allowed_diff",
        "avg_point_diff_diff",
        "win_pct_diff",
        "last3_avg_points_scored_diff",
        "last3_avg_points_allowed_diff",
        "last3_avg_point_diff_diff",
        "last3_win_pct_diff",
    ]

    target = "home_team_won"

    print("Loading modeling data...")
    modeling_data = load_data(data_path)

    print("Splitting data...")
    train_data, test_data = split_data(modeling_data)

    X_train = train_data[features]
    y_train = train_data[target]

    X_test = test_data[features]
    y_test = test_data[target]

    print("Training Logistic Regression model...")
    model = train_model(X_train, y_train)

    print("Making predictions...")
    y_pred = model.predict(X_test)
    y_prob = model.predict_proba(X_test)[:, 1]

    accuracy = accuracy_score(y_test, y_pred)

    print()
    print("Model Results")
    print("-------------")
    print(f"Accuracy: {accuracy:.2%}")
    print()
    print("Classification Report:")
    print(classification_report(y_test, y_pred))

    results = create_predictions(test_data, y_pred, y_prob)

    os.makedirs("data/predictions", exist_ok=True)

    results.to_csv(output_path, index=False)

    print()
    print(f"Saved predictions to {output_path}")
    print(f"Number of predictions: {len(results)}")


if __name__ == "__main__":
    main()