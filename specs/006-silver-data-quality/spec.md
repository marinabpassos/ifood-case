# Feature Specification: Data Quality & Camada Silver

**Feature Branch**: `006-silver-data-quality`

**Created**: 2026-07-23

**Status**: Draft

**Input**: User description: "feature 006 - Data Quality & Camada Silver: aplica as regras de DQ definidas no contrato (feature 005) sobre a bronze (feature 004), escreve a tabela Delta silver tipada e limpa"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Only valid trips reach the analytical layer (Priority: P1)

As the case author, I need the silver table to contain only rows that
represent a real, valid taxi trip — no negative/zero fares, no
null/zero passenger counts, no trips that end before they start, no
dates outside the Jan-May 2023 scope — so the case's two analytical
questions (average `total_amount` per month, average `passenger_count`
by hour in May) are computed over data that actually reflects fleet
activity, not known data defects.

**Why this priority**: This is the entire reason the silver layer
exists — Constitution Principle I gates silver-layer modeling on this
exact cleaning step, and it's the reason features 003 (profiling) and
005 (contract) were done first. Nothing else in this feature matters if
invalid rows still reach silver.

**Independent Test**: Query `ifood_case.silver.yellow_taxi_trips` for
each of the 4 drop conditions declared in `contracts/nyc_taxi_silver.yaml`
and confirm zero matching rows, independent of the schema-assertion or
reporting stories.

**Acceptance Scenarios**:

1. **Given** bronze contains rows with `total_amount <= 0` (144,146
   across all 5 months, per feature 004's `ingestion-log.md`) and rows
   with null/zero `passenger_count` (702,146 across all 5 months),
   **When** the silver table is written, **Then** none of those rows
   are present in `ifood_case.silver.yellow_taxi_trips`.
2. **Given** bronze contains 795 rows where `tpep_dropoff_datetime` is
   before `tpep_pickup_datetime` and 1,077 rows outside the Jan 1 - May
   31, 2023 window (both per feature 004's `ingestion-log.md`), **When**
   the silver table is written, **Then** none of those rows are present
   either.
3. **Given** bronze already deduplicated full-row duplicates during
   ingestion (feature 004, 0 found), **When** silver is written, **Then**
   no additional dedup logic runs — silver simply inherits bronze's
   already-duplicate-free input, per the contract's
   `duplicates: resolved_upstream` policy.

---

### User Story 2 - The written table matches the contract exactly (Priority: P2)

As the implementer, I need the pipeline to assert bronze's actual schema
against `contracts/nyc_taxi_silver.yaml`'s declared columns before
writing anything, and to write exactly the contract's 6 columns (no
more, no fewer), so the contract from feature 005 is enforced, not just
described.

**Why this priority**: Directly satisfies Constitution Principle II's
mandate that "the pipeline MUST assert the contract... before writing to
the silver table — the contract is not documentation-only." Depends on
User Story 1's cleaning logic existing (the assertion runs against the
same data path), so it's sequenced second.

**Independent Test**: Compare `DESCRIBE TABLE ifood_case.silver.yellow_taxi_trips`
against `contracts/nyc_taxi_silver.yaml`'s `columns` list, independent of
the row-level cleaning outcome.

**Acceptance Scenarios**:

1. **Given** `contracts/nyc_taxi_silver.yaml` declares 6 columns
   (`VendorID`, `passenger_count`, `total_amount`,
   `tpep_pickup_datetime`, `tpep_dropoff_datetime`,
   `_silver_processed_at`), **When** the silver table is written,
   **Then** it has exactly these 6 columns — no bronze passthrough
   column and none of bronze's own `_source_file`/`_ingested_at`
   metadata columns are present.
2. **Given** bronze's actual schema no longer matches what the contract
   assumes (e.g. a required column is missing or has an incompatible
   type), **When** the pipeline runs, **Then** it fails explicitly before
   writing anything, rather than silently producing a wrong table.

---

### User Story 3 - Every rule's impact is measured and reported (Priority: P3)

As the case evaluator, I need the volume of rows affected by each
data-quality rule reported — independently per rule, plus a separate
total-dropped count — so the cleaning decisions are backed by evidence,
matching the counting semantics `contracts/nyc_taxi_silver.yaml` already
declares, not just asserted in prose.

**Why this priority**: Lowest priority because it doesn't change what
ends up in the table (User Stories 1-2 already determine that) — it's
about making the *evidence* for that outcome visible, satisfying
Constitution Principle I's "MUST report the volume of records affected or
removed."

**Independent Test**: Run the pipeline and confirm a report exists with
all 4 independent per-rule counts and one total-dropped count,
independent of what the actual numbers turn out to be.

**Acceptance Scenarios**:

1. **Given** each of the 4 drop rules is evaluated independently against
   the full bronze input (not sequentially against an already-shrinking
   set), **When** the pipeline runs, **Then** each rule's reported count
   matches the same condition's count already established in bronze
   (feature 004's `ingestion-log.md`): 144,146 / 702,146 / 795 / 1,077 —
   confirming silver re-derives the same population bronze already
   measured, rather than a different (sequentially-biased) number.
2. **Given** some rows fail more than one rule at once, **When** the
   total-dropped count is computed, **Then** it counts each such row
   once (logical OR across the 4 rules), and is therefore less than or
   equal to the sum of the 4 independent counts and at least as large as
   the largest single rule's count.

---

### Edge Cases

- If bronze's schema has drifted since feature 004 in a way the contract
  doesn't anticipate (a required column missing or retyped), the
  pipeline MUST fail explicitly during the schema assertion (User Story
  2), not silently coerce or drop the mismatched column.
- If a single rule's independent count exceeds a large share of a
  month's rows (e.g. >50%), that's an anomaly worth surfacing, but the
  actual alerting mechanism (a defined threshold triggering a visible
  alert) is feature 007's scope — this feature only needs to report the
  number accurately, not decide when a number is "too high."
- If the silver table already exists from a prior run, writing again
  MUST replace it cleanly (idempotent overwrite), not append duplicate
  data — consistent with how feature 004's bronze write behaves.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The pipeline MUST read exclusively from
  `ifood_case.bronze.yellow_taxi_trips` (feature 004) — not the landing
  zone, not raw parquet files.
- **FR-002**: Before writing anything, the pipeline MUST assert bronze's
  actual schema is compatible with the column types
  `contracts/nyc_taxi_silver.yaml` declares, and fail explicitly (not
  silently coerce) if it isn't.
- **FR-003**: The pipeline MUST apply exactly the 4 drop rules declared
  in the contract (`total_amount_negative_or_zero`,
  `passenger_count_null_or_zero`, `dropoff_before_pickup`,
  `out_of_range_dates`). Each rule's dropped-row count MUST be computed
  independently against the full bronze input (not sequentially against
  a set already reduced by an earlier rule), per the contract's
  `counting: independent` declaration.
- **FR-004**: The pipeline MUST NOT implement any duplicate-detection or
  removal logic of its own — duplicates are already resolved at the
  bronze layer (feature 004), matching the contract's
  `duplicates: resolved_upstream` policy.
- **FR-005**: The pipeline MUST add `_silver_processed_at` (a single
  timestamp value for the entire write) and MUST NOT carry over bronze's
  `_source_file`/`_ingested_at` columns.
- **FR-006**: The written table (`ifood_case.silver.yellow_taxi_trips`)
  MUST contain exactly the 6 columns `contracts/nyc_taxi_silver.yaml`
  declares — no more, no fewer — with matching types and nullability.
- **FR-007**: The pipeline MUST report, at minimum: rows read (from
  bronze), rows written (to silver), each of the 4 rules' independent
  dropped-row counts, and one separate total-rows-dropped count (logical
  OR across the 4 rules, no double-counting) — this feature's own
  auditable evidence, without waiting for feature 007's full
  observability layer.
- **FR-008**: This feature MUST NOT modify
  `contracts/nyc_taxi_silver.yaml` — it implements the already-decided
  contract from feature 005, it does not redecide its rules or schema.

### Key Entities

- **Silver Trip Record**: one row per valid trip, grain = one trip
  (inherited from the contract). Exactly the 6 contract columns; every
  row already satisfies all 4 drop rules by construction (no row in this
  table can have a negative/zero `total_amount`, null/zero
  `passenger_count`, `dropoff` before `pickup`, or an out-of-range date).
- **Silver Data Quality Run**: this feature's own execution record —
  rows read, rows written, the 4 independent per-rule dropped counts,
  the total-dropped count, schema-assertion status. Same role feature
  004's "Bronze Ingestion Run" played for the bronze layer; not the
  durable `_pipeline_run_log` table (feature 007's scope).

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Querying `ifood_case.silver.yellow_taxi_trips` for any of
  the 4 drop conditions returns zero rows — 100% of known invalid rows
  excluded.
- **SC-002**: `DESCRIBE TABLE ifood_case.silver.yellow_taxi_trips`
  matches `contracts/nyc_taxi_silver.yaml`'s declared 6 columns exactly
  — no extra column, no missing column, matching types/nullability.
- **SC-003**: Each of the 4 independent per-rule dropped-row counts
  matches the same condition's count already established at the bronze
  layer (feature 004): 144,146 / 702,146 / 795 / 1,077 — proving silver's
  cleaning re-derives the same population bronze already measured. The
  separate total-dropped count is reported and falls between the largest
  single rule's count and the sum of all 4.
- **SC-004**: The silver table is usable for both of the case's
  analytical questions (average `total_amount` per month; average
  `passenger_count` by hour in May) with a direct aggregation query — no
  further cleaning step needed by feature 008 (Análises Analíticas).

## Assumptions

- This feature depends on features 004 (bronze layer) and 005 (silver
  data contract), both complete and merged.
- Independent per-rule counting (FR-003, per the contract's own
  `counting: independent` declaration) requires evaluating all 4 rule
  conditions against the same, full bronze input before any row is
  removed — not a sequential/chained filter where each rule only sees
  the rows the previous rule left behind. This is what makes "counts may
  overlap" (the contract's own language) possible and testable (SC-003).
- The actual alerting mechanism for an unusually high drop rate (a
  defined threshold triggering a visible alert, per Constitution
  Principle III) is out of scope here — this feature reports accurate
  numbers; feature 007 decides what counts as "too high" and how to
  surface it.
- Business-level types from the contract (`integer`, `decimal`,
  `timestamp`) are mapped to concrete Spark types during implementation
  — the contract intentionally stays technology-agnostic (feature 005's
  research.md §3).
