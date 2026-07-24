# Phase 1 Data Model: POC App Chat — Consumo & Diferencial

No new table or schema — this feature is a read-only consumption app.
Both entities below are runtime/documentation-level records, not
physical data structures the app persists (the app itself is stateless
per spec FR-008 — no database, no Lakebase).

## NL-to-SQL Chat App

One instance: the deployed Databricks App itself.

| Field | Notes |
|---|---|
| `app_name` | Databricks Apps resource name (≤26 chars, lowercase/hyphens) |
| `chat_interface` | Gradio `ChatInterface` — receives a Portuguese natural-language question, returns a Portuguese formatted answer |
| `data_source` | `ifood_case.silver.yellow_taxi_trips` — the app's only table (FR-002) |
| `sql_warehouse` | The project's existing single 2X-Small SQL Warehouse (feature 002), wired via the `resources` array at `databricks apps create`/`update` time (research.md §4) — not a new warehouse |
| `serving_endpoint` | `databricks-meta-llama-3-1-8b-instruct` (swapped from `databricks-gpt-5-6-luna` during implementation — rate limit 0 on this workspace), wired the same way, used for NL→SQL generation (research.md §2) |

**Behavior per question** (FR-001, FR-002, FR-008):
1. Receive the question text (no prior-turn context — each question is independent).
2. Call the serving endpoint with the question + the silver table's schema (sourced from `contracts/nyc_taxi_silver.yaml`) as context; get back a single SQL `SELECT` statement.
3. Execute that statement against the SQL Warehouse (research.md §3).
4. Format the real result into a Portuguese-language answer and return it to the chat interface.

**Validation rules**:
- The generated SQL MUST target `ifood_case.silver.yellow_taxi_trips` only — never bronze, never landing, never another table (FR-002, FR-007).
- The app MUST NOT write to any table — `statement_execution` is used for `SELECT` only (FR-007).
- A failed/invalid generated query MUST NOT be silently retried into a hidden "corrected" version and presented as the first attempt (spec Edge Cases) — the app returns a graceful failure response for that turn instead of fabricating an answer.

**Relationships**: Reads from the same `ifood_case.silver.yellow_taxi_trips` (feature 006) every other consumption path in this project reads from. Runs on Databricks Apps' own compute, distinct from and non-conflicting with the project's SQL Warehouse (research.md §3).

## Example Interaction

One record per curated example question (spec SC-002: at least 3), captured from a real run against the actually-deployed app — not hand-authored or simulated.

| Field | Notes |
|---|---|
| `question` | The natural-language question text, in Portuguese, as typed into the chat interface |
| `generated_sql` | The exact SQL the app's backend produced for this question (research.md §2) |
| `executed_result` | The raw row(s) returned by `statement_execution.execute_statement()` |
| `formatted_answer` | The Portuguese-language answer the app actually returned in the chat UI |
| `captured_at` | Timestamp the example was run against the real deployed app |

**Validation rules**:
- Every field MUST come from one real, successful run against the deployed app (data-model's `NL-to-SQL Chat App` entity) — no field is invented or backfilled from what the app "should" produce (spec Edge Cases: a failing candidate question is dropped from the curated set, not faked into a passing one).
- At least 3 distinct `Example Interaction` records MUST exist (SC-002).
- The full set of records, saved together, MUST be clearly labeled as this feature's differentiator content (FR-006), distinct from the required deliverables of features 002-008.

**Relationships**: Each record is produced by one interaction with the `NL-to-SQL Chat App` entity above. The saved set (`src/app/examples.md`, research.md §6) is this feature's User Story 2 deliverable — reviewable without live Databricks access (SC-004).
