# Phase 2: Data Preprocessing and Feature Preparation

This folder contains the implementation of **Phase 2** from `Docs/Phase Wise Architecture.md`.

## What this phase does

- Reads Phase 1 raw snapshot metadata from:
  - `../phase1_data_acquisition/staging/metadata/latest_ingestion.json`
- Loads the raw parquet dataset.
- Cleans and standardizes key fields:
  - `name`
  - `location`
  - `cuisines`
  - `cost_for_two`
  - `rating`
  - `tags`
- Drops invalid records and writes structured output.

## Folder structure

- `src/config.py` - paths and constants
- `src/preprocess.py` - preprocessing pipeline
- `src/main.py` - entrypoint
- `processed/structured/` - cleaned output parquet
- `processed/metadata/` - preprocessing metadata JSON

## Setup

Use the same Python installed for Phase 1:

```powershell
& "$env:LocalAppData\Programs\Python\Python312\python.exe" -m pip install -r requirements.txt
```

## Run

From inside `phase2_preprocessing`:

```powershell
& "$env:LocalAppData\Programs\Python\Python312\python.exe" src/main.py
```

## Output

Each run creates:
- `processed/structured/zomato_structured_<timestamp>.parquet`
- `processed/metadata/preprocessing_<timestamp>.json`
- `processed/metadata/latest_preprocessing.json`
