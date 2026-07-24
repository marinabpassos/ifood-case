# Phase 0 Research: POC App Chat — Consumo

**Input**: [spec.md](./spec.md) · Constitution `.specify/memory/constitution.md` ·
`ifood_case.silver.yellow_taxi_trips` (features 004-006)

No `[NEEDS CLARIFICATION]` markers remain in the spec — the
`/speckit-clarify` session (2026-07-23, 3 questions) already resolved
this feature's core architecture question (Genie → custom Databricks
App) before planning began. This research phase resolves the
*technical* decisions the spec deliberately left open (Assumptions:
"exact model/mechanism is a planning-phase technical decision").

## 1. Why not AppKit (this project's other, "default" Databricks App option)

- **Decision**: Build with a **Python backend (Gradio)**, not AppKit
  (Node/TypeScript/React — the `databricks-apps` skill's stated default
  for new apps).
- **Rationale**: AppKit's only mechanism for "natural language query
  interface over tables" is its `genie()` plugin — which, per the
  skill's own Genie Agent Workflow, means creating and wiring a real
  Genie Space (`databricks genie create-space`) under the hood. The
  user explicitly rejected using Genie Space anywhere in this feature
  (Clarifications). AppKit's other pattern, the `analytics` plugin, is
  built around *known, static* SQL files resolved at build time via
  `npm run typegen` — explicitly wrong for this feature, where the SQL
  text doesn't exist until a user's question arrives at request time
  ("NEVER add custom endpoints to run SELECT queries against the
  warehouse" is the `analytics` plugin's own rule, for exactly this
  static/dynamic distinction). A custom Express endpoint calling a
  foundation model and then executing dynamic SQL is technically
  possible in AppKit, but fights the framework's typed, build-time-query
  design at every step.
- **Alternatives considered**: FastAPI (this project's Python-backend
  default per `databricks-apps-python`) + a hand-built HTML/JS chat
  frontend — rejected as more code for the same outcome, when Gradio's
  `gr.ChatInterface` is a pre-installed, purpose-built chat component
  requiring far less custom frontend work for a prototype-scoped
  deliverable. Streamlit — a reasonable alternative, not chosen only
  because Gradio's chat primitive is a more direct fit than Streamlit's
  general-purpose widget model for a specifically conversational UI.

## 2. NL-to-SQL generation mechanism

- **Decision (revised after implementation)**: The app's backend calls
  `WorkspaceClient().serving_endpoints.query()` against the
  `databricks-meta-llama-3-1-8b-instruct` Foundation Model endpoint,
  passing the user's question plus the silver table's known schema
  (column names/types/business meaning — a static copy of the 5
  business columns from `contracts/nyc_taxi_silver.yaml`, feature 005,
  embedded directly in `app.py` rather than read from the contract file
  at runtime — a Databricks App doesn't share a notebook/job's direct
  workspace-filesystem mount, and reading it via the Workspace API would
  need new permission wiring beyond T008's `resources` for a 5-column
  schema that's already frozen for this case) as context, and
  instructing the model to return only a single SQL `SELECT` statement
  against `ifood_case.silver.yellow_taxi_trips`.
- **Rationale**: The originally-planned endpoint, `databricks-gpt-5-6-luna`
  (chosen for being "the fast, cost-efficient model" per its own
  metadata, confirmed `READY` during planning), turned out to have a
  workspace-set rate limit of 0 — discovered running the actual call for
  the first time during implementation (T010): `PERMISSION_DENIED: The
  endpoint is temporarily disabled due to a Databricks-set rate limit of
  0`, reproduced identically via both the SDK and a plain `databricks
  serving-endpoints query` CLI call (not code-specific — a real
  workspace/endpoint constraint, likely because this newer premium model
  needs an AI Gateway quota this Free Edition workspace doesn't have
  configured). `databricks-meta-llama-3-1-8b-instruct` was tried next and
  confirmed working end-to-end (correct SQL generated, correct answer
  returned) — a capable, low-cost instruction-tuned model, a reasonable
  fit for this bounded, structured task once the originally-planned
  endpoint proved unusable.
- **Alternatives considered**: `ai_query()` as a SQL function (calling
  the model from inside a SQL statement) — rejected because it doesn't
  cleanly separate "generate SQL" from "execute SQL" the way two
  sequential SDK calls do, making error handling (a malformed generated
  query) harder to isolate. Other larger/more expensive models
  (`databricks-gpt-5-6-sol`, `claude-opus-4-8`) — not tried once Llama
  3.1 8B was confirmed working end-to-end; no evidence a larger model
  was needed for a task this bounded (5-column schema, one SQL
  statement out).

## 3. SQL execution mechanism

- **Decision**: `WorkspaceClient().statement_execution.execute_statement()`,
  targeting the project's existing single SQL Warehouse (feature 002),
  executing the model-generated SQL text directly — with polling via
  `get_statement()` for any statement still `PENDING`/`RUNNING` when the
  call returns, not an assumption that the response is always complete.
- **Rationale**: Same SDK client as decision 2 (one authenticated
  `WorkspaceClient()` per app process, reused across both calls) — the
  `databricks-python-sdk` skill documents this exact API for ad hoc
  statement execution, returning rows the app formats into its
  Portuguese answer. Reuses the one warehouse every prior feature's SQL
  path already uses — no new compute provisioned (constitution's Free
  Edition constraint). **Bug found post-deployment (2026-07-24)**: the
  first version of `execute_sql()` read `result.manifest.schema.columns`
  unconditionally, assuming `execute_statement()` (called with
  `wait_timeout="30s"`) always returns a completed statement — it
  doesn't. `wait_timeout` maxes out at `"50s"` (SDK-enforced range: 0 or
  5-50), and the project's single 2X-Small SQL Warehouse auto-stops
  after 10 minutes idle (feature 002); a cold start after auto-stop can
  take longer than that window, leaving the statement `PENDING`/
  `RUNNING` and `manifest`/`result` both `None` — `AttributeError:
  'NoneType' object has no attribute 'schema'`. The user hit this
  live (all 3 example buttons returned the fallback answer) after the
  warehouse had gone idle since T010's original verification. Fixed by
  bumping `wait_timeout` to the max (`"50s"`) and polling
  `get_statement(statement_id)` every 2s (bounded to 90s total) until
  `state == SUCCEEDED`, raising a clear error on `FAILED`/`CANCELED`/
  timeout instead of assuming success.
- **Alternatives considered**: `databricks-sql-connector`'s
  `sql.connect()`/cursor pattern (also documented in
  `databricks-apps-python`) — either would work; the SDK's
  `statement_execution` API was chosen only to avoid a second
  connection/auth pattern in the same file when `WorkspaceClient()` is
  already open for the serving-endpoint call.

## 3b. Unity Catalog data grants for the app's service principal (found post-deployment)

- **Decision**: The app's service principal (client ID
  `078b986f-104f-450f-87a6-fe11e47439bf`, same as the app's own `id`)
  needs its own, explicit Unity Catalog grants — `USE CATALOG` on
  `ifood_case`, `USE SCHEMA` on `ifood_case.silver`, `SELECT` on
  `ifood_case.silver.yellow_taxi_trips` — separate from, and in
  addition to, the `sql-warehouse` resource wired in decision 4 below.
- **Rationale**: The `resources` array's `sql_warehouse` entry (`CAN_USE`
  permission) only grants the app's identity the right to *use the
  warehouse as compute* — it does not grant Unity Catalog *data* access.
  The two are entirely separate permission systems. This was invisible
  in every prior planning/implementation step because all local
  verification (T010's local script, the CLI probes during planning)
  ran under the developer's own PAT-authenticated identity, which
  already had catalog-owner-level access from feature 002 — only the
  app's own, narrower service-principal identity hit
  `[INSUFFICIENT_PERMISSIONS] Insufficient privileges: User does not
  have USE CATALOG on Catalog 'ifood_case'`, and only once the user
  actually used the deployed app for the first time. Granted via three
  `GRANT` statements run against the warehouse with the developer's
  admin identity — scoped tightly (table-level `SELECT`, not
  catalog-wide) per FR-003's "no bypass of existing governance"
  requirement and the `/speckit-analyze` E1 finding that flagged this
  exact gap (structural-only coverage) before implementation.
- **Alternatives considered**: Granting broader access (e.g., `SELECT`
  on the whole `silver` schema) — rejected as more than the app
  actually needs; the app reads exactly one table (FR-002).

## 3c. Follow-up question resolution and answer-number formatting (found via real user testing)

- **Decision**: (1) The last chat turn's question+answer text is passed
  as plain-text context to the SQL-generation call (`generate_sql`'s new
  `context` parameter, built by `build_context(history)`), so an
  elliptical follow-up like "e a média mensal e diária?" can resolve
  what "a média" refers to. (2) `format_answer` no longer lets the LLM
  restate computed numbers freely — `format_value()` formats every
  numeric result deterministically in Python (BR-style separators)
  *before* the LLM sees it, and the answer-generation prompt instructs
  the model to copy those figures verbatim, never re-deriving or
  rescaling them.
- **Rationale**: A real 2-turn conversation ("qual a receita total do
  período?" → "e a média mensal e diária?") exposed two compounding
  problems at once: (a) with zero context, the second question's SQL
  defaulted to a flat `AVG(total_amount)` (per-trip average, ~$28) and
  reported it as *both* the monthly *and* daily average — same number,
  wrong concept, no relation to the first question's topic (total
  revenue); (b) independently, the first answer itself was wrong by
  ~10x — the model wrote "$43,4 milhões" in prose for a real value of
  $434,378,880.73, an outright scale/magnitude error letting an 8B
  model restate a large float in natural language. Fix (1) is addressed
  with a concrete worked SQL example (scalar-subquery pattern:
  aggregate-then-average, grouped by month/day) added to
  `SQL_SYSTEM_PROMPT`, verified correct against the real warehouse
  (monthly average now $86,875,776.15 ≈ total÷5; daily average
  $2,876,681.33 ≈ total÷~151 — both internally consistent and
  cross-checked against the deterministic Python total). Fix (2)
  removes the LLM from the number-formatting critical path entirely —
  it only supplies surrounding prose now, never the digits themselves.
- **Alternatives considered**: Full structured conversation
  memory (a session store keyed by chat ID) — rejected as unnecessary
  complexity for a POC prototype; a single prior turn's text
  is enough context for the kind of elliptical follow-up this surfaced,
  and keeps FR-008's "not required to persist... conversation history"
  intent intact (nothing is persisted; it's passed through, once, as
  prompt text). Asking the LLM to double-check its own arithmetic
  (chain-of-thought before answering) — rejected in favor of removing
  the failure mode structurally (Python formats the numbers, the model
  never touches them) rather than hoping a small model self-corrects.

## 4. Resource wiring: fully CLI-automatable, verified live

- **Decision**: The app's SQL Warehouse and serving-endpoint access are
  declared via the `resources` array in the JSON body passed to
  `databricks apps create --json`/`databricks apps update --json` —
  not configured through the Databricks Apps UI.
- **Rationale**: The `databricks-apps-python` skill's own reference doc
  states resources are added "via the Databricks Apps UI after creating
  the app," which would have meant a manual step breaking this
  project's established "Claude Code executes end-to-end via the CLI"
  pattern (every prior feature, 002-008). Rather than accept that at
  face value, this was verified directly during planning:
  ```
  databricks apps create --json '{"name":"probe-resources-test", ...,
    "resources":[{"name":"sql-warehouse","sql_warehouse":{"id":"test123","permission":"CAN_USE"}}]}'
  → Error: Invalid SQL warehouse resource sql-warehouse: ID test123 is invalid.
  ```
  The API validated the (deliberately fake) warehouse ID and rejected
  it — proof the `resources` field is real, schema-checked, and
  settable via CLI JSON at creation time, not UI-only. No app was
  actually created by this probe (it errored before creation).
- **Alternatives considered**: Accepting the skill doc's UI-only
  framing and asking the user to configure resources manually — this
  was the original plan for the (now-abandoned) Genie Space path
  (see `Clarifications`, question 1); rejected here the same way, once
  the CLI path was confirmed real.

## 5. Where the app's source code lives in the repository

- **Decision**: `src/app/` (see plan.md Project Structure).
- **Rationale**: The constitution's `src/` directory is defined
  generically as "código fonte da solução" (source code of the
  solution), not restricted to pipeline stages — this is genuine
  application source code (not a notebook, not a query file), so it
  belongs there rather than introducing a new top-level directory
  (Principle VI: lean architecture, no unnecessary new structure).
- **Alternatives considered**: A new top-level `app/` directory —
  rejected as an avoidable structural addition when `src/` already
  covers "source code" generically and has room for a new
  subdirectory. Nesting under `analysis/` — rejected, that directory is
  specifically defined (case brief + this project's own convention) as
  "answers to the two analytical questions," not a general app.

## 6. Curated example documentation format

- **Decision**: `src/app/examples.md` — one entry per curated example
  question (spec SC-002: at least 3), each with the question text, the
  SQL the app actually generated for it, the executed result, and the
  formatted answer — all captured from a real run against the deployed
  app (not hand-authored), clearly headed as POC/bonus content.
- **Rationale**: Directly mirrors feature 008's `analysis/answers.md`
  pattern (real computed results, not hypothetical ones, saved as a
  versioned artifact) — this project's own established precedent for
  "clareza na comunicação dos resultados."
- **Alternatives considered**: A JSON/structured log file instead of
  Markdown — rejected, Markdown is directly human-readable in a GitHub
  PR/repo browse without tooling, matching every prior feature's
  documentation format.
