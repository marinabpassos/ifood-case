# Databricks notebook source
"""Idempotent Unity Catalog landing zone provisioning (spec FR-003).

Tries to create a dedicated `ifood_case` catalog first, falling back to
the workspace's default catalog with an `ifood_case_bronze` schema if
that fails (research.md, decision 3). In practice, `CREATE CATALOG IF NOT
EXISTS` via Spark SQL inside a notebook succeeds on Free Edition using its
Default Storage automatically -- only the standalone CLI `catalogs create`
call needed an explicit managed location (see DECISOES_PROJETO.md 2.2) --
so the fallback below is a safety net, not the path actually used.
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
        "COMMENT 'iFood case bronze/landing schema - raw Yellow Taxi files, unmodified from source'"
    )
    spark.sql(
        f"CREATE VOLUME IF NOT EXISTS {catalog}.{schema}.{VOLUME} "
        "COMMENT 'Landing zone for raw NYC TLC Yellow Taxi monthly parquet files (Jan-May 2023), unmodified from source'"
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
