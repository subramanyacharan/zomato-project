from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent
PHASE2_ROOT = PROJECT_ROOT.parent / "phase2_preprocessing"
PHASE2_METADATA_FILE = (
    PHASE2_ROOT / "processed" / "metadata" / "latest_preprocessing.json"
)

DATA_DIR = PROJECT_ROOT / "data"
OUTPUT_DIR = PROJECT_ROOT / "output"
PROFILES_DIR = OUTPUT_DIR / "profiles"

BUDGET_ALIASES = {
    "low": "low",
    "budget": "low",
    "cheap": "low",
    "economy": "low",
    "mid": "medium",
    "medium": "medium",
    "moderate": "medium",
    "avg": "medium",
    "high": "high",
    "premium": "high",
    "expensive": "high",
    "luxury": "high",
}
