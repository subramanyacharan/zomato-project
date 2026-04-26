import os
import sys
import json
import tempfile
import subprocess
from pathlib import Path
from typing import Any

import pandas as pd
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

from .schemas import RecommendationRequest, RecommendationResponse, RestaurantRecommendation

# Load environment variables
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
load_dotenv(PROJECT_ROOT / ".env")

app = FastAPI(
    title="Restaurant Recommendation API",
    description="Phase 6 Backend API integrating data pipeline and LLM ranking.",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def run_script(script_path: str, args: list[str]) -> dict[str, Any]:
    cmd = [sys.executable, str(PROJECT_ROOT / script_path)] + args
    result = subprocess.run(cmd, cwd=str(PROJECT_ROOT), capture_output=True, text=True)
    if result.returncode != 0:
        raise HTTPException(status_code=500, detail=f"Script {script_path} failed: {result.stderr}\nStdout: {result.stdout}")
    
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError:
        raise HTTPException(status_code=500, detail=f"Failed to parse JSON output from {script_path}: {result.stdout}")

@app.post("/api/recommend", response_model=RecommendationResponse)
def recommend(request: RecommendationRequest):
    # Prepare input for Phase 3
    payload = {
        "location": request.location,
        "budget": request.budget,
        "cuisine": request.cuisine,
        "minimum_rating": request.minimum_rating,
        "additional_preferences": []
    }
    
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix=".json") as tf:
        json.dump(payload, tf)
        temp_input_path = tf.name
        
    try:
        # 1. Run Phase 3
        p3_res = run_script("phase3_preference_collection/src/main.py", ["--input", temp_input_path])
        if p3_res.get("errors"):
            raise HTTPException(status_code=400, detail={"errors": p3_res["errors"], "warnings": p3_res.get("warnings", [])})
            
        warnings = p3_res.get("warnings", [])
        
        # 2. Run Phase 4
        p4_res = run_script("phase4_candidate_filtering/src/main.py", ["--top-n", str(request.top_n)])
        if p4_res.get("shortlisted_row_count", 0) == 0:
            return RecommendationResponse(
                success=True,
                recommendations=[],
                warnings=warnings + p4_res.get("relaxation_reasons", []),
                errors=["No candidates matched the criteria."],
                metadata={"phase4": p4_res}
            )
            
        warnings.extend(p4_res.get("relaxation_reasons", []))
        
        # 3. Run Phase 5
        p5_args = ["--top-n", str(request.top_n)]
        if request.mock:
            p5_args.append("--mock")
            
        p5_res = run_script("phase5_llm_ranking/src/main.py", p5_args)
        
        # 4. Read final Parquet output
        parquet_path = p5_res.get("recommendations_output_path")
        if not parquet_path or not Path(parquet_path).exists():
            raise HTTPException(status_code=500, detail="LLM ranking output file not found.")
            
        df = pd.read_parquet(parquet_path)
        
        recs = []
        for _, row in df.iterrows():
            recs.append(RestaurantRecommendation(
                rank=int(row["rank"]),
                restaurant_name=str(row["restaurant_name"]),
                location=str(row["location"]) if pd.notna(row["location"]) else None,
                cuisines=str(row["cuisines"]) if pd.notna(row["cuisines"]) else None,
                cost_for_two=float(row["cost_for_two"]) if pd.notna(row["cost_for_two"]) else None,
                rating=float(row["rating"]) if pd.notna(row["rating"]) else None,
                tags=str(row["tags"]) if pd.notna(row["tags"]) else None,
                llm_reason=str(row.get("llm_reason", "")),
                llm_summary=str(row.get("llm_summary", ""))
            ))
            
        return RecommendationResponse(
            success=True,
            recommendations=recs,
            warnings=warnings,
            errors=[],
            metadata={
                "phase3": p3_res,
                "phase4": p4_res,
                "phase5": p5_res,
                "mock_mode": request.mock
            }
        )
        
    finally:
        if os.path.exists(temp_input_path):
            os.remove(temp_input_path)

if __name__ == "__main__":
    import uvicorn
    # Make sure we can run this directly for testing
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
