# Phase 4: Candidate Retrieval and Rule-Based Filtering

This folder implements **Phase 4** from `Docs/Phase Wise Architecture.md`.

## Purpose

- Apply rule-based filtering using normalized user preferences.
- Shortlist top candidates for LLM ranking in Phase 5.
- Support progressive constraint relaxation when strict matches are empty.

## Inputs

- Phase 2 latest preprocessing metadata:
  - `../phase2_preprocessing/processed/metadata/latest_preprocessing.json`
- Phase 3 latest normalized profile:
  - `../phase3_preference_collection/output/profiles/latest_profile.json`

## Filtering logic

Strict matching order:
1. location
2. cuisine
3. budget range
4. minimum rating

Relaxation strategy when no strict matches:
1. reduce minimum rating by 0.5
2. relax budget
3. relax cuisine
4. location-only fallback

## Run

From `phase4_candidate_filtering`:

```powershell
& "$env:LocalAppData\Programs\Python\Python312\python.exe" -m pip install -r requirements.txt
& "$env:LocalAppData\Programs\Python\Python312\python.exe" src/main.py --top-n 25
```

## Outputs

- `output/candidates/shortlisted_candidates_<timestamp>.parquet`
- `output/metadata/filtering_<timestamp>.json`
- `output/metadata/latest_filtering.json`

Metadata includes row counts, relaxation reasons, and output file path.
