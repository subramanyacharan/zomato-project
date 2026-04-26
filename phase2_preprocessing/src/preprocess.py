import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import pandas as pd

from config import METADATA_DIR, PHASE1_METADATA_FILE, STRUCTURED_DIR


LOCATION_ALIASES = {
    "bengaluru": "Bangalore",
    "bangalore": "Bangalore",
    "new delhi": "Delhi",
    "delhi ncr": "Delhi",
}

CUISINE_ALIASES = {
    "north indian": "North Indian",
    "south indian": "South Indian",
    "street food": "Street Food",
    "fast food": "Fast Food",
}


def _ensure_dirs() -> None:
    STRUCTURED_DIR.mkdir(parents=True, exist_ok=True)
    METADATA_DIR.mkdir(parents=True, exist_ok=True)


def _build_run_id() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def _load_phase1_raw_path() -> Path:
    if not PHASE1_METADATA_FILE.exists():
        raise FileNotFoundError(
            f"Phase 1 metadata not found: {PHASE1_METADATA_FILE}. Run Phase 1 first."
        )
    payload = json.loads(PHASE1_METADATA_FILE.read_text(encoding="utf-8"))
    raw_output_path = payload.get("raw_output_path")
    if not raw_output_path:
        raise ValueError("Invalid Phase 1 metadata: missing 'raw_output_path'.")
    path = Path(raw_output_path)
    if not path.exists():
        raise FileNotFoundError(
            f"Phase 1 raw output path does not exist: {raw_output_path}"
        )
    return path


def _clean_text(value: object) -> Optional[str]:
    if value is None:
        return None
    text = str(value).strip()
    if not text or text.lower() in {"nan", "none", "null"}:
        return None
    return text


def _normalize_location(value: object) -> Optional[str]:
    text = _clean_text(value)
    if text is None:
        return None
    key = re.sub(r"\s+", " ", text.lower())
    mapped = LOCATION_ALIASES.get(key, text.title())
    return mapped


def _normalize_cuisines(value: object) -> str:
    text = _clean_text(value)
    if text is None:
        return "Unknown"
    parts = [part.strip() for part in re.split(r"[,/|]", text) if part.strip()]
    normalized = []
    for part in parts:
        key = re.sub(r"\s+", " ", part.lower())
        normalized.append(CUISINE_ALIASES.get(key, part.title()))
    normalized = sorted(set(normalized))
    return ", ".join(normalized) if normalized else "Unknown"


def _parse_cost(value: object) -> Optional[float]:
    text = _clean_text(value)
    if text is None:
        return None
    cleaned = text.replace(",", "")
    nums = re.findall(r"\d+(?:\.\d+)?", cleaned)
    if not nums:
        return None
    if len(nums) == 1:
        return float(nums[0])
    # If range is provided, use mean to normalize.
    values = [float(n) for n in nums]
    return sum(values) / len(values)


def _parse_rating(value: object) -> Optional[float]:
    text = _clean_text(value)
    if text is None:
        return None
    if text.upper() in {"NEW", "-", "N/A"}:
        return None
    match = re.search(r"\d+(?:\.\d+)?", text)
    if not match:
        return None
    rating = float(match.group(0))
    if rating > 5.0:
        return None
    return rating


def _build_tags(row: pd.Series) -> str:
    tags = []
    for col in ["rest_type", "listed_in(type)", "listed_in(city)"]:
        value = _clean_text(row.get(col))
        if value:
            tags.extend([v.strip().title() for v in value.split(",") if v.strip()])
    deduped = sorted(set(tags))
    return ", ".join(deduped)


def preprocess_phase2() -> dict:
    _ensure_dirs()
    run_id = _build_run_id()

    raw_path = _load_phase1_raw_path()
    df = pd.read_parquet(raw_path)
    input_rows = len(df)

    df["name"] = df["name"].map(_clean_text)
    df["location"] = df["location"].map(_normalize_location)
    df["cuisines"] = df["cuisines"].map(_normalize_cuisines)
    df["cost_for_two"] = df["approx_cost(for two people)"].map(_parse_cost)
    df["rating"] = df["rate"].map(_parse_rating)
    df["tags"] = df.apply(_build_tags, axis=1)

    # Mandatory core fields for downstream filtering/ranking.
    cleaned_df = df.dropna(subset=["name", "location", "rating"])

    # Remove impossible values.
    cleaned_df = cleaned_df[
        (cleaned_df["rating"] >= 0.0)
        & (cleaned_df["rating"] <= 5.0)
        & ((cleaned_df["cost_for_two"].isna()) | (cleaned_df["cost_for_two"] >= 0))
    ]

    structured_df = cleaned_df[
        ["name", "location", "cuisines", "cost_for_two", "rating", "tags"]
    ].copy()
    structured_df = structured_df.drop_duplicates(subset=["name", "location", "cuisines"])
    structured_df = structured_df.sort_values(
        by=["location", "rating", "name"], ascending=[True, False, True]
    )

    output_path = STRUCTURED_DIR / f"zomato_structured_{run_id}.parquet"
    structured_df.to_parquet(output_path, index=False)

    metadata = {
        "run_id": run_id,
        "phase1_raw_input_path": str(raw_path),
        "phase2_output_path": str(output_path),
        "input_row_count": int(input_rows),
        "output_row_count": int(len(structured_df)),
        "output_columns": list(structured_df.columns),
        "processed_at_utc": datetime.now(timezone.utc).isoformat(),
    }

    metadata_path = METADATA_DIR / f"preprocessing_{run_id}.json"
    metadata_path.write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    latest_path = METADATA_DIR / "latest_preprocessing.json"
    latest_path.write_text(json.dumps(metadata, indent=2), encoding="utf-8")

    return metadata
