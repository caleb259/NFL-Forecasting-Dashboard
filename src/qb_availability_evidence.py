import json
from datetime import datetime, timezone
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
EVIDENCE_PATH = (
    PROJECT_ROOT / "data/research/qb_availability_pilot.json"
)


def parse_timestamp(value):
    timestamp = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if timestamp.tzinfo is None:
        raise ValueError("Evidence timestamps must include a timezone.")
    return timestamp.astimezone(timezone.utc)


def load_evidence(path=EVIDENCE_PATH):
    with open(path, encoding="utf-8") as handle:
        records = json.load(handle)

    required = {
        "game_id", "team", "availability_player", "availability_status",
        "reported_starter", "published_at", "modified_at",
        "archive_verified", "source_url",
    }

    if not isinstance(records, list) or not records:
        raise ValueError("Expected a nonempty list of evidence records.")

    for record in records:
        if not isinstance(record, dict) or required - record.keys():
            raise ValueError("Evidence record is missing required fields.")

        for field in ["game_id", "team", "source_url"]:
            if not isinstance(record[field], str) or not record[field].strip():
                raise ValueError(f"Invalid {field}.")

        if record["availability_status"] not in {
            None, "out", "doubtful", "questionable", "available"
        }:
            raise ValueError("Unrecognized availability status.")

        if record["availability_status"] is not None:
            if not record["availability_player"]:
                raise ValueError("Availability status needs a named player.")

        if not isinstance(record["archive_verified"], bool):
            raise ValueError("archive_verified must be true or false.")

        published = parse_timestamp(record["published_at"])
        modified = parse_timestamp(record["modified_at"])

        # Use the later timestamp for the current version of the report.
        # This is a publisher-metadata assumption, not archive proof.
        record["eligible_after"] = max(published, modified)
        record["metadata_order_anomaly"] = modified < published

    return records


def summarize_evidence(records, game_id, team, cutoff):
    cutoff = parse_timestamp(cutoff)

    eligible = [
        record for record in records
        if record["game_id"] == game_id
        and record["team"] == team
        and record["eligible_after"] < cutoff
    ]

    # Do not silently resolve conflicting reports in this pilot.
    reported = {
        record["reported_starter"]
        for record in eligible
        if record["reported_starter"] is not None
    }
    ruled_out = {
        record["availability_player"]
        for record in eligible
        if record["availability_status"] == "out"
    }

    candidate = next(iter(reported)) if len(reported) == 1 else None

    if not eligible:
        status = "no_eligible_evidence"
    elif len(reported) > 1 or reported.intersection(ruled_out):
        status = "conflicting_evidence"
        candidate = None
    elif candidate is not None:
        status = "reported_starting_plan"
    else:
        status = "no_explicit_starting_plan"

    return {
        "status": status,
        "reported_starter": candidate,
        "ruled_out": sorted(ruled_out),
        "eligible_reports": len(eligible),
        "unverified_archive_reports": sum(
            not record["archive_verified"] for record in eligible
        ),
        "metadata_order_anomalies": sum(
            record["metadata_order_anomaly"] for record in eligible
        ),
        "sources": [record["source_url"] for record in eligible],
    }


def main():
    records = load_evidence()

    # Identical Saturday review time for this source-loader demonstration.
    # These are not the games' exact 24-hour forecast cutoffs.
    examples = [
        ("2025_08_SF_HOU", "2025-10-25T12:00:00Z"),
        ("2025_09_SF_NYG", "2025-11-01T12:00:00Z"),
        ("2025_10_LA_SF", "2025-11-08T12:00:00Z"),
        ("2025_11_SF_ARI", "2025-11-15T12:00:00Z"),
    ]

    for game_id, cutoff in examples:
        result = summarize_evidence(records, game_id, "SF", cutoff)
        print(f"\n{game_id} — review cutoff {cutoff}")
        print(json.dumps(result, indent=2))

    print("\nExploratory evidence only. No forecasts or files changed.")


if __name__ == "__main__":
    main()