# Implementation Plan: Data Profiling (EDA sobre Bronze)

**Branch**: `003-data-profiling` | **Date**: 2026-07-23 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `specs/003-data-profiling/spec.md`

## Summary

Run read-only exploratory profiling over the 5 bronze parquet files landed
by feature 002: a full-column schema comparison (severity-split between
the 5 required columns and everything else), per-month volumetry,
completeness (null rates) on the required columns, descriptive statistics
and outlier counts on `total_amount`/`passenger_count`, out-of-range date
counts, and full-row duplicate counts. No table is written or altered —
findings are transcribed into a versioned `findings.md` that feature 004
(data contract) and feature 005 (quality rules) will read as their input.

## Technical Context

**Language/Version**: Python 3.11+ / PySpark (matches features 001-002's
fixed stack; no new dependency)

**Primary Dependencies**: PySpark only (`spark.read.parquet`, `.schema`,
`.approxQuantile`, `.dropDuplicates`) — already fixed in `requirements.txt`.
`ydata-profiling` (listed as optional in `requirements.txt`) is **not**
used here; pure PySpark covers every FR without adding a dependency
(Constitution Principle IV/VI)

**Storage**: Reads `ifood_case.bronze.yellow_taxi_raw` (feature 002,
read-only); writes no table. Findings persist as
`specs/003-data-profiling/findings.md` (research.md §4), not a Delta table

**Testing**: N/A — no application logic beyond profiling computations.
Verification is operational: the two scripted checks in `quickstart.md`
plus confirming `findings.md` matches `contracts/profiling-findings-schema.md`

**Target Platform**: Databricks Free Edition workspace (serverless
compute) — same execution mechanism as feature 002 (notebook-format
scripts run via `databricks jobs submit`)

**Project Type**: Single project — adds a `src/profiling/` package, no new
top-level directory

**Performance Goals**: N/A — 5 files, ~15M rows total, well within
serverless compute's default capacity for a one-time exploratory job

**Constraints**: Free Edition's single 2X-Small SQL Warehouse / serverless
-only compute constraints (already documented in feature 002) apply
unchanged; this feature introduces no new constraint

**Scale/Scope**: 5 monthly files (Jan-May 2023), 6 metric categories per
month (schema, volumetry, completeness, stats, date-range, duplicates),
plus a cross-month schema deviation list

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Applies? | Assessment |
|---|---|---|
| I. Data Quality Is a Gate | **Yes** | This feature **is** the profiling step Principle I requires before any silver-layer modeling — it directly satisfies the constitution's mandate, though the DQ *rules* themselves (drop/flag policy) are feature 005's, not this one's |
| II. Data Contracts First | No | No silver table or contract is written here; `findings.md` is this feature's output, consumed by feature 004 when it writes the actual data contract |
| III. Observability Is Part of the Deliverable | Partial | Findings are recorded as a versioned, reviewable artifact (FR-007) — satisfies the documentation spirit, but full pipeline-run logging (`_pipeline_run_log`) is feature 006's scope, not re-implemented here |
| IV. Fixed Stack, Justified Deviations | **Yes** | Pure PySpark, no new dependency, same Free Edition serverless execution mechanism as feature 002 — no deviation to justify |
| V. Spec-Driven Development Workflow | **Yes** | Delivered via Specify → Clarify → Plan → Tasks → Implement with human checkpoints — satisfied by construction |
| VI. Lean Instructions, Simple Architecture | **Yes** | Two scripts (not six), findings in one new file (not scattered), reuses feature 002's execution pattern rather than inventing a new one |

**Result**: PASS. No unjustified violations. Principle I is the reason
this feature exists; it's satisfied by design, not a gate this feature
risks failing. Re-checked after Phase 1 below.

## Project Structure

### Documentation (this feature)

```text
specs/003-data-profiling/
├── plan.md                                   # This file (/speckit-plan command output)
├── research.md                               # Phase 0 output (/speckit-plan command)
├── data-model.md                             # Phase 1 output (/speckit-plan command)
├── quickstart.md                             # Phase 1 output (/speckit-plan command)
├── contracts/
│   └── profiling-findings-schema.md          # Phase 1 output — structure findings.md must follow, consumed by features 004/005
├── checklists/
│   └── requirements.md                       # Spec quality checklist (/speckit-specify command)
├── findings.md                               # Implementation-phase output — NOT created by /speckit-plan, see research.md §4
└── tasks.md                                  # Phase 2 output (/speckit-tasks command - NOT created by /speckit-plan)
```

### Source Code (repository root)

```text
ifood_case/
├── src/
│   ├── ingestion/                    # Existing (feature 002), untouched
│   └── profiling/
│       ├── __init__.py
│       ├── schema_check.py           # US1 / FR-001, FR-009, FR-010: full-column schema comparison with severity split
│       └── profile_bronze.py         # US2-4 / FR-002-006: volumetry, completeness, stats, date-range, duplicates
└── specs/003-data-profiling/findings.md   # FR-007: versioned profiling output, structure fixed by contracts/profiling-findings-schema.md
```

**Structure Decision**: Single-project layout, consistent with features
001-002. A new `src/profiling/` package holds two scripts — one for the
higher-priority schema check (US1, sequenced first since later stories
depend on its column mapping), one bundling the remaining four
requirements (US2-4 plus the date-range/duplicate edge cases), which are
all "read each file, compute a metric" concerns cohesive enough not to
warrant six separate files (Constitution Principle VI). No `tests/`
directory — per Technical Context, verification is operational
(`quickstart.md`), matching the reasoning in features 001 and 002.

## Complexity Tracking

*No entries — the Constitution Check above found no unjustified
violations. Principle I is satisfied by this feature's existence, not a
gate it risks failing.*

## Post-Design Constitution Re-Check

Re-evaluated after Phase 1 (`data-model.md`, `contracts/profiling-findings-schema.md`,
`quickstart.md`): unchanged from the pre-Phase-0 assessment above.
`data-model.md` confirms the only entities are profiling metadata (Schema
Deviation, Profiling Finding) plus a read-only reference to feature 002's
Monthly Trip Record File — no bronze content is modified, and Principle
I/II remain correctly scoped (this feature satisfies I's profiling
mandate; II's contract is still feature 004's). The findings contract
makes "sufficient for feature 005 to draft quality rules" (SC-004)
concrete and checkable rather than aspirational. **Result: PASS, no new
violations.**
