# Databricks notebook source
"""Profiling mês a mês dos arquivos bronze de Yellow Taxi.

Implementa da spec 003: FR-002 (volumetria) e FR-003 (completude). Lê
cada um dos 5 meses de forma independente (research.md SS6) -- nunca um
DataFrame unido -- para que cada métrica fique claramente atribuível ao
seu mês. Os nomes das colunas obrigatórias são literais (VendorID,
passenger_count, total_amount, tpep_pickup_datetime,
tpep_dropoff_datetime), já que estão confirmados com caixa consistente
nos 5 meses.
"""

import json

from pyspark.sql import functions as F

CATALOG, SCHEMA, VOLUME = "ifood_case", "bronze", "yellow_taxi_raw"
BASE_PATH = f"/Volumes/{CATALOG}/{SCHEMA}/{VOLUME}"
MONTHS = ["01", "02", "03", "04", "05"]
REQUIRED_COLUMNS = [
    "VendorID",
    "passenger_count",
    "total_amount",
    "tpep_pickup_datetime",
    "tpep_dropoff_datetime",
]


def file_path(month: str) -> str:
    return f"{BASE_PATH}/yellow_tripdata_2023-{month}.parquet"


def null_rates(df, row_count: int) -> dict:
    if row_count == 0:
        return {col: {"null_count": 0, "null_pct": 0.0} for col in REQUIRED_COLUMNS}
    agg = df.select([
        F.sum(F.col(col).isNull().cast("int")).alias(col) for col in REQUIRED_COLUMNS
    ]).collect()[0]
    return {
        col: {
            "null_count": agg[col],
            "null_pct": round(100.0 * agg[col] / row_count, 4),
        }
        for col in REQUIRED_COLUMNS
    }


def count_and_pct(df, condition, row_count: int) -> dict:
    if row_count == 0:
        return {"count": 0, "pct": 0.0}
    count = df.filter(condition).count()
    return {"count": count, "pct": round(100.0 * count / row_count, 4)}


PERCENTILES = [0.25, 0.5, 0.75, 0.95, 0.99]
APPROX_ERROR = 0.01


def descriptive_stats(df, column: str) -> dict:
    agg = df.agg(
        F.min(column).alias("min"),
        F.max(column).alias("max"),
        F.mean(column).alias("mean"),
    ).collect()[0]
    quantiles = df.approxQuantile(column, PERCENTILES, APPROX_ERROR)
    return {
        "min": agg["min"],
        "max": agg["max"],
        "mean": agg["mean"],
        "p25": quantiles[0],
        "p50": quantiles[1],
        "p75": quantiles[2],
        "p95": quantiles[3],
        "p99": quantiles[4],
    }


WINDOW_START = "2023-01-01 00:00:00"
WINDOW_END = "2023-06-01 00:00:00"  # limite superior exclusivo


def _in_window(column: str):
    return (F.col(column) >= WINDOW_START) & (F.col(column) < WINDOW_END)


def out_of_range_date_count(df, row_count: int) -> dict:
    in_range = _in_window("tpep_pickup_datetime") & _in_window("tpep_dropoff_datetime")
    return count_and_pct(df, ~in_range, row_count)


def duplicate_row_count(df, row_count: int) -> dict:
    distinct_count = df.dropDuplicates().count()
    count = row_count - distinct_count
    pct = round(100.0 * count / row_count, 4) if row_count else 0.0
    return {"count": count, "pct": pct}


def profile_month(spark, month: str) -> dict:
    df = spark.read.parquet(file_path(month))
    row_count = df.count()
    return {
        "row_count": row_count,
        "null_rates": null_rates(df, row_count),
        "passenger_count_null_or_zero": count_and_pct(
            df, F.col("passenger_count").isNull() | (F.col("passenger_count") == 0), row_count
        ),
        "stats_total_amount": descriptive_stats(df, "total_amount"),
        "stats_passenger_count": descriptive_stats(df, "passenger_count"),
        "total_amount_negative_or_zero": count_and_pct(
            df, F.col("total_amount") <= 0, row_count
        ),
        "out_of_range_dates": out_of_range_date_count(df, row_count),
        "duplicates": duplicate_row_count(df, row_count),
    }


def profile_all_months(spark) -> dict:
    return {month: profile_month(spark, month) for month in MONTHS}


if __name__ == "__main__":
    result = profile_all_months(spark)
    print(json.dumps(result))
    try:
        dbutils.notebook.exit(json.dumps(result))
    except NameError:
        pass
