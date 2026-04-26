from pathlib import Path


DATASET_ID = "ManikaSaini/zomato-restaurant-recommendation"
DEFAULT_SPLIT = "train"

# Resolve paths relative to this module, not process cwd.
PROJECT_ROOT = Path(__file__).resolve().parent.parent
STAGING_DIR = PROJECT_ROOT / "staging"
RAW_DIR = STAGING_DIR / "raw"
METADATA_DIR = STAGING_DIR / "metadata"
