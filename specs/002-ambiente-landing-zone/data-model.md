# Phase 1 Data Model: Ambiente & Landing Zone

Both entities below are **metadata about the landing process**, not the
content of the trip-record files themselves — no column from inside the
parquet files is modeled here (that begins with feature 003, Data
Profiling). This keeps the entity list consistent with the spec's Key
Entities and the constitution's bronze-only scope for this feature.

## Landing Zone

The governed catalog/schema/volume location that holds raw files before
any table is modeled. One instance exists for the whole project (singleton,
created once by this feature, reused by every later feature).

| Field | Type | Notes |
|---|---|---|
| `catalog` | string | `ifood_case` (or the workspace default catalog, if catalog creation is restricted — see research.md §3) |
| `schema` | string | `bronze` (or `ifood_case_bronze` under the fallback path) |
| `volume` | string | `yellow_taxi_raw` |
| `full_path` | string (derived) | `/Volumes/{catalog}/{schema}/{volume}` |
| `provisioning_method` | enum: `sql_ddl` \| `cli` \| `sdk` | Whichever tool actually created it — recorded per FR-007 |
| `provisioned_at` | timestamp | When the volume was created |

**Validation rules**: `full_path` MUST resolve and be listable via standard
platform tooling before any file is landed (spec User Story 2, Independent
Test). Exactly one Landing Zone exists for this project — no ambiguity
between candidate locations (FR-003).

## Monthly Trip Record File

One raw file per month (January–May 2023), landed unmodified from source.
Grain: one row per month.

| Field | Type | Notes |
|---|---|---|
| `month` | string, `YYYY-MM` | Primary key/grain. One of `2023-01` … `2023-05` |
| `source_url` | string | Original NYC TLC CloudFront URL for that month |
| `file_name` | string | e.g. `yellow_tripdata_2023-01.parquet`, unchanged from source |
| `ingestion_path` | enum: `direct_download` \| `local_upload_fallback` | Which path (FR-001/FR-002) actually landed this file |
| `file_size_bytes` | integer | MUST be `> 0` (FR-005) |
| `landed_at` | timestamp | When the file arrived in the Landing Zone |
| `readability_check` | boolean | Result of the Spark smoke-read probe (research.md §4) |
| `size_outlier_check` | boolean | `true` if `file_size_bytes` is within 50% of the median size of the other four months (FR-005, research.md §6) — only computable once all 5 files have a landing attempt |
| `retry_attempted` | boolean | Whether the single automatic retry (FR-008) was used for this month |
| `verification_status` | enum: `pending` \| `verified` \| `failed` \| `incomplete` | `verified` requires `file_size_bytes > 0` AND `readability_check = true` AND `size_outlier_check = true`. `failed` = first attempt didn't pass. `incomplete` = still failing after the one automatic retry (terminal, flagged per FR-008) |

**State transitions**: `pending` → `failed` (first attempt didn't pass) →
retry once (`retry_attempted = true`) → (`verified` | `incomplete`).
`incomplete` is terminal and MUST be explicitly flagged, never silently
dropped (spec Edge Cases, Acceptance Scenario 3, FR-008). Note the
`size_outlier_check` can only run after all 5 months have at least one
landing attempt (research.md §6), so `verification_status` for every month
stays provisional until the full batch has landed once.

**Relationships**: Each Monthly Trip Record File belongs to exactly one
Landing Zone (1:5 for this project's fixed Jan–May 2023 scope). No other
relationships — content columns are opaque to this feature.

**Completion condition (SC-002)**: All 5 `month` rows exist with
`verification_status = verified`.
