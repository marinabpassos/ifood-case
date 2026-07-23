# Phase 0 Research: Contrato de Dados da Silver

**Input**: [spec.md](./spec.md) · Constitution `.specify/memory/constitution.md` ·
`DECISOES_PROJETO.md` §6 · feature 003 findings · feature 004 ingestion-log

No `[NEEDS CLARIFICATION]` markers remain in the spec (resolved via
`/speckit-clarify`, 2026-07-23). The items below are planning-phase
technical decisions needed to turn the spec's requirements into a
concrete contract file and validator.

## 1. Contract YAML top-level structure

- **Decision**: `contracts/nyc_taxi_silver.yaml` uses six top-level keys:
  `contract` (name, version), `table` (catalog, schema, name, owner),
  `grain` (statement + uniqueness note), `columns` (list of exactly 6
  entries), `quality_rules` (list of exactly 5 entries), `sla`
  (frequency, latency target, note), and `versioning`
  (current_version, breaking_change_policy with `major`/`minor`/`patch`
  keys).
- **Rationale**: Maps 1:1 to Principle II's mandated fields (identity,
  schema, grain, quality rules, SLA, version/breaking-change policy) —
  nothing extraneous, nothing missing. A flat, predictable top-level
  shape is what makes the structural validator in decision 2 possible
  without a heavyweight schema library.
- **Alternatives considered**: Adopting the external Data Contract
  Specification's full structure — rejected per spec Assumptions
  (`DECISOES_PROJETO.md` §6 explicitly allows "algo mais simples,
  próprio, se preferir menos overhead"); that spec's structure is
  designed for multi-team, multi-consumer governance at a scale this
  one-table, one-author case doesn't need.

## 2. Validator scope: structural completeness, not data validation

- **Decision**: `src/contracts/validate_silver_contract.py` checks that
  the YAML parses and that: all 6 top-level keys are present; `columns`
  has exactly 6 entries, each with `name`/`type`/`nullable`/`description`;
  `quality_rules` has exactly 5 entries, each with `id`/`policy`/
  `rationale`; `sla` and `versioning` are non-empty; `versioning.current_version`
  matches a simple `vN` pattern. It does **not** connect to Databricks,
  read any table, or validate that real data conforms to the contract.
- **Rationale**: This feature's own FR-008 explicitly excludes applying
  rules against real data (that's feature 006). "Is the contract itself
  well-formed and complete" is fully checkable offline and is what this
  feature's Success Criteria (SC-001 through SC-004) actually ask for —
  a stronger validator here would just duplicate feature 006's future
  live-data schema assertion (Principle II), against Principle VI.
- **Alternatives considered**: A full JSON-Schema-based validator —
  rejected as unnecessary machinery for 6 fixed top-level keys; a plain
  Python function with explicit checks is more legible for a repo this
  size and avoids a new dependency.

## 3. Business-level column types

- **Decision**: `VendorID`: `integer`; `passenger_count`: `integer`;
  `total_amount`: `decimal`; `tpep_pickup_datetime` /
  `tpep_dropoff_datetime`: `timestamp`; `_silver_processed_at`:
  `timestamp`. Nullability is declared as the **post-cleaning**
  invariant: `passenger_count` and `total_amount` are `not nullable` and
  implicitly `> 0` (their quality rule drops any row violating this,
  per spec Assumptions), `VendorID`/both trip timestamps/
  `_silver_processed_at` are `not nullable` (feature 003/004 found zero
  nulls in the source for these already).
- **Rationale**: The contract describes what a reader gets *after* the
  data-quality rules run, not the raw bronze shape — that's the whole
  point of a consumption-layer contract per Principle II. Declaring
  `passenger_count` as merely "nullable" would be true of bronze but
  false of silver once feature 006 applies the drop rule.
- **Alternatives considered**: Declaring pre-cleaning nullability (mirror
  bronze) — rejected, would misrepresent what silver actually guarantees
  to a consumer, defeating the contract's purpose.

## 4. Execution mechanism (deviates from every prior feature)

- **Decision**: `validate_silver_contract.py` is a plain local Python
  script — no `# Databricks notebook source` header, no
  `databricks jobs submit`. Run directly: `python src/contracts/validate_silver_contract.py`.
- **Rationale**: This is the first feature in the project that touches
  no Databricks table or workspace resource at all — the contract is a
  pure repository artifact. Forcing it through the notebook/job
  execution path used by features 002-004 would add Databricks-specific
  ceremony (workspace import, job submit, serverless startup latency) to
  a check that runs in well under a second locally, contrary to
  Principle VI.
- **Alternatives considered**: Running it as a Databricks job anyway for
  consistency with prior features — rejected; consistency isn't a value
  in itself when the underlying need (validate a local YAML file) has
  nothing to do with the platform those other scripts needed.

## 5. Per-rule and total-drop count representation in the contract

- **Decision**: Each of the 5 entries in `quality_rules` declares its own
  `policy` (`drop` for 4 of them, `resolved_upstream` for duplicates) and
  a `counting: independent` marker; the contract adds one additional
  note (not a 6th rule) stating that "total rows dropped" is a separate,
  non-overlapping metric feature 006/007 must also report, per the
  2026-07-23 clarification.
- **Rationale**: Keeps the clarification's "independent per-rule counts
  distinguishable from a separate total" decision literally present in
  the contract's content, not just in the spec — so feature 006 reads it
  from the source of truth (the contract) rather than back-referencing
  the spec's clarification log.
- **Alternatives considered**: Making "total rows dropped" its own 6th
  `quality_rules` entry — rejected, it isn't a data-quality *rule* (no
  condition of its own), it's a derived reporting metric; conflating the
  two would make `quality_rules` say "5 risks" in the constitution sense
  while actually listing 6 things.
