from io import StringIO
from pathlib import Path
import subprocess

import numpy as np
import pandas as pd
import argparse


ROOT = Path(__file__).resolve().parents[1]
FORECAST_PATH = "data/predictions/upcoming_2026_predictions.csv"

# Known snapshots from the current carryover-model version.
SNAPSHOTS = ["0ae50d67", "281ce055", "f25d084e"]


def git(*arguments):
    return subprocess.check_output(
        ["git", *arguments],
        cwd=ROOT,
        text=True,
        encoding="utf-8",
    ).strip()


def main(save=False):
    schedule = pd.read_csv(
        ROOT / "data/processed/schedules_2026.csv"
    )
    schedule = schedule.loc[
        schedule["season"].eq(2026)
        & schedule["game_type"].isin(["REG", "WC", "DIV", "CON", "SB"])
    ].copy()

    if schedule["game_id"].duplicated().any():
        raise ValueError("Duplicate schedule game IDs.")

    local_kickoff = pd.to_datetime(
        schedule["gameday"].astype(str)
        + " "
        + schedule["gametime"].astype(str),
        errors="raise",
    )
    schedule["kickoff_utc"] = (
        local_kickoff.dt.tz_localize(
            "America/New_York",
            ambiguous="raise",
            nonexistent="raise",
        ).dt.tz_convert("UTC")
    )

    if schedule["kickoff_utc"].isna().any():
        raise ValueError("Missing kickoff timestamps.")

    schedule["completed"] = schedule[
        ["home_score", "away_score"]
    ].notna().all(axis=1)

    recovered = []

    for reference in SNAPSHOTS:
        commit = git("rev-parse", reference)
        saved_at = pd.Timestamp(
            git("show", "-s", "--format=%cI", commit)
        ).tz_convert("UTC")

        snapshot = pd.read_csv(StringIO(
            git("show", f"{commit}:{FORECAST_PATH}")
        ))

        if snapshot["game_id"].duplicated().any():
            raise ValueError(f"Duplicate forecast IDs in {reference}.")

        snapshot["snapshot_commit"] = commit
        snapshot["saved_at_utc"] = saved_at

        recovered.append(snapshot)

    history = pd.concat(recovered, ignore_index=True)

    # Match game ID, season, teams, and date. Schedule changes are not
    # silently accepted as equivalent historical matchups.
    keys = ["game_id", "season", "gameday", "home_team", "away_team"]
    candidates = history.merge(
        schedule[keys + ["kickoff_utc", "completed"]],
        on=keys,
        how="inner",
        validate="many_to_one",
    )

    eligible = candidates.loc[
        candidates["saved_at_utc"] < candidates["kickoff_utc"]
    ].copy()

    probabilities = eligible[
        ["home_win_probability", "away_win_probability"]
    ].to_numpy(dtype=float)

    if (
        not np.isfinite(probabilities).all()
        or not ((probabilities >= 0) & (probabilities <= 1)).all()
        or not np.allclose(probabilities.sum(axis=1), 1)
    ):
        raise ValueError("Invalid archived probabilities.")

    expected_winner = np.where(
        eligible["home_win_probability"] >= 0.5,
        eligible["home_team"],
        eligible["away_team"],
    )
    if not eligible["predicted_winner"].eq(expected_winner).all():
        raise ValueError("Archived picks disagree with their probabilities.")

    latest = (
        eligible.sort_values(["saved_at_utc", "snapshot_commit"])
        .drop_duplicates("game_id", keep="last")
    )

    completed = schedule.loc[schedule["completed"]]
    matched = latest.loc[latest["completed"]].copy()
    missing = completed.loc[
        ~completed["game_id"].isin(matched["game_id"])
    ]

    print("\nForecast recovery audit:")
    print(f"Completed games in saved schedule: {len(completed)}")
    print(f"Completed games with eligible forecasts: {len(matched)}")
    print(f"Completed games without eligible forecasts: {len(missing)}")

    print("\nRecovered completed games by snapshot:")
    print(matched.groupby(
        ["snapshot_commit", "saved_at_utc"]
    ).size().to_string())

    print("\nRecovered forecast preview:")
    print(matched[
        [
            "game_id",
            "saved_at_utc",
            "kickoff_utc",
            "predicted_winner",
            "home_win_probability",
        ]
    ].sort_values("kickoff_utc").head(20).to_string(index=False))

    if not missing.empty:
        print("\nGames needing further investigation:")
        print(missing[
            ["game_id", "gameday", "home_team", "away_team"]
        ].to_string(index=False))

    print(
        "\nTiming uses Git commit timestamps and the current saved schedule. "
        "Historical kickoff changes have not been independently verified."
    )
    if not save:
        print("Audit only: no predictions regenerated and no files changed.")
        return

    archive_dir = ROOT / "data/predictions/archive/2026"
    archive_dir.mkdir(parents=True, exist_ok=True)

    # Preserve every original forecast row, not just completed games.
    # Dashboard loading will apply the pre-kickoff eligibility checks.
    for commit, snapshot in history.groupby("snapshot_commit"):
        snapshot = snapshot.copy()
        snapshot["archive_source"] = "git_history"
        snapshot["timestamp_basis"] = "git_committer_time"

        destination = archive_dir / f"git_{commit}.csv"
        content = snapshot.to_csv(index=False, lineterminator="\n")

        if destination.exists():
            if destination.read_text(encoding="utf-8") != content:
                raise ValueError(
                    f"Existing archive differs; refusing to overwrite: "
                    f"{destination}"
                )
            print(f"Already archived: {destination.name}")
        else:
            with destination.open(
                "x", encoding="utf-8", newline=""
            ) as handle:
                handle.write(content)
            print(f"Saved {len(snapshot)} forecasts: {destination.name}")

    print(
        "\nOriginal forecast snapshots preserved. "
        "No models retrained and no existing predictions overwritten."
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--save",
        action="store_true",
        help="Preserve the original Git forecast snapshots.",
    )
    args = parser.parse_args()
    main(save=args.save)