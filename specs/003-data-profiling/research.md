# Phase 0 Research: Data Profiling (EDA sobre Bronze)

**Input**: [spec.md](./spec.md) · Constitution `.specify/memory/constitution.md` · feature 002's execution pattern

No `[NEEDS CLARIFICATION]` markers remain in the spec. The items below are
planning-phase technical decisions needed to turn the spec's requirements
into an implementable design.

## 1. Percentile computation method (FR-004)

- **Decision**: Use PySpark's `DataFrame.approxQuantile` (approximate
  percentiles with a small relative error, e.g. 0.01) rather than an exact
  percentile computation.
- **Rationale**: Exact percentiles require a full sort across ~15M rows
  (5 months); approximate quantiles are the standard, cheap approach for
  exploratory profiling and are more than precise enough to spot outliers
  ahead of the two analytical questions — this isn't a metric with a
  precision SLA.
- **Alternatives considered**: Exact `percentile()`/sort-based computation
  — rejected as unnecessary cost for a profiling report, not a billing or
  compliance metric. `percentile_approx` SQL function — equivalent choice,
  not used only because `approxQuantile` is the more direct DataFrame API.

## 2. Type-family classification for schema comparison (FR-001/FR-009/FR-010)

- **Decision**: Group Spark data types into families before comparing
  across months: `integer` (byte/short/int/long), `floating` (float/
  double/decimal), `string`, `timestamp_or_date`, `boolean`. Two columns
  match if they're in the same family, even if the exact type differs
  (e.g. `int` vs `bigint`).
- **Rationale**: Codifies the 2026-07-22 clarification directly — this
  avoids flagging harmless width differences (common across NYC TLC
  yearly schema revisions) as deviations while still catching real
  incompatibilities (e.g. a column that changed from string to numeric).
- **Alternatives considered**: Exact `DataType` equality — rejected per
  the clarification (too noisy). Name-only comparison ignoring type
  entirely — rejected, would miss a genuine cross-family type change.

## 3. Full-row duplicate detection (FR-006)

- **Decision**: Compute `total_row_count - df.dropDuplicates().count()`
  per month (and optionally across the full 5-month set) rather than a
  `groupBy(all_columns).count().filter(count > 1)` aggregation.
- **Rationale**: Only a count is required by FR-006 (not which rows are
  duplicated), so the simpler two-count subtraction is cheaper and easier
  to read than a full group-by over every column.
- **Alternatives considered**: `groupBy(*columns).count()` — rejected as
  more expensive and returns more detail than the spec asks for.

## 4. Where profiling findings are persisted (FR-007)

- **Decision**: A new `specs/003-data-profiling/findings.md`, authored
  during implementation from each script's JSON output — the same
  convention feature 002 used for `DECISOES_PROJETO.md` §2 (script runs,
  produces a JSON result via `dbutils.notebook.exit`, the result is then
  transcribed into a versioned, human-readable markdown artifact).
- **Rationale**: `DECISOES_PROJETO.md` is for project *decisions*, not raw
  profiling tables — a dedicated file keeps that document from becoming a
  data dump, and gives feature 004 a single, stable file to read when
  designing the data contract. The structure this file must follow is
  fixed by `contracts/profiling-findings-schema.md` (Phase 1).
- **Alternatives considered**: Writing findings into `analysis/` — rejected,
  that directory is reserved by the case brief for the two analytical
  questions, not profiling. Leaving findings only as notebook/job output —
  rejected, violates FR-007 (must be a versioned, reviewable artifact).

## 5. Execution mechanism (consistent with feature 002)

- **Decision**: Each profiling script is written in Databricks
  notebook-source format, imported into the workspace, and run via
  `databricks jobs submit` (serverless compute) — the same mechanism
  `network_check.py`/`landing_zone.py`/`land_files.py` used in feature 002.
- **Rationale**: The bronze volume (`ifood_case.bronze.yellow_taxi_raw`)
  is only reachable from inside the workspace; reusing the proven
  mechanism from feature 002 avoids introducing a second execution pattern
  for no reason (Constitution Principle VI).
- **Alternatives considered**: Local PySpark against downloaded copies of
  the files — rejected, adds a redundant local-data-handling path and
  contradicts profiling the actual governed bronze volume.

## 6. Reading files individually vs. a unioned DataFrame

- **Decision**: Read each of the 5 monthly files independently in a loop
  (`spark.read.parquet(path)` per month), never as a single unioned
  DataFrame.
- **Rationale**: A `unionByName` (even with `allowMissingColumns=True`)
  would obscure exactly the schema differences User Story 1 needs to
  surface, and a plain `union` would outright fail or silently misalign
  columns if schemas differ — reading per-file keeps every metric cleanly
  attributable to its month, matching feature 002's own per-month loop
  pattern in `land_files.py`.
- **Alternatives considered**: `unionByName(allowMissingColumns=True)` for
  volumetry/stats after schema is confirmed compatible — rejected as an
  unnecessary second code path when per-month reads already give every
  number this feature needs.
