import json
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from difflib import get_close_matches
from pathlib import Path
from typing import Any, Optional

import pandas as pd

from config import BUDGET_ALIASES, PHASE2_METADATA_FILE, PROFILES_DIR


@dataclass
class ValidationResult:
    normalized_profile: dict[str, Any]
    warnings: list[str]
    errors: list[str]


def _clean_text(value: Any) -> Optional[str]:
    if value is None:
        return None
    text = str(value).strip()
    if not text:
        return None
    return re.sub(r"\s+", " ", text)


def _normalize_budget(value: Any) -> tuple[Optional[str], Optional[str]]:
    text = _clean_text(value)
    if text is None:
        return None, "Missing budget. Use low, medium, or high."
    try:
        numeric_budget = float(text)
        if numeric_budget < 0:
            return None, "Budget cannot be negative."
        if numeric_budget <= 800:
            return "low", None
        if numeric_budget <= 1800:
            return "medium", None
        return "high", None
    except ValueError:
        pass
    key = text.lower()
    canonical = BUDGET_ALIASES.get(key)
    if canonical is None:
        return None, (
            f"Invalid budget '{text}'. Allowed values: low, medium, high, "
            "or a numeric amount."
        )
    return canonical, None


def _normalize_min_rating(value: Any) -> tuple[Optional[float], Optional[str]]:
    if value is None or str(value).strip() == "":
        return None, None
    try:
        rating = float(value)
    except (TypeError, ValueError):
        return None, f"Invalid minimum rating '{value}'. Must be numeric."
    if not (0 <= rating <= 5):
        return None, "Minimum rating must be between 0 and 5."
    return round(rating, 1), None


def _load_phase2_reference() -> pd.DataFrame:
    if not PHASE2_METADATA_FILE.exists():
        raise FileNotFoundError(
            f"Phase 2 metadata not found: {PHASE2_METADATA_FILE}. Run Phase 2 first."
        )
    metadata = json.loads(PHASE2_METADATA_FILE.read_text(encoding="utf-8"))
    output_path = metadata.get("phase2_output_path")
    if not output_path:
        raise ValueError("Invalid Phase 2 metadata: missing 'phase2_output_path'.")
    data_path = Path(output_path)
    if not data_path.exists():
        raise FileNotFoundError(f"Phase 2 output not found: {data_path}")
    return pd.read_parquet(data_path)


def _normalize_location(value: Any, valid_locations: list[str]) -> tuple[Optional[str], list[str]]:
    warnings: list[str] = []
    text = _clean_text(value)
    if text is None:
        return None, ["Location is required."]

    location_title = text.title()
    if location_title in valid_locations:
        return location_title, warnings

    match = get_close_matches(location_title, valid_locations, n=1, cutoff=0.75)
    if match:
        warnings.append(
            f"Location '{text}' normalized to '{match[0]}' using fuzzy matching."
        )
        return match[0], warnings

    return None, [f"Location '{text}' is not supported in current dataset."]


def _normalize_cuisine(value: Any, valid_cuisines: list[str]) -> tuple[Optional[str], list[str]]:
    warnings: list[str] = []
    text = _clean_text(value)
    if text is None:
        return None, ["Cuisine not provided; filtering will not enforce cuisine."]

    cuisine_title = text.title()
    if cuisine_title in valid_cuisines:
        return cuisine_title, warnings

    match = get_close_matches(cuisine_title, valid_cuisines, n=1, cutoff=0.75)
    if match:
        warnings.append(
            f"Cuisine '{text}' normalized to '{match[0]}' using fuzzy matching."
        )
        return match[0], warnings

    return None, [f"Cuisine '{text}' is not supported in current dataset."]


def _extract_reference_lists(df: pd.DataFrame) -> tuple[list[str], list[str]]:
    locations = sorted({str(v).strip() for v in df["location"].dropna().unique() if str(v).strip()})

    cuisines: set[str] = set()
    for value in df["cuisines"].dropna():
        for item in str(value).split(","):
            token = item.strip()
            if token:
                cuisines.add(token)
    return locations, sorted(cuisines)


def build_profile(payload: dict[str, Any]) -> ValidationResult:
    df = _load_phase2_reference()
    valid_locations, valid_cuisines = _extract_reference_lists(df)

    errors: list[str] = []
    warnings: list[str] = []

    location, location_messages = _normalize_location(payload.get("location"), valid_locations)
    for msg in location_messages:
        if "normalized" in msg:
            warnings.append(msg)
        else:
            errors.append(msg)

    cuisine, cuisine_messages = _normalize_cuisine(payload.get("cuisine"), valid_cuisines)
    for msg in cuisine_messages:
        if "normalized" in msg or "not provided" in msg:
            warnings.append(msg)
        else:
            errors.append(msg)

    budget, budget_error = _normalize_budget(payload.get("budget"))
    if budget_error:
        errors.append(budget_error)

    min_rating, rating_error = _normalize_min_rating(payload.get("minimum_rating"))
    if rating_error:
        errors.append(rating_error)

    additional_preferences = payload.get("additional_preferences", [])
    if additional_preferences is None:
        additional_preferences = []
    if not isinstance(additional_preferences, list):
        errors.append("additional_preferences must be a list of strings.")
        additional_preferences = []
    else:
        additional_preferences = [
            p for p in (_clean_text(v) for v in additional_preferences) if p is not None
        ]

    normalized_profile = {
        "location": location,
        "budget": budget,
        "cuisine": cuisine,
        "minimum_rating": min_rating,
        "additional_preferences": additional_preferences,
        "source": "phase3_preference_collection",
    }

    return ValidationResult(
        normalized_profile=normalized_profile,
        warnings=warnings,
        errors=errors,
    )


def save_profile(validation_result: ValidationResult) -> dict[str, Any]:
    PROFILES_DIR.mkdir(parents=True, exist_ok=True)
    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    output_path = PROFILES_DIR / f"normalized_profile_{run_id}.json"

    output_payload = {
        "run_id": run_id,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "normalized_profile": validation_result.normalized_profile,
        "warnings": validation_result.warnings,
        "errors": validation_result.errors,
        "is_valid": len(validation_result.errors) == 0,
    }
    output_path.write_text(json.dumps(output_payload, indent=2), encoding="utf-8")

    latest_path = PROFILES_DIR / "latest_profile.json"
    latest_path.write_text(json.dumps(output_payload, indent=2), encoding="utf-8")

    return {
        "run_id": run_id,
        "output_path": str(output_path),
        "latest_path": str(latest_path),
        "is_valid": output_payload["is_valid"],
        "warnings_count": len(validation_result.warnings),
        "errors_count": len(validation_result.errors),
    }
