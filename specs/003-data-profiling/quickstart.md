# Quickstart: Validate Data Profiling (EDA sobre Bronze)

Validates the four Independent Tests from spec.md end-to-end. User Story 1
(schema) should run first since Stories 2-4 assume its column mapping is
known; Stories 2-4 are otherwise independent of each other.

## Prerequisites

- Feature 002 complete: `ifood_case.bronze.yellow_taxi_raw` contains all 5
  monthly files, verified (see `specs/002-ambiente-landing-zone/`).
- Databricks CLI authenticated against the `DEFAULT` profile (same setup
  as feature 002's quickstart).

## Step 1 — Schema comparison across all columns (User Story 1 / FR-001, FR-009, FR-010)

Upload and run `src/profiling/schema_check.py` as a job on serverless
compute (same pattern as feature 002's `network_check.py`):

```
databricks workspace import /Workspace/Users/<you>/ifood_case/schema_check \
  --file src/profiling/schema_check.py --language PYTHON --format SOURCE --overwrite
databricks jobs submit --json '{"tasks":[{"task_key":"schema_check","notebook_task":{"notebook_path":"/Workspace/Users/<you>/ifood_case/schema_check"}}]}' --timeout 5m
databricks jobs get-run-output <run-id>
```

**Expected outcome**: JSON listing any `Schema Deviation` rows (data-model.md),
each tagged `critical` (required column) or `informational` (any other
column). Empty list means identical schema across all 5 months (SC-001).

## Step 2 — Volumetry, completeness, statistics, date-range, duplicates (User Stories 2-4)

Upload and run `src/profiling/profile_bronze.py` the same way. It reads
each of the 5 months independently (research.md §6) and computes, per
month: row count (FR-002), null rate for the 5 required columns (FR-003),
descriptive statistics for `total_amount`/`passenger_count` including the
negative-or-zero / null-or-zero counts (FR-004), out-of-range date count
(FR-005), and full-row duplicate count (FR-006).

**Expected outcome**: A JSON result with one entry per month, covering all
6 metric categories — no month missing any field (SC-002).

## Step 3 — Transcribe results into `findings.md`

Write `specs/003-data-profiling/findings.md` following the structure fixed
by `contracts/profiling-findings-schema.md`, using the JSON outputs from
Steps 1-2 as the source of truth (same convention as feature 002's
`DECISOES_PROJETO.md` §2 entries).

**Expected outcome**: `findings.md` has all 6 required sections, every
constitution-named data-quality risk (negative/zero `total_amount`,
null/zero `passenger_count`, out-of-range dates, duplicates) is quantified
(SC-003), and a reader could draft feature 005's quality rules from this
file alone (SC-004).

## Done when

- [ ] Step 1 output reviewed — schema deviations (if any) classified by
      severity
- [ ] Step 2 output reviewed — all 5 months have all 6 metric categories
- [ ] `findings.md` written matching `contracts/profiling-findings-schema.md`
- [ ] No persisted table was written or altered anywhere (FR-008) — this
      feature only read the bronze volume
