# Phase 1 Data Model: Camada Bronze

Two entities are net-new artifacts of this feature; one is an existing
entity whose Unity Catalog address changes. Column-by-column detail for
the bronze table itself lives in
[contracts/bronze-schema.md](contracts/bronze-schema.md), not duplicated
here.

## Landing Zone (renamed)

The same singleton entity from `specs/002-ambiente-landing-zone/data-model.md`,
with its Unity Catalog address updated. No change to its content or
validation rules — only the `catalog`/`schema` fields move.

| Field | Type | Notes |
|---|---|---|
| `catalog` | string | `ifood_case` (unchanged) |
| `schema` | string | **Changes from `bronze` to `landing`** (this feature, FR-001) |
| `volume` | string | `yellow_taxi_raw` (unchanged) |
| `full_path` | string (derived) | `/Volumes/ifood_case/landing/yellow_taxi_raw` (was `/Volumes/ifood_case/bronze/yellow_taxi_raw`) |

**Validation rule**: After the move, `full_path` MUST resolve and be
listable via standard platform tooling, and every file's size MUST be
byte-identical to what feature 002 originally landed (no re-download, no
transformation) — the same SC-004 guarantee feature 002 established, now
re-verified at the new address.

## Bronze Trip Record

New entity. Grain: one row per trip record, spanning all 5 months
(Jan-May 2023) in a single table, `ifood_case.bronze.yellow_taxi_trips`.

| Field group | Notes |
|---|---|
| Source columns (19, per feature 003's full-schema comparison) | Carried through with their original names; the two type-drifted columns (`passenger_count`, `ratecodeid`) are cast to a single consistent type (research.md §2). No column is dropped, added, or renamed beyond the two ingestion-metadata columns below. Exact column list and types fixed by [contracts/bronze-schema.md](contracts/bronze-schema.md). |
| `_source_file` | string; the originating monthly file name (research.md §4) |
| `_ingested_at` | timestamp; shared by every row from a given ingestion run (research.md §4) |

**Validation rules**:
- No row is dropped for a business-quality reason (spec User Story 4 /
  FR-006) — negative/zero `total_amount`, null/zero `passenger_count`,
  `dropoff` before `pickup`, and out-of-range dates all remain present at
  the same rate feature 003 measured.
- Full-row duplicates (measured on source columns only, before the two
  metadata columns are added — research.md §5) MUST NOT appear more than
  once.
- Total row count MUST equal feature 003's total (16,186,386) minus
  whatever duplicate count this feature's own run reports.

**Relationships**: Every Bronze Trip Record traces to exactly one Landing
Zone file via `_source_file` (1:5, one of the five monthly files). No
other relationships — this is a single flat fact-shaped table, not a star
schema (per the 2026-07-23 brainstorming decision).

## Bronze Ingestion Run

New entity — a lightweight, single-purpose record of this feature's own
execution, persisted as `specs/004-bronze-layer/ingestion-log.md`
(research.md §6). Not the durable `_pipeline_run_log` table (that's
feature 007's scope) — this is this feature's own auditable evidence for
FR-007/SC-003.

| Field | Type | Notes |
|---|---|---|
| `rows_read` | integer | Total rows read across the 5 landing files, pre-dedup |
| `rows_written` | integer | Rows actually written to `ifood_case.bronze.yellow_taxi_trips` |
| `duplicates_removed` | integer | `rows_read - rows_written` (expected 0, per feature 003) |
| `schema_validation_status` | enum: `pass` \| `failed` | Result of the FR-008 pre-cast schema assertion |
| `executed_at` | timestamp | When the ingestion job ran |

**Completion condition**: `schema_validation_status = pass` AND
`rows_written` equals feature 003's total row count minus
`duplicates_removed`.
