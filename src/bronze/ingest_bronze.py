# Databricks notebook source
"""Ingere os 5 arquivos da landing zone na tabela Delta bronze.

Implementa da spec 004: FR-002 a FR-008 (User Stories 2-4):

- FR-008 (US2): garante que o schema de cada mês é consistente com os
  demais, exceto pelas duas colunas que a feature 003 já achou com drift
  (`passenger_count`, `ratecodeid`) -- essa checagem cruzada entre meses
  equivale a comparar contra o baseline documentado da feature 003, já
  que esse baseline *é* "idêntico entre os meses, exceto essas duas
  colunas" (research.md, decisão 6). Qualquer outro desvio faz o job
  falhar.
- FR-003 (US2): faz cast das duas colunas com drift para um tipo
  consistente (research.md, decisão 2).
- FR-002 (US2): une os 5 meses com `allowMissingColumns=False`
  (research.md, decisão 3) -- não se espera que falte nenhuma coluna.
- FR-004 (US2): adiciona `_source_file` (capturado por mês, antes do
  union, via a coluna oculta `_metadata.file_name` -- `input_file_name()`
  não é suportado em compute governado por Unity Catalog, confirmado em
  runtime) e um único valor de `_ingested_at` para o lote inteiro
  (research.md, decisão 4).
- FR-005 (US3): deduplica apenas nas colunas originais da fonte, via um
  `subset` explícito, para que as duas colunas de metadados nunca possam
  mascarar uma duplicata real (research.md, decisão 4).
- FR-006 (US4): nenhuma regra de qualidade de negócio é aplicada aqui --
  só o dedup técnico acima.
- FR-007 (US3): reporta linhas lidas, linhas escritas e duplicatas
  removidas.
"""

import json
import time
from datetime import datetime, timezone

from pyspark.sql import functions as F
from pyspark.sql import types as T

CATALOG = "ifood_case"
LANDING_SCHEMA = "landing"
BRONZE_SCHEMA = "bronze"
VOLUME = "yellow_taxi_raw"
TABLE = "yellow_taxi_trips"
BASE_PATH = f"/Volumes/{CATALOG}/{LANDING_SCHEMA}/{VOLUME}"
MONTHS = ["01", "02", "03", "04", "05"]

# Feature 007: observability. Mesmo schema/helpers duplicados em
# src/silver/build_silver.py (research.md decisão 2 - scripts
# autocontidos, sem módulo compartilhado importável).
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
    """FR-004: >1% de rows_read em qualquer contagem nomeada dispara um alerta visível."""
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
    """FR-002/FR-003: adiciona uma linha em _pipeline_run_log, com sucesso ou falha."""
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

# Colunas que a comparação de schema completa da feature 003 achou com
# drift de família de tipo entre os meses (float em 2023-01, integer em
# 2023-02..05) -- as únicas colunas que esta checagem de schema pode ver
# divergir entre os meses.
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
    """FR-008: falha rápido se o schema de algum mês desviar além da lista de drift conhecida."""
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
    # input_file_name() não é suportado em compute governado por Unity Catalog
    # (UC_COMMAND_NOT_SUPPORTED.WITH_RECOMMENDATION, confirmado em runtime) --
    # a coluna oculta _metadata.file_name é o equivalente suportado.
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

    # O schema antigo ifood_case.bronze (o volume de landing zone da
    # feature 002) foi apagado por rename_landing_schema.py -- este é o
    # novo schema bronze, criado do zero para conter a tabela Delta.
    spark.sql(
        f"CREATE SCHEMA IF NOT EXISTS {CATALOG}.{BRONZE_SCHEMA} "
        "COMMENT 'Schema bronze do case iFood - tabela Delta, ingestão a partir da landing com schema normalizado, sem regras de negócio'"
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
    executed_at = datetime.now(timezone.utc)
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
        # NOTA: dbutils.notebook.exit() abaixo levanta sua própria exceção
        # interna de controle de fluxo em caso de sucesso -- ele PRECISA
        # ficar fora deste bloco try, ou toda execução bem-sucedida
        # também registra uma linha "failed" espúria (descoberto rodando
        # isto de verdade, feature 007).
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
