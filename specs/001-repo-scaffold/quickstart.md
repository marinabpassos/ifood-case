# Quickstart: Validating the Repo Scaffold

Validation steps for this feature's success criteria (`spec.md` §Success
Criteria). No pipeline, cluster, or Databricks workspace is needed — this
is a local, structural check.

## Prerequisites

- Repository cloned locally
- Python 3.11+ available on PATH

## 1. Confirm required structure exists (SC-002)

```powershell
Get-ChildItem -Directory C:\Repos\ifood_case | Select-Object Name
```

Expected: `src`, `analysis`, `contracts`, `data`, `specs`, `.specify`
(plus `.claude`, `.git`) are all present. `README.md` and
`requirements.txt` are present at the root.

## 2. Confirm layout is self-explanatory (SC-001, SC-003)

Open `README.md` cold (no other context) and confirm, within a minute of
reading, that you can answer:
- What is this project?
- Where does pipeline code go? Where do contract files go? Where do
  analysis answers go?
- Which folders are required by the case brief, and which are this
  project's own addition — and why do the additions exist?

If any of those three questions isn't answerable from the README alone,
`SC-001`/`SC-003` fail.

## 3. Confirm dependencies install cleanly (SC-004)

```powershell
python -m venv .venv-quickstart-check
.\.venv-quickstart-check\Scripts\pip install -r requirements.txt
Remove-Item -Recurse -Force .venv-quickstart-check
```

Expected: `pyspark`, `delta-spark`, and `pyyaml` install without error
(the commented-out future dependencies in `requirements.txt` are not
installed and are not expected to be).

## 4. Confirm no premature content (FR-006)

```powershell
Get-ChildItem -Recurse C:\Repos\ifood_case\src, C:\Repos\ifood_case\analysis, C:\Repos\ifood_case\contracts
```

Expected: only placeholder files (e.g. `.gitkeep`) — no pipeline code,
notebooks, or contract YAML yet. Their arrival is tracked by later
features, not this one.
