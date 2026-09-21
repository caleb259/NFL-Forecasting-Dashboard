from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]


def attach_archived_forecasts(games, season):
    games = games.copy()

    local_kickoff = pd.to_datetime(
        games["gameday"].dt.strftime("%Y-%m-%d")
        + " "
        + games["gametime"].astype(str),
        errors="raise",
    )
    games["kickoff_utc"] = (
        local_kickoff.dt.tz_localize(
            "America/New_York",
            ambiguous="raise",
            nonexistent="raise",
        ).dt.tz_convert("UTC")
    )

    if games["kickoff_utc"].isna().any():
        raise ValueError("Missing kickoff timestamps.")

    files = sorted(
        (ROOT / f"data/predictions/archive/{season}").glob("*.csv")
    )

    games["archive_saved_at_utc"] = pd.NaT
    games["archive_source"] = None

    if files:
        history = pd.concat(
            [pd.read_csv(path) for path in files],
            ignore_index=True,
        )
        history["saved_at_utc"] = pd.to_datetime(
            history["saved_at_utc"], utc=True, errors="raise"
        )

        if history["saved_at_utc"].isna().any():
            raise ValueError("Archive contains missing save timestamps.")

        history["gameday"] = pd.to_datetime(
            history["gameday"]
        ).dt.normalize()

        keys = ["game_id", "season", "gameday", "home_team", "away_team"]
        eligible = history.merge(
            games[keys + ["kickoff_utc"]],
            on=keys,
            how="inner",
            validate="many_to_one",
        )
        eligible = eligible.loc[
            eligible["saved_at_utc"] < eligible["kickoff_utc"]
        ].copy()

        # New snapshots preserve their original scheduled kickoff.
        # Git-recovered snapshots only have the current schedule check.
        if "kickoff_at_save_utc" in eligible.columns:
            original_kickoff = pd.to_datetime(
                eligible["kickoff_at_save_utc"],
                utc=True,
                errors="raise",
            )
            is_new_snapshot = eligible["archive_source"].eq("forecast_run")

            if original_kickoff.loc[is_new_snapshot].isna().any():
                raise ValueError("A forecast-run archive lacks its kickoff.")

            eligible = eligible.loc[
                ~is_new_snapshot
                | (eligible["saved_at_utc"] < original_kickoff)
            ].copy()        

        probability = pd.to_numeric(
            eligible["home_win_probability"], errors="raise"
        )
        if (
            not np.isfinite(probability.to_numpy()).all()
            or not probability.between(0, 1).all()
        ):
            raise ValueError("Invalid archived home-win probability.")

        eligible["home_win_probability"] = probability
        expected_pick = np.where(
            probability >= 0.5,
            eligible["home_team"],
            eligible["away_team"],
        )
        if not eligible["predicted_winner"].eq(expected_pick).all():
            raise ValueError("Archived picks disagree with probabilities.")

        # Do not silently choose between conflicting simultaneous snapshots.
        conflicts = eligible.groupby(
            ["game_id", "saved_at_utc"]
        )["home_win_probability"].nunique()

        if conflicts.gt(1).any():
            raise ValueError("Conflicting archives have identical timestamps.")

        latest = (
            eligible.sort_values("saved_at_utc")
            .drop_duplicates("game_id", keep="last")
        )

        latest = latest[
            [
                "game_id", "predicted_winner", "home_win_probability",
                "saved_at_utc", "archive_source",
            ]
        ].rename(columns={
            "predicted_winner": "archived_pick",
            "home_win_probability": "archived_probability",
            "saved_at_utc": "archive_saved_at_utc",
        })

        games = games.drop(
            columns=["archive_saved_at_utc", "archive_source"]
        ).merge(
            latest,
            on="game_id",
            how="left",
            validate="one_to_one",
        )

        # Completed games use archived predictions exclusively.
        mask = games["completed"]
        games.loc[mask, "predicted_winner"] = games.loc[
            mask, "archived_pick"
        ]
        games.loc[mask, "home_win_probability"] = games.loc[
            mask, "archived_probability"
        ]

    games["has_archived_forecast"] = games[
        "archive_saved_at_utc"
    ].notna()

    games["actual_winner"] = None
    finished = games["completed"]
    games.loc[finished, "actual_winner"] = np.where(
        games.loc[finished, "home_score"]
        > games.loc[finished, "away_score"],
        games.loc[finished, "home_team"],
        games.loc[finished, "away_team"],
    )

    tied = finished & games["home_score"].eq(games["away_score"])
    games.loc[tied, "actual_winner"] = "Tie"

    games["pick_result"] = "Awaiting result"
    games.loc[finished, "pick_result"] = "No archived forecast"

    evaluated = finished & games["has_archived_forecast"] & ~tied
    games.loc[evaluated, "pick_result"] = np.where(
        games.loc[evaluated, "predicted_winner"].eq(
            games.loc[evaluated, "actual_winner"]
        ),
        "Correct",
        "Incorrect",
    )
    games.loc[tied, "pick_result"] = "Tie — excluded"

    return games

def save_forecast_snapshot(predictions, schedule, season):
    from datetime import datetime, timezone
    import subprocess
    from uuid import uuid4

    if predictions.empty:
        return None

    keys = ["game_id", "season", "home_team", "away_team"]
    timing = schedule[keys + ["gameday", "gametime"]].copy()

    local_kickoff = pd.to_datetime(
        timing["gameday"].astype(str)
        + " "
        + timing["gametime"].astype(str),
        errors="raise",
    )
    timing["kickoff_at_save_utc"] = (
        local_kickoff.dt.tz_localize(
            "America/New_York",
            ambiguous="raise",
            nonexistent="raise",
        ).dt.tz_convert("UTC")
    )

    snapshot = predictions.merge(
        timing[keys + ["kickoff_at_save_utc"]],
        on=keys,
        how="left",
        validate="one_to_one",
    )

    if snapshot["kickoff_at_save_utc"].isna().any():
        raise ValueError("Cannot archive forecasts without kickoff times.")

    if not snapshot["season"].eq(season).all():
        raise ValueError("Unexpected season in forecast snapshot.")

    probabilities = snapshot[
        ["home_win_probability", "away_win_probability"]
    ].to_numpy(dtype=float)

    if (
        not np.isfinite(probabilities).all()
        or not ((probabilities >= 0) & (probabilities <= 1)).all()
        or not np.allclose(probabilities.sum(axis=1), 1)
    ):
        raise ValueError("Invalid forecast probabilities; archive not saved.")

    expected_pick = np.where(
        snapshot["home_win_probability"] >= 0.5,
        snapshot["home_team"],
        snapshot["away_team"],
    )
    if not snapshot["predicted_winner"].eq(expected_pick).all():
        raise ValueError("Forecast picks disagree with their probabilities.")

    try:
        model_revision = subprocess.check_output(
            ["git", "rev-parse", "HEAD"],
            cwd=ROOT,
            text=True,
            encoding="utf-8",
            stderr=subprocess.DEVNULL,
        ).strip()
        working_tree_changed = bool(subprocess.check_output(
            ["git", "status", "--porcelain", "--", "src"],
            cwd=ROOT,
            text=True,
            encoding="utf-8",
            stderr=subprocess.DEVNULL,
        ).strip())
    except (OSError, subprocess.CalledProcessError):
        model_revision = "unavailable"
        working_tree_changed = "unknown"

    saved_at = datetime.now(timezone.utc)

    # A game may have started while the forecast job was running.
    snapshot = snapshot.loc[
        snapshot["kickoff_at_save_utc"] > saved_at
    ].copy()

    if snapshot.empty:
        print("No pre-kickoff forecasts available to archive.")
        return None

    snapshot["saved_at_utc"] = saved_at.isoformat()
    snapshot["archive_source"] = "forecast_run"
    snapshot["timestamp_basis"] = "utc_clock_at_save"
    snapshot["model_git_revision"] = model_revision
    snapshot["model_working_tree_changed"] = working_tree_changed

    archive_dir = ROOT / f"data/predictions/archive/{season}"
    archive_dir.mkdir(parents=True, exist_ok=True)

    filename = (
        f"run_{saved_at.strftime('%Y%m%dT%H%M%S%fZ')}_"
        f"{uuid4().hex[:8]}.csv"
    )
    destination = archive_dir / filename

    # Exclusive creation prevents overwriting an existing archive.
    with destination.open("x", encoding="utf-8", newline="") as handle:
        snapshot.to_csv(handle, index=False)

    print(f"Archived {len(snapshot)} pregame forecasts: {destination.name}")
    return destination