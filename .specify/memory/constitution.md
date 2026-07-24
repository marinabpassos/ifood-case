<!--
Sync Impact Report
===================
Version change: 1.1.2 → 1.1.3
Modified principles: none (wording-only correction, no principle redefined)
Modified sections:
  - Technology Stack & Environment Constraints — "Consumption" line now
    names feature 009's app by its final name, `poc-app-chat`, and
    flags it explicitly as a POC (not a finished product) -- the
    feature was renamed end-to-end (branch, spec directory, the
    deployed Databricks App itself, all docs) at the user's request on
    2026-07-24, after the app was already built and in use.
Added sections: none
Removed sections: none
Templates requiring updates:
  - .specify/templates/plan-template.md ✅ no change needed
  - .specify/templates/spec-template.md ✅ no change needed
  - .specify/templates/tasks-template.md ✅ no change needed
Follow-up TODOs: none
-->

# iFood Data Architect Case — Constitution

## Core Principles

### I. Data Quality Is a Gate, Not a Report (NON-NEGOTIABLE)

Data profiling on raw (bronze) data MUST be performed and documented before any
silver-layer modeling begins. Every data quality rule applied in the
bronze→silver transition (negative/zero `total_amount`, null/zero
`passenger_count`, `dropoff` before `pickup`, out-of-range dates, duplicates)
MUST be explicit, versioned in code, and MUST report the volume of records
affected or removed. Silver tables MUST NOT be written from data that has not
passed through this profiling and quality-rule step.

**Rationale**: The case is evaluated on "processo de análise exploratória"
and "justificativa das escolhas técnicas." Skipping straight to modeling
hides the reasoning the evaluator is meant to see, and real NYC TLC data is
known to contain these exact defects.

### II. Data Contracts First

Every table in the consumption (silver) layer MUST have a declarative,
versioned data contract (e.g. `contracts/nyc_taxi_silver.yaml`) written
*before* the table-writing code is implemented. The contract MUST define:
table name/schema/owner, explicit column-level schema (type, nullability,
business description), primary key/grain, the data quality rules from
Principle I, update frequency/SLA, and a contract version with a breaking
change policy. The pipeline MUST assert the contract (schema check) before
writing to the silver table — the contract is not documentation-only. Unity
Catalog column comments are the published view of the contract, not a
substitute for it.

**Rationale**: A contract written after the fact tends to describe whatever
the code happened to produce. Writing it first forces the schema and quality
rules to be a deliberate decision, and gives an automatic enforcement point.

### III. Observability Is Part of the Deliverable

Every pipeline execution MUST log, at minimum: rows read (bronze), rows
written (silver), rows dropped/flagged per data-quality rule, schema-mismatch
alerts against the contract (Principle II), execution duration, and
status (success/failure/partial). These MUST be persisted to a queryable
metadata table (e.g. `_pipeline_run_log`) in the consumption layer, not just
printed to notebook output. Native Unity Catalog lineage MUST be used for
landing→bronze→silver lineage rather than rebuilt manually. A defined
threshold (e.g. >1% of rows dropped by a single rule) MUST trigger a visible
alert (structured log or notebook banner) even for a one-time load.

**Rationale**: Observability is an explicit evaluation criterion, not a
"nice to have" for this case, and it doubles as evidence of the data-quality
decisions made under Principle I.

### IV. Fixed Stack, Justified Deviations

The technology stack is fixed for this project: PySpark for processing,
Delta Lake as table format, Unity Catalog for metadata/governance, and a
Databricks SQL Warehouse for consumption. Any deviation from this stack, or
any workaround required by a Databricks Free Edition constraint (serverless
-only compute, restricted outbound network domains, single 2X-Small
warehouse), MUST be documented with its rationale (e.g. in the README or a
decision doc) at the point the deviation is introduced. Silent workarounds
that aren't recorded are treated as constitution violations.

**Rationale**: "Justificativa das escolhas técnicas" is graded directly.
Free Edition's constraints (especially outbound network restrictions that
may block direct NYC TLC parquet downloads) are known risks that must be
validated early and their resolution documented, not discovered silently.

### V. Spec-Driven Development Workflow

Work proceeds through the SDD flow — Specify → Plan → Tasks → Implement —
with a human checkpoint between each phase; no phase auto-advances to the
next without explicit approval. Feature specs, plans, and tasks live as
versioned files in the repository (under the Spec Kit `specs/` structure),
not only inside ephemeral notebook cells or chat history. `/speckit-clarify`,
`/speckit-analyze`, and `/speckit-checklist` are optional gates to be used
when a spec or plan has open ambiguity, not skipped by default when
ambiguity exists.

**Rationale**: This case is explicitly also a demonstration of "boas
práticas de engenharia de dados agêntica" — the SDD process itself is part
of what's being evaluated, not just its output.

### VI. Lean Instructions, Simple Architecture

`CLAUDE.md` and any other always-loaded instruction file MUST be kept short;
rules that need to be reliably enforced belong in skills, hooks, or this
constitution, not in a growing prose file (adherence to instructions
degrades as files grow). The data architecture MUST stay to the minimum
medallion layering needed for this case — three physical layers, no more:
**landing** (raw files as landed, unmodified, in a Unity Catalog Volume),
**bronze** (a Delta table: 1:1 ingestion of the landing files with schema
normalization and technical deduplication only — no business-rule
filtering), and **silver** (a Delta table: business data-quality rules
applied, per Principle I, on top of bronze). No gold layer, star schema,
extra abstraction, or speculative generalization should be added unless a
specific requirement in the spec calls for it.

**Rationale**: Both over-long instruction files and speculative architecture
work against "qualidade e organização do código" by adding surface area that
isn't earning its place for a case of this scope.

## Technology Stack & Environment Constraints

- **Platform**: Databricks Free Edition. Known constraints to design around:
  serverless-only compute (no custom clusters), possibly restricted outbound
  network access (NYC TLC parquet files may need to be staged locally and
  uploaded via Databricks CLI/API instead of downloaded in-notebook), a
  single 2X-Small SQL Warehouse.
- **Processing**: PySpark (required by the case).
- **Table format**: Delta Lake.
- **Catalog/metadata**: Unity Catalog (native to Free Edition).
- **Consumption**: SQL via Databricks SQL Warehouse; a custom Databricks
  App with a chat-style natural-language interface (feature 009,
  `poc-app-chat` — a POC, not a finished product) is this
  project's NL-to-SQL consumption path — not Genie Space, which was
  evaluated and explicitly rejected (its own setup is UI-only, with no
  CLI/API path, unlike every other mechanism this project uses).
- **Scope of data**: NYC Yellow Taxi trip records, January–May 2023 only.
  Required columns for the silver layer: `VendorID`, `passenger_count`,
  `total_amount`, `tpep_pickup_datetime`, `tpep_dropoff_datetime`.

## Development Workflow & Repository Structure

- Repository layout is fixed by the case brief:
  `src/` (pipeline code), `analysis/` (answers to the analytical questions,
  as SQL or structured PySpark), `contracts/` (data contracts),
  `specs/` (versioned SDD specs), plus `README.md` and
  `requirements.txt` at the root.
- The two analytical questions this project must answer — average monthly
  `total_amount` across the fleet, and average `passenger_count` by hour of
  day for May — are delivered as versioned artifacts in `analysis/`, not
  ad hoc query results.
- The custom NL-to-SQL Databricks App (feature 009) — built and deployed
  via the Databricks CLI, not the Databricks MCP, and without a Genie
  Space anywhere in this project — is itself both this project's
  consumption interface and its differentiator content; it MUST be
  clearly documented as differentiator content in any written
  deliverable, distinct from the required deliverables of features
  002-008.

## Governance

This constitution supersedes ad hoc practice for this repository. Amendments
require: (1) editing this file, (2) a version bump per semantic versioning —
MAJOR for removing or redefining a principle, MINOR for adding a principle or
materially expanding guidance, PATCH for wording/clarification only — and
(3) a Sync Impact Report prepended as an HTML comment describing what changed
and which dependent templates were checked. Compliance is self-reviewed at
each SDD phase transition (before moving from Specify → Plan → Tasks →
Implement): the active spec/plan/tasks MUST be checked against the Core
Principles above before proceeding to the next phase. Complexity or
deviation from Principle IV or VI MUST be justified in writing at the point
it is introduced, not retroactively.

**Version**: 1.1.3 | **Ratified**: 2026-07-22 | **Last Amended**: 2026-07-24
