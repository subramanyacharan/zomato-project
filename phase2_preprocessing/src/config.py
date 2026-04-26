from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent
PHASE1_ROOT = PROJECT_ROOT.parent / "phase1_data_acquisition"
PHASE1_METADATA_FILE = PHASE1_ROOT / "staging" / "metadata" / "latest_ingestion.json"

PROCESSED_DIR = PROJECT_ROOT / "processed"
STRUCTURED_DIR = PROCESSED_DIR / "structured"
METADATA_DIR = PROCESSED_DIR / "metadata"
