import json
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
from datasets import load_dataset

from config import DATASET_ID, DEFAULT_SPLIT, METADATA_DIR, RAW_DIR


def _ensure_dirs() -> None:
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    METADATA_DIR.mkdir(parents=True, exist_ok=True)


def _build_run_id() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def _dataset_to_dataframe(split: str) -> pd.DataFrame:
    dataset = load_dataset(DATASET_ID, split=split)
    return dataset.to_pandas()


def ingest_raw_snapshot(split: str = DEFAULT_SPLIT) -> dict:
    """
    Downloads the source dataset and stores a raw, versioned snapshot.
    Returns ingestion metadata as a dictionary.
    """
    _ensure_dirs()
    run_id = _build_run_id()

    df = _dataset_to_dataframe(split)
    row_count, column_count = df.shape

    raw_output_path = RAW_DIR / f"zomato_raw_{run_id}.parquet"
    df.to_parquet(raw_output_path, index=False)

    metadata = {
        "run_id": run_id,
        "dataset_id": DATASET_ID,
        "split": split,
        "raw_output_path": str(raw_output_path),
        "row_count": int(row_count),
        "column_count": int(column_count),
        "columns": [str(c) for c in df.columns],
        "ingested_at_utc": datetime.now(timezone.utc).isoformat(),
    }

    metadata_output_path = METADATA_DIR / f"ingestion_{run_id}.json"
    metadata_output_path.write_text(json.dumps(metadata, indent=2), encoding="utf-8")

    latest_path = METADATA_DIR / "latest_ingestion.json"
    latest_path.write_text(json.dumps(metadata, indent=2), encoding="utf-8")

    return metadata
