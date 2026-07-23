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
  via the `_metadata.file_name` hidden column -- `input_file_name()` is
  not supported on Unity Catalog-governed compute, confirmed at runtime)
  and a single `_ingested_at` value for the whole batch (research.md,
  decision 4).
- FR-005 (US3): deduplicates on the original source columns only, via an
  explicit `subset`, so the two metadata columns can never mask a real
  duplicate (research.md, decision 4).
- FR-006 (US4): no business data-quality rule is applied anywhere here --
  only the technical dedup above.
- FR-007 (US3): reports rows read, rows written, and duplicates removed.
"""

import json
import time
from datetime import datetime

from pyspark.sql import functions as F
from pyspark.sql import types as T

CATALOG = "ifood_case"
LANDING_SCHEMA = "landing"
BRONZE_SCHEMA = "bronze"
VOLUME = "yellow_taxi_raw"
TABLE = "yellow_taxi_trips"
BASE_PATH = f"/Volumes/{CATALOG}/{LANDING_SCHEMA}/{VOLUME}"
MONTHS = ["01", "02", "03", "04", "05"]

# Feature 007: observability. Same schema/helpers duplicated in
# src/silver/build_silver.py (research.md decision 2 - self-contained
# scripts, no shared importable module).
RUN_LOG_TABLE = "ifood_case.silver._pipeline_run_log"
ALERT_THRESHOLD = 0.01

LOG_SCHEMA = T.StructType([
    T.StructField("pipeline_stage", T.StringType(), False),
    T.StructField("executed_at", T.TimestampType(), False),
    T.StructField("status", T.StringType(), False),
    T.StructField("rows_read", T.LongType(), True),
    T.StructField("rows_written", T.LongType(), True),
    T.StructField("schema_check_status", T.StringType(), True),
    T.StructField("duration_seconds", T.DoubleType(), True),
    T.StructField("metrics", T.StringType(), True),
    T.StructField("alerts", T.ArrayType(T.StringType()), True),
])


def check_alerts(named_counts: dict, rows_read: int) -> list:
    """FR-004: >1% of rows_read for any named count triggers a visible alert."""
    if not rows_read:
        return []
    alerts = []
    for name, count in named_counts.items():
        if count is None:
            continue
        pct = count / rows_read
        if pct > ALERT_THRESHOLD:
            alerts.append(f"{name}: {pct:.2%} > 1% threshold")
    return alerts


def write_run_log(spark, entry: dict) -> None:
    """FR-002/FR-003: append one row to _pipeline_run_log, success or failure."""
    row = {
        "pipeline_stage": entry["pipeline_stage"],
        "executed_at": entry["executed_at"],
        "status": entry["status"],
        "rows_read": entry.get("rows_read"),
        "rows_written": entry.get("rows_written"),
        "schema_check_status": entry.get("schema_check_status"),
        "duration_seconds": entry.get("duration_seconds"),
        "metrics": json.dumps(entry.get("metrics") or {}),
        "alerts": entry.get("alerts") or [],
    }
    spark.createDataFrame([row], schema=LOG_SCHEMA).write.format("delta").mode(
        "append"
    ).saveAsTable(RUN_LOG_TABLE)
    for alert in row["alerts"]:
        print(f"ALERT [{entry['pipeline_stage']}]: {alert}")

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
    # input_file_name() is not supported on Unity Catalog-governed compute
    # (UC_COMMAND_NOT_SUPPORTED.WITH_RECOMMENDATION, confirmed at runtime) --
    # the hidden _metadata.file_name column is the supported equivalent.
    df = df.withColumn("_source_file", F.col("_metadata.file_name"))
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


def dedup_and_write(spark, combined) -> dict:
    original_columns = [c for c in combined.columns if c not in ("_source_file", "_ingested_at")]
    rows_read = combined.count()
    deduped = combined.dropDuplicates(subset=original_columns)
    rows_written = deduped.count()

    # The old ifood_case.bronze schema (feature 002's landing-zone volume)
    # was dropped by rename_landing_schema.py -- this is the new bronze
    # schema, created fresh to hold the Delta table.
    spark.sql(
        f"CREATE SCHEMA IF NOT EXISTS {CATALOG}.{BRONZE_SCHEMA} "
        "COMMENT 'iFood case bronze schema - Delta table, schema-normalized ingestion from landing, no business rules'"
    )
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

    result = dedup_and_write(spark, combined)
    result["schema_validation_status"] = "pass"
    return result


if __name__ == "__main__":
    start_time = time.time()
    executed_at = datetime.utcnow()
    try:
        result = ingest_bronze(spark)
        metrics = {"duplicates_removed": result.get("duplicates_removed")}
        alerts = check_alerts(metrics, result.get("rows_read", 0))
        write_run_log(spark, {
            "pipeline_stage": "bronze",
            "executed_at": executed_at,
            "status": result.get("schema_validation_status", "failed"),
            "rows_read": result.get("rows_read"),
            "rows_written": result.get("rows_written"),
            "schema_check_status": result.get("schema_validation_status"),
            "duration_seconds": time.time() - start_time,
            "metrics": metrics,
            "alerts": alerts,
        })
    except Exception:
        # NOTE: dbutils.notebook.exit() below raises its own internal
        # control-flow exception on success -- it MUST stay outside this
        # try block, or every successful run also logs a spurious
        # "failed" row (found by actually running this, feature 007).
        write_run_log(spark, {
            "pipeline_stage": "bronze",
            "executed_at": executed_at,
            "status": "failed",
            "duration_seconds": time.time() - start_time,
        })
        raise

    print(json.dumps(result))
    try:
        dbutils.notebook.exit(json.dumps(result))
    except NameError:
        pass
