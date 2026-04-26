import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import pandas as pd

sys.path.append(str(Path(__file__).resolve().parent.parent / "src"))
import filter_engine  # noqa: E402


class TestPhase4FilterEngine(unittest.TestCase):
    def test_filter_with_strict_match(self) -> None:
        df = pd.DataFrame(
            [
                {
                    "name": "R1",
                    "location": "Delhi",
                    "cuisines": "Italian, Chinese",
                    "cost_for_two": 1200.0,
                    "rating": 4.4,
                    "tags": "Casual Dining",
                },
                {
                    "name": "R2",
                    "location": "Delhi",
                    "cuisines": "North Indian",
                    "cost_for_two": 500.0,
                    "rating": 4.0,
                    "tags": "Cafe",
                },
            ]
        )
        profile = {"location": "Delhi", "cuisine": "Italian", "budget": "medium", "minimum_rating": 4.2}

        filtered, reasons = filter_engine._filter_with_relaxation(df, profile)
        self.assertEqual(len(filtered), 1)
        self.assertEqual(reasons, [])

    def test_filter_with_relaxation_fallback(self) -> None:
        df = pd.DataFrame(
            [
                {
                    "name": "R1",
                    "location": "Delhi",
                    "cuisines": "North Indian",
                    "cost_for_two": 400.0,
                    "rating": 3.8,
                    "tags": "Casual Dining",
                }
            ]
        )
        profile = {"location": "Delhi", "cuisine": "Italian", "budget": "high", "minimum_rating": 4.5}

        filtered, reasons = filter_engine._filter_with_relaxation(df, profile)
        self.assertEqual(len(filtered), 1)
        self.assertTrue(any("relaxed" in msg.lower() for msg in reasons))

    def test_run_candidate_filtering_writes_artifacts(self) -> None:
        df = pd.DataFrame(
            [
                {
                    "name": "R1",
                    "location": "Delhi",
                    "cuisines": "Italian",
                    "cost_for_two": 1000.0,
                    "rating": 4.5,
                    "tags": "Fine Dining",
                }
            ]
        )
        profile = {
            "location": "Delhi",
            "cuisine": "Italian",
            "budget": "medium",
            "minimum_rating": 4.0,
            "additional_preferences": [],
            "source": "phase3",
        }

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            candidates_dir = root / "candidates"
            metadata_dir = root / "metadata"
            with (
                patch.object(filter_engine, "CANDIDATES_DIR", candidates_dir),
                patch.object(filter_engine, "METADATA_DIR", metadata_dir),
                patch.object(filter_engine, "_load_phase2_df", return_value=df),
                patch.object(filter_engine, "_load_phase3_profile", return_value=profile),
                patch.object(filter_engine, "_run_id", return_value="20260101T030000Z"),
            ):
                result = filter_engine.run_candidate_filtering(top_n=5)

            self.assertEqual(result["shortlisted_row_count"], 1)
            out_file = candidates_dir / "shortlisted_candidates_20260101T030000Z.parquet"
            self.assertTrue(out_file.exists())
            latest = metadata_dir / "latest_filtering.json"
            self.assertTrue(latest.exists())
            payload = json.loads(latest.read_text(encoding="utf-8"))
            self.assertEqual(payload["run_id"], "20260101T030000Z")


if __name__ == "__main__":
    unittest.main()
