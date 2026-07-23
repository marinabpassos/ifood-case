# Implementation Plan: Análises Analíticas

**Branch**: `008-analytical-questions` | **Date**: 2026-07-23 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `specs/008-analytical-questions/spec.md`

## Summary

Answer the case's two required analytical questions directly against
`ifood_case.silver.yellow_taxi_trips`: average `total_amount` per month
(5 rows) and average `passenger_count` by hour of `tpep_pickup_datetime`
for May 2023 (24 rows). Delivered two ways, deliberately kept both (user
decision, 2026-07-23): (1) two plain standalone `.sql` files a business
user can run directly with no other tooling, and (2) a genuine Databricks
notebook (PySpark, executing the same SQL via `spark.sql()`) that also
renders each result as a chart — a concrete demonstration of the
platform's visualization capability, not just the minimal path to an
answer. Chart images are generated server-side (matplotlib is already
present on Databricks Runtime) and brought back into the repo as PNGs
via the job's own JSON output (base64), the same "compute on Databricks,
transcribe the result locally" pattern every prior feature already uses
— no new Databricks infrastructure (no Volume, no local matplotlib
install) needed.

## Technical Context

**Language/Version**: Two languages, deliberately: plain SQL (the
standalone `.sql` files) and Python 3.11+/PySpark (the notebook that
also produces charts) — first feature to ship both a pure-SQL and a
PySpark-notebook artifact side by side, not as alternatives but as two
audiences for the same two answers.

**Primary Dependencies**: PySpark (`spark.sql`, `.toPandas()` — each
result is at most 24 rows, trivially small to collect to the driver),
`matplotlib` (pre-installed on Databricks Runtime, generates the chart
images; no new dependency to add to `requirements.txt` since it never
runs locally), `base64`/`io` (stdlib, to round-trip the PNG bytes through
the job's JSON output).

**Storage**: Reads `ifood_case.silver.yellow_taxi_trips` only (features
004-006). Writes nothing — no table, no schema change.

**Testing**: N/A — no unit-testable application logic. Verification is
operational: run the notebook via `databricks jobs submit`, decode the
returned chart PNGs, and confirm row counts/values match
`analysis/answers.md`; separately confirm both standalone `.sql` files
run unchanged against the SQL Warehouse.

**Target Platform**: Databricks Free Edition workspace (serverless
compute) for the notebook — same `databricks jobs submit` mechanism as
features 002/003/004/006/007. The standalone `.sql` files additionally
target the Databricks SQL Warehouse directly (constitution's "Consumo
final" line), for a reader who wants to run only SQL.

**Project Type**: Single project. Adds files under `analysis/` only —
still no `src/` package (the notebook lives in `analysis/`, since its
entire purpose *is* answering the two analytical questions, not general
pipeline code).

**Performance Goals**: N/A — two `GROUP BY` aggregations over ~15.3M
rows, each collapsing to 5 or 24 rows; trivial for serverless compute or
the SQL Warehouse.

**Constraints**: Free Edition's serverless-only compute / single
2X-Small SQL Warehouse constraints (feature 002) apply unchanged.

**Scale/Scope**: 2 standalone `.sql` files, 1 notebook (2 queries + 2
chart-generation cells), 2 PNG chart images, 1 results document.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Applies? | Assessment |
|---|---|---|
| I. Data Quality Is a Gate | No | Reads already-cleaned data (features 004-006); introduces no new data-quality rule. |
| II. Data Contracts First | No | Reads the silver table under its existing contract (feature 005); doesn't write any table, so no new contract is needed. |
| III. Observability Is Part of the Deliverable | No | A read-only analytical notebook is not a pipeline execution in Principle III's sense (no rows dropped/flagged, nothing to log to `_pipeline_run_log`). |
| IV. Fixed Stack, Justified Deviations | **Yes** | PySpark (fixed stack) plus `matplotlib`, which ships with Databricks Runtime already — not a new dependency introduced by this project, just a standard-library-adjacent tool already present on the fixed compute environment. The standalone `.sql` files use the constitution's own named "Consumo final: SQL via Databricks SQL Warehouse" path directly. |
| V. Spec-Driven Development Workflow | **Yes** | Specify → Plan (this document, revised once on user feedback before tasks) → Tasks → Implement — satisfied by construction. |
| VI. Lean Instructions, Simple Architecture | **Yes** | One notebook, two SQL files, one results doc — no new schema, no new table, no `src/` package. The notebook is not speculative scope: it's the concrete mechanism chosen (over a simpler pure-SQL-only path) specifically to satisfy spec FR-006/SC-005 (chart requirement), a real, already-approved requirement — not gold-plating. |

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
format needing its own structure-fixing doc.

### Source Code (repository root)

```text
ifood_case/
├── analysis/
│   ├── avg_total_amount_by_month.sql        # US1/US3 / FR-001, FR-004: standalone query, business-SQL path
│   ├── avg_passenger_count_by_hour_may.sql  # US2/US3 / FR-002, FR-004: standalone query, business-SQL path
│   ├── generate_answers.py                  # US4 / FR-006: Databricks notebook - runs both queries via spark.sql(), renders + saves chart PNGs
│   ├── charts/
│   │   ├── avg_total_amount_by_month.png    # Generated by generate_answers.py, decoded from job output
│   │   └── avg_passenger_count_by_hour_may.png
│   └── answers.md                           # US3/US4 / FR-004-006: both questions' full results, embedded charts, plain-language answers
```

**Structure Decision**: Single-project layout, consistent with features
001-007. `analysis/` (already reserved by the case brief for "Scripts/
Notebooks com as respostas das perguntas") now holds both a notebook and
plain SQL, exactly matching that brief's own "Scripts/Notebooks" wording
literally — not a deviation, a fuller use of what the directory was
always meant for. No `tests/` directory — verification is operational
(`quickstart.md`).

## Complexity Tracking

*No entries — the Constitution Check above found no violations or
workarounds requiring justification. The notebook is the direct
implementation of an already-approved spec requirement (FR-006), not an
unplanned addition.*

## Post-Design Constitution Re-Check

Re-evaluated after Phase 1 (`data-model.md`, `quickstart.md`): unchanged
from the pre-Phase-0 assessment above. `data-model.md` confirms the two
"Analytical Answer" entities now include a chart-image field matching
spec's updated Key Entities, with nothing extraneous beyond what FR-006
asks for. **Result: PASS, no new violations.**
