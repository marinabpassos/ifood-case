# Phase 0 Research: Camada Bronze

**Input**: [spec.md](./spec.md) · Constitution `.specify/memory/constitution.md` ·
feature 002's execution pattern · feature 003's findings (`../003-data-profiling/findings.md`)

No `[NEEDS CLARIFICATION]` markers remain in the spec. The items below are
planning-phase technical decisions needed to turn the spec's requirements
into an implementable design.

## 1. Schema-namespace move mechanism (FR-001)

- **Decision**: Implement the "rename" as create-new + copy + verify +
  drop-old, run as a scripted job (same execution mechanism as every other
  step): create `ifood_case.landing` schema and `yellow_taxi_raw` volume,
  copy the 5 files from `ifood_case.bronze.yellow_taxi_raw` into it,
  verify byte-for-byte size match (same check used in feature 002, SC-004),
  then drop the now-empty `ifood_case.bronze` schema/volume.
- **Rationale**: Confirmed via Databricks documentation that Unity Catalog
  has **no `ALTER SCHEMA ... RENAME TO` SQL statement** — renaming a
  schema requires either the Catalog Explorer UI's kebab-menu action, or
  (for a scripted/reproducible path) creating a new schema and moving
  assets into it. The UI action is a true metadata-only rename (faster,
  zero data movement) but is manual and can't run via `databricks jobs
  submit`, breaking this project's established reproducible-execution
  pattern (Constitution Principle V). The copy-verify-delete path costs a
  one-time transfer of ~264MB (5 files, already-known sizes from feature
  002) — negligible for a one-time batch load.
- **Alternatives considered**: Catalog Explorer UI rename — rejected as
  unscripted/manual (see above), though noted as a valid fallback if the
  scripted copy hits an unexpected Free Edition restriction (same posture
  as feature 002's catalog-creation fallback). Leaving the volume under
  the `bronze`-named schema and putting the new Delta table in a
  differently-named schema instead (e.g. `ifood_case.bronze_tables`) —
  rejected, contradicts the 2026-07-23 brainstorming decision to use
  `landing`/`bronze`/`silver` as the three canonical schema names.
- **Constitution note**: This is a Free-Edition-driven workaround
  (Principle IV) — documented here, in `plan.md`'s Complexity Tracking,
  and to be added to `DECISOES_PROJETO.md` at implementation time.

## 2. Target type for drifted columns (FR-003)

- **Decision**: Cast both `passenger_count` and `ratecodeid` to
  `IntegerType` across all 5 months (not `DoubleType`/`LongType`).
- **Rationale**: Feature 003 profiling shows `passenger_count` is a small
  whole-number count (min 0, max 9 in every month) even in the 2023-01
  file where it's stored as `float` — no fractional values are meaningful
  for a passenger count, so casting to integer loses no real information.
  `ratecodeid` is a categorical code (also float only in 2023-01),
  equally safe to normalize to integer.
- **Alternatives considered**: Casting to `DoubleType` (widen everything
  to float instead of narrowing to int) — rejected, keeps a
  conceptually-integer field numerically ambiguous for every downstream
  reader, including feature 006's null/zero `passenger_count` rule and the
  case's second analytical question (average passengers per hour).

## 3. Combining the 5 months into one table (contrast with feature 003)

- **Decision**: Read each month with `spark.read.parquet(path)`, cast the
  two drifted columns per month, then combine with
  `unionByName(allowMissingColumns=False)` before writing.
  `allowMissingColumns=False` is intentional: feature 003's full-schema
  comparison found the only real deviations are the two type-family casts
  handled above (casing-only differences like `airport_fee`/`Airport_fee`
  are excluded by design) — no column is genuinely missing in any month,
  so silently allowing missing columns here would hide a real problem
  instead of failing fast (FR-008).
- **Rationale**: Feature 003 deliberately read files separately to keep
  each month's metrics attributable and to avoid a premature union masking
  schema differences it needed to *measure*. This feature's job is the
  opposite: schema differences are now known and are being *resolved*, so
  producing one physically unioned table is the actual deliverable (SC-002).
- **Alternatives considered**: Keeping 5 separate per-month tables and
  presenting a view — rejected, adds a second abstraction (view + 5
  tables) for no benefit over one physical table at this data volume
  (~16.2M rows total), contrary to Principle VI.

## 4. Ingestion metadata columns and duplicate detection (FR-004, FR-005)

- **Decision**: Add `_source_file` via `pyspark.sql.functions.input_file_name()`
  immediately after reading each month (i.e. before the union) — this
  function only resolves reliably when evaluated close to the file read,
  before any shuffle. Add `_ingested_at` via a single `current_timestamp()`
  value applied once to the whole batch. Then run
  `.dropDuplicates(subset=<original_source_columns>)` on the unioned
  DataFrame, **explicitly excluding** `_source_file` and `_ingested_at`
  from the subset. Report `rows_before_dedup - rows_after_dedup` as the
  removed-duplicate count.
- **Rationale**: An earlier draft of this decision assumed
  `_source_file`/`_ingested_at` had to be added *after* dedup to avoid
  breaking duplicate detection — but `input_file_name()` must actually be
  captured *before* the union/dedup shuffle to resolve correctly at all
  (Spark loses the per-partition file context after a shuffle, and would
  otherwise return an empty string for every row). Reconciling both
  constraints: add both metadata columns early (correct for
  `input_file_name()`), but pass an explicit `subset` of only the original
  source columns to `dropDuplicates()`, so the metadata columns can't
  accidentally make every row look unique. This is the only ordering that
  is both technically correct and satisfies FR-005's "full-row duplicate"
  definition from feature 003 (0 found per month).
- **Alternatives considered**: Adding metadata columns after dedup (no
  `subset` needed) — rejected once we confirmed `input_file_name()`
  requires evaluation before the union's shuffle to stay accurate.
  Deduplicating per-month before the union — equivalent result for this
  dataset (0 duplicates found per month in feature 003) but rejected as an
  unnecessary extra pass when one `dropDuplicates(subset=...)` over the
  combined DataFrame covers both intra- and cross-file duplicates in one
  step.

## 5. Where the ingestion run report is persisted (FR-007)

- **Decision**: A new `specs/004-bronze-layer/ingestion-log.md`, authored
  during implementation from the script's JSON output (`rows_read`,
  `rows_written`, `duplicates_removed`, `schema_validation_status`,
  `executed_at`) — same convention as feature 003's `findings.md`.
- **Rationale**: Keeps a versioned, reviewable record of this one-time
  load's volume accounting without waiting for feature 007's full
  `_pipeline_run_log` Delta table, matching FR-007's narrower ask (this
  feature's own auditability, not the durable multi-run log).
- **Alternatives considered**: Writing straight into feature 007's future
  `_pipeline_run_log` table now — rejected as scope creep; that table's
  design (schema, retention, multi-run querying) belongs to feature 007,
  not this one.

## 6. Fail-fast schema validation (FR-008)

- **Decision**: Before casting/unioning, assert that each month's raw
  schema contains exactly the column set and type-family shape documented
  in feature 003's findings (19 columns, with `passenger_count`/
  `ratecodeid` as the only type-family deviations). If any file's schema
  doesn't match, raise an exception and let the job fail visibly rather
  than proceeding.
- **Rationale**: This feature's cast logic (decision 2) is derived
  entirely from the known 5-month comparison — silently applying it to an
  unanticipated 6th schema variant could produce wrong or null data
  instead of an honest failure.
- **Alternatives considered**: Best-effort casting with a warning log
  instead of a hard failure — rejected, contradicts FR-008's explicit
  "MUST fail" requirement and this dataset's one-time, fully-known scope
  (there's no operational reason to prefer degraded output over a loud
  failure here).

## 7. Execution mechanism (consistent with features 002-003)

- **Decision**: Both scripts (`rename_landing_schema.py`,
  `ingest_bronze.py`) are written in Databricks notebook-source format,
  imported into the workspace, and run via `databricks jobs submit`
  (serverless compute) — same mechanism as every prior feature.
- **Rationale**: The landing volume is only reachable from inside the
  workspace; reusing the proven mechanism avoids a second execution
  pattern for no reason (Constitution Principle VI).
