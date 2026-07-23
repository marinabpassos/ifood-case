# Feature Specification: Observability da Pipeline

**Feature Branch**: `007-pipeline-observability`

**Created**: 2026-07-23

**Status**: Draft

**Input**: User description: "feature 007 - Observability da Pipeline: tabela _pipeline_run_log, métricas de volume/schema por execução, lineage nativo do Unity Catalog, alerting por threshold"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Every pipeline execution is queryable, not just readable in markdown (Priority: P1)

As the case evaluator, I need every pipeline execution (bronze ingestion,
silver cleaning) to persist its volume, schema-check, and status metrics
into a queryable table in the consumption layer, so pipeline health is
auditable via SQL or Genie — not only by reading `ingestion-log.md`/
`dq-run-log.md` by hand.

**Why this priority**: This is Constitution Principle III's core mandate
("These MUST be persisted to a queryable metadata table... not just
printed to notebook output") and the reason this feature exists at all.

**Independent Test**: Query `ifood_case.silver._pipeline_run_log` and
confirm it has one row per pipeline stage execution (bronze, silver)
with the expected metrics populated, independent of the alerting or
lineage stories.

**Acceptance Scenarios**:

1. **Given** `src/bronze/ingest_bronze.py` and `src/silver/build_silver.py`
   are extended to log and then re-run, **When** each completes, **Then**
   a row appears in `ifood_case.silver._pipeline_run_log` with
   `rows_read`/`rows_written`/`status`/`schema_check_status`/
   `duration_seconds` matching what each script's own JSON output
   already reports (feature 004's `ingestion-log.md`; feature 006's
   `dq-run-log.md`).
2. **Given** a pipeline is re-run again later, **When** it completes,
   **Then** a **new** row is appended to `_pipeline_run_log` — the log
   accumulates history across runs, unlike the bronze/silver data tables
   themselves (which overwrite).
3. **Given** a pipeline run fails partway (e.g., a schema assertion
   raises), **When** the failure happens, **Then** a row is still
   written recording `status = "failed"` and the error, not silently
   skipped.

---

### User Story 2 - A real data-quality issue triggers a visible alert (Priority: P2)

As the case evaluator, I need a visible alert when any data-quality
rule's drop rate exceeds a defined threshold, so quality issues surface
immediately in the log, not buried in a report someone has to go looking
for.

**Why this priority**: Directly satisfies Principle III's explicit
alerting mandate ("A defined threshold... MUST trigger a visible
alert"). Depends on User Story 1's logging existing (the alert is
recorded in the same log row), so it's sequenced second.

**Independent Test**: Confirm the rule already known to exceed the
threshold with real data (`passenger_count_null_or_zero`, ~4.34% of
rows read, per feature 006's `dq-run-log.md`) produces a recorded alert,
independent of the lineage story.

**Acceptance Scenarios**:

1. **Given** the threshold is >1% of rows read for a single rule (the
   constitution's own example value), **When** the silver pipeline runs,
   **Then** `passenger_count_null_or_zero` (~4.34%) triggers a visible
   alert — both a console/notebook banner and an entry in the log row's
   alert list — while the other 3 rules (0.89%, 0.005%, 0.007%, all
   under 1%) do not.
2. **Given** bronze's only "rule" is technical dedup (0 duplicates
   found, feature 004), **When** the bronze pipeline runs, **Then** no
   alert is triggered there — the same threshold logic applies
   uniformly to both stages, it just has nothing to trigger on in
   bronze with the current data.

---

### User Story 3 - Data lineage is traceable without a custom-built system (Priority: P3)

As the case evaluator, I need to trace `ifood_case.silver.yellow_taxi_trips`
back through `ifood_case.bronze.yellow_taxi_trips` to
`ifood_case.landing.yellow_taxi_raw` using Unity Catalog's native
lineage feature, so provenance is auditable without this project
building its own lineage tracker.

**Why this priority**: Lowest priority because the mechanism already
exists natively in Unity Catalog for every table this project has read
or written since feature 002 — this story is about verifying and
documenting it, not building new logic.

**Independent Test**: Query Unity Catalog's table-level lineage system
for `ifood_case.silver.yellow_taxi_trips` and confirm bronze appears as
an upstream source; separately confirm in Catalog Explorer's lineage
graph that bronze's own upstream shows the landing volume (see note
below on why these are two different mechanisms).

**Acceptance Scenarios**:

1. **Given** every table in this project was read/written exclusively
   through Unity Catalog, **When** lineage is queried via
   `system.access.table_lineage`, **Then**
   `ifood_case.bronze.yellow_taxi_trips` appears as
   `ifood_case.silver.yellow_taxi_trips`'s direct upstream source (both
   are tables — this edge is table-to-table).
2. **Given** `ifood_case.landing.yellow_taxi_raw` is a Volume (files),
   not a table, **When** `system.access.table_lineage` is queried for
   `ifood_case.bronze.yellow_taxi_trips`, **Then** no upstream table
   appears there (this system table only tracks table-to-table edges) —
   the landing→bronze edge is instead confirmed via Catalog Explorer's
   lineage graph UI, which does track file/volume-level sources, per
   Databricks' own lineage feature set. This is a real platform
   constraint discovered during planning, not a gap this feature needs
   to work around: `table_lineage` still completes the table-to-table
   half of the chain (bronze→silver) with zero custom code, and the UI
   covers the volume-to-table half the same way it always has for any
   Unity Catalog volume.

---

### Edge Cases

- If a pipeline run fails before any metric can be computed (e.g., the
  bronze table itself is unreadable), the log row MUST still record
  `status = "failed"` with whatever information is available (at
  minimum `pipeline_stage` and `executed_at`) — never silently skip
  logging just because the run didn't succeed.
- A drop rate of exactly 1.0% is **not** an alert (threshold is
  strictly `> 1%`, per the constitution's own phrasing).
- If Unity Catalog's lineage view has a delay before reflecting a very
  recent write, this feature only needs to demonstrate the lineage
  chain is present and correct at verification time — not guarantee
  real-time propagation.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: A Delta table `ifood_case.silver._pipeline_run_log` MUST
  exist, and MUST be appended to (never overwritten) on every pipeline
  execution — unlike the bronze/silver data tables, this table
  accumulates history.
- **FR-002**: Both `src/bronze/ingest_bronze.py` and
  `src/silver/build_silver.py` MUST be extended to write exactly one row
  to `_pipeline_run_log` as the final step of their own execution,
  recording at minimum: `pipeline_stage`, `executed_at`, `status`,
  `rows_read`, `rows_written`, `schema_check_status`,
  `duration_seconds`, and stage-specific metrics.
- **FR-003**: The log row MUST be written even when the pipeline run
  fails (`status = "failed"`, with the error captured) — logging MUST
  NOT be skipped on the failure path.
- **FR-004**: For any rule/check whose dropped-row rate exceeds 1% of
  rows read in a given run, the pipeline MUST record a visible alert —
  both a console/notebook banner and an entry in that run's log row —
  expected to trigger for silver's `passenger_count_null_or_zero` rule
  (~4.34%) with the current data, and not for the other 3 rules or
  bronze's dedup check.
- **FR-005**: This feature MUST NOT build a custom lineage-tracking
  mechanism — landing→bronze→silver lineage MUST be confirmed via Unity
  Catalog's native lineage feature.
- **FR-006**: Both `ingest_bronze.py` and `build_silver.py` MUST be
  re-run at least once after being extended, so `_pipeline_run_log`
  contains real, current execution evidence — not simulated or
  hand-entered data.
- **FR-007**: This feature MUST NOT change bronze's or silver's actual
  data-quality rules, target schema, or the content of the tables they
  write — logging and alerting are added as a side effect of their
  existing execution, not a behavior change to the data itself.

### Key Entities

- **Pipeline Run Log Entry**: one row per (pipeline stage, execution).
  Fields: `pipeline_stage` (`bronze` | `silver`), `executed_at`,
  `status` (`success` | `failed` | `partial`), `rows_read`,
  `rows_written`, `schema_check_status`, `duration_seconds`,
  stage-specific metrics (e.g. bronze's duplicates-removed count,
  silver's 4 independent per-rule counts and total-dropped), and a list
  of triggered alert messages (empty if none).

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Querying `ifood_case.silver._pipeline_run_log` returns at
  least one row per pipeline stage (bronze, silver) from this feature's
  re-runs, with every required field populated — zero rows with missing
  core fields.
- **SC-002**: The silver run's log row contains a recorded alert for
  `passenger_count_null_or_zero` (a real, non-simulated threshold
  trigger at ~4.34%), and no alert for the other 3 rules or bronze's
  dedup check.
- **SC-003**: A reader can trace `ifood_case.silver.yellow_taxi_trips`
  back to `ifood_case.bronze.yellow_taxi_trips` via
  `system.access.table_lineage` (table-to-table), and further back to
  `ifood_case.landing.yellow_taxi_raw` via Catalog Explorer's lineage
  graph (the volume-to-table half — not captured by the queryable
  system table, confirmed during planning) — using only Unity Catalog's
  native lineage features, no custom lineage table built by this
  project.
- **SC-004**: The re-run's logged `rows_read`/`rows_written`/per-rule
  counts match exactly what feature 004's `ingestion-log.md` and feature
  006's `dq-run-log.md` already recorded — proving the pipelines are
  idempotent and consistent across repeated executions, not just logged
  once by chance.

## Assumptions

- This feature depends on features 004 (bronze layer) and 006 (silver
  data quality), both complete and merged.
- **Design decision**: rather than backfilling `_pipeline_run_log` with
  historical numbers transcribed from `ingestion-log.md`/`dq-run-log.md`,
  this feature extends the actual `ingest_bronze.py`/`build_silver.py`
  scripts to log as part of their own execution, then re-runs both once
  (safe: both already use idempotent overwrite semantics on the data
  tables themselves) to produce genuine, current log evidence. This
  matches Principle III's "every pipeline execution MUST log" literally,
  rather than treating observability as a retroactive report.
- The alerting threshold is fixed at **>1% of rows read for a single
  rule/check**, per the constitution's own example value — not an
  independently chosen number.
- `_pipeline_run_log` lives in `ifood_case.silver` (the "consumption
  layer," per the constitution's own example placement), reusing the
  schema feature 006 already created — no new schema needed.
- Unity Catalog's native lineage is assumed to already track every
  table this project reads/writes automatically (standard behavior for
  any table accessed exclusively through Unity Catalog, which every
  feature since 002 has done) — this feature verifies and documents it,
  it does not build it.
- Stage-specific metrics (e.g. silver's 4 per-rule counts) are stored as
  a single structured/JSON column rather than a wide table with one
  column per possible metric, since bronze and silver report different
  metric sets and a single flexible column avoids a schema that's mostly
  null for any given row.
