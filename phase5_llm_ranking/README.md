# Phase 5: LLM-Powered Ranking and Explanation Generation (Groq)

This folder implements **Phase 5** from `Docs/Phase Wise Architecture.md`.

## Purpose

- Use a Groq-hosted LLM to rank shortlisted candidates.
- Generate concise, human-readable explanations for each recommendation.
- Produce structured outputs for final presentation (Phase 6).

## Inputs

- Phase 3 latest normalized profile:
  - `../phase3_preference_collection/output/profiles/latest_profile.json`
- Phase 4 latest filtering metadata:
  - `../phase4_candidate_filtering/output/metadata/latest_filtering.json`
  - from metadata, this phase reads shortlisted candidate parquet.

## LLM Provider

- Provider: **Groq**
- Endpoint: `https://api.groq.com/openai/v1/chat/completions`
- Default model: `llama-3.3-70b-versatile`

## Setup

From `phase5_llm_ranking`:

```powershell
& "$env:LocalAppData\Programs\Python\Python312\python.exe" -m pip install -r requirements.txt
```

Set Groq API key (PowerShell):

```powershell
$env:GROQ_API_KEY = "your_api_key_here"
```

Optional custom model:

```powershell
$env:GROQ_MODEL = "llama-3.1-8b-instant"
```

## Run

Live Groq call:

```powershell
& "$env:LocalAppData\Programs\Python\Python312\python.exe" src/main.py --top-n 10
```

Local mock mode (no API key needed):

```powershell
& "$env:LocalAppData\Programs\Python\Python312\python.exe" src/main.py --top-n 10 --mock
```

## Outputs

- `output/recommendations/ranked_recommendations_<timestamp>.parquet`
- `output/metadata/ranking_<timestamp>.json`
- `output/metadata/latest_ranking.json`

Metadata includes provider (`groq`), mock/live mode, row counts, and output path.
