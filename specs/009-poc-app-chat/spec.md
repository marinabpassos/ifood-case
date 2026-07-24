# Feature Specification: POC App Chat — Consumo & Diferencial

> ⚠️ **Isto é uma POC (prova de conceito), não um produto finalizado.**
> Demonstra a viabilidade de um agente NL-to-SQL sobre a silver, mas
> tem melhorias pendentes conhecidas (ver "Limitações conhecidas da
> POC" no final deste documento) — não deve ser lido como uma entrega
> pronta para produção.

**Feature Branch**: `009-poc-app-chat`

**Created**: 2026-07-23

**Status**: Draft

**Input**: User description: "feature 009 - Consumo & Diferencial: Genie Space (UI, produção) sobre a silver + protótipo do agente NL-to-SQL custom via Claude Code + MCP Databricks"

## Clarifications

### Session 2026-07-23

- Q: Genie Space's own decision-log note says it's UI-configured, with no CLI/API path — unlike every prior feature, which Claude Code executed end-to-end via the CLI. User rejected using Genie Space at all and asked for another way to build an agent inside Databricks. → A: A **Databricks App** with a custom chat interface, calling NL-to-SQL logic (e.g., via `ai_query`) behind it — not Genie Space, not a bare API-only Supervisor Agent. Fully buildable/deployable by Claude Code via CLI, no manual UI steps, no Genie anywhere in the feature.
- Q: With Genie gone, is the Databricks App one unified deliverable, or does a second, separate Claude-Code-driven agent prototype still exist alongside it (the roadmap's original two-part "production + differentiator" split)? → A: One deliverable. The Databricks App itself is both the consumption interface and the differentiator content — no second, separate agent.
- Q: What language should the app's own content (chat UI text, example questions, formatted answers) be authored in? → A: Portuguese (PT-BR) — consistent with feature 008's precedent (`answers.md`, chart labels) for content aimed at the project's end business user.
- Q (2026-07-24, post-implementation): Rename the feature/app from "consumption-differentiator" — user didn't like the name. → A: Renamed to **`poc-app-chat`** everywhere (branch, spec directory, Databricks App resource name, in-app title, all docs) and framed explicitly as a POC throughout, with a "known limitations" section added so it's never mistaken for a finished product. Link to the live app added to the repository's root `README.md`.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Business user gets a self-service answer via a chat app, no SQL (Priority: P1)

As a non-technical business stakeholder, I need to ask a question about
yellow taxi trips in plain Portuguese, through a chat-style app, and get
a correct answer — without writing SQL, opening a notebook, or asking a
data engineer.

**Why this priority**: This is this feature's entire consumption
deliverable and its differentiator content at once (per Clarifications)
— a custom-built Databricks App with an NL-to-SQL chat backend, built
and deployed end-to-end via the Databricks CLI (no Genie Space, no
manual UI configuration step for Claude Code to hand off).

**Independent Test**: Open the deployed app, type a natural-language
question about `ifood_case.silver.yellow_taxi_trips` in Portuguese
(e.g., "qual foi a média de total_amount em março de 2023?"), and
confirm a correct answer is returned with zero SQL written or seen by
the person asking.

**Acceptance Scenarios**:

1. **Given** the app is deployed and connected to
   `ifood_case.silver.yellow_taxi_trips`, **When** a business user types
   a natural-language question in the chat interface, **Then** the app
   generates the SQL that answers it, executes that SQL against the
   Databricks SQL Warehouse, and returns a correct, formatted answer in
   Portuguese that matches what the equivalent direct SQL query would
   produce.
2. **Given** the app runs under its own Databricks App identity, **When**
   it queries the silver table, **Then** it operates under the same
   Unity Catalog governance already enforced on that table — the app is
   not a way to bypass existing governance.
3. **Given** the app is meant to be reliable for the case evaluator to
   try, **When** it is delivered, **Then** it includes a small set of
   curated example questions (in the chat UI or accompanying
   documentation) known to answer correctly, so a reviewer isn't
   guessing what to ask.
4. **Given** each question is handled independently, **When** a user
   asks a follow-up question, **Then** it is processed as its own
   new question (no requirement to remember or reference earlier turns
   in the same session).

---

### User Story 2 - The app's example interactions are reviewable without live access (Priority: P2)

As the case evaluator, I need the app's example question-and-answer
interactions saved as versioned, readable artifacts in the repository,
so I can review what it actually produced without needing live
Databricks access, an active app session, or having to type anything
myself.

**Why this priority**: Directly serves "clareza na comunicação dos
resultados," one of the case's own stated evaluation criteria, and
matches this project's established pattern (see feature 008) of
delivering evidence as versioned files, not only as live UI state.
Lower priority because it documents User Story 1's output rather than
producing new capability of its own.

**Independent Test**: Without opening Databricks or the app, open the
repository and confirm example questions and their actual returned
answers are readable.

**Acceptance Scenarios**:

1. **Given** the app's curated example questions (User Story 1) have
   been asked at least once against the real deployed app, **When**
   their results are recorded, **Then** each question, the SQL the app
   generated, and its actual returned answer are saved together as a
   versioned artifact in the repository.
2. **Given** this feature is explicitly the case's differentiator
   content (roadmap: "Consumo & Diferencial"), **When** the artifact is
   delivered, **Then** it is clearly labeled as such, distinct from the
   required deliverables of features 002-008.

---

### Edge Cases

- If the app's LLM-generated SQL is invalid or fails to execute for a
  candidate example question, that question is dropped from the curated
  set rather than delivered as a known-bad example — the curated set is
  a reliability demonstration, not a liability showcase. This feature
  does not require hiding an agent's real limitations if any surface
  during prototyping; it only requires not presenting a known failure as
  a working example.
- Questions outside the scope of the yellow taxi silver table (other
  data sources, unrelated topics) are out of scope — the app is not
  expected to answer questions the underlying table cannot support; a
  graceful "I can't answer that from this data" style response is
  preferred over a fabricated or misleading answer.
- This feature does not modify `ifood_case.silver.yellow_taxi_trips`,
  its contract, or any upstream pipeline stage — the app is read-only
  against the silver table.
- The app has no persisted multi-turn conversation memory (no
  database, no session state) — each question still generates and
  executes its own independent SQL query (User Story 1, Acceptance
  Scenario 4). **Revised after real user testing (2026-07-24)**: the
  last chat turn's text (not structured state) is now passed as
  context to the SQL-generation step, so an elliptical follow-up
  question (e.g., "e a média mensal e diária?" right after "qual a
  receita total do período?") resolves correctly instead of the model
  guessing an unrelated, mislabeled answer — this is a resolution aid
  for the current question's own SQL generation, not committed memory
  of prior facts or results.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: A Databricks App MUST be built and deployed, providing a
  chat-style interface where a business user can ask a natural-language
  question in Portuguese and receive an answer without writing SQL.
- **FR-002**: The app's backend MUST, for each question: generate the
  SQL query that answers it, execute that query against the Databricks
  SQL Warehouse (reading `ifood_case.silver.yellow_taxi_trips` only),
  and return a formatted, Portuguese-language answer derived from the
  real executed result — not a canned or hallucinated response.
- **FR-003**: The app MUST operate under the same Unity Catalog
  governance and permissions already enforced on the silver table — it
  MUST NOT provide a path around existing access controls.
- **FR-004**: The app MUST include a curated set of example questions
  verified to produce correct answers, for a reviewer to try without
  guessing.
- **FR-005**: The app's example interactions (questions and their actual
  returned answers) MUST be saved as versioned artifacts in the
  repository, not left only as live Databricks UI state.
- **FR-006**: This feature's deliverable MUST be clearly documented as
  this project's differentiator content ("Consumo & Diferencial" per the
  roadmap), distinct from the required deliverables of features 002-008.
- **FR-007**: The app and its backend MUST NOT modify
  `ifood_case.silver.yellow_taxi_trips`, its contract, or any upstream
  pipeline stage (features 002-008) — read-only only.
- **FR-008**: Each question MUST be answered independently — the app is
  not required to persist or reference conversation history across
  questions in the same session.

### Key Entities

- **NL-to-SQL Chat App**: the deployed Databricks App itself — its chat
  interface, its backend logic (question → generated SQL → executed
  result → formatted answer), and its single data source
  (`ifood_case.silver.yellow_taxi_trips`).
- **Example Interaction**: one record per curated example — the
  natural-language question asked, the SQL the app generated to answer
  it, the executed result, and the formatted answer derived from that
  result. A set of these records, saved as a versioned artifact, is this
  feature's reviewable evidence (User Story 2).

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A business user with no SQL knowledge can get a correct
  answer to a data question about yellow taxi trips through the chat app
  in under one minute, without writing or reading any code.
- **SC-002**: The app correctly answers at least 3 distinct example
  natural-language questions, with each question's generated SQL and
  executed result documented.
- **SC-003**: A reader of the delivered documentation can immediately
  tell this feature is differentiator/experimental content (per the
  roadmap's "Consumo & Diferencial"), not one of the case's required
  deliverables.
- **SC-004**: The app's example results can be reviewed directly from
  files in the repository, with no live Databricks access required.
- **SC-005**: The app required no modification to the silver table, its
  contract, or any upstream pipeline stage, validating that it is
  genuinely a read-only addition on top of already-shipped work
  (features 002-008).

## Assumptions

- This feature depends only on feature 006 (silver data quality),
  already complete and merged; features 007-008 are unrelated to this
  feature's own logic but are already merged too — matching the
  project's own roadmap note that 007/008/009 can proceed in any order
  once 006 is done.
- Genie Space is explicitly **not** used anywhere in this feature (see
  Clarifications) — superseding the roadmap's original framing of it as
  the "official" consumption path. The constitution has been formally
  amended (v1.1.2, `/speckit-analyze` remediation) to reflect this: it
  now names this feature's custom Databricks App, not Genie Space, as
  the project's NL-to-SQL consumption mechanism.
- The Databricks MCP connection between Claude Code and the workspace
  (a previously outstanding setup item in the project's own decision
  log) is no longer a dependency of this feature at all — the app is
  built and deployed via the Databricks CLI (the mechanism used by every
  prior feature, 002-008), not an MCP tool-call integration.
- "The app generates SQL from natural language" means an LLM call (e.g.,
  Databricks `ai_query` against a foundation model endpoint, or an
  equivalent model call) performed by the app's own backend at request
  time — the exact model/mechanism is a planning-phase technical
  decision, not a spec-level business requirement.
- The number and content of the app's curated example questions are left
  as an implementation choice (planning phase) — the business
  requirement is "a small, reliable, reviewable set," not a specific
  count beyond SC-002's minimum of 3.
- Exact repository location for this feature's documentation artifacts
  (the app's example Q&A) is a planning-phase decision — the case's
  fixed repository structure doesn't reserve a folder for this the way
  it does for `analysis/` or `contracts/`, so plan.md will decide the
  concrete path.
- The app reads from `ifood_case.silver.yellow_taxi_trips` only — it
  introduces no new table, no new schema, and no change to the data
  itself.
- The app reuses the project's existing single 2X-Small SQL Warehouse
  (constitution's Free Edition constraint) rather than provisioning new
  compute — consistent with every prior feature's consumption path.
- Databricks Apps are assumed available and functional on this
  workspace's Free Edition tier; verifying this is a planning-phase
  concern (the same kind of early-validation risk the constitution
  already calls out for Free Edition constraints generally), not a
  spec-level ambiguity.

## Limitações conhecidas da POC

Esta é uma prova de conceito, não um produto pronto para produção.
Melhorias conhecidas e deliberadamente fora de escopo neste momento:

- **Contexto limitado a 1 turno**: perguntas de acompanhamento
  funcionam (ex.: "e a média mensal?" depois de uma pergunta sobre
  receita), mas só a última troca da conversa é usada como contexto —
  uma cadeia de 3+ perguntas relacionadas pode perder o fio da meada.
  Não há memória persistida de verdade (FR-008 continua valendo).
- **Modelo pequeno (8B parâmetros)**: `databricks-meta-llama-3-1-8b-instruct`
  é rápido e barato, mas menos confiável que um modelo maior para
  perguntas analíticas complexas ou ambíguas — perguntas fora do padrão
  das perguntas de exemplo têm mais chance de gerar SQL incorreto ou
  mal interpretado.
- **Validação de SQL é só uma lista de palavras proibidas**: `is_safe_select()`
  bloqueia por regex (INSERT/UPDATE/DELETE/DROP/...), não é um parser
  SQL de verdade — funciona para o caso de uso atual, mas não é uma
  camada de segurança robusta contra entradas adversariais. O SQL
  Warehouse e o Unity Catalog (permissão `SELECT` só na tabela silver)
  são a proteção real de fundo.
- **Sem controle de custo/limite de uso**: cada pergunta gera 2
  chamadas ao serving endpoint (gerar SQL + formatar resposta), sem
  limite de requisições por usuário/sessão — aceitável para uma POC de
  demonstração, não para uso real sem guardrails adicionais.
- **Latência variável**: se o SQL Warehouse do projeto estiver parado
  (auto-stop de 10 min de ociosidade, feature 002), a primeira pergunta
  de uma sessão pode demorar mais que os ~1 minuto de SC-001 enquanto
  o warehouse liga — perguntas seguintes já ficam rápidas.
- **Mensagens de erro genéricas por design**: qualquer falha (SQL
  inválido, timeout, permissão) retorna a mesma mensagem amigável ao
  usuário final ("não consegui responder") — bom para não vazar
  detalhes técnicos, mas significa que diagnosticar problemas exige
  acesso de desenvolvedor (ver `research.md` para os bugs reais já
  encontrados e corrigidos durante a implementação).
- **Sem autenticação própria**: a POC usa só a autenticação OAuth
  padrão dos Databricks Apps — não há controle de acesso adicional
  específico desta feature.
