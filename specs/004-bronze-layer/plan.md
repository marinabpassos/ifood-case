# Implementation Plan: Camada Bronze

**Branch**: `004-bronze-layer` | **Date**: 2026-07-23 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `specs/004-bronze-layer/spec.md`

## Summary

Turn the landing zone (currently misnamed `ifood_case.bronze`, feature 002)
into its own `ifood_case.landing` schema, then ingest the 5 monthly parquet
files into a new `ifood_case.bronze.yellow_taxi_trips` Delta table: one
consistent schema across months (resolving the `passenger_count`/
`ratecodeid` float-vs-integer drift found in feature 003), two ingestion
metadata columns (`_source_file`, `_ingested_at`), and full-row-duplicate
removal. No business data-quality rule runs here — bronze is a technical,
1:1 (minus exact duplicates) representation of the landing files; business
rules are feature 006's job, against feature 005's contract.

## Technical Context

**Language/Version**: Python 3.11+ / PySpark (same fixed stack as features
002-003, no new dependency)

**Primary Dependencies**: PySpark (`spark.read.parquet`, `.withColumn`/
`.cast`, `input_file_name()`, `current_timestamp()`, `.dropDuplicates()`,
`unionByName`), Delta Lake (`.write.format("delta").saveAsTable(...)`) —
both already fixed in `requirements.txt`. Unity Catalog DDL (`CREATE
SCHEMA`, `CREATE VOLUME`) via Spark SQL, same as feature 002's
`landing_zone.py`.

**Storage**: Reads `ifood_case.bronze.yellow_taxi_raw` (feature 002) before
the rename, and `ifood_case.landing.yellow_taxi_raw` after; writes the new
managed Delta table `ifood_case.bronze.yellow_taxi_trips`.

**Testing**: N/A — no unit-testable application logic beyond Spark
transformations. Verification is operational: `quickstart.md`'s scripted
checks (row counts, schema shape, known-defect rates matching feature 003)
plus the schema fixed by `contracts/bronze-schema.md`.

**Target Platform**: Databricks Free Edition workspace (serverless
compute), same `databricks jobs submit` execution mechanism as features
002-003 — the landing volume is only reachable from inside the workspace.

**Project Type**: Single project — adds a `src/bronze/` package; existing
`src/ingestion/` and `src/profiling/` are untouched.

**Performance Goals**: N/A — 5 files, ~16.2M rows total (feature 003
volumetry), a one-time batch well within serverless compute's default
capacity.

**Constraints**: Free Edition's serverless-only compute / single
2X-Small SQL Warehouse constraints (documented in feature 002) apply
unchanged. New constraint discovered during this plan's research: **Unity
Catalog does not support an in-place schema rename via SQL** (no `ALTER
SCHEMA ... RENAME TO`) — see `research.md` §1 for the resulting design
decision and Constitution Principle IV documentation.

**Scale/Scope**: One schema-namespace move (5 files, ~264MB combined,
already verified byte-identical in feature 002) + one Delta table covering
5 months / ~16.2M rows / 19 source columns (5 required + 14 ignorable,
per feature 003's full-schema comparison), plus 2 added metadata columns.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Applies? | Assessment |
|---|---|---|
| I. Data Quality Is a Gate | Partial | This feature does **not** apply any business data-quality rule (that's Principle I's actual subject, deferred to feature 006) — it only does technical dedup. No violation: Principle I gates *silver*, and no silver table is written here. |
| II. Data Contracts First | No | Principle II is scoped to "every table in the consumption (silver) layer" — bronze is not the consumption layer, so no `contracts/*.yaml`-style governed data contract is required. `contracts/bronze-schema.md` (this feature's Phase 1 output) fixes the expected schema for implementation/verification purposes, but is not the Principle-II contract (that's `contracts/nyc_taxi_silver.yaml`, feature 005). |
| III. Observability Is Part of the Deliverable | Partial | FR-007 requires reporting rows-read/rows-written/duplicates-removed for this feature's own auditability now; the durable, queryable `_pipeline_run_log` table and full alerting threshold are feature 007's scope, not re-implemented here. Native UC lineage (landing→bronze) is automatic (Unity Catalog tracks it from the read/write job) — nothing to build. |
| IV. Fixed Stack, Justified Deviations | **Yes, with a documented workaround** | PySpark/Delta/Unity Catalog, no new dependency. One workaround required: since Unity Catalog has no schema-rename DDL, FR-001 ("rename") is implemented as create-new-schema + copy files + verify + drop-old-schema (research.md §1) — documented here and in `DECISOES_PROJETO.md` per Principle IV, not a silent substitution. |
| V. Spec-Driven Development Workflow | **Yes** | Specify → Plan (this document) → Tasks → Implement, human checkpoint between each — satisfied by construction. |
| VI. Lean Instructions, Simple Architecture | **Yes** | This feature exists specifically to instantiate the three-layer cap the constitution itself defines (landing → bronze → silver, no gold) — it does not add a layer beyond that cap, it fulfills it. |

**Result**: PASS. One documented workaround (schema-rename mechanism,
Principle IV) — not a violation, since Principle IV requires
documentation of Free-Edition-driven workarounds, not their avoidance.
Re-checked after Phase 1 below.

## Project Structure

### Documentation (this feature)

```text
specs/004-bronze-layer/
├── plan.md                       # This file (/speckit-plan command output)
├── research.md                   # Phase 0 output (/speckit-plan command)
├── data-model.md                 # Phase 1 output (/speckit-plan command)
├── quickstart.md                 # Phase 1 output (/speckit-plan command)
├── contracts/
│   └── bronze-schema.md          # Phase 1 output — expected ifood_case.bronze.yellow_taxi_trips schema, consumed by this feature's own verification and by feature 005/006
├── checklists/
│   └── requirements.md           # Spec quality checklist (/speckit-specify command)
└── tasks.md                      # Phase 2 output (/speckit-tasks command - NOT created by /speckit-plan)
```

### Source Code (repository root)

```text
ifood_case/
├── src/
│   ├── ingestion/                        # Existing (feature 002), untouched
│   ├── profiling/                        # Existing (feature 003), untouched
│   └── bronze/
│       ├── __init__.py
│       ├── rename_landing_schema.py      # US1 / FR-001: landing schema move (create landing, copy files, verify, drop old bronze-named schema)
│       └── ingest_bronze.py              # US2-4 / FR-002-008: read landing, cast drifted columns, add ingestion metadata, dedup, write Delta table, report counts
└── specs/004-bronze-layer/
    └── (this feature's docs, see above — no ingestion-log.md until implementation, see research.md §6)
```

**Structure Decision**: Single-project layout, consistent with features
001-003. A new `src/bronze/` package holds two scripts — one for the
schema-namespace move (US1, sequenced first since User Story 2 reads from
the renamed location), one for the ingestion itself (US2-4, cohesive
enough to stay one file per Principle VI: cast, metadata, dedup, and the
no-business-rule guardrail are all "shape the bronze write" concerns, not
separate systems). No `tests/` directory — verification is operational
(`quickstart.md`), matching features 001-003.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|---------------------------------------|
| Schema "rename" implemented as copy+verify+delete, not a metadata-only rename | Unity Catalog has no `ALTER SCHEMA ... RENAME TO` (confirmed via Databricks docs, research.md §1) — a true rename isn't available through any scripted/SQL path | The only true rename mechanism is the Catalog Explorer UI's kebab-menu action, which is manual/interactive and unscripted — rejected because it can't run via `databricks jobs submit` like every other step in this pipeline, breaking the reproducible/versioned execution pattern features 002-003 established (Constitution Principle V) |

## Post-Design Constitution Re-Check

Re-evaluated after Phase 1 (`data-model.md`, `contracts/bronze-schema.md`,
`quickstart.md`): unchanged from the pre-Phase-0 assessment above. The
data model confirms bronze carries no business-quality columns or flags
(Principle I/VI boundary holds), and `contracts/bronze-schema.md` makes
"one consistent schema" (SC-002) concrete and checkable. The one
documented workaround (Complexity Tracking above) is the only deviation,
and it is recorded here plus flagged for `DECISOES_PROJETO.md` at
implementation time, per Principle IV. **Result: PASS, no new
violations.**
