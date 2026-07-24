# Quickstart: Validate POC App Chat — Consumo & Diferencial

Validates the 2 Independent Tests from spec.md. Depends only on
`ifood_case.silver.yellow_taxi_trips` (features 004-006) already
existing.

## Prerequisites

- Feature 006 complete: `ifood_case.silver.yellow_taxi_trips` exists,
  15,339,417 rows (`specs/006-silver-data-quality/dq-run-log.md`).
- Databricks CLI authenticated against the `DEFAULT` profile.
- `databricks-meta-llama-3-1-8b-instruct` serving endpoint `READY`
  (confirmed working end-to-end during implementation; the originally
  planned `databricks-gpt-5-6-luna` has a workspace rate limit of 0 —
  research.md §2).
- The project's existing SQL Warehouse ID (feature 002) available for
  the `resources` wiring below.

## Step 1 — Deploy the app (User Story 1)

```bash
databricks workspace mkdirs /Workspace/Users/<you>/apps/poc-app-chat
databricks workspace import-dir src/app /Workspace/Users/<you>/apps/poc-app-chat --overwrite

databricks apps create --json '{
  "name": "poc-app-chat",
  "description": "Chat NL-to-SQL sobre yellow_taxi_trips (diferencial, sem Genie)",
  "resources": [
    {"name": "sql-warehouse", "sql_warehouse": {"id": "<WAREHOUSE_ID>", "permission": "CAN_USE"}},
    {"name": "serving-endpoint", "serving_endpoint": {"name": "databricks-meta-llama-3-1-8b-instruct", "permission": "CAN_QUERY"}}
  ]
}'

databricks apps get poc-app-chat -o json
# note the "service_principal_client_id" from the output above, then:
databricks experimental aitools tools query \
  "GRANT USE CATALOG ON CATALOG ifood_case TO \`<SERVICE_PRINCIPAL_CLIENT_ID>\`" \
  "GRANT USE SCHEMA ON SCHEMA ifood_case.silver TO \`<SERVICE_PRINCIPAL_CLIENT_ID>\`" \
  "GRANT SELECT ON TABLE ifood_case.silver.yellow_taxi_trips TO \`<SERVICE_PRINCIPAL_CLIENT_ID>\`" \
  -o json

databricks apps deploy poc-app-chat \
  --source-code-path /Workspace/Users/<you>/apps/poc-app-chat
```

**Expected outcome**: `app_status.state: RUNNING`; the returned `url`
opens the Gradio chat interface (confirms `resources` wiring — research.md
§4 — worked with the real warehouse/endpoint IDs, not the deliberately
invalid one used to validate the mechanism during planning). The
`resources` wiring alone only grants *compute* access to the SQL
Warehouse — the explicit `GRANT` statements above are what actually let
the app's service principal *read* the silver table (Unity Catalog data
access is a separate permission system; research.md §3b) — a step easy
to miss (this project's own implementation missed it initially and only
found it once a real user tried the app).

## Step 2 — Ask a question end-to-end (User Story 1 / FR-001, FR-002)

In the deployed app's chat UI, type a natural-language question in
Portuguese, e.g.: "qual foi a média de total_amount em março de 2023?"

**Expected outcome**: The app returns a correct, formatted Portuguese
answer within about a minute (SC-001), derived from an actually-executed
SQL query against `ifood_case.silver.yellow_taxi_trips` (cross-check the
number against a direct query, e.g. via
`databricks experimental aitools tools query`, for the same month).

## Step 3 — Capture the curated example set (User Story 2 / SC-002)

Ask each of the curated example questions (at least 3) against the real
running app. For each: record the question, the SQL the app generated
(visible via `databricks apps logs poc-app-chat`, `[APP]`
lines), the executed result, and the formatted answer returned in the
chat UI. Save all of them together in `src/app/examples.md`.

**Expected outcome**: `src/app/examples.md` exists with at least 3
distinct question → SQL → result → answer records, all captured from
real app runs, clearly labeled as this feature's differentiator content
(FR-006), distinct from features 002-008's required deliverables.

## Step 4 — Confirm no upstream modification (FR-007)

```bash
git status
git diff --stat
```

**Expected outcome**: Changes confined to `src/app/` and
`specs/009-poc-app-chat/` — nothing under `contracts/`,
nothing touching `ifood_case.silver.yellow_taxi_trips` or any earlier
feature's files.

## Done when

- [ ] Step 1 confirms the app is deployed and `RUNNING`, with SQL
      Warehouse and serving-endpoint resources wired via CLI JSON (no
      manual UI configuration step) (FR-001, research.md §4)
- [ ] Step 2 confirms a real question gets a correct, formatted
      Portuguese answer, cross-checked against a direct SQL query
      (SC-001, FR-002)
- [ ] Step 3 confirms `src/app/examples.md` has at least 3 real,
      captured example interactions, clearly labeled as differentiator
      content (SC-002, SC-003, FR-004, FR-005, FR-006)
- [ ] Step 4 confirms `git status`/`git diff` show changes only under
      `src/app/` and `specs/009-poc-app-chat/` (SC-005,
      FR-007)
