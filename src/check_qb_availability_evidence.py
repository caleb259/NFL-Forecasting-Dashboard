import json
import tempfile
import unittest
from pathlib import Path

from qb_availability_evidence import load_evidence, summarize_evidence


CUTOFF = "2025-11-01T12:00:00Z"


def report(**changes):
    row = {
        "game_id": "TEST_GAME",
        "team": "SF",
        "availability_player": None,
        "availability_status": None,
        "reported_starter": None,
        "published_at": "2025-10-31T10:00:00Z",
        "modified_at": "2025-10-31T10:00:00Z",
        "archive_verified": False,
        "source_url": "https://example.com/test-report",
    }
    row.update(changes)
    return row


class EvidenceChecks(unittest.TestCase):
    def summarize(self, *reports):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "evidence.json"
            path.write_text(json.dumps(list(reports)), encoding="utf-8")
            records = load_evidence(path)

        return summarize_evidence(records, "TEST_GAME", "SF", CUTOFF)

    def test_questionable_does_not_select_starter(self):
        result = self.summarize(report(
            availability_player="QB A",
            availability_status="questionable",
        ))
        self.assertEqual(result["status"], "no_explicit_starting_plan")
        self.assertIsNone(result["reported_starter"])
        self.assertEqual(result["ruled_out"], [])

    def test_out_does_not_invent_replacement(self):
        result = self.summarize(report(
            availability_player="QB A",
            availability_status="out",
        ))
        self.assertIsNone(result["reported_starter"])
        self.assertEqual(result["ruled_out"], ["QB A"])

    def test_explicit_plan_is_preserved(self):
        result = self.summarize(report(
            availability_player="QB A",
            availability_status="questionable",
            reported_starter="QB B",
        ))
        self.assertEqual(result["status"], "reported_starting_plan")
        self.assertEqual(result["reported_starter"], "QB B")
        self.assertEqual(result["unverified_archive_reports"], 1)

    def test_publication_and_modification_boundaries(self):
        for field in ["published_at", "modified_at"]:
            for timestamp, expected_reports in [
                ("2025-11-01T11:59:59Z", 1),
                ("2025-11-01T12:00:00Z", 0),
                ("2025-11-01T12:00:01Z", 0),
            ]:
                with self.subTest(field=field, timestamp=timestamp):
                    result = self.summarize(report(
                        reported_starter="QB A",
                        **{field: timestamp},
                    ))
                    self.assertEqual(
                        result["eligible_reports"], expected_reports
                    )
                    if expected_reports == 0:
                        self.assertEqual(
                            result["status"], "no_eligible_evidence"
                        )
                        self.assertIsNone(result["reported_starter"])

    def test_conflicting_plans_remain_unresolved(self):
        result = self.summarize(
            report(reported_starter="QB A"),
            report(reported_starter="QB B"),
        )
        self.assertEqual(result["status"], "conflicting_evidence")
        self.assertIsNone(result["reported_starter"])

    def test_reported_starter_also_ruled_out_is_conflict(self):
        result = self.summarize(
            report(reported_starter="QB A"),
            report(
                availability_player="QB A",
                availability_status="out",
            ),
        )
        self.assertEqual(result["status"], "conflicting_evidence")
        self.assertIsNone(result["reported_starter"])

    def test_other_games_and_teams_are_ignored(self):
        result = self.summarize(
            report(reported_starter="QB A"),
            report(game_id="OTHER_GAME", reported_starter="QB B"),
            report(team="OTHER_TEAM", reported_starter="QB C"),
        )
        self.assertEqual(result["eligible_reports"], 1)
        self.assertEqual(result["reported_starter"], "QB A")

    def test_timezone_offset_obeys_same_boundary(self):
        # 08:00 at UTC-04:00 equals our 12:00 UTC cutoff.
        result = self.summarize(report(
            published_at="2025-11-01T08:00:00-04:00",
            modified_at="2025-11-01T08:00:00-04:00",
            reported_starter="QB A",
        ))
        self.assertEqual(result["eligible_reports"], 0)

    def test_metadata_anomaly_is_retained(self):
        result = self.summarize(report(
            published_at="2025-10-31T10:00:00Z",
            modified_at="2025-10-31T09:59:40Z",
            reported_starter="QB A",
        ))
        self.assertEqual(result["metadata_order_anomalies"], 1)
        self.assertEqual(result["reported_starter"], "QB A")


if __name__ == "__main__":
    unittest.main(verbosity=2)