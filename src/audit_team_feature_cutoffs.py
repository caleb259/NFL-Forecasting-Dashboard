from pathlib import Path

import numpy as np
import pandas as pd

from backtest_model import FEATURES
from data_loader import load_game_results
from feature_engineering import create_modeling_dataset
from season_carryover import apply_scoring_carryover
from train_model import add_elo_features


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def build_features(games):
    data = create_modeling_dataset(games)
    data = apply_scoring_carryover(
        data, games, carryover_weight=4
    )
    return add_elo_features(data, games)


def audit_team_feature_cutoffs(qb_features):
    path = (
        PROJECT_ROOT
        / "data/processed/game_results_2018_2025.csv"
    )
    games = load_game_results(path).copy()
    games["gameday"] = pd.to_datetime(games["gameday"])

    if games["game_id"].duplicated().any():
        raise ValueError("Duplicate historical game IDs.")

    if games[["home_score", "away_score"]].isna().any().any():
        raise ValueError("Historical game results contain missing scores.")

    targets = qb_features.loc[
        qb_features["horizon"].eq("24 hours before"),
        ["game_id", "cutoff"],
    ].copy()

    if targets.empty or targets["game_id"].duplicated().any():
        raise ValueError("Missing or duplicate 24-hour targets.")

    missing = set(targets["game_id"]) - set(games["game_id"])
    if missing:
        raise ValueError(f"Targets missing from historical data: {missing}")

    print("\nBuilding ordinary historical team features...")
    ordinary = build_features(games).set_index("game_id")

    differences = []
    matched_games = 0

    for number, target in enumerate(
        targets.itertuples(index=False), start=1
    ):
        cutoff_date = (
            target.cutoff.tz_convert("America/New_York").date()
        )

        history = games.loc[
            games["gameday"].dt.date < cutoff_date
        ].copy()

        target_game = games.loc[
            games["game_id"].eq(target.game_id)
        ].copy()

        if target_game["gameday"].dt.date.iloc[0] <= cutoff_date:
            raise ValueError("Target game is not after its cutoff date.")

        # Include a target row so the existing builders emit its
        # pregame features. Its real outcome is deliberately withheld.
        target_game["home_score"] = 0
        target_game["away_score"] = 0

        restricted_games = pd.concat(
            [history, target_game], ignore_index=True
        )
        restricted = build_features(
            restricted_games
        ).set_index("game_id")

        before = ordinary.loc[target.game_id, FEATURES].astype(float)
        at_cutoff = restricted.loc[
            target.game_id, FEATURES
        ].astype(float)

        if not (
            np.isfinite(before.to_numpy()).all()
            and np.isfinite(at_cutoff.to_numpy()).all()
        ):
            raise ValueError(f"Invalid features for {target.game_id}")

        same = np.isclose(
            before.to_numpy(),
            at_cutoff.to_numpy(),
            rtol=1e-9,
            atol=1e-9,
        )

        if same.all():
            matched_games += 1
        else:
            for feature, matches in zip(FEATURES, same):
                if not matches:
                    differences.append({
                        "game_id": target.game_id,
                        "cutoff": target.cutoff,
                        "feature": feature,
                        "ordinary_value": before[feature],
                        "cutoff_value": at_cutoff[feature],
                    })

        if number % 25 == 0 or number == len(targets):
            print(f"Checked {number}/{len(targets)} games...")

    print("\n24-hour team-feature timing audit:")
    print(f"Games checked: {len(targets)}")
    print(f"All 13 features match: {matched_games}")
    print(f"Games with differences: {len(targets) - matched_games}")

    if differences:
        details = pd.DataFrame(differences)
        print("\nDifferences by feature:")
        print(details.groupby("feature").size().to_string())
        print("\nFirst 20 differences:")
        print(details.head(20).to_string(index=False))
    else:
        print("No differences under the calendar-date cutoff rule.")

    print("No models were trained and no files were saved.")