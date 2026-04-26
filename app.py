import os
import sys
import json
import tempfile
import subprocess
from pathlib import Path
from typing import Any, Tuple

import pandas as pd
import streamlit as st
from dotenv import load_dotenv

# Page config must be the first Streamlit command
st.set_page_config(
    page_title="Zomato AI Engine",
    page_icon="🍽️",
    layout="centered",
    initial_sidebar_state="expanded",
)

# Load environment variables
PROJECT_ROOT = Path(__file__).resolve().parent
load_dotenv(PROJECT_ROOT / ".env")

def run_script(script_path: str, args: list[str]) -> dict[str, Any]:
    cmd = [sys.executable, str(PROJECT_ROOT / script_path)] + args
    
    # Merge current environment with Streamlit secrets
    env = os.environ.copy()
    try:
        # Inject streamlit secrets into the environment for subprocesses
        for key, value in st.secrets.items():
            env[key] = str(value)
    except:
        pass # Not running in Streamlit Cloud or no secrets set
        
    result = subprocess.run(cmd, cwd=str(PROJECT_ROOT), capture_output=True, text=True, env=env)
    if result.returncode != 0:
        raise Exception(f"Script {script_path} failed: {result.stderr}")
    
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError:
        raise Exception(f"Failed to parse JSON output: {result.stdout}")

@st.cache_data(show_spinner=False, ttl=3600)
def fetch_recommendations(location: str, budget: str, minimum_rating: float, cuisine: str, top_n: int, mock: bool) -> Tuple[pd.DataFrame, list[str]]:
    """Cached function to prevent running heavy subprocesses multiple times for the same input."""
    
    payload = {
        "location": location,
        "budget": budget,
        "cuisine": cuisine if cuisine else None,
        "minimum_rating": minimum_rating,
        "additional_preferences": []
    }
    
    warnings = []

    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix=".json") as tf:
        json.dump(payload, tf)
        temp_input_path = tf.name
        
    try:
        # Phase 3
        p3_res = run_script("phase3_preference_collection/src/main.py", ["--input", temp_input_path])
        if p3_res.get("errors"):
            raise ValueError(f"Validation Errors: {', '.join(p3_res['errors'])}")
            
        # Phase 4
        p4_res = run_script("phase4_candidate_filtering/src/main.py", ["--top-n", str(top_n)])
        if p4_res.get("shortlisted_row_count", 0) == 0:
            if p4_res.get("relaxation_reasons"):
                warnings.extend(p4_res["relaxation_reasons"])
            raise ValueError("No candidates matched your criteria.")
            
        if p4_res.get("relaxation_reasons"):
            warnings.extend(p4_res["relaxation_reasons"])
            
        # Phase 5
        p5_args = ["--top-n", str(top_n)]
        if mock:
            p5_args.append("--mock")
        p5_res = run_script("phase5_llm_ranking/src/main.py", p5_args)
        
        # Parse Output
        parquet_path = p5_res.get("recommendations_output_path")
        if not parquet_path or not Path(parquet_path).exists():
            raise Exception("AI ranking output file not found.")
            
        df = pd.read_parquet(parquet_path)
        return df, warnings
        
    finally:
        if os.path.exists(temp_input_path):
            os.remove(temp_input_path)


# Custom CSS for Aesthetics
st.markdown("""
<style>
    .stApp { background-color: #0a0a0f; }
    .restaurant-card {
        background-color: rgba(255, 255, 255, 0.05);
        border: 1px solid rgba(255, 255, 255, 0.1);
        padding: 1.5rem;
        border-radius: 12px;
        margin-bottom: 1.5rem;
        transition: all 0.3s ease;
    }
    .restaurant-card:hover {
        border-color: rgba(255, 71, 87, 0.5);
        box-shadow: 0 4px 20px rgba(0,0,0,0.4);
    }
    .restaurant-title {
        font-size: 1.5rem;
        font-weight: 600;
        margin-bottom: 0.5rem;
        color: #ffffff;
    }
    .ai-insight {
        background-color: rgba(83, 82, 237, 0.15);
        border-left: 4px solid #5352ed;
        padding: 1rem;
        border-radius: 4px;
        margin-top: 1rem;
        font-style: italic;
        line-height: 1.5;
    }
</style>
""", unsafe_allow_html=True)

st.title("🍽️ Zomato AI Recommendations")
st.markdown("Discover your next favorite meal using our advanced LLM-powered engine.")

# Sidebar for inputs
with st.sidebar:
    st.header("Your Preferences")
    
    locations = ["Bellandur", "Indiranagar", "Koramangala", "Whitefield", "Marathahalli", "HSR", "Jayanagar", "JP Nagar", "BTM", "Banashankari", "Malleshwaram", "MG Road", "Electronic City", "Sarjapur Road"]
    location = st.selectbox("Location", options=locations, index=0)
    
    budget = st.selectbox("Budget", options=["low", "medium", "high"], index=2)
    
    ratings = [3.0, 3.5, 4.0, 4.5, 4.8]
    minimum_rating = st.selectbox("Minimum Rating", options=ratings, index=2)
    
    cuisines = ["Any", "North Indian", "South Indian", "Chinese", "Italian", "Continental", "Desserts", "Fast Food", "Biryani", "Street Food", "Cafe", "Mexican", "Japanese", "Healthy Food"]
    cuisine_selection = st.selectbox("Cuisine", options=cuisines, index=0)
    cuisine = None if cuisine_selection == "Any" else cuisine_selection
    
    top_n = st.slider("Number of Recommendations", min_value=1, max_value=10, value=5)
    mock = st.checkbox("Mock Mode (No API Call)", value=False)
    
    submit_button = st.button("Generate Recommendations", type="primary", use_container_width=True)

if submit_button:
    if not location:
        st.warning("Please enter a location.")
        st.stop()

    status_placeholder = st.empty()
    status_placeholder.info("🚀 Processing request... (This may take up to 15 seconds if booting up).")

    try:
        df, warnings = fetch_recommendations(
            location=location,
            budget=budget,
            minimum_rating=minimum_rating,
            cuisine=cuisine,
            top_n=top_n,
            mock=mock
        )
        
        status_placeholder.empty()
        st.success("✅ Analysis Complete!")
        
        for warning in warnings:
            st.warning(f"Note: {warning}")

        if not df.empty:
            st.markdown(f"### ✨ AI Summary\n*{df.iloc[0].get('llm_summary', '')}*")
            st.divider()

            for _, row in df.iterrows():
                with st.container():
                    st.markdown(f"""
                    <div class="restaurant-card">
                        <div class="restaurant-title">#{int(row['rank'])} - {str(row['restaurant_name'])}</div>
                        <div style="color: #fbbf24; font-weight: bold; margin-bottom: 0.5rem;">★ {float(row.get('rating', 0))} &nbsp;|&nbsp; <span style="color: #a0a0ab;">₹{float(row.get('cost_for_two', 0))} for two</span></div>
                        <div style="color: #a0a0ab; font-size: 0.9rem; margin-bottom: 0.5rem;">{str(row.get('cuisines', ''))}</div>
                        <div class="ai-insight">
                            <strong>AI Insight:</strong> {str(row.get('llm_reason', ''))}
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                    
    except ValueError as e:
        status_placeholder.empty()
        st.error(str(e))
    except Exception as e:
        status_placeholder.empty()
        st.error(f"Critical System Error: {str(e)}")
else:
    st.info("👈 Enter your preferences in the sidebar and click **Generate Recommendations** to begin!")
