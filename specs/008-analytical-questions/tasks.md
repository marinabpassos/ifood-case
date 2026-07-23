---

description: "Task list template for feature implementation"
---

# Tasks: Análises Analíticas

**Input**: Design documents from `specs/008-analytical-questions/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, quickstart.md (all present)

**Tests**: Not included — spec/plan explicitly mark testing as operational
(quickstart.md), not unit-testable application logic (no test tasks requested).

**Organization**: Tasks are grouped by user story (spec.md priorities P1-P5)
to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1-US5)
- Exact file paths included in every task description

## Path Conventions

Single project, no `src/` footprint for this feature — everything lives
under `analysis/` at the repository root (per plan.md's Project Structure).

---

## Phase 1: Setup

**Purpose**: Confirm the shared prerequisite all 5 user stories read from

- [X] T001 Confirm `analysis/` exists at the repository root (already present, empty except `.gitkeep` — no action needed)
- [X] T002 Confirm `ifood_case.silver.yellow_taxi_trips` is queryable via `databricks experimental aitools tools query "SELECT COUNT(*) FROM ifood_case.silver.yellow_taxi_trips" --profile DEFAULT` and returns 15,339,417 (feature 006's known row count) — the one shared prerequisite every user story below depends on; no code changes

**Checkpoint**: Silver table confirmed reachable — all user story work below may proceed.

---

## Phase 2: Foundational

**Purpose**: No blocking shared infrastructure beyond Phase 1 — every user
story reads directly from the already-existing, already-verified
`ifood_case.silver.yellow_taxi_trips` (features 004-006). This phase is
intentionally empty; proceed straight to Phase 3.

---

## Phase 3: User Story 1 - Average total charged per month (Priority: P1) 🎯 MVP

**Goal**: Deliver the case's first required answer — average `total_amount`
per month (5 rows) — as a standalone, business-runnable SQL query.

**Independent Test**: Run the query directly against
`ifood_case.silver.yellow_taxi_trips` and confirm exactly 5 rows, values
matching feature 006's own `dq-run-log.md` sample (~27.46/27.37/28.29/
28.78/29.45 for Jan-May).

### Implementation for User Story 1

- [X] T003 [P] [US1] Write `analysis/avg_total_amount_by_month.sql`: `GROUP BY date_format(tpep_pickup_datetime, 'yyyy-MM')`, `ROUND(AVG(total_amount), 2)`, `COUNT(*)`, `ORDER BY 1` — no `WHERE` clause (FR-001, research.md §4)
- [X] T004 [US1] Run `databricks experimental aitools tools query "$(cat analysis/avg_total_amount_by_month.sql)" --profile DEFAULT`, confirm exactly 5 rows, and record the result values for use in T008 (US3 Acceptance Scenario 2 / spec's known-good figures) — confirmed: Jan 27.46 (2,918,145), Feb 27.37 (2,764,536), Mar 28.29 (3,227,403), Apr 28.78 (3,110,368), May 29.45 (3,318,965), matching feature 006's dq-run-log.md exactly

**Checkpoint**: US1 standalone SQL path complete and independently verified — no dependency on any other story.

---

## Phase 4: User Story 2 - Average passengers by hour in May (Priority: P2)

**Goal**: Deliver the case's second required answer — average
`passenger_count` by pickup hour in May 2023 (24 rows) — as a standalone,
business-runnable SQL query.

**Independent Test**: Run the query directly against
`ifood_case.silver.yellow_taxi_trips` and confirm exactly 24 rows (hour 0
through 23), independent of User Story 1.

### Implementation for User Story 2

- [X] T005 [P] [US2] Write `analysis/avg_passenger_count_by_hour_may.sql`: `WHERE year(tpep_pickup_datetime) = 2023 AND month(tpep_pickup_datetime) = 5`, `GROUP BY hour(tpep_pickup_datetime)`, `ROUND(AVG(passenger_count), 2)`, `COUNT(*)`, `ORDER BY 1` (FR-002, research.md §4)
- [X] T006 [US2] Run `databricks experimental aitools tools query "$(cat analysis/avg_passenger_count_by_hour_may.sql)" --profile DEFAULT`, confirm exactly 24 rows, and record the result values for use in T009 — confirmed: 24 rows (hour 0-23), avg_passenger_count ranges 1.26 (hour 6) to 1.46 (hour 2), lowest during early-morning commute hours, highest overnight

**Checkpoint**: US2 standalone SQL path complete — both required questions now independently runnable as plain SQL, satisfying User Story 3's promise on their own.

---

## Phase 5: User Story 3 - Both answers as versioned artifacts (Priority: P3)

**Goal**: Both required questions exist as files in `analysis/` — query
plus actual computed result — not ad hoc chat output.

**Independent Test**: Open `analysis/` without running anything and confirm
both questions' queries and their actual computed answers are readable
there.

### Implementation for User Story 3

- [X] T007 [US3] Create `analysis/answers.md` with a section per required question (heading, embedded query reference, result-table placeholder, plain-language-answer placeholder, computed-at timestamp placeholder) plus a placeholder heading reserved for the bonus section (populated later by T022)
- [X] T008 [US3] Populate `analysis/answers.md`'s Q1 section with the actual 5-row result table from T004, a one-line plain-language answer (e.g., "average total_amount rose from ~$27.46 in January to ~$29.45 in May"), and the UTC timestamp T004 was run (data-model.md's `computed_at` field)
- [X] T009 [US3] Populate `analysis/answers.md`'s Q2 section with the actual 24-row result table from T006, a one-line plain-language answer, and the UTC timestamp T006 was run (data-model.md's `computed_at` field)

**Checkpoint**: Both required questions fully delivered as versioned artifacts (query + result) in `analysis/`, independent of any chart or notebook (FR-004, SC-001, SC-002, SC-003).

---

## Phase 6: User Story 4 - Results readable as a chart (Priority: P4)

**Goal**: Each required question also gets a chart image, generated by a
genuine Databricks notebook (not local tooling — user's explicit
preference, see feedback memory), without displacing the plain-SQL path
from User Story 3.

**Independent Test**: Open `analysis/` and confirm a chart image exists for
each required question, independent of whether anyone runs the SQL.

### Implementation for User Story 4

- [X] T010 [US4] Create `analysis/generate_answers.py` as a Databricks notebook-source script (`# Databricks notebook source` header): reads `avg_total_amount_by_month.sql` and `avg_passenger_count_by_hour_may.sql` from the workspace via `open(path).read()` (not re-typed — research.md §2) and executes each via `spark.sql(...)`, collecting each tiny result to a pandas DataFrame via `.toPandas()`
- [X] T011 [US4] In `analysis/generate_answers.py`, render a matplotlib bar chart per required question (month on x-axis for Q1, hour on x-axis for Q2 — research.md §5), save each to an in-memory buffer, base64-encode, and include both payloads plus both result-row sets in the script's `dbutils.notebook.exit(json.dumps(...))` output (guarded by the existing `try/except NameError` pattern for local execution, per feature 007's established convention — the exit call must stay outside any broad `except Exception` block)
- [X] T012 [US4] Upload both `.sql` files (`--format AUTO`) and `generate_answers.py` (`--format SOURCE`) to the workspace via `databricks workspace import --overwrite`, then run via `databricks jobs submit --json '{"tasks":[{"task_key":"generate_answers","notebook_task":{"notebook_path":"..."}}]}' --timeout 5m` and fetch output via `databricks jobs get-run-output <run-id>` (quickstart.md Step 2)
- [X] T013 [US4] Decode both base64 chart payloads from T012's job output into `analysis/charts/avg_total_amount_by_month.png` and `analysis/charts/avg_passenger_count_by_hour_may.png`
- [X] T014 [US4] Embed both chart images into `analysis/answers.md`'s existing Q1/Q2 sections (from T008/T009), alongside their tables and plain-language answers — already present since answers.md was authored with the `![...](./charts/...)` references pointing at these now-materialized files

**Checkpoint**: Both required questions have chart images, viewable directly in the repo with no need to open Databricks or re-run anything (FR-006, SC-005) — the standalone SQL path from US1-US3 remains unaffected.

---

## Phase 7: User Story 5 - Bonus: daily trip volume, trend and seasonality (Priority: P5)

**Goal**: A differentiator analysis — daily trip-count time series across
the full Jan-May 2023 window, decomposed into trend and weekly seasonality
via Prophet, delivered as chart(s) clearly labeled as bonus content,
distinct from the two required answers.

**Independent Test**: Open `analysis/` and confirm a daily trip-count time
series exists with a trend/seasonality decomposition and chart(s), clearly
labeled as bonus, independent of whether User Stories 1-2 are being
reviewed.

### Implementation for User Story 5

- [X] T015 [P] [US5] Write `analysis/daily_trip_counts.sql`: `GROUP BY date(tpep_pickup_datetime)`, `COUNT(*)`, no month/date filter, `ORDER BY 1` (FR-007, research.md §7)
- [X] T016 [US5] Run `databricks experimental aitools tools query "$(cat analysis/daily_trip_counts.sql)" --profile DEFAULT`, confirm ~151 rows covering every calendar day Jan 1-May 31, 2023 with no gaps (spec Acceptance Scenario 1) — confirmed: exactly 151 rows, first row 2023-01-01 (71,199 trips), last row 2023-05-31 (107,768 trips), matching the exact calendar-day count for Jan 1-May 31 2023 (31+28+31+30+31), no gaps
- [X] T017 [US5] Extend `analysis/generate_answers.py`: read `daily_trip_counts.sql` from the workspace, execute via `spark.sql(...)`, collect to a pandas DataFrame with columns renamed to `ds`/`y` (Prophet's required shape)
- [X] T018 [US5] Extend `analysis/generate_answers.py`: fit `Prophet(yearly_seasonality=False, weekly_seasonality=True, daily_seasonality=False)` on the `ds`/`y` DataFrame and call `.predict()` on the same historical dates — no forecasting into unseen future dates (research.md §7)
- [X] T019 [US5] Extend `analysis/generate_answers.py`: render `model.plot(forecast)` and `model.plot_components(forecast)`, base64-encode both figures, and add both payloads to the same `dbutils.notebook.exit(json.dumps(...))` output as T011 (research.md §8)
- [X] T020 [US5] Upload `daily_trip_counts.sql` to the workspace (`--format AUTO --overwrite`), re-upload the extended `generate_answers.py`, and re-run via `databricks jobs submit` with a Prophet dependency declared on the `generate_answers` task — **deviation from research.md §6**: the task-level `"libraries":[{"pypi":{...}}]` field is rejected by serverless compute ("Libraries field is not supported for serverless task"); the working mechanism is a job-level `environments` entry (`{"environment_key":"prophet_env","spec":{"client":"2","dependencies":["prophet"]}}`) referenced from the task via `"environment_key":"prophet_env"` (`client:"1"` also rejected — "Invalid platform channel Client-1"; `client:"2"` succeeded). Job ran successfully (run_id 413326042762667, ~39s)
- [X] T021 [US5] Decode both new base64 chart payloads from T020's job output into `analysis/charts/daily_trip_volume_trend.png` and `analysis/charts/daily_trip_volume_components.png`
- [X] T022 [US5] Add a clearly labeled "Bonus: Daily Trip Volume (Prophet)" section to `analysis/answers.md`, visually and structurally separate from the Q1/Q2 sections, containing both bonus chart images, a short written interpretation of the observed trend and weekly seasonality (FR-009, SC-006), and the UTC timestamp T020's job run completed (data-model.md's `computed_at` field)

**Post-completion revision (2026-07-23, user feedback after T001-T024 were already done)**: `generate_answers.py` (flat single-cell script, no cell markers — T010's original design) was rejected: the user explicitly wanted **one single notebook**, renamed `analise.py`, with genuine Databricks cell structure — a markdown cell per question, a `%sql` cell whose rendered result table *is* the answer (not a `spark.sql(open(path).read())` call hidden in Python), and a Python chart cell reading Databricks' implicit `_sqldf` variable. Applies to T010/T011 (Q1/Q2 cells) and T017-T019 (bonus cells) — same chart outputs, same row data, same filenames under `analysis/charts/`, restructured delivery mechanism only (research.md §1-§2 revised accordingly):

- [X] T025 Rewrite `analysis/generate_answers.py` as `analysis/analise.py`: real `# COMMAND ----------` cell breaks, one markdown+`%sql`+Python-chart section per question (Q1, Q2) plus one for the bonus Prophet decomposition (reusing the same Prophet config as T018); delete the old `generate_answers.py` locally and its workspace notebook object
- [X] T026 Upload `analise.py` to the workspace (`--format SOURCE --overwrite`) and re-run via `databricks jobs submit` (task_key `analise`, same `environment_key`/`environments` Prophet mechanism as T020), confirm `SUCCESS`, and re-decode all 4 chart PNGs from the new run's output — confirmed identical row data/values to the prior run (5/24/151 rows, same figures) with `_sqldf` correctly populated after each `%sql` cell

**Second post-completion revision (2026-07-23, user feedback)**: user reported a Prophet import error running the notebook **interactively** in the Databricks UI — the `environment_key`/`environments` job-level dependency from T020/T026 only applies to that specific job's task, not to an attach-and-run-interactively session. User asked for a single initial block with all installs/imports, with imports removed from the individual cells.

- [X] T027 Add two new cells right after `analise.py`'s title markdown cell: `%pip install prophet` then `dbutils.library.restartPython()`, followed by one consolidated import cell (`base64`, `io`, `json`, `matplotlib.pyplot`, `prophet.Prophet`) — removed the now-duplicate scattered `import` statements from the Q1/Q2/bonus/final cells (research.md §6, final revision). Re-uploaded and re-ran via a plain `databricks jobs submit` task with **no** `environment_key`/`environments` field (run `analise_run_pip_install`, `result_state: SUCCESS`) to confirm the notebook is now self-installing regardless of how it's run; re-decoded all 4 chart PNGs, byte-for-byte equivalent (±1 byte PNG-encoding noise) to the prior run

**Third post-completion revision (2026-07-23, user feedback)**: user asked for prettier charts, Portuguese labels/titles, and iFood brand colors. Invoked the `dataviz` skill for methodology (form/color/marks/labels checks) rather than eyeballing it.

- [X] T028 Define an iFood-brand chart style in `analise.py`'s import cell: `IFOOD_RED = "#EA1D2C"` as the single-hue mark color (one series per chart -> no legend needed per dataviz skill's categorical-vs-single-series rule), contrast-checked at 4.46:1 vs. white via the skill's `validate_palette.js` `contrast()` export (clears the 3:1 mark floor); `INK`/`MUTED`/`GRID` text/grid tokens (never coloring text with the data color, per the skill's mark spec); a shared `style_bar_axes()` helper (no top/right/left spines, recessive horizontal gridlines, no tick marks)
- [X] T029 Re-title and re-label every chart in Portuguese (Q1: "Média de total_amount por mês", eixos "Mês"/"Valor médio (USD)"; Q2: "Média de passageiros por hora do dia", eixos "Hora do dia"/"Média de passageiros"; bonus: "BÔNUS: Volume diário de corridas..." titles, eixos "Data"/"Número de corridas"/"Dia da semana", com um mapa `DIAS_PT` traduzindo os rótulos de dia da semana que o Prophet gera em inglês). Added selective direct labels (dataviz skill: never a number on every point) — all 5 bars for Q1 (small n), only min/max for Q2's 24 bars
- [X] T030 Restyle the Prophet-generated figures (`model.plot()`, `model.plot_components()`) in iFood red instead of Prophet's default blue, via a `restyle_prophet_axis()` helper that recolors the artists the library already drew rather than reimplementing the plot — found and fixed a bug where `plot_components()`'s single-line subplots (trend, weekly) were being mis-mapped to the "observed data" ink color (a distinction that only applies to `model.plot()`'s 2-line case); re-ran (`analise_run_ifood_style2`, `result_state: SUCCESS`), re-decoded and visually verified all 4 charts show consistent iFood red across bars, trend line, and uncertainty band

**Fourth post-completion revision (2026-07-23, user feedback)**: running interactively, the user hit a wall of matplotlib `findfont: Font family 'Helvetica Neue'/'Arial' not found` warnings (Databricks Runtime only ships DejaVu Sans; matplotlib's fallback is not silent, unlike a browser's CSS font-stack fallback). While fixing that, the user asked to look at a different charting library — Plotly — for a nicer result. Prototyped Plotly + Kaleido (static PNG export) via a throwaway `_probe_plotly.py` script to inspect `plot_plotly`/`plot_components_plotly` trace structure (name/mode/fill per trace) before committing to styling code, rather than guessing — found and fixed 2 real bugs this way before they reached the final script (see T031/T032). `_probe_plotly.py` deleted (local + workspace) once done.

- [X] T031 Migrate `analise.py`'s import cell from `matplotlib`/`io` to `plotly.graph_objects` + `prophet.plot.{plot_plotly,plot_components_plotly}`; pip-install `plotly` and `"kaleido==0.2.1"` alongside `prophet` — pinned below Kaleido 1.x because that major version dropped its bundled Chromium in favor of a separate `pio.get_chrome()` download step, which would likely fail under Free Edition's restricted outbound network (constitution Principle IV); 0.2.1 is the last self-contained version. `fig.to_image()` (via Kaleido) replaces the matplotlib buffer/`savefig` dance directly (bytes out, no `io.BytesIO` needed); `displayHTML(fig.to_html(...))` replaces `display(fig)` for inline rendering
- [X] T032 Rewrite all 4 charts as Plotly figures with the same iFood palette/PT-BR labels as T028-T029, via a shared `style_layout()` helper (title/axis/grid/font styling only — color job unchanged from T028's dataviz-skill reasoning) and a `restyle_prophet_axis`-equivalent (direct trace mutation: `fig.data[i].line.color = IFOOD_RED`, matched by trace role, not reimplementing Prophet's plot). Found and fixed 2 bugs via the T030 probe/first real run: (1) Q1's `"2023-01"` x-values were auto-detected as dates by Plotly, collapsing the 5 bars into invisible slivers on a Dec 2022-May 2023 date axis (`width=0.55` was being read as 0.55 **milliseconds**) — fixed with explicit `update_xaxes(type="category")`; (2) `plot_plotly()`'s default range-selector buttons (1w/1m/6m/1y/all) and range-slider mini-chart are meaningless in a static export — disabled via `update_xaxes(rangeslider_visible=False, rangeselector=None)`. Weekly-component weekday labels (Prophet's fixed 2017-01-01(Sun)-01-07(Sat) reference week, plain date axis with no pre-set weekday ticks — confirmed via the probe) set explicitly via `tickvals`/`ticktext` in the same Dom-Sáb order as the matplotlib version. Re-ran (`analise_run_plotly3`, `result_state: SUCCESS`), re-decoded and visually verified all 4 charts: same data, crisper rendering, no font warnings (Kaleido/Chromium's CSS font-stack fallback is silent, unlike matplotlib's `findfont`)

**Checkpoint**: All 3 queries and all 4 chart images exist; `analysis/answers.md` documents both required answers and the bonus analysis, with the bonus clearly distinguishable and never presented as a substitute for the required answers.

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: End-to-end validation against the spec's Success Criteria

- [X] T023 Run `quickstart.md` Steps 1-4 end-to-end and confirm SC-001 through SC-006 all hold — confirmed: Step 1 (3 standalone SQL queries run directly, 5/24/151 rows), Step 2 (notebook run twice via `databricks jobs submit`, both SUCCESS), Step 3 (all 4 PNGs decoded and visually verified against row data), Step 4 (`analysis/answers.md` has both required tables, both required charts, both plain-language answers, and a clearly bonus-labeled Prophet section)
- [X] T024 [P] Confirm no upstream pipeline file was modified by this feature — `git status` shows changes only under `analysis/`, `specs/008-analytical-questions/`, and `.specify/memory/constitution.md` (a pre-approved `/speckit-analyze` wording fix, not pipeline code); nothing under `src/`, `contracts/`, or any prior feature's files (FR-005)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — run first.
- **Foundational (Phase 2)**: Empty — no blocking work beyond Phase 1.
- **User Stories (Phase 3-7)**: All depend only on Phase 1 (silver table
  confirmed reachable). US1/US2/US5's SQL-writing tasks (T003, T005, T015)
  are mutually independent and can run in parallel.
- **Polish (Phase 8)**: Depends on all of Phase 3-7 being complete.

### User Story Dependencies

- **US1 (P1)**: Independent — only needs Phase 1.
- **US2 (P2)**: Independent — only needs Phase 1. No dependency on US1.
- **US3 (P3)**: Depends on US1 (T004's result) and US2 (T006's result) to
  populate `answers.md` — not independent of them for content, but adds no
  new computation of its own.
- **US4 (P4)**: Depends on US1/US2's `.sql` files existing (T003, T005) and
  on US3's `answers.md` existing (T007) to embed charts into. Does not
  modify the standalone SQL path.
- **US5 (P5, bonus)**: Depends on its own `daily_trip_counts.sql` (T015)
  and, since it extends the same physical `generate_answers.py` file
  created in US4 (T010-T011), must run its script-editing tasks (T017-T019)
  *after* T010-T011 complete (same-file sequential dependency, not a
  logical dependency between the two stories' analyses).

### Within Each User Story

- SQL file creation before running/verifying it.
- Query results recorded before being embedded in `answers.md`.
- Notebook script written before being uploaded and run.
- Job run before chart payloads can be decoded.
- Charts decoded before being embedded in `answers.md`.

### Parallel Opportunities

- T003, T005, T015 (the three standalone `.sql` files) can be written in
  parallel — different files, no dependencies between them.
- T004 and T006 (running US1/US2's queries) can run in parallel once their
  respective `.sql` files exist.
- T023 and T024 (final validation) can run in parallel.

---

## Parallel Example: Standalone SQL files (US1, US2, US5)

```bash
# Launch all three standalone .sql file-writing tasks together:
Task: "Write analysis/avg_total_amount_by_month.sql"
Task: "Write analysis/avg_passenger_count_by_hour_may.sql"
Task: "Write analysis/daily_trip_counts.sql"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup.
2. Complete Phase 3: User Story 1 — the first required answer, as plain
   SQL, independently runnable.
3. **STOP and VALIDATE**: Confirm the 5-row result matches feature 006's
   known figures.

### Incremental Delivery

1. Phase 1 → Phase 3 (US1) → Phase 4 (US2): both required questions
   answered as plain SQL — satisfies the case brief's literal requirement.
2. Phase 5 (US3): both answers recorded as versioned artifacts in
   `analysis/answers.md`.
3. Phase 6 (US4): both answers gain chart images via the Databricks
   notebook — satisfies the chart requirement (FR-006).
4. Phase 7 (US5, bonus): daily trip-volume Prophet decomposition added on
   top, clearly labeled as differentiator content.
5. Phase 8: end-to-end quickstart validation.

---

## Notes

- [P] tasks = different files, no dependencies.
- [Story] label maps task to specific user story (US1-US5) for
  traceability.
- No test tasks: spec/plan explicitly treat verification as operational
  (`quickstart.md`), not unit-testable application logic.
- `analysis/charts/*.png` files are generated outputs (T013, T021), not
  hand-authored — no task creates them directly by hand.
- Commit after each phase checkpoint, consistent with this project's
  established rhythm (features 004-007).
