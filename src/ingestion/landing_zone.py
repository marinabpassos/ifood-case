# Databricks notebook source
"""Provisionamento idempotente da landing zone no Unity Catalog (spec FR-003).

Tenta primeiro criar um catalog dedicado `ifood_case`, caindo para o
catalog padrão do workspace com um schema `ifood_case_bronze` se isso
falhar (research.md, decisão 3). Na prática, `CREATE CATALOG IF NOT
EXISTS` via Spark SQL dentro de um notebook funciona na Free Edition
usando o Default Storage automaticamente -- só a chamada avulsa da CLI
`catalogs create` precisou de uma managed location explícita (ver
DECISOES_PROJETO.md 2.2) -- então o fallback abaixo é uma rede de
segurança, não o caminho de fato usado.
"""

import json

CATALOG = "ifood_case"
FALLBACK_CATALOG = "workspace"
SCHEMA = "bronze"
FALLBACK_SCHEMA = "ifood_case_bronze"
VOLUME = "yellow_taxi_raw"


def provision_landing_zone(spark) -> dict:
    catalog, schema = CATALOG, SCHEMA
    try:
        spark.sql(f"CREATE CATALOG IF NOT EXISTS {catalog}")
    except Exception:
        catalog, schema = FALLBACK_CATALOG, FALLBACK_SCHEMA

    spark.sql(
        f"CREATE SCHEMA IF NOT EXISTS {catalog}.{schema} "
        "COMMENT 'Schema bronze/landing do case iFood - arquivos Yellow Taxi crus, sem modificação em relação à fonte'"
    )
    spark.sql(
        f"CREATE VOLUME IF NOT EXISTS {catalog}.{schema}.{VOLUME} "
        "COMMENT 'Landing zone dos arquivos parquet mensais crus de Yellow Taxi da NYC TLC (Jan-Mai 2023), sem modificação em relação à fonte'"
    )
    return {
        "catalog": catalog,
        "schema": schema,
        "volume": VOLUME,
        "path": f"/Volumes/{catalog}/{schema}/{VOLUME}",
    }


if __name__ == "__main__":
    result = provision_landing_zone(spark)
    print(json.dumps(result))
    try:
        dbutils.notebook.exit(json.dumps(result))
    except NameError:
        pass
