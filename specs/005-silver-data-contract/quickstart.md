# Quickstart: Validate Contrato de Dados da Silver

Validates the 3 Independent Tests from spec.md. Unlike every prior
feature, none of this requires Databricks access — everything here runs
locally against repository files.

## Prerequisites

- Feature 003 (profiling findings) and feature 004 (bronze layer,
  including the `ingestion-log.md` measurement of `dropoff` before
  `pickup`) complete.
- Python 3.11+ with `PyYAML` installed (`pip install -r requirements.txt`).

## Step 1 — Read the contract directly (User Story 1)

```
cat contracts/nyc_taxi_silver.yaml
```

**Expected outcome**: All 6 columns (`VendorID`, `passenger_count`,
`total_amount`, `tpep_pickup_datetime`, `tpep_dropoff_datetime`,
`_silver_processed_at`) are listed with type, nullability, and
description — no bronze passthrough column, no `_source_file`/
`_ingested_at` (SC-001).

## Step 2 — Read the data-quality policy section (User Story 2)

```
python -c "import yaml; c = yaml.safe_load(open('contracts/nyc_taxi_silver.yaml')); [print(r['id'], '->', r['policy']) for r in c['quality_rules']]"
```

**Expected outcome**: 5 rules listed — `total_amount_negative_or_zero`,
`passenger_count_null_or_zero`, `dropoff_before_pickup`,
`out_of_range_dates` all `drop`; `duplicates` `resolved_upstream`
(SC-002).

## Step 3 — Run the structural validator (User Story 1-3, all together)

```
python src/contracts/validate_silver_contract.py
```

**Expected outcome**: Prints a JSON result with
`"structurally_valid": true` and an empty `missing_or_invalid` list — no
Databricks connection attempted, runs in well under a second.

## Step 4 — Confirm versioning answers a hypothetical change (User Story 3)

```
python -c "import yaml; c = yaml.safe_load(open('contracts/nyc_taxi_silver.yaml')); print(c['versioning'])"
```

**Expected outcome**: `current_version: v1` and a `breaking_change_policy`
with `major`/`minor`/`patch` keys specific enough to classify, for
example, "remove `VendorID`" (major) vs "add a new optional column"
(minor) without asking the contract's author (SC-003).

## Done when

- [ ] Step 1 confirms all 6 columns, no bronze passthrough/metadata
      columns
- [ ] Step 2 confirms all 5 quality rules with an explicit policy
- [ ] Step 3's validator reports `structurally_valid: true`
- [ ] Step 4 confirms the versioning/breaking-change policy is concrete
- [ ] No table was read, written, or altered anywhere in this feature
      (FR-008) — everything above is local file/YAML inspection
