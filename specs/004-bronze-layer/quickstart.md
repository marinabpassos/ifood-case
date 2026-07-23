# Quickstart: Validate Camada Bronze

Validates the 4 Independent Tests from spec.md end-to-end. User Story 1
(schema-namespace move) MUST run first — User Story 2 reads from the
renamed location. User Stories 3-4 are checks against the same ingestion
run, not separate executions.

## Prerequisites

- Feature 002 complete and feature 003's findings available: all 5
  monthly files verified in `ifood_case.bronze.yellow_taxi_raw`
  (`specs/002-ambiente-landing-zone/`), full-schema comparison documented
  in `specs/003-data-profiling/findings.md`.
- Databricks CLI authenticated against the `DEFAULT` profile (same setup
  as features 002-003's quickstarts).

## Step 1 — Move the landing zone to its own schema (User Story 1 / FR-001)

Upload and run `src/bronze/rename_landing_schema.py` as a job on
serverless compute (same pattern as prior features):

```
databricks workspace import /Workspace/Users/<you>/ifood_case/rename_landing_schema \
  --file src/bronze/rename_landing_schema.py --language PYTHON --format SOURCE --overwrite
databricks jobs submit --json '{"tasks":[{"task_key":"rename_landing_schema","notebook_task":{"notebook_path":"/Workspace/Users/<you>/ifood_case/rename_landing_schema"}}]}' --timeout 5m
databricks jobs get-run-output <run-id>
```

**Expected outcome**: `ifood_case.landing.yellow_taxi_raw` lists all 5
files, each with the same size recorded in feature 002's landing table
(SC-001). The old `ifood_case.bronze` schema no longer exists (dropped
only after verification passes — research.md §1).

```
databricks volumes list ifood_case landing
```

## Step 2 — Ingest into the bronze Delta table (User Stories 2-4 / FR-002 through FR-008)

Upload and run `src/bronze/ingest_bronze.py` the same way. It asserts the
source schema against feature 003's documented baseline (FR-008), casts
`passenger_count`/`ratecodeid` to `IntegerType` (contracts/bronze-schema.md),
unions all 5 months, deduplicates on source columns, adds `_source_file`/
`_ingested_at`, and writes `ifood_case.bronze.yellow_taxi_trips`.

**Expected outcome**: A JSON result with `rows_read`, `rows_written`,
`duplicates_removed`, and `schema_validation_status` (data-model.md,
Bronze Ingestion Run).

## Step 3 — Verify the written table matches the contract

```sql
-- SC-002: one consistent schema
DESCRIBE TABLE ifood_case.bronze.yellow_taxi_trips;

-- SC-003: row count matches feature 003's total minus duplicates removed
SELECT count(*) FROM ifood_case.bronze.yellow_taxi_trips;
-- expected: 16186386 - duplicates_removed (0, per feature 003)

-- SC-004: known defects still present, unfiltered, at feature 003's rates
SELECT count(*) FROM ifood_case.bronze.yellow_taxi_trips WHERE total_amount <= 0;
SELECT count(*) FROM ifood_case.bronze.yellow_taxi_trips WHERE passenger_count IS NULL OR passenger_count = 0;
SELECT count(*) FROM ifood_case.bronze.yellow_taxi_trips
  WHERE tpep_pickup_datetime < '2023-01-01' OR tpep_dropoff_datetime >= '2023-06-01';
```

**Expected outcome**: Each count is consistent with the per-month rates
documented in `specs/003-data-profiling/findings.md` (e.g. negative/zero
`total_amount` totalling ~144,146 rows across all 5 months) — proving
bronze applied no business-rule filtering (User Story 4).

## Step 4 — Transcribe the run into `ingestion-log.md`

Write `specs/004-bronze-layer/ingestion-log.md` from Step 2's JSON output
(research.md §5) — same convention as feature 003's `findings.md`.

## Done when

- [ ] Step 1 output reviewed — landing zone moved, byte-identical, old
      `bronze`-named schema dropped only after verification
- [ ] Step 2 output reviewed — schema validation passed, row counts
      accounted for
- [ ] Step 3 queries confirm one consistent schema and unfiltered
      known-defect rates
- [ ] `ingestion-log.md` written
- [ ] No business data-quality rule was applied anywhere in this feature
      (FR-006) — only technical dedup
