# Bronze Ingestion Run Log

Structure per `data-model.md` ("Bronze Ingestion Run"). Produced by
`src/bronze/ingest_bronze.py`, run via `databricks jobs submit` on
serverless compute, 2026-07-23. Source: `ifood_case.landing.yellow_taxi_raw`
(moved from `ifood_case.bronze.yellow_taxi_raw` by
`src/bronze/rename_landing_schema.py`, same run date).

## Run Result

| Field | Value |
|---|---|
| `rows_read` | 16,186,386 |
| `rows_written` | 16,186,386 |
| `duplicates_removed` | 0 |
| `schema_validation_status` | pass |
| `executed_at` | 2026-07-23T14:09:41Z |

`rows_read` matches feature 003 profiling's documented total exactly
(`specs/003-data-profiling/findings.md` §2: 16,186,386 across the 5
months). `duplicates_removed = 0` matches feature 003's finding of 0
full-row duplicates in every month (§6). No unexplained row loss (SC-003).

## Attempts

Two failed attempts preceded the successful run, both fixed in code
(`src/bronze/ingest_bronze.py`) before the third attempt, not worked
around at the job level:

1. **`UC_COMMAND_NOT_SUPPORTED.WITH_RECOMMENDATION`** — `input_file_name()`
   is not supported on this workspace's Unity Catalog-governed serverless
   compute. Fixed by switching `_source_file` to the hidden
   `_metadata.file_name` column (research.md §4, updated after this
   finding).
2. **`SCHEMA_NOT_FOUND`** — `ifood_case.bronze` didn't exist at write
   time, because `rename_landing_schema.py` (User Story 1) correctly
   dropped it as the *old* landing-zone schema, and nothing recreated it
   as the *new* bronze-table schema. Fixed by adding
   `CREATE SCHEMA IF NOT EXISTS ifood_case.bronze` immediately before the
   table write in `dedup_and_write`.

## SC-004 Guardrail Verification (User Story 4)

Queried directly against `ifood_case.bronze.yellow_taxi_trips` after the
successful run:

| Condition | Bronze count | Feature 003 baseline (sum across 5 months) | Match |
|---|---|---|---|
| `total_amount <= 0` | 144,146 | 144,146 | Exact |
| `passenger_count` null or zero | 702,146 | 702,146 | Exact |
| Out-of-range dates (outside Jan 1 - May 31, 2023) | 1,077 | 1,077 | Exact |
| `tpep_dropoff_datetime < tpep_pickup_datetime` | 795 | *(none — first measurement, analyze finding D1)* | N/A |

The first three conditions match feature 003's profiling baseline
exactly, confirming bronze applied no business-rule filtering (FR-006,
SC-004). The fourth (`dropoff` before `pickup`) has no feature 003
baseline to compare against — this run is this pipeline's first-ever
measurement of that condition (795 rows across all 5 months combined).
This number should be carried forward as the new baseline for feature
006's data-quality rule on this condition.

## Schema Verification (SC-002)

`DESCRIBE TABLE ifood_case.bronze.yellow_taxi_trips` confirms 21 columns:
the 19 source columns (with `passenger_count` and `RatecodeID` both
`int`, resolving the float/integer drift from feature 003) plus
`_source_file` (`string`) and `_ingested_at` (`timestamp`) — matching
`contracts/bronze-schema.md`.

## Landing Zone Move (User Story 1)

`rename_landing_schema.py` ran successfully on the first attempt:
`ifood_case.bronze.yellow_taxi_raw` (feature 002) moved to
`ifood_case.landing.yellow_taxi_raw`, all 5 files verified byte-for-byte
identical to feature 002's recorded sizes, old `ifood_case.bronze` schema
dropped only after verification passed (SC-001). Independently
re-confirmed via `databricks schemas list ifood_case` (no `bronze` schema
present until `ingest_bronze.py` recreated it for the table) and
`databricks fs ls` on the new volume path.
