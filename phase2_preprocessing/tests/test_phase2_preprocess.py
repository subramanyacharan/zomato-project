import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import pandas as pd

sys.path.append(str(Path(__file__).resolve().parent.parent / "src"))
import preprocess  # noqa: E402


class TestPhase2Preprocessing(unittest.TestCase):
    def test_helpers_normalize_values(self) -> None:
        self.assertEqual(preprocess._normalize_location("bengaluru"), "Bangalore")
        self.assertEqual(
            preprocess._normalize_cuisines("italian / chinese"),
            "Chinese, Italian",
        )
        self.assertEqual(preprocess._parse_cost("500-700"), 600.0)
        self.assertEqual(preprocess._parse_rating("4.3/5"), 4.3)
        self.assertIsNone(preprocess._parse_rating("NEW"))

    def test_preprocess_phase2_generates_structured_output(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            raw_path = root / "raw.parquet"
            structured_dir = root / "structured"
            metadata_dir = root / "metadata"

            pd.DataFrame(
                [
                    {
                        "name": "R1",
                        "location": "bengaluru",
                        "cuisines": "italian, chinese",
                        "approx_cost(for two people)": "600",
                        "rate": "4.1/5",
                        "rest_type": "Casual Dining",
                        "listed_in(type)": "Delivery",
                        "listed_in(city)": "Bangalore",
                    },
                    {
                        "name": None,
                        "location": "bangalore",
                        "cuisines": "north indian",
                        "approx_cost(for two people)": "700",
                        "rate": "4.0/5",
                        "rest_type": "Cafe",
                        "listed_in(type)": "Dine-out",
                        "listed_in(city)": "Bangalore",
                    },
                ]
            ).to_parquet(raw_path, index=False)

            with (
                patch.object(preprocess, "STRUCTURED_DIR", structured_dir),
                patch.object(preprocess, "METADATA_DIR", metadata_dir),
                patch.object(preprocess, "_load_phase1_raw_path", return_value=raw_path),
                patch.object(preprocess, "_build_run_id", return_value="20260101T010000Z"),
            ):
                result = preprocess.preprocess_phase2()

            self.assertEqual(result["input_row_count"], 2)
            self.assertEqual(result["output_row_count"], 1)

            out_path = structured_dir / "zomato_structured_20260101T010000Z.parquet"
            self.assertTrue(out_path.exists())

            latest = metadata_dir / "latest_preprocessing.json"
            self.assertTrue(latest.exists())
            latest_obj = json.loads(latest.read_text(encoding="utf-8"))
            self.assertEqual(latest_obj["run_id"], "20260101T010000Z")


if __name__ == "__main__":
    unittest.main()
