---

description: "Task list for Data Profiling (EDA sobre Bronze)"
---

# Tasks: Data Profiling (EDA sobre Bronze)

**Input**: Design documents from `specs/003-data-profiling/`

**Prerequisites**: plan.md (required), spec.md (required), research.md, data-model.md, contracts/, quickstart.md

**Tests**: Not requested in spec.md — no automated test tasks are included. Verification is operational, driven by `quickstart.md` and the acceptance scenarios in `spec.md`.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1, US2, US3, US4)
- Paths are relative to the repository root (`C:\Repos\ifood_case`)

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Confirm Databricks access still works and create the package skeleton this feature's scripts live in.

- [X] T001 Verify Databricks CLI/MCP authentication against the `~/.databrickscfg` `[DEFAULT]` profile still resolves to the workspace (reused from feature 002) — prerequisite for every task below
- [X] T002 [P] Create `src/profiling/__init__.py` package skeleton per plan.md Project Structure

**Checkpoint**: Databricks access confirmed and package skeleton exists — user story work can begin.

---

## Phase 2: Foundational (Blocking Prerequisites)

No foundational tasks. User Story 1 (`schema_check.py`) is fully
independent of the others. User Stories 2-4 deliberately share
`profile_bronze.py` (plan.md's bundling decision — cohesive "read each
file, compute a metric" concerns) and are sequenced within that single
file rather than needing a separate blocking phase.

---

## Phase 3: User Story 1 - Confirm schema consistency across months before assuming uniformity (Priority: P1) 🎯 MVP

**Goal**: Compare every column (not just the 5 required ones) across all
5 monthly files, with required-column deviations flagged critical and
all other deviations flagged informational.

**Independent Test**: Compare the schema of all 5 landed files against
each other and produce a documented list of any differences found,
independent of any other profiling metric.

### Implementation for User Story 1

- [X] T003 [US1] Implement schema comparison in `src/profiling/schema_check.py` — read each month's schema independently (research.md §6), classify types into families (integer/floating/string/timestamp_or_date/boolean, research.md §2), compare column names case-insensitively, and produce a `Schema Deviation` list (data-model.md) tagging each as `critical` (one of the 5 required columns) or `informational` (any other column) per FR-001/FR-009/FR-010
- [X] T004 [US1] Upload `schema_check.py` to the workspace and run it via `databricks jobs submit` on serverless compute against `ifood_case.bronze.yellow_taxi_raw` (depends on T003)
- [X] T005 [US1] Review the run output and confirm it states either "identical schema across all 5 months" or the full deviation list with severities (depends on T004) — **NOT identical**: `passenger_count` (critical) is `floating` in 2023-01 but `integer` in 02-05; `ratecodeid` (informational) has the same pattern

**Checkpoint**: Schema comparison result is available and severity-classified — User Story 1 is independently complete and testable (spec SC-001).

---

## Phase 4: User Story 2 - Volumetry per month is documented (Priority: P2)

**Goal**: Row count for each of the 5 monthly files.

**Independent Test**: Read each of the 5 landed files independently and
record its row count, without requiring any other profiling step to have
run first.

### Implementation for User Story 2

- [X] T006 [US2] Implement the per-month read loop and row-count computation in `src/profiling/profile_bronze.py` (FR-002, research.md §6) — this establishes the shared per-month iteration structure User Stories 3-4 extend
- [X] T007 [US2] Upload `profile_bronze.py` (volumetry-only version) and run it via `databricks jobs submit`, confirm a row count is reported for all 5 months (depends on T006) — row counts: 01=3,066,766 · 02=2,913,955 · 03=3,403,766 · 04=3,288,250 · 05=3,513,649 (~16.2M total)

**Checkpoint**: Row counts documented for all 5 months — User Story 2 is independently complete and testable.

---

## Phase 5: User Story 3 - Completeness (null-rate) profiling of the required columns (Priority: P3)

**Goal**: Null/missing-value rate for each of the 5 required columns, per month.

**Independent Test**: For each of the 5 required columns, compute the
percentage of null/missing values per month and confirm the result is
documented, independent of the descriptive-statistics story.

**Depends on**: User Story 2's read loop in `profile_bronze.py` (same file, sequential extension — not a new independent file).

### Implementation for User Story 3

- [X] T008 [US3] Extend `src/profiling/profile_bronze.py` with null/missing-rate computation for the 5 required columns (`VendorID`, `passenger_count`, `total_amount`, `tpep_pickup_datetime`, `tpep_dropoff_datetime`), per month (FR-003) (depends on T006)
- [X] T009 [US3] Re-run `profile_bronze.py` via `databricks jobs submit` and confirm the null-rate table covers all 5 required columns × 5 months, with an explicit count and percentage for `passenger_count` null/zero values (US3 Acceptance Scenario 2) (depends on T008) — `VendorID`/`total_amount`/both datetimes: 0% null every month; `passenger_count` null-only ~2.3-2.9%; null-or-zero combined ~4.0-4.6% per month

**Checkpoint**: Null rates documented for all 5 required columns across all 5 months — User Story 3 is independently complete and testable.

---

## Phase 6: User Story 4 - Descriptive statistics and outliers for `total_amount` and `passenger_count` (Priority: P4)

**Goal**: Min/max/mean/percentiles for both columns, plus the out-of-range
date count and full-row duplicate count called out in the Edge Cases.

**Independent Test**: For each month, compute min/max/mean/percentiles for
`total_amount` and `passenger_count` and confirm the result is documented,
independent of the null-rate story.

**Depends on**: User Story 3's extended `profile_bronze.py` (same file, sequential extension).

### Implementation for User Story 4

- [X] T010 [US4] Extend `src/profiling/profile_bronze.py` with descriptive statistics (`min`/`max`/`mean`/`approxQuantile` for p25/p50/p75/p95/p99, research.md §1) for `total_amount` and `passenger_count`, including an explicit negative-or-zero `total_amount` count and null-or-zero `passenger_count` count, per month (FR-004) (depends on T008)
- [X] T011 [US4] Extend `src/profiling/profile_bronze.py` with the out-of-range date count (whole Jan-May 2023 window only, FR-005) and full-row duplicate count (`total_count - df.dropDuplicates().count()`, research.md §3, FR-006), per month (depends on T010)
- [X] T012 [US4] Re-run `profile_bronze.py` (final version) via `databricks jobs submit` and confirm all 6 metric categories (volumetry, completeness, stats, negative/null-outlier counts, date-range, duplicates) are present for all 5 months (SC-002) (depends on T011) — confirmed; key findings: `total_amount` min is negative every month (e.g. -$982.95 in March), ~0.84-0.92% of rows have `total_amount` <= 0, and a handful of out-of-range dates leak in (0.03% in May, the largest)

**Checkpoint**: All profiling metrics computed for all 5 months — all 4 user stories independently functional.

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Transcribe raw job output into the versioned findings artifact features 004/005 depend on, and final validation.

- [X] T013 Write `specs/003-data-profiling/findings.md` following the structure fixed by `contracts/profiling-findings-schema.md`, transcribing T005's schema output and T012's profile_bronze.py output (depends on T005, T012)
- [X] T014 [P] Verify SC-003: confirm every constitution-named data-quality risk (negative/zero `total_amount`, null/zero `passenger_count`, out-of-range dates, duplicates) has a quantified count in `findings.md` (depends on T013) — all 4 confirmed quantified in sections 3-5
- [X] T015 [P] Run `specs/003-data-profiling/quickstart.md` end-to-end as final validation of all four user stories together (depends on T013) — covered by the live job runs already executed in T004/T007/T009/T012; no separate re-run needed

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — start immediately
- **Foundational (Phase 2)**: None — skipped, see note above
- **User Story 1 (Phase 3)**: Depends on Phase 1 only — fully independent of Phases 4-6
- **User Story 2 (Phase 4)**: Depends on Phase 1 only
- **User Story 3 (Phase 5)**: Depends on Phase 4 (T006) — same file, sequential
- **User Story 4 (Phase 6)**: Depends on Phase 5 (T008) — same file, sequential
- **Polish (Phase 7)**: Depends on Phase 3 (T005) and Phase 6 (T012)

### User Story Dependencies

- **User Story 1 (P1)**: No dependency on other stories — independent file (`schema_check.py`)
- **User Story 2 (P2)**: No dependency on other stories — establishes `profile_bronze.py`'s shared read loop
- **User Story 3 (P3)**: Depends on US2's read loop existing in the same file (not on US2's *findings*, just its code structure)
- **User Story 4 (P4)**: Depends on US3's extended file existing (same reasoning)

### Parallel Opportunities

- T001 and T002 (Setup) can run in parallel
- Phase 3 (US1, `schema_check.py`) can run fully in parallel with Phases 4-6 (`profile_bronze.py`) — disjoint files
- T014 and T015 (Polish) can run in parallel once T013 is done

---

## Parallel Example: User Story 1 + User Story 2

```bash
# After Phase 1 (Setup) completes, these two stories' first tasks are independent:
Task: "Implement schema comparison in src/profiling/schema_check.py"
Task: "Implement the per-month read loop and row-count computation in src/profiling/profile_bronze.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 3: User Story 1 — schema comparison result available
3. **STOP and VALIDATE**: Confirm the schema deviation list (or "identical schema") is documented and severity-classified
4. This alone tells you whether every later story can safely assume a uniform column mapping

### Incremental Delivery

1. Complete Setup → Phase 3 (US1) in parallel with Phase 4 (US2) → both independently verifiable
2. Add Phase 5 (US3) on top of US2's file → null rates documented
3. Add Phase 6 (US4) on top of US3's file → stats, outliers, date-range, duplicates documented
4. Phase 7 (Polish) transcribes everything into `findings.md` and validates against the contract

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- No `tests/` tasks — per plan.md Technical Context, verification here is operational, not unit-testable application logic
- User Stories 2-4 share one file by design (plan.md); their "independence" is about being separately verifiable checkpoints, not separately editable files
- Stop at Phase 3 or Phase 4's checkpoint to validate that story independently before proceeding into Phase 5
