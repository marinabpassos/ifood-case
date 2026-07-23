# Phase 1 Data Model: Contrato de Dados da Silver

One entity: the contract document itself. Its required shape is fixed by
[contracts/silver-contract-structure.md](contracts/silver-contract-structure.md),
not duplicated here — this file describes what the entity *means*, the
structure doc fixes what it must *contain*.

## Silver Data Contract

The declarative specification for `ifood_case.silver.yellow_taxi_trips`,
written before any silver table-writing code exists. Lives at
`contracts/nyc_taxi_silver.yaml`. Not a physical table — a specification
for one, consumed by feature 006 (implementation) and feature 007
(observability reporting shape).

| Field group | Notes |
|---|---|
| `contract` | Name (`nyc_taxi_silver`) and current version (`v1`, research.md §1). |
| `table` | Full identity: `catalog=ifood_case`, `schema=silver`, `name=yellow_taxi_trips`, `owner` (the case author). |
| `grain` | "One row = one trip event." Explicitly states no formal uniqueness constraint is enforced on the 6-column schema alone — the only inherited uniqueness guarantee is bronze's full-row dedup over its 19 source columns (feature 004), which silver's narrower 5-business-column schema can't independently re-derive (spec Edge Cases). |
| `columns` | Exactly 6 entries (2026-07-23 clarification): the 5 required business columns (`VendorID`, `passenger_count`, `total_amount`, `tpep_pickup_datetime`, `tpep_dropoff_datetime`) plus `_silver_processed_at` (new, silver-specific audit timestamp — not inherited from bronze's `_source_file`/`_ingested_at`, both dropped). Each entry: `name`, `type` (business-level: integer/decimal/timestamp, research.md §3), `nullable` (post-cleaning invariant), `description`. |
| `quality_rules` | Exactly 5 entries, one per constitution-named risk: `total_amount` negative/zero (drop), `passenger_count` null/zero (drop), `dropoff` before `pickup` (drop), out-of-range dates (drop), duplicates (resolved upstream at bronze, no silver-layer action). Each drop rule: `id`, `condition`, `policy: drop`, `counting: independent` (2026-07-23 clarification, research.md §5), `rationale`. |
| `sla` | Illustrative update frequency/latency target, framed as if the pipeline were recurring (spec Assumptions; this project's real load is one-time Jan-May 2023). |
| `versioning` | `current_version: v1`, `breaking_change_policy` with explicit `major`/`minor`/`patch` triggers (spec Assumptions, standard semver default). |

**Validation rules**:
- All 6 `columns` entries and all 5 `quality_rules` entries MUST be
  present — no partial contract (SC-001, SC-002).
- `versioning.breaking_change_policy` MUST be specific enough to resolve
  any hypothetical future change (add/remove/rename a column, change a
  rule's policy) to exactly one of major/minor/patch, without needing to
  ask the contract's author (SC-003).
- The contract MUST NOT reference any Spark-specific type or any bronze
  passthrough column — only the 6 columns and business-level types
  (research.md §3).

**Relationships**: None — this is a standalone specification document,
not a physical entity with foreign keys. It *describes* the future
`ifood_case.silver.yellow_taxi_trips` table that feature 006 will create.

## Contract Validation Result

A lightweight, ephemeral result of running
`src/contracts/validate_silver_contract.py` — not persisted anywhere
(no `_pipeline_run_log` entry; there's no pipeline execution to log,
research.md §4).

| Field | Type | Notes |
|---|---|---|
| `structurally_valid` | boolean | `true` only if every check in research.md §2 passes |
| `missing_or_invalid` | list of strings | Empty when `structurally_valid` is `true`; otherwise names each failing check |

**Completion condition**: `structurally_valid = true` with an empty
`missing_or_invalid` list.
