# Detailed Edge Cases: AI-Powered Restaurant Recommendation System

This document lists detailed edge cases based on:
- `Docs/Problem Statement.md`
- `Docs/Phase Wise Architecture.md`

Each edge case includes a condition, risk, and expected handling behavior.

## Phase 1: Data Acquisition and Storage

### 1.1 Source Unavailable
- **Condition:** Hugging Face dataset URL is temporarily down or rate-limited.
- **Risk:** Data ingestion fails; no recommendations possible.
- **Expected Handling:** Retry with exponential backoff, log failure reason, use last successful snapshot if available, show system status as degraded.

### 1.2 Schema Drift in Dataset
- **Condition:** Dataset columns are renamed (e.g., `avg_cost` becomes `average_cost_for_two`).
- **Risk:** Pipeline breaks during extraction.
- **Expected Handling:** Validate schema before ingestion; maintain a schema mapping layer with fallback aliases.

### 1.3 Partial Download / Corrupt File
- **Condition:** Download interrupted or file checksum mismatch.
- **Risk:** Invalid records enter preprocessing.
- **Expected Handling:** Verify row count/checksum, reject corrupted file, re-download from source.

### 1.4 Duplicate Data Pull
- **Condition:** Same ingestion job runs twice.
- **Risk:** Duplicate restaurants in storage and repeated recommendations.
- **Expected Handling:** Use idempotent ingestion with primary keys and upsert logic.

### 1.5 Missing Unique Restaurant ID
- **Condition:** Dataset has no stable unique identifier.
- **Risk:** Deduplication becomes unreliable.
- **Expected Handling:** Generate composite key (name + location + address), run fuzzy dedup with thresholds.

### 1.6 Unsupported Encoding
- **Condition:** Dataset includes non-UTF characters.
- **Risk:** Parse errors or garbled text in outputs.
- **Expected Handling:** Normalize encoding to UTF-8 and replace invalid bytes safely.

## Phase 2: Data Preprocessing and Feature Preparation

### 2.1 Missing Critical Fields
- **Condition:** Restaurant has missing location, cuisine, or rating.
- **Risk:** Bad candidate selection.
- **Expected Handling:** Drop records missing mandatory fields; impute non-critical fields with defaults.

### 2.2 Inconsistent Location Names
- **Condition:** Same city appears as `Bengaluru`, `Bangalore`, `B'lore`.
- **Risk:** Relevant restaurants excluded during filtering.
- **Expected Handling:** Build normalization dictionary and canonical city mapping.

### 2.3 Cost in Mixed Formats
- **Condition:** Cost appears as `500`, `₹500 for two`, `500-700`.
- **Risk:** Budget filters fail.
- **Expected Handling:** Parse to normalized numeric range and store currency separately.

### 2.4 Rating Scale Mismatch
- **Condition:** Ratings include `4.3/5`, `86%`, `NEW`, `-`.
- **Risk:** Incorrect ranking and filtering.
- **Expected Handling:** Standardize to a single numeric scale; map `NEW` or unavailable values to null and handle explicitly.

### 2.5 Multi-Cuisine Formatting Noise
- **Condition:** `Italian,Chinese`, `Italian / Chinese`, `itln`.
- **Risk:** Cuisine matching misses valid options.
- **Expected Handling:** Tokenize by multiple separators, lowercase and normalize aliases.

### 2.6 Outlier Values
- **Condition:** Cost = 999999 or rating = 9.5.
- **Risk:** Skewed ranking.
- **Expected Handling:** Enforce sanity bounds; quarantine suspicious records for review.

### 2.7 Restaurant Permanently Closed
- **Condition:** Dataset includes stale entries.
- **Risk:** Recommending unavailable restaurants.
- **Expected Handling:** Maintain `status` field where possible; deprioritize or exclude inactive entries.

## Phase 3: Preference Collection and Query Understanding

### 3.1 Empty Input Submission
- **Condition:** User submits with no filters.
- **Risk:** Over-broad result set.
- **Expected Handling:** Ask for at least location; otherwise show popular restaurants by city default.

### 3.2 Ambiguous Location
- **Condition:** User enters `MG Road`.
- **Risk:** Wrong city inferred.
- **Expected Handling:** Prompt user to select city/state disambiguation.

### 3.3 Typo in Cuisine
- **Condition:** `Itallian`, `Chines`.
- **Risk:** No match returned.
- **Expected Handling:** Apply fuzzy matching and suggest nearest cuisine options.

### 3.4 Budget Outside Supported Range
- **Condition:** User gives negative value or unrealistic high amount.
- **Risk:** Filter returns empty or nonsense results.
- **Expected Handling:** Validate input range and prompt correction.

### 3.5 Conflicting Constraints
- **Condition:** Low budget + fine dining + rating >= 4.8 in low-density area.
- **Risk:** No results.
- **Expected Handling:** Return nearest alternatives with explicit constraint-relaxation explanation.

### 3.6 Non-English / Mixed-Language Input
- **Condition:** User asks in Hindi-English mix.
- **Risk:** Intent parser misses fields.
- **Expected Handling:** Use multilingual normalization or fallback translation before parsing.

### 3.7 Unsafe Prompt Text in Preferences
- **Condition:** User enters malicious text (prompt injection) in additional preferences.
- **Risk:** LLM behavior manipulation.
- **Expected Handling:** Sanitize free-text input, strip instruction-like patterns, separate data from system prompt.

## Phase 4: Candidate Retrieval and Rule-Based Filtering

### 4.1 Zero Candidates After Strict Filtering
- **Condition:** No restaurant meets all hard constraints.
- **Risk:** Empty recommendation response.
- **Expected Handling:** Progressive relaxation strategy (rating, then budget band, then cuisine similarity) with transparent message.

### 4.2 Too Many Candidates
- **Condition:** Broad query returns thousands of candidates.
- **Risk:** High latency and token overflow for LLM.
- **Expected Handling:** Pre-rank with deterministic scoring; pass top-N only to LLM.

### 4.3 Duplicate Candidates in Final Pool
- **Condition:** Same restaurant appears multiple times from near-duplicate rows.
- **Risk:** Repeated recommendations.
- **Expected Handling:** Deduplicate by canonical restaurant key before LLM stage.

### 4.4 Hard Filter Bias
- **Condition:** New restaurants with low review count are excluded by rating threshold.
- **Risk:** Reduced discovery and unfair results.
- **Expected Handling:** Add confidence-aware scoring and optional exploration quota.

### 4.5 Distance Not Considered
- **Condition:** City-level filter includes far-away neighborhoods.
- **Risk:** Poor practical relevance.
- **Expected Handling:** If geodata exists, include proximity filter or zone-based weighting.

### 4.6 Time-Sensitive Constraints Ignored
- **Condition:** User needs late-night dining; dataset lacks operating hours.
- **Risk:** Unusable recommendations.
- **Expected Handling:** Mark uncertainty and avoid claiming open/closed status without reliable data.

## Phase 5: LLM-Powered Ranking and Explanation Generation

### 5.1 Prompt Token Overflow
- **Condition:** Candidate context exceeds model token limit.
- **Risk:** Truncated prompts or failed requests.
- **Expected Handling:** Compact candidate format and cap input to top-N candidates.

### 5.2 Hallucinated Attributes
- **Condition:** LLM adds details not present in dataset (e.g., live music).
- **Risk:** User trust loss.
- **Expected Handling:** Instruct model to use only provided fields; post-validate response against source data.

### 5.3 Inconsistent Ranking Logic
- **Condition:** Lower-rated/high-cost options ranked above better matches without rationale.
- **Risk:** Perceived poor quality.
- **Expected Handling:** Add ranking rubric in prompt and deterministic tie-breakers.

### 5.4 Biased or Unsafe Language
- **Condition:** Output includes culturally insensitive or subjective assumptions.
- **Risk:** Ethical and reputational risk.
- **Expected Handling:** Apply moderation/safety filters and regenerate with stricter prompt.

### 5.5 Non-Deterministic Output Drift
- **Condition:** Same input gives significantly different rankings frequently.
- **Risk:** Inconsistent UX.
- **Expected Handling:** Lower temperature for ranking tasks and cache responses per normalized query.

### 5.6 API Timeout / Rate Limit
- **Condition:** LLM provider latency spike or quota exceeded.
- **Risk:** Recommendation request fails.
- **Expected Handling:** Retry with backoff; fallback to rule-based ranking without explanation.

### 5.7 Malformed LLM Output
- **Condition:** Response is not parseable into expected JSON/structure.
- **Risk:** Frontend render failure.
- **Expected Handling:** Enforce structured output schema; retry once with repair prompt.

### 5.8 Prompt Injection via Data Fields
- **Condition:** Restaurant text contains malicious instructions (e.g., in reviews/tags).
- **Risk:** Model follows untrusted instructions.
- **Expected Handling:** Escape untrusted text and isolate it as quoted data only.

## Phase 6: Result Presentation and Feedback Loop

### 6.1 Missing Display Fields
- **Condition:** A recommended restaurant has null cost or rating.
- **Risk:** Broken or confusing UI.
- **Expected Handling:** Display fallback labels like `Not available` and keep card layout stable.

### 6.2 Duplicate Cards in UI
- **Condition:** Same restaurant rendered twice due to frontend state merge bug.
- **Risk:** Poor user experience.
- **Expected Handling:** Deduplicate on client using unique key before render.

### 6.3 Sort Order Mismatch
- **Condition:** Backend returns ranked list, frontend re-sorts unintentionally.
- **Risk:** Incorrect final ordering.
- **Expected Handling:** Preserve backend rank index and lock client sort by that field.

### 6.4 Explanation Too Long
- **Condition:** LLM explanation exceeds card size.
- **Risk:** Visual clutter and poor readability.
- **Expected Handling:** Limit explanation length server-side; show `Read more` option if needed.

### 6.5 Feedback Spam / Abuse
- **Condition:** Same user sends repeated likes/dislikes rapidly.
- **Risk:** Skewed feedback analytics.
- **Expected Handling:** Throttle feedback events and enforce user/session-level deduplication windows.

### 6.6 Feedback Without Recommendation Context
- **Condition:** Feedback event missing recommendation/session ID.
- **Risk:** Unusable training signal.
- **Expected Handling:** Reject orphan feedback and log telemetry error.

### 6.7 Privacy Leakage in Logs
- **Condition:** Raw user preferences logged with personal identifiers.
- **Risk:** Privacy and compliance concerns.
- **Expected Handling:** Mask PII, minimize logs, retain only required analytics fields.

## Cross-Cutting Edge Cases

### C1. End-to-End Latency Spike
- **Condition:** Slow preprocessing + LLM latency.
- **Risk:** User drop-off.
- **Expected Handling:** Async pipeline, cached popular queries, and progressive loading states.

### C2. Observability Gaps
- **Condition:** Failures occur but no phase-level metrics exist.
- **Risk:** Hard to debug production issues.
- **Expected Handling:** Add metrics per phase (ingestion success, filter counts, LLM error rate, response time).

### C3. Version Incompatibility
- **Condition:** Prompt version, parser version, and schema version drift apart.
- **Risk:** Silent failures or bad results.
- **Expected Handling:** Version all artifacts and validate compatibility at runtime.

### C4. Regional/Currency Expansion
- **Condition:** New city/country added with different currency and cuisine taxonomy.
- **Risk:** Budget and cuisine filters break.
- **Expected Handling:** Locale-aware normalization and pluggable taxonomy mappings.

### C5. Cold Start for New City
- **Condition:** Very few restaurants available for selected city.
- **Risk:** Weak recommendations.
- **Expected Handling:** Expand search radius and clearly mark limited-data recommendations.

## Suggested Test Strategy Mapping

- **Unit tests:** schema mapping, normalization, filter logic, dedup, parser validity.
- **Integration tests:** ingestion -> preprocessing -> filtering -> LLM -> presentation pipeline.
- **Resilience tests:** provider timeout, malformed LLM output, dataset schema drift.
- **UX tests:** empty-state handling, relaxed constraint messaging, explanation readability.
- **Security tests:** prompt injection attempts from user input and dataset fields.
