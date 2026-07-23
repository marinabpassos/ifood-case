---

description: "Task list for Data Quality & Camada Silver"
---

# Tasks: Data Quality & Camada Silver

**Input**: Design documents from `specs/006-silver-data-quality/`

**Prerequisites**: plan.md (required), spec.md (required), research.md, data-model.md, quickstart.md

**Tests**: Not requested in spec.md — no automated test tasks are included. Verification is operational, driven by `quickstart.md` and the acceptance scenarios in `spec.md`.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1, US2, US3)
- Paths are relative to the repository root (`C:\Repos\ifood_case`)

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Confirm Databricks access still works and create the package skeleton this feature's script lives in.

- [X] T001 [P] Create `src/silver/__init__.py` package skeleton per plan.md Project Structure
- [X] T002 Verify Databricks CLI/MCP authentication against the `~/.databrickscfg` `[DEFAULT]` profile still resolves to the workspace (reused from features 002-004; see `CLAUDE.md` for the PATH fix if needed) — prerequisite for every execution task below

**Checkpoint**: Databricks access confirmed and package skeleton exists.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Load the contract and confirm bronze's schema is compatible with it — a true blocking prerequisite for all 3 user stories (rule conditions, column selection, and the report all depend on the contract being loaded and the schema being trustworthy first).

**⚠️ CRITICAL**: No user story work can begin until this phase is complete.

- [X] T003 Implement contract loading in `src/silver/build_silver.py`: parse `contracts/nyc_taxi_silver.yaml` via `PyYAML`, extracting table identity, the `columns` list, and the `quality_rules` list (research.md §1) — the contract is uploaded alongside the script as a plain Workspace File (`databricks workspace import --format AUTO`, confirmed `object_type: FILE`) and read via `open()` at runtime; see `CLAUDE.md` for the reusable pattern
- [X] T004 Implement the schema-compatibility assertion in `build_silver.py`: reuse the `type_family()` classifier already established in `src/profiling/schema_check.py`/`src/bronze/ingest_bronze.py`, map each contract business type (`integer`→`integer`, `decimal`→`floating`, `timestamp`→`timestamp_or_date`) and confirm bronze's 5 business columns exist with a matching family; raise an exception and let the job fail if any column is missing or mismatched (FR-002, research.md §3) (depends on T003)

**Checkpoint**: Contract loaded, schema confirmed compatible (or the job fails loudly) — user story implementation can now begin.

---

## Phase 3: User Story 1 - Only valid trips reach the analytical layer (Priority: P1) 🎯 MVP

**Goal**: Evaluate all 4 drop rules independently against the full bronze input and compute the combined drop mask.

**Independent Test**: Query `ifood_case.silver.yellow_taxi_trips` for each of the 4 drop conditions and confirm zero matching rows (once the table exists — this story's logic is exercised end-to-end at Polish's job run).

**Depends on**: Phase 2 (T004) — rule conditions must run against a schema already confirmed compatible.

### Implementation for User Story 1

- [X] T005 [US1] Read `ifood_case.bronze.yellow_taxi_trips` and add one boolean column per drop rule to `build_silver.py`, each computed via `F.expr(rule["condition"])` from the loaded contract, evaluated against the full, unfiltered bronze DataFrame (FR-003, research.md §1-2) (depends on T004)
- [X] T006 [US1] Compute each rule's independent count (`df.filter(<rule column>).count()`) and the combined OR drop mask across all 4 rule columns; compute `total_dropped` as the count of rows matching the combined mask (FR-003, research.md §2) (depends on T005)
- [X] T007 [US1] Code-review confirmation: verify no duplicate-detection/removal logic was added anywhere in `build_silver.py` (FR-004) — silver inherits bronze's already-deduplicated input, per the contract's `duplicates: resolved_upstream` policy (depends on T006)

**Checkpoint**: Independent per-rule counts and the combined drop mask are implemented — User Story 1's core logic exists (verified against real data at Polish's job run, spec SC-001).

---

## Phase 4: User Story 2 - The written table matches the contract exactly (Priority: P2)

**Goal**: Select only rows passing all 4 rules, produce exactly the contract's 6 columns, and write the table.

**Independent Test**: Compare `DESCRIBE TABLE ifood_case.silver.yellow_taxi_trips` against `contracts/nyc_taxi_silver.yaml`'s `columns` list.

**Depends on**: User Story 1 (Phase 3, T006) — needs the combined drop mask to select the final row set.

### Implementation for User Story 2

- [X] T008 [US2] Apply the combined drop mask from T006 (keep rows failing none of the 4 rules), select exactly the 5 business columns, and add `_silver_processed_at` (a single `current_timestamp()` value shared by the whole batch, research.md §5) to `build_silver.py` (FR-005/FR-006) (depends on T006)
- [X] T009 [US2] Add `CREATE SCHEMA IF NOT EXISTS ifood_case.silver` immediately before the table write in `build_silver.py` (research.md §4 — proactively avoids the `SCHEMA_NOT_FOUND` bug hit during feature 004), then write the managed Delta table `ifood_case.silver.yellow_taxi_trips` (FR-006) (depends on T008)

**Checkpoint**: Silver table write logic complete, producing exactly the contract's 6-column schema — User Story 2's core logic exists (verified at Polish, spec SC-002).

---

## Phase 5: User Story 3 - Every rule's impact is measured and reported (Priority: P3)

**Goal**: Return a complete report of rows read/written, the 4 independent counts, the total-dropped count, and the schema-assertion status.

**Independent Test**: Confirm the report contains all required fields, independent of what the actual numbers turn out to be.

**Depends on**: User Story 2 (Phase 4, T009) — `rows_written` is only meaningful once the write exists.

### Implementation for User Story 3

- [X] T010 [US3] Implement the final report dict in `build_silver.py`: `rows_read`, `rows_written`, the 4 named per-rule counts (`total_amount_negative_or_zero_count`, `passenger_count_null_or_zero_count`, `dropoff_before_pickup_count`, `out_of_range_dates_count`), `total_dropped`, `schema_assertion_status`, per data-model.md "Silver Data Quality Run" (FR-007) (depends on T009)

**Checkpoint**: Full report implemented — all 3 user stories' logic exists in `build_silver.py` (spec SC-003 verified at Polish).

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Run the completed script against the real workspace, verify all 3 stories against real data, and record the evidence.

- [X] T011 Upload `build_silver.py` to the workspace and run it via `databricks jobs submit` on serverless compute (depends on T010) — run 1083792319793578, SUCCESS on the first attempt, 57s execution
- [X] T012 Review the run output: confirm `schema_assertion_status: "pass"` and record `rows_read`/`rows_written`/the 4 per-rule counts/`total_dropped` (depends on T011) — confirmed: `{"rows_read": 16186386, "rows_written": 15339417, "total_amount_negative_or_zero_count": 144146, "passenger_count_null_or_zero_count": 702146, "dropoff_before_pickup_count": 795, "out_of_range_dates_count": 1077, "total_dropped": 846969, "schema_assertion_status": "pass"}`
- [X] T013 Run quickstart.md Steps 2-3 (SQL guardrail queries + `DESCRIBE TABLE`) against `ifood_case.silver.yellow_taxi_trips` and confirm all 4 guardrail queries return 0 and the schema matches the contract's 6 columns (SC-001/SC-002) (depends on T012) — confirmed: all 4 queries returned 0; `DESCRIBE TABLE` shows exactly `VendorID`/`passenger_count`/`total_amount`/`tpep_pickup_datetime`/`tpep_dropoff_datetime`/`_silver_processed_at`
- [X] T014 Run quickstart.md Step 4: compare the 4 independent counts from T012 against feature 004's `ingestion-log.md` baseline (144,146 / 702,146 / 795 / 1,077) and confirm an exact match (SC-003) (depends on T012) — confirmed exact match on all 4
- [X] T015 [P] Write `specs/006-silver-data-quality/dq-run-log.md` from T012's JSON output plus T013/T014's verification results (research.md §6) (depends on T013, T014)
- [X] T016 [P] Confirm `contracts/nyc_taxi_silver.yaml` has no diff introduced by this feature's implementation (`git diff contracts/nyc_taxi_silver.yaml` clean) — this feature implements the already-decided contract, it does not redecide it (FR-008) — confirmed clean
- [X] T017 [P] Run quickstart.md Step 5: a sample `GROUP BY` aggregation directly against `ifood_case.silver.yellow_taxi_trips` with no extra cleaning clause, confirming the table is analysis-ready (SC-004) (depends on T013) — confirmed: avg `total_amount` by month (27.46/27.37/28.29/28.78/29.45), consistent with feature 003's profiling means

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — start immediately
- **Foundational (Phase 2)**: No dependency on Databricks access to *write* T003/T004's code — parsing a local YAML and writing assertion logic needs nothing from the platform. Only *running* the finished script (Polish, T011) needs Phase 1's T002 confirmed. Still BLOCKS all user stories at the content level (contract loading + schema assertion are genuine prerequisites for the rule/column/report logic)
- **User Story 1 (Phase 3)**: Depends on Phase 2 (T004)
- **User Story 2 (Phase 4)**: Depends on Phase 3 (T006) — needs the drop mask
- **User Story 3 (Phase 5)**: Depends on Phase 4 (T009) — needs the write to exist
- **Polish (Phase 6)**: Depends on Phase 5 (T010) — the script must be complete before it's run for real

### User Story Dependencies

- **User Story 1 (P1)**: Depends on the Foundational phase's schema assertion, not on any other story
- **User Story 2 (P2)**: Depends on User Story 1's combined drop mask existing in the same file (content-level, not a separate blocking phase)
- **User Story 3 (P3)**: Depends on User Story 2's write existing (same file, sequential)

### Parallel Opportunities

- T001 (Setup) can run in parallel with T002
- This feature's user stories form a strictly linear chain (US1→US2→US3, same as feature 004's chain, unlike feature 005's US2/US3 parallel split) — each stage's output is the next stage's input within the same script
- T015 (Polish) has no parallel partner left by that point — final documentation step

---

## Parallel Example: Setup

```bash
# These two Setup tasks are independent:
Task: "Create src/silver/__init__.py package skeleton"
Task: "Verify Databricks CLI/MCP authentication still resolves"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational — contract loaded, schema confirmed compatible
3. Complete Phase 3: User Story 1 — independent rule counts and combined drop mask computed
4. **STOP and VALIDATE**: Confirm the rule logic is correct in code review before adding the write (Phase 4) on top of it
5. This alone establishes the core data-quality logic the rest of the feature builds on

### Incremental Delivery

1. Complete Setup + Foundational → contract loaded, schema assertion in place
2. Add Phase 3 (US1) → rule evaluation and drop mask computed
3. Add Phase 4 (US2) → table written, matching the contract's schema
4. Add Phase 5 (US3) → full report available
5. Phase 6 (Polish) runs the finished script for real and records the evidence

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- No `tests/` tasks — per plan.md Technical Context, verification here is operational
- Unlike feature 005, this feature needs Databricks CLI/MCP access again (Phase 6 onward)
- The Foundational phase (Phase 2) is a genuine blocking prerequisite here — contract loading and schema assertion serve all 3 user stories, unlike features 004/005 where no such shared blocker existed
- Stop at Phase 3's checkpoint to review the rule logic independently before proceeding into Phase 4
