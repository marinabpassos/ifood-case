# Databricks notebook source
"""Land and verify the 5 monthly Yellow Taxi files in the landing zone.

Implements spec 002's FR-004 (land unmodified), FR-005 (non-empty,
readable, not a size outlier), FR-006 (no transformation), and FR-008
(retry once, then flag incomplete). Files are landed directly from the
NYC TLC source into the Unity Catalog Volume (direct-download path, per
DECISOES_PROJETO.md 2.1 -- outbound access was confirmed reachable, so
the local-download-and-upload fallback is not used).

The size-outlier check needs every month's size to compute a median, so
all 5 months are landed first, then verified as a batch (research.md,
decision 6).
"""

import json
import os
import statistics
import urllib.request

CATALOG, SCHEMA, VOLUME = "ifood_case", "bronze", "yellow_taxi_raw"
BASE_PATH = f"/Volumes/{CATALOG}/{SCHEMA}/{VOLUME}"
SOURCE_BASE_URL = "https://d37ci6vzurychx.cloudfront.net/trip-data"
MONTHS = ["01", "02", "03", "04", "05"]
OUTLIER_TOLERANCE = 0.5


def file_name(month: str) -> str:
    return f"yellow_tripdata_2023-{month}.parquet"


def dest_path(month: str) -> str:
    return f"{BASE_PATH}/{file_name(month)}"


def try_land(month: str) -> bool:
    url = f"{SOURCE_BASE_URL}/{file_name(month)}"
    try:
        urllib.request.urlretrieve(url, dest_path(month))
        return True
    except Exception:
        return False


def size_of(month: str) -> int:
    try:
        return os.path.getsize(dest_path(month))
    except OSError:
        return 0


def is_readable(month: str, spark) -> bool:
    try:
        spark.read.parquet(dest_path(month)).limit(1).count()
        return True
    except Exception:
        return False


def is_size_outlier(month: str, sizes: dict) -> bool:
    others = [s for m, s in sizes.items() if m != month]
    median = statistics.median(others)
    if median == 0:
        return True
    return abs(sizes[month] - median) > OUTLIER_TOLERANCE * median


def verify(month: str, landed: dict, sizes: dict, spark) -> bool:
    if not landed[month] or sizes[month] == 0:
        return False
    if is_size_outlier(month, sizes):
        return False
    return is_readable(month, spark)


def land_and_verify(spark) -> dict:
    landed = {m: try_land(m) for m in MONTHS}
    sizes = {m: size_of(m) for m in MONTHS}

    results = {}
    for month in MONTHS:
        ok = verify(month, landed, sizes, spark)
        if not ok:
            landed[month] = try_land(month)  # one automatic retry (FR-008)
            sizes[month] = size_of(month)
            ok = verify(month, landed, sizes, spark)
        results[month] = {
            "status": "verified" if ok else "incomplete",
            "size_bytes": sizes[month],
        }
    return results


if __name__ == "__main__":
    result = land_and_verify(spark)
    print(json.dumps(result))
    try:
        dbutils.notebook.exit(json.dumps(result))
    except NameError:
        pass
