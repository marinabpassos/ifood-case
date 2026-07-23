# Implementation Plan: Observability da Pipeline

**Branch**: `007-pipeline-observability` | **Date**: 2026-07-23 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `specs/007-pipeline-observability/spec.md`

## Summary

Extend `src/bronze/ingest_bronze.py` and `src/silver/build_silver.py`
(minimally, as a side effect of their existing execution) to append one
row each to a new `ifood_case.silver._pipeline_run_log` Delta table:
`pipeline_stage`, `executed_at`, `status`, `rows_read`, `rows_written`,
`schema_check_status`, `duration_seconds`, a `metrics` JSON blob
(stage-specific counts), and an `alerts` array (populated when any
rule/check's drop rate exceeds 1% of rows read). Re-run both scripts
once to produce real, current log evidence. Verify — not build —
landing→bronze→silver lineage via Unity Catalog's native lineage
feature. No change to bronze's or silver's actual data-quality rules,
schema, or written table content.

## Technical Context

**Language/Version**: Python 3.11+ / PySpark (same fixed stack as
features 002-006, no new dependency)

**Primary Dependencies**: PySpark (`spark.createDataFrame` with an
explicit `StructType` for the log row, `.write.format("delta")
.mode("append")`), `time` (stdlib, for `duration_seconds`), `json`
(stdlib, already used everywhere). No new third-party dependency.

**Storage**: Reads/writes unchanged for bronze/silver's own data tables
(still `mode("overwrite")`, same content). Adds one new table,
`ifood_case.silver._pipeline_run_log` — **append-only**, the one
deliberate exception to this project's overwrite convention, since a
run log's entire purpose is accumulating history across executions.

**Testing**: N/A — no unit-testable application logic beyond Spark
transformations. Verification is operational: `quickstart.md`'s scripted
checks (query the log table, confirm alert entries, query lineage) run
via `databricks jobs submit` (re-running the two extended scripts) plus
SQL queries against the workspace.

**Target Platform**: Databricks Free Edition workspace (serverless
compute) — same mechanism as every feature except 005.

**Project Type**: Single project. **No new `src/` package** — this
feature modifies two existing files
(`src/bronze/ingest_bronze.py`, `src/silver/build_silver.py`) rather
than adding a new one. See Complexity Tracking for why touching
previously-delivered features' code is the correct shape for this
feature, not scope creep.

**Performance Goals**: N/A — one extra row written per run; negligible
next to the ~16.2M-row read/write each script already does.

**Constraints**: Free Edition's serverless-only compute / single
2X-Small SQL Warehouse constraints (documented in feature 002) apply
unchanged. Unity Catalog's native lineage system tables
(`system.access.table_lineage` or equivalent) may or may not be enabled
by default on Free Edition — this is a genuine unknown resolved in
Phase 0 research, with the Catalog Explorer UI as a documented fallback
verification path (research.md §5).

**Scale/Scope**: 2 existing scripts extended (not rewritten), 1 new
append-only table (9 columns), re-running 2 already-proven pipelines
(~16.2M rows each).

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Applies? | Assessment |
|---|---|---|
| I. Data Quality Is a Gate | No | This feature adds no new data-quality rule and changes none of the existing ones (spec FR-007) — it only logs the outcome of rules features 004/006 already apply. |
| II. Data Contracts First | No | `_pipeline_run_log` is an operational/observability table, not a consumption-layer table governed by a Principle-II data contract the way `yellow_taxi_trips` is — "consumption layer" in Principle II means the business-facing analytical table per the principle's own rationale ("gives an automatic enforcement point" for a business table) and `DECISOES_PROJETO.md` §6, not every table that happens to share the `silver` schema namespace. `_pipeline_run_log` has no business schema to contract, only an operational log shape (fixed by this plan's data-model.md instead). |
| III. Observability Is Part of the Deliverable | **Yes — this feature exists to satisfy it** | Implements every explicit clause: a queryable metadata table (not notebook-print-only), native UC lineage (not custom-built), and threshold-based alerting (>1%) — all three named requirements from Principle III, in one feature. |
| IV. Fixed Stack, Justified Deviations | **Yes** | PySpark/Delta/Unity Catalog only, no new dependency. The one deliberate deviation from this project's usual "overwrite" table convention (`_pipeline_run_log` uses `append`) is justified by construction — a run log that overwrote itself every run would defeat its own purpose — and documented here rather than silently introduced. |
| V. Spec-Driven Development Workflow | **Yes** | Specify → Clarify (no critical ambiguities found) → Plan (this document) → Tasks → Implement — satisfied by construction. |
| VI. Lean Instructions, Simple Architecture | **Yes** | No new layer, no new schema beyond one operational table reusing the existing `silver` schema, no new `src/` package — the smallest change that satisfies Principle III's three clauses. |

**Result**: PASS. One documented, deliberate deviation (append-only
table, Principle IV) — not a violation, since Principle IV requires
documenting deviations, not avoiding all of them when justified. See
Complexity Tracking for the "modifies existing features' code" question.
Re-checked after Phase 1 below.

## Project Structure

### Documentation (this feature)

```text
specs/007-pipeline-observability/
├── plan.md                       # This file (/speckit-plan command output)
├── research.md                   # Phase 0 output (/speckit-plan command)
├── data-model.md                 # Phase 1 output (/speckit-plan command)
├── quickstart.md                 # Phase 1 output (/speckit-plan command)
├── checklists/
│   └── requirements.md           # Spec quality checklist (/speckit-specify command)
└── tasks.md                      # Phase 2 output (/speckit-tasks command - NOT created by /speckit-plan)
```

No `contracts/` subfolder: `_pipeline_run_log` is an operational log
table, not a Principle-II governed data contract — its shape is fixed
by `data-model.md` alone, matching feature 006's precedent of skipping
`contracts/` when nothing new needs a structure-fixing doc of that kind.

### Source Code (repository root)

```text
ifood_case/
├── src/
│   ├── ingestion/                 # Existing (feature 002), untouched
│   ├── profiling/                 # Existing (feature 003), untouched
│   ├── bronze/
│   │   └── ingest_bronze.py       # MODIFIED (feature 007): adds run-log write + alert check as its final step
│   ├── contracts/                 # Existing (feature 005), untouched
│   └── silver/
│       └── build_silver.py        # MODIFIED (feature 007): adds run-log write + alert check as its final step
```

**Structure Decision**: Single-project layout, consistent with features
001-006. No new package — the logging/alerting helper code is small
enough (research.md §2-3) to duplicate directly into each of the two
existing scripts, matching this project's established convention of
self-contained, independently-deployable notebook scripts (each script
is uploaded to the workspace on its own; a shared importable module
would need its own upload/import-path handling for no real benefit at
this size). No `tests/` directory — verification is operational
(`quickstart.md`).

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|---------------------------------------|
| This feature modifies two previously-delivered features' scripts (`ingest_bronze.py` from feature 004, `build_silver.py` from feature 006) instead of adding new, isolated code | Principle III requires *every pipeline execution* to log its own metrics — that can only happen from inside the scripts that constitute each execution; a separate, disconnected logging script would not be logging the actual execution, only a report about it | A standalone script that reads bronze/silver's already-written `ingestion-log.md`/`dq-run-log.md` and backfills the table — rejected in the spec's own Assumptions: it would satisfy the letter of "a queryable table exists" but not "every pipeline execution MUST log" (Principle III's literal wording), and would leave future re-runs unlogged unless someone remembered to backfill again by hand |
| `_pipeline_run_log` uses `mode("append")`, the only table in this project that doesn't overwrite | Every other table in this project represents current-state data (bronze/silver hold the latest cleaned dataset); a run log's entire value is historical accumulation — overwriting it on each run would erase the audit trail Principle III requires | `mode("overwrite")` for consistency with other tables — rejected, it would defeat the log's purpose (US1 Acceptance Scenario 2 explicitly requires history to accumulate across runs) |

## Post-Design Constitution Re-Check

Re-evaluated after Phase 1 (`data-model.md`, `quickstart.md`): unchanged
from the pre-Phase-0 assessment above. `data-model.md` confirms the
"Pipeline Run Log Entry" fields map 1:1 to Principle III's mandated list
(rows read/written, drop/flag volumes, schema-mismatch status, duration,
status) with nothing extraneous, and the alerting design (research.md
§4) implements the constitution's own example threshold (>1%) rather
than inventing an unrelated one. **Result: PASS, no new violations.**
