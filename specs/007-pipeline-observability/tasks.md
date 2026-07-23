---

description: "Task list for Observability da Pipeline"
---

# Tasks: Observability da Pipeline

**Input**: Design documents from `specs/007-pipeline-observability/`

**Prerequisites**: plan.md (required), spec.md (required), research.md, data-model.md, quickstart.md

**Tests**: Not requested in spec.md — no automated test tasks are included. Verification is operational, driven by `quickstart.md` and the acceptance scenarios in `spec.md`.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1, US2, US3)
- Paths are relative to the repository root (`C:\Repos\ifood_case`)

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Confirm Databricks access still works — no new package needed (plan.md: this feature modifies two existing scripts, adds none).

- [ ] T001 Verify Databricks CLI/MCP authentication against the `~/.databrickscfg` `[DEFAULT]` profile still resolves to the workspace (reused from features 002-006; see `CLAUDE.md` for the PATH fix if needed)

**Checkpoint**: Databricks access confirmed.

---

## Phase 2: Foundational (Blocking Prerequisites)

No foundational phase. `ingest_bronze.py` and `build_silver.py` are
extended independently (each gets its own copy of the logging helper,
research.md §2) — there is no shared artifact both depend on beyond
Setup.

---

## Phase 3: User Story 1 - Every pipeline execution is queryable, not just readable in markdown (Priority: P1) 🎯 MVP

**Goal**: Both scripts append one row each to `ifood_case.silver._pipeline_run_log` as the final step of their own execution, including on the (already-existing) anticipated-failure path, and a new broad catch for unanticipated crashes.

**Independent Test**: Query `ifood_case.silver._pipeline_run_log` and confirm one row per pipeline stage with the expected metrics — independent of the alerting or lineage stories.

### Implementation for User Story 1

- [ ] T002 [US1] Define the log-row `StructType` (data-model.md "Pipeline Run Log Entry") and a `write_run_log(spark, entry: dict)` helper in `src/bronze/ingest_bronze.py`: builds a one-row DataFrame and appends it to `ifood_case.silver._pipeline_run_log` (`CREATE TABLE IF NOT EXISTS` semantics via `mode("append")`'s first-write behavior) (research.md §1)
- [ ] T003 [US1] In `ingest_bronze.py`'s `__main__` block, capture a start timestamp, run the existing ingestion logic unchanged, then call `write_run_log()` with `pipeline_stage="bronze"`, the existing result dict's `schema_validation_status`/`rows_read`/`rows_written`, `metrics={"duplicates_removed": ...}`, and `duration_seconds` (FR-002) (depends on T002)
- [ ] T004 [US1] [P] Define the same log-row `StructType` and `write_run_log()` helper in `src/silver/build_silver.py` (duplicated, not imported — research.md §2)
- [ ] T005 [US1] In `build_silver.py`'s `__main__` block, capture a start timestamp, run the existing cleaning logic unchanged, then call `write_run_log()` with `pipeline_stage="silver"`, the existing result dict's `schema_assertion_status`/`rows_read`/`rows_written`, `metrics={"total_amount_negative_or_zero_count": ..., ...}`, and `duration_seconds` (FR-002) (depends on T004)
- [ ] T006 [US1] Wrap each script's `__main__` block in a broad `try/except Exception` (research.md §3): on any exception not already caught inside `ingest_bronze()`/`build_silver()`, call `write_run_log()` with `status="failed"` and the error message, then re-raise so the Databricks job still reports FAILED (FR-003) (depends on T003, T005)

**Checkpoint**: Both scripts write a log row on every execution, success or failure — User Story 1's core logic exists (verified against real data at Polish's re-runs, spec SC-001).

---

## Phase 4: User Story 2 - A real data-quality issue triggers a visible alert (Priority: P2)

**Goal**: Any named metric whose rate exceeds 1% of rows read produces a recorded alert plus a console banner.

**Independent Test**: Confirm the rule already known to exceed the threshold (`passenger_count_null_or_zero`, ~4.34%) produces a recorded alert — independent of the lineage story.

**Depends on**: User Story 1 (Phase 3, T006) — alerts populate a field on the same log row US1 builds.

### Implementation for User Story 2

- [ ] T007 [US2] Implement a `check_alerts(metrics: dict, rows_read: int) -> list[str]` helper in `ingest_bronze.py`: for `duplicates_removed`, compute `count / rows_read`, append a message if `> 0.01` (research.md §4) (depends on T006)
- [ ] T008 [US2] [P] Same `check_alerts()` helper in `build_silver.py`, applied to each of the 4 named rule counts (not `total_dropped`, which isn't a single rule) (research.md §4) (depends on T006)
- [ ] T009 [US2] Wire `check_alerts()`'s return value into each script's `write_run_log()` call as the `alerts` field, and `print()` a clearly-marked banner for each triggered alert (FR-004) (depends on T007, T008)

**Checkpoint**: Alert logic implemented in both scripts — User Story 2's core logic exists (verified against real data at Polish, spec SC-002).

---

## Phase 5: User Story 3 - Data lineage is traceable without a custom-built system (Priority: P3)

**Goal**: Confirm landing→bronze→silver lineage via Unity Catalog's two native mechanisms (research.md §5) — no code to write, verification only.

**Independent Test**: Query `system.access.table_lineage` and Catalog Explorer's lineage UI independently of US1/US2's code changes (lineage already exists from prior runs).

### Implementation for User Story 3

- [ ] T010 [US3] Run quickstart.md Step 4's `system.access.table_lineage` query for `ifood_case.silver.yellow_taxi_trips` and confirm `ifood_case.bronze.yellow_taxi_trips` appears as the source (spec Acceptance Scenario 1)
- [ ] T011 [US3] Verify in Catalog Explorer's Lineage tab for `ifood_case.bronze.yellow_taxi_trips` that `ifood_case.landing.yellow_taxi_raw` appears as an upstream source (spec Acceptance Scenario 2 — UI-only, per research.md §5's platform constraint)

**Checkpoint**: Both lineage mechanisms verified — User Story 3 independently complete (spec SC-003).

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Re-run both extended pipelines for real, verify all 3 stories against fresh execution evidence, and record findings.

- [ ] T012 Upload `ingest_bronze.py` to the workspace and re-run it via `databricks jobs submit` on serverless compute (depends on T009)
- [ ] T013 Upload `build_silver.py` to the workspace and re-run it via `databricks jobs submit` — **after** T012 completes, since silver reads from bronze (depends on T012, T009)
- [ ] T014 Run quickstart.md Step 2: query `ifood_case.silver._pipeline_run_log` and confirm ≥2 rows (bronze + silver), all core fields populated (SC-001) (depends on T013)
- [ ] T015 Run quickstart.md Step 3: confirm the silver run's `alerts` contains the `passenger_count_null_or_zero` entry and bronze's `alerts` is empty (SC-002) (depends on T013)
- [ ] T016 Confirm the re-run's `rows_read`/`rows_written`/per-rule counts match feature 004's `ingestion-log.md` and feature 006's `dq-run-log.md` exactly (SC-004) (depends on T014)
- [ ] T017 [P] Write `specs/007-pipeline-observability/observability-log.md` summarizing the run-log query results (T014-T016) and the lineage verification (T010-T011)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — start immediately
- **Foundational (Phase 2)**: None as a separate phase — see note above
- **User Story 1 (Phase 3)**: Depends on Phase 1 only
- **User Story 2 (Phase 4)**: Depends on Phase 3 (T006) — alerts populate the log row US1 builds
- **User Story 3 (Phase 5)**: No dependency on Phase 3/4 — pure verification of an already-existing platform capability
- **Polish (Phase 6)**: Depends on Phase 4 (T009) for the re-runs (T012/T013); T017 also depends on Phase 5 (T010, T011)

### User Story Dependencies

- **User Story 1 (P1)**: No dependency on other stories
- **User Story 2 (P2)**: Depends on User Story 1's log-row structure existing in the same two files (content-level, not a separate blocking phase)
- **User Story 3 (P3)**: Fully independent of User Story 1/2's code — lineage already exists from prior runs of bronze/silver, this story only verifies it

### Parallel Opportunities

- T004 (US1, `build_silver.py`) can be written in parallel with T002-T003 (US1, `ingest_bronze.py`) — different files
- T008 (US2, `build_silver.py`) can be written in parallel with T007 (US2, `ingest_bronze.py`) — different files
- Phase 5 (US3, T010-T011) can run fully in parallel with Phases 3-4 — no shared dependency
- T017 (Polish) has no parallel partner left by that point — final documentation step

---

## Parallel Example: User Story 1

```bash
# These two US1 tasks touch different files:
Task: "Define log-row StructType + write_run_log() in src/bronze/ingest_bronze.py"
Task: "Define log-row StructType + write_run_log() in src/silver/build_silver.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 3: User Story 1 — both scripts log every execution
3. **STOP and VALIDATE**: Re-run both scripts once, confirm `_pipeline_run_log` has 2 rows with core fields populated
4. This alone satisfies Principle III's "queryable table" mandate even before alerting or lineage verification are added

### Incremental Delivery

1. Complete Setup → Phase 3 (US1) → both scripts log on every run
2. Add Phase 4 (US2) → alert logic wired into the same log rows
3. Add Phase 5 (US3), independent of 3-4 → lineage verified via both native mechanisms
4. Phase 6 (Polish) re-runs both pipelines for real and records the combined evidence

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- No `tests/` tasks — per plan.md Technical Context, verification here is operational
- This feature needs Databricks CLI/MCP access from Phase 6 onward (re-running the pipelines); Phase 5 (US3) also needs it for the lineage queries, but doesn't depend on Phase 3/4's code changes
- Stop at Phase 3's checkpoint to validate logging independently before proceeding into Phase 4
