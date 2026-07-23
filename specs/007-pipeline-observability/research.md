# Phase 0 Research: Observability da Pipeline

**Input**: [spec.md](./spec.md) · Constitution `.specify/memory/constitution.md` ·
`src/bronze/ingest_bronze.py` (feature 004) · `src/silver/build_silver.py` (feature 006)

No `[NEEDS CLARIFICATION]` markers remain in the spec (clarify found no
critical ambiguities, 2026-07-23). The items below are planning-phase
technical decisions, including one real platform constraint discovered
by directly querying this workspace during this research phase.

## 1. Pipeline Run Log Entry schema

- **Decision**: An explicit `StructType`, not schema-on-write inference:
  `pipeline_stage` (string), `executed_at` (timestamp), `status`
  (string), `rows_read` (long, nullable), `rows_written` (long,
  nullable), `schema_check_status` (string, nullable),
  `duration_seconds` (double, nullable), `metrics` (string — a JSON
  blob of stage-specific counts), `alerts` (array\<string\>, empty when
  none triggered).
- **Rationale**: Bronze and silver report different metric sets
  (bronze: `duplicates_removed`; silver: 4 named rule counts +
  `total_dropped`) — a single flexible `metrics` JSON column avoids a
  wide table that's mostly null for any given row, while every other
  field is common to both stages and stays strongly typed. An explicit
  schema avoids Spark inferring `array<string>` vs `array<null>`
  inconsistently across an empty vs. non-empty `alerts` list on
  different runs.
- **Alternatives considered**: A wide table with one column per
  possible metric across both stages — rejected, mostly-null columns
  and no clear extension path if a future stage reports yet another
  shape. A separate table per stage — rejected, defeats the point of one
  queryable log a reader can scan across all stages at once.

## 2. Where the logging/alerting code lives

- **Decision**: Duplicate the (small) logging and alert-check helper
  code directly into both `ingest_bronze.py` and `build_silver.py` —
  no new shared `src/` package.
- **Rationale**: Every prior feature in this project keeps each
  Databricks notebook-source script self-contained and independently
  deployable (`databricks workspace import` uploads one file at a
  time); a shared importable module would need its own upload and a
  working import path inside the remote notebook environment, for a
  net addition of maybe 30 lines duplicated once — not worth the new
  deployment mechanism (Constitution Principle VI).
- **Alternatives considered**: A shared `src/observability/pipeline_log.py`
  module — rejected for the reason above; revisit only if a third
  pipeline stage needs the exact same helper (not the case here).

## 3. Failure-path logging (FR-003)

- **Decision**: Two layers, matching what each script already does:
  1. **Anticipated failures** (the schema-assertion `ValueError` both
     scripts already catch internally, feature 004/006) are unchanged —
     they already return a `{"...status": "failed", "error": ...}` dict
     without re-raising, so the Databricks job still reports SUCCESS
     with a failure-flagged payload. This feature only adds: *also*
     write that dict's status into `_pipeline_run_log`, whether it says
     "pass" or "failed".
  2. **Unanticipated exceptions** (anything not already caught inside
     `ingest_bronze()`/`build_silver()`) are now caught by a new, broad
     `try/except Exception` wrapping the `if __name__ == "__main__":`
     block: log a minimal row (`status="failed"`, the error message,
     whatever partial timing is available), then **re-raise** — so the
     Databricks job correctly reports FAILED for a genuine crash, unlike
     the anticipated-failure path.
- **Rationale**: FR-007 forbids changing bronze's/silver's actual
  behavior — so the already-established "catch known failure, report,
  don't crash the job" pattern for schema mismatches stays exactly as
  it is. The new broad catch only covers failure modes that previously
  had *no* logging at all (an uncaught crash before either script's
  `print`/`dbutils.notebook.exit` line), which is what FR-003 is
  actually asking for.
- **Alternatives considered**: Making the anticipated schema-assertion
  failure also re-raise (so it, too, fails the job) — rejected as an
  unrelated behavior change to features 004/006, forbidden by FR-007.

## 4. Alert threshold check (FR-004)

- **Decision**: For any named count in a run's metrics (bronze:
  `duplicates_removed`; silver: each of the 4 rule counts), compute
  `count / rows_read`. If `> 0.01`, append a message (e.g.
  `"passenger_count_null_or_zero: 4.34% > 1% threshold"`) to that run's
  `alerts` list and `print()` a clearly-marked banner. `total_dropped`
  is not itself checked against the threshold (it's a derived,
  overlapping-aware total, not a single rule).
- **Rationale**: Matches the constitution's own example value (">1%")
  literally, applied uniformly across both stages per spec Edge Case 2
  — bronze's check exists in the code even though it won't fire with
  current data (0 duplicates).
- **Alternatives considered**: A configurable threshold parameter —
  rejected as unnecessary for a fixed, one-time case; the constitution
  names one value, not a range to tune.

## 5. Native Unity Catalog lineage: two mechanisms, not one

- **Decision**: Confirmed by directly querying this workspace
  (`SELECT * FROM system.access.table_lineage`) that this system table
  **is** enabled on Free Edition and already contains real entries —
  e.g. `ifood_case.bronze.yellow_taxi_trips → ifood_case.silver.yellow_taxi_trips`
  shows up automatically, tied to the actual job run that produced it,
  with zero custom code. However, `SHOW TABLES IN system.access` lists
  only `table_lineage` and `column_lineage` — both track **table**-to-
  **table** edges only. `ifood_case.landing.yellow_taxi_raw` is a
  **Volume** (files), not a table, so the landing→bronze edge does not
  appear in `table_lineage` (confirmed empty `source_table_full_name`
  for bronze's row). The volume→table half of the chain is instead
  visible in Catalog Explorer's lineage graph UI, which Databricks
  documents as tracking file/volume-level sources in addition to
  tables.
- **Rationale**: This is a genuine platform constraint, not a design
  choice — verified empirically rather than assumed. Splitting the
  verification story (system table for bronze→silver, UI for
  landing→bronze) still satisfies FR-005 ("MUST NOT build a custom
  lineage-tracking mechanism") using only native features, just two of
  them instead of one.
- **Alternatives considered**: Querying `system.access.column_lineage`
  for the volume path — rejected, same table-centric limitation applies
  (column lineage is a finer-grained view of the same table-to-table
  tracking, not a route to file-level sources).

## 6. Execution mechanism (consistent with features 002-004, 006)

- **Decision**: Both modified scripts are re-uploaded via
  `databricks workspace import --overwrite` and re-run via
  `databricks jobs submit` (serverless compute) — same mechanism as
  every feature except 005.
- **Rationale**: No new execution pattern needed; both scripts already
  proved this pipeline runs cleanly (mostly) or reasonably at that.
