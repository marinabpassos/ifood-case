# Databricks notebook source
"""Ingest the 5 landing-zone files into the bronze Delta table.

Implements spec 004's FR-002 through FR-008 (User Stories 2-4):

- FR-008 (US2): asserts every month's schema is consistent with the others
  except for the two columns feature 003 already found drifting
  (`passenger_count`, `ratecodeid`) -- this cross-month check is
  equivalent to comparing against feature 003's documented baseline,
  since that baseline *is* "identical across months except these two
  columns" (research.md, decision 6). Any other deviation fails the job.
- FR-003 (US2): casts the two drifted columns to one consistent type
  (research.md, decision 2).
- FR-002 (US2): unions all 5 months with `allowMissingColumns=False`
  (research.md, decision 3) -- no column is expected to be missing.
- FR-004 (US2): adds `_source_file` (captured per month, before the union,
  since `input_file_name()` only resolves correctly pre-shuffle) and a
  single `_ingested_at` value for the whole batch (research.md, decision
  4).
- FR-005 (US3): deduplicates on the original source columns only, via an
  explicit `subset`, so the two metadata columns can never mask a real
  duplicate (research.md, decision 4).
- FR-006 (US4): no business data-quality rule is applied anywhere here --
  only the technical dedup above.
- FR-007 (US3): reports rows read, rows written, and duplicates removed.
"""

import json

from pyspark.sql import functions as F
from pyspark.sql import types as T

CATALOG = "ifood_case"
LANDING_SCHEMA = "landing"
BRONZE_SCHEMA = "bronze"
VOLUME = "yellow_taxi_raw"
TABLE = "yellow_taxi_trips"
BASE_PATH = f"/Volumes/{CATALOG}/{LANDING_SCHEMA}/{VOLUME}"
MONTHS = ["01", "02", "03", "04", "05"]

# Columns feature 003's full-schema comparison found drifting in type
# family across months (float in 2023-01, integer in 2023-02..05) -- the
# only columns this schema check is allowed to see disagree between
# months.
KNOWN_DRIFTED_COLUMNS = {"passenger_count", "ratecodeid"}
DRIFT_TARGET_TYPE = T.IntegerType()


def file_path(month: str) -> str:
    return f"{BASE_PATH}/yellow_tripdata_2023-{month}.parquet"


def type_family(data_type) -> str:
    if isinstance(data_type, T.IntegralType):
        return "integer"
    if isinstance(data_type, T.FractionalType):
        return "floating"
    if isinstance(data_type, T.BooleanType):
        return "boolean"
    if isinstance(data_type, T.StringType):
        return "string"
    ntz = getattr(T, "TimestampNTZType", None)
    timestamp_types = (T.TimestampType, T.DateType) + ((ntz,) if ntz else ())
    if isinstance(data_type, timestamp_types):
        return "timestamp_or_date"
    return "other"


def schema_family_map(df) -> dict:
    return {field.name.lower(): type_family(field.dataType) for field in df.schema}


def assert_known_schema(schemas_by_month: dict) -> None:
    """FR-008: fail fast if any month's schema deviates outside the known drift list."""
    baseline_month = MONTHS[0]
    baseline = schemas_by_month[baseline_month]
    for month, columns in schemas_by_month.items():
        unexpected_columns = set(columns).symmetric_difference(baseline)
        if unexpected_columns:
            raise ValueError(
                f"Month {month} has a column set feature 003 never profiled: "
                f"{unexpected_columns}"
            )
        for column, family in columns.items():
            if column in KNOWN_DRIFTED_COLUMNS:
                continue
            if family != baseline[column]:
                raise ValueError(
                    f"Month {month}, column '{column}': type family '{family}' "
                    f"does not match baseline '{baseline[column]}' and isn't one "
                    "of the columns feature 003 found drifting"
                )


def read_month(spark, month: str):
    df = spark.read.parquet(file_path(month))
    df = df.withColumn("_source_file", F.input_file_name())
    for column in KNOWN_DRIFTED_COLUMNS:
        matches = [f.name for f in df.schema if f.name.lower() == column]
        if matches:
            df = df.withColumn(matches[0], F.col(matches[0]).cast(DRIFT_TARGET_TYPE))
    return df


def combine_months(spark):
    schemas_by_month = {
        month: schema_family_map(spark.read.parquet(file_path(month))) for month in MONTHS
    }
    assert_known_schema(schemas_by_month)

    dfs = [read_month(spark, month) for month in MONTHS]
    combined = dfs[0]
    for df in dfs[1:]:
        combined = combined.unionByName(df, allowMissingColumns=False)
    return combined.withColumn("_ingested_at", F.current_timestamp())


def dedup_and_write(combined) -> dict:
    original_columns = [c for c in combined.columns if c not in ("_source_file", "_ingested_at")]
    rows_read = combined.count()
    deduped = combined.dropDuplicates(subset=original_columns)
    rows_written = deduped.count()

    deduped.write.format("delta").mode("overwrite").saveAsTable(
        f"{CATALOG}.{BRONZE_SCHEMA}.{TABLE}"
    )

    return {
        "rows_read": rows_read,
        "rows_written": rows_written,
        "duplicates_removed": rows_read - rows_written,
    }


def ingest_bronze(spark) -> dict:
    try:
        combined = combine_months(spark)
    except ValueError as exc:
        return {"schema_validation_status": "failed", "error": str(exc)}

    result = dedup_and_write(combined)
    result["schema_validation_status"] = "pass"
    return result


if __name__ == "__main__":
    result = ingest_bronze(spark)
    print(json.dumps(result))
    try:
        dbutils.notebook.exit(json.dumps(result))
    except NameError:
        pass
