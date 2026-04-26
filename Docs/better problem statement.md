# Phase-Wise Architecture: AI-Powered Restaurant Recommendation System

## Problem Context

This system provides personalized restaurant recommendations (Zomato use case) by combining structured restaurant data with a Large Language Model (LLM). The goal is to return relevant, explainable, and user-friendly suggestions based on user preferences.

## High-Level Objective

Build an application that:

- Accepts user preferences (location, budget, cuisine, minimum rating, additional needs).
- Uses a real-world restaurant dataset.
- Applies filtering and LLM reasoning to rank restaurants.
- Displays recommendations with clear explanations.

## Phase-Wise Architecture

### Phase 1: Data Acquisition and Storage

**Purpose:** Collect and store restaurant data for recommendation processing.

**Input:**
- Zomato dataset from Hugging Face: [Dataset Link](https://huggingface.co/datasets/ManikaSaini/zomato-restaurant-recommendation)

**Process:**
- Load raw dataset.
- Store source data in a staging layer for repeatable preprocessing.

**Output:**
- Raw dataset available in local/database storage.

**Core Components:**
- Data loader
- Staging storage

---

### Phase 2: Data Preprocessing and Feature Preparation

**Purpose:** Clean and standardize restaurant records for accurate filtering and ranking.

**Input:**
- Raw restaurant dataset from Phase 1

**Process:**
- Handle missing/null values.
- Standardize location, cuisine, cost, and rating fields.
- Extract key attributes: name, location, cuisines, average cost, rating, tags.

**Output:**
- Cleaned and structured restaurant dataset.

**Core Components:**
- Data cleaning pipeline
- Feature extraction module

---

### Phase 3: Preference Collection and Query Understanding

**Purpose:** Capture user intent in structured form.

**Input:**
- User preferences from UI/API:
  - Location (e.g., Delhi, Bangalore)
  - Budget (low, medium, high)
  - Cuisine preference (e.g., Italian, Chinese)
  - Minimum rating
  - Optional preferences (e.g., family-friendly, quick service)

**Process:**
- Validate input values.
- Convert user input into a normalized query object.

**Output:**
- Structured user preference profile.

**Core Components:**
- Input form/API handler
- Query normalization module

---

### Phase 4: Candidate Retrieval and Rule-Based Filtering

**Purpose:** Narrow down restaurants that satisfy hard constraints.

**Input:**
- Structured user preference profile (Phase 3)
- Cleaned restaurant dataset (Phase 2)

**Process:**
- Filter by location, budget range, cuisine match, and minimum rating.
- Select top candidate set for LLM reasoning.

**Output:**
- Filtered candidate restaurants.

**Core Components:**
- Filtering engine
- Ranking pre-selector

---

### Phase 5: LLM-Powered Ranking and Explanation Generation

**Purpose:** Rank candidates intelligently and explain recommendation relevance.

**Input:**
- Filtered candidate list (Phase 4)
- Structured prompt template

**Process:**
- Convert candidate data to a prompt-friendly format.
- Ask LLM to:
  - Rank the best matches
  - Generate concise reasons for each recommendation
  - Optionally summarize overall choices

**Output:**
- Ranked recommendations with AI-generated explanations.

**Core Components:**
- Prompt builder
- LLM inference layer
- Response parser

---

### Phase 6: Result Presentation and Feedback Loop

**Purpose:** Present recommendations clearly and improve future performance.

**Input:**
- LLM-ranked recommendation output (Phase 5)

**Process:**
- Display user-friendly recommendation cards/results.
- Show key fields:
  - Restaurant name
  - Cuisine
  - Rating
  - Estimated cost
  - AI explanation
- Capture optional user feedback (liked/skipped/saved).

**Output:**
- Final recommendations shown to user.
- Feedback data for iterative improvement.

**Core Components:**
- Frontend/UI renderer
- Feedback collector

## End-to-End Data Flow

`Dataset Ingestion -> Preprocessing -> User Preference Capture -> Candidate Filtering -> LLM Ranking & Explanation -> Recommendation Display`
