# Observability Findings: Pipeline Run Log & Lineage

Structure per `data-model.md` ("Pipeline Run Log Entry"). Produced by the
extended `src/bronze/ingest_bronze.py` and `src/silver/build_silver.py`,
re-run via `databricks jobs submit` on serverless compute, 2026-07-23.

## Bug found and fixed during implementation

The first re-run of `ingest_bronze.py` (with the new logging code)
**succeeded** at the Databricks job level but produced **two** log rows
— one `"pass"` and one spurious `"failed"` with empty metrics. Root
cause: `dbutils.notebook.exit()` raises its own internal control-flow
exception to terminate the notebook on success. The new broad
`except Exception:` block (meant to catch genuinely unanticipated
crashes, research.md §3) was wrapped **around** that call too, so it
caught this internal exception and logged a false failure before
re-raising it (harmlessly, since Databricks itself still recognized the
exit signal — hence the job showing SUCCESS despite the spurious row).

**Fix**: moved `dbutils.notebook.exit(...)` (and its existing
`except NameError` guard for local/non-Databricks execution) *outside*
the broad `try/except Exception` block in both scripts. The spurious row
was deleted (`DELETE FROM ifood_case.silver._pipeline_run_log WHERE
status = 'failed'`) before re-running bronze a second time to confirm
the fix — that second, corrected run is what appears in the results
below alongside the original first run (both `"pass"`, demonstrating the
log's append/history-accumulation behavior, spec US1 Acceptance
Scenario 2).

## Pipeline Run Log contents (after fix)

| pipeline_stage | status | rows_read | rows_written | schema_check_status | duration_seconds | metrics | alerts |
|---|---|---|---|---|---|---|---|
| bronze | pass | 16,186,386 | 16,186,386 | pass | 90.5 | `{"duplicates_removed": 0}` | `[]` |
| bronze | pass | 16,186,386 | 16,186,386 | pass | 20.7 | `{"duplicates_removed": 0}` | `[]` |
| silver | pass | 16,186,386 | 15,339,417 | pass | 14.0 | `{"total_amount_negative_or_zero_count": 144146, "passenger_count_null_or_zero_count": 702146, "dropoff_before_pickup_count": 795, "out_of_range_dates_count": 1077, "total_dropped": 846969}` | `["passenger_count_null_or_zero_count: 4.34% > 1% threshold"]` |

## SC-001 verification: queryable, accumulating log

Two `bronze` rows exist from two separate re-runs during this feature's
implementation (the first pre-fix, the second post-fix) — confirming
the log **accumulates** history rather than overwriting, unlike every
other table in this project (spec US1 Acceptance Scenario 2).

## SC-004 verification: re-run reproduces features 004/006 exactly

| Metric | This re-run | Original (`ingestion-log.md` / `dq-run-log.md`) | Match |
|---|---|---|---|
| bronze rows_read/written | 16,186,386 / 16,186,386 | 16,186,386 / 16,186,386 | Exact |
| bronze duplicates_removed | 0 | 0 | Exact |
| silver rows_read/written | 16,186,386 / 15,339,417 | 16,186,386 / 15,339,417 | Exact |
| silver total_amount_negative_or_zero | 144,146 | 144,146 | Exact |
| silver passenger_count_null_or_zero | 702,146 | 702,146 | Exact |
| silver dropoff_before_pickup | 795 | 795 | Exact |
| silver out_of_range_dates | 1,077 | 1,077 | Exact |
| silver total_dropped | 846,969 | 846,969 | Exact |

Every number matches exactly — proving both pipelines are idempotent and
that this feature's logging changes had zero effect on the actual data
or rules (FR-007).

## SC-002 verification: real alert fired

The silver run's `alerts` field contains exactly one entry —
`passenger_count_null_or_zero_count: 4.34% > 1% threshold` — matching
the rate already known from feature 006. The other 3 silver rules
(0.89%, 0.005%, 0.007%, all under 1%) and bronze's `duplicates_removed`
(0%) correctly produced no alert.

## SC-003 verification: lineage via two native mechanisms

**Table-to-table half (bronze → silver)** — confirmed programmatically
via `system.access.table_lineage`, re-queried after this feature's
fresh re-runs:

```
source_table_full_name              | target_table_full_name
ifood_case.bronze.yellow_taxi_trips | ifood_case.silver.yellow_taxi_trips
```

**Volume-to-table half (landing → bronze)** — per research.md §5,
`system.access.table_lineage` only tracks table-to-table edges (confirmed:
bronze's own row in that table has an empty `source_table_full_name`,
since its source is a Volume, not a table). This half of the chain is
documented by Databricks as visible in Catalog Explorer's lineage graph
UI instead. **This session has no browser/UI access**, so this half was
not personally clicked through — it is documented here as the correct
verification path (per Databricks' own lineage feature documentation and
the empirically-confirmed table-only scope of the system table above),
not as a visually-confirmed screenshot. A follow-up session with UI
access should do this final click-through if a visual record is needed
for the case presentation.

## Files modified

- `src/bronze/ingest_bronze.py`: added `LOG_SCHEMA`, `check_alerts()`,
  `write_run_log()`, and a broad failure-path catch in `__main__`
  (research.md §1-3).
- `src/silver/build_silver.py`: same additions, applied to silver's
  4 named rule counts.

No change to either script's actual ingestion/cleaning logic, target
schema, or the content of `ifood_case.bronze.yellow_taxi_trips` /
`ifood_case.silver.yellow_taxi_trips` (confirmed above, SC-004).
