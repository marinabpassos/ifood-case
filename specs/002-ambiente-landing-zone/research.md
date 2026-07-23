# Phase 0 Research: Ambiente & Landing Zone

**Input**: [spec.md](./spec.md) · Constitution `.specify/memory/constitution.md` · `DECISOES_PROJETO.md` §2-§3

No `[NEEDS CLARIFICATION]` markers remain in the spec. The items below are
planning-phase technical decisions the spec deliberately deferred (see
spec.md Assumptions: "the exact technology choice is a planning-phase
decision, not re-litigated here").

## 1. How to test outbound network reachability (FR-001)

- **Decision**: Run a minimal Python check from *inside* the Databricks
  workspace (serverless notebook cell or job task) using the stdlib
  `urllib.request.urlopen` against the known NYC TLC CloudFront URL for one
  file (e.g. `yellow_tripdata_2023-01.parquet`), with a short timeout, and
  record success/failure plus any HTTP/connection error.
- **Rationale**: The spec's Independent Test #1 requires the check to run
  "from within the target environment" — the workspace's egress policy is
  what's in question, not the developer's laptop. `urllib` is stdlib, so no
  dependency is added for a one-off check (Constitution Principle IV — no
  unjustified stack additions).
- **Alternatives considered**:
  - `requests` library — rejected: adds a dependency not otherwise needed
    by the fixed stack for a single GET/HEAD check.
  - Testing from the local machine — rejected: doesn't validate the actual
    constraint (workspace network policy, not local network).

## 2. Fallback ingestion path if direct download is blocked (FR-002)

- **Decision**: Download the 5 monthly files locally into the git-ignored
  `data/` staging directory (already scaffolded in feature 001), then
  upload each file to the Unity Catalog Volume via the Databricks CLI/SDK
  Files API (`databricks fs cp` or SDK `w.files.upload`).
- **Rationale**: `DECISOES_PROJETO.md` §2 already pre-commits to exactly
  this fallback ("Plano B: baixar localmente e subir via Databricks
  CLI/API"). Scripting the upload keeps it reproducible and documentable,
  satisfying Principle IV's requirement that any deviation be recorded, not
  worked around silently.
- **Alternatives considered**: Manual upload through the Databricks
  workspace UI — rejected: not scriptable/reproducible, leaves no
  documented trail (conflicts with Principle III/V's emphasis on
  documented, repeatable steps).

## 3. Landing zone naming and provisioning method (FR-003)

- **Decision**: catalog `ifood_case`, schema `bronze`, volume
  `yellow_taxi_raw` → `/Volumes/ifood_case/bronze/yellow_taxi_raw/`.
  Provision with `CREATE CATALOG/SCHEMA/VOLUME IF NOT EXISTS` (idempotent
  DDL), issued via whichever tool is available at implementation time
  (Databricks CLI, SDK, or the Databricks MCP/plugin) — the DDL statements
  are identical regardless of the invocation tool.
- **Fallback**: If catalog creation is restricted under Free Edition, reuse
  the workspace's existing default catalog and create schema
  `ifood_case_bronze` + volume `yellow_taxi_raw` under it instead. Whichever
  path is actually used MUST be documented (FR-007).
- **Rationale**: A single, unambiguous, discoverable path is required by
  FR-003/SC-003. `bronze` matches the medallion terminology already used
  throughout the constitution and `DECISOES_PROJETO.md`, so later features
  (003+) can reference it without renegotiating vocabulary.
- **Alternatives considered**: DBFS root — rejected, not governed by Unity
  Catalog; spec's Assumptions already fix the landing zone as a UC Volume.

## 4. Verifying a landed file is "non-empty and readable" (FR-005)

- **Decision**: After landing each month's file, check (a) file size > 0
  via CLI/`dbutils.fs.ls`, and (b) a minimal Spark smoke-read
  (`spark.read.parquet(path).limit(1).count()`) succeeds without error.
- **Rationale**: A size check alone cannot catch a truncated or corrupt
  parquet footer. The smoke-read is the cheapest real proof of readability
  without performing any cleaning/typing — it stays inside this feature's
  bronze-only scope (no columns are inspected or transformed, only that the
  file opens).
- **Alternatives considered**: File-size check only — rejected, doesn't
  prove readability (edge case in spec explicitly calls out corrupted
  files). Local `pyarrow` metadata read — rejected, adds a dependency the
  fixed stack doesn't otherwise need when Spark already covers this.

## 5. Where to document environment findings (FR-007)

- **Decision**: Append a dated subsection to `DECISOES_PROJETO.md` §2
  recording the network test outcome, which ingestion path was used, and
  any other Free Edition constraint hit — rather than creating a new file.
- **Rationale**: Constitution Principle VI (lean instructions, no
  speculative structure) — §2 is already the single source of prior/ongoing
  environment decisions; extending it keeps that single-source property
  instead of splitting environment notes across files.
- **Alternatives considered**: New `docs/environment-findings.md` —
  rejected as unnecessary file proliferation.

## 6. Size-outlier detection & retry sequencing (resolved via `/speckit-clarify`)

- **Decision**: Land all 5 files first, then run the size-outlier check
  (FR-005) as a single batch pass across all 5 — each file's size compared
  to the median of the *other four* — since the rule needs at least the
  other months' sizes to compute a median and can't be evaluated on a
  single file in isolation. Any file that fails to download, arrives
  corrupted, or fails the outlier check is retried once (re-download/
  re-upload that single month), then re-checked; if it still fails, it is
  flagged as incomplete in `DECISOES_PROJETO.md` §2 rather than silently
  accepted (FR-008).
- **Rationale**: Codifies spec Clarifications (2026-07-22, Q1/Q2) into an
  implementable sequence. Outlier detection is inherently a cross-file
  comparison, so the check must run after all 5 months have at least one
  landing attempt, not per-file as each one arrives.
- **Alternatives considered**: Checking against a hardcoded absolute
  expected size — rejected in clarification in favor of the relative/
  median approach, which needs no external reference data about NYC TLC's
  typical file sizes.
