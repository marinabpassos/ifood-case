# Phase 0 Research: Data Quality & Camada Silver

**Input**: [spec.md](./spec.md) · Constitution `.specify/memory/constitution.md` ·
`contracts/nyc_taxi_silver.yaml` (feature 005) · feature 004's `ingestion-log.md`

No `[NEEDS CLARIFICATION]` markers remain in the spec. The items below
are planning-phase technical decisions needed to turn the spec's
requirements into an implementable design.

## 1. Contract-driven rule application (FR-003)

- **Decision**: Load `contracts/nyc_taxi_silver.yaml` at runtime with
  `PyYAML`, and for each of the 4 drop rules, build its filter directly
  from the YAML's own `condition` string via `pyspark.sql.functions.expr(condition)`
  — not a hand-written, hardcoded Python/Spark equivalent of each
  condition.
- **Rationale**: The `condition` field was added to the contract
  specifically during feature 005's `/speckit-analyze` pass "to
  strengthen SC-004... a stated condition is more directly implementable
  than rationale prose alone." Actually executing that condition string
  (rather than re-encoding the same logic by hand in Python) is what
  makes Constitution Principle II's "the contract is not
  documentation-only" concrete: change the YAML's condition, and the
  pipeline's behavior changes without a code edit.
- **Alternatives considered**: Hardcoding each of the 4 conditions
  directly as PySpark filter expressions in `build_silver.py`, treating
  the contract as a human-readable reference only — rejected; it would
  leave two sources of truth for the same 4 conditions (the YAML string
  and the hand-written Python), which could silently drift apart, and
  would make the `condition` field itself decorative rather than
  load-bearing.

## 2. Independent per-rule counting must run against the full input

- **Decision**: For each of the 4 rule conditions, compute a boolean
  column against the *original*, unfiltered bronze DataFrame (e.g.
  `df.withColumn("_fails_total_amount_rule", F.expr(condition))` for
  each rule, all four added before any row is removed). Each rule's
  reported count is `df.filter(col(f"_fails_{rule_id}")).count()`. The
  combined drop mask is the logical OR of all 4 boolean columns; the
  final written table is `df.filter(~combined_mask).select(<6 contract
  columns>)`; the total-dropped count is `df.filter(combined_mask).count()`.
- **Rationale**: This is the only implementation consistent with the
  contract's own `counting: independent` declaration and its "counts may
  overlap" language (feature 005) — a sequential/chained filter (drop
  rule 1's failures, then evaluate rule 2 only on the remainder) would
  make later rules' counts artificially smaller and dependent on
  execution order, contradicting "independent" and breaking spec SC-003's
  verification target (each count must equal feature 004's already-known
  bronze-layer population count exactly).
- **Alternatives considered**: Sequential chained filtering (simpler
  code, one `.filter()` per rule applied in sequence) — rejected exactly
  because it cannot reproduce SC-003's expected numbers; a row dropped by
  an earlier rule would never be counted by a later rule it also fails,
  even though "independent" counting requires it to be.

## 3. Schema-compatibility assertion (FR-002)

- **Decision**: Reuse the type-family classification approach already
  established in features 003/004 (`type_family()`: integer/floating/
  string/timestamp_or_date/boolean). Map each contract business type to
  an accepted Spark family: `integer` → `integer`, `decimal` →
  `floating`, `timestamp` → `timestamp_or_date`. For each of the 5
  contract-declared business columns (excluding `_silver_processed_at`,
  which doesn't exist in bronze yet), confirm the column exists in
  bronze and its type family matches the contract's declared type.
  Raise an exception and let the job fail if any column is missing or
  its family doesn't match.
- **Rationale**: Bronze's actual schema (feature 004:
  `VendorID`=bigint, `passenger_count`=int, `total_amount`=double, both
  timestamps=timestamp_ntz) already satisfies this by construction, so
  this check should pass silently on the current data — its value is
  catching *future* drift (e.g. if bronze were ever rebuilt with a
  differently-typed column) before it silently produces a wrong silver
  table, per Principle II's schema-assertion requirement.
- **Alternatives considered**: Exact type equality instead of type-family
  matching — rejected, would make this assertion fail on harmless
  differences (e.g. `int` vs `bigint`, both "integer") the same way an
  exact match was rejected in features 003/004's schema comparison.

## 4. Schema creation before write

- **Decision**: `CREATE SCHEMA IF NOT EXISTS ifood_case.silver` runs
  before the table write, every time.
- **Rationale**: Feature 004 hit `SCHEMA_NOT_FOUND` on its first real
  run precisely because a schema didn't exist yet and nothing created
  it — `ifood_case.silver` doesn't exist yet either (only `bronze`,
  `landing`, `default`, `information_schema` do). Applying that same
  fix proactively here avoids repeating a known failure mode.
- **Alternatives considered**: Assuming the schema already exists —
  rejected; confirmed via `databricks schemas list ifood_case` (feature
  004/005 sessions) that no `silver` schema exists yet.

## 5. `_silver_processed_at` value

- **Decision**: A single `current_timestamp()` value computed once and
  applied to every row in the batch, added after the rule-evaluation
  columns are dropped (so it never participates in any rule condition).
- **Rationale**: Same reasoning as bronze's `_ingested_at` (feature 004)
  — one run, one shared timestamp, not a per-row evaluation.

## 6. Where the data-quality run report is persisted

- **Decision**: A new `specs/006-silver-data-quality/dq-run-log.md`,
  authored during implementation from the script's JSON output
  (`rows_read`, `rows_written`, 4 named per-rule counts,
  `total_dropped`, `schema_assertion_status`, `executed_at`) — same
  convention as feature 004's `ingestion-log.md`.
- **Rationale**: Versioned, reviewable evidence for SC-003's exact-match
  claim against feature 004's numbers, without waiting for feature 007's
  full `_pipeline_run_log` table.
- **Alternatives considered**: Writing directly into feature 007's future
  `_pipeline_run_log` table now — rejected as scope creep, same reasoning
  as feature 004's research.md §5.

## 7. Execution mechanism (consistent with features 002-004)

- **Decision**: `build_silver.py` is written in Databricks
  notebook-source format, imported into the workspace, and run via
  `databricks jobs submit` (serverless compute) — same mechanism as
  every feature except 005 (which needed no platform access at all).
- **Rationale**: Both the source (bronze) and destination (silver)
  tables only exist inside the Databricks workspace; reusing the proven
  mechanism avoids a second execution pattern for no reason (Constitution
  Principle VI).
