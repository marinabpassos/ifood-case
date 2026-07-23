# Implementation Plan: Contrato de Dados da Silver

**Branch**: `005-silver-data-contract` | **Date**: 2026-07-23 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `specs/005-silver-data-contract/spec.md`

## Summary

Write the declarative, versioned data contract for the silver layer —
`contracts/nyc_taxi_silver.yaml` — before any silver table-writing code
exists (Constitution Principle II). The contract declares: table
identity, a 6-column schema (5 required business columns +
`_silver_processed_at`, per the 2026-07-23 clarification), grain (no
formal uniqueness constraint), an explicit drop policy with independent
per-rule counting for all 5 constitution-named data-quality risks, an
illustrative SLA, and a `v1` version with a semver breaking-change
policy. A small local validator confirms the YAML is structurally
complete. No table is read, written, or altered — this feature produces
a document only.

## Technical Context

**Language/Version**: Python 3.11+ (validator script only; the contract
itself is a YAML document, not code)

**Primary Dependencies**: `PyYAML` (already fixed in `requirements.txt`
under "Contratos de dados (parsing de YAML)" — no new dependency)

**Storage**: N/A — no table is read or written. The contract lives as a
file in the repository (`contracts/nyc_taxi_silver.yaml`), the first
feature in this project that touches no Databricks table at all.

**Testing**: The validator script (`src/contracts/validate_silver_contract.py`)
is itself the verification mechanism — it loads the YAML and asserts
structural completeness against `contracts/silver-contract-structure.md`
(this feature's Phase 1 output). Runs entirely locally; no Databricks
access needed.

**Target Platform**: Local (author's machine / CI). This is the first
feature in the project that needs no Databricks workspace access at all
— a contract is a repository artifact, not a platform one.

**Project Type**: Single project — adds the repository-root
`contracts/nyc_taxi_silver.yaml` (already an empty directory with
`.gitkeep`, per the case brief's fixed repo layout) and a new
`src/contracts/` package holding the validator.

**Performance Goals**: N/A — one YAML file (~6 columns, 5 rules), one
validation script running against it.

**Constraints**: None new. No Free Edition constraint applies (no
platform interaction).

**Scale/Scope**: 1 contract file, 1 validator script, 1 structure-fixing
companion doc (`specs/005-silver-data-contract/contracts/silver-contract-structure.md`).

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Applies? | Assessment |
|---|---|---|
| I. Data Quality Is a Gate | No (indirectly satisfied) | This feature doesn't profile or filter any data itself — it consumes feature 003/004's already-quantified findings and declares a policy. The rules it declares (drop, independently counted) are what feature 006 will enforce and report by volume, satisfying Principle I's actual mandate at that point. |
| II. Data Contracts First | **Yes — this feature exists to satisfy it** | Produces `contracts/nyc_taxi_silver.yaml` before any silver table-writing code (feature 006) is implemented. Declares table identity, explicit column schema, grain, quality rules, SLA, version, and breaking-change policy — every field Principle II mandates. |
| III. Observability Is Part of the Deliverable | No | No pipeline execution happens in this feature — nothing to log. The independent-per-rule-counting decision (spec clarification) sets up feature 006/007's future reporting shape, but doesn't itself produce a run to observe. |
| IV. Fixed Stack, Justified Deviations | **Yes** | PyYAML only, already a declared dependency — no new tech, no deviation. |
| V. Spec-Driven Development Workflow | **Yes** | Specify → Clarify → Plan (this document) → Tasks → Implement, human checkpoint at each — satisfied by construction. |
| VI. Lean Instructions, Simple Architecture | **Yes** | One contract file, one small validator — no gold layer, no speculative abstraction. The validator only checks structural completeness (not a full schema-enforcement engine); the real enforcement against live data is feature 006's job, not duplicated here. |

**Result**: PASS. No violations, no workarounds to document. Re-checked
after Phase 1 below.

## Project Structure

### Documentation (this feature)

```text
specs/005-silver-data-contract/
├── plan.md                              # This file (/speckit-plan command output)
├── research.md                          # Phase 0 output (/speckit-plan command)
├── data-model.md                        # Phase 1 output (/speckit-plan command)
├── quickstart.md                        # Phase 1 output (/speckit-plan command)
├── contracts/
│   └── silver-contract-structure.md     # Phase 1 output — the required top-level structure contracts/nyc_taxi_silver.yaml must follow, consumed by this feature's own validator and by feature 006
├── checklists/
│   └── requirements.md                  # Spec quality checklist (/speckit-specify command)
└── tasks.md                             # Phase 2 output (/speckit-tasks command - NOT created by /speckit-plan)
```

### Source Code (repository root)

```text
ifood_case/
├── contracts/
│   └── nyc_taxi_silver.yaml     # THE deliverable: the actual Principle-II data contract (repo-root location, fixed by case brief layout)
├── src/
│   ├── ingestion/                # Existing (feature 002), untouched
│   ├── profiling/                # Existing (feature 003), untouched
│   ├── bronze/                   # Existing (feature 004), untouched
│   └── contracts/
│       ├── __init__.py
│       └── validate_silver_contract.py   # Loads contracts/nyc_taxi_silver.yaml, asserts structural completeness against silver-contract-structure.md
```

**Structure Decision**: Single-project layout, consistent with features
001-004. `contracts/nyc_taxi_silver.yaml` lives at the repository root
(the case brief's own fixed layout names `contracts/` as the top-level
home for data contracts — not under `specs/`). A new `src/contracts/`
package holds the one validator script — no `tests/` directory, since
the validator script itself is the executable verification (matching
features 002-004's operational-verification pattern, just runnable
locally here instead of via a Databricks job).

## Complexity Tracking

*No entries — the Constitution Check above found no violations or
workarounds requiring justification.*

## Post-Design Constitution Re-Check

Re-evaluated after Phase 1 (`data-model.md`,
`contracts/silver-contract-structure.md`, `quickstart.md`): unchanged
from the pre-Phase-0 assessment above. `data-model.md` confirms the
contract's fields map 1:1 to Principle II's mandated list (identity,
columns, grain, quality rules, SLA, version) with nothing extraneous
added, and the validator's scope stays limited to structural completeness
rather than reimplementing feature 006's future live-data schema
assertion. **Result: PASS, no new violations.**
