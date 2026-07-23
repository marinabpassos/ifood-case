# Silver Data Quality Run Log

Structure per `data-model.md` ("Silver Data Quality Run"). Produced by
`src/silver/build_silver.py`, run via `databricks jobs submit` on
serverless compute, 2026-07-23. Source: `ifood_case.bronze.yellow_taxi_trips`
(feature 004). Contract: `contracts/nyc_taxi_silver.yaml` (feature 005),
uploaded alongside the script to
`/Workspace/Users/marinabpassos@gmail.com/ifood_case/nyc_taxi_silver.yaml`
as a plain workspace file (`databricks workspace import --format AUTO`)
so the runtime can load it directly (research.md decision 1 — the
contract drives the pipeline's behavior, not just documents it).

## Run Result

| Field | Value |
|---|---|
| `rows_read` | 16,186,386 |
| `rows_written` | 15,339,417 |
| `total_amount_negative_or_zero_count` | 144,146 |
| `passenger_count_null_or_zero_count` | 702,146 |
| `dropoff_before_pickup_count` | 795 |
| `out_of_range_dates_count` | 1,077 |
| `total_dropped` | 846,969 |
| `schema_assertion_status` | pass |
| `executed_at` | 2026-07-23T15:44:42Z |

Succeeded on the first run — no fixes needed during implementation.

## SC-003 Verification: independent counts match feature 004 exactly

| Rule | This run | Feature 004 baseline (`ingestion-log.md`) | Match |
|---|---|---|---|
| `total_amount_negative_or_zero` | 144,146 | 144,146 | Exact |
| `passenger_count_null_or_zero` | 702,146 | 702,146 | Exact |
| `dropoff_before_pickup` | 795 | 795 | Exact |
| `out_of_range_dates` | 1,077 | 1,077 | Exact |

All 4 independent counts reproduce bronze's own population counts
exactly, confirming the rules were evaluated against the full,
unfiltered bronze input (research.md decision 2) rather than a
sequentially-shrinking one.

`total_dropped` (846,969) falls between the largest single count
(702,146) and the sum of all 4 (848,164), as expected — the gap
(848,164 − 846,969 = 1,195) is the number of rows that failed more than
one rule simultaneously and were only counted once in `total_dropped`.
`rows_written` (15,339,417) = `rows_read` (16,186,386) − `total_dropped`
(846,969), exactly.

## SC-001 Verification: no invalid rows reached silver

```
total_amount <= 0                                        -> 0
passenger_count IS NULL OR passenger_count = 0            -> 0
tpep_dropoff_datetime < tpep_pickup_datetime               -> 0
out-of-range dates (outside Jan 1 - May 31, 2023)          -> 0
```

## SC-002 Verification: schema matches the contract exactly

`DESCRIBE TABLE ifood_case.silver.yellow_taxi_trips` returned exactly 6
columns: `VendorID` (bigint), `passenger_count` (int), `total_amount`
(double), `tpep_pickup_datetime`/`tpep_dropoff_datetime` (timestamp_ntz),
`_silver_processed_at` (timestamp) — matching
`contracts/nyc_taxi_silver.yaml`'s declared 6 columns, no bronze
passthrough or bronze metadata column present.

## SC-004 Verification: silver is analysis-ready as-is

A direct `GROUP BY` aggregation (average `total_amount` per month) ran
against `ifood_case.silver.yellow_taxi_trips` with no extra cleaning
clause:

| Month | Avg `total_amount` |
|---|---|
| 1 | 27.46 |
| 2 | 27.37 |
| 3 | 28.29 |
| 4 | 28.78 |
| 5 | 29.45 |

Values are consistent with feature 003's bronze-layer profiling means
(~27-29 per month), confirming the cleaning removed known defects
without distorting the overall distribution.

## FR-008 Verification: contract untouched

`git diff contracts/nyc_taxi_silver.yaml` is clean — this feature
implemented the already-decided contract from feature 005 without
modifying it.
