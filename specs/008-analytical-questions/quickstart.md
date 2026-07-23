# Quickstart: Validate Análises Analíticas

Validates the 5 Independent Tests from spec.md. Both required questions,
their chart delivery path, and the bonus analysis are independent of
each other; all depend only on `ifood_case.silver.yellow_taxi_trips`
(features 004-006) already existing.

## Prerequisites

- Feature 006 complete: `ifood_case.silver.yellow_taxi_trips` exists,
  15,339,417 rows (`specs/006-silver-data-quality/dq-run-log.md`).
- Databricks CLI authenticated against the `DEFAULT` profile.

## Step 1 — Run the standalone SQL directly (User Story 1/2/3 — business-SQL path)

```
databricks experimental aitools tools query "$(cat analysis/avg_total_amount_by_month.sql)" --profile DEFAULT
databricks experimental aitools tools query "$(cat analysis/avg_passenger_count_by_hour_may.sql)" --profile DEFAULT
databricks experimental aitools tools query "$(cat analysis/daily_trip_counts.sql)" --profile DEFAULT
```

**Expected outcome**: 5 rows for the first query (2023-01 through
2023-05), 24 rows for the second (hour 0 through 23), ~151 rows for the
third (one per calendar day, Jan 1-May 31, 2023) — no notebook or job
involved, matching User Story 3's plain-SQL promise.

## Step 2 — Run the notebook to generate charts (User Story 4/5 / FR-006, FR-009)

```
databricks workspace import /Workspace/Users/<you>/ifood_case/avg_total_amount_by_month.sql \
  --file analysis/avg_total_amount_by_month.sql --format AUTO --overwrite
databricks workspace import /Workspace/Users/<you>/ifood_case/avg_passenger_count_by_hour_may.sql \
  --file analysis/avg_passenger_count_by_hour_may.sql --format AUTO --overwrite
databricks workspace import /Workspace/Users/<you>/ifood_case/daily_trip_counts.sql \
  --file analysis/daily_trip_counts.sql --format AUTO --overwrite
databricks workspace import /Workspace/Users/<you>/ifood_case/generate_answers \
  --file analysis/generate_answers.py --language PYTHON --format SOURCE --overwrite
databricks jobs submit --json '{"tasks":[{"task_key":"generate_answers","notebook_task":{"notebook_path":"/Workspace/Users/<you>/ifood_case/generate_answers"},"libraries":[{"pypi":{"package":"prophet"}}]}]}' --timeout 10m
databricks jobs get-run-output <run-id>
```

**Expected outcome**: A JSON result containing all three queries' row
data plus four base64-encoded PNG chart images (2 for the required
questions, 2 for the bonus Prophet decomposition). The `libraries`
field installs `prophet` on the serverless job cluster before the task
runs (research.md §6) — allow extra time for that install on top of the
usual job runtime.

## Step 3 — Decode the charts and confirm they match the data

Decode each base64 chart payload from Step 2's output into
`analysis/charts/avg_total_amount_by_month.png`,
`analysis/charts/avg_passenger_count_by_hour_may.png`,
`analysis/charts/daily_trip_volume_trend.png`, and
`analysis/charts/daily_trip_volume_components.png`. Visually confirm
each required-question bar chart's shape matches the row data from Step
1/2 (e.g., Q1's bars trend upward from January to May, per feature 006's
own sample: 27.46 → 29.45), and confirm the bonus trend/components
charts show a plausible trend line and a distinct weekly (7-day)
seasonality pattern.

## Step 4 — Confirm all answers are fully documented (User Story 3/4/5 / FR-004-009)

```
cat analysis/answers.md
```

**Expected outcome**: Both required questions' full result tables, both
required chart images (embedded), a one-line plain-language answer each,
and — in a section clearly labeled as bonus/differentiator content —
the daily trip-count decomposition's two charts and a short written
interpretation of the trend/seasonality observed. Everything readable
without re-running anything.

## Done when

- [ ] Step 1 confirms all three standalone `.sql` files run with no
      notebook (SC-003)
- [ ] Step 2 notebook run succeeds (with `prophet` installed via the
      job's `libraries` field), returns all three row sets and all four
      chart payloads
- [ ] Step 3 charts decoded and visually consistent with the row data
      (SC-005, SC-006)
- [ ] Step 4 confirms `analysis/answers.md` has both required tables,
      both required charts, both plain-language answers, and a clearly
      labeled bonus section with the Prophet decomposition (SC-001,
      SC-002, SC-006)
- [ ] Neither required query applies any filtering beyond Q2's May-2023
      `WHERE` clause (FR-003, SC-004); the bonus query applies no
      filtering at all beyond the full date range (FR-007)
