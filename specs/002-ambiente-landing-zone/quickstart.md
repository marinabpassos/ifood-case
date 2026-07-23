# Quickstart: Validate Ambiente & Landing Zone

Validates the three Independent Tests from spec.md end-to-end. Run in
order — each step's prerequisite is the previous step's outcome.

## Prerequisites

- Databricks Free Edition workspace URL + PAT configured (`~/.databrickscfg`
  `[DEFAULT]` profile).
- Databricks CLI (or the Databricks MCP/plugin) authenticated against that
  profile.
- Repo cloned locally, with the `data/` staging directory available
  (feature 001 scaffold) for the fallback path if it's needed.

## Step 1 — Network reachability (User Story 1 / FR-001, FR-002)

Run the reachability check (research.md §1) from inside the workspace
(serverless notebook cell or job task), targeting one known NYC TLC file.

```python
import urllib.request
url = "https://d37ci6vzurychx.cloudfront.net/trip-data/yellow_tripdata_2023-01.parquet"
try:
    with urllib.request.urlopen(url, timeout=15) as r:
        print("REACHABLE", r.status)
except Exception as e:
    print("BLOCKED", repr(e))
```

**Expected outcome**: One of `REACHABLE` or `BLOCKED` is printed and
recorded in `DECISOES_PROJETO.md` §2 (SC-001). If `BLOCKED`, proceed with
the local-download-and-upload fallback (research.md §2) for Step 3.

## Step 2 — Landing zone provisioned (User Story 2 / FR-003)

Create the catalog/schema/volume (research.md §3), then confirm it's
listable:

```sql
SHOW VOLUMES IN ifood_case.bronze;
```

or via CLI:

```
databricks volumes list ifood_case bronze
```

**Expected outcome**: `yellow_taxi_raw` appears in the listing — no ad hoc
setup needed to find it (SC-003). Cross-check the path against
`contracts/landing-zone-location.md`; update that file if the fallback
naming was used instead.

## Step 3 — Land and verify the 5 monthly files (User Story 3 / FR-004, FR-005, FR-006, FR-008)

For each month `2023-01` … `2023-05`, land the file via whichever path
Step 1 determined. Land all 5 first — the size-outlier check needs every
month's size to compute a median (research.md §6) — then verify as a
batch, retrying once per failing month:

```python
months = ["01", "02", "03", "04", "05"]
base = "/Volumes/ifood_case/bronze/yellow_taxi_raw"

def size_of(month):
    return dbutils.fs.ls(f"{base}/yellow_tripdata_2023-{month}.parquet")[0].size

def readable(month):
    path = f"{base}/yellow_tripdata_2023-{month}.parquet"
    spark.read.parquet(path).limit(1).count()  # raises on unreadable/corrupt file
    return True

def check(month, sizes):
    others = [s for m, s in sizes.items() if m != month]
    median = sorted(others)[len(others) // 2]
    size = sizes[month]
    return size > 0 and readable(month) and abs(size - median) <= 0.5 * median

sizes = {m: size_of(m) for m in months}
results = {}
for m in months:
    ok = check(m, sizes)
    if not ok:
        # retry once: re-land this month via land_files.py, then re-check
        sizes[m] = size_of(m)
        ok = check(m, sizes)
    results[m] = "verified" if ok else "incomplete"
    print(m, results[m], sizes[m], "bytes")
```

**Expected outcome**: All 5 months print `verified` (SC-002). A byte-size
or row-count spot-check against the original source confirms no
transformation occurred (SC-004). Any month still `incomplete` after the
one retry MUST be explicitly flagged in `DECISOES_PROJETO.md` §2 (FR-008)
— not silently skipped.

## Done when

- [ ] Step 1 outcome recorded in `DECISOES_PROJETO.md` §2
- [ ] Step 2 listing succeeds, `contracts/landing-zone-location.md` matches
      reality
- [ ] Step 3 prints `OK` for all 5 months, none empty or failing the
      readability check
