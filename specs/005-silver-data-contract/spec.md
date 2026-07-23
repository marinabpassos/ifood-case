# Feature Specification: Contrato de Dados da Silver

**Feature Branch**: `005-silver-data-contract`

**Created**: 2026-07-23

**Status**: Draft

**Input**: User description: "feature 005 - Contrato de Dados da Silver: contracts/nyc_taxi_silver.yaml (schema, grão, regras de qualidade, SLA, versionamento) escrito antes do código de escrita da tabela (Constituição, Princípio II)"

## Clarifications

### Session 2026-07-23

- Q: The 5 required columns don't guarantee lineage back to source files the way bronze's `_source_file`/`_ingested_at` do — should silver inherit those columns, have none, or add its own equivalent? → A: Drop bronze's inherited `_source_file`/`_ingested_at`, but add a new silver-specific `_silver_processed_at` timestamp column (own audit trail for the silver write, not carried over from bronze) — 6 columns total (5 required + 1 audit column).
- Q: When a row fails more than one data-quality rule at once (e.g. negative `total_amount` AND an out-of-range date), should each rule's dropped-row count be independent (may overlap, sum can exceed total dropped) or mutually exclusive (each row attributed to exactly one rule by priority order)? → A: Independent — same approach feature 003's profiling already used (each defect reported in isolation, no arbitrary priority order invented). Total rows dropped (logical OR across all rules, no double-counting) is reported as a separate metric.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - A reader knows exactly what the silver table looks like before it exists (Priority: P1)

As a data consumer (analyst, evaluator, or the feature 006 implementer), I
need a single declarative document that states the silver table's exact
column list, types, nullability, and business meaning, so I can know
precisely what to expect from `ifood_case.silver.yellow_taxi_trips`
without reading pipeline code or waiting for the table to be built.

**Why this priority**: This is the core deliverable Principle II requires
— a contract written *before* the table-writing code, not derived from
whatever the code happens to produce. Every other part of this feature
(quality rules, SLA, versioning) is additional detail on top of this
schema declaration.

**Independent Test**: Read `contracts/nyc_taxi_silver.yaml` alone and
answer "what are the columns, their types, and can each be null?" — the
answer must be complete and unambiguous without consulting any other file.

**Acceptance Scenarios**:

1. **Given** the case brief's 5 required columns (`VendorID`,
   `passenger_count`, `total_amount`, `tpep_pickup_datetime`,
   `tpep_dropoff_datetime`), **When** the contract is read, **Then** each
   one has an explicit type, a nullability declaration, and a one-line
   business description — no column is left implicit.
2. **Given** the contract exists, **When** compared to the case brief's
   note that "demais colunas podem ser ignoradas," **Then** the contract
   contains only these 5 columns plus one silver-specific audit column
   (`_silver_processed_at`) — no bronze-layer passthrough column (e.g.
   `trip_distance`, `PULocationID`) and none of bronze's own metadata
   columns (`_source_file`, `_ingested_at`) are carried into the silver
   schema declaration (2026-07-23 clarification).

---

### User Story 2 - Feature 006 has an unambiguous data-quality specification to implement (Priority: P2)

As the implementer of feature 006 (Data Quality & Camada Silver), I need
every known data-quality defect to have a declared, reasoned policy
(drop, flag, or keep) in the contract, so I'm implementing a deliberate
decision instead of inventing one mid-pipeline.

**Why this priority**: Depends on User Story 1's column list existing
first (a rule needs to reference a column), but is the second most
important part of the contract — Principle I requires these rules to be
explicit and reported by volume, and Principle II requires the contract
to carry them, not just the code.

**Independent Test**: For each of the 5 data-quality risks named in the
constitution (negative/zero `total_amount`, null/zero `passenger_count`,
`dropoff` before `pickup`, out-of-range dates, duplicates), confirm the
contract states a policy and a rationale, independent of whether feature
006 has implemented it yet.

**Acceptance Scenarios**:

1. **Given** feature 003's profiling found `total_amount` negative-or-zero
   in every month (~144,146 rows across all 5 months) and `passenger_count`
   null-or-zero in every month (~702,146 rows across all 5 months),
   **When** the contract is read, **Then** it states explicitly whether
   these rows are dropped, flagged, or kept in silver, with a one-line
   business rationale for the choice.
2. **Given** feature 004's bronze layer measured 795 rows where
   `tpep_dropoff_datetime` is before `tpep_pickup_datetime` (the first
   measurement of this condition in the pipeline — no feature 003
   baseline existed), **When** the contract is read, **Then** it states
   the same kind of explicit policy for this condition.
3. **Given** out-of-range dates (1,077 rows across all 5 months, per
   feature 003) and full-row duplicates (0 found, already removed at the
   bronze layer per feature 004), **When** the contract is read, **Then**
   it states that duplicates are already resolved upstream (bronze) and
   states an explicit policy for out-of-range dates.

---

### User Story 3 - The contract signals operational maturity even for a one-time load (Priority: P3)

As the case evaluator, I need the contract to declare a grain, an
update-frequency/SLA, and a version with a breaking-change policy — even
though the actual data load here is a single Jan-May 2023 batch — so the
contract reads as production-grade documentation, not a one-off note.

**Why this priority**: Lowest priority because it doesn't block feature
006's implementation the way User Stories 1-2 do, but it's an explicit,
named requirement from the case brief's guidance on "reforça maturidade
da solução" and ties directly to Constitution Principle II's mandatory
contract fields.

**Independent Test**: Read the contract's grain, SLA, and version sections
in isolation and confirm each is a concrete, non-vague statement (not
"TBD" or "as needed").

**Acceptance Scenarios**:

1. **Given** the source data has no natural single-column identifier for
   a trip, **When** the contract declares its grain, **Then** it states
   "one row = one trip event" explicitly and documents that no formal
   uniqueness constraint is enforced on the 5-column silver schema alone
   (see Edge Cases).
2. **Given** this project's actual load is one-time (Jan-May 2023),
   **When** the contract declares SLA/update frequency, **Then** it
   describes a hypothetical recurring (e.g. monthly) cadence as if the
   pipeline were ongoing, per the case brief's guidance.
3. **Given** the contract is versioned, **When** a future change is
   proposed (e.g. removing a column), **Then** the contract's own
   breaking-change policy determines whether that requires a new major
   version.

---

### Edge Cases

- The 5 required columns alone do not guarantee row uniqueness (e.g. two
  distinct trips could coincidentally share the same `VendorID`,
  timestamps, `passenger_count`, and `total_amount`). The contract MUST
  state this explicitly rather than implying a primary key that doesn't
  actually exist — silver's only inherited uniqueness guarantee is
  bronze's full-row dedup over all 19 source columns (feature 004),
  which is a stronger check than anything re-derivable from the 5
  narrowed columns alone.
- If a future month's data is missing one of the 5 required columns
  entirely, that is a contract-breaking condition (not silently
  tolerated) — feature 006's schema assertion (Principle II) must fail
  loudly, per this contract's breaking-change policy.
- If the drop-based quality rules (User Story 2) ever remove 100% of a
  month's rows, that's an anomaly the contract's rules alone can't catch
  — that belongs to feature 007's observability threshold alerting, not
  this contract.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The contract MUST declare the silver table's full identity:
  catalog, schema, table name (`ifood_case.silver.yellow_taxi_trips`), and
  owner.
- **FR-002**: The contract MUST declare an explicit column-level schema
  for exactly the 5 required columns (`VendorID`, `passenger_count`,
  `total_amount`, `tpep_pickup_datetime`, `tpep_dropoff_datetime`) — type,
  nullability, and a one-line business description each — plus one new
  silver-specific audit column, `_silver_processed_at` (timestamp,
  non-nullable, own audit trail for the silver write). No bronze-layer
  passthrough column and none of bronze's own metadata columns
  (`_source_file`, `_ingested_at`) are inherited (2026-07-23
  clarification).
- **FR-003**: The contract MUST declare the table's grain ("one row = one
  trip event") and explicitly state that no formal uniqueness constraint
  is enforced on the 5-column silver schema alone (see Edge Cases).
- **FR-004**: The contract MUST declare an explicit, reasoned policy
  (drop, flag, or keep) for every data-quality risk named in the
  constitution: `total_amount` negative/zero, `passenger_count`
  null/zero, `tpep_dropoff_datetime` before `tpep_pickup_datetime`,
  out-of-range dates (outside Jan 1 - May 31, 2023), and duplicates
  (already resolved at the bronze layer, per feature 004). Rows failing
  more than one rule simultaneously MUST be counted independently under
  each rule they fail (counts may overlap and their sum may exceed the
  total rows dropped); the contract MUST also require a separate "total
  rows dropped" metric (rows failing at least one rule, counted once
  each, no double-counting) (2026-07-23 clarification).
- **FR-005**: The contract MUST declare an update frequency/SLA,
  described as if the pipeline were recurring (e.g. monthly), even though
  the actual load for this case is a single Jan-May 2023 batch.
- **FR-006**: The contract MUST declare a version identifier (starting at
  `v1`) and a breaking-change policy (what kind of future change requires
  a new major version vs. a minor/patch one).
- **FR-007**: The contract MUST exist as a declarative, versioned file in
  the repository (`contracts/nyc_taxi_silver.yaml`) — not embedded only in
  pipeline code or a chat/notebook artifact.
- **FR-008**: This feature MUST NOT write, alter, or create the silver
  table itself, and MUST NOT apply any data-quality rule to any table —
  it produces the contract document only. Applying these rules against
  real data is feature 006's scope.

### Key Entities

- **Silver Data Contract**: the declarative document itself — table
  identity, the 6-column schema (5 required business columns + 1
  silver-specific audit column, `_silver_processed_at`), grain
  declaration, the 5 data-quality rule policies, SLA, and
  version/breaking-change policy. Lives at
  `contracts/nyc_taxi_silver.yaml`. Not a physical table — a specification
  for one.
- **Contract Validation Result**: the ephemeral output of running the
  structural validator locally — whether the contract is structurally
  complete, and which checks (if any) failed. Not persisted anywhere; no
  pipeline execution to log (FR-008).

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A reader can state the exact column list, type, and
  nullability of every silver column from the contract alone, with 100%
  of the 6 columns covered (5 required business columns + the
  `_silver_processed_at` audit column) — no pipeline code needed.
- **SC-002**: All 5 constitution-named data-quality risks (negative/zero
  `total_amount`, null/zero `passenger_count`, `dropoff` before `pickup`,
  out-of-range dates, duplicates) have an explicit, reasoned policy in
  the contract — zero risks left undecided or implicit. The contract
  distinguishes independent per-rule counts from the single "total rows
  dropped" count, so a reader never has to guess whether the numbers are
  meant to sum to the total.
- **SC-003**: The contract declares a version and breaking-change policy
  specific enough that a reader can determine, for any hypothetical
  future schema change (e.g. "remove `VendorID`," "add `trip_distance`"),
  whether it would require a new major version — without needing to ask
  the contract's author.
- **SC-004**: Feature 006 can be implemented directly from this
  contract's content alone, with no additional data-quality or schema
  decision left for that feature to invent.

## Assumptions

- This feature depends on features 003 (profiling findings) and 004
  (bronze layer, including the bronze-layer measurement of `dropoff`
  before `pickup`), both complete.
- **Quality-rule policy decided in this spec**: all 4 business-judgment
  data-quality risks (`total_amount` negative/zero, `passenger_count`
  null/zero, `dropoff` before `pickup`, out-of-range dates) are policed
  as **drop, with the dropped row count reported per rule** (not flag,
  not keep). Rationale: all 4 conditions describe rows that cannot
  represent a real, valid taxi trip within this case's Jan-May 2023
  scope (a negative fare, a trip with no passengers, a trip that ends
  before it starts, or a date outside the analysis window), and the
  case's two analytical questions (average `total_amount` per month,
  average `passenger_count` by hour) are cleaner and more representative
  of real fleet activity computed over valid rows only. The 5th risk
  (duplicates) requires no silver-layer policy — bronze already
  deduplicates on ingestion (feature 004), so silver inherits a
  duplicate-free input.
- The contract format is a self-authored YAML structure (not a strict
  implementation of the external Data Contract Specification) per
  `DECISOES_PROJETO.md` §6's explicit allowance for "algo mais simples,
  próprio, se preferir menos overhead."
- Column types in the contract are declared as business-level types
  (integer, decimal, timestamp) rather than Spark-specific types — the
  contract is a business/consumption-facing document; feature 006 maps
  these to concrete Spark types during implementation.
- SLA/update-frequency content is illustrative (this project's real load
  is one-time), per `DECISOES_PROJETO.md` §6's explicit instruction to
  document it "como se fosse recorrente."
- **Breaking-change semver semantics** (FR-006): standard semantic
  versioning applies — removing/renaming a column, narrowing a column's
  type, or changing a data-quality rule's policy (e.g. drop → keep) is a
  MAJOR change; adding a new optional column is MINOR; wording/description
  -only edits are PATCH. This is a conventional default, not a
  case-specific decision requiring clarification.
