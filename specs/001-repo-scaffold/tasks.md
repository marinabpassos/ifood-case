---

description: "Task list for Repo Scaffold"
---

# Tasks: Repo Scaffold

**Input**: Design documents from `specs/001-repo-scaffold/`

**Prerequisites**: plan.md (required), spec.md (required), research.md, quickstart.md

**Tests**: Not requested in spec.md — no automated test tasks are included. Verification is structural, driven by `quickstart.md`.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1, US2, US3)
- Paths are relative to the repository root (`C:\Repos\ifood_case`)

## Phase 1: Setup (Shared Infrastructure)

No setup tasks. Environment prerequisites this feature depends on
(`.gitignore`, `.specify/`, `specs/001-repo-scaffold/`) already exist from
the constitution and specify phases — nothing shared needs initializing
before user story work can begin.

---

## Phase 2: Foundational (Blocking Prerequisites)

No foundational tasks. The three user stories write to disjoint
files/directories (US1: four new folders, US2: `README.md`, US3:
`requirements.txt`), so there is no shared blocking prerequisite. Priority
order (P1 → P2 → P3) below is a sequencing preference — US2 reads more
accurately once US1's folders exist — not a hard technical dependency.

---

## Phase 3: User Story 1 - Standard directory layout ready for pipeline artifacts (Priority: P1) 🎯 MVP

**Goal**: Create the four structural directories (`src/`, `analysis/`,
`contracts/`, `data/`) so the repo's intended layout exists and survives a
fresh clone.

**Independent Test**: Run `Get-ChildItem -Directory` at the repo root and
confirm `src`, `analysis`, `contracts`, `data` are present; confirm `git
status` shows them tracked.

### Implementation for User Story 1

- [X] T001 [P] [US1] Create `src/` with a `.gitkeep` placeholder at `src/.gitkeep`
- [X] T002 [P] [US1] Create `analysis/` with a `.gitkeep` placeholder at `analysis/.gitkeep`
- [X] T003 [P] [US1] Create `contracts/` with a `.gitkeep` placeholder at `contracts/.gitkeep`
- [X] T004 [P] [US1] Create `data/` with a `.gitkeep` placeholder at `data/.gitkeep`, and confirm the existing `.gitignore` `data/*` / `!data/.gitkeep` rule keeps this placeholder tracked while ignoring future landed files

**Checkpoint**: At this point, the full directory layout exists and is
independently verifiable (spec `SC-002`).

---

## Phase 4: User Story 2 - Project README communicates the solution (Priority: P2)

**Goal**: A root `README.md` that lets a first-time reader understand the
project, its layout, and which folders are case-brief minimum vs. this
project's own additions — within one minute of reading (spec `SC-001`,
`SC-003`).

**Independent Test**: Read `README.md` alone (per `quickstart.md` step 2)
and answer: what is this project, where does each kind of deliverable go,
and which folders are additions with a stated reason.

### Implementation for User Story 2

- [X] T005 [US2] Write `README.md` at repo root with sections: Objetivo,
      Arquitetura (short summary of the bronze/silver + contracts approach
      from `DECISOES_PROJETO.md`), Estrutura do Repositório (table: folder →
      purpose → case-brief-minimum or project-addition, with a one-line
      justification for `contracts/` and `data/` per `FR-007`), Stack
      Tecnológica, Como Executar (explicit placeholder, to be completed by
      the ingestion feature), Perguntas Analíticas Respondidas (placeholder
      linking to `analysis/`). Depends on T001-T004 so the folder table
      reflects the actual layout.
- [X] T006 [US2] Validate `README.md` against the three cold-read questions
      in `quickstart.md` step 2; revise the file until all three are
      answerable without other context. Depends on T005.
      Result: all three answerable — Objetivo answers "what is this
      project", the Estrutura table answers "where does each deliverable
      go", and its Origem column marks `contracts/`/`data/` as additions
      with a stated reason each.

**Checkpoint**: At this point, User Stories 1 AND 2 both work
independently — the layout exists and is documented.

---

## Phase 5: User Story 3 - Dependency manifest ready for incremental use (Priority: P3)

**Goal**: A root `requirements.txt` that installs the fixed stack cleanly
in a fresh environment.

**Independent Test**: Install from `requirements.txt` in a clean
environment (per `quickstart.md` step 3) and confirm `pyspark`,
`delta-spark`, and `pyyaml` install without error.

### Implementation for User Story 3

- [X] T007 [P] [US3] Verify `requirements.txt` at repo root lists `pyspark`,
      `delta-spark`, and `pyyaml` as active dependencies, matching the
      fixed stack in the Constitution's Technology Stack section and
      `DECISOES_PROJETO.md` §3/§10; per `research.md`, no changes are
      expected — correct only if it has drifted. Not dependent on US1/US2.
      Result: matches exactly, no drift, no changes made.
- [X] T008 [US3] Run the install check from `quickstart.md` step 3 (create
      a temporary venv, `pip install -r requirements.txt`, confirm success,
      remove the temporary venv). Depends on T007.
      Result: `pyspark-3.5.9`, `delta-spark-3.3.2`, `pyyaml-6.0.3` (+
      transitive deps) installed successfully in a clean venv; temp venv
      removed after verification.

**Checkpoint**: All three user stories are now independently functional.

---

## Phase 6: Polish & Cross-Cutting Concerns

- [X] T009 [P] Run the full `quickstart.md` validation (steps 1-4) end to
      end and confirm `SC-001` through `SC-004` all pass. Depends on
      T001-T008.
      Result: SC-001/SC-003 pass (T006), SC-002 passes (T001-T004 tree
      matches), SC-004 passes (T008 clean install), step 4 confirmed only
      `.gitkeep` placeholders exist in `src/`, `analysis/`, `contracts/`.
- [X] T010 Re-check `DECISOES_PROJETO.md` §11's repository structure
      snippet against the actual final layout (`src/`, `analysis/`,
      `contracts/`, `data/`, `specs/`, `.specify/`, `README.md`,
      `requirements.txt`) and correct it if it has drifted. Depends on T005.
      Result: `data/` was missing from the §11 snippet — added.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: None — no tasks.
- **Foundational (Phase 2)**: None — no tasks.
- **User Story 1 (Phase 3)**: No dependencies — can start immediately.
- **User Story 2 (Phase 4)**: T005 depends on T001-T004 (accurate folder
  table); T006 depends on T005.
- **User Story 3 (Phase 5)**: T007 has no dependency and can run in
  parallel with Phases 3-4; T008 depends on T007.
- **Polish (Phase 6)**: T009 depends on all of T001-T008; T010 depends on T005.

### User Story Dependencies

- **User Story 1 (P1)**: No dependencies on other stories.
- **User Story 2 (P2)**: Soft dependency on US1 (documents US1's output
  accurately) but touches a disjoint file — not a hard blocker.
- **User Story 3 (P3)**: No dependency on US1 or US2.

### Parallel Opportunities

- T001, T002, T003, T004 (all of US1) can run in parallel — four different
  directories, no shared file.
- T007 (US3) can run in parallel with all of US1 and the start of US2.

---

## Parallel Example: User Story 1

```bash
# Launch all four directory-creation tasks together:
Task: "Create src/ with .gitkeep placeholder at src/.gitkeep"
Task: "Create analysis/ with .gitkeep placeholder at analysis/.gitkeep"
Task: "Create contracts/ with .gitkeep placeholder at contracts/.gitkeep"
Task: "Create data/ with .gitkeep placeholder at data/.gitkeep"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 3 (US1): the four directories exist and are tracked.
2. **STOP and VALIDATE**: confirm `SC-002` via `Get-ChildItem` — this alone
   is a demonstrable, independently testable increment.

### Incremental Delivery

1. Phase 3 (US1) → directories exist → validate independently.
2. Phase 4 (US2) → README documents the layout → validate independently.
3. Phase 5 (US3) → dependencies confirmed installable → validate independently.
4. Phase 6 (Polish) → full quickstart pass, decisions-doc consistency check.

---

## Notes

- No `[P]` tasks conflict on the same file.
- `[Story]` labels trace every Phase 3-5 task back to its spec.md user story.
- This feature intentionally has no Setup/Foundational tasks — see the
  notes under Phase 1 and Phase 2 above for why.
- Commit after each checkpoint (US1, US2, US3, Polish) rather than one
  large commit, so the independent-test claim for each story is verifiable
  in the commit history.
