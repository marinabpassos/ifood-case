# Implementation Plan: Data Quality & Camada Silver

**Branch**: `006-silver-data-quality` | **Date**: 2026-07-23 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `specs/006-silver-data-quality/spec.md`

## Summary

Read `ifood_case.bronze.yellow_taxi_trips`, load
`contracts/nyc_taxi_silver.yaml` at runtime (not just as a design
reference — the contract's own `condition` strings drive the actual
filter logic via `F.expr()`), assert bronze's schema is compatible with
the contract's declared columns, compute each of the 4 drop rules'
row counts independently against the full bronze input, apply the
combined filter, select exactly the contract's 6 columns (adding
`_silver_processed_at`), and write `ifood_case.silver.yellow_taxi_trips`.
Report rows read/written, the 4 independent counts, and one
non-overlapping total-dropped count.

## Technical Context

**Language/Version**: Python 3.11+ / PySpark (same fixed stack as
features 002-004, no new dependency)

**Primary Dependencies**: PySpark (`spark.read.table`, `F.expr`,
`.withColumn`, `.filter`, `.dropDuplicates` not needed here — dedup is
bronze's job), Delta Lake (`.write.format("delta").saveAsTable(...)`),
`PyYAML` (already established in feature 005, reused here to load
`contracts/nyc_taxi_silver.yaml` at runtime — this feature is
contract-*driven*, not just contract-*documented*).

**Storage**: Reads `ifood_case.bronze.yellow_taxi_trips` (feature 004);
writes the new managed Delta table
`ifood_case.silver.yellow_taxi_trips`. The `ifood_case.silver` schema
does not exist yet and must be created before the write — same fix
already learned the hard way in feature 004 (forgetting this caused
`SCHEMA_NOT_FOUND` on the first real run there).

**Testing**: N/A — no unit-testable application logic beyond Spark
transformations. Verification is operational: `quickstart.md`'s scripted
checks (schema match, zero invalid rows, per-rule counts matching
feature 004's bronze-layer baseline exactly) run via
`databricks jobs submit`, same mechanism as features 002-004.

**Target Platform**: Databricks Free Edition workspace (serverless
compute) — back to needing Databricks access, unlike feature 005 (a
pure local YAML/validator feature).

**Project Type**: Single project — adds a `src/silver/` package;
`src/ingestion/`, `src/profiling/`, `src/bronze/`, `src/contracts/` are
untouched.

**Performance Goals**: N/A — one source table (~16.2M rows, 21
columns), one target table (6 columns), a one-time batch well within
serverless compute's default capacity.

**Constraints**: Free Edition's serverless-only compute / single
2X-Small SQL Warehouse constraints (documented in feature 002) apply
unchanged. No new constraint expected — the `ifood_case.silver` schema
creation follows the exact pattern already proven in feature 004.

**Scale/Scope**: 1 source table (bronze, ~16.2M rows / 21 columns) → 1
target table (silver, 6 columns), 4 drop rules loaded from the contract,
1 schema-compatibility assertion.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Applies? | Assessment |
|---|---|---|
| I. Data Quality Is a Gate | **Yes — this feature applies the gate** | The 4 data-quality rules (already profiled in feature 003, already declared in feature 005's contract) are applied here for the first time against real data, with each rule's affected-row volume explicitly reported (FR-007) — exactly what Principle I requires at the point a rule is actually enforced. |
| II. Data Contracts First | **Yes** | The contract (feature 005) was written and merged before this feature's table-writing code was implemented — satisfied by construction. This feature also *asserts* the contract (schema check, FR-002) before writing, per Principle II's explicit requirement that the contract "is not documentation-only." |
| III. Observability Is Part of the Deliverable | Partial | FR-007 requires reporting rows read/written and per-rule/total counts for this feature's own auditability now; the durable, queryable `_pipeline_run_log` table and the >1%-threshold alerting are feature 007's scope, not re-implemented here. |
| IV. Fixed Stack, Justified Deviations | **Yes** | PySpark/Delta/Unity Catalog + PyYAML (already an established dependency since feature 005) — no new technology, no deviation. |
| V. Spec-Driven Development Workflow | **Yes** | Specify → Plan (this document) → Tasks → Implement, human checkpoint at each — satisfied by construction. |
| VI. Lean Instructions, Simple Architecture | **Yes** | One script (`build_silver.py`) covers contract loading, schema assertion, rule application, and the write — cohesive enough not to warrant splitting (matching `profile_bronze.py`'s precedent). No gold layer, no speculative abstraction. |

**Result**: PASS. No violations, no workarounds to document. Re-checked
after Phase 1 below.

## Project Structure

### Documentation (this feature)

```text
specs/006-silver-data-quality/
├── plan.md                       # This file (/speckit-plan command output)
├── research.md                   # Phase 0 output (/speckit-plan command)
├── data-model.md                 # Phase 1 output (/speckit-plan command)
├── quickstart.md                 # Phase 1 output (/speckit-plan command)
├── checklists/
│   └── requirements.md           # Spec quality checklist (/speckit-specify command)
└── tasks.md                      # Phase 2 output (/speckit-tasks command - NOT created by /speckit-plan)
```

No `contracts/` subfolder for this feature: unlike features 003-005,
this feature introduces no new artifact format needing its own
structure-fixing doc — it *consumes* an already-fixed structure
(`contracts/nyc_taxi_silver.yaml`, fixed by feature 005's
`silver-contract-structure.md`) and produces a Delta table whose shape
that same contract already specifies in full.

### Source Code (repository root)

```text
ifood_case/
├── src/
│   ├── ingestion/                 # Existing (feature 002), untouched
│   ├── profiling/                 # Existing (feature 003), untouched
│   ├── bronze/                    # Existing (feature 004), untouched
│   ├── contracts/                 # Existing (feature 005), untouched
│   └── silver/
│       ├── __init__.py
│       └── build_silver.py        # US1-3 / FR-001-008: load contract, assert schema, apply rules, write table, report
```

**Structure Decision**: Single-project layout, consistent with features
001-005. A new `src/silver/` package holds the one script — contract
loading, schema assertion, independent rule evaluation, the combined
filter, column selection, schema creation, table write, and reporting
are all "produce the silver table from the contract" concerns, cohesive
enough to stay in one file per Principle VI. No `tests/` directory —
verification is operational (`quickstart.md`), matching every prior
feature that touches Databricks.

## Complexity Tracking

*No entries — the Constitution Check above found no violations or
workarounds requiring justification.*

## Post-Design Constitution Re-Check

Re-evaluated after Phase 1 (`data-model.md`, `quickstart.md`): unchanged
from the pre-Phase-0 assessment above. `data-model.md` confirms the
"Silver Data Quality Run" report entity carries exactly the fields
Principle I/III require (rows read/written, 4 independent counts, 1
total-dropped count, schema-assertion status) without inventing
anything feature 007's future `_pipeline_run_log` should own instead.
**Result: PASS, no new violations.**
