# Implementation Plan: Repo Scaffold

**Branch**: `001-repo-scaffold` | **Date**: 2026-07-22 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `specs/001-repo-scaffold/spec.md`

## Summary

Create the repository's structural skeleton for the iFood taxi-data case:
the two directories required by the case brief (`src/`, `analysis/`), the
two directories this project's own decisions add (`contracts/`, `data/`),
and the two root files the brief requires (`README.md`,
`requirements.txt`). No pipeline code, contracts content, or analysis is
written by this feature — only structure, placeholders, and documentation
that makes the layout self-explanatory (per spec `FR-001`–`FR-007`).

## Technical Context

**Language/Version**: Python 3.11+ (declared for the eventual PySpark
pipeline; this feature itself writes no code)

**Primary Dependencies**: pyspark, delta-spark, pyyaml — already fixed in
`requirements.txt` (Constitution §Technology Stack); this feature only
confirms the manifest is present and installable, it does not add new
dependencies

**Storage**: Local filesystem only (git-tracked directories); no database,
no Delta tables — those belong to later ingestion/contracts features

**Testing**: N/A — no executable code is introduced. Verification is
structural (directory/file existence, README content, `pip install`
succeeds) and is covered by `quickstart.md`, not an automated test suite

**Target Platform**: Local development machine (any OS); the eventual
pipeline targets Databricks Free Edition, but that is out of scope here

**Project Type**: Single project — a data engineering case repository, not
a client/server or multi-package application

**Performance Goals**: N/A (no runtime behavior in this feature)

**Constraints**: Must match the case brief's minimum structure exactly;
every directory beyond that minimum (`contracts/`, `data/`) must carry a
documented one-line justification in `README.md` (Constitution Principle
IV — Fixed Stack, Justified Deviations)

**Scale/Scope**: One repository, 6 top-level directories, 2 root files —
no per-feature subdirectories are created yet (those arrive with the
features that populate them)

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Applies? | Assessment |
|---|---|---|
| I. Data Quality Is a Gate | No | No data is read or written by this feature |
| II. Data Contracts First | Partial | `contracts/` directory is created as a placeholder only; no contract content is written here — writing an actual contract before table code remains a gate for the future ingestion/contracts feature |
| III. Observability Is Part of the Deliverable | No | No pipeline execution exists yet to instrument |
| IV. Fixed Stack, Justified Deviations | **Yes** | `contracts/` and `data/` go beyond the case brief's minimum (`src/`, `analysis/`, `README.md`, `requirements.txt`); FR-002/FR-007/SC-003 require each to be justified in `README.md` — this is the binding gate for this feature |
| V. Spec-Driven Development Workflow | **Yes** | This feature is itself being delivered via Specify → Plan → Tasks → Implement with human checkpoints — satisfied by construction |
| VI. Lean Instructions, Simple Architecture | **Yes** | No `tests/`, no per-layer subfolders (e.g. no `bronze/`/`silver/` folders), no speculative structure beyond what the case brief + prior decisions already call for |

**Result**: PASS. No unjustified violations. The one binding gate
(Principle IV) is satisfied by design — `FR-007` and `SC-003` require the
README to state why `contracts/` and `data/` exist — and is re-checked
after Phase 1 below.

## Project Structure

### Documentation (this feature)

```text
specs/001-repo-scaffold/
├── plan.md              # This file (/speckit-plan command output)
├── research.md          # Phase 0 output (/speckit-plan command)
├── data-model.md        # Phase 1 output (/speckit-plan command) — N/A, no data entities
├── quickstart.md        # Phase 1 output (/speckit-plan command)
├── checklists/
│   └── requirements.md  # Spec quality checklist (/speckit-specify command)
└── tasks.md              # Phase 2 output (/speckit-tasks command - NOT created by /speckit-plan)
```

No `contracts/` subdirectory is generated under `specs/001-repo-scaffold/`:
this feature exposes no external interface (API, CLI, schema) — it only
creates repository directories and docs — so the "interface contracts"
output is skipped per the plan workflow's own guidance. (Note: this is
distinct from the repository-root `contracts/` directory, which is a
placeholder for future *data* contracts, created by FR-002.)

### Source Code (repository root)

```text
ifood_case/
├── src/                 # Pipeline code — required by case brief, empty until ingestion feature
├── analysis/            # SQL/PySpark answers to the two analytical questions — required by case brief
├── contracts/           # Versioned data contracts (e.g. nyc_taxi_silver.yaml) — project addition, empty until contracts feature
├── data/                # Local landing zone for plan-B ingestion — project addition, contents gitignored
├── specs/               # Spec Kit feature specs (this SDD flow) — already exists
├── .specify/             # Spec Kit constitution, templates, config — already exists
├── README.md             # Project overview, architecture summary, repo layout, execution placeholder
└── requirements.txt      # Fixed technology stack (pyspark, delta-spark, pyyaml) — already exists
```

**Structure Decision**: Single-project layout. `src/`, `analysis/`,
`README.md`, and `requirements.txt` match the case brief's required
structure exactly. `contracts/` and `data/` are the project's own
documented additions (Constitution Principle IV) and their purpose is
stated in `README.md` per FR-005/FR-007. No `tests/` directory is created
here — there is no code yet to test, and adding one now would be
speculative structure disallowed by Constitution Principle VI; it will be
introduced by whichever future feature first adds testable pipeline code.

## Complexity Tracking

*No entries — the Constitution Check above found no unjustified
violations. `contracts/` and `data/` are justified additions (Principle IV)
covered directly by this feature's own requirements (FR-002, FR-007), not
complexity that needs a separate exception.*

## Post-Design Constitution Re-Check

Re-evaluated after Phase 1 (`data-model.md`, `quickstart.md`): unchanged
from the pre-Phase-0 assessment above. `data-model.md` confirms no domain
entities are introduced (Principle I/II remain not-yet-applicable), and
`quickstart.md`'s validation steps directly test the Principle IV
requirement (README must justify `contracts/` and `data/`). **Result:
PASS, no new violations.**
