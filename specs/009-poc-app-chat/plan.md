# Implementation Plan: POC App Chat — Consumo

**Branch**: `009-poc-app-chat` | **Date**: 2026-07-23 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `specs/009-poc-app-chat/spec.md`

## Summary

Deliver a single custom **Databricks App** — a Portuguese-language chat
interface where a business user types a natural-language question about
`ifood_case.silver.yellow_taxi_trips` and gets a correct, formatted
answer, with no SQL written or seen. Per Clarifications, this replaces
the roadmap's originally-planned Genie Space entirely (Genie's own setup
is UI-only with no CLI/API path, unlike every prior feature; the user
explicitly rejected using it) and is this feature's single deliverable —
both the consumption interface and the case's POC/bonus content at
once, not two separate pieces.

The app's backend, on each question: calls a Databricks Foundation Model
serving endpoint (`databricks-meta-llama-3-1-8b-instruct` — swapped
from the originally-planned `databricks-gpt-5-6-luna` during
implementation, which turned out to have a workspace rate limit of 0;
research.md §2) to generate the SQL that
answers the question, executes that SQL against the project's existing
SQL Warehouse via the Databricks SDK's `statement_execution` API
(reading the silver table only), and returns a formatted Portuguese
answer built from the real result — never a canned or hallucinated
response. Built with **Gradio** (`gr.ChatInterface`, pre-installed on
the Databricks Apps Python runtime) rather than AppKit, because AppKit's
only natural-language-query mechanism is its `genie()` plugin, which
routes through Genie Space under the hood — exactly what this feature
must avoid.

Everything is deployed end-to-end via the Databricks CLI, including
wiring the app to its SQL Warehouse and serving-endpoint resources —
confirmed live (not assumed) during planning that `databricks apps
create --json` accepts a `resources` array validated against real
resource IDs, so no manual UI configuration step is needed, keeping this
feature consistent with every prior feature's "Claude Code executes
end-to-end via the CLI" pattern.

## Technical Context

**Language/Version**: Python 3.11 (Databricks Apps' fixed runtime,
Ubuntu 22.04) — a new target beyond this project's PySpark/notebook
code, but still Python, consistent with the project's language even
where the constitution's fixed stack doesn't itself cover an
interactive app.

**Primary Dependencies**: `gradio` (chat UI — pre-installed on the
Databricks Apps Python runtime, no install step; `ChatInterface`
purpose-built for exactly this question-in/answer-out shape, per the
`databricks-apps-python` skill's own routing table); `databricks-sdk`'s
`WorkspaceClient` (`serving_endpoints.query()` for the NL→SQL
generation call, `statement_execution.execute_statement()` to run the
generated SQL) — scoped to the app's own `src/app/requirements.txt`,
never added to the project-root `requirements.txt` (same discipline
feature 008 used for matplotlib/prophet/plotly: dependencies that only
run inside Databricks, never locally, stay out of the root file).

**Storage**: Reads `ifood_case.silver.yellow_taxi_trips` only (features
004-006). Writes nothing — no table, no schema, no persisted state; the
app is fully stateless per request (spec FR-008 — no cross-question
memory needed, so no Lakebase/database resource is used).

**Testing**: N/A — no unit-testable application logic in the
traditional sense (the "logic" is an LLM call). Verification is
operational: deploy the real app, ask the curated example questions
against it for real, and confirm each answer is correct — same
operational-verification pattern as features 008 and (implicitly) every
prior feature's `quickstart.md`.

**Target Platform**: Databricks Apps (Free Edition workspace) — its own
managed compute (2 vCPU / 6 GB, separate from the project's SQL
Warehouse), reached via `https://<app>.<workspace>.databricksapps.com`
after deploy. The app's *queries* still land on the project's existing
single 2X-Small SQL Warehouse (feature 002) — Apps compute runs the
Python/Gradio process; the warehouse runs the SQL.

**Project Type**: Single project. Adds `src/app/` only — the
constitution's `src/` is defined generically as "código fonte da
solução" (not restricted to pipeline code), so this genuine source-code
deliverable (not a notebook, not an analysis script) belongs there
rather than introducing a new top-level directory (Principle VI).

**Performance Goals**: Each question answered well under one minute
end-to-end (LLM call + SQL execution + formatting) — matches spec
SC-001. No concurrency/throughput target: this is a POC prototype for
a case evaluator to try, not a production service sized for concurrent
users.

**Constraints**: Free Edition's serverless-only compute / single
2X-Small SQL Warehouse constraints (feature 002) apply unchanged — the
app directs all its generated SQL at that one existing warehouse, never
provisions new compute. No Lakebase, no Vector Search, no new UC
resources of any kind.

**Scale/Scope**: 1 Databricks App (`src/app/`: `app.py` chat UI +
backend logic, `requirements.txt`, `app.yaml`), at least 3 curated
example questions (spec SC-002) verified against the real deployed app
and saved as a versioned artifact (`src/app/examples.md`).

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Applies? | Assessment |
|---|---|---|
| I. Data Quality Is a Gate | No | Reads already-cleaned data (features 004-006); introduces no new data-quality rule. |
| II. Data Contracts First | No | Reads the silver table under its existing contract (feature 005); doesn't write any table, so no new contract is needed. |
| III. Observability Is Part of the Deliverable | No | A read-only consumption app answering ad hoc questions is not a "pipeline execution" in Principle III's sense (no rows dropped/flagged, nothing to log to `_pipeline_run_log`) — same reasoning feature 008 already established for its own read-only notebook. |
| IV. Fixed Stack, Justified Deviations | **Yes** | This feature's entire existence is a pre-approved deviation — the constitution itself names "a custom NL-to-SQL agent built with the Databricks MCP/platform" as expected POC content (Development Workflow section). Specific new pieces beyond the fixed PySpark/Delta/UC/SQL-Warehouse stack, each justified in Complexity Tracking below: the Databricks Apps platform itself, Gradio, a Foundation Model serving endpoint call, and `databricks-sdk` usage from application code (every prior feature used the Databricks *CLI*, not the *SDK* from within running app code — a genuinely new pattern for this project, necessary because a live app process needs a Python-native API, not a shell-invoked CLI). |
| V. Spec-Driven Development Workflow | **Yes** | Specify → Clarify (3 questions, spec substantially revised) → Plan (this document) → Tasks → Implement — satisfied by construction. |
| VI. Lean Instructions, Simple Architecture | **Yes** | One app, one directory (`src/app/`), no new schema, no new table, no gold layer. Single deliverable per Clarifications (not two, as the roadmap originally split it) — actively *less* architecture than the original plan, not more. |

**Result**: PASS. Deviations from the fixed stack are real but
pre-approved by the constitution's own framing of this feature as POC
content; each is itemized in Complexity Tracking below, not silently
introduced. Re-checked after Phase 1 below.

## Project Structure

### Documentation (this feature)

```text
specs/009-poc-app-chat/
├── plan.md                       # This file (/speckit-plan command output)
├── research.md                   # Phase 0 output (/speckit-plan command)
├── data-model.md                 # Phase 1 output (/speckit-plan command)
├── quickstart.md                 # Phase 1 output (/speckit-plan command)
├── checklists/
│   └── requirements.md           # Spec quality checklist (/speckit-specify + /speckit-clarify)
└── tasks.md                      # Phase 2 output (/speckit-tasks command - NOT created by /speckit-plan)
```

No `contracts/` subfolder: the app's only "interface" is its own chat
UI and its calls to two existing Databricks platform APIs (Foundation
Model serving, SQL statement execution) — not a new API this project
exposes to other consumers, so there's no new contract format to
document structurally.

### Source Code (repository root)

```text
ifood_case/
├── src/
│   └── app/
│       ├── app.py              # US1 / FR-001, FR-002, FR-008: Gradio ChatInterface + backend (question -> generated SQL -> executed result -> formatted PT-BR answer), stateless per question
│       ├── requirements.txt    # US1: gradio, databricks-sdk -- scoped to this app only, never merged into project-root requirements.txt
│       ├── app.yaml            # US1: Databricks Apps runtime config (command, resource valueFrom for sql-warehouse + serving-endpoint)
│       └── examples.md         # US2 / FR-004, FR-005, FR-006: curated example questions with their real generated SQL + executed answers, run against the actually-deployed app, clearly labeled as POC/bonus content
```

**Structure Decision**: Single-project layout, consistent with features
001-008. `src/` (already the constitution's generic "código fonte da
solução" directory) gains one new subdirectory, `src/app/`, for this
feature's one deliverable — no new top-level directory, no `tests/`
(verification is operational per `quickstart.md`, matching every prior
feature that had no unit-testable application logic).

## Complexity Tracking

| Deviation | Why needed | Simpler alternative rejected because |
|---|---|---|
| Databricks Apps platform (new for this project — features 002-008 used CLI-driven jobs/notebooks/SQL Warehouse only, never a deployed app) | This feature's whole purpose (roadmap: "Consumo", POC) is a natural-language consumption interface with a real UI a business user interacts with directly — no fixed-stack tool provides that | A notebook (feature 008's pattern) has no persistent, user-facing chat UI; the case brief and roadmap both point to something more interactive than a notebook for this specific feature |
| Gradio (new Python web framework) | Pre-installed on the Databricks Apps Python runtime (no install step); `gr.ChatInterface` is purpose-built for exactly this question-in/answer-out chat shape | AppKit (this project's other Databricks-app option) — rejected because its only NL-query mechanism is the `genie()` plugin, which routes through Genie Space under the hood; the user explicitly rejected Genie anywhere in this feature (Clarifications) |
| Foundation Model serving endpoint call (`databricks-meta-llama-3-1-8b-instruct`, via `databricks-sdk`) | An LLM call is the only way to translate an open-ended natural-language question into SQL — there is no fixed-stack, non-AI way to do this | N/A — this is the literal mechanism the feature exists to demonstrate; not avoidable without abandoning the "NL-to-SQL" premise itself |
| `databricks-sdk`'s `WorkspaceClient` called from live application code (not the CLI) | A running Gradio app process needs a Python-native API to call the serving endpoint and execute SQL per request — the CLI (every prior feature's mechanism) is a shell tool invoked once per command, not embeddable in a request-handling loop | Shelling out to the `databricks` CLI from within the app process per question — rejected as fragile and slow (process-spawn overhead per chat message) compared to the SDK's native Python client reusing one authenticated session |

No entries beyond these — the rest of the Constitution Check above
found no violations requiring justification. This table also
supersedes the earlier, now-obsolete Complexity Tracking concern this
feature would have needed for a Genie Space (manual UI configuration,
no CLI path) — that whole class of deviation no longer applies now that
Genie isn't used at all.

## Post-Design Constitution Re-Check

Re-evaluated after Phase 1 (`data-model.md`, `quickstart.md`): unchanged
from the pre-Phase-0 assessment above. `data-model.md` confirms the
`NL-to-SQL Chat App` and `Example Interaction` entities from spec.md's
Key Entities map cleanly onto `src/app/app.py`'s runtime behavior and
`src/app/examples.md`'s file structure, with nothing extraneous beyond
what FR-001–008 ask for. **Result: PASS, no new violations.**
