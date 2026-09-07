import warnings

import numpy as np
import pandas as pd
from sklearn.exceptions import ConvergenceWarning
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    brier_score_loss,
    log_loss,
)

from audit_team_feature_cutoffs import PROJECT_ROOT, build_features
from backtest_model import FEATURES
from data_loader import load_game_results


def summarize(rows):
    actual = rows["actual_home_win"].to_numpy()
    probability = rows["home_win_probability"].to_numpy()

    return {
        "Games": len(rows),
        "Accuracy": accuracy_score(actual, probability >= 0.5),
        "Brier score": brier_score_loss(actual, probability),
        "Log loss": log_loss(actual, probability, labels=[0, 1]),
    }


def print_results(rows, groups):
    summaries = []

    grouper = groups[0] if len(groups) == 1 else groups
    for group, values in rows.groupby(grouper):
        if not isinstance(group, tuple):
            group = (group,)

        summaries.append({
            **dict(zip(groups, group)),
            **summarize(values),
        })

    print(pd.DataFrame(summaries).to_string(
        index=False,
        formatters={
            "Accuracy": lambda x: f"{x:.2%}",
            "Brier score": lambda x: f"{x:.4f}",
            "Log loss": lambda x: f"{x:.4f}",
        },
    ))


def backtest_qb_feature(qb_features):
    path = (
        PROJECT_ROOT
        / "data/processed/game_results_2018_2025.csv"
    )
    games = load_game_results(path).copy()

    if games["game_id"].duplicated().any():
        raise ValueError("Duplicate historical game IDs.")

    if games[["home_score", "away_score"]].isna().any().any():
        raise ValueError("Historical results contain missing scores.")

    # Earlier seasons supply feature history, but classifier fitting
    # in this experiment uses only earlier games within 2025.
    historical = build_features(games)
    historical = historical.loc[
        historical["season"].eq(2025)
    ].copy()

    qb = qb_features.loc[
        qb_features["horizon"].eq("24 hours before"),
        ["game_id", "cutoff", "qb_rating_diff"],
    ].copy()

    if set(qb["game_id"]) != set(historical["game_id"]):
        raise ValueError("QB and historical game coverage differ.")

    data = historical.merge(
        qb,
        on="game_id",
        how="left",
        validate="one_to_one",
    )

    columns = FEATURES + ["qb_rating_diff"]

    if not np.isfinite(data[columns].to_numpy(dtype=float)).all():
        raise ValueError("Missing or non-finite model inputs.")

    if data["cutoff"].isna().any():
        raise ValueError("Missing forecast cutoffs.")

    data["game_date"] = pd.to_datetime(data["gameday"]).dt.date
    data["actual_home_win"] = (
        data["home_score"] > data["away_score"]
    ).astype(int)

    ties = data["home_score"].eq(data["away_score"])
    print(f"\nTies excluded from classifier fitting/evaluation: {ties.sum()}")
    data = data.loc[~ties].copy()

    approaches = {
        "Existing features": FEATURES,
        "Existing features + QB": FEATURES + ["qb_rating_diff"],
    }

    predictions = []
    coefficient_checks = []

    for week in sorted(data.loc[data["week"].ge(9), "week"].unique()):
        testing = data.loc[data["week"].eq(week)].copy()

        # Freeze each week's fitted models before its earliest forecast.
        training_cutoff = testing["cutoff"].min()
        cutoff_date = training_cutoff.tz_convert(
            "America/New_York"
        ).date()

        training = data.loc[
            data["week"].lt(week)
            & (data["game_date"] < cutoff_date)
        ].copy()

        if training.empty or training["actual_home_win"].nunique() != 2:
            raise ValueError(f"Insufficient training classes for Week {week}.")

        print(
            f"Week {week}: training on {len(training)} earlier games; "
            f"testing on {len(testing)} games."
        )

        for name, feature_columns in approaches.items():
            model = LogisticRegression(max_iter=1000)

            # Stop rather than silently accepting an unfinished fit.
            with warnings.catch_warnings():
                warnings.simplefilter("error", ConvergenceWarning)
                model.fit(
                    training[feature_columns],
                    training["actual_home_win"],
                )

            if name == "Existing features + QB":
                qb_index = feature_columns.index("qb_rating_diff")
                qb_coefficient = float(model.coef_[0, qb_index])

                # Logistic regression adds this term to its log-odds score.
                qb_contribution = (
                    testing["qb_rating_diff"].to_numpy()
                    * qb_coefficient
                )

                coefficient_checks.append({
                    "Week": week,
                    "Training games": len(training),
                    "QB coefficient": qb_coefficient,
                    "Minimum QB contribution": qb_contribution.min(),
                    "Maximum QB contribution": qb_contribution.max(),
                })

            probability = model.predict_proba(
                testing[feature_columns]
            )[:, list(model.classes_).index(1)]

            result = testing[
                ["game_id", "week", "actual_home_win"]
            ].copy()
            result["Approach"] = name
            result["home_win_probability"] = probability
            predictions.append(result)

    if not predictions:
        raise ValueError("No test predictions were generated.")

    predictions = pd.concat(predictions, ignore_index=True)

    if predictions.duplicated(["game_id", "Approach"]).any():
        raise ValueError("A game was predicted twice by the same approach.")

    paired = predictions.pivot(
        index="game_id",
        columns="Approach",
        values="home_win_probability",
    )
    if paired.isna().any().any():
        raise ValueError("The models were not evaluated on identical games.")

    # Compare the two predictions for each evaluated game.
    baseline = predictions.loc[
        predictions["Approach"].eq("Existing features"),
        ["game_id", "week", "actual_home_win", "home_win_probability"],
    ].rename(columns={
        "home_win_probability": "baseline_probability",
    })

    with_qb = predictions.loc[
        predictions["Approach"].eq("Existing features + QB"),
        ["game_id", "home_win_probability"],
    ].rename(columns={
        "home_win_probability": "qb_probability",
    })

    changes = baseline.merge(
        with_qb,
        on="game_id",
        validate="one_to_one",
    )

    context = qb_features.loc[
        qb_features["horizon"].eq("24 hours before"),
        [
            "game_id",
            "home_listed_qb",
            "away_listed_qb",
            "qb_rating_diff",
            "home_prior_attempts_plus_sacks",
            "away_prior_attempts_plus_sacks",
            "home_signals_disagree",
            "away_signals_disagree",
        ],
    ]

    changes = changes.merge(
        context,
        on="game_id",
        how="left",
        validate="one_to_one",
    )

    # Percentage-point change in the HOME team's win probability.
    changes["home_probability_change_pp"] = 100 * (
        changes["qb_probability"] - changes["baseline_probability"]
    )

    actual = changes["actual_home_win"]
    changes["brier_improvement"] = (
        (changes["baseline_probability"] - actual) ** 2
        - (changes["qb_probability"] - actual) ** 2
    )

    baseline_pick = changes["baseline_probability"].ge(0.5)
    qb_pick = changes["qb_probability"].ge(0.5)
    changes["pick_changed"] = baseline_pick.ne(qb_pick)

    changes["baseline_correct"] = baseline_pick.eq(actual)
    changes["qb_correct"] = qb_pick.eq(actual)

    largest = changes.loc[
        changes["home_probability_change_pp"]
        .abs()
        .sort_values(ascending=False)
        .head(15)
        .index
    ]

    print("\nLargest probability changes — 15 games:")
    print(largest[
        [
            "game_id",
            "home_listed_qb",
            "away_listed_qb",
            "actual_home_win",
            "baseline_probability",
            "qb_probability",
            "home_probability_change_pp",
            "brier_improvement",
            "qb_rating_diff",
            "home_prior_attempts_plus_sacks",
            "away_prior_attempts_plus_sacks",
            "home_signals_disagree",
            "away_signals_disagree",
        ]
    ].to_string(
        index=False,
        float_format=lambda value: f"{value:.4f}",
    ))

    flipped = changes.loc[changes["pick_changed"]]

    print("\nWinner-pick changes:")
    print(f"Games with a different pick: {len(flipped)}")
    print(
        "Wrong pick changed to correct:",
        int((~flipped["baseline_correct"] & flipped["qb_correct"]).sum()),
    )
    print(
        "Correct pick changed to wrong:",
        int((flipped["baseline_correct"] & ~flipped["qb_correct"]).sum()),
    )

    print("\nQB coefficient by test week:")
    print(pd.DataFrame(coefficient_checks).to_string(
        index=False,
        float_format=lambda value: f"{value:.4f}",
    ))

    print("\nResults by test week:")
    print_results(predictions, ["week", "Approach"])

    print("\nCombined results — Week 9 onward, including postseason:")
    print_results(predictions, ["Approach"])

    predictions["Period"] = np.where(
        predictions["week"].le(18),
        "Weeks 9–18",
        "Postseason",
    )
    print("\nResults by season period:")
    print_results(predictions, ["Period", "Approach"])

    print(
        "\nExploratory 2025 comparison. Both classifiers fit only "
        "earlier 2025 games; historical features use earlier seasons."
    )
    print("No models or prediction files were saved.")