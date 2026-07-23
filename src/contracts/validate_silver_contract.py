"""Validate structural completeness of contracts/nyc_taxi_silver.yaml.

Implements spec 005's FR-001 through FR-007 as a checkable assertion:
loads the YAML and confirms the 8 top-level keys, the 6-entry `columns`
list, and the 5-entry `quality_rules` list all match the structure fixed
by specs/005-silver-data-contract/contracts/silver-contract-structure.md.
Runs entirely locally -- no Databricks connection, no table read
(research.md decision 4). It does not validate that any real data
conforms to the contract; that is feature 006's job.
"""

import json
import re
from pathlib import Path

import yaml

CONTRACT_PATH = Path(__file__).resolve().parents[2] / "contracts" / "nyc_taxi_silver.yaml"

REQUIRED_TOP_LEVEL_KEYS = {
    "contract", "table", "grain", "columns", "quality_rules",
    "total_dropped_metric_note", "sla", "versioning",
}
EXPECTED_COLUMNS = {
    "VendorID", "passenger_count", "total_amount",
    "tpep_pickup_datetime", "tpep_dropoff_datetime", "_silver_processed_at",
}
EXPECTED_RULES = {
    "total_amount_negative_or_zero", "passenger_count_null_or_zero",
    "dropoff_before_pickup", "out_of_range_dates", "duplicates",
}
DROP_POLICY_RULES = EXPECTED_RULES - {"duplicates"}


def _check(condition: bool, message: str, problems: list) -> None:
    if not condition:
        problems.append(message)


def check_top_level(contract: dict, problems: list) -> None:
    missing_keys = REQUIRED_TOP_LEVEL_KEYS - set(contract.keys())
    _check(not missing_keys, f"missing top-level keys: {sorted(missing_keys)}", problems)


def check_contract_and_table(contract: dict, problems: list) -> None:
    c = contract.get("contract", {})
    _check(bool(c.get("name")), "contract.name is missing/empty", problems)
    _check(bool(c.get("version")), "contract.version is missing/empty", problems)

    t = contract.get("table", {})
    for field in ("catalog", "schema", "name", "owner"):
        _check(bool(t.get(field)), f"table.{field} is missing/empty", problems)


def check_grain(contract: dict, problems: list) -> None:
    g = contract.get("grain", {})
    _check(bool(g.get("statement")), "grain.statement is missing/empty", problems)
    _check(bool(g.get("uniqueness_note")), "grain.uniqueness_note is missing/empty", problems)


def check_columns(contract: dict, problems: list) -> None:
    columns = contract.get("columns", [])
    _check(len(columns) == 6, f"columns must have exactly 6 entries, found {len(columns)}", problems)

    names = {col.get("name") for col in columns}
    _check(
        names == EXPECTED_COLUMNS,
        f"columns name set mismatch: {names.symmetric_difference(EXPECTED_COLUMNS)}",
        problems,
    )

    for col in columns:
        name = col.get("name", "<unnamed>")
        for field in ("name", "type", "description"):
            _check(bool(col.get(field)), f"columns[{name}].{field} is missing/empty", problems)
        _check(isinstance(col.get("nullable"), bool), f"columns[{name}].nullable must be a boolean", problems)


def check_quality_rules(contract: dict, problems: list) -> None:
    rules = contract.get("quality_rules", [])
    _check(len(rules) == 5, f"quality_rules must have exactly 5 entries, found {len(rules)}", problems)

    ids = {rule.get("id") for rule in rules}
    _check(
        ids == EXPECTED_RULES,
        f"quality_rules id set mismatch: {ids.symmetric_difference(EXPECTED_RULES)}",
        problems,
    )

    for rule in rules:
        rule_id = rule.get("id", "<unknown>")
        _check(bool(rule.get("policy")), f"quality_rules[{rule_id}].policy is missing/empty", problems)
        _check(bool(rule.get("rationale")), f"quality_rules[{rule_id}].rationale is missing/empty", problems)
        if rule_id in DROP_POLICY_RULES:
            _check(bool(rule.get("condition")), f"quality_rules[{rule_id}].condition is missing/empty", problems)
            _check(
                rule.get("counting") == "independent",
                f"quality_rules[{rule_id}].counting must be 'independent'",
                problems,
            )

    _check(bool(contract.get("total_dropped_metric_note")), "total_dropped_metric_note is missing/empty", problems)


def check_sla(contract: dict, problems: list) -> None:
    sla = contract.get("sla", {})
    for field in ("frequency", "latency_target", "note"):
        _check(bool(sla.get(field)), f"sla.{field} is missing/empty", problems)


def check_versioning(contract: dict, problems: list) -> None:
    v = contract.get("versioning", {})
    version = v.get("current_version", "") or ""
    _check(bool(re.fullmatch(r"v\d+", version)), f"versioning.current_version '{version}' does not match pattern vN", problems)

    policy = v.get("breaking_change_policy", {})
    for field in ("major", "minor", "patch"):
        _check(bool(policy.get(field)), f"versioning.breaking_change_policy.{field} is missing/empty", problems)


def validate(contract: dict) -> dict:
    problems: list = []
    check_top_level(contract, problems)
    check_contract_and_table(contract, problems)
    check_grain(contract, problems)
    check_columns(contract, problems)
    check_quality_rules(contract, problems)
    check_sla(contract, problems)
    check_versioning(contract, problems)
    return {
        "structurally_valid": len(problems) == 0,
        "missing_or_invalid": problems,
    }


if __name__ == "__main__":
    with open(CONTRACT_PATH, encoding="utf-8") as f:
        loaded_contract = yaml.safe_load(f)
    result = validate(loaded_contract)
    print(json.dumps(result, indent=2))
