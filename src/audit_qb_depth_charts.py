import pandas as pd
import nfl_data_py as nfl


def audit_season(season):
    print(f"\n{'=' * 60}")
    print(f"DEPTH-CHART AUDIT: {season}")
    print("=" * 60)

    try:
        data = nfl.import_depth_charts([season])
    except Exception as error:
        print(f"DOWNLOAD FAILED: {type(error).__name__}: {error}")
        return

    print(f"Total rows: {len(data):,}")
    print("Columns:", ", ".join(data.columns))

    if data.empty:
        print("No records available.")
        return

    if "pos_abb" in data.columns:
        # Timestamped format documented for 2025 onward.
        position_column = "pos_abb"
        team_column = "team"
        rank_column = "pos_rank"
        name_column = "player_name"
        snapshot_column = "dt"
    elif "depth_position" in data.columns:
        # Older weekly format.
        position_column = "depth_position"
        team_column = "club_code"
        rank_column = "depth_team"
        name_column = "full_name"
        snapshot_column = "week"
    else:
        print("Unrecognized position fields; inspect the column list.")
        return

    required = [
        team_column, rank_column, snapshot_column, "gsis_id"
    ]
    missing_columns = [
        column for column in required if column not in data.columns
    ]

    if missing_columns:
        print("Missing expected columns:", missing_columns)
        return

    qb = data.loc[
        data[position_column].astype(str).str.upper().str.strip() == "QB"
    ].copy()

    print(f"Quarterback rows: {len(qb):,}")

    if qb.empty:
        print("No QB records found.")
        return

    print(f"Teams represented: {qb[team_column].nunique()}")
    print("Team codes:", ", ".join(
        sorted(qb[team_column].dropna().astype(str).unique())
    ))

    ids = qb["gsis_id"].astype("string")
    missing_ids = ids.isna() | ids.str.strip().eq("")
    print(f"QB rows missing GSIS IDs: {int(missing_ids.sum()):,}")

    qb[rank_column] = pd.to_numeric(qb[rank_column], errors="coerce")

    if snapshot_column == "dt":
        qb["snapshot_time"] = pd.to_datetime(
            qb["dt"], utc=True, errors="coerce"
        )

        print(f"Invalid timestamps: {qb['snapshot_time'].isna().sum()}")
        print(f"Earliest QB snapshot: {qb['snapshot_time'].min()}")
        print(f"Latest QB snapshot:   {qb['snapshot_time'].max()}")
        print(f"Distinct timestamps: {qb['snapshot_time'].nunique():,}")

        snapshot_keys = ["snapshot_time", team_column]

        coverage = qb.groupby(team_column)["snapshot_time"].agg(
            first_snapshot="min",
            last_snapshot="max",
            snapshots="nunique",
        )

        print("\nSnapshot coverage by team:")
        print(coverage.to_string())

        qb = qb.sort_values("snapshot_time")
    else:
        snapshot_keys = [snapshot_column, team_column]

        if "game_type" in qb.columns:
            snapshot_keys.insert(0, "game_type")

        print("Weeks represented:", sorted(
            qb["week"].dropna().unique().tolist()
        ))
        print(
            "Weekly labels alone do not establish whether these records "
            "were available on Tuesday or immediately before kickoff."
        )

        qb = qb.sort_values("week")

    # Count rank-one rows within team/snapshot groups that contain QBs.
    qb["is_rank_one"] = qb[rank_column].eq(1)

    counts = (
        qb.groupby(snapshot_keys, dropna=False)["is_rank_one"]
        .sum()
    )

    print(f"\nTeam/snapshot groups containing QBs: {len(counts):,}")
    print(f"Groups with no rank-one QB: {(counts == 0).sum():,}")
    print(f"Groups with multiple rank-one QB rows: {(counts > 1).sum():,}")

    sample_columns = [
        snapshot_column, team_column, name_column, "gsis_id", rank_column
    ]
    sample_columns = [
        column for column in sample_columns if column in qb.columns
    ]

    print("\nLatest rank-one QB rows — sample:")
    print(
        qb.loc[qb["is_rank_one"], sample_columns]
        .tail(10)
        .to_string(index=False)
    )

    print(
        "\nRank one means listed first on the depth chart, "
        "not confirmed healthy or confirmed to start."
    )


def main():
    for season in [2024, 2025, 2026]:
        audit_season(season)

    print("\nAudit complete. No project data files were saved.")


if __name__ == "__main__":
    main()