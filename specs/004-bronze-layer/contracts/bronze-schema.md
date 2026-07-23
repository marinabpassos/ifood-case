# Interface Contract: Bronze Table Schema

This fixes what `ifood_case.bronze.yellow_taxi_trips` MUST look like once
this feature's ingestion script runs. It is the structure this feature's
own `quickstart.md` checks against, and what feature 005 (data contract)
and feature 006 (silver) can rely on without re-deriving it from source
parquet. This is **not** the Principle-II governed data contract
(`contracts/nyc_taxi_silver.yaml`, feature 005) — that one governs the
consumption/silver layer; this one is an implementation-level fixture for
the bronze layer, the same role `profiling-findings-schema.md` played for
feature 003's `findings.md`.

## Columns this contract fixes explicitly

| Column | Type | Notes |
|---|---|---|
| `VendorID` | source type, unchanged | Required column (case brief) — no drift found in feature 003 |
| `passenger_count` | `IntegerType` | **Cast** — float in 2023-01 source, integer in 2023-02→05 (feature 003 finding); research.md §2 |
| `total_amount` | source type, unchanged | Required column — no drift found |
| `tpep_pickup_datetime` | source type, unchanged | Required column — no drift found |
| `tpep_dropoff_datetime` | source type, unchanged | Required column — no drift found |
| `ratecodeid` | `IntegerType` | **Cast** — same float/integer drift pattern as `passenger_count` in 2023-01 (feature 003 finding); not a required column, but resolved here since the drift is already known |
| `_source_file` | `StringType` | New — added by this feature (research.md §4) |
| `_ingested_at` | `TimestampType` | New — added by this feature (research.md §4) |

## Columns this contract does not hardcode

The remaining 13 source columns (e.g. `trip_distance`, `store_and_fwd_flag`,
`PULocationID`, `DOLocationID`, `payment_type`, `fare_amount`, `extra`,
`mta_tax`, `tip_amount`, `tolls_amount`, `improvement_surcharge`,
`congestion_surcharge`, `airport_fee`) are **not** individually retyped by
this feature — feature 003's full-schema comparison found no type-family
deviation in any of them across the 5 months. They pass through with
whatever type family feature 003 already confirmed as uniform.

This contract does not restate each of their exact Spark types here to
avoid a second, hand-maintained copy of feature 003's findings drifting
out of sync with it. Instead, the ingestion script's own FR-008
pre-transformation assertion (research.md §6) is the authoritative,
executable check: it compares each month's actual schema against feature
003's documented baseline (`../003-data-profiling/findings.md` §1) column
by column, and fails the job if any column outside the two known
deviations doesn't match. If that assertion passes, this contract's
guarantee — "every non-drifted column is uniform across months and
unchanged from source" — holds by construction.

## Guarantees this feature provides to consumers

1. `ifood_case.bronze.yellow_taxi_trips` has exactly one schema — no
   caller ever needs to cast or branch per source month.
2. `passenger_count` and `ratecodeid` are `IntegerType` in every row,
   regardless of which month they originated from.
3. `_source_file` and `_ingested_at` are present and non-null on every row.
4. No row is missing due to a business-quality rule — only exact full-row
   duplicates (research.md §4) can reduce the row count below feature
   003's total.

## Non-guarantees (explicitly out of scope here)

- No business data-quality flag, filter, or column is added — that's
  feature 006, against feature 005's contract.
- This contract does not enumerate the exact Spark type of every
  passthrough column (see above) — only that it is internally consistent
  across months, which FR-008's assertion enforces at run time.
