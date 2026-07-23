# Phase 1 Data Model: Data Quality & Camada Silver

Two entities, both already named in spec.md's Key Entities. Column-by
-column detail for the silver table itself is fixed entirely by
`contracts/nyc_taxi_silver.yaml` (feature 005) — not duplicated here.

## Silver Trip Record

Grain: one row per valid trip (per the contract's grain declaration),
spanning all 5 months, in `ifood_case.silver.yellow_taxi_trips`. Exactly
the 6 columns `contracts/nyc_taxi_silver.yaml` declares.

| Field | Notes |
|---|---|
| `VendorID`, `passenger_count`, `total_amount`, `tpep_pickup_datetime`, `tpep_dropoff_datetime` | Carried through from bronze unchanged in value, but only for rows passing all 4 drop rules. Types/nullability exactly as `contracts/nyc_taxi_silver.yaml` declares (research.md §3 maps contract business types to bronze's actual Spark types). |
| `_silver_processed_at` | New; single timestamp shared by every row from this run (research.md §5). |

**Validation rules** (all enforced by construction, not asserted
separately after the write):
- No row has `total_amount <= 0`.
- No row has `passenger_count` null or `0`.
- No row has `tpep_dropoff_datetime < tpep_pickup_datetime`.
- No row has a date outside Jan 1 - May 31, 2023.
- No full-row duplicate (inherited from bronze's own dedup, feature 004
  — not re-checked here, per the contract's `duplicates: resolved_upstream`
  policy).

**Relationships**: Every Silver Trip Record traces back to exactly one
Bronze Trip Record (feature 004) — a strict subset relationship (silver
rows are always a subset of bronze rows that passed all 4 rules). No
other relationships — still a single flat fact-shaped table, no star
schema.

## Silver Data Quality Run

This feature's own execution record — the evidence behind SC-001
through SC-003. Persisted as `specs/006-silver-data-quality/dq-run-log.md`
(research.md §6), not the durable `_pipeline_run_log` table (feature
007's scope).

| Field | Type | Notes |
|---|---|---|
| `rows_read` | integer | Rows read from `ifood_case.bronze.yellow_taxi_trips` |
| `rows_written` | integer | Rows actually written to `ifood_case.silver.yellow_taxi_trips` |
| `total_amount_negative_or_zero_count` | integer | Independent count (research.md §2); expected to equal feature 004's bronze-layer figure exactly (144,146) |
| `passenger_count_null_or_zero_count` | integer | Independent count; expected 702,146 |
| `dropoff_before_pickup_count` | integer | Independent count; expected 795 |
| `out_of_range_dates_count` | integer | Independent count; expected 1,077 |
| `total_dropped` | integer | Logical OR across the 4 rules above, no double-counting; `rows_read - rows_written` |
| `schema_assertion_status` | enum: `pass` \| `failed` | Result of the FR-002 pre-write schema-compatibility check |
| `executed_at` | timestamp | When the job ran |

**Completion condition**: `schema_assertion_status = pass` AND
`rows_written = rows_read - total_dropped` AND each of the 4 named
per-rule counts matches its feature-004 baseline exactly.
