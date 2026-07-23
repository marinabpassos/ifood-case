# Interface Contract: Landing Zone Location

This is **not** a data contract in the Constitution Principle II sense
(that governs the silver table, feature 004). This is the operational
interface this feature exposes to every later feature (003 Data Profiling
onward): a fixed, unambiguous path to read raw files from.

## Fixed location

```
Catalog: ifood_case            (fallback: workspace default catalog)
Schema:  bronze                (fallback: ifood_case_bronze)
Volume:  yellow_taxi_raw
Path:    /Volumes/{catalog}/{schema}/yellow_taxi_raw/
```

The actual values used (default vs. fallback) MUST be recorded in
`DECISOES_PROJETO.md` §2 per FR-007 and reflected here if they differ from
the default above — this file is the single source later features read
from, so it MUST stay accurate, not aspirational.

## File naming convention

One file per month, original filename preserved from source, no renaming:

```
/Volumes/{catalog}/{schema}/yellow_taxi_raw/yellow_tripdata_2023-01.parquet
/Volumes/{catalog}/{schema}/yellow_taxi_raw/yellow_tripdata_2023-02.parquet
/Volumes/{catalog}/{schema}/yellow_taxi_raw/yellow_tripdata_2023-03.parquet
/Volumes/{catalog}/{schema}/yellow_taxi_raw/yellow_tripdata_2023-04.parquet
/Volumes/{catalog}/{schema}/yellow_taxi_raw/yellow_tripdata_2023-05.parquet
```

## Guarantees this feature provides to consumers

1. The path above resolves and is listable via standard Unity Catalog
   tooling (`SHOW VOLUMES`, `databricks volumes list`, or MCP equivalent).
2. Exactly 5 files are present, one per month, each `file_size_bytes > 0`,
   passing a Spark readability smoke-read (research.md §4), and within 50%
   of the median size of the other four months (research.md §6) — any
   month that failed this bar was retried once before being flagged
   incomplete (FR-008), not silently dropped.
3. Files are byte-for-byte/row-count identical to the original source —
   no transformation, cleaning, or retyping has been applied (FR-006).

## Non-guarantees (explicitly out of scope here)

- Schema consistency across months is **not** verified or guaranteed by
  this feature — the raw files may have differing columns between months.
  That check belongs to feature 003 (Data Profiling).
- No data-quality rule (nulls, negative amounts, date ranges, duplicates)
  is applied or checked here.
