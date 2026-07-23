# Phase 1 Data Model: Análises Analíticas

No new table or schema — both entities are documentation-level records
of a read-only query and its result, not physical data structures.

## Analytical Answer

Two instances, one per question (spec Key Entities).

| Field | Notes |
|---|---|
| `question` | The case brief's original question text (Portuguese, verbatim) |
| `query_file` | `analysis/avg_total_amount_by_month.sql` or `analysis/avg_passenger_count_by_hour_may.sql` |
| `result_rows` | Q1: 5 rows (month, avg_total_amount, trip_count). Q2: 24 rows (pickup_hour, avg_passenger_count, trip_count) |
| `computed_at` | Timestamp the query was actually run against the SQL Warehouse |
| `plain_language_answer` | One-line summary in `analysis/answers.md` (e.g. "average total_amount ranged from X in February to Y in May") |

**Validation rules**:
- `result_rows` MUST have exactly 5 rows for Q1 (one per month,
  January-May 2023) and exactly 24 rows for Q2 (one per hour, 0-23) —
  per spec Edge Case 1, a genuinely empty hour/month simply doesn't
  appear as a row (not zero-filled), so "exactly N rows" only holds if
  every month/hour actually has at least one trip, which is expected at
  this data volume (~15.3M rows).
- Every row's average MUST derive solely from
  `ifood_case.silver.yellow_taxi_trips`, with no additional filtering
  beyond Q2's May-2023 restriction (FR-003).

**Relationships**: Both Analytical Answers read from the same source —
`ifood_case.silver.yellow_taxi_trips` (feature 006) — but have no
relationship to each other (different grain, different scope).
