# Databricks notebook source
"""Comparação de schema, coluna a coluna, entre os 5 arquivos mensais da bronze.

Implementa da spec 003: FR-001, FR-009, FR-010 -- toda coluna (não só as
5 obrigatórias) é comparada entre os 5 meses. Nomes de coluna são
comparados de forma case-insensitive; os tipos são agrupados em famílias
em vez de exigir correspondência exata (research.md, decisões 2 e 6). Um
desvio em coluna obrigatória é `critical`; qualquer outro desvio é
`informational`.
"""

import json

from pyspark.sql import types as T

CATALOG, SCHEMA, VOLUME = "ifood_case", "bronze", "yellow_taxi_raw"
BASE_PATH = f"/Volumes/{CATALOG}/{SCHEMA}/{VOLUME}"
MONTHS = ["01", "02", "03", "04", "05"]
REQUIRED_COLUMNS = {
    "vendorid",
    "passenger_count",
    "total_amount",
    "tpep_pickup_datetime",
    "tpep_dropoff_datetime",
}


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


def schema_by_month(spark) -> dict:
    result = {}
    for month in MONTHS:
        schema = spark.read.parquet(file_path(month)).schema
        result[month] = {field.name.lower(): type_family(field.dataType) for field in schema}
    return result


def compare_schemas(spark) -> dict:
    schemas = schema_by_month(spark)
    all_columns = sorted({col for cols in schemas.values() for col in cols})

    deviations = []
    for column in all_columns:
        family_by_month = {m: schemas[m].get(column, "missing") for m in MONTHS}
        families_present = {f for f in family_by_month.values() if f != "missing"}
        is_uniform = len(families_present) == 1 and all(f != "missing" for f in family_by_month.values())
        if not is_uniform:
            deviations.append({
                "column_name": column,
                "months_present": [m for m, f in family_by_month.items() if f != "missing"],
                "type_family_by_month": family_by_month,
                "is_required_column": column in REQUIRED_COLUMNS,
                "severity": "critical" if column in REQUIRED_COLUMNS else "informational",
            })

    return {
        "identical_schema": len(deviations) == 0,
        "deviations": deviations,
    }


if __name__ == "__main__":
    result = compare_schemas(spark)
    print(json.dumps(result))
    try:
        dbutils.notebook.exit(json.dumps(result))
    except NameError:
        pass
