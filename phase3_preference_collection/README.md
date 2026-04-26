# Phase 3: Preference Collection and Query Understanding

This folder implements **Phase 3** from `Docs/Phase Wise Architecture.md`.

## Purpose

- Validate user preference inputs.
- Normalize user inputs into a consistent query object.
- Save normalized profile for downstream filtering (Phase 4).

## Input

JSON payload with fields:
- `location` (required)
- `budget` (required: low/medium/high + aliases)
- `cuisine` (required)
- `minimum_rating` (optional, 0-5)
- `additional_preferences` (optional list of strings)

## Data dependency

Phase 3 reads Phase 2 latest metadata:
- `../phase2_preprocessing/processed/metadata/latest_preprocessing.json`

and uses the Phase 2 structured parquet to validate supported locations/cuisines.

## Run

From `phase3_preference_collection`:

```powershell
& "$env:LocalAppData\Programs\Python\Python312\python.exe" -m pip install -r requirements.txt
& "$env:LocalAppData\Programs\Python\Python312\python.exe" src/main.py --input data/sample_input.json
```

## Output

- `output/profiles/normalized_profile_<timestamp>.json`
- `output/profiles/latest_profile.json`

The output includes:
- normalized profile
- warning list
- error list
- validity flag (`is_valid`)
