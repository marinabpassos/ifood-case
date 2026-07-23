# Quickstart: Validate Data Quality & Camada Silver

Validates the 3 Independent Tests from spec.md. All 3 user stories
converge in a single script run — verification happens by inspecting the
run's own report plus the written table.

## Prerequisites

- Feature 004 complete: `ifood_case.bronze.yellow_taxi_trips` exists,
  16,186,386 rows (`specs/004-bronze-layer/ingestion-log.md`).
- Feature 005 complete: `contracts/nyc_taxi_silver.yaml` exists and
  passes `python src/contracts/validate_silver_contract.py`.
- Databricks CLI authenticated against the `DEFAULT` profile.

## Step 1 — Run the silver build (User Stories 1-3 / FR-001 through FR-008)

Upload and run `src/silver/build_silver.py` as a job on serverless
compute:

```
databricks workspace import /Workspace/Users/<you>/ifood_case/build_silver \
  --file src/silver/build_silver.py --language PYTHON --format SOURCE --overwrite
databricks jobs submit --json '{"tasks":[{"task_key":"build_silver","notebook_task":{"notebook_path":"/Workspace/Users/<you>/ifood_case/build_silver"}}]}' --timeout 10m
databricks jobs get-run-output <run-id>
```

**Expected outcome**: A JSON result with `rows_read`, `rows_written`,
the 4 named per-rule counts, `total_dropped`, and
`schema_assertion_status` (data-model.md, "Silver Data Quality Run").

## Step 2 — Verify no invalid rows reached silver (User Story 1 / SC-001)

```sql
SELECT count(*) FROM ifood_case.silver.yellow_taxi_trips WHERE total_amount <= 0;
SELECT count(*) FROM ifood_case.silver.yellow_taxi_trips WHERE passenger_count IS NULL OR passenger_count = 0;
SELECT count(*) FROM ifood_case.silver.yellow_taxi_trips WHERE tpep_dropoff_datetime < tpep_pickup_datetime;
SELECT count(*) FROM ifood_case.silver.yellow_taxi_trips
  WHERE tpep_pickup_datetime < '2023-01-01' OR tpep_dropoff_datetime >= '2023-06-01';
```

**Expected outcome**: All 4 queries return `0`.

## Step 3 — Verify the schema matches the contract (User Story 2 / SC-002)

```sql
DESCRIBE TABLE ifood_case.silver.yellow_taxi_trips;
```

**Expected outcome**: Exactly 6 columns —
`VendorID`, `passenger_count`, `total_amount`, `tpep_pickup_datetime`,
`tpep_dropoff_datetime`, `_silver_processed_at` — matching
`contracts/nyc_taxi_silver.yaml`'s `columns` list, no bronze passthrough
or bronze metadata column present.

## Step 4 — Verify per-rule counts match feature 004's bronze-layer numbers exactly (User Story 3 / SC-003)

Compare Step 1's JSON output against feature 004's
`ingestion-log.md`:

| Rule | Step 1 output | Feature 004 baseline |
|---|---|---|
| `total_amount_negative_or_zero_count` | — | 144,146 |
| `passenger_count_null_or_zero_count` | — | 702,146 |
| `dropoff_before_pickup_count` | — | 795 |
| `out_of_range_dates_count` | — | 1,077 |

**Expected outcome**: Each row matches exactly. `total_dropped` is
reported separately and falls between 702,146 (the largest single
count) and 848,164 (the sum of all 4).

## Step 5 — Verify silver is analysis-ready as-is (User Story 1 / SC-004)

```sql
SELECT month(tpep_pickup_datetime) AS month, avg(total_amount) AS avg_total_amount
FROM ifood_case.silver.yellow_taxi_trips
GROUP BY 1 ORDER BY 1;
```

**Expected outcome**: Runs directly against `ifood_case.silver.yellow_taxi_trips`
with no `WHERE`/cleaning clause needed — proving the table is ready for
feature 008's analytical questions as-is.

## Done when

- [ ] Step 1 output reviewed — `schema_assertion_status: pass`, all
      counts present
- [ ] Step 2 queries all return 0
- [ ] Step 3 confirms exactly 6 columns matching the contract
- [ ] Step 4 confirms all 4 counts match feature 004's numbers exactly
- [ ] Step 5 confirms a direct aggregation query runs against silver
      with no extra cleaning clause
- [ ] `specs/006-silver-data-quality/dq-run-log.md` written from Step 1's
      output (research.md §6)
- [ ] `contracts/nyc_taxi_silver.yaml` has no diff from this feature's
      implementation (FR-008)
