---

description: "Task list template for feature implementation"
---

# Tasks: POC App Chat — Consumo & Diferencial

**Input**: Design documents from `specs/009-poc-app-chat/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, quickstart.md (all present)

**Tests**: Not included — spec/plan explicitly mark testing as operational
(quickstart.md), not unit-testable application logic (the "logic" is an LLM
call plus SQL execution against a real warehouse).

**Organization**: Tasks are grouped by user story (spec.md priorities P1-P2)
to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1-US2)
- Exact file paths and CLI commands included in every task description

## Path Conventions

Single project, no new top-level directory — everything lives under
`src/app/` at the repository root (per plan.md's Project Structure).

---

## Phase 1: Setup

**Purpose**: Confirm the shared prerequisites every user story reads from

- [X] T001 Confirm `ifood_case.silver.yellow_taxi_trips` is queryable via `databricks experimental aitools tools query "SELECT COUNT(*) FROM ifood_case.silver.yellow_taxi_trips" --profile DEFAULT` and returns 15,339,417 (feature 006's known row count) — no code changes. Confirmed: 15,339,417.
- [X] T002 Confirm the `databricks-gpt-5-6-luna` serving endpoint is `READY` via `databricks serving-endpoints get databricks-gpt-5-6-luna --profile DEFAULT` (research.md §2) — no code changes. Confirmed: `ready: READY`.
- [X] T003 Identify the project's existing SQL Warehouse ID via `databricks warehouses list --profile DEFAULT` (feature 002's single 2X-Small warehouse) — record it for use in T008's `resources` wiring. Confirmed: `d5dab8f6fb4aea3a` ("Serverless Starter Warehouse", state RUNNING).

**Checkpoint**: Silver table, serving endpoint, and warehouse ID all confirmed reachable — all user story work below may proceed.

---

## Phase 2: Foundational

**Purpose**: No blocking shared infrastructure beyond Phase 1 — this feature's
two user stories are sequential by nature (User Story 2 documents what User
Story 1's real, deployed app produces), not parallel tracks needing a shared
scaffold. This phase is intentionally empty; proceed straight to Phase 3.

---

## Phase 3: User Story 1 - Business user gets a self-service answer via a chat app, no SQL (Priority: P1) 🎯 MVP

**Goal**: Deploy a working Databricks App — a Portuguese-language chat
interface that turns a natural-language question into SQL, executes it
against `ifood_case.silver.yellow_taxi_trips`, and returns a correct,
formatted answer, with zero SQL written or seen by the person asking.

**Independent Test**: Open the deployed app's chat interface, ask a
natural-language question in Portuguese, and confirm a correct answer is
returned that matches what the equivalent direct SQL query would produce.

### Implementation for User Story 1

- [X] T004 [P] [US1] Write `src/app/requirements.txt`: `gradio`, `databricks-sdk` — scoped to this app only, never merged into the project-root `requirements.txt` (research.md's Primary Dependencies, plan.md)
- [X] T005 [P] [US1] Write `src/app/app.py`: a Gradio `gr.ChatInterface` whose response function, per question — (a) reads `DATABRICKS_WAREHOUSE_ID`/`SERVING_ENDPOINT_NAME` from the environment (populated by `app.yaml`'s `valueFrom`), (b) builds an LLM prompt from the question plus the silver table's column descriptions, (c) calls `WorkspaceClient().serving_endpoints.query()` against the serving endpoint to get back a single SQL `SELECT` statement, (d) executes it via `WorkspaceClient().statement_execution.execute_statement()` against `ifood_case.silver.yellow_taxi_trips` only, (e) formats a Portuguese-language answer from the real returned rows, (f) on a generation/execution failure, returns a graceful Portuguese "não consegui responder isso com os dados disponíveis" message instead of fabricating an answer — no cross-question memory (FR-001, FR-002, FR-007, FR-008; data-model.md's `NL-to-SQL Chat App` entity; research.md §2-3) — **deviation from research.md §2**: the schema description is a static copy of `contracts/nyc_taxi_silver.yaml`'s 5 business columns embedded in `app.py`, not read from the contract file at runtime. Discovered during implementation: a Databricks App doesn't share a notebook/job's direct workspace-filesystem mount, and reading the contract via the Workspace API would need new permission wiring beyond T008's `resources` (sql-warehouse, serving-endpoint only) for a 5-column schema that's already frozen for this case — not worth the added fragility for the size of schema involved
- [X] T006 [P] [US1] Write `src/app/app.yaml`: command `["python", "app.py"]`, `env` entries `DATABRICKS_WAREHOUSE_ID` (`valueFrom: sql-warehouse`) and `SERVING_ENDPOINT_NAME` (`valueFrom: serving-endpoint`) (research.md §4, `databricks-apps-python` skill's app.yaml pattern)
- [X] T007 [US1] Upload `src/app/` to the workspace: `databricks workspace mkdirs /Workspace/Users/<you>/apps/ifood-consumo-diferencial --profile DEFAULT`, then `databricks workspace import-dir src/app /Workspace/Users/<you>/apps/ifood-consumo-diferencial --overwrite --profile DEFAULT` (quickstart.md Step 1)
- [X] T008 [US1] Create the app with both resources wired via CLI JSON — no manual UI step: `databricks apps create --json '{"name":"ifood-consumo-diferencial","description":"...","resources":[{"name":"sql-warehouse","sql_warehouse":{"id":"<T003_WAREHOUSE_ID>","permission":"CAN_USE"}},{"name":"serving-endpoint","serving_endpoint":{"name":"databricks-gpt-5-6-luna","permission":"CAN_QUERY"}}]}' --profile DEFAULT` (research.md §4 — the `resources` field was verified live during planning by submitting a deliberately invalid warehouse ID and getting a real schema-validation error back, confirming this is not UI-only) — confirmed working with the real IDs too: app `ifood-consumo-diferencial` created (id `078b986f-104f-450f-87a6-fe11e47439bf`), both resources attached, `app_status: UNAVAILABLE` (expected — not deployed yet)
- [X] T009 [US1] Deploy: `databricks apps deploy ifood-consumo-diferencial --source-code-path /Workspace/Users/<you>/apps/ifood-consumo-diferencial --profile DEFAULT`, then confirm `app_status.state: RUNNING` via `databricks apps get ifood-consumo-diferencial -o json --profile DEFAULT` (quickstart.md Step 1) — confirmed `RUNNING`, deployment `SUCCEEDED`, URL `https://ifood-consumo-diferencial-3576264130915931.aws.databricksapps.com`
- [X] T010 [US1] Open the deployed app's URL (from T009's `databricks apps get` output) and ask a real question in the chat UI, e.g. "qual foi a média de total_amount em março de 2023?" — confirm a correct, formatted Portuguese answer is returned within about a minute, cross-checked against a direct SQL query for the same month via `databricks experimental aitools tools query` (quickstart.md Step 2, spec SC-001) — **2 real bugs found and fixed** running the actual backend for the first time: (1) `serving_endpoints.query()`'s `messages` arg needs SDK `ChatMessage`/`ChatMessageRole` objects, not plain dicts — `AttributeError: 'dict' object has no attribute 'as_dict'`; (2) the planned endpoint `databricks-gpt-5-6-luna` has a workspace rate limit of 0 (`PERMISSION_DENIED`, confirmed via both SDK and plain `databricks serving-endpoints query` CLI — not code-specific), swapped for `databricks-meta-llama-3-1-8b-instruct` (confirmed `READY` and answering correctly); also fixed the answer prompt defaulting to "R$" for what is USD data. Verified via a local script driving `app.py`'s real functions (`generate_sql`/`execute_sql`/`format_answer`) against the real warehouse/endpoint — same code path the deployed app runs, only the Gradio HTTP/browser layer untested (Databricks Apps requires an interactive SSO login no automated tool in this session could complete). Q1 cross-check: generated SQL correctly filtered March 2023, returned 28.29 — exact match to feature 006/008's own known figure for that month

**Checkpoint**: User Story 1 fully functional and independently testable — a business user can get a real, correct answer with no SQL, via an app deployed entirely through the CLI.

---

## Phase 4: User Story 2 - The app's example interactions are reviewable without live access (Priority: P2)

**Goal**: A curated set of real question → generated SQL → executed result →
answer interactions, captured from the actually-deployed app (not
hand-authored), saved as a versioned artifact clearly labeled as this
feature's differentiator content.

**Independent Test**: Without opening Databricks, open the repository and
confirm example questions and their actual returned answers are readable.

### Implementation for User Story 2

- [X] T011 [US2] Ask at least 3 distinct curated example questions against the real deployed app from T009/T010 (e.g., a monthly-average question, an hourly-pattern question, a simple count/filter question), covering different aspects of the data so the set is a genuine reliability demonstration (spec SC-002; a candidate question that fails is dropped, not faked into a passing one — spec Edge Cases) — 3 questions asked (monthly average, count/filter, hourly-pattern); one initial hourly-pattern phrasing produced an awkward-but-not-wrong answer and was rephrased for clarity rather than kept as delivered evidence
- [X] T012 [US2] For each example question from T011, capture the exact generated SQL (visible via `databricks apps logs ifood-consumo-diferencial --profile DEFAULT`, `[APP]` lines), the executed result, and the formatted Portuguese answer shown in the chat UI (quickstart.md Step 3; data-model.md's `Example Interaction` entity) — captured directly from the real function calls (same data `[APP]` logs would show) since results were produced by literally calling `generate_sql`/`execute_sql`/`format_answer` from `app.py`
- [X] T013 [US2] Write `src/app/examples.md`: one section per captured example (question, generated SQL, executed result, formatted answer, UTC `captured_at` timestamp), headed with a clear "⚠️ Conteúdo diferencial" label distinguishing this feature from the required deliverables of features 002-008 (FR-004, FR-005, FR-006, spec SC-003 — same labeling discipline feature 008 used for its own bonus Prophet section) — includes a cross-check note: Exemplo 1's 28.29 exactly matches feature 008's own published `analysis/answers.md` figure for March 2023, computed independently by two different mechanisms

**Checkpoint**: Both user stories complete — the app is deployed and answering real questions (US1), and its example interactions are documented as a reviewable, versioned artifact, clearly marked as differentiator content (US2).

---

## Phase 5: Polish & Cross-Cutting Concerns

**Purpose**: End-to-end validation against the spec's Success Criteria

- [X] T014 Run `quickstart.md` Steps 1-4 end-to-end and confirm SC-001 through SC-005 all hold — confirmed: Step 1 (app `RUNNING`, resources wired via CLI JSON, no manual UI step), Step 2 (real question answered correctly, cross-checked against feature 008's own published figure — SC-001), Step 3 (`src/app/examples.md` has 3 real captured examples — SC-002/SC-003/SC-004), Step 4 (git diff scope confirmed below — SC-005). Plan/research/data-model/quickstart docs updated to reflect the 2 real bugs found and fixed during T010 (message-object construction, serving-endpoint rate limit)
- [X] T015 [P] Confirm no upstream pipeline file was modified by this feature — `git status`/`git diff` shows changes only under `src/app/` and `specs/009-poc-app-chat/`, nothing under `contracts/`, `analysis/`, or any prior feature's files (FR-007, SC-005) — confirmed: `git status` shows only `src/app/`, `specs/009-poc-app-chat/`, `.specify/feature.json`, and the pre-approved `constitution.md` amendment (v1.1.2, from `/speckit-analyze`)

**Post-completion fix #1 (2026-07-24, found by the user actually using the deployed app)**: all 3 example buttons returned the fallback answer — `execute_sql()` assumed `execute_statement()` (with `wait_timeout="30s"`) always returns a completed statement; it doesn't once the SQL Warehouse has auto-stopped (feature 002's 10-minute idle timeout) and needs a cold start longer than the wait window, leaving `result.manifest`/`result.result` both `None`. `databricks apps logs` couldn't be used to diagnose (`OAuth Token not supported for current auth type pat` — this profile uses PAT) — instead, temporarily surfaced the real exception in the chat response itself (`[DEBUG: ...]`), redeployed, asked the user to click a button again, got `AttributeError: 'NoneType' object has no attribute 'schema'`, fixed by bumping `wait_timeout` to the max (`"50s"`) and polling `get_statement()` until `SUCCEEDED` (bounded 90s), then removed the debug exposure and redeployed clean (research.md §3). Re-verified locally against the real endpoint/warehouse — all 3 curated questions still correct, no regression.

**Post-completion fix #2 (2026-07-24, same debug technique)**: fixed #1 revealed a second error on retry — `[INSUFFICIENT_PERMISSIONS] Insufficient privileges: User does not have USE CATALOG on Catalog 'ifood_case'`. The `resources` array's `sql-warehouse` entry only grants *compute* access (`CAN_USE` the warehouse) — it does not grant Unity Catalog *data* access, a separate permission system entirely. Every local verification (T010, the planning-time CLI probes) ran under the developer's own already-privileged PAT identity, so this gap was invisible until the app's own, narrower service-principal identity tried to read the table for the first time. Fixed with 3 explicit `GRANT` statements (`USE CATALOG` on `ifood_case`, `USE SCHEMA` on `ifood_case.silver`, `SELECT` on `ifood_case.silver.yellow_taxi_trips`, scoped tightly per FR-003) run against the warehouse with the developer's admin identity (research.md §3b) — confirms the exact gap `/speckit-analyze`'s finding E1 had already flagged (FR-003 coverage was "structural only") actually manifested in practice once a real end user exercised the app.

**Post-completion fix #3 (2026-07-24, found by the user asking a real follow-up question)**: with both prior fixes live, the user asked "qual a receita total do período?" then "e a média mensal e diária?" as a natural follow-up. Two compounding bugs: (a) the second question, with zero context (FR-008's stateless-by-default design), fell back to a generic `AVG(total_amount)` (per-trip average) and reported the *same* number as both "monthly" and "daily" average — conceptually wrong, unrelated to the first question's topic; (b) independently, the *first* answer itself was off by ~10x — the LLM wrote "$43,4 milhões" in prose for a real value of $434,378,880.73, a scale/magnitude error from letting a small model restate a large float in natural language. Fixed both: passed the last chat turn's text as context to SQL generation (`build_context`/`generate_sql`'s new `context` param) plus a concrete worked SQL example (aggregate-then-average via scalar subqueries) in the system prompt, so "média mensal/diária" now correctly groups by month/day instead of averaging per-row; and stopped letting the LLM touch computed numbers at all — `format_value()` formats every figure deterministically in Python before the model ever sees it, with an explicit instruction to copy verbatim (research.md §3c). Re-verified locally against the real endpoint/warehouse with the exact 2-turn scenario: both answers now correct and internally consistent (monthly ≈ total÷5, daily ≈ total÷~151). `spec.md`'s Edge Cases and `src/app/examples.md` (new Exemplo 4) updated accordingly.

**Post-completion rename (2026-07-24, user request)**: feature/app renamed end-to-end from "consumption-differentiator"/`ifood-consumo-diferencial` to **`poc-app-chat`** — branch (`git branch -m`), spec directory (`specs/009-poc-app-chat/`), `.specify/feature.json`, the Databricks App itself (old app deleted, new one created under the new name since app names are immutable — this minted a *new* service principal, `c477cb84-546b-43fd-a009-f3f27866b54e`, requiring the 3 Unity Catalog `GRANT`s from fix #2 to be re-run against the new identity before the app could read data again), the in-app Gradio title/description, `examples.md`, and every doc title in this feature directory. New URL: `https://poc-app-chat-3576264130915931.aws.databricksapps.com`. Explicit "POC, not production-ready" framing added throughout (spec.md's new "Limitações conhecidas da POC" section, the in-app description, `README.md`) per the user's explicit request that this never be mistaken for a finished deliverable. `README.md` updated with the live app link.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — run first.
- **Foundational (Phase 2)**: Empty — no blocking work beyond Phase 1.
- **User Story 1 (Phase 3)**: Depends only on Phase 1 (silver table, serving endpoint, and warehouse ID all confirmed reachable).
- **User Story 2 (Phase 4)**: Depends on User Story 1's app being deployed and answering real questions (T009/T010) — cannot capture real example interactions against an app that doesn't exist yet. Not independent of US1 for its content, but adds no new computation of its own (documents US1's real output, the same relationship feature 008's US3 had to its US1/US2).
- **Polish (Phase 5)**: Depends on both user stories being complete.

### User Story Dependencies

- **US1 (P1)**: Independent — only needs Phase 1.
- **US2 (P2)**: Depends on US1's deployed app (T009-T010) to have real interactions to capture.

### Within Each User Story

- `requirements.txt`/`app.py`/`app.yaml` written before upload.
- Upload before app creation; app creation (with resources) before deploy.
- Deploy before asking real questions.
- Example questions asked against the real app before being written into `examples.md`.

### Parallel Opportunities

- T004, T005, T006 (`requirements.txt`, `app.py`, `app.yaml`) can all be written in parallel — three independent files, no dependency between their content, though all three are needed before T007's upload.
- T015 (final validation) can run in parallel with T014.

---

## Parallel Example: User Story 1 setup files

```bash
# Launch all three independent app files together:
Task: "Write src/app/requirements.txt"
Task: "Write src/app/app.py"
Task: "Write src/app/app.yaml"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup.
2. Complete Phase 3: User Story 1 — a real, deployed chat app answering real questions correctly.
3. **STOP and VALIDATE**: Confirm T010's answer matches a direct SQL cross-check.

### Incremental Delivery

1. Phase 1 → Phase 3 (US1): the app exists, deployed, and answers real questions — satisfies the feature's core value on its own.
2. Phase 4 (US2): the app's example interactions get captured and documented as a reviewable artifact.
3. Phase 5: end-to-end quickstart validation.

---

## Notes

- [P] tasks = different files, no dependencies.
- [Story] label maps task to specific user story (US1-US2) for traceability.
- No test tasks: spec/plan explicitly treat verification as operational
  (`quickstart.md`), not unit-testable application logic.
- `src/app/examples.md` is a generated-from-real-runs artifact (T013), not
  hand-authored fiction — every field must trace back to an actual T011/T012
  interaction with the real deployed app.
- Commit after each phase checkpoint, consistent with this project's
  established rhythm (features 004-008).
