# Databricks notebook source
"""Move the landing zone from ifood_case.bronze to ifood_case.landing.

Implements spec 004's FR-001 (User Story 1). Unity Catalog has no `ALTER
SCHEMA ... RENAME TO` on any tier (research.md, decision 1, confirmed via
Databricks documentation) -- not a Free Edition-specific restriction. This
"rename" is therefore a scripted create-new + copy + verify + drop-old:
create `ifood_case.landing` (schema + `yellow_taxi_raw` volume), copy the
5 files from `ifood_case.bronze.yellow_taxi_raw`, verify each file's size
matches feature 002's recorded sizes byte-for-byte, and only then drop the
old `ifood_case.bronze` schema/volume -- never before verification passes.
"""

import json

CATALOG = "ifood_case"
OLD_SCHEMA = "bronze"
NEW_SCHEMA = "landing"
VOLUME = "yellow_taxi_raw"
OLD_PATH = f"/Volumes/{CATALOG}/{OLD_SCHEMA}/{VOLUME}"
NEW_PATH = f"/Volumes/{CATALOG}/{NEW_SCHEMA}/{VOLUME}"
MONTHS = ["01", "02", "03", "04", "05"]

# Byte sizes landed and verified byte-for-byte against source in feature 002
# (DECISOES_PROJETO.md SS2.3) -- the values this move must still match.
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
        "COMMENT 'iFood case landing schema - raw Yellow Taxi files, unmodified from source'"
    )
    spark.sql(
        f"CREATE VOLUME IF NOT EXISTS {CATALOG}.{NEW_SCHEMA}.{VOLUME} "
        "COMMENT 'Landing zone for raw NYC TLC Yellow Taxi monthly parquet files (Jan-May 2023), unmodified from source'"
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
        drop_old_schema(spark)  # only drop the old location once every file is confirmed
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
