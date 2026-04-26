import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd

from p5_config import (
    DEFAULT_TOP_N,
    METADATA_DIR,
    PHASE3_PROFILE_FILE,
    PHASE4_METADATA_FILE,
    RECOMMENDATIONS_DIR,
    GROQ_API_KEY,
    GROQ_API_URL,
    GROQ_MODEL
)
from groq_client import call_groq
from prompt_builder import build_prompt


def _ensure_dirs() -> None:
    RECOMMENDATIONS_DIR.mkdir(parents=True, exist_ok=True)
    METADATA_DIR.mkdir(parents=True, exist_ok=True)


def _run_id() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def _load_profile() -> dict[str, Any]:
    if not PHASE3_PROFILE_FILE.exists():
        raise FileNotFoundError(
            f"Phase 3 profile not found: {PHASE3_PROFILE_FILE}. Run Phase 3 first."
        )
    payload = json.loads(PHASE3_PROFILE_FILE.read_text(encoding="utf-8"))
    if not payload.get("is_valid", False):
        raise ValueError("Phase 3 profile is invalid. Resolve errors before Phase 5.")
    profile = payload.get("normalized_profile")
    if not profile:
        raise ValueError("Invalid Phase 3 profile payload: missing normalized_profile.")
    return profile


def _load_candidates() -> pd.DataFrame:
    if not PHASE4_METADATA_FILE.exists():
        raise FileNotFoundError(
            f"Phase 4 metadata not found: {PHASE4_METADATA_FILE}. Run Phase 4 first."
        )
    metadata = json.loads(PHASE4_METADATA_FILE.read_text(encoding="utf-8"))
    path = metadata.get("candidates_output_path")
    if not path:
        raise ValueError("Invalid Phase 4 metadata: missing candidates_output_path.")
    data_path = Path(path)
    if not data_path.exists():
        raise FileNotFoundError(f"Phase 4 candidates file not found: {data_path}")
    return pd.read_parquet(data_path)


def _to_candidate_dicts(df: pd.DataFrame, top_n: int) -> list[dict[str, Any]]:
    subset = df.head(top_n).copy()
    fields = ["rank", "name", "location", "cuisines", "cost_for_two", "rating", "tags"]
    for field in fields:
        if field not in subset.columns:
            subset[field] = None
    records = subset[fields].to_dict(orient="records")
    return [{k: (None if pd.isna(v) else v) for k, v in r.items()} for r in records]


def _mock_response(candidates: list[dict[str, Any]], top_n: int) -> dict[str, Any]:
    recs = []
    for idx, c in enumerate(candidates[:top_n], start=1):
        recs.append(
            {
                "rank": idx,
                "restaurant_name": c.get("name"),
                "reason": (
                    f"Matches requested location/cuisine with rating {c.get('rating')} "
                    f"and estimated cost for two {c.get('cost_for_two')}."
                ),
            }
        )
    return {
        "recommendations": recs,
        "summary": "Generated using mock mode (no live Groq call).",
    }


def _merge_llm_with_candidates(
    llm_output: dict[str, Any], candidates_df: pd.DataFrame
) -> pd.DataFrame:
    recs = llm_output.get("recommendations", [])
    summary = llm_output.get("summary", "")
    if not isinstance(recs, list):
        raise ValueError("LLM response 'recommendations' must be a list.")

    by_name = {
        str(row["name"]).strip().lower(): row
        for _, row in candidates_df.iterrows()
        if str(row.get("name", "")).strip()
    }

    rows = []
    for item in recs:
        name = str(item.get("restaurant_name", "")).strip()
        rank = item.get("rank")
        reason = item.get("reason", "")
        source = by_name.get(name.lower())
        if source is None:
            continue
        rows.append(
            {
                "rank": rank,
                "restaurant_name": source.get("name"),
                "location": source.get("location"),
                "cuisines": source.get("cuisines"),
                "cost_for_two": source.get("cost_for_two"),
                "rating": source.get("rating"),
                "tags": source.get("tags"),
                "llm_reason": reason,
                "llm_summary": summary,
            }
        )

    result = pd.DataFrame(rows)
    if len(result) == 0:
        raise ValueError("LLM response could not be mapped to candidate set.")
    result = result.sort_values(by=["rank"], ascending=[True]).reset_index(drop=True)
    return result


def run_phase5(top_n: int = DEFAULT_TOP_N, mock: bool = False) -> dict[str, Any]:
    _ensure_dirs()
    run_id = _run_id()

    profile = _load_profile()
    candidates_df = _load_candidates()
    candidate_records = _to_candidate_dicts(candidates_df, top_n=top_n)
    if len(candidate_records) == 0:
        raise ValueError("No candidates found from Phase 4 output.")

    prompt = build_prompt(profile=profile, candidates=candidate_records, top_n=top_n)
    llm_output = _mock_response(candidate_records, top_n) if mock else call_groq(prompt)

    recommendation_df = _merge_llm_with_candidates(llm_output, candidates_df)

    output_path = RECOMMENDATIONS_DIR / f"ranked_recommendations_{run_id}.parquet"
    recommendation_df.to_parquet(output_path, index=False)

    metadata = {
        "run_id": run_id,
        "top_n": top_n,
        "model_provider": "groq",
        "mock_mode": mock,
        "input_candidates_count": int(len(candidates_df)),
        "output_recommendations_count": int(len(recommendation_df)),
        "recommendations_output_path": str(output_path),
        "processed_at_utc": datetime.now(timezone.utc).isoformat(),
    }

    metadata_path = METADATA_DIR / f"ranking_{run_id}.json"
    metadata_path.write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    latest_path = METADATA_DIR / "latest_ranking.json"
    latest_path.write_text(json.dumps(metadata, indent=2), encoding="utf-8")

    return metadata
