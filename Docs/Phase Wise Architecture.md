# Phase-Wise Architecture: AI-Powered Restaurant Recommendation System

## Overview

This architecture is designed for a Zomato-style restaurant recommendation system that combines structured restaurant data with a Large Language Model (LLM) to deliver personalized, explainable recommendations.

## Phase 1: Data Acquisition and Storage

**Purpose:** Collect and store restaurant data for downstream processing.

**Input:**
- Zomato dataset from Hugging Face: [Dataset Link](https://huggingface.co/datasets/ManikaSaini/zomato-restaurant-recommendation)

**Process:**
- Load the raw dataset from the source.
- Store the dataset in a staging area (local or database).

**Output:**
- Raw dataset available for preprocessing.

**Core Components:**
- Data loader
- Staging storage

---

## Phase 2: Data Preprocessing and Feature Preparation

**Purpose:** Clean and standardize data for accurate recommendation.

**Input:**
- Raw dataset from Phase 1

**Process:**
- Handle missing and inconsistent values.
- Standardize location, cuisine, cost, and rating fields.
- Extract key attributes (name, location, cuisines, cost, rating, tags).

**Output:**
- Cleaned and structured restaurant dataset.

**Core Components:**
- Data cleaning pipeline
- Feature extraction module

---

## Phase 3: Preference Collection and Query Understanding

**Purpose:** Capture and normalize user intent.

**Input:**
- User preferences:
  - Location (e.g., Delhi, Bangalore)
  - Budget (low, medium, high)
  - Cuisine preference (e.g., Italian, Chinese)
  - Minimum rating
  - Optional needs (e.g., family-friendly, quick service)

**Process:**
- Validate user inputs.
- Convert inputs to a normalized query structure.

**Output:**
- Structured user preference profile.

**Core Components:**
- Input form/API handler
- Query normalization module

---

## Phase 4: Candidate Retrieval and Rule-Based Filtering

**Purpose:** Select restaurants matching hard constraints.

**Input:**
- Structured user profile (Phase 3)
- Cleaned dataset (Phase 2)

**Process:**
- Filter by location, budget, cuisine, and minimum rating.
- Shortlist the top candidate set for LLM reasoning.

**Output:**
- Filtered candidate restaurant list.

**Core Components:**
- Filtering engine
- Candidate pre-selector

---

## Phase 5: LLM-Powered Ranking and Explanation Generation

**Purpose:** Rank shortlisted restaurants and generate reasoning.

**Input:**
- Filtered candidates (Phase 4)
- Prompt template

**Process:**
- Convert candidate records into prompt-ready context.
- Use the LLM to:
  - Rank best matches
  - Explain why each recommendation fits
  - Optionally summarize top choices

**Output:**
- Ranked recommendations with AI-generated explanations.

**Core Components:**
- Prompt builder
- LLM inference layer
- Response parser

---

## Phase 6: Backend API Integration

**Purpose:** Wrap the Python recommendation pipeline into a robust web server.

**Input:**
- API requests from the frontend containing user preferences.

**Process:**
- Expose a REST API endpoint (e.g., `POST /api/recommend`).
- Receive user input and orchestrate Phase 3 (Normalization), Phase 4 (Filtering), and Phase 5 (LLM Ranking).
- Format the final ranked candidates into a structured JSON response.

**Output:**
- JSON payload containing the top-ranked restaurants and AI-generated explanations.

**Core Components:**
- Web Server Framework (e.g., FastAPI)
- Endpoint Routing & Validation
- Pipeline Orchestrator

---

## Phase 7: Frontend Web Application and Feedback Loop

**Purpose:** Provide a dynamic, visually stunning UI for users to interact with the system.

**Input:**
- Ranked recommendations from the Backend API (Phase 6).

**Process:**
- Capture user preferences via a modern input form.
- Show dynamic loading states while the backend processes the request.
- Present recommendations in a user-friendly view, displaying:
  - Restaurant name, cuisine, rating, estimated cost
  - AI-generated explanation
- Collect optional user feedback (liked/skipped/saved).

**Output:**
- Final recommendations beautifully displayed to the user.
- Feedback data sent to the backend for future improvement.

**Core Components:**
- Frontend Framework (e.g., Next.js, Vite + React, or Vanilla JS/HTML/CSS)
- UI Components (Input Forms, Loading Skeletons, Result Cards)
- Backend API Client

---

## Phase 8: Deployment using Streamlit

**Purpose:** Provide an alternative, simplified free deployment option using Streamlit Community Cloud for demonstrating the end-to-end AI pipeline.

**Input:**
- The entire project repository (including Phase 1-5 logic) hosted on GitHub.

**Process:**
- Wrap the core recommendation logic (Phases 3, 4, 5) into a single Streamlit script.
- Build UI components native to Streamlit (text inputs, sliders, select boxes) to gather user preferences.
- Connect the GitHub repository to Streamlit Community Cloud for automatic, free hosting.

**Output:**
- A live, publicly accessible web application.

**Core Components:**
- Streamlit UI (`app.py`)
- Streamlit Community Cloud connection
- `requirements.txt` for dependency management

## End-to-End Data Flow

`Dataset Ingestion -> Preprocessing -> Frontend User Input -> Backend API (Candidate Filtering & LLM Ranking) -> Frontend Recommendation Display -> User Feedback`
