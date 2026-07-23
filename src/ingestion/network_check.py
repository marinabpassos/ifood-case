# Databricks notebook source
"""Reachability probe for the NYC TLC data source (spec FR-001).

One representative request against the shared NYC TLC CloudFront domain
stands for all 5 monthly files (research.md, decision 1) -- Free
Edition's network policy is enforced at the domain level, not per file
(spec FR-001, Clarifications 2026-07-22).
"""

import json
import urllib.request

NYC_TLC_URL = "https://d37ci6vzurychx.cloudfront.net/trip-data/yellow_tripdata_2023-01.parquet"
TIMEOUT_SECONDS = 15


def check_reachability(url: str = NYC_TLC_URL, timeout: int = TIMEOUT_SECONDS) -> dict:
    try:
        with urllib.request.urlopen(url, timeout=timeout) as response:
            return {"reachable": True, "status": response.status, "url": url}
    except Exception as exc:
        return {"reachable": False, "error": repr(exc), "url": url}


if __name__ == "__main__":
    result = check_reachability()
    print(json.dumps(result))
    try:
        dbutils.notebook.exit(json.dumps(result))
    except NameError:
        pass
