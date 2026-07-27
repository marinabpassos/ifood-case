# Databricks notebook source
"""Sonda de acessibilidade da fonte de dados NYC TLC (spec FR-001).

Uma requisição representativa contra o domínio CloudFront compartilhado
da NYC TLC vale por todos os 5 arquivos mensais (research.md, decisão 1)
-- a política de rede da Free Edition é aplicada no nível de domínio, não
por arquivo (spec FR-001, Clarifications 2026-07-22).
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
