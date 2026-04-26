import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd

from p4_config import (
    CANDIDATES_DIR,
    DEFAULT_TOP_N,
    METADATA_DIR,
    PHASE2_METADATA_FILE,
    PHASE3_PROFILE_FILE,
)


BUDGET_RANGES = {
    "low": (0.0, 800.0),
    "medium": (500.0, 1800.0),
    "high": (1500.0, float("inf")),
}


def _ensure_dirs() -> None:
    CANDIDATES_DIR.mkdir(parents=True, exist_ok=True)
    METADATA_DIR.mkdir(parents=True, exist_ok=True)


def _run_id() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def _load_phase2_df() -> pd.DataFrame:
    if not PHASE2_METADATA_FILE.exists():
        raise FileNotFoundError(
            f"Phase 2 metadata not found: {PHASE2_METADATA_FILE}. Run Phase 2 first."
        )
    metadata = json.loads(PHASE2_METADATA_FILE.read_text(encoding="utf-8"))
    data_path = metadata.get("phase2_output_path")
    if not data_path:
        raise ValueError("Invalid Phase 2 metadata: missing 'phase2_output_path'.")
    path = Path(data_path)
    if not path.exists():
        raise FileNotFoundError(f"Phase 2 dataset not found: {path}")
    return pd.read_parquet(path)


def _load_phase3_profile() -> dict[str, Any]:
    if not PHASE3_PROFILE_FILE.exists():
        raise FileNotFoundError(
            f"Phase 3 profile not found: {PHASE3_PROFILE_FILE}. Run Phase 3 first."
        )
    payload = json.loads(PHASE3_PROFILE_FILE.read_text(encoding="utf-8"))
    profile = payload.get("normalized_profile")
    if not profile:
        raise ValueError("Invalid Phase 3 profile: missing 'normalized_profile'.")
    if not payload.get("is_valid", False):
        raise ValueError("Phase 3 profile is invalid. Resolve profile errors first.")
    return profile


def _contains_cuisine(series: pd.Series, cuisine: str) -> pd.Series:
    cuisine_l = cuisine.lower()
    return series.fillna("").str.lower().str.contains(cuisine_l, regex=False)


def _apply_location(df: pd.DataFrame, location: str) -> pd.DataFrame:
    return df[df["location"].str.lower() == location.lower()].copy()


def _apply_cuisine(df: pd.DataFrame, cuisine: str) -> pd.DataFrame:
    if cuisine is None:
        return df.copy()
    return df[_contains_cuisine(df["cuisines"], cuisine)].copy()


def _apply_rating(df: pd.DataFrame, min_rating: float | None) -> pd.DataFrame:
    if min_rating is None:
        return df.copy()
    return df[df["rating"] >= float(min_rating)].copy()


def _apply_budget(df: pd.DataFrame, budget: str) -> pd.DataFrame:
    min_cost, max_cost = BUDGET_RANGES[budget]
    if max_cost == float("inf"):
        return df[df["cost_for_two"].fillna(float("inf")) >= min_cost].copy()
    return df[
        (df["cost_for_two"].fillna(-1) >= min_cost)
        & (df["cost_for_two"].fillna(-1) <= max_cost)
    ].copy()


def _score_candidates(df: pd.DataFrame, profile: dict[str, Any]) -> pd.DataFrame:
    scored = df.copy()
    min_rating = profile.get("minimum_rating") or 0.0
    budget = profile["budget"]
    b_min, b_max = BUDGET_RANGES[budget]
    target_cost = (b_min + (2200.0 if b_max == float("inf") else b_max)) / 2.0

    scored["rating_score"] = scored["rating"].fillna(0.0)
    scored["cost_score"] = 1.0 - (
        (scored["cost_for_two"].fillna(target_cost) - target_cost).abs()
        / max(target_cost, 1.0)
    )
    scored["cost_score"] = scored["cost_score"].clip(lower=0.0, upper=1.0)
    scored["preference_score"] = (
        (scored["rating_score"] - min_rating).clip(lower=0.0) * 0.75
        + scored["cost_score"] * 0.25
    )

    scored = scored.sort_values(
        by=["preference_score", "rating", "name"], ascending=[False, False, True]
    )
    return scored


def _filter_with_relaxation(df: pd.DataFrame, profile: dict[str, Any]) -> tuple[pd.DataFrame, list[str]]:
    reasons: list[str] = []
    location = profile["location"]
    cuisine = profile["cuisine"]
    budget = profile["budget"]
    min_rating = profile.get("minimum_rating")

    # Pass 1: strict
    strict = _apply_location(df, location)
    strict = _apply_cuisine(strict, cuisine)
    strict = _apply_budget(strict, budget)
    strict = _apply_rating(strict, min_rating)
    if len(strict) > 0:
        return strict, reasons

    # Pass 2: relax rating by 0.5
    if min_rating is not None:
        relaxed_rating = max(0.0, float(min_rating) - 0.5)
        p2 = _apply_location(df, location)
        p2 = _apply_cuisine(p2, cuisine)
        p2 = _apply_budget(p2, budget)
        p2 = _apply_rating(p2, relaxed_rating)
        if len(p2) > 0:
            reasons.append(
                f"No strict matches found; relaxed minimum rating from {min_rating} to {relaxed_rating}."
            )
            return p2, reasons

    # Pass 3: ignore budget, keep location+cuisine+rating
    p3 = _apply_location(df, location)
    p3 = _apply_cuisine(p3, cuisine)
    p3 = _apply_rating(p3, min_rating)
    if len(p3) > 0:
        reasons.append("No budget-compliant matches found; budget constraint was relaxed.")
        return p3, reasons

    # Pass 4: keep location + budget + rating, relax cuisine
    p4 = _apply_location(df, location)
    p4 = _apply_budget(p4, budget)
    p4 = _apply_rating(p4, min_rating)
    if len(p4) > 0:
        if cuisine is None:
            reasons.append("Cuisine was not provided; location/budget/rating filters were used.")
        else:
            reasons.append("No cuisine matches found; cuisine constraint was relaxed.")
        return p4, reasons

    # Pass 5: location only fallback
    p5 = _apply_location(df, location)
    if len(p5) > 0:
        reasons.append(
            "Only location-matched candidates were available; budget/cuisine/rating were relaxed."
        )
        return p5, reasons

    return pd.DataFrame(columns=df.columns), ["No candidates available for selected location."]


def run_candidate_filtering(top_n: int = DEFAULT_TOP_N) -> dict[str, Any]:
    _ensure_dirs()
    run_id = _run_id()

    df = _load_phase2_df()
    profile = _load_phase3_profile()

    filtered, relaxation_reasons = _filter_with_relaxation(df, profile)
    scored = _score_candidates(filtered, profile) if len(filtered) > 0 else filtered
    shortlisted = scored.head(top_n).copy()

    if len(shortlisted) > 0:
        shortlisted["rank"] = range(1, len(shortlisted) + 1)
        shortlisted = shortlisted[
            [
                "rank",
                "name",
                "location",
                "cuisines",
                "cost_for_two",
                "rating",
                "tags",
                "preference_score",
            ]
        ]

    candidates_path = CANDIDATES_DIR / f"shortlisted_candidates_{run_id}.parquet"
    shortlisted.to_parquet(candidates_path, index=False)

    metadata = {
        "run_id": run_id,
        "profile_used": profile,
        "input_row_count": int(len(df)),
        "filtered_row_count": int(len(filtered)),
        "shortlisted_row_count": int(len(shortlisted)),
        "top_n": int(top_n),
        "relaxation_reasons": relaxation_reasons,
        "candidates_output_path": str(candidates_path),
        "processed_at_utc": datetime.now(timezone.utc).isoformat(),
    }

    metadata_path = METADATA_DIR / f"filtering_{run_id}.json"
    metadata_path.write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    latest_path = METADATA_DIR / "latest_filtering.json"
    latest_path.write_text(json.dumps(metadata, indent=2), encoding="utf-8")

    return metadata
