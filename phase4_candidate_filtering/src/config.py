from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent
PHASE2_ROOT = PROJECT_ROOT.parent / "phase2_preprocessing"
PHASE3_ROOT = PROJECT_ROOT.parent / "phase3_preference_collection"

PHASE2_METADATA_FILE = PHASE2_ROOT / "processed" / "metadata" / "latest_preprocessing.json"
PHASE3_PROFILE_FILE = PHASE3_ROOT / "output" / "profiles" / "latest_profile.json"

OUTPUT_DIR = PROJECT_ROOT / "output"
CANDIDATES_DIR = OUTPUT_DIR / "candidates"
METADATA_DIR = OUTPUT_DIR / "metadata"

DEFAULT_TOP_N = 25
