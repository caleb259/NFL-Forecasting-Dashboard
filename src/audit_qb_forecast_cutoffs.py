import pandas as pd
import nfl_data_py as nfl
from audit_qb_passing_history import audit_passing_history
from build_qb_game_features import build_qb_game_features
from audit_team_feature_cutoffs import audit_team_feature_cutoffs
from backtest_qb_feature import backtest_qb_feature
from audit_qb_evidence_pilot import audit_qb_evidence_pilot

def select_qb(team_history, cutoff):
    """Select from the latest team snapshot strictly before the cutoff."""
    available = team_history.loc[
        team_history["snapshot_time"] < cutoff
    ]

    result = {
        "snapshot_time": pd.NaT,
        "snapshot_age_hours": float("nan"),
        "listed_qb": None,
        "listed_qb_id": None,
        "status": "no_snapshot",
    }

    if available.empty:
        return result

    latest_time = available["snapshot_time"].max()
    snapshot = available.loc[
        available["snapshot_time"] == latest_time
    ]

    result["snapshot_time"] = latest_time
    result["snapshot_age_hours"] = (
        cutoff - latest_time
    ).total_seconds() / 3600

    # Filter only AFTER choosing the latest complete team snapshot.
    first_choice = snapshot.loc[
        snapshot["pos_abb"].astype(str).str.upper().str.strip().eq("QB")
        & snapshot["pos_rank"].eq(1)
    ]

    if first_choice.empty:
        result["status"] = "no_rank_one_qb"
    elif len(first_choice) > 1:
        result["status"] = "multiple_rank_one_rows"
    else:
        player = first_choice.iloc[0]
        result["listed_qb"] = player["player_name"]

        player_id = player["gsis_id"]
        if pd.isna(player_id) or not str(player_id).strip():
            result["status"] = "missing_player_id"
        else:
            result["listed_qb_id"] = str(player_id).strip()
            result["status"] = "identified"

    return result


def compare_previous_starters(audit, schedules):
    """Compare two QB signals without using target-game starters as inputs."""
    completed = schedules.loc[
        schedules["game_type"].isin(["REG", "WC", "DIV", "CON", "SB"])
    ].dropna(subset=["home_score", "away_score"]).copy()

    team_rows = []

    for side in ["home", "away"]:
        rows = completed[
            ["game_id", "gameday", f"{side}_team", f"{side}_qb_id"]
        ].rename(columns={
            f"{side}_team": "team",
            f"{side}_qb_id": "previous_qb_id",
        })
        team_rows.append(rows)

    history = pd.concat(team_rows, ignore_index=True)
    history["game_date"] = pd.to_datetime(history["gameday"]).dt.date
    history["previous_qb_id"] = (
        history["previous_qb_id"]
        .astype("string")
        .str.strip()
        .replace("", pd.NA)
    )

    comparison = audit.copy()
    previous_ids = []
    previous_ages = []

    for _, row in comparison.iterrows():
        cutoff_date = row["cutoff"].tz_convert("America/New_York").date()

        eligible = history.loc[
            history["team"].eq(row["team"])
            & (history["game_date"] < cutoff_date)
            & history["game_id"].ne(row["game_id"])
        ].sort_values("game_date")

        if eligible.empty:
            previous_ids.append(pd.NA)
            previous_ages.append(float("nan"))
            continue

        # Select the latest game first. Do not skip missing QB IDs
        # by silently reaching back to an older game.
        previous = eligible.iloc[-1]
        previous_ids.append(previous["previous_qb_id"])
        previous_ages.append(
            (cutoff_date - previous["game_date"]).days
        )

    comparison["previous_qb_id"] = pd.array(previous_ids, dtype="string")
    comparison["previous_game_age_days"] = previous_ages

    summary = []
    agreement_groups = []

    for horizon, rows in comparison.groupby("horizon"):
        for name, column in [
            ("Depth-chart rank one", "listed_qb_id"),
            ("Previous starter", "previous_qb_id"),
        ]:
            available = rows[column].notna()
            usable = rows.loc[
                available & rows["recorded_qb_id"].notna()
            ]
            matches = usable[column].eq(usable["recorded_qb_id"])

            summary.append({
                "Cutoff": horizon,
                "Signal": name,
                "Available": int(available.sum()),
                "Compared": len(usable),
                "Matches": int(matches.sum()),
                "Agreement": (
                    f"{matches.mean():.2%}" if len(usable) else "Unavailable"
                ),
            })

        # Compare both signals on exactly the same eligible cases.
        paired = rows.dropna(subset=[
            "listed_qb_id", "previous_qb_id", "recorded_qb_id"
        ]).copy()

        signals_agree = paired["listed_qb_id"].eq(paired["previous_qb_id"])

        for label, mask in [
            ("Signals agree", signals_agree),
            ("Signals disagree", ~signals_agree),
        ]:
            group = paired.loc[mask]
            depth_correct = group["listed_qb_id"].eq(group["recorded_qb_id"])
            previous_correct = group["previous_qb_id"].eq(
                group["recorded_qb_id"]
            )

            agreement_groups.append({
                "Cutoff": horizon,
                "Group": label,
                "Cases": len(group),
                "Depth correct": int(depth_correct.sum()),
                "Previous correct": int(previous_correct.sum()),
                "Neither correct": int(
                    (~depth_correct & ~previous_correct).sum()
                ),
            })

    print("\nQB signal comparison:")
    print(pd.DataFrame(summary).to_string(index=False))

    print("\nPerformance when the signals agree or disagree:")
    print(pd.DataFrame(agreement_groups).to_string(index=False))

    print("\nAge of previous-game information, in calendar days:")
    print(
        comparison.groupby("horizon")["previous_game_age_days"]
        .agg(["count", "median", "max"])
        .to_string()
    )

    print(
        "\nPrevious starters are reconstructed from historical records. "
        "Exact record-publication times are not verified."
    )

    return comparison

def main():
    print("Loading 2025 schedules and depth-chart snapshots...")
    schedules = nfl.import_schedules([2023, 2024, 2025])
    depth = nfl.import_depth_charts([2025]).copy()

    # Include completed regular-season and postseason games, including ties.
    games = schedules.loc[
        schedules["season"].eq(2025)
        & schedules["game_type"].isin(["REG", "WC", "DIV", "CON", "SB"])
    ].dropna(subset=["home_score", "away_score"]).copy()

    if games.empty or games["game_id"].duplicated().any():
        raise ValueError("The game list is empty or contains duplicates.")

    local_kickoff = pd.to_datetime(
        games["gameday"].astype(str)
        + " "
        + games["gametime"].astype(str),
        errors="coerce",
    )

    if local_kickoff.isna().any():
        raise ValueError("Some kickoff dates/times could not be parsed.")

    games["kickoff_utc"] = (
        local_kickoff.dt.tz_localize(
            "America/New_York",
            ambiguous="raise",
            nonexistent="raise",
        )
        .dt.tz_convert("UTC")
    )

    depth["snapshot_time"] = pd.to_datetime(
        depth["dt"], utc=True, errors="coerce"
    )

    if depth["snapshot_time"].isna().any():
        raise ValueError("Depth-chart data contains invalid timestamps.")

    depth["pos_rank"] = pd.to_numeric(
        depth["pos_rank"], errors="coerce"
    )

    team_histories = {
        team: rows
        for team, rows in depth.groupby("team")
    }
    empty_history = depth.iloc[:0]
    audit_rows = []

    for _, game in games.iterrows():
        for horizon, hours in [
            ("Seven days before", 168),
            ("24 hours before", 24),
        ]:
            cutoff = game["kickoff_utc"] - pd.Timedelta(hours=hours)

            for side in ["away", "home"]:
                team = game[f"{side}_team"]
                selection = select_qb(
                    team_histories.get(team, empty_history),
                    cutoff,
                )

                audit_rows.append({
                    "game_id": game["game_id"],
                    "team": team,
                    "horizon": horizon,
                    "cutoff": cutoff,
                    "recorded_qb_id": game.get(f"{side}_qb_id"),
                    "recorded_qb_name": game.get(f"{side}_qb_name"),
                    **selection,
                })

    audit = pd.DataFrame(audit_rows)

    print(f"\nCompleted games: {len(games)}")
    print(f"Audit rows: {len(audit)}")
    print("Each game has two teams and two forecast cutoffs.")

    print("\nSelection status by cutoff:")
    print(pd.crosstab(
        audit["horizon"], audit["status"]
    ).to_string())

    age_summary = audit.groupby("horizon")[
        "snapshot_age_hours"
    ].agg(["count", "median", "max"])

    print("\nSnapshot age in hours at the forecast cutoff:")
    print(age_summary.round(2).to_string())

    print("\nSnapshots older than 48 hours:")
    print(
        audit.assign(
            older_than_48h=audit["snapshot_age_hours"] > 48
        )
        .groupby("horizon")["older_than_48h"]
        .sum()
        .to_string()
    )

    problems = audit.loc[
        audit["status"].ne("identified")
        | audit["snapshot_age_hours"].gt(48)
    ]

    print("\nMissing, ambiguous, or older-than-48-hour selections:")
    if problems.empty:
        print("None.")
    else:
        print(problems[
            [
                "game_id", "team", "horizon", "status",
                "listed_qb", "snapshot_age_hours",
            ]
        ].head(30).to_string(index=False))
        print(f"Total flagged rows: {len(problems)}")

    selections = audit.pivot(
        index=["game_id", "team"],
        columns="horizon",
        values="listed_qb_id",
    )

    comparable = selections.dropna()
    changed = (
        comparable["Seven days before"]
        != comparable["24 hours before"]
    )

    print(
        "\nTeams with an identified QB at both cutoffs: "
        f"{len(comparable)}"
    )
    print(f"Listed QB changed between cutoffs: {int(changed.sum())}")

    print("\nExample selections:")
    print(audit[
        [
            "game_id", "team", "horizon",
            "listed_qb", "status", "snapshot_age_hours",
        ]
    ].head(12).to_string(index=False))

    # Recorded starters are retrospective comparison labels only.
    recorded_ids = (
        audit["recorded_qb_id"]
        .astype("string")
        .str.strip()
        .replace("", pd.NA)
    )
    audit["recorded_qb_id"] = recorded_ids

    agreement_results = []

    for horizon, rows in audit.groupby("horizon"):
        usable = rows.loc[
            rows["status"].eq("identified")
            & rows["recorded_qb_id"].notna()
        ].copy()

        matches = (
            usable["listed_qb_id"] == usable["recorded_qb_id"]
        )

        agreement_results.append({
            "Cutoff": horizon,
            "Team-games": len(rows),
            "Comparable": len(usable),
            "Matches": int(matches.sum()),
            "Disagreements": int((~matches).sum()),
            "Agreement": (
                f"{matches.mean():.2%}" if len(usable) else "Unavailable"
            ),
        })

    print("\nAgreement with recorded starting quarterbacks:")
    print(pd.DataFrame(agreement_results).to_string(index=False))

    disagreements = audit.loc[
        audit["status"].eq("identified")
        & audit["recorded_qb_id"].notna()
        & audit["listed_qb_id"].ne(audit["recorded_qb_id"])
    ]

    print("\nDisagreement examples — up to 30 rows:")
    if disagreements.empty:
        print("None.")
    else:
        print(disagreements[
            [
                "game_id",
                "team",
                "horizon",
                "listed_qb",
                "recorded_qb_name",
                "snapshot_age_hours",
            ]
        ].head(30).to_string(index=False))

    comparison = compare_previous_starters(audit, schedules)
    ratings = audit_passing_history(comparison, schedules)

    features = build_qb_game_features(games, comparison, ratings)

    print("\nGame-level QB feature coverage:")
    print(features.groupby("horizon").agg(
        games=("game_id", "size"),
        both_ratings_available=("both_ratings_available", "sum"),
    ).to_string())

    print("\nGame-level QB feature preview:")
    print(features[
        [
            "game_id",
            "horizon",
            "home_listed_qb",
            "away_listed_qb",
            "home_adjusted_anya",
            "away_adjusted_anya",
            "qb_rating_diff",
            "home_prior_attempts_plus_sacks",
            "away_prior_attempts_plus_sacks",
            "home_signals_disagree",
            "away_signals_disagree",
        ]
    ].head(12).to_string(
        index=False,
        float_format=lambda value: f"{value:.3f}",
    ))

    print(f"\nTotal game/cutoff rows: {len(features)}")
    audit_qb_evidence_pilot(audit)
    print("\nAudit complete. No model or forecast files were changed.")


if __name__ == "__main__":
    main()