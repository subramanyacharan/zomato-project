import os
import sys
import json
import tempfile
import subprocess
from pathlib import Path
from typing import Any

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
PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_ROOT / ".env")

def run_script(script_path: str, args: list[str]) -> dict[str, Any]:
    cmd = [sys.executable, str(PROJECT_ROOT / script_path)] + args
    result = subprocess.run(cmd, cwd=str(PROJECT_ROOT), capture_output=True, text=True)
    if result.returncode != 0:
        st.error(f"Script {script_path} failed.")
        st.code(result.stderr)
        st.stop()
    
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError:
        st.error(f"Failed to parse JSON output from {script_path}.")
        st.code(result.stdout)
        st.stop()

# Custom CSS for Aesthetics
st.markdown("""
<style>
    /* Premium Streamlit Theming Override */
    .stApp {
        background-color: #0a0a0f;
    }
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
    location = st.text_input("Location", value="Bellandur", placeholder="e.g. Bellandur")
    budget = st.selectbox("Budget", options=["low", "medium", "high"], index=2)
    minimum_rating = st.number_input("Minimum Rating", min_value=0.0, max_value=5.0, value=4.0, step=0.1)
    cuisine = st.text_input("Cuisine (Optional)", placeholder="e.g. Italian")
    top_n = st.slider("Number of Recommendations", min_value=1, max_value=10, value=5)
    mock = st.checkbox("Mock Mode (No API Call)", value=False)
    
    submit_button = st.button("Generate Recommendations", type="primary", use_container_width=True)

if submit_button:
    if not location:
        st.warning("Please enter a location.")
        st.stop()

    payload = {
        "location": location,
        "budget": budget,
        "cuisine": cuisine if cuisine else None,
        "minimum_rating": minimum_rating,
        "additional_preferences": []
    }

    with st.spinner("Analyzing your preferences and consulting Llama 3.3..."):
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix=".json") as tf:
            json.dump(payload, tf)
            temp_input_path = tf.name
            
        try:
            # 1. Run Phase 3
            p3_res = run_script("phase3_preference_collection/src/main.py", ["--input", temp_input_path])
            if p3_res.get("errors"):
                st.error("Validation Errors:")
                for err in p3_res["errors"]:
                    st.write(f"- {err}")
                st.stop()
                
            # 2. Run Phase 4
            p4_res = run_script("phase4_candidate_filtering/src/main.py", ["--top-n", str(top_n)])
            if p4_res.get("shortlisted_row_count", 0) == 0:
                st.warning("No candidates matched your criteria.")
                if p4_res.get("relaxation_reasons"):
                    st.info("System tried relaxing constraints:")
                    for msg in p4_res["relaxation_reasons"]:
                        st.write(f"- {msg}")
                st.stop()
                
            # 3. Run Phase 5
            p5_args = ["--top-n", str(top_n)]
            if mock:
                p5_args.append("--mock")
            p5_res = run_script("phase5_llm_ranking/src/main.py", p5_args)
            
            # 4. Display Results
            parquet_path = p5_res.get("recommendations_output_path")
            if not parquet_path or not Path(parquet_path).exists():
                st.error("LLM ranking output file not found.")
                st.stop()
                
            df = pd.read_parquet(parquet_path)
            
            st.success("Analysis Complete!")
            
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
                        
        finally:
            if os.path.exists(temp_input_path):
                os.remove(temp_input_path)
else:
    st.info("👈 Enter your preferences in the sidebar and click **Generate Recommendations** to begin!")
