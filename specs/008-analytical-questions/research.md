# Phase 0 Research: Análises Analíticas

**Input**: [spec.md](./spec.md) · Constitution `.specify/memory/constitution.md` ·
`ifood_case.silver.yellow_taxi_trips` (features 004-006)

No `[NEEDS CLARIFICATION]` markers remain in the spec. The items below
are planning-phase technical decisions needed to turn the spec's
requirements into two runnable SQL files and a results doc.

## 1. SQL over PySpark

- **Decision**: Both questions are answered as plain `.sql` files, run
  directly against the Databricks SQL Warehouse — not PySpark scripts
  run as jobs.
- **Rationale**: The case brief explicitly allows either format
  ("Entregar como SQL ou PySpark estruturado"). The constitution's own
  Technology Stack section names "Consumo final: SQL via Databricks SQL
  Warehouse" — this is the first feature whose actual deliverable *is*
  that consumption path, rather than a PySpark ingestion/transformation
  step. A `GROUP BY`/`AVG` aggregation is also simpler to read and
  re-run as a single SQL statement than as a Python script wrapping the
  same query.
- **Alternatives considered**: A PySpark script matching the pattern of
  features 004/006 — rejected as unnecessary ceremony (notebook upload,
  job submission, serverless compute startup) for what is, at its core,
  two `SELECT ... GROUP BY` statements with no transformation logic to
  write in Python.

## 2. Query design

- **Decision**:
  - Q1 (`avg_total_amount_by_month.sql`): `GROUP BY date_format(tpep_pickup_datetime, 'yyyy-MM')`,
    `AVG(total_amount)` rounded to 2 decimals, plus a `COUNT(*)` column
    for context (not required by the spec, but cheap and useful evidence
    that no month is empty).
  - Q2 (`avg_passenger_count_by_hour_may.sql`): `WHERE year(tpep_pickup_datetime) = 2023
    AND month(tpep_pickup_datetime) = 5`, `GROUP BY hour(tpep_pickup_datetime)`,
    `AVG(passenger_count)` rounded to 2 decimals, plus `COUNT(*)`.
- **Rationale**: `tpep_pickup_datetime` is guaranteed non-null and within
  Jan-May 2023 by the silver contract's rules (features 005-006), so no
  additional `WHERE` is needed for Q1 beyond the `GROUP BY` itself — the
  table already *is* the whole fleet's valid trips. The `COUNT(*)`
  column costs nothing extra in the same aggregation and directly
  supports spec Edge Case 1 (confirming no hour/month is silently empty).
- **Alternatives considered**: A single combined query with both
  aggregations via `FILTER`/conditional aggregation — rejected, the two
  questions have different grain (month vs. hour) and different scope
  (all 5 months vs. May only), so combining them would only make the
  single result set harder to read for no benefit.

## 3. Rounding precision

- **Decision**: Round both averages to 2 decimal places.
- **Rationale**: Matches the precision already used when this same Q1
  aggregation was shown as a sample query in feature 006's
  `dq-run-log.md` (SC-004 verification) — consistent with existing
  precedent, and a standard, readable precision for a monetary average
  (Q1) and a small count average (Q2).
- **Alternatives considered**: Unrounded `double` output — rejected,
  unnecessarily noisy (e.g. `27.462743969152461`) for a reported answer.

## 4. Where results are recorded

- **Decision**: `analysis/answers.md` — one section per question, each
  with the SQL file it corresponds to, the full result table (all 5
  month-rows / all 24 hour-rows), and a one-line plain-language answer.
- **Rationale**: Spec FR-004/FR-005 requires both the query and its
  actual computed result to be saved as versioned artifacts — a `.sql`
  file alone only satisfies half of that. Same "transcribe the real
  output into a versioned markdown file" convention already established
  by features 003/004/006's findings/log files.
- **Alternatives considered**: Embedding the results as SQL comments
  inside each `.sql` file instead of a separate `answers.md` — rejected,
  mixes a reusable, re-runnable artifact (the query) with a point-in-time
  snapshot (last run's numbers) in the same file; keeping them separate
  makes it obvious the `.sql` files are meant to be re-run, not just read.

## 5. Execution mechanism

- **Decision**: Run both `.sql` files' contents directly against the
  workspace's SQL Warehouse (`databricks experimental aitools tools
  query`, the same mechanism already used throughout this project for
  ad hoc verification queries) — no `databricks jobs submit`, no
  notebook upload.
- **Rationale**: There's no PySpark script to upload as a notebook this
  time (decision 1) — the SQL Warehouse query path is the entire
  execution mechanism, not just a verification step layered on top of a
  job.
- **Alternatives considered**: Wrapping the SQL in a thin PySpark/
  notebook script purely to reuse the `databricks jobs submit` pattern —
  rejected as adding a code layer with no purpose beyond superficial
  consistency with other features (Constitution Principle VI).
