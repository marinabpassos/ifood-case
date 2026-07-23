# Feature Specification: Camada Bronze

**Feature Branch**: `004-bronze-layer`

**Created**: 2026-07-23

**Status**: Draft

**Input**: User description: "Feature 004 - Camada Bronze. Renomear o schema `ifood_case.bronze` (que hoje contém só o Volume de landing, feature 002) para `ifood_case.landing`, preservando o volume `yellow_taxi_raw`; criar a tabela Delta `ifood_case.bronze.yellow_taxi_trips` a partir da landing, com ingestão 1:1 dos 5 meses, cast de schema consistente entre meses, colunas técnicas de ingestão (_source_file, _ingested_at), e dedup de linhas 100% idênticas — sem nenhuma regra de qualidade de negócio."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Landing zone keeps its own namespace, separate from bronze (Priority: P1)

As the case author, I need the existing raw-file location to live under a
`landing` schema (not `bronze`), so the `bronze` name is free to hold the
new Delta table without colliding with the already-landed files.

**Why this priority**: Nothing else in this feature can proceed without a
naming collision — the schema currently called `bronze` (feature 002)
holds only the Volume with the 5 landed files. This rename must happen
first and cleanly, or every later step in this feature builds on an
ambiguous location.

**Independent Test**: After the rename, the same 5 parquet files are
listable and byte-identical to their originals at the new location, with
no data loss or path breakage — independent of whether the bronze table
has been created yet.

**Acceptance Scenarios**:

1. **Given** the schema `ifood_case.bronze` today contains only the volume
   `yellow_taxi_raw` (5 landed files, feature 002), **When** it is renamed
   to `ifood_case.landing`, **Then** all 5 files remain listable at
   `/Volumes/ifood_case/landing/yellow_taxi_raw/` with unchanged file sizes
   (byte-identical to the originals confirmed in feature 002).
2. **Given** the rename has completed, **When** anything still references
   the old `ifood_case.bronze.yellow_taxi_raw` path, **Then** that
   reference MUST fail or be updated — no silent dual-path ambiguity
   between an old and new location (same principle as feature 002 FR-003).

---

### User Story 2 - A consistent-schema Delta table exists for the 5 months combined (Priority: P2)

As the case author, I need the 5 monthly raw files ingested into one Delta
table with a single, consistent schema, so later features (contract, data
quality, silver) read from a stable typed source instead of re-deriving
schema fixes from raw parquet every time.

**Why this priority**: This is the actual deliverable of the feature — the
reason bronze exists as a physical layer at all. It depends on User Story
1 (the `landing` schema must exist first as the read source).

**Independent Test**: Query `ifood_case.bronze.yellow_taxi_trips` and
confirm it contains all 5 months combined, with every type-drifted column
in one consistent type, and the two ingestion metadata columns present —
independent of the dedup or guardrail stories.

**Acceptance Scenarios**:

1. **Given** the 5 files in the landing zone, **When** bronze ingestion
   runs, **Then** `ifood_case.bronze.yellow_taxi_trips` contains rows from
   all 5 months, with `passenger_count` (float in 2023-01, integer in
   2023-02 through 2023-05, per feature 003 findings) in one consistent
   numeric type across every row.
2. **Given** a row originated from a specific month's file, **When** it
   lands in bronze, **Then** it carries `_source_file` (originating file
   name) and `_ingested_at` (ingestion timestamp) columns.
3. **Given** the total row count from feature 003 profiling (16,186,386
   across 5 months), **When** bronze ingestion completes, **Then** the
   bronze row count equals that number minus whatever exact-duplicate
   count User Story 3 reports — any other difference is a defect.

---

### User Story 3 - Exact duplicate rows are not carried into bronze (Priority: P3)

As the case author, I need full-row duplicate records — a rule already
defined and measured in feature 003 profiling (0 found across all 5
months) — to be actively removed during bronze ingestion, so bronze
doesn't silently carry technical duplication forward into later layers,
even though this dataset currently has none.

**Why this priority**: Lower than User Story 2 because feature 003 found
zero duplicates in this dataset — this is a defensive, completeness rule
rather than a fix for an active defect. It still needs to be explicit and
verifiable, matching the constitution's precedent that a rule is reported
by volume even when it affects zero rows.

**Independent Test**: Verify the dedup step executes and reports a
duplicate count (0, per current data), independent of the schema-cast
logic in User Story 2.

**Acceptance Scenarios**:

1. **Given** the 5 landed files (confirmed duplicate-free in feature 003),
   **When** bronze ingestion runs, **Then** the dedup step executes and
   reports 0 duplicate rows removed, consistent with feature 003's finding.
2. **Given** a full-row duplicate existed in a source file, **When**
   bronze ingestion runs, **Then** only one copy of that row reaches
   `ifood_case.bronze.yellow_taxi_trips`, and the removed-duplicate count
   is reported, not silently dropped.

---

### User Story 4 - Bronze applies no business-rule filtering (Priority: P4, guardrail)

As the case author, I need bronze to preserve every row that isn't an
exact technical duplicate — including rows with negative `total_amount`,
null/zero `passenger_count`, or out-of-range dates — so those business
data-quality decisions stay entirely in the silver layer (feature 006),
keeping the bronze/silver boundary clean per the constitution.

**Why this priority**: Lowest priority because it's a guardrail
(confirming the *absence* of behavior) rather than new functionality, but
it's the exact boundary this whole feature's design decision depends on,
so it must be independently verified, not just assumed from the code.

**Independent Test**: Compare row counts and known-defect rates between
bronze and the feature 003 profiling baseline — no rows should be missing
due to any business-rule condition.

**Acceptance Scenarios**:

1. **Given** feature 003 found 0.84%-0.92% of rows per month with
   negative/zero `total_amount`, **When** bronze ingestion runs, **Then**
   those rows are present in `ifood_case.bronze.yellow_taxi_trips`
   unfiltered, at the same rate.
2. **Given** feature 003 found 4.01%-4.60% of rows per month with
   null/zero `passenger_count`, **When** bronze ingestion runs, **Then**
   those rows are present in bronze unfiltered, at the same rate.
3. **Given** feature 003 found a small number of out-of-range-date rows
   per month, **When** bronze ingestion runs, **Then** those rows are
   present in bronze unfiltered.
4. **Given** no baseline for this condition exists yet anywhere in the
   pipeline (feature 003's profiling did not measure trip duration),
   **When** bronze ingestion runs, **Then** rows where
   `tpep_dropoff_datetime` is before `tpep_pickup_datetime` are present in
   bronze unfiltered, and this feature's own run establishes the first
   quantified count of this condition (rather than comparing against a
   feature 003 baseline that doesn't exist).

---

### Edge Cases

- If the schema rename (User Story 1) is interrupted partway (some objects
  moved, others not), the system MUST be left in — or recoverable to — a
  single unambiguous end state (fully renamed, or fully rolled back), never
  a half-renamed state where both `bronze` and `landing` appear to hold
  part of the volume.
- If a future file is landed later with a schema not seen during feature
  003's profiling (e.g. a third type variant, or a new column), bronze
  ingestion MUST fail explicitly rather than silently coercing or dropping
  data — this feature's type-cast logic is derived from the known 5-month
  schema comparison, not a general-purpose schema-evolution handler.
- If a column not covered by feature 003's known type-drift list
  (`passenger_count`, `ratecodeid`) unexpectedly has a type mismatch during
  actual ingestion, it MUST be flagged, not silently coerced or truncated.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The Unity Catalog schema currently named `ifood_case.bronze`
  (containing only the landing volume from feature 002) MUST be renamed to
  `ifood_case.landing`, preserving the volume `yellow_taxi_raw` and all 5
  landed files without data loss or path breakage.
- **FR-002**: A new Delta table `ifood_case.bronze.yellow_taxi_trips` MUST
  be created, containing the ingested content of all 5 monthly files from
  the landing zone.
- **FR-003**: Any column with a known type drift across the 5 months (per
  feature 003 findings: `passenger_count`, `ratecodeid`) MUST be cast to
  one consistent type across the entire bronze table.
- **FR-004**: Each row in bronze MUST carry ingestion metadata:
  `_source_file` (originating file name) and `_ingested_at` (ingestion
  timestamp).
- **FR-005**: Bronze ingestion MUST remove exact full-row duplicate
  records and report the count removed.
- **FR-006**: Bronze ingestion MUST NOT apply any business-rule filtering
  — rows with negative/zero `total_amount`, null/zero `passenger_count`,
  out-of-range dates, or `dropoff` before `pickup` MUST all be preserved
  in bronze unfiltered.
- **FR-007**: Bronze ingestion MUST report, at minimum, rows read from
  landing and rows written to bronze (and the delta between them, i.e.
  duplicates removed), so the volume accounting for this feature's own
  success criteria is auditable without waiting for feature 007's full
  observability layer.
- **FR-008**: If a source file's schema deviates from what feature 003
  profiling documented (an unexpected new column or type not among the
  known 5-month variations), bronze ingestion MUST fail explicitly rather
  than silently coercing or dropping data.

### Key Entities

- **Landing Zone (renamed)**: the same Volume from feature 002, now
  addressed as `ifood_case.landing.yellow_taxi_raw` instead of
  `ifood_case.bronze.yellow_taxi_raw`. No content change — a Unity Catalog
  namespace change only.
- **Bronze Trip Record**: one row per trip record, grain = one trip.
  Columns match the source schema with consistent types across all 5
  months, plus `_source_file` and `_ingested_at`. No business-quality
  flags or filters — those begin in silver (feature 006).
- **Bronze Ingestion Run**: a record of this feature's own ingestion
  execution — rows read, rows written, duplicates removed, schema
  validation status, execution timestamp (FR-007). Not a business entity;
  this feature's own auditable evidence of what happened.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: All 5 previously-landed files remain listable and
  byte-identical at the renamed `ifood_case.landing.yellow_taxi_raw`
  location — zero data loss from the rename.
- **SC-002**: `ifood_case.bronze.yellow_taxi_trips` contains all 5 months
  of data in one consistent schema — queryable with a single `SELECT`,
  with no per-month type casting needed by the reader.
- **SC-003**: The bronze row count equals the landing row count
  (16,186,386, per feature 003) minus the number of exact duplicates
  removed (expected 0, per feature 003's finding) — no unexplained row
  loss.
- **SC-004**: Every known data-quality-relevant condition from feature 003
  (negative/zero `total_amount`, null/zero `passenger_count`,
  out-of-range dates) is still present and countable in bronze at the same
  rate found during profiling — proving no business-rule filtering
  happened silently in this layer.

## Assumptions

- This feature depends on features 002 (landing zone) and 003 (data
  profiling findings), both complete.
- The two type-drift cases resolved here (`passenger_count`, `ratecodeid`)
  are the only ones expected, per feature 003's exhaustive full-schema
  comparison across every column; any other type mismatch encountered
  during actual ingestion is an explicit failure (FR-008), not silently
  handled.
- "Business-rule filtering" (out of scope for bronze) is exactly the 4
  rules named in the constitution/`DECISOES_PROJETO.md`: `total_amount`
  negative/zero, `passenger_count` null/zero, `dropoff` before `pickup`,
  and out-of-range dates. Full-row-duplicate removal is the one rule that
  IS in scope for bronze, per the 2026-07-23 brainstorming decision
  (`docs/superpowers/specs/2026-07-23-medallion-layering-design.md`) — it
  is classified as a technical/structural rule, not a business one.
- The schema rename (FR-001) is implemented as create-new + copy + verify
  + drop-old (research.md §1), not a metadata-only rename — confirmed via
  Databricks documentation that Unity Catalog has no `ALTER SCHEMA ...
  RENAME TO` statement on any tier (not a Free-Edition-specific
  restriction). This is the primary implementation path, not a
  conditional fallback, and it MUST be documented in `DECISOES_PROJETO.md`
  per Constitution Principle IV.
- No data-quality assertions or business-rule tests belong in this
  feature beyond schema-shape and volume checks — actual business DQ
  rules are feature 006's scope, formalized against the contract from
  feature 005.
