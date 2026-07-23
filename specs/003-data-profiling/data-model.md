# Phase 1 Data Model: Data Profiling (EDA sobre Bronze)

All entities here are **profiling metadata** — read-only findings about the
bronze files, never a transformation of their content (Constitution
Principle I: profiling happens before any modeling, and per FR-008, this
feature writes no persisted table).

## Monthly Trip Record File (read-only input, from feature 002)

Unchanged from `specs/002-ambiente-landing-zone/data-model.md` — this
feature only reads `ifood_case.bronze.yellow_taxi_raw/yellow_tripdata_2023-{MM}.parquet`
for each of the 5 months. No field of this entity is modified here.

## Schema Deviation

One row per column that differs across the 5 months (User Story 1,
FR-001/FR-009/FR-010). Absent if a column is identical (name + type
family) across all 5 files.

| Field | Type | Notes |
|---|---|---|
| `column_name` | string | Canonical (lower-cased) column name |
| `months_present` | list of `YYYY-MM` | Which months have this column at all |
| `type_family_by_month` | map `month -> family` | `integer`\|`floating`\|`string`\|`timestamp_or_date`\|`boolean`\|`missing` per month (research.md §2) |
| `is_required_column` | boolean | Whether `column_name` is one of the 5 case-brief-required columns |
| `severity` | enum: `critical` \| `informational` | `critical` iff `is_required_column = true` (FR-009); otherwise `informational` (FR-010) |

**Validation rule**: A `Schema Deviation` row exists only when at least one
month's type family or presence differs from the others — an identical
column across all 5 months produces no row (SC-001's "identical schema"
case is the empty-list state, not a special value).

## Profiling Finding

One row per (month × metric) combination for the non-schema metrics
(User Stories 2-4 and the duplicate/date-range edge cases). Read-only,
non-authoritative for anything beyond what feature 004/005 explicitly
consume from `findings.md`.

| Field | Type | Notes |
|---|---|---|
| `month` | string, `YYYY-MM` | One of `2023-01`..`2023-05` |
| `row_count` | integer | FR-002 |
| `null_rate_by_required_column` | map `column -> percentage` | FR-003, only the 5 required columns |
| `stats_total_amount` | object: min/max/mean/p25/p50/p75/p95/p99 | FR-004 |
| `stats_passenger_count` | object: min/max/mean/p25/p50/p75/p95/p99 | FR-004 |
| `negative_or_zero_total_amount_count` | integer | Called out explicitly per US4 Acceptance Scenario 2 |
| `null_or_zero_passenger_count` | integer | Called out explicitly per US3 Acceptance Scenario 2 |
| `out_of_range_date_count` | integer | FR-005, whole Jan-May 2023 window only (not adjacent-month leakage) |
| `duplicate_row_count` | integer | FR-006, full-row duplicates (research.md §3) |

**Completion condition (SC-002)**: All 5 `month` rows exist with every
field populated (no month skipped).

## Relationships

- Each `Monthly Trip Record File` (5 total) has exactly one `Profiling
  Finding` row.
- Each `Schema Deviation` (0 or more) references the set of months where
  the deviation was observed — it is a cross-month entity, not scoped to
  a single month like `Profiling Finding`.
