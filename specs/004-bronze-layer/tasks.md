---

description: "Task list for Camada Bronze"
---

# Tasks: Camada Bronze

**Input**: Design documents from `specs/004-bronze-layer/`

**Prerequisites**: plan.md (required), spec.md (required), research.md, data-model.md, contracts/, quickstart.md

**Tests**: Not requested in spec.md — no automated test tasks are included. Verification is operational, driven by `quickstart.md` and the acceptance scenarios in `spec.md`.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1, US2, US3, US4)
- Paths are relative to the repository root (`C:\Repos\ifood_case`)

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Confirm Databricks access still works and create the package skeleton this feature's scripts live in.

- [ ] T001 Verify Databricks CLI/MCP authentication against the `~/.databrickscfg` `[DEFAULT]` profile still resolves to the workspace (reused from features 002-003) — prerequisite for every task below
- [ ] T002 [P] Create `src/bronze/__init__.py` package skeleton per plan.md Project Structure

**Checkpoint**: Databricks access confirmed and package skeleton exists — user story work can begin.

---

## Phase 2: Foundational (Blocking Prerequisites)

No separate foundational phase. Unlike feature 003 (where User Story 1
was fully independent of the rest), **User Story 1 itself is the blocking
prerequisite here**: User Story 2 reads from `ifood_case.landing.yellow_taxi_raw`,
which only exists once User Story 1's move has run (spec.md, User Story 2
"Why this priority"). See User Story Dependencies below.

---

## Phase 3: User Story 1 - Landing zone keeps its own namespace, separate from bronze (Priority: P1) 🎯 MVP

**Goal**: Move the landing zone from `ifood_case.bronze` to `ifood_case.landing`
without data loss, freeing the `bronze` name for the new Delta table.

**Independent Test**: After the move, the same 5 parquet files are
listable and byte-identical to their originals at the new location,
independent of whether the bronze table has been created yet.

### Implementation for User Story 1

- [ ] T003 [US1] Implement the landing-zone move in `src/bronze/rename_landing_schema.py`: create `ifood_case.landing` schema + `yellow_taxi_raw` volume, copy the 5 files from `ifood_case.bronze.yellow_taxi_raw`, verify byte-for-byte size match against feature 002's recorded sizes (47,673,370 / 47,748,012 / 56,127,762 / 54,222,699 / 58,654,627 bytes for Jan-May), then drop the old `ifood_case.bronze` schema/volume **only if** verification passes (FR-001, research.md §1)
- [ ] T004 [US1] Upload `rename_landing_schema.py` to the workspace and run it via `databricks jobs submit` on serverless compute (depends on T003)
- [ ] T005 [US1] Review the run output and confirm all 5 files are listed at `ifood_case.landing.yellow_taxi_raw` with sizes matching feature 002's records, and the old `bronze`-named schema no longer exists (SC-001) (depends on T004)

**Checkpoint**: Landing zone moved and verified — User Story 1 is independently complete and testable (spec SC-001).

---

## Phase 4: User Story 2 - A consistent-schema Delta table exists for the 5 months combined (Priority: P2)

**Goal**: Read the 5 months from the (now-renamed) landing zone, validate
their schema against feature 003's known baseline, cast the two drifted
columns, and combine them into one schema-consistent, metadata-tagged
DataFrame.

**Independent Test**: Inspect the combined DataFrame's schema and confirm
`passenger_count`/`ratecodeid` are `IntegerType` everywhere and
`_source_file`/`_ingested_at` are present — checkable before Phase 5 adds
dedup and persists the table.

**Depends on**: User Story 1 (Phase 3, T005) — reads from `ifood_case.landing.yellow_taxi_raw`.

### Implementation for User Story 2

- [ ] T006 [US2] Implement the pre-transformation schema assertion in `src/bronze/ingest_bronze.py`: for each of the 5 months, validate the actual schema against feature 003's documented baseline (`../003-data-profiling/findings.md` §1 — 19 columns, with `passenger_count`/`ratecodeid` as the only known type-family deviations); raise an exception and let the job fail if any file's schema doesn't match (FR-008, research.md §6) (depends on T005)
- [ ] T007 [US2] Extend `ingest_bronze.py`: read each of the 5 months from `ifood_case.landing.yellow_taxi_raw`, add `_source_file` via `input_file_name()` immediately after each month's read (before any shuffle — research.md §4), and cast `passenger_count`/`ratecodeid` to `IntegerType` per month (FR-003/FR-004, research.md §2 and §4) (depends on T006)
- [ ] T008 [US2] Extend `ingest_bronze.py`: combine the 5 per-month DataFrames with `unionByName(allowMissingColumns=False)`, and add a single `_ingested_at` value (`current_timestamp()`, computed once for the whole batch) (FR-002/FR-004, research.md §3-4) (depends on T007)

**Checkpoint**: The combined, schema-consistent, metadata-tagged DataFrame exists in code (pre-dedup, not yet persisted) — its schema is independently inspectable (spec SC-002 groundwork).

---

## Phase 5: User Story 3 - Exact duplicate rows are not carried into bronze (Priority: P3)

**Goal**: Deduplicate the combined DataFrame on its original source
columns only, then persist it as `ifood_case.bronze.yellow_taxi_trips`
and report the run's volume accounting.

**Independent Test**: Confirm the dedup step executes and reports a
duplicate count (0, per feature 003's finding), independent of the
schema/cast logic already verified in Phase 4.

**Depends on**: User Story 2 (Phase 4, T008) — same file, sequential extension.

### Implementation for User Story 3

- [ ] T009 [US3] Extend `ingest_bronze.py`: apply `dropDuplicates(subset=<the 19 original source column names>)` to the combined DataFrame from T008, explicitly excluding `_source_file`/`_ingested_at` from the subset so they can't mask a real duplicate (FR-005, research.md §4) (depends on T008)
- [ ] T010 [US3] Extend `ingest_bronze.py`: write the deduplicated DataFrame to the managed Delta table `ifood_case.bronze.yellow_taxi_trips`, and compute/report `rows_read`, `rows_written`, `duplicates_removed`, `schema_validation_status` (FR-002/FR-007, data-model.md "Bronze Ingestion Run") (depends on T009)
- [ ] T011 [US3] Upload `ingest_bronze.py` to the workspace and run it via `databricks jobs submit` on serverless compute (depends on T010)
- [ ] T012 [US3] Review the run output: confirm `duplicates_removed = 0` (matching feature 003's finding of 0 full-row duplicates in every month) and `rows_written` equals feature 003's total (16,186,386) minus `duplicates_removed` (SC-003) (depends on T011)

**Checkpoint**: `ifood_case.bronze.yellow_taxi_trips` exists, deduplicated, with a reported run summary — User Stories 2 and 3 are both independently verifiable now (SC-002, SC-003).

---

## Phase 6: User Story 4 - Bronze applies no business-rule filtering (Priority: P4, guardrail)

**Goal**: Prove, by query, that bronze preserves every row feature 003
found — including the known-defect ones — unfiltered.

**Independent Test**: Compare row counts and known-defect rates between
bronze and the feature 003 profiling baseline.

**Depends on**: User Story 3 (Phase 5, T012) — the table must exist to query.

### Implementation for User Story 4

- [ ] T013 [US4] Run the SC-004 guardrail queries (quickstart.md Step 3) against `ifood_case.bronze.yellow_taxi_trips` — counts for `total_amount <= 0`, `passenger_count IS NULL OR passenger_count = 0`, out-of-range `tpep_pickup_datetime`/`tpep_dropoff_datetime`, and `tpep_dropoff_datetime < tpep_pickup_datetime` — confirm the first three match feature 003's per-month rates (e.g. ~144,146 total negative/zero `total_amount` rows across all 5 months), and record the fourth as this pipeline's first-ever measurement of that condition (no feature 003 baseline exists to compare against — analyze finding D1) (depends on T012)

**Checkpoint**: Bronze confirmed to preserve every known-defect row unfiltered — all 4 user stories independently functional.

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Record the run's evidence as a versioned artifact, document the Free-Edition workaround per the constitution, and run final validation.

- [ ] T014 Write `specs/004-bronze-layer/ingestion-log.md` from T011's JSON output (`rows_read`, `rows_written`, `duplicates_removed`, `schema_validation_status`, `executed_at`) per research.md §5 (depends on T011)
- [ ] T015 [P] Add an entry to `DECISOES_PROJETO.md` documenting the schema-rename workaround actually used (copy+verify+delete, since Unity Catalog has no `ALTER SCHEMA ... RENAME TO`) per Constitution Principle IV — same convention as feature 002's §2.1-2.3 entries (depends on T005)
- [ ] T016 [P] Run `specs/004-bronze-layer/quickstart.md` end-to-end as final validation of all four user stories together (depends on T005, T012, T013) — covered by the live job runs already executed in T004/T011/T013; no separate re-run needed

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — start immediately
- **Foundational (Phase 2)**: None as a separate phase — User Story 1 fills this blocking role, see below
- **User Story 1 (Phase 3)**: Depends on Phase 1 only
- **User Story 2 (Phase 4)**: Depends on Phase 3 (T005) — reads from the renamed landing zone
- **User Story 3 (Phase 5)**: Depends on Phase 4 (T008) — same file, sequential
- **User Story 4 (Phase 6)**: Depends on Phase 5 (T012) — queries the persisted table
- **Polish (Phase 7)**: Depends on Phase 3 (T005), Phase 5 (T011/T012), and Phase 6 (T013)

### User Story Dependencies

- **User Story 1 (P1)**: No dependency on other stories — independent file (`rename_landing_schema.py`)
- **User Story 2 (P2)**: Depends on User Story 1 having completed (the landing zone must exist at its new address before it can be read) — this is a real, spec-documented dependency (spec.md, US2 "Why this priority"), unlike feature 003 where every story was mutually independent
- **User Story 3 (P3)**: Depends on User Story 2's combined DataFrame existing in the same file (not on US2's *acceptance being separately re-verified*, just its code)
- **User Story 4 (P4)**: Depends on User Story 3's persisted table existing to query

### Parallel Opportunities

- T001 and T002 (Setup) can run in parallel
- T015 (Polish, DECISOES_PROJETO.md update) can run in parallel with T014/T016 once its own dependency (T005) is done — different files
- No user story phase here can run fully in parallel with another (unlike feature 003's US1/US2-4 split) — US1→US2→US3→US4 is a real, mostly linear chain for this feature, because each stage reads the previous stage's physical output (renamed schema → combined DataFrame → persisted table → query-based verification)

---

## Parallel Example: Setup

```bash
# These two Setup tasks are independent:
Task: "Verify Databricks CLI/MCP authentication still resolves"
Task: "Create src/bronze/__init__.py package skeleton"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 3: User Story 1 — landing zone moved and verified
3. **STOP and VALIDATE**: Confirm all 5 files are listable and byte-identical at `ifood_case.landing.yellow_taxi_raw`
4. This alone unblocks every later feature that needs to read from the landing zone, even before the bronze table exists

### Incremental Delivery

1. Complete Setup → Phase 3 (US1) → landing zone moved (MVP-equivalent for this feature: nothing downstream can start without it)
2. Add Phase 4 (US2) → schema-consistent combined DataFrame confirmed in code
3. Add Phase 5 (US3) → bronze table persisted, dedup and volume counts confirmed
4. Add Phase 6 (US4) → guardrail queries confirm no business-rule filtering
5. Phase 7 (Polish) records the run's evidence and the constitution-required workaround documentation

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- No `tests/` tasks — per plan.md Technical Context, verification here is operational, not unit-testable application logic
- Unlike feature 003, this feature's user stories form a mostly linear chain (US1→US2→US3→US4), not parallel-independent stories — each one's physical output is the next one's input
- Stop at Phase 3's checkpoint to validate the landing-zone move independently before proceeding into Phase 4
