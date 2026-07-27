# Databricks notebook source
"""Move a landing zone de ifood_case.bronze para ifood_case.landing.

Implementa da spec 004: FR-001 (User Story 1). O Unity Catalog não tem
`ALTER SCHEMA ... RENAME TO` em nenhuma camada (research.md, decisão 1,
confirmado via documentação do Databricks) -- não é uma restrição
específica da Free Edition. Esse "rename" é, portanto, um create-new +
copy + verify + drop-old feito por script: criar `ifood_case.landing`
(schema + volume `yellow_taxi_raw`), copiar os 5 arquivos de
`ifood_case.bronze.yellow_taxi_raw`, verificar que o tamanho de cada
arquivo bate byte a byte com os tamanhos registrados na feature 002 e só
então apagar o schema/volume antigo `ifood_case.bronze` -- nunca antes da
verificação passar.
"""

import json

CATALOG = "ifood_case"
OLD_SCHEMA = "bronze"
NEW_SCHEMA = "landing"
VOLUME = "yellow_taxi_raw"
OLD_PATH = f"/Volumes/{CATALOG}/{OLD_SCHEMA}/{VOLUME}"
NEW_PATH = f"/Volumes/{CATALOG}/{NEW_SCHEMA}/{VOLUME}"
MONTHS = ["01", "02", "03", "04", "05"]

# Tamanhos em bytes aterrissados e verificados byte a byte contra a fonte
# na feature 002 (DECISOES_PROJETO.md SS2.3) -- os valores que este move
# ainda precisa bater.
EXPECTED_SIZES = {
    "01": 47_673_370,
    "02": 47_748_012,
    "03": 56_127_762,
    "04": 54_222_699,
    "05": 58_654_627,
}


def file_name(month: str) -> str:
    return f"yellow_tripdata_2023-{month}.parquet"


def create_landing_schema(spark) -> None:
    spark.sql(
        f"CREATE SCHEMA IF NOT EXISTS {CATALOG}.{NEW_SCHEMA} "
        "COMMENT 'Schema landing do case iFood - arquivos Yellow Taxi crus, sem modificação em relação à fonte'"
    )
    spark.sql(
        f"CREATE VOLUME IF NOT EXISTS {CATALOG}.{NEW_SCHEMA}.{VOLUME} "
        "COMMENT 'Landing zone dos arquivos parquet mensais crus de Yellow Taxi da NYC TLC (Jan-Mai 2023), sem modificação em relação à fonte'"
    )


def copy_files(dbutils) -> None:
    for month in MONTHS:
        dbutils.fs.cp(f"{OLD_PATH}/{file_name(month)}", f"{NEW_PATH}/{file_name(month)}")


def verify_move(dbutils) -> dict:
    results = {}
    for month in MONTHS:
        try:
            size = dbutils.fs.ls(f"{NEW_PATH}/{file_name(month)}")[0].size
        except Exception:
            size = 0
        results[month] = {
            "size_bytes": size,
            "matches_expected": size == EXPECTED_SIZES[month],
        }
    return results


def drop_old_schema(spark) -> None:
    spark.sql(f"DROP VOLUME IF EXISTS {CATALOG}.{OLD_SCHEMA}.{VOLUME}")
    spark.sql(f"DROP SCHEMA IF EXISTS {CATALOG}.{OLD_SCHEMA}")


def move_landing_zone(spark, dbutils) -> dict:
    create_landing_schema(spark)
    copy_files(dbutils)
    verification = verify_move(dbutils)
    all_verified = all(v["matches_expected"] for v in verification.values())
    if all_verified:
        drop_old_schema(spark)  # só apaga a localização antiga depois que todo arquivo é confirmado
    return {
        "verification": verification,
        "all_verified": all_verified,
        "old_schema_dropped": all_verified,
    }


if __name__ == "__main__":
    result = move_landing_zone(spark, dbutils)
    print(json.dumps(result))
    try:
        dbutils.notebook.exit(json.dumps(result))
    except NameError:
        pass
