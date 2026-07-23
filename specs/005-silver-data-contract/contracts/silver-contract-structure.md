# Interface Contract: Silver Contract YAML Structure

This fixes what `contracts/nyc_taxi_silver.yaml` (the repository-root
deliverable) MUST contain. It's the structure this feature's own
validator (`src/contracts/validate_silver_contract.py`) checks against,
and what feature 006 can rely on without re-deriving expectations from
the spec. Same role `profiling-findings-schema.md` played for feature
003's `findings.md`, and `bronze-schema.md` for feature 004's table.

## Required top-level keys, all mandatory

### 1. `contract`

- `name`: string, fixed value `nyc_taxi_silver`.
- `version`: string, matching the current value in `versioning.current_version` below.

### 2. `table`

- `catalog`: `ifood_case`.
- `schema`: `silver`.
- `name`: `yellow_taxi_trips`.
- `owner`: non-empty string.

### 3. `grain`

- `statement`: non-empty string — MUST state "one row = one trip event"
  in substance.
- `uniqueness_note`: non-empty string — MUST explicitly state that no
  formal uniqueness constraint is enforced on the 6-column schema alone.

### 4. `columns`

- A list of **exactly 6** entries, each with:
  - `name`: one of `VendorID`, `passenger_count`, `total_amount`,
    `tpep_pickup_datetime`, `tpep_dropoff_datetime`, `_silver_processed_at`
    — all 6 MUST appear, no more, no fewer.
  - `type`: non-empty string (business-level type, e.g. `integer`,
    `decimal`, `timestamp` — not a Spark type).
  - `nullable`: boolean.
  - `description`: non-empty string (one-line business description).

### 5. `quality_rules`

- A list of **exactly 5** entries, one per constitution-named risk:
  `total_amount_negative_or_zero`, `passenger_count_null_or_zero`,
  `dropoff_before_pickup`, `out_of_range_dates`, `duplicates`. Each
  entry has:
  - `id`: one of the 5 names above.
  - `policy`: `drop` (4 of the 5 entries) or `resolved_upstream` (the
    `duplicates` entry only).
  - `counting`: `independent` for all 4 `drop` entries (2026-07-23
    clarification) — omitted for `resolved_upstream`.
  - `rationale`: non-empty string.
- A sibling key, `total_dropped_metric_note`: non-empty string, stating
  that "total rows dropped" is a separate, non-overlapping metric
  distinct from the 4 independent per-rule counts (research.md §5).

### 6. `sla`

- `frequency`: non-empty string (e.g. `monthly`, illustrative).
- `latency_target`: non-empty string.
- `note`: non-empty string, MUST state that this project's actual load is
  one-time (Jan-May 2023), and the frequency above is illustrative.

### 7. `versioning`

- `current_version`: string matching pattern `v` + integer (e.g. `v1`).
- `breaking_change_policy`: object with `major`, `minor`, `patch` keys,
  each a non-empty string describing what kind of change falls in that
  category.

## Guarantees this feature provides to consumers

1. `contracts/nyc_taxi_silver.yaml` has all 7 top-level keys above, with
   the exact list-length constraints on `columns` (6) and `quality_rules`
   (5) — checkable by `validate_silver_contract.py` without connecting to
   Databricks.
2. Every column's nullability reflects the **post-cleaning** invariant
   (what silver guarantees once feature 006 applies the rules above),
   not bronze's raw shape (research.md §3).
3. The independent-per-rule-counting decision and the separate
   total-dropped metric are both present in the contract's own content,
   not only in the spec's clarification log (research.md §5).

## Non-guarantees (explicitly out of scope here)

- No validation against real data — this only checks the YAML's own
  shape. Asserting real rows conform is feature 006's job.
- No Spark-specific type mapping — that translation happens during
  feature 006's implementation.
