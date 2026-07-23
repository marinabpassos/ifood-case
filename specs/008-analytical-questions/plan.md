# Implementation Plan: Análises Analíticas

**Branch**: `008-analytical-questions` | **Date**: 2026-07-23 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `specs/008-analytical-questions/spec.md`

## Summary

Answer the case's two required analytical questions directly against
`ifood_case.silver.yellow_taxi_trips`: average `total_amount` per month
(5 rows) and average `passenger_count` by hour of `tpep_pickup_datetime`
for May 2023 (24 rows). Delivered two ways, deliberately kept both (user
decision, 2026-07-23): (1) two plain standalone `.sql` files a business
user can run directly with no other tooling, and (2) a single genuine
Databricks notebook, `analysis/analise.py` (revised once more, user
feedback 2026-07-23: real cell structure, not a flat script) — one
section per question, each a markdown cell with the question, a `%sql`
cell whose rendered result table *is* the answer, and a Python cell that
turns that same result (`_sqldf`) into a chart — a concrete demonstration
of the platform's visualization capability, not just the minimal path to
an answer. Chart images are generated server-side (matplotlib is already
present on Databricks Runtime) and brought back into the repo as PNGs
via the job's own JSON output (base64), the same "compute on Databricks,
transcribe the result locally" pattern every prior feature already uses
— no new Databricks infrastructure (no Volume, no local matplotlib
install) needed.

Additionally ships one bonus/differentiator analysis (user request,
2026-07-23), as one more section of the same `analise.py` notebook,
same markdown/`%sql`/Python-chart pattern: a daily trip-count time series
across the full Jan-May 2023 window, decomposed into trend and weekly
seasonality using Prophet, with its own two chart images — clearly
labeled as bonus content, never presented as a substitute for the two
required answers above.

## Technical Context

**Language/Version**: Two languages, deliberately: plain SQL (the
standalone `.sql` files) and Python 3.11+/PySpark (the notebook that
also produces charts) — first feature to ship both a pure-SQL and a
PySpark-notebook artifact side by side, not as alternatives but as two
audiences for the same two answers.

**Primary Dependencies**: PySpark (`spark.sql`, `.toPandas()` — each
result is at most 24 rows, trivially small to collect to the driver),
`plotly` + `kaleido==0.2.1` (chart rendering + static PNG export;
**not** pre-installed on Databricks Runtime — installed by the
notebook's own first cell alongside `prophet`, research.md §1 revised
again after implementation: replaced `matplotlib`, which is
pre-installed but produced noisy `findfont` warnings for unavailable
font families and a visibly less polished static render than Kaleido's
Chromium-based export; Kaleido pinned below 1.x because that major
version dropped its bundled Chromium for a separate `pio.get_chrome()`
download step, a poor fit for Free Edition's restricted outbound
network), `base64` (stdlib, to round-trip the PNG bytes — `.to_image()`
returns bytes directly, no `io.BytesIO` buffer dance needed the way
matplotlib's `savefig` required). Bonus analysis only: `prophet` — **not**
pre-installed on Databricks Runtime, installed by the notebook's own
first two cells (`%pip install prophet plotly kaleido==0.2.1` +
`dbutils.library.restartPython()`, research.md §6, revised twice after
implementation — both a task-level `libraries` field and a job-level
`environments`/`environment_key` entry were tried and
rejected/insufficient before landing on notebook-level `%pip install`,
the only mechanism that works both for job runs and interactive runs);
`pandas` (already a PySpark/Databricks Runtime transitive dependency)
to shape the `ds`/`y` DataFrame Prophet requires.

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

**Scale/Scope**: 3 standalone `.sql` files, 1 multi-cell notebook
(markdown + `%sql` + Python cells — 3 questions/sections, each with its
own markdown, query, and chart cell), 4 PNG chart images, 1 results
document.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Applies? | Assessment |
|---|---|---|
| I. Data Quality Is a Gate | No | Reads already-cleaned data (features 004-006); introduces no new data-quality rule. |
| II. Data Contracts First | No | Reads the silver table under its existing contract (feature 005); doesn't write any table, so no new contract is needed. |
| III. Observability Is Part of the Deliverable | No | A read-only analytical notebook is not a pipeline execution in Principle III's sense (no rows dropped/flagged, nothing to log to `_pipeline_run_log`). |
| IV. Fixed Stack, Justified Deviations | **Yes** | PySpark (fixed stack) for all 3 queries. The standalone `.sql` files use the constitution's own named "Consumo final: SQL via Databricks SQL Warehouse" path directly. **Justified deviations** (both post-implementation, both scoped to this one read-only analytical notebook, zero footprint on bronze/silver or their dependencies): (1) `prophet` for the bonus analysis — explicitly user-requested differentiator content. (2) `plotly`+`kaleido==0.2.1` for chart rendering, replacing the originally-planned `matplotlib` (which needed no justification as pre-installed/not-a-new-dependency) — this genuinely is a new dependency, on the *required* Q1/Q2 charts too, not just the bonus; justified by explicit user request after hitting matplotlib's `findfont` warning spam and asking to evaluate an alternative library, with Kaleido's Chromium-based render also giving a visibly crisper static PNG (research.md §1, §10, revised after implementation). |
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
│   ├── daily_trip_counts.sql                # US5 (bonus) / FR-007: standalone query, daily trip counts Jan-May 2023
│   ├── analise.py                           # US4/US5 / FR-006, FR-009: single genuine Databricks notebook (markdown + %sql + Python cells, not a flat script) - one section per question (markdown question, %sql query whose result table is the answer, Python chart cell reading `_sqldf`), plus a bonus section fitting Prophet
│   ├── charts/
│   │   ├── avg_total_amount_by_month.png    # Generated by analise.py, decoded from job output
│   │   ├── avg_passenger_count_by_hour_may.png
│   │   ├── daily_trip_volume_trend.png      # Bonus (US5): Prophet plot_plotly(forecast), iFood-red restyled
│   │   └── daily_trip_volume_components.png # Bonus (US5): Prophet plot_components_plotly(forecast), iFood-red restyled
│   └── answers.md                           # US3/US4/US5 / FR-004-009: both required questions' full results + embedded charts + plain-language answers, plus the bonus analysis clearly labeled as differentiator content
```

**Structure Decision**: Single-project layout, consistent with features
001-007. `analysis/` (already reserved by the case brief for "Scripts/
Notebooks com as respostas das perguntas") now holds both a notebook and
plain SQL, exactly matching that brief's own "Scripts/Notebooks" wording
literally — not a deviation, a fuller use of what the directory was
always meant for. No `tests/` directory — verification is operational
(`quickstart.md`).

## Complexity Tracking

| Deviation | Why needed | Simpler alternative rejected because |
|---|---|---|
| `prophet` (installed via the notebook's own `%pip install`), not part of the fixed stack | Bonus/differentiator analysis (User Story 5) explicitly requested by the user; no fixed-stack tool performs trend/seasonality decomposition | Hand-rolled decomposition (e.g., a manual weekly rolling average) would not be a genuine Prophet-based analysis, which the user specifically named |
| `plotly` + `kaleido==0.2.1` (post-implementation revision), replacing `matplotlib` for all 4 charts, not part of the fixed stack | User explicitly asked to evaluate an alternative library after matplotlib's `findfont` warning-spam surfaced on an interactive run; Kaleido's Chromium-based static export also renders visibly crisper than matplotlib for the same chart | Fixing only the font warning (pin `font.family` to `DejaVu Sans`, matplotlib's one Runtime-bundled font) was tried first and worked, but didn't address the user's actual ask ("dá uma olhada em outra lib, tipo plotly") — kept as a smaller alternative only until Plotly was evaluated and preferred |

No other entries — the rest of the Constitution Check above found no
violations or workarounds requiring justification. The notebook itself
is the direct implementation of an already-approved spec requirement
(FR-006), not an unplanned addition.

## Post-Design Constitution Re-Check

Re-evaluated after Phase 1 (`data-model.md`, `quickstart.md`): unchanged
from the pre-Phase-0 assessment above. `data-model.md` confirms the two
"Analytical Answer" entities now include a chart-image field matching
spec's updated Key Entities, with nothing extraneous beyond what FR-006
asks for. The added "Daily Trip Volume Decomposition" (bonus) entity is
scoped exactly to FR-007-009, with its Complexity Tracking entry above
covering the one new dependency it introduces. **Result: PASS, no new
violations.**
