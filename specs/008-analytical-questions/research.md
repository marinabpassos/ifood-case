# Phase 0 Research: Análises Analíticas

**Input**: [spec.md](./spec.md) · Constitution `.specify/memory/constitution.md` ·
`ifood_case.silver.yellow_taxi_trips` (features 004-006)

No `[NEEDS CLARIFICATION]` markers remain in the spec. Decision 1 below
was revised once, before `/speckit-tasks`, based on explicit user
feedback that a genuine Databricks notebook was wanted for the chart
requirement (FR-006) — not a local script — since the notebook is
itself meant to demonstrate the platform's analysis/visualization
capability, not just be the shortest path to a number. Decisions 6-8
were added in a second pre-`/speckit-tasks` revision, for the bonus
Prophet-based daily trip-volume analysis (User Story 5 / FR-007-009)
the user requested as a differentiator on top of the two required
questions.

## 1. Notebook + standalone SQL, not SQL-only (revised)

- **Decision**: Ship both: two plain, standalone `.sql` files (unchanged
  from the original plan) for a business user who wants to run only
  SQL, **and** a Databricks notebook (`analysis/generate_answers.py`,
  PySpark, executing the exact same query text via `spark.sql()`) that
  additionally renders and saves a chart per question.
- **Rationale**: The case brief allows "SQL ou PySpark estruturado," and
  the user explicitly asked for a notebook specifically because it
  doubles as "uma amostra do uso da ferramenta" (a demonstration of tool
  usage) — a legitimate, already-approved requirement (spec FR-006/
  SC-005), not scope creep. Keeping the plain `.sql` files too (rather
  than replacing them with the notebook) preserves User Story 3's
  original "a business user can run this with nothing but SQL" promise.
- **Alternatives considered**: Local Python + `matplotlib` reading query
  results fetched via the CLI's SQL Warehouse query path — rejected per
  explicit user correction: this would be a local-tooling shortcut, not
  a Databricks notebook, and would miss the point of demonstrating the
  platform itself. Notebook-only (dropping the standalone `.sql` files)
  — rejected, that would remove the direct-SQL path the user separately
  asked to keep ("a pessoa de negócio sempre poderá analisar via query
  SQL também").

## 2. Reusing the same query text in both places

- **Decision**: The notebook does not re-type the SQL — it reads each
  `.sql` file's contents from the workspace (uploaded alongside the
  notebook, same `databricks workspace import --format AUTO` pattern
  proven for the data contract in feature 005/006) and executes that
  exact text via `spark.sql(open(path).read())`.
- **Rationale**: Avoids two hand-maintained copies of the same query
  (one in the `.sql` file, one duplicated inside the notebook) that
  could silently drift apart — the same reasoning that led feature 006
  to load its contract's `condition` strings at runtime instead of
  re-encoding them in Python.
- **Alternatives considered**: Writing the SQL a second time directly in
  the notebook as a Python string — rejected for the drift risk above.

## 3. Getting chart images out of Databricks and into the repo

- **Decision**: Each chart is rendered with `matplotlib` inside the
  notebook (already present on Databricks Runtime — no new dependency),
  saved to an in-memory buffer, base64-encoded, and included in the
  notebook's JSON result (the same `dbutils.notebook.exit(json.dumps(...))`
  pattern every prior feature already uses). Locally, the JSON is
  decoded and each chart's base64 payload is written to a `.png` file
  under `analysis/charts/`.
- **Rationale**: Avoids inventing new infrastructure (no Unity Catalog
  Volume just to stage two small images, no local `matplotlib`
  install) — the existing "run a job, get JSON back, transcribe it
  locally" mechanism already handles arbitrary text payloads (base64 is
  just text), so two ~30-50KB PNGs round-trip through it without any
  new mechanism.
- **Alternatives considered**: Writing the PNGs to a Unity Catalog
  Volume and downloading via `databricks fs cp` — rejected as an extra
  Volume just for two small images, more moving parts than the
  already-proven JSON-output round-trip. Manual screenshot (feature
  007's lineage-evidence pattern) — rejected here since these charts
  are *generatable* content (unlike a UI-only lineage graph), so there's
  no reason to require a human screenshot when the notebook can produce
  the exact image deterministically.

## 4. Query design (unchanged from the original plan)

- **Decision**: Same as originally planned:
  - Q1: `GROUP BY date_format(tpep_pickup_datetime, 'yyyy-MM')`,
    `AVG(total_amount)` rounded to 2 decimals, plus `COUNT(*)`.
  - Q2: `WHERE year(tpep_pickup_datetime) = 2023 AND month(tpep_pickup_datetime) = 5`,
    `GROUP BY hour(tpep_pickup_datetime)`, `AVG(passenger_count)` rounded
    to 2 decimals, plus `COUNT(*)`.
- **Rationale**: `tpep_pickup_datetime` is guaranteed non-null and within
  Jan-May 2023 by the silver contract's rules (features 005-006), so no
  additional `WHERE` is needed for Q1. Matches the same precision already
  used in feature 006's own `dq-run-log.md` sample query.
- **Alternatives considered**: See the original research (unchanged) —
  a single combined query was rejected for mixing two different grains
  for no benefit.

## 5. Chart type

- **Decision**: A bar chart for both questions (month on the x-axis for
  Q1, hour of day for Q2) — a bar chart is the most direct, unambiguous
  way to compare discrete categories (5 months; 24 hours), and needs no
  justification beyond "the simplest chart that shows the trend clearly"
  (spec's own FR-006 leaves chart type as an implementation choice).
- **Alternatives considered**: A line chart for Q2 (hour of day is
  ordinal/continuous-ish) — a reasonable alternative, not chosen only
  because a bar chart is marginally more consistent visually with Q1
  without materially changing readability at 24 categories.

## 6. Bonus analysis: Prophet availability and installation mechanism

- **Decision**: Prophet is **not** pre-installed on Databricks Runtime
  (unlike `matplotlib`), so it's declared as a job-level PyPI library
  dependency in the `databricks jobs submit` JSON payload —
  `"libraries": [{"pypi": {"package": "prophet"}}]` on the
  `generate_answers` task — rather than a `%pip install prophet` magic
  cell inside the notebook.
- **Rationale**: `generate_answers.py` is uploaded and run as a plain
  `# Databricks notebook source` script with no `# COMMAND ----------`
  cell markers (the same pattern as every prior feature's notebook) —
  `%pip` magic commands are an interactive-notebook-cell mechanism and
  their behavior in a single-cell plain-script SOURCE notebook run via
  a job is not something to rely on unverified. The Jobs API's per-task
  `libraries` field is the documented, job-native way to install a PyPI
  package before a task runs, regardless of notebook cell structure.
- **Alternatives considered**: `%pip install prophet` as the first line
  of the script — rejected due to the cell-structure uncertainty above.
  A cluster-scoped init script or a persistent library — rejected as
  unnecessary infrastructure for a single read-only bonus analysis on
  serverless compute.

## 7. Bonus analysis: daily trip-count query and decomposition design

- **Decision**: `analysis/daily_trip_counts.sql` computes
  `GROUP BY date(tpep_pickup_datetime)`, `COUNT(*)` across the whole
  silver table (no month filter) — one row per calendar day, ~151 rows
  for Jan 1-May 31, 2023. The notebook collects this to a pandas
  DataFrame (`ds`/`y` columns, Prophet's required shape), fits
  `Prophet(yearly_seasonality=False, weekly_seasonality=True,
  daily_seasonality=False)`, and calls `.predict()` on the same
  historical dates (no forecast into unseen future dates — the ask was
  to see trend/seasonality in the existing data, not to forecast).
- **Rationale**: Yearly seasonality is explicitly disabled because
  ~5 months of data cannot support a meaningful yearly-cycle estimate —
  Prophet would either error or fit an overfit, meaningless yearly
  curve on less than one full period. Weekly seasonality is exactly the
  "repeating pattern" the user asked to see (weekday vs. weekend
  ridership). Daily seasonality doesn't apply since the series is
  already aggregated to one point per day (no sub-daily resolution to
  decompose).
- **Alternatives considered**: Forecasting future (June+) trip counts —
  rejected, out of scope for "ver sazonalidade, tendência" (the user
  asked to see the existing pattern, not predict unseen data). A
  from-scratch statsmodels STL decomposition instead of Prophet —
  rejected, the user explicitly named Prophet.

## 8. Bonus analysis: chart output

- **Decision**: Two chart images, both clearly labeled as bonus/
  differentiator content and kept visually and by-filename distinct
  from the two required questions' charts: `daily_trip_volume_trend.png`
  (`model.plot(forecast)` — actual daily counts with the fitted
  trend/seasonality curve overlaid) and
  `daily_trip_volume_components.png` (`model.plot_components(forecast)`
  — separate trend and weekly-seasonality subplots, Prophet's own
  standard decomposition view). Both round-trip through the same
  base64-in-JSON-output mechanism as decision 3 above.
- **Rationale**: `plot_components` is Prophet's own built-in,
  purpose-built way to show trend and seasonality separately — no
  need to hand-roll a custom decomposition chart when the library
  already produces the standard one.
- **Alternatives considered**: A single combined figure — rejected,
  `plot()` and `plot_components()` serve different, complementary
  purposes (raw fit vs. decomposed components) and Prophet returns them
  as two separate figures natively.

## 9. Execution mechanism

- **Decision**: `generate_answers.py` is a Databricks notebook-source
  script, imported and run via `databricks jobs submit` on serverless
  compute — identical mechanism to features 002/003/004/006/007. The
  two standalone `.sql` files are run directly against the SQL Warehouse
  via `databricks experimental aitools tools query` (or any SQL client),
  with no job/notebook involved for that path.
- **Rationale**: Two different audiences, two different execution paths
  — a business user never needs to touch a notebook or job to get the
  numbers; the notebook is specifically for the chart-generation
  requirement. The bonus analysis's `jobs submit` payload additionally
  carries the `libraries` field from decision 6 above, scoped to the
  `generate_answers` task only.
