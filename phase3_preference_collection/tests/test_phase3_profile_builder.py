import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import pandas as pd

sys.path.append(str(Path(__file__).resolve().parent.parent / "src"))
import profile_builder  # noqa: E402


class TestPhase3ProfileBuilder(unittest.TestCase):
    def test_build_profile_valid_payload(self) -> None:
        reference_df = pd.DataFrame(
            [
                {"location": "Bangalore", "cuisines": "Italian, Chinese"},
                {"location": "Delhi", "cuisines": "North Indian"},
            ]
        )

        payload = {
            "location": "bangalore",
            "budget": "mid",
            "cuisine": "italian",
            "minimum_rating": 4,
            "additional_preferences": ["quick service", " family-friendly "],
        }

        with patch.object(
            profile_builder, "_load_phase2_reference", return_value=reference_df
        ):
            result = profile_builder.build_profile(payload)

        self.assertEqual(result.normalized_profile["location"], "Bangalore")
        self.assertEqual(result.normalized_profile["budget"], "medium")
        self.assertEqual(result.normalized_profile["cuisine"], "Italian")
        self.assertEqual(result.errors, [])

    def test_build_profile_invalid_budget_and_rating(self) -> None:
        reference_df = pd.DataFrame([{"location": "Delhi", "cuisines": "North Indian"}])
        payload = {
            "location": "Delhi",
            "budget": "super-high",
            "cuisine": "North Indian",
            "minimum_rating": 7,
            "additional_preferences": "not-a-list",
        }

        with patch.object(
            profile_builder, "_load_phase2_reference", return_value=reference_df
        ):
            result = profile_builder.build_profile(payload)

        self.assertGreaterEqual(len(result.errors), 3)

    def test_save_profile_writes_outputs(self) -> None:
        validation_result = profile_builder.ValidationResult(
            normalized_profile={"location": "Delhi", "budget": "low", "cuisine": "Italian"},
            warnings=["test warning"],
            errors=[],
        )
        with tempfile.TemporaryDirectory() as tmp:
            profiles_dir = Path(tmp) / "profiles"
            with patch.object(profile_builder, "PROFILES_DIR", profiles_dir):
                result = profile_builder.save_profile(validation_result)

            self.assertTrue(Path(result["output_path"]).exists())
            self.assertTrue(Path(result["latest_path"]).exists())
            latest = json.loads(Path(result["latest_path"]).read_text(encoding="utf-8"))
            self.assertTrue(latest["is_valid"])


if __name__ == "__main__":
    unittest.main()
