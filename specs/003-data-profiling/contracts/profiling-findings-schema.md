# Interface Contract: Profiling Findings Schema

This is the structure `specs/003-data-profiling/findings.md` MUST follow.
It's the operational interface this feature exposes to feature 004 (data
contract) and feature 005 (data quality rules) — they read this file
rather than re-profiling the raw parquet files themselves.

## Required sections, in order

### 1. Schema Comparison

- A single statement: either "identical schema across all 5 months" or a
  table of `Schema Deviation` rows (data-model.md) — one row per column
  name, listing `months_present`, `type_family_by_month`, and `severity`
  (`critical`/`informational`).
- Deviations MUST be grouped or sorted so all `critical` rows are visible
  before `informational` rows — a reader designing the feature 004
  contract should never have to hunt for the required-column deviations.

### 2. Volumetry

- A table: one row per month, one column for `row_count`.

### 3. Completeness (Null Rates)

- A table: rows = the 5 required columns, columns = the 5 months, cells =
  null rate (count and percentage).

### 4. Descriptive Statistics

- Two tables (one for `total_amount`, one for `passenger_count`): rows =
  the 5 months, columns = min/max/mean/p25/p50/p75/p95/p99.
- Immediately below each table: the count of negative-or-zero
  `total_amount` records (per US4) or null-or-zero `passenger_count`
  records (per US3), per month — not folded silently into the mean.

### 5. Out-of-Range Dates

- A table: one row per month, one column for the count of records whose
  `tpep_pickup_datetime` or `tpep_dropoff_datetime` falls outside the
  whole Jan 1 - May 31, 2023 window (FR-005 scope — not adjacent-month
  leakage; see spec.md Assumptions).

### 6. Duplicates

- One line per month (or one line for the full 5-month set, whichever the
  implementation computes per research.md §3): the full-row duplicate
  count.

## Guarantees this feature provides to consumers

1. Every one of the 6 sections above exists and covers all 5 months — no
   month silently skipped (SC-002).
2. Every data-quality risk named in the constitution (negative/zero
   `total_amount`, null/zero `passenger_count`, out-of-range dates,
   duplicates) has a quantified count in this file (SC-003) — feature 005
   should never need to re-derive these numbers from scratch.
3. Schema deviations are pre-classified by severity so feature 004 doesn't
   have to re-judge which differences matter.

## Non-guarantees (explicitly out of scope here)

- No dedup policy, null-handling policy, or outlier-handling policy is
  decided in this file — only the volumes are reported (features 004/005
  decide what to do about them).
- Adjacent-month date leakage within the Jan-May window is not measured
  (2026-07-22 clarification) — only whole-window out-of-range dates are.
