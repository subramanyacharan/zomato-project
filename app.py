import os
import sys
import json
import tempfile
from pathlib import Path
from typing import Tuple

import pandas as pd
import streamlit as st
from dotenv import load_dotenv

# Page config must be the first Streamlit command
st.set_page_config(
    page_title="Zomato Engine",
    page_icon="🍽️",
    layout="centered",
    initial_sidebar_state="expanded",
)

# Load environment variables
PROJECT_ROOT = Path(__file__).resolve().parent
load_dotenv(PROJECT_ROOT / ".env")

# Ensure Python path is set so we can import from the phases directly
# We add each src directory to sys.path to allow internal imports like 'from pX_config import ...'
sys.path.insert(0, str(PROJECT_ROOT / "phase3_preference_collection" / "src"))
sys.path.insert(0, str(PROJECT_ROOT / "phase4_candidate_filtering" / "src"))
sys.path.insert(0, str(PROJECT_ROOT / "phase5_llm_ranking" / "src"))

# Direct imports from the modular pipeline
from profile_builder import build_profile, save_profile
from filter_engine import run_candidate_filtering
from ranker import run_phase5

@st.cache_data(show_spinner=False, ttl=3600)
def fetch_recommendations(location: str, budget: str, minimum_rating: float, cuisine: str, top_n: int) -> Tuple[pd.DataFrame, list[str]]:
    """Directly calls the pipeline functions without subprocess overhead."""
    
    payload = {
        "location": location,
        "budget": budget,
        "cuisine": cuisine if cuisine else None,
        "minimum_rating": minimum_rating,
        "additional_preferences": []
    }
    
    # 1. Run Phase 3 logic
    validation_result = build_profile(payload)
    if validation_result.errors:
        raise ValueError(f"Validation Errors: {', '.join(validation_result.errors)}")
    save_profile(validation_result)
    
    # 2. Run Phase 4 logic
    p4_res = run_candidate_filtering(top_n=top_n)
    warnings = p4_res.get("relaxation_reasons", [])
    if p4_res.get("shortlisted_row_count", 0) == 0:
        raise ValueError("No candidates matched your criteria.")
        
    # 3. Run Phase 5 logic
    p5_res = run_phase5(top_n=top_n, mock=False)
    
    # 4. Parse Results
    parquet_path = p5_res.get("recommendations_output_path")
    if not parquet_path or not Path(parquet_path).exists():
        raise Exception("Ranking output file not found.")
        
    df = pd.read_parquet(parquet_path)
    return df, warnings


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

st.title("🍽️ Zomato Engine")
st.markdown("Discover the best restaurants in town tailored just for you.")

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
    
    submit_button = st.button("Find Restaurants", type="primary", use_container_width=True)

if submit_button:
    if not location:
        st.warning("Please enter a location.")
        st.stop()

    status_placeholder = st.empty()
    status_placeholder.info("🚀 Finding the best matches for you...")

    try:
        df, warnings = fetch_recommendations(
            location=location,
            budget=budget,
            minimum_rating=minimum_rating,
            cuisine=cuisine,
            top_n=top_n
        )
        
        status_placeholder.empty()
        st.success("✅ Results Found!")
        
        for warning in warnings:
            st.warning(f"Note: {warning}")

        if not df.empty:
            st.markdown(f"### ✨ Recommendations Summary\n*{df.iloc[0].get('llm_summary', '')}*")
            st.divider()

            for _, row in df.iterrows():
                with st.container():
                    st.markdown(f"""
                    <div class="restaurant-card">
                        <div class="restaurant-title">#{int(row['rank'])} - {str(row['restaurant_name'])}</div>
                        <div style="color: #fbbf24; font-weight: bold; margin-bottom: 0.5rem;">★ {float(row.get('rating', 0))} &nbsp;|&nbsp; <span style="color: #a0a0ab;">₹{float(row.get('cost_for_two', 0))} for two</span></div>
                        <div style="color: #a0a0ab; font-size: 0.9rem; margin-bottom: 0.5rem;">{str(row.get('cuisines', ''))}</div>
                        <div class="ai-insight">
                            {str(row.get('llm_reason', ''))}
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                    
    except ValueError as e:
        status_placeholder.empty()
        st.error(str(e))
    except Exception as e:
        status_placeholder.empty()
        st.error(f"System Error: {str(e)}")
else:
    st.info("👈 Enter your preferences and click **Find Restaurants** to begin!")
