# Quickstart: Validate Análises Analíticas

Validates the 3 Independent Tests from spec.md. Both questions are
independent of each other; both depend only on
`ifood_case.silver.yellow_taxi_trips` (features 004-006) already
existing.

## Prerequisites

- Feature 006 complete: `ifood_case.silver.yellow_taxi_trips` exists,
  15,339,417 rows (`specs/006-silver-data-quality/dq-run-log.md`).
- Databricks CLI authenticated against the `DEFAULT` profile.

## Step 1 — Run Q1: average total_amount per month (User Story 1 / FR-001)

```
databricks experimental aitools tools query "$(cat analysis/avg_total_amount_by_month.sql)" --profile DEFAULT
```

**Expected outcome**: Exactly 5 rows (2023-01 through 2023-05), each
with an `avg_total_amount` and a `trip_count` — no month missing, no
extra month.

## Step 2 — Run Q2: average passenger_count by hour in May (User Story 2 / FR-002)

```
databricks experimental aitools tools query "$(cat analysis/avg_passenger_count_by_hour_may.sql)" --profile DEFAULT
```

**Expected outcome**: Exactly 24 rows (hour 0 through hour 23), each
with an `avg_passenger_count` and a `trip_count`.

## Step 3 — Confirm both answers are documented, not just queried (User Story 3 / FR-004, FR-005)

```
cat analysis/answers.md
```

**Expected outcome**: Both questions' full result tables (5 rows / 24
rows) and a one-line plain-language answer are present — readable
without re-running anything.

## Done when

- [ ] Step 1 returns exactly 5 rows, matching `analysis/answers.md`
- [ ] Step 2 returns exactly 24 rows, matching `analysis/answers.md`
- [ ] Step 3 confirms both queries and their actual results are saved as
      versioned files (SC-001, SC-002, SC-003)
- [ ] Neither query applies any filtering beyond Q2's May-2023 `WHERE`
      clause — no re-derived business rule of this feature's own
      invention (FR-003, SC-004)
