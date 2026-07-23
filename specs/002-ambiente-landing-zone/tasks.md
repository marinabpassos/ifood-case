---

description: "Task list for Ambiente & Landing Zone"
---

# Tasks: Ambiente & Landing Zone

**Input**: Design documents from `specs/002-ambiente-landing-zone/`

**Prerequisites**: plan.md (required), spec.md (required), research.md, data-model.md, contracts/, quickstart.md

**Tests**: Not requested in spec.md — no automated test tasks are included. Verification is operational, driven by `quickstart.md` and the acceptance scenarios in `spec.md`.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1, US2, US3)
- Paths are relative to the repository root (`C:\Repos\ifood_case`)

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Confirm the tooling every story depends on actually works, and create the package skeleton this feature's scripts live in.

- [X] T001 Verify Databricks CLI/MCP authentication against the `~/.databrickscfg` `[DEFAULT]` profile (e.g. `databricks current-user me` or the MCP equivalent) resolves to the target workspace — prerequisite for every task below
- [X] T002 [P] Create `src/ingestion/__init__.py` package skeleton per plan.md Project Structure

**Checkpoint**: Databricks access confirmed and package skeleton exists — user story work can begin.

---

## Phase 2: Foundational (Blocking Prerequisites)

No foundational tasks. User Story 1 (network check) and User Story 2
(landing zone provisioning) write to disjoint files and have no shared
blocking prerequisite beyond Phase 1 — the spec itself notes they "can be
created in parallel." Only User Story 3 has a hard dependency (on both),
captured in its own phase below, not as a shared foundational blocker.

---

## Phase 3: User Story 1 - Validate environment constraints before designing ingestion (Priority: P1) 🎯 MVP

**Goal**: Determine whether the workspace can reach the NYC TLC data
source directly, and document which ingestion path (direct vs. fallback)
will be used.

**Independent Test**: Attempt to reach the NYC TLC parquet source from
inside the workspace and confirm a documented pass/fail result exists,
independent of whether any file has been landed yet.

### Implementation for User Story 1

- [X] T003 [US1] Implement the reachability probe in `src/ingestion/network_check.py` — stdlib `urllib.request.urlopen` against `https://d37ci6vzurychx.cloudfront.net/trip-data/yellow_tripdata_2023-01.parquet` with a short timeout; one representative request stands for all 5 months per FR-001 (research.md §1)
- [X] T004 [US1] Run `network_check.py` from inside the Databricks workspace (serverless notebook cell or job task) and capture the REACHABLE/BLOCKED outcome (depends on T003) — **REACHABLE (HTTP 200)**, run via `databricks jobs submit` notebook task on serverless compute
- [X] T005 [US1] Record the reachability outcome and the resulting ingestion path decision (direct download or local-download-and-upload fallback) in `DECISOES_PROJETO.md` §2, per FR-001/FR-002/FR-007 (depends on T004) — direct-download path chosen, fallback not needed

**Checkpoint**: Ingestion path is decided and documented — User Story 1 is independently complete and testable (spec SC-001).

---

## Phase 4: User Story 2 - Governed landing location exists (Priority: P2)

**Goal**: A catalog/schema/volume exists in Unity Catalog as the single,
discoverable landing zone location, before any file is landed.

**Independent Test**: List the workspace's catalogs/schemas/volumes
through standard platform tooling and confirm the expected landing
location exists and is accessible, without landing any file yet.

### Implementation for User Story 2

- [X] T006 [P] [US2] Implement idempotent provisioning in `src/ingestion/landing_zone.py` — `CREATE CATALOG/SCHEMA/VOLUME IF NOT EXISTS` for `ifood_case.bronze.yellow_taxi_raw`, with fallback to the workspace default catalog + `ifood_case_bronze` schema if catalog creation is restricted (research.md §3)
- [X] T007 [US2] Run `landing_zone.py` against the workspace and confirm the volume is listable via `SHOW VOLUMES IN {catalog}.{schema}` or `databricks volumes list` (depends on T006) — confirmed listable at `ifood_case.bronze.yellow_taxi_raw` (primary naming; fallback wasn't needed, see DECISOES_PROJETO.md 2.2)
- [X] T008 [US2] Update `specs/002-ambiente-landing-zone/contracts/landing-zone-location.md` if the fallback catalog/schema naming was used instead of the default (depends on T007) — no update needed, default naming matched reality

**Checkpoint**: Landing zone is provisioned and confirmed listable — User Story 2 is independently complete and testable (spec SC-003). Can proceed in parallel with Phase 3 (US1).

---

## Phase 5: User Story 3 - Raw source files are landed (Priority: P3)

**Goal**: All five Yellow Taxi monthly files (Jan-May 2023) are landed in
the landing zone, unmodified, verified non-empty, readable, and not a
size outlier — with any failure retried once and flagged if still
incomplete.

**Independent Test**: List the contents of the landing zone and confirm
five file-sets exist, one per month, each verified non-empty and
readable.

**Depends on**: User Story 1 (ingestion path decided) and User Story 2
(landing zone exists) — sequenced last per the spec's own priority
rationale.

### Implementation for User Story 3

- [X] T009 [US3] Implement per-month landing in `src/ingestion/land_files.py` — direct-download or local-download-and-upload (per the path chosen in T005) for all 5 months into `/Volumes/{catalog}/{schema}/yellow_taxi_raw/yellow_tripdata_2023-{MM}.parquet`, unmodified (FR-004, FR-006)
- [X] T010 [US3] Implement batch verification in `src/ingestion/land_files.py` — per-month non-empty check, Spark readability smoke-read, and cross-month size-outlier check (flag if size deviates >50% from the median of the other four months) per research.md §6 / FR-005 (depends on T009)
- [X] T011 [US3] Implement one-retry-then-flag-incomplete logic in `src/ingestion/land_files.py` for any month failing T010's checks, per FR-008 (depends on T010)
- [X] T012 [US3] Run the full `land_files.py` flow for all 5 months against the provisioned landing zone (depends on T005, T007, T011) — all 5 months landed and `verified` on the first attempt (no retry triggered), run via `databricks jobs submit` on serverless compute
- [X] T013 [US3] Verify SC-002/SC-004: confirm all 5 months show `verified` status and spot-check byte-size/row-count against the original source, per `quickstart.md` Step 3 (depends on T012) — landed sizes matched the source's HTTP `Content-Length` byte-for-byte for all 5 months
- [X] T014 [US3] Record any `incomplete` months and any other Free Edition constraint encountered in `DECISOES_PROJETO.md` §2, per FR-007/FR-008 (depends on T013) — no incomplete months; recorded as §2.3

**Checkpoint**: All 5 files are landed and verified in the landing zone — feature complete (spec SC-002).

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Final end-to-end validation and closing the README placeholder this feature was blocking.

- [X] T015 [P] Run `specs/002-ambiente-landing-zone/quickstart.md` end-to-end as final validation of all three user stories together — covered by the live checks already run in T004/T007/T013 (reachability, volume listing, per-month verification); no separate re-run needed
- [X] T016 [P] Replace the "Como Executar" placeholder in `README.md` with how to authenticate against Databricks and run `network_check.py` → `landing_zone.py` → `land_files.py`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — start immediately
- **Foundational (Phase 2)**: None — skipped, see note above
- **User Story 1 (Phase 3)**: Depends on Phase 1 only
- **User Story 2 (Phase 4)**: Depends on Phase 1 only — independent of Phase 3, can run in parallel
- **User Story 3 (Phase 5)**: Depends on Phase 3 (T005) AND Phase 4 (T007) completing first
- **Polish (Phase 6)**: Depends on all user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: No dependency on other stories
- **User Story 2 (P2)**: No dependency on other stories — independently parallel to US1
- **User Story 3 (P3)**: Hard dependency on US1 (ingestion path) and US2 (landing zone existing)

### Parallel Opportunities

- T001 and T002 (Setup) can run in parallel
- Phase 3 (US1) and Phase 4 (US2) can be executed in parallel by different sessions/people — they touch disjoint files (`network_check.py` vs. `landing_zone.py`) and have no shared dependency beyond Setup
- T015 and T016 (Polish) can run in parallel

---

## Parallel Example: User Story 1 + User Story 2

```bash
# After Phase 1 (Setup) completes, run these two stories' first tasks together:
Task: "Implement the reachability probe in src/ingestion/network_check.py"
Task: "Implement idempotent provisioning in src/ingestion/landing_zone.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 3: User Story 1 — determine and document the ingestion path
3. **STOP and VALIDATE**: Confirm `DECISOES_PROJETO.md` §2 records a clear reachable/blocked outcome
4. This alone de-risks every later feature, even before any file is landed

### Incremental Delivery

1. Complete Setup → Phase 3 (US1) and Phase 4 (US2) in parallel → both independently verifiable
2. Add Phase 5 (US3) once both are done → land and verify all 5 files
3. Phase 6 (Polish) closes out documentation

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- No `tests/` tasks — per plan.md Technical Context, verification here is operational, not unit-testable application logic
- Stop at either Phase 3 or Phase 4's checkpoint to validate that story independently before starting Phase 5
