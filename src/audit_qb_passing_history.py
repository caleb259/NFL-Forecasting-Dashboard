import pandas as pd
from audit_qb_change import audit_qb_change
from audit_qb_starter_signals import audit_qb_starter_signals


def calculate_qb_rating(passing, player_id, cutoff, prior_weight=100):
    """Rate a QB using games before the cutoff's Eastern calendar date."""
    if prior_weight <= 0:
        raise ValueError("prior_weight must be positive.")

    cutoff = pd.Timestamp(cutoff)

    if cutoff.tzinfo is None:
        raise ValueError("The forecast cutoff must include a timezone.")

    cutoff_date = cutoff.tz_convert("America/New_York").date()

    # Apply the same time restriction to player and league history.
    league_prior = passing.loc[
        passing["game_date"] < cutoff_date
    ].copy()

    # This source stores sack yards as signed negative yardage.
    league_prior["anya_numerator"] = (
        league_prior["passing_yards"]
        + 20 * league_prior["passing_tds"]
        - 45 * league_prior["passing_interceptions"]
        + league_prior["sack_yards_lost"]
    )
    league_prior["anya_denominator"] = (
        league_prior["attempts"] + league_prior["sacks_suffered"]
    )

    league_denominator = league_prior["anya_denominator"].sum()

    if league_denominator <= 0:
        raise ValueError("No earlier league history for this cutoff.")

    league_anya = (
        league_prior["anya_numerator"].sum() / league_denominator
    )

    prior = league_prior.loc[
        league_prior["player_id"].eq(player_id)
    ]

    player_denominator = prior["anya_denominator"].sum()
    player_numerator = prior["anya_numerator"].sum()

    raw_anya = (
        player_numerator / player_denominator
        if player_denominator > 0
        else float("nan")
    )

    adjusted_anya = (
        player_numerator + prior_weight * league_anya
    ) / (player_denominator + prior_weight)

    return {
        "prior_passing_games": len(prior),
        "prior_attempts": int(prior["attempts"].sum()),
        "prior_attempts_plus_sacks": player_denominator,
        "raw_anya": raw_anya,
        "league_anya": league_anya,
        "adjusted_anya": adjusted_anya,
        "anya_above_league": adjusted_anya - league_anya,
    }

def audit_passing_history(qb_selections, schedules):
    print("\nLoading 2023–2025 player statistics...")

    season_tables = []

    for season in [2023, 2024, 2025]:
        url = (
            "https://github.com/nflverse/nflverse-data/releases/download/"
            f"stats_player/stats_player_week_{season}.parquet"
        )

        print(f"Downloading player statistics for {season}...")
        season_data = pd.read_parquet(url)

        if season_data.empty:
            raise ValueError(f"No player statistics returned for {season}.")

        if not season_data["season"].eq(season).all():
            raise ValueError(f"Unexpected season values in the {season} file.")

        season_tables.append(season_data)

    stats = pd.concat(season_tables, ignore_index=True)

    print("Available columns:", ", ".join(stats.columns))

    # Older and newer files may use different team-column names.
    if "recent_team" in stats.columns:
        team_column = "recent_team"
    elif "team" in stats.columns:
        team_column = "team"
    else:
        raise ValueError("No recognized player-statistics team column.")

    required = [
        "player_id", "season", "week", "position",
        "attempts", "passing_yards", "passing_tds",
        "passing_interceptions", "sacks_suffered", "sack_yards_lost",
    ]
    missing = [column for column in required if column not in stats.columns]

    if missing:
        raise ValueError(f"Missing required fields: {missing}")

    print("\nPlayer-statistics rows by season:")
    print(stats.groupby("season").size().to_string())

    numeric_columns = [
        "attempts", "passing_yards", "passing_tds",
        "passing_interceptions", "sacks_suffered", "sack_yards_lost",
    ]

    for column in numeric_columns:
        stats[column] = pd.to_numeric(stats[column], errors="raise")

    passing = stats.loc[
        stats["position"].astype(str).str.upper().str.strip().eq("QB")
        & (
            stats["attempts"].gt(0)
            | stats["sacks_suffered"].gt(0)
        )
    ].copy()

    if passing[numeric_columns].isna().any().any():
        raise ValueError("Missing statistics in quarterback passing rows.")

    if passing[numeric_columns].isin(
        [float("inf"), float("-inf")]
    ).any().any():
        raise ValueError("Non-finite quarterback statistics found.")

    if (
        passing[["attempts", "sacks_suffered"]] < 0
    ).any().any():
        raise ValueError("Negative attempt or sack counts found.")

    passing = passing.rename(columns={team_column: "passing_team"})

    # Map season/week/team to a completed game's date.
    completed = schedules.loc[
        schedules["game_type"].isin(["REG", "WC", "DIV", "CON", "SB"])
    ].dropna(subset=["home_score", "away_score"]).copy()

    schedule_rows = []

    for side in ["home", "away"]:
        rows = completed[
            ["season", "week", "gameday", f"{side}_team"]
        ].rename(columns={f"{side}_team": "passing_team"})
        schedule_rows.append(rows)

    game_dates = pd.concat(schedule_rows, ignore_index=True)
    keys = ["season", "week", "passing_team"]

    if game_dates.duplicated(keys).any():
        raise ValueError("More than one scheduled game per season/week/team.")

    passing = passing.merge(
        game_dates,
        on=keys,
        how="left",
        validate="many_to_one",
        indicator=True,
    )

    unmatched = passing["_merge"].ne("both")
    print(f"\nPassing rows without a matching game: {int(unmatched.sum())}")

    if unmatched.any():
        print(passing.loc[
            unmatched, keys + ["player_id"]
        ].head(15).to_string(index=False))
        raise ValueError("Resolve unmatched games before counting history.")

    if passing.duplicated(keys + ["player_id"]).any():
        raise ValueError("Duplicate player/game passing rows found.")

    passing["game_date"] = pd.to_datetime(passing["gameday"]).dt.date

    results = []

    for _, selection in qb_selections.iterrows():
        player_id = selection["listed_qb_id"]

        if selection["status"] != "identified" or pd.isna(player_id):
            continue

        rating = calculate_qb_rating(
            passing,
            player_id,
            selection["cutoff"],
            prior_weight=100,
        )

        attempts = rating["prior_attempts"]

        if attempts == 0:
            band = "0 attempts"
        elif attempts < 100:
            band = "1–99 attempts"
        elif attempts < 300:
            band = "100–299 attempts"
        else:
            band = "300+ attempts"

        results.append({
            "game_id": selection["game_id"],
            "team": selection["team"],
            "horizon": selection["horizon"],
            "listed_qb": selection["listed_qb"],
            "player_id": player_id,
            "history_band": band,
            "cutoff": selection["cutoff"],
            **rating,
        })

    result = pd.DataFrame(results)

    if result.empty:
        raise ValueError("No identified quarterback selections to audit.")

    # Show each selected quarterback's earliest appearance in this audit.
    examples = (
        result.loc[result["horizon"] == "24 hours before"]
        .sort_values(["cutoff", "game_id"])
        .drop_duplicates("player_id")
        .sort_values("prior_attempts_plus_sacks")
    )

    print("\nProvisional ratings — earliest audited selection per QB:")
    print(examples[
        [
            "listed_qb",
            "cutoff",
            "prior_attempts_plus_sacks",
            "raw_anya",
            "league_anya",
            "adjusted_anya",
            "anya_above_league",
        ]
    ].to_string(index=False, float_format=lambda value: f"{value:.3f}"))

    print("\nPrior passing attempts by forecast cutoff:")
    print(pd.crosstab(
        result["horizon"], result["history_band"]
    ).reindex(
        columns=[
            "0 attempts", "1–99 attempts",
            "100–299 attempts", "300+ attempts",
        ],
        fill_value=0,
    ).to_string())

    print("\nSelections with fewer than 100 prior attempts — first 20:")
    limited = result.loc[result["prior_attempts"] < 100]
    print(limited[
        [
            "game_id", "team", "horizon", "listed_qb",
            "prior_passing_games", "prior_attempts",
        ]
    ].head(20).to_string(index=False))

    print(
        "\nDistinct selected quarterbacks:",
        result["player_id"].nunique(),
    )

    print(
        "History uses 2023–2025 only. Zero history does not establish "
        "rookie status or prove a player-ID match is correct."
    )
    print("No ratings, model inputs, or forecast files were saved.")

    audit_qb_change(
        passing,
        schedules,
        result,
        rating_function=calculate_qb_rating,
    )

    audit_qb_starter_signals(passing, schedules, qb_selections)

    return result