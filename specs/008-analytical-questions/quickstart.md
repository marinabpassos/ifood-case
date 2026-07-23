# Quickstart: Validate Análises Analíticas

Validates the 4 Independent Tests from spec.md. Both questions and both
delivery paths (standalone SQL, notebook+chart) are independent of each
other; all depend only on `ifood_case.silver.yellow_taxi_trips`
(features 004-006) already existing.

## Prerequisites

- Feature 006 complete: `ifood_case.silver.yellow_taxi_trips` exists,
  15,339,417 rows (`specs/006-silver-data-quality/dq-run-log.md`).
- Databricks CLI authenticated against the `DEFAULT` profile.

## Step 1 — Run the standalone SQL directly (User Story 1/2/3 — business-SQL path)

```
databricks experimental aitools tools query "$(cat analysis/avg_total_amount_by_month.sql)" --profile DEFAULT
databricks experimental aitools tools query "$(cat analysis/avg_passenger_count_by_hour_may.sql)" --profile DEFAULT
```

**Expected outcome**: 5 rows for the first query (2023-01 through
2023-05), 24 rows for the second (hour 0 through 23) — no notebook or
job involved, matching User Story 3's plain-SQL promise.

## Step 2 — Run the notebook to generate charts (User Story 4 / FR-006)

```
databricks workspace import /Workspace/Users/<you>/ifood_case/avg_total_amount_by_month.sql \
  --file analysis/avg_total_amount_by_month.sql --format AUTO --overwrite
databricks workspace import /Workspace/Users/<you>/ifood_case/avg_passenger_count_by_hour_may.sql \
  --file analysis/avg_passenger_count_by_hour_may.sql --format AUTO --overwrite
databricks workspace import /Workspace/Users/<you>/ifood_case/generate_answers \
  --file analysis/generate_answers.py --language PYTHON --format SOURCE --overwrite
databricks jobs submit --json '{"tasks":[{"task_key":"generate_answers","notebook_task":{"notebook_path":"/Workspace/Users/<you>/ifood_case/generate_answers"}}]}' --timeout 5m
databricks jobs get-run-output <run-id>
```

**Expected outcome**: A JSON result containing both questions' row data
plus two base64-encoded PNG chart images.

## Step 3 — Decode the charts and confirm they match the data

Decode each base64 chart payload from Step 2's output into
`analysis/charts/avg_total_amount_by_month.png` and
`analysis/charts/avg_passenger_count_by_hour_may.png`, and visually
confirm each bar chart's shape matches the row data from Step 1/2 (e.g.,
Q1's bars trend upward from January to May, per feature 006's own
sample: 27.46 → 29.45).

## Step 4 — Confirm both answers are fully documented (User Story 3/4 / FR-004, FR-006)

```
cat analysis/answers.md
```

**Expected outcome**: Both questions' full result tables, both chart
images (embedded), and a one-line plain-language answer each — readable
without re-running anything.

## Done when

- [ ] Step 1 confirms the standalone `.sql` files run with no notebook
      (SC-003)
- [ ] Step 2 notebook run succeeds, returns both row sets and both chart
      payloads
- [ ] Step 3 charts decoded and visually consistent with the row data
      (SC-005)
- [ ] Step 4 confirms `analysis/answers.md` has both tables, both
      charts, and both plain-language answers (SC-001, SC-002)
- [ ] Neither query applies any filtering beyond Q2's May-2023 `WHERE`
      clause (FR-003, SC-004)
