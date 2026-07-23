# Phase 1 Data Model: Observability da Pipeline

One new entity — the log row itself. No changes to any existing entity
from features 002-006 (bronze/silver table content and schema are
untouched, per spec FR-007).

## Pipeline Run Log Entry

Grain: one row per (pipeline stage, execution). Lives in
`ifood_case.silver._pipeline_run_log` — **append-only**, the one
deliberate exception to this project's overwrite convention (plan.md
Complexity Tracking).

| Field | Type | Notes |
|---|---|---|
| `pipeline_stage` | string | `"bronze"` or `"silver"` |
| `executed_at` | timestamp | Captured once at the start of the script's `__main__` block |
| `status` | string | `"pass"` / `"failed"` — taken directly from the script's own existing result dict (feature 004's `schema_validation_status`, feature 006's `schema_assertion_status`), not a new status concept |
| `rows_read` | long, nullable | From the script's own result dict; null if the run failed before this was computed |
| `rows_written` | long, nullable | Same |
| `schema_check_status` | string, nullable | Mirrors `status` for the schema-assertion step specifically (kept distinct in case a future stage separates "ran successfully" from "schema was fine" — not the case today, both scripts fail together on schema mismatch) |
| `duration_seconds` | double | Wall-clock time from the start of `__main__` to the point logging happens |
| `metrics` | string (JSON) | Stage-specific: bronze → `{"duplicates_removed": int}`; silver → `{"total_amount_negative_or_zero_count": int, "passenger_count_null_or_zero_count": int, "dropoff_before_pickup_count": int, "out_of_range_dates_count": int, "total_dropped": int}` (research.md §1) |
| `alerts` | array\<string\> | One entry per rule/check exceeding the 1% threshold (research.md §4); empty array if none |

**Validation rules**:
- Every run of `ingest_bronze.py` or `build_silver.py` appends exactly
  one row, whether it succeeds or fails (FR-002, FR-003).
- `status`/`schema_check_status` are never left null on a completed run
  — at minimum they reflect the anticipated-failure or success path
  already established in features 004/006 (research.md §3).
- `alerts` is deterministic from `metrics` and `rows_read`: any named
  count whose `count / rows_read > 0.01` produces exactly one entry, no
  more, no fewer (research.md §4).

**Relationships**: Each row correlates to exactly one Databricks job
run (traceable via `system.access.table_lineage`'s `entity_run_id`/
`entity_metadata.job_info`, research.md §5, if cross-referencing is ever
needed) — not modeled as a foreign key in the table itself, since this
project has no separate "job run" entity to reference.

## Existing entities (unchanged)

- **Bronze Trip Record** (feature 004), **Silver Trip Record** (feature
  006): no field, type, or content change — this feature only reads
  their already-computed row counts and rule counts for logging.
- **Silver Data Contract** (feature 005): untouched (spec FR-007 /
  Constitution Principle II — this feature has no data contract of its
  own, since `_pipeline_run_log` is operational, not consumption-layer
  business data).
