import pandas as pd

from qb_availability_evidence import load_evidence, summarize_evidence


def audit_qb_evidence_pilot(audit):
    records = load_evidence()

    pilot_keys = pd.DataFrame(
        sorted({
            (record["game_id"], record["team"])
            for record in records
        }),
        columns=["game_id", "team"],
    )

    targets = pilot_keys.merge(
        audit.loc[audit["horizon"].eq("24 hours before")],
        on=["game_id", "team"],
        how="left",
        validate="one_to_one",
        indicator=True,
    )

    if targets["_merge"].ne("both").any():
        raise ValueError("A pilot game/team is missing from the cutoff audit.")

    if targets["cutoff"].isna().any():
        raise ValueError("A pilot forecast cutoff is missing.")

    rows = []

    for target in targets.itertuples(index=False):
        evidence = summarize_evidence(
            records,
            target.game_id,
            target.team,
            target.cutoff.isoformat(),
        )

        # This pilot reports explicit evidence without selecting a
        # replacement from the depth chart or the actual starter.
        reported = evidence["reported_starter"]
        ruled_out = evidence["ruled_out"]

        if evidence["status"] == "conflicting_evidence":
            interpretation = "Unresolved: conflicting evidence"
        elif reported is not None:
            interpretation = "Explicit reported starting plan"
        elif ruled_out:
            interpretation = "Exclusion only; replacement unresolved"
        else:
            interpretation = "No explicit starting plan"

        rows.append({
            "game_id": target.game_id,
            "team": target.team,
            "cutoff_utc": target.cutoff.isoformat(),
            "depth_chart_qb": target.listed_qb,
            "reported_starter": reported,
            "ruled_out": ", ".join(ruled_out),
            "interpretation": interpretation,
            "eligible_reports": evidence["eligible_reports"],
            "archive_unverified": evidence["unverified_archive_reports"],
            "metadata_anomalies": evidence["metadata_order_anomalies"],
        })

    result = pd.DataFrame(rows)

    # Join actual starters only after evidence interpretation.
    result = result.merge(
        targets[["game_id", "team", "recorded_qb_name"]],
        on=["game_id", "team"],
        validate="one_to_one",
    )

    print("\nQB evidence pilot — actual 24-hour cutoffs:")
    print(result[
        [
            "game_id",
            "cutoff_utc",
            "depth_chart_qb",
            "reported_starter",
            "ruled_out",
            "recorded_qb_name",
        ]
    ].to_string(index=False))

    print("\nEvidence interpretation and limitations:")
    print(result[
        [
            "game_id",
            "interpretation",
            "eligible_reports",
            "archive_unverified",
            "metadata_anomalies",
        ]
    ].to_string(index=False))

    print(
        "\nRecorded starters are evaluation labels only. "
        "Names are displayed for manual review; no automatic ID matching "
        "or accuracy calculation is performed."
    )
    print(
        "This selected four-game pilot does not establish general accuracy. "
        "No forecasts or files were changed."
    )

    return result