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

`analise.py` is a single genuine multi-cell notebook (markdown + `%sql`
+ Python cells; research.md §1-§2, revised 2026-07-23) — each `%sql`
cell embeds its own query text directly (no runtime read of the
standalone `.sql` files needed), so only the notebook itself needs
uploading. All installs (`%pip install prophet plotly kaleido==0.2.1`)
and all imports live in one dedicated block right after the title cell
(research.md §6/§11, revised twice more — self-installing, not a
job-level dependency; matplotlib replaced by Plotly+Kaleido for
rendering), so the notebook is self-sufficient whether run interactively
or via a job with no special job JSON needed for either dependency:

```
databricks workspace import /Workspace/Users/<you>/ifood_case/analise \
  --file analysis/analise.py --language PYTHON --format SOURCE --overwrite
databricks jobs submit --json '{"tasks":[{"task_key":"analise","notebook_task":{"notebook_path":"/Workspace/Users/<you>/ifood_case/analise"}}]}' --timeout 10m
databricks jobs get-run-output <run-id>
```

**Expected outcome**: A JSON result containing all three queries' row
data plus four base64-encoded PNG chart images (2 for the required
questions, 2 for the bonus Prophet decomposition), rendered via Plotly
and exported with Kaleido. The notebook's own `%pip install` +
`dbutils.library.restartPython()` cells install Prophet, Plotly, and
Kaleido before they're imported — allow extra time for that install on
top of the usual job runtime.

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
- [ ] Step 2 notebook run succeeds (with `prophet` installed by the
      notebook's own `%pip install` cell), returns all three row sets
      and all four chart payloads
- [ ] Step 3 charts decoded and visually consistent with the row data
      (SC-005, SC-006)
- [ ] Step 4 confirms `analysis/answers.md` has both required tables,
      both required charts, both plain-language answers, and a clearly
      labeled bonus section with the Prophet decomposition (SC-001,
      SC-002, SC-006)
- [ ] Neither required query applies any filtering beyond Q2's May-2023
      `WHERE` clause (FR-003, SC-004); the bonus query applies no
      filtering at all beyond the full date range (FR-007)
