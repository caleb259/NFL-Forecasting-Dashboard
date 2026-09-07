import pandas as pd


def audit_qb_change(passing, schedules, ratings, rating_function):
    # Use the horizon already validated for the existing team features.
    selections = ratings.loc[
        ratings["horizon"].eq("24 hours before")
    ].copy()

    completed = schedules.loc[
        schedules["game_type"].isin(["REG", "WC", "DIV", "CON", "SB"])
    ].dropna(subset=["home_score", "away_score"]).copy()

    team_games = pd.concat([
        completed[
            ["game_id", "season", "week", "gameday", f"{side}_team"]
        ].rename(columns={f"{side}_team": "passing_team"})
        for side in ["home", "away"]
    ], ignore_index=True)

    team_games["game_date"] = pd.to_datetime(
        team_games["gameday"]
    ).dt.date

    keys = ["season", "week", "passing_team"]

    if team_games.duplicated(keys).any():
        raise ValueError("Duplicate team/game schedule keys.")

    stats = passing.copy()
    stats["denominator"] = (
        stats["attempts"] + stats["sacks_suffered"]
    )

    rows = []

    for selection in selections.itertuples(index=False):
        cutoff_date = selection.cutoff.tz_convert(
            "America/New_York"
        ).date()

        # Choose games from the schedule first, so missing statistics
        # cannot silently make us reach back to an older game.
        recent = team_games.loc[
            team_games["passing_team"].eq(selection.team)
            & (team_games["game_date"] < cutoff_date)
            & team_games["game_id"].ne(selection.game_id)
        ].sort_values(["game_date", "game_id"]).tail(3)

        recent_stats = stats.merge(
            recent[keys],
            on=keys,
            how="inner",
            validate="many_to_one",
        )

        covered_games = len(recent_stats[keys].drop_duplicates())
        sample = recent_stats["denominator"].sum()

        if recent.empty:
            status = "no_prior_games"
        elif covered_games != len(recent):
            status = "missing_game_stats"
        elif sample <= 0:
            status = "no_passing_sample"
        elif len(recent) < 3:
            status = "fewer_than_three_games"
        else:
            status = "complete"

        # Only produce the candidate difference for complete windows.
        recent_rating = float("nan")
        difference = float("nan")
        starter_share = float("nan")

        if status == "complete":
            player_ids = recent_stats["player_id"].astype("string")

            if (
                player_ids.isna()
                | player_ids.str.strip().eq("")
            ).any():
                raise ValueError("Missing player ID in recent passing history.")

            contributions = recent_stats.groupby(
                "player_id"
            )["denominator"].sum()

            if abs(contributions.sum() - sample) > 1e-9:
                raise ValueError("Player contributions do not match team sample.")

            weighted_total = 0.0
            participant_ratings = []

            for player_id, player_sample in contributions.items():
                if player_sample <= 0:
                    continue

                rating = rating_function(
                    passing,
                    player_id,
                    selection.cutoff,
                    prior_weight=100,
                )
                player_rating = rating["adjusted_anya"]

                weighted_total += player_sample * player_rating
                participant_ratings.append(player_rating)

            recent_rating = weighted_total / sample
            difference = selection.adjusted_anya - recent_rating

            starter_sample = contributions.get(selection.player_id, 0)
            starter_share = starter_sample / sample

            # A weighted average must stay within its component ratings.
            if not (
                min(participant_ratings) - 1e-9
                <= recent_rating
                <= max(participant_ratings) + 1e-9
            ):
                raise ValueError("QB mix rating is outside participant ratings.")

            # With only the listed starter, both sides must be identical.
            if starter_sample == sample and abs(difference) > 1e-9:
                raise ValueError(
                    "Nonzero difference when the starter supplied all attempts."
                )

        rows.append({
            "game_id": selection.game_id,
            "team": selection.team,
            "listed_qb": selection.listed_qb,
            "listed_qb_id": selection.player_id,
            "status": status,
            "recent_games": len(recent),
            "games_with_stats": covered_games,
            "recent_attempts_plus_sacks": sample,
            "starter_history_sample": selection.prior_attempts_plus_sacks,
            "days_since_latest_game": (
                (cutoff_date - recent["game_date"].max()).days
                if not recent.empty else float("nan")
            ),
            "days_since_oldest_game": (
                (cutoff_date - recent["game_date"].min()).days
                if not recent.empty else float("nan")
            ),
            "starter_share_of_recent_sample": starter_share,
            "starter_adjusted_anya": selection.adjusted_anya,
            "recent_qb_mix_rating": recent_rating,
            "starter_minus_recent_qb_mix": difference,
        })

    result = pd.DataFrame(rows)

    if result.empty:
        raise ValueError("No 24-hour QB ratings to audit.")

    if result.duplicated(["game_id", "team"]).any():
        raise ValueError("Duplicate team-game audit rows.")

    print("\nQB change audit — 24 hours before:")
    print(f"Team-game rows: {len(result)}")
    print(result["status"].value_counts().to_string())

    usable = result.loc[result["status"].eq("complete")].copy()

    same_starter = usable[
        "starter_share_of_recent_sample"
    ].eq(1.0)

    print(
        "\nRows where the listed starter supplied the entire recent sample:",
        int(same_starter.sum()),
    )
    print("All such rows passed the zero-difference check.")

    print("\nRecent-history age and sample sizes:")
    print(usable[
        [
            "recent_attempts_plus_sacks",
            "days_since_latest_game",
            "days_since_oldest_game",
        ]
    ].agg(["min", "median", "max"]).to_string())

    largest = usable.loc[
        usable["starter_minus_recent_qb_mix"].abs()
        .sort_values(ascending=False).head(20).index
    ]

    print("\nLargest absolute starter-versus-QB-mix differences:")
    print(largest[
        [
            "game_id",
            "team",
            "listed_qb",
            "starter_adjusted_anya",
            "recent_qb_mix_rating",
            "starter_minus_recent_qb_mix",
            "starter_history_sample",
            "recent_attempts_plus_sacks",
            "starter_share_of_recent_sample",
            "days_since_latest_game",
        ]
    ].to_string(
        index=False,
        float_format=lambda value: f"{value:.3f}",
    ))

    problems = result.loc[result["status"].ne("complete")]
    if not problems.empty:
        print("\nIncomplete windows — first 15:")
        print(problems[
            ["game_id", "team", "status", "recent_games", "games_with_stats"]
        ].head(15).to_string(index=False))

    # Retrospective labels are joined only after feature calculation.
    actual_starters = pd.concat([
        completed[
            ["game_id", f"{side}_team", f"{side}_qb_id", f"{side}_qb_name"]
        ].rename(columns={
            f"{side}_team": "team",
            f"{side}_qb_id": "actual_qb_id",
            f"{side}_qb_name": "actual_qb_name",
        })
        for side in ["home", "away"]
    ], ignore_index=True)

    evaluation = usable.merge(
        actual_starters,
        on=["game_id", "team"],
        how="left",
        validate="one_to_one",
    )

    for column in ["listed_qb_id", "actual_qb_id"]:
        evaluation[column] = (
            evaluation[column]
            .astype("string")
            .str.strip()
            .replace("", pd.NA)
        )

    comparable = evaluation[
        ["listed_qb_id", "actual_qb_id"]
    ].notna().all(axis=1)

    print(
        "\nRows without comparable starter IDs:",
        int((~comparable).sum()),
    )

    evaluation["listed_qb_started"] = (
        evaluation["listed_qb_id"].eq(evaluation["actual_qb_id"])
    ).where(comparable, pd.NA).astype("boolean")

    share = evaluation["starter_share_of_recent_sample"]

    if share.isna().any() or not share.between(0, 1).all():
        raise ValueError("Invalid recent passing participation share.")

    evaluation["Participation"] = "Some"
    evaluation.loc[share.eq(0), "Participation"] = "None"
    evaluation.loc[share.eq(1), "Participation"] = "All"

    summaries = []

    for group in ["None", "Some", "All"]:
        group_rows = evaluation.loc[
            evaluation["Participation"].eq(group)
        ]
        matches = group_rows["listed_qb_started"].dropna()

        summaries.append({
            "Recent participation": group,
            "Cases": len(group_rows),
            "Compared": len(matches),
            "Matches": int(matches.sum()),
            "Agreement": (
                f"{matches.mean():.2%}"
                if len(matches) else "Unavailable"
            ),
        })

    print("\nStarter agreement by recent passing participation:")
    print(pd.DataFrame(summaries).to_string(index=False))

    evaluation["absolute_mix_difference"] = evaluation[
        "starter_minus_recent_qb_mix"
    ].abs()

    known = evaluation.loc[comparable].copy()
    known["Selection result"] = "Incorrect"
    known.loc[
        known["listed_qb_started"].eq(True), "Selection result"
    ] = "Correct"

    print("\nAbsolute feature magnitude by starter-selection result:")
    print(known.groupby("Selection result")[
        "absolute_mix_difference"
    ].agg(["count", "mean", "median", "max"]).round(3).to_string())

    largest_evaluated = evaluation.sort_values(
        "absolute_mix_difference", ascending=False
    ).head(20)

    print("\nLargest differences with recorded starters:")
    print(largest_evaluated[
        [
            "game_id",
            "team",
            "listed_qb",
            "actual_qb_name",
            "listed_qb_started",
            "starter_minus_recent_qb_mix",
            "starter_share_of_recent_sample",
            "days_since_latest_game",
        ]
    ].to_string(
        index=False,
        float_format=lambda value: f"{value:.3f}",
    ))

    print("\nAudit only: no models trained or files saved.")
    return result