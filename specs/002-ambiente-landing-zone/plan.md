# Implementation Plan: Ambiente & Landing Zone

**Branch**: `002-ambiente-landing-zone` | **Date**: 2026-07-22 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `specs/002-ambiente-landing-zone/spec.md`

## Summary

Validate whether the Databricks Free Edition workspace can reach the NYC
TLC data source directly, provision a governed Unity Catalog landing zone
(catalog/schema/volume), and land the five Yellow Taxi monthly files
(Jan-May 2023) into it unmodified — using whichever ingestion path (direct
download or local-download-and-upload) the reachability test dictates, with
every constraint and decision documented per Constitution Principle IV. Any
month failing the non-empty/readable/size-outlier check (FR-005) is
retried once automatically before being flagged incomplete (FR-008), per
the 2026-07-22 spec clarifications.

## Technical Context

**Language/Version**: Python 3.11+ (matches feature 001's declared
manifest; used for the reachability check, provisioning, and file-landing
scripts)

**Primary Dependencies**: stdlib `urllib` (network check, research.md §1),
Databricks CLI/SDK (catalog/schema/volume provisioning and file upload,
research.md §2-3), PySpark (readability smoke-read only, research.md §4) —
no new entry needed in `requirements.txt` beyond what feature 001 already
fixed (`pyspark`, `delta-spark`, `pyyaml`)

**Storage**: Unity Catalog Volume (target: `/Volumes/ifood_case/bronze/yellow_taxi_raw/`,
research.md §3) as the landing zone; local `data/` directory (feature 001
scaffold) as git-ignored staging for the fallback ingestion path only

**Testing**: N/A — no application logic is introduced. Verification is
operational: the three scripted checks in `quickstart.md` (reachability,
volume listing, per-file size + readability + cross-month size-outlier
check with one retry), not an automated test suite

**Target Platform**: Databricks Free Edition workspace (serverless compute
only); local development machine only if the fallback ingestion path
(research.md §2) is required

**Project Type**: Single project — this feature adds a small ingestion
script/module under `src/`, not a new component

**Performance Goals**: N/A — one-time batch landing of 5 files, not a
recurring or latency-sensitive workload

**Constraints**: Databricks Free Edition's known limits (serverless-only
compute, possibly-restricted outbound network, single 2X-Small SQL
Warehouse) apply directly to this feature and are exactly what FR-001/FR-007
require to be validated and documented, not assumed

**Scale/Scope**: 5 monthly parquet files (January-May 2023), one Landing
Zone (catalog/schema/volume triple) — no per-row content is inspected here

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Applies? | Assessment |
|---|---|---|
| I. Data Quality Is a Gate | No | This feature only lands raw bytes; no quality rule is applied or checked here — that begins with feature 003 (Data Profiling), per the spec's own scope boundary note |
| II. Data Contracts First | No | No silver table is written by this feature; `contracts/landing-zone-location.md` is an operational interface contract (path/naming), not the Principle II data contract, which arrives with feature 004 |
| III. Observability Is Part of the Deliverable | Partial | FR-001/FR-005/FR-007 require the reachability outcome, ingestion path used, and any Free Edition constraint to be documented (`DECISOES_PROJETO.md` §2) — a lightweight, one-time record. The full `_pipeline_run_log` table and threshold alerting is feature 006's scope, not re-implemented here |
| IV. Fixed Stack, Justified Deviations | **Yes** | This is the binding gate. The network test (FR-001) and, if triggered, the fallback ingestion path (FR-002) are exactly the "possible Free Edition deviation" the constitution calls out by name — its use MUST be documented, not silently adopted |
| V. Spec-Driven Development Workflow | **Yes** | Delivered via Specify → Plan → Tasks → Implement with human checkpoints — satisfied by construction |
| VI. Lean Instructions, Simple Architecture | **Yes** | No new layer beyond landing/bronze is introduced; provisioning uses idempotent DDL/CLI calls rather than a bespoke framework; environment findings extend the existing `DECISOES_PROJETO.md` §2 rather than a new doc |

**Result**: PASS. No unjustified violations. Principle IV is the binding
gate for this feature and is satisfied by design — FR-001/FR-002/FR-007
require exactly the validation and documentation the constitution demands.
Re-checked after Phase 1 below.

## Project Structure

### Documentation (this feature)

```text
specs/002-ambiente-landing-zone/
├── plan.md                          # This file (/speckit-plan command output)
├── research.md                      # Phase 0 output (/speckit-plan command)
├── data-model.md                    # Phase 1 output (/speckit-plan command)
├── quickstart.md                    # Phase 1 output (/speckit-plan command)
├── contracts/
│   └── landing-zone-location.md     # Phase 1 output — path/naming interface for features 003+
├── checklists/
│   └── requirements.md              # Spec quality checklist (/speckit-specify command)
└── tasks.md                         # Phase 2 output (/speckit-tasks command - NOT created by /speckit-plan)
```

### Source Code (repository root)

```text
ifood_case/
├── src/
│   └── ingestion/
│       ├── __init__.py
│       ├── network_check.py     # FR-001: reachability probe (research.md §1)
│       ├── landing_zone.py      # FR-003: idempotent catalog/schema/volume provisioning
│       └── land_files.py        # FR-004/005/006/008: download-or-upload + batch verification (size-outlier + readability) + one retry per failing month
├── data/                        # Existing fallback staging dir (feature 001), used only if FR-002 triggers
├── DECISOES_PROJETO.md          # §2 extended with this feature's environment findings (FR-007)
└── specs/002-ambiente-landing-zone/  # This feature's docs (above)
```

**Structure Decision**: Single-project layout, consistent with feature
001. A new `src/ingestion/` package holds the three scripts this feature
needs; no new top-level directory is created since `src/` and `data/`
already exist from feature 001's scaffold. No `tests/` directory is added
— per Technical Context, verification here is operational
(`quickstart.md`), not unit-testable application logic; the first feature
to introduce testable transformation logic (likely 003 or 005) is where a
`tests/` directory earns its place, consistent with how feature 001
reasoned about the same point.

## Complexity Tracking

*No entries — the Constitution Check above found no unjustified
violations. The one binding gate (Principle IV) is satisfied by this
feature's own requirements (FR-001, FR-002, FR-007), not complexity
needing a separate exception.*

## Post-Design Constitution Re-Check

Re-evaluated after Phase 1 (`data-model.md`, `contracts/landing-zone-location.md`,
`quickstart.md`): unchanged from the pre-Phase-0 assessment above.
`data-model.md` confirms the only entities are landing-process metadata
(Landing Zone, Monthly Trip Record File) — no file content is modeled, so
Principle I/II remain correctly not-yet-applicable. The interface contract
makes the "single, unambiguous location" requirement (FR-003) concrete and
checkable rather than aspirational. **Result: PASS, no new violations.**
