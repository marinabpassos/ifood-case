# Quickstart: Validate Observability da Pipeline

Validates the 3 Independent Tests from spec.md. Re-running bronze MUST
happen before re-running silver (silver reads from bronze) — same
ordering constraint that has always existed between these two
pipelines, unrelated to this feature.

## Prerequisites

- Features 004 (bronze) and 006 (silver) complete and merged, both
  scripts extended per this feature's tasks.
- Databricks CLI authenticated against the `DEFAULT` profile.

## Step 1 — Re-run bronze, then silver (User Story 1 / FR-002, FR-006)

```
databricks workspace import /Workspace/Users/<you>/ifood_case/ingest_bronze \
  --file src/bronze/ingest_bronze.py --language PYTHON --format SOURCE --overwrite
databricks jobs submit --json '{"tasks":[{"task_key":"ingest_bronze","notebook_task":{"notebook_path":"/Workspace/Users/<you>/ifood_case/ingest_bronze"}}]}' --timeout 10m
databricks jobs get-run-output <run-id>

databricks workspace import /Workspace/Users/<you>/ifood_case/build_silver \
  --file src/silver/build_silver.py --language PYTHON --format SOURCE --overwrite
databricks jobs submit --json '{"tasks":[{"task_key":"build_silver","notebook_task":{"notebook_path":"/Workspace/Users/<you>/ifood_case/build_silver"}}]}' --timeout 10m
databricks jobs get-run-output <run-id>
```

**Expected outcome**: Both runs complete; each script's own JSON output
matches feature 004's `ingestion-log.md` / feature 006's `dq-run-log.md`
exactly (idempotent — SC-004).

## Step 2 — Query the run log (User Story 1 / SC-001)

```sql
SELECT pipeline_stage, executed_at, status, rows_read, rows_written,
       schema_check_status, duration_seconds, metrics, alerts
FROM ifood_case.silver._pipeline_run_log
ORDER BY executed_at;
```

**Expected outcome**: At least 2 rows (one `bronze`, one `silver`), all
core fields populated, no nulls in `status`/`rows_read`/`rows_written`
for a successful run.

## Step 3 — Confirm the real alert fired (User Story 2 / SC-002)

```sql
SELECT pipeline_stage, alerts FROM ifood_case.silver._pipeline_run_log
WHERE pipeline_stage = 'silver' ORDER BY executed_at DESC LIMIT 1;
```

**Expected outcome**: `alerts` contains exactly one entry, for
`passenger_count_null_or_zero` (~4.34% > 1%). The equivalent `bronze`
row's `alerts` is an empty array (0 duplicates, no rule exceeds 1%).

## Step 4 — Verify lineage via both native mechanisms (User Story 3 / SC-003)

```sql
-- Table-to-table half: bronze -> silver
SELECT DISTINCT source_table_full_name, target_table_full_name
FROM system.access.table_lineage
WHERE target_table_full_name = 'ifood_case.silver.yellow_taxi_trips';
```

**Expected outcome**: One row showing
`ifood_case.bronze.yellow_taxi_trips` as the source.

For the volume-to-table half (landing → bronze), open Catalog Explorer
→ `ifood_case.bronze.yellow_taxi_trips` → **Lineage** tab and confirm
`ifood_case.landing.yellow_taxi_raw` appears as an upstream source
(research.md §5 — `system.access.table_lineage` only tracks
table-to-table edges, so this half is UI-only by platform design, not a
gap in this feature).

## Done when

- [ ] Step 1: both re-runs succeed with numbers matching features 004/006
- [ ] Step 2: `_pipeline_run_log` has ≥2 rows, all core fields populated
- [ ] Step 3: the silver run's `alerts` contains the
      `passenger_count_null_or_zero` entry; bronze's is empty
- [ ] Step 4: `table_lineage` confirms bronze→silver; Catalog Explorer
      confirms landing→bronze
- [ ] No change to bronze's or silver's data-quality rules, schema, or
      table content anywhere in this feature (FR-007)
