# Phase 1: Data Acquisition and Storage

This folder contains the implementation of **Phase 1** from `Docs/Phase Wise Architecture.md`.

## What this phase does

- Downloads the Zomato dataset from Hugging Face (`ManikaSaini/zomato-restaurant-recommendation`)
- Stores a **raw versioned snapshot** in staging storage
- Writes ingestion metadata (row count, columns, timestamp, output path)

## Folder structure

- `src/config.py` - dataset/staging configuration
- `src/ingest.py` - ingestion logic
- `src/main.py` - command-line entrypoint
- `staging/raw/` - raw snapshot files (`.parquet`)
- `staging/metadata/` - ingestion metadata (`.json`)

## Setup

```bash
pip install -r requirements.txt
```

## Run

From inside `phase1_data_acquisition`:

```bash
python src/main.py
```

Optional split:

```bash
python src/main.py --split train
```

## Output

Each run creates:
- `staging/raw/zomato_raw_<timestamp>.parquet`
- `staging/metadata/ingestion_<timestamp>.json`
- `staging/metadata/latest_ingestion.json`
