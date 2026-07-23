---

description: "Task list for Contrato de Dados da Silver"
---

# Tasks: Contrato de Dados da Silver

**Input**: Design documents from `specs/005-silver-data-contract/`

**Prerequisites**: plan.md (required), spec.md (required), research.md, data-model.md, contracts/, quickstart.md

**Tests**: Not requested in spec.md — no automated test tasks are included beyond the structural validator itself, which is this feature's verification mechanism (plan.md Technical Context).

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1, US2, US3)
- Paths are relative to the repository root (`C:\Repos\ifood_case`)

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Create the package skeleton the validator will live in. Unlike every prior feature, no Databricks access check is needed here (plan.md Technical Context — this feature touches no platform resource).

- [ ] T001 [P] Create `src/contracts/__init__.py` package skeleton per plan.md Project Structure

**Checkpoint**: Package skeleton exists — user story work can begin.

---

## Phase 2: Foundational (Blocking Prerequisites)

No foundational phase. User Story 1 is the natural starting point (the
`columns` section other stories' content refers to), but nothing here
blocks in the "shared infrastructure" sense feature 002 needed — see
User Story Dependencies below for the real (content-level) ordering.

---

## Phase 3: User Story 1 - A reader knows exactly what the silver table looks like before it exists (Priority: P1) 🎯 MVP

**Goal**: Declare the contract's identity and full 6-column schema.

**Independent Test**: Read `contracts/nyc_taxi_silver.yaml` alone and
answer "what are the columns, their types, and can each be null?"

### Implementation for User Story 1

- [ ] T002 [US1] Create `contracts/nyc_taxi_silver.yaml` with the `contract` block (`name: nyc_taxi_silver`, `version: v1`) and `table` block (`catalog: ifood_case`, `schema: silver`, `name: yellow_taxi_trips`, `owner`) per `contracts/silver-contract-structure.md` §1-2
- [ ] T003 [US1] Add the `columns` list (exactly 6 entries) to `contracts/nyc_taxi_silver.yaml`: `VendorID`, `passenger_count`, `total_amount`, `tpep_pickup_datetime`, `tpep_dropoff_datetime`, `_silver_processed_at` — each with `name`/`type`/`nullable`/`description`, nullability declared as the post-cleaning invariant (research.md §3, e.g. `passenger_count`/`total_amount` `nullable: false`) (FR-002, data-model.md) (depends on T002)
- [ ] T004 [US1] Manually verify quickstart.md Step 1: reading the `columns` list alone answers type/nullability/description for all 6 entries, with zero bronze passthrough columns (e.g. `trip_distance`) and zero bronze metadata columns (`_source_file`, `_ingested_at`) present (depends on T003)

**Checkpoint**: Contract identity and full column schema declared — User Story 1 is independently complete and testable (spec SC-001).

---

## Phase 4: User Story 2 - Feature 006 has an unambiguous data-quality specification to implement (Priority: P2)

**Goal**: Declare an explicit, reasoned policy for all 5 constitution-named data-quality risks.

**Independent Test**: For each of the 5 risks, confirm the contract
states a policy and rationale, independent of feature 006's
implementation.

**Depends on**: User Story 1 (Phase 3, T003) — rules reference the
column names just declared.

### Implementation for User Story 2

- [ ] T005 [US2] Add the `quality_rules` list (exactly 5 entries) to `contracts/nyc_taxi_silver.yaml`: `total_amount_negative_or_zero`, `passenger_count_null_or_zero`, `dropoff_before_pickup`, `out_of_range_dates` (all `policy: drop`, `counting: independent`), and `duplicates` (`policy: resolved_upstream`) — each with `id`/`policy`/`rationale` (`counting` on the 4 drop rules only) per FR-004, research.md §5, `contracts/silver-contract-structure.md` §5 (depends on T003)
- [ ] T006 [US2] Add the `total_dropped_metric_note` sibling key to `contracts/nyc_taxi_silver.yaml`, stating that "total rows dropped" (logical OR across the 4 drop rules, no double-counting) is a separate metric from the 4 independent per-rule counts (research.md §5, 2026-07-23 clarification) (depends on T005)
- [ ] T007 [US2] Manually verify quickstart.md Step 2: all 5 rules have an explicit policy, the 4 drop rules are marked `independent`, and the total-dropped note is present and distinguishable from the per-rule counts (depends on T006)

**Checkpoint**: All 5 data-quality risks have an explicit, reasoned policy — User Story 2 is independently complete and testable (spec SC-002).

---

## Phase 5: User Story 3 - The contract signals operational maturity even for a one-time load (Priority: P3)

**Goal**: Declare grain, SLA/update frequency, and version/breaking-change policy.

**Independent Test**: Read the grain, SLA, and version sections in
isolation and confirm each is concrete, not vague.

**Depends on**: User Story 1 (Phase 3, T003) — the grain's uniqueness
note references the finalized 6-column set.

### Implementation for User Story 3

- [ ] T008 [US3] Add the `grain` block to `contracts/nyc_taxi_silver.yaml`: `statement` ("one row = one trip event") and `uniqueness_note` (explicitly no formal uniqueness constraint on the 6-column schema alone; bronze's full-row dedup over 19 columns is the only inherited guarantee) per FR-003, spec Edge Cases, `contracts/silver-contract-structure.md` §3 (depends on T003)
- [ ] T009 [US3] Add the `sla` block to `contracts/nyc_taxi_silver.yaml`: illustrative `frequency` (e.g. `monthly`), `latency_target`, and a `note` stating the real load for this case is one-time (Jan-May 2023) per FR-005, spec Assumptions
- [ ] T010 [US3] [P] Add the `versioning` block to `contracts/nyc_taxi_silver.yaml`: `current_version: v1` and `breaking_change_policy` with explicit `major`/`minor`/`patch` triggers (standard semver default, spec Assumptions) per FR-006
- [ ] T011 [US3] Manually verify quickstart.md Step 4: the `versioning` block resolves a hypothetical change (e.g. "remove `VendorID`" = major, "add an optional column" = minor) without needing to ask the contract's author (depends on T010)

**Checkpoint**: Grain, SLA, and versioning declared — User Story 3 is independently complete and testable (spec SC-003).

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Build the structural validator over the now-complete contract and run final validation.

- [ ] T012 Implement `src/contracts/validate_silver_contract.py`: load `contracts/nyc_taxi_silver.yaml`, assert all 7 top-level keys, the 6-entry `columns` list (with `name`/`type`/`nullable`/`description` each), the 5-entry `quality_rules` list (with `id`/`policy`/`rationale`, `counting` on drop rules), non-empty `sla`, and a `versioning.current_version` matching a `vN` pattern with a `breaking_change_policy` containing `major`/`minor`/`patch` — per research.md §2, `contracts/silver-contract-structure.md`, data-model.md "Contract Validation Result" (depends on T001, T004, T007, T011 — the contract must be fully written first)
- [ ] T013 Run `python src/contracts/validate_silver_contract.py` (quickstart.md Step 3) and confirm `"structurally_valid": true` with an empty `missing_or_invalid` list (depends on T012)
- [ ] T014 [P] Run `specs/005-silver-data-contract/quickstart.md` end-to-end (all 4 steps) as final validation of all three user stories together (depends on T013)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — start immediately
- **Foundational (Phase 2)**: None as a separate phase — see note above
- **User Story 1 (Phase 3)**: Depends on Phase 1 (T001) only
- **User Story 2 (Phase 4)**: Depends on Phase 3 (T003) — rules reference declared columns
- **User Story 3 (Phase 5)**: Depends on Phase 3 (T003) — grain references the finalized column set; independent of Phase 4 (US2)
- **Polish (Phase 6)**: Depends on Phase 3 (T004), Phase 4 (T007), and Phase 5 (T011) — the validator checks the whole, now-complete contract

### User Story Dependencies

- **User Story 1 (P1)**: No dependency on other stories — first content written
- **User Story 2 (P2)**: Depends on User Story 1's `columns` existing in the same file (content-level, not a separate blocking phase)
- **User Story 3 (P3)**: Depends on User Story 1's `columns` existing (for the grain's uniqueness note) — does **not** depend on User Story 2; Phases 4 and 5 can proceed in parallel once Phase 3 completes

### Parallel Opportunities

- Phase 4 (US2, `quality_rules`) and Phase 5 (US3, `grain`/`sla`/`versioning`) can proceed in parallel once Phase 3 (US1) completes — both append different top-level keys to the same file but don't depend on each other's content
- T010 (`versioning` block) can be written in parallel with T008-T009 within Phase 5 — independent top-level key
- T014 (Polish, quickstart end-to-end) has no parallel partner left by that point — it's the final check

---

## Parallel Example: User Story 2 + User Story 3

```bash
# After Phase 3 (US1) completes, these two stories' work is independent:
Task: "Add the quality_rules list to contracts/nyc_taxi_silver.yaml"
Task: "Add the grain block to contracts/nyc_taxi_silver.yaml"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 3: User Story 1 — contract identity and full column schema declared
3. **STOP and VALIDATE**: Confirm the 6-column schema is complete and unambiguous on its own
4. This alone tells any reader exactly what silver's shape will be, before any quality rule or SLA detail is added

### Incremental Delivery

1. Complete Setup → Phase 3 (US1) → schema declared
2. Add Phase 4 (US2) and Phase 5 (US3) in parallel → quality rules and operational-maturity sections both complete
3. Phase 6 (Polish) builds the validator over the finished contract and runs quickstart end-to-end

---

## Notes

- [P] tasks = different files (or independent top-level keys within the
  same file, safe to edit without conflict), no dependencies
- [Story] label maps task to specific user story for traceability
- No `tests/` tasks — the validator script (T012-T013) is this feature's
  verification mechanism, per plan.md Technical Context
- Unlike every prior feature, no task here needs Databricks CLI/MCP
  access — everything is local file authoring and a local Python script
- Stop at Phase 3's checkpoint to validate the schema declaration
  independently before proceeding into Phases 4-5
