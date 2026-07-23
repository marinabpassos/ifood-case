# Phase 0 Research: Análises Analíticas

**Input**: [spec.md](./spec.md) · Constitution `.specify/memory/constitution.md` ·
`ifood_case.silver.yellow_taxi_trips` (features 004-006)

No `[NEEDS CLARIFICATION]` markers remain in the spec. Decision 1 below
was revised once, before `/speckit-tasks`, based on explicit user
feedback that a genuine Databricks notebook was wanted for the chart
requirement (FR-006) — not a local script — since the notebook is
itself meant to demonstrate the platform's analysis/visualization
capability, not just be the shortest path to a number.

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

## 6. Execution mechanism

- **Decision**: `generate_answers.py` is a Databricks notebook-source
  script, imported and run via `databricks jobs submit` on serverless
  compute — identical mechanism to features 002/003/004/006/007. The
  two standalone `.sql` files are run directly against the SQL Warehouse
  via `databricks experimental aitools tools query` (or any SQL client),
  with no job/notebook involved for that path.
- **Rationale**: Two different audiences, two different execution paths
  — a business user never needs to touch a notebook or job to get the
  numbers; the notebook is specifically for the chart-generation
  requirement.
