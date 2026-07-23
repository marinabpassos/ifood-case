# Implementation Plan: Análises Analíticas

**Branch**: `008-analytical-questions` | **Date**: 2026-07-23 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `specs/008-analytical-questions/spec.md`

## Summary

Answer the case's two required analytical questions directly against
`ifood_case.silver.yellow_taxi_trips`: average `total_amount` per month
(5 rows) and average `passenger_count` by hour of `tpep_pickup_datetime`
for May 2023 (24 rows). Deliver as two plain SQL files in `analysis/`
(the constitution's own "Consumo final: SQL via Databricks SQL
Warehouse" line, applied literally for the first time — every prior
data-producing feature used PySpark jobs instead) plus one results file
recording the actual computed numbers. No `src/` code, no pipeline
change — pure read-only SQL analysis.

## Technical Context

**Language/Version**: SQL (Databricks SQL / Spark SQL dialect) — the
first feature whose primary deliverable is SQL, not PySpark.

**Primary Dependencies**: None. Runs directly against the Databricks SQL
Warehouse; no PySpark, no new Python dependency.

**Storage**: Reads `ifood_case.silver.yellow_taxi_trips` only (features
004-006). Writes nothing — no table, no schema change.

**Testing**: N/A — no application code. Verification is operational: run
both SQL files against the SQL Warehouse and confirm the row counts and
spot-checked values match what's recorded in `analysis/answers.md`.

**Target Platform**: Databricks SQL Warehouse (2X-Small, Free Edition) —
not a serverless PySpark job. First feature to use this specific
consumption path directly, matching the constitution's Technology Stack
section verbatim ("Consumo final: SQL via Databricks SQL Warehouse").

**Project Type**: Single project. Adds files under `analysis/` only —
**no `src/` package**, the first feature with zero source-code footprint.

**Performance Goals**: N/A — two `GROUP BY` aggregations over ~15.3M
rows; Databricks SQL Warehouse handles this well within seconds.

**Constraints**: Free Edition's single 2X-Small SQL Warehouse (documented
in feature 002) applies unchanged; no new constraint.

**Scale/Scope**: 2 SQL files (5-row and 24-row results respectively), 1
results document.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Applies? | Assessment |
|---|---|---|
| I. Data Quality Is a Gate | No | Reads already-cleaned data (features 004-006); introduces no new data-quality rule. |
| II. Data Contracts First | No | Reads the silver table under its existing contract (feature 005); doesn't write any table, so no new contract is needed. |
| III. Observability Is Part of the Deliverable | No | Principle III's "every pipeline execution MUST log" targets ingestion/transformation pipelines (bronze, silver) — a read-only analytical SELECT is not a pipeline execution in that sense, and produces no rows to log volume/schema metrics about. |
| IV. Fixed Stack, Justified Deviations | **Yes** | SQL via Databricks SQL Warehouse is literally named as the "Consumo final" in the constitution's Technology Stack section — no deviation, in fact the most direct use of the fixed stack of any feature so far. |
| V. Spec-Driven Development Workflow | **Yes** | Specify → Plan (this document) → Tasks → Implement — satisfied by construction. |
| VI. Lean Instructions, Simple Architecture | **Yes** | Two SQL files and one results doc — no new abstraction, no `src/` package, the smallest footprint of any feature in this project. |

**Result**: PASS. No violations, no workarounds to document. Re-checked
after Phase 1 below.

## Project Structure

### Documentation (this feature)

```text
specs/008-analytical-questions/
├── plan.md                       # This file (/speckit-plan command output)
├── research.md                   # Phase 0 output (/speckit-plan command)
├── data-model.md                 # Phase 1 output (/speckit-plan command)
├── quickstart.md                 # Phase 1 output (/speckit-plan command)
├── checklists/
│   └── requirements.md           # Spec quality checklist (/speckit-specify command)
└── tasks.md                      # Phase 2 output (/speckit-tasks command - NOT created by /speckit-plan)
```

No `contracts/` subfolder: this feature introduces no new artifact
format needing its own structure-fixing doc — the two SQL files and the
results doc are the deliverable itself, not a specification for
something else to implement.

### Source Code (repository root)

```text
ifood_case/
├── analysis/
│   ├── avg_total_amount_by_month.sql        # US1 / FR-001: average total_amount per month
│   ├── avg_passenger_count_by_hour_may.sql  # US2 / FR-002: average passenger_count by hour, May only
│   └── answers.md                           # US3 / FR-004-005: both questions' actual computed results, documented
```

**Structure Decision**: Single-project layout, consistent with features
001-007, but the first to add nothing under `src/` at all — the case
brief's own repository layout already reserves `analysis/` specifically
for "Scripts/Notebooks com as respostas das perguntas," so this feature
uses exactly that directory and nothing else. No `tests/` directory —
verification is operational (`quickstart.md`), matching every prior
feature.

## Complexity Tracking

*No entries — the Constitution Check above found no violations or
workarounds requiring justification.*

## Post-Design Constitution Re-Check

Re-evaluated after Phase 1 (`data-model.md`, `quickstart.md`): unchanged
from the pre-Phase-0 assessment above. `data-model.md` confirms the two
"Analytical Answer" entities carry only what the spec's Key Entities
already named (question, query, result rows, computed timestamp) —
nothing extraneous, no new table or schema. **Result: PASS, no new
violations.**
