from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, classification_report

from data_loader import load_game_results, save_csv
from elo import create_elo_features
from feature_engineering import create_modeling_dataset



def add_elo_features(modeling_data, game_results):
    """Create Elo features and merge them into the modeling dataset."""
    elo_features = create_elo_features(game_results)

    elo_cols = [
        "game_id",
        "home_elo_before",
        "away_elo_before",
        "elo_diff",
        "home_elo_with_hfa_diff",
        "elo_home_win_prob",
    ]

    modeling_data_elo = modeling_data.merge(
        elo_features[elo_cols],
        on="game_id",
        how="left"
    )

    return modeling_data_elo


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
        "elo_diff",
        "home_elo_with_hfa_diff",
        "elo_home_win_prob",
        "strength_of_schedule_diff",
        "current_opponent_win_pct_diff",
    ]

    target = "home_team_won"


    print("Loading game results...")
    game_results = load_game_results()

    print("Creating modeling dataset...")
    modeling_data = create_modeling_dataset(game_results)

    print("Creating and merging Elo features...")
    modeling_data = add_elo_features(modeling_data, game_results)

    print("Checking for missing feature values...")
    missing_values = modeling_data[features].isna().sum()

    if missing_values.sum() > 0:
        print("Missing values found:")
        print(missing_values[missing_values > 0])
        raise ValueError("Missing values found in model features.")

    print("Splitting data...")
    train_data, test_data = split_data(modeling_data)

    X_train = train_data[features]
    y_train = train_data[target]

    X_test = test_data[features]
    y_test = test_data[target]

    print("Training Logistic Regression model with Elo and strength of schedule features...")
    model = train_model(X_train, y_train)

    print("Making predictions...")
    y_pred = model.predict(X_test)
    y_prob = model.predict_proba(X_test)[:, 1]

    accuracy = accuracy_score(y_test, y_pred)

    print()
    print("Model Results")
    print("-------------")
    print("Model: Logistic Regression with Elo and strength of schedule features")
    print("Training seasons: 2018-2024")
    print("Testing season: 2025")
    print(f"Accuracy: {accuracy:.2%}")
    print()
    print("Classification Report:")
    print(classification_report(y_test, y_pred))

    results = create_predictions(test_data, y_pred, y_prob)

    save_csv(results, output_path)

    print()
    print(f"Saved predictions to {output_path}")
    print(f"Number of predictions: {len(results)}")


if __name__ == "__main__":
    main()