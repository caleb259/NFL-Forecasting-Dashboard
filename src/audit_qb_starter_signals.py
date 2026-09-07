import pandas as pd


def audit_qb_starter_signals(passing, schedules, selections):
    completed = schedules.loc[
        schedules["game_type"].isin(["REG", "WC", "DIV", "CON", "SB"])
    ].dropna(subset=["home_score", "away_score"]).copy()

    history = pd.concat([
        completed[
            ["game_id", "season", "week", "gameday", f"{side}_team"]
        ].rename(columns={f"{side}_team": "team"})
        for side in ["home", "away"]
    ], ignore_index=True)

    history["game_date"] = pd.to_datetime(history["gameday"]).dt.date
    history = history.sort_values(
        ["team", "season", "game_date", "game_id"]
    )
    history["season_opener"] = (
        history.groupby(["team", "season"]).cumcount().eq(0)
    )

    if history.duplicated(["game_id", "team"]).any():
        raise ValueError("Duplicate team-game schedule rows.")

    rows = []

    # Keep this experiment at the already-audited 24-hour horizon.
    targets = selections.loc[
        selections["horizon"].eq("24 hours before")
    ]

    for selection in targets.itertuples(index=False):
        cutoff_date = selection.cutoff.tz_convert(
            "America/New_York"
        ).date()

        eligible = history.loc[
            history["team"].eq(selection.team)
            & (history["game_date"] < cutoff_date)
            & history["game_id"].ne(selection.game_id)
        ].sort_values(["game_date", "game_id"])

        leader_id = pd.NA
        leader_status = "no_prior_game"

        if not eligible.empty:
            latest = eligible.iloc[-1]

            # Select the latest game first; never skip it for an older one.
            game_stats = passing.loc[
                passing["season"].eq(latest["season"])
                & passing["week"].eq(latest["week"])
                & passing["passing_team"].eq(selection.team)
            ].copy()

            ids = game_stats["player_id"].astype("string")

            if game_stats.empty:
                leader_status = "missing_game_stats"
            elif (ids.isna() | ids.str.strip().eq("")).any():
                leader_status = "missing_player_id"
            else:
                game_stats["player_id"] = ids.str.strip()
                game_stats["sample"] = (
                    game_stats["attempts"] + game_stats["sacks_suffered"]
                )
                totals = game_stats.groupby("player_id")["sample"].sum()

                if totals.max() <= 0:
                    leader_status = "no_passing_sample"
                else:
                    leaders = totals.loc[totals.eq(totals.max())]
                    if len(leaders) != 1:
                        leader_status = "tied_leaders"
                    else:
                        leader_status = "identified"
                        leader_id = leaders.index[0]

        rows.append({
            "game_id": selection.game_id,
            "team": selection.team,
            "depth_chart": (
                selection.listed_qb_id
                if selection.status == "identified" else pd.NA
            ),
            "previous_starter": selection.previous_qb_id,
            "passing_leader": leader_id,
            "leader_status": leader_status,
            # Evaluation label only; never used to choose a player.
            "actual_starter": selection.recorded_qb_id,
        })

    result = pd.DataFrame(rows)

    if result.empty:
        raise ValueError("No 24-hour selections supplied.")

    result = result.merge(
        history[["game_id", "team", "season_opener"]],
        on=["game_id", "team"],
        how="left",
        validate="one_to_one",
    )

    if result["season_opener"].isna().any():
        raise ValueError("A target game is missing from the schedule.")

    signals = {
        "Depth chart": "depth_chart",
        "Previous starter": "previous_starter",
        "Latest-game passing leader": "passing_leader",
    }

    for column in list(signals.values()) + ["actual_starter"]:
        result[column] = (
            result[column].astype("string").str.strip().replace("", pd.NA)
        )

    print("\nLatest-game passing-leader selection status:")
    print(result["leader_status"].value_counts().to_string())

    availability = [
        {"Signal": name, "Cases": len(result),
         "Available": int(result[column].notna().sum())}
        for name, column in signals.items()
    ]
    print("\nStarter-signal coverage — 24 hours before:")
    print(pd.DataFrame(availability).to_string(index=False))

    paired = result.dropna(
        subset=list(signals.values()) + ["actual_starter"]
    ).copy()

    print(f"\nCases available for all three signals: {len(paired)}")
    print(f"Cases excluded from matched comparison: {len(result) - len(paired)}")

    summaries = []

    groups = {
        "All games": paired,
        "Season openers": paired.loc[paired["season_opener"]],
        "Later games": paired.loc[~paired["season_opener"]],
    }

    for period, period_rows in groups.items():
        for name, column in signals.items():
            matches = period_rows[column].eq(period_rows["actual_starter"])
            summaries.append({
                "Period": period,
                "Signal": name,
                "Compared": len(period_rows),
                "Matches": int(matches.sum()),
                "Agreement": (
                    f"{matches.mean():.2%}" if len(matches) else "Unavailable"
                ),
            })

    print("\nMatched starter agreement:")
    print(pd.DataFrame(summaries).to_string(index=False))

    all_agree = (
        paired["depth_chart"].eq(paired["previous_starter"])
        & paired["depth_chart"].eq(paired["passing_leader"])
    )
    disagreements = paired.loc[~all_agree].copy()

    print("\nCases where at least one signal differs:")
    print(f"Cases: {len(disagreements)}")

    correct = pd.DataFrame({
        name: disagreements[column].eq(disagreements["actual_starter"])
        for name, column in signals.items()
    })

    print("Correct selections by signal:")
    print(correct.sum().to_string())
    print(f"None of the signals correct: {int((~correct.any(axis=1)).sum())}")

    # A pattern identifies which signals were correct together.
    if not correct.empty:
        patterns = correct.apply(
            lambda row: " + ".join(
                name for name, value in row.items() if value
            ) or "None correct",
            axis=1,
        )
        print("\nCorrect-signal combinations among disagreements:")
        print(patterns.value_counts().to_string())

    print("\nEvaluation only: no models trained or files saved.")