import json
import pandas as pd
from pathlib import Path

ROOT = Path(".")
PHASE2_METADATA_DIR = ROOT / "phase2_preprocessing" / "processed" / "metadata"

def main():
    latest_metadata_file = PHASE2_METADATA_DIR / "latest_preprocessing.json"
    if not latest_metadata_file.exists():
        print("Latest preprocessing metadata not found.")
        return

    with open(latest_metadata_file, "r") as f:
        metadata = json.load(f)
    
    dataset_path = Path(metadata["phase2_output_path"])
    if not dataset_path.exists():
        print(f"Dataset not found at {dataset_path}")
        return

    print(f"Loading dataset from {dataset_path}...")
    df = pd.read_parquet(dataset_path)
    
    print("Extracting locations...")
    locations = sorted({str(v).strip() for v in df["location"].dropna().unique() if str(v).strip()})
    
    print("Extracting cuisines...")
    cuisines = set()
    for value in df["cuisines"].dropna():
        for item in str(value).split(","):
            token = item.strip()
            if token:
                cuisines.add(token)
    
    output_path = ROOT / "phase3_preference_collection" / "data" / "reference_lists.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        json.dump({
            "locations": locations,
            "cuisines": sorted(list(cuisines))
        }, f, indent=2)
    
    print(f"Reference lists saved to {output_path}")

if __name__ == "__main__":
    main()
