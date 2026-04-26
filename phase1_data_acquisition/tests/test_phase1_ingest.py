import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import pandas as pd

sys.path.append(str(Path(__file__).resolve().parent.parent / "src"))
import ingest  # noqa: E402


class TestPhase1Ingestion(unittest.TestCase):
    def test_ingest_raw_snapshot_writes_parquet_and_metadata(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            raw_dir = root / "raw"
            metadata_dir = root / "metadata"
            sample_df = pd.DataFrame(
                [
                    {"name": "A", "location": "X", "rate": "4.0/5"},
                    {"name": "B", "location": "Y", "rate": "3.5/5"},
                ]
            )

            with (
                patch.object(ingest, "RAW_DIR", raw_dir),
                patch.object(ingest, "METADATA_DIR", metadata_dir),
                patch.object(ingest, "_dataset_to_dataframe", return_value=sample_df),
                patch.object(ingest, "_build_run_id", return_value="20260101T000000Z"),
            ):
                metadata = ingest.ingest_raw_snapshot(split="train")

            self.assertEqual(metadata["row_count"], 2)
            self.assertEqual(metadata["column_count"], 3)
            self.assertEqual(metadata["split"], "train")

            raw_path = raw_dir / "zomato_raw_20260101T000000Z.parquet"
            self.assertTrue(raw_path.exists())

            latest_metadata = metadata_dir / "latest_ingestion.json"
            self.assertTrue(latest_metadata.exists())
            latest = json.loads(latest_metadata.read_text(encoding="utf-8"))
            self.assertEqual(latest["run_id"], "20260101T000000Z")


if __name__ == "__main__":
    unittest.main()
