# Data Profiling Findings: NYC Yellow Taxi Bronze (Jan-May 2023)

Structure fixed by [contracts/profiling-findings-schema.md](contracts/profiling-findings-schema.md).
Source: `ifood_case.bronze.yellow_taxi_raw` (feature 002). Produced by
`src/profiling/schema_check.py` and `src/profiling/profile_bronze.py`, run
via `databricks jobs submit` on serverless compute, 2026-07-23.

## 1. Schema Comparison

**Result: NOT identical across all 5 months.** Two deviations found —
column names are matched case-insensitively and types by family
(research.md §2), so only genuine differences are listed below.

| Column | Severity | Months present | Type family by month |
|---|---|---|---|
| `passenger_count` | **critical** (required column) | all 5 | `floating` in 2023-01; `integer` in 2023-02 through 2023-05 |
| `ratecodeid` | informational | all 5 | `floating` in 2023-01; `integer` in 2023-02 through 2023-05 |

**Note (not a deviation)**: `airport_fee` is spelled `airport_fee` in the
January file and `Airport_fee` in February-May — a casing-only difference,
correctly excluded from the table above per the case-insensitive matching
rule (2026-07-22 clarification).

**Implication for feature 004**: the data contract must cast
`passenger_count` to a consistent numeric type (it already tolerates
fractional values in the January source, even though it's conceptually an
integer count) rather than assuming a fixed source type.

## 2. Volumetry

| Month | Row count |
|---|---|
| 2023-01 | 3,066,766 |
| 2023-02 | 2,913,955 |
| 2023-03 | 3,403,766 |
| 2023-04 | 3,288,250 |
| 2023-05 | 3,513,649 |
| **Total** | **16,186,386** |

## 3. Completeness (Null Rates)

Null-count and null-percentage per required column, per month. `VendorID`,
`total_amount`, `tpep_pickup_datetime`, and `tpep_dropoff_datetime` have
**zero nulls in every month**.

| Month | `passenger_count` null count | `passenger_count` null % |
|---|---|---|
| 2023-01 | 71,743 | 2.34% |
| 2023-02 | 76,817 | 2.64% |
| 2023-03 | 87,619 | 2.57% |
| 2023-04 | 90,690 | 2.76% |
| 2023-05 | 101,796 | 2.90% |

**`passenger_count` null-**or**-zero (combined defect, US3 Acceptance Scenario 2)**:

| Month | Count | % of rows |
|---|---|---|
| 2023-01 | 122,907 | 4.01% |
| 2023-02 | 124,094 | 4.26% |
| 2023-03 | 145,984 | 4.29% |
| 2023-04 | 147,640 | 4.49% |
| 2023-05 | 161,521 | 4.60% |

## 4. Descriptive Statistics

### `total_amount`

| Month | min | max | mean | p25 | p50 | p75 | p95 | p99 |
|---|---|---|---|---|---|---|---|---|
| 2023-01 | -751.00 | 1169.40 | 27.02 | 15.25 | 20.15 | 28.20 | 76.60 | 1169.40 |
| 2023-02 | -757.55 | 2208.10 | 26.90 | 15.47 | 20.16 | 28.56 | 77.46 | 2208.10 |
| 2023-03 | -982.95 | 2100.00 | 27.80 | 15.70 | 20.52 | 29.40 | 81.80 | 2100.00 |
| 2023-04 | -807.55 | 2451.00 | 28.27 | 15.70 | 20.75 | 30.60 | 81.80 | 2451.00 |
| 2023-05 | -900.50 | 6304.90 | 28.96 | 16.00 | 21.35 | 30.80 | 82.30 | 6304.90 |

**`total_amount` negative-or-zero (US4 Acceptance Scenario 2)**:

| Month | Count | % of rows |
|---|---|---|
| 2023-01 | 25,772 | 0.84% |
| 2023-02 | 25,466 | 0.87% |
| 2023-03 | 30,363 | 0.89% |
| 2023-04 | 30,272 | 0.92% |
| 2023-05 | 32,273 | 0.92% |

### `passenger_count`

| Month | min | max | mean | p25 | p50 | p75 | p95 | p99 |
|---|---|---|---|---|---|---|---|---|
| 2023-01 | 0 | 9 | 1.36 | 1.0 | 1.0 | 1.0 | 4.0 | 9.0 |
| 2023-02 | 0 | 9 | 1.35 | 1.0 | 1.0 | 1.0 | 4.0 | 9.0 |
| 2023-03 | 0 | 9 | 1.35 | 1.0 | 1.0 | 1.0 | 4.0 | 9.0 |
| 2023-04 | 0 | 9 | 1.38 | 1.0 | 1.0 | 1.0 | 4.0 | 9.0 |
| 2023-05 | 0 | 9 | 1.36 | 1.0 | 1.0 | 1.0 | 3.0 | 9.0 |

(null-or-zero counts already reported in section 3.)

## 5. Out-of-Range Dates

Records whose `tpep_pickup_datetime` or `tpep_dropoff_datetime` falls
entirely outside the Jan 1 - May 31, 2023 window (whole-window scope only;
adjacent-month leakage within the window is out of scope per the
2026-07-22 clarification).

| Month | Count | % of rows |
|---|---|---|
| 2023-01 | 38 | 0.0012% |
| 2023-02 | 5 | 0.0002% |
| 2023-03 | 11 | 0.0003% |
| 2023-04 | 8 | 0.0002% |
| 2023-05 | 1,015 | 0.0289% |

## 6. Duplicates

Full-row duplicate count per month (`total_count - dropDuplicates().count()`).

| Month | Duplicate rows |
|---|---|
| 2023-01 | 0 |
| 2023-02 | 0 |
| 2023-03 | 0 |
| 2023-04 | 0 |
| 2023-05 | 0 |

No full-row duplicates found in any month.

## Summary for feature 004/005

- **Schema**: `passenger_count` (required) needs a type cast in the
  contract — source varies between floating and integer across months.
- **Completeness**: `passenger_count` has a real, non-trivial null-or-zero
  rate (~4-4.6% per month) that feature 005's quality rules must decide
  how to handle (drop, flag, or impute).
- **Validity**: `total_amount` has negative/zero values in every month
  (~0.8-0.9% of rows) — a known NYC TLC defect, must be ruled on by
  feature 005.
- **Date range**: a small number of out-of-range dates exist (largest in
  May, 0.03% of rows) — low volume but non-zero, feature 005 should decide
  whether to filter or flag.
- **Duplicates**: no full-row duplicates in any month — no policy decision
  needed here.
