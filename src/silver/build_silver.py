# Databricks notebook source
"""Build the silver Yellow Taxi table from bronze and the data contract.

Implements spec 006's FR-001 through FR-008:

- FR-001/FR-002: reads only `ifood_case.bronze.yellow_taxi_trips`, and
  asserts its 5 business columns are type-family compatible with
  `contracts/nyc_taxi_silver.yaml` before doing anything else --
  `_silver_processed_at` is excluded (it has no bronze equivalent; this
  feature adds it fresh).
- FR-003: loads the contract at runtime and evaluates each of the 4 drop
  rules independently against the full, unfiltered bronze input via the
  contract's own `condition` string (`F.expr(...)`) -- not a hand
  -written Python re-encoding of the same logic (research.md decisions
  1-2).
- FR-004: no duplicate-detection logic here -- the `duplicates` rule's
  `resolved_upstream` policy is a no-op at this layer.
- FR-005/FR-006: writes exactly the contract's 6 columns (5 business
  columns unchanged + a fresh `_silver_processed_at`), no bronze
  passthrough or bronze metadata column.
- FR-007: reports rows read/written, the 4 independent counts, and one
  non-overlapping total-dropped count.
- FR-008: never writes to `contracts/nyc_taxi_silver.yaml` -- read-only.
"""

import json
import time
from datetime import datetime, timezone

import yaml
from pyspark.sql import functions as F
from pyspark.sql import types as T

CATALOG = "ifood_case"
BRONZE_SCHEMA = "bronze"
BRONZE_TABLE = "yellow_taxi_trips"
SILVER_SCHEMA = "silver"

# Feature 007: observability. Same schema/helpers duplicated in
# src/bronze/ingest_bronze.py (research.md decision 2 - self-contained
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

# The contract lives in the repo (contracts/nyc_taxi_silver.yaml); this
# script runs in the Databricks workspace, so it reads the copy uploaded
# alongside it (see quickstart.md Step 1).
CONTRACT_WORKSPACE_PATH = "/Workspace/Users/marinabpassos@gmail.com/ifood_case/nyc_taxi_silver.yaml"

# Maps the contract's business-level type names to the same type-family
# vocabulary already used by schema_check.py/ingest_bronze.py.
CONTRACT_TYPE_TO_FAMILY = {
    "integer": "integer",
    "decimal": "floating",
    "timestamp": "timestamp_or_date",
}


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


def load_contract() -> dict:
    with open(CONTRACT_WORKSPACE_PATH, encoding="utf-8") as f:
        return yaml.safe_load(f)


def assert_schema_compatible(bronze_schema, contract: dict) -> None:
    """FR-002: the 5 business columns' type families must match the contract."""
    bronze_families = {field.name: type_family(field.dataType) for field in bronze_schema}
    for column in contract["columns"]:
        name = column["name"]
        if name == "_silver_processed_at":
            continue  # added fresh here -- no bronze equivalent (research.md SS3)
        expected_family = CONTRACT_TYPE_TO_FAMILY[column["type"]]
        actual_family = bronze_families.get(name)
        if actual_family != expected_family:
            raise ValueError(
                f"Column '{name}': bronze type family '{actual_family}' does not "
                f"match contract-declared '{column['type']}' (expected family "
                f"'{expected_family}')"
            )


def evaluate_rules(df, contract: dict):
    """FR-003: one boolean column per drop rule, against the full unfiltered input."""
    rule_columns = {}
    for rule in contract["quality_rules"]:
        if rule["policy"] != "drop":
            continue  # duplicates: resolved_upstream -- no condition to evaluate (FR-004)
        column_name = f"_fails_{rule['id']}"
        df = df.withColumn(column_name, F.expr(rule["condition"]))
        rule_columns[rule["id"]] = column_name
    return df, rule_columns


def build_silver(spark) -> dict:
    contract = load_contract()
    bronze = spark.table(f"{CATALOG}.{BRONZE_SCHEMA}.{BRONZE_TABLE}")

    assert_schema_compatible(bronze.schema, contract)

    df, rule_columns = evaluate_rules(bronze, contract)

    rows_read = df.count()
    per_rule_counts = {
        rule_id: df.filter(F.col(col_name)).count() for rule_id, col_name in rule_columns.items()
    }

    combined_mask = None
    for col_name in rule_columns.values():
        combined_mask = F.col(col_name) if combined_mask is None else combined_mask | F.col(col_name)

    total_dropped = df.filter(combined_mask).count()

    business_columns = [c["name"] for c in contract["columns"] if c["name"] != "_silver_processed_at"]
    clean = (
        df.filter(~combined_mask)
        .select(*business_columns)
        .withColumn("_silver_processed_at", F.current_timestamp())
    )

    rows_written = clean.count()

    spark.sql(f"CREATE SCHEMA IF NOT EXISTS {CATALOG}.{SILVER_SCHEMA}")
    clean.write.format("delta").mode("overwrite").saveAsTable(
        f"{CATALOG}.{SILVER_SCHEMA}.{contract['table']['name']}"
    )

    return {
        "rows_read": rows_read,
        "rows_written": rows_written,
        "total_amount_negative_or_zero_count": per_rule_counts["total_amount_negative_or_zero"],
        "passenger_count_null_or_zero_count": per_rule_counts["passenger_count_null_or_zero"],
        "dropoff_before_pickup_count": per_rule_counts["dropoff_before_pickup"],
        "out_of_range_dates_count": per_rule_counts["out_of_range_dates"],
        "total_dropped": total_dropped,
        "schema_assertion_status": "pass",
    }


if __name__ == "__main__":
    start_time = time.time()
    executed_at = datetime.now(timezone.utc)
    try:
        try:
            result = build_silver(spark)
        except ValueError as exc:
            result = {"schema_assertion_status": "failed", "error": str(exc)}

        metrics = {
            "total_amount_negative_or_zero_count": result.get("total_amount_negative_or_zero_count"),
            "passenger_count_null_or_zero_count": result.get("passenger_count_null_or_zero_count"),
            "dropoff_before_pickup_count": result.get("dropoff_before_pickup_count"),
            "out_of_range_dates_count": result.get("out_of_range_dates_count"),
            "total_dropped": result.get("total_dropped"),
        }
        rule_metrics = {k: v for k, v in metrics.items() if k != "total_dropped"}
        alerts = check_alerts(rule_metrics, result.get("rows_read", 0))
        write_run_log(spark, {
            "pipeline_stage": "silver",
            "executed_at": executed_at,
            "status": result.get("schema_assertion_status", "failed"),
            "rows_read": result.get("rows_read"),
            "rows_written": result.get("rows_written"),
            "schema_check_status": result.get("schema_assertion_status"),
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
            "pipeline_stage": "silver",
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
