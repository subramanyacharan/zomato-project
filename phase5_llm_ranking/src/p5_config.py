import os
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent
PHASE3_ROOT = PROJECT_ROOT.parent / "phase3_preference_collection"
PHASE4_ROOT = PROJECT_ROOT.parent / "phase4_candidate_filtering"

PHASE3_PROFILE_FILE = PHASE3_ROOT / "output" / "profiles" / "latest_profile.json"
PHASE4_METADATA_FILE = PHASE4_ROOT / "output" / "metadata" / "latest_filtering.json"

OUTPUT_DIR = PROJECT_ROOT / "output"
RECOMMENDATIONS_DIR = OUTPUT_DIR / "recommendations"
METADATA_DIR = OUTPUT_DIR / "metadata"

GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
import streamlit as st
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
if not GROQ_API_KEY:
    try:
        GROQ_API_KEY = st.secrets["GROQ_API_KEY"]
    except:
        pass

DEFAULT_TOP_N = 10
