# Feature Specification: Data Profiling (EDA sobre Bronze)

**Feature Branch**: `003-data-profiling`

**Created**: 2026-07-22

**Status**: Draft

**Input**: User description: "feature 003 - Data Profiling (EDA sobre Bronze)"

## Clarifications

### Session 2026-07-22

- Q: The out-of-range date check (FR-005) could mean "outside the whole Jan-May 2023 window" or "outside this specific file's own month" (catching adjacent-month leakage even within the window). Which scope applies? → A: Whole-window only — flag records outside Jan 1-May 31, 2023 overall. Per-file adjacent-month leakage (e.g. an April record inside the March file) is explicitly out of scope for this metric.
- Q: How strict should the schema comparison (FR-001) be — exact name+type match, name-only, or something in between? → A: Column name matched case-insensitively, and data type matched by type family (e.g. int32/int64 both count as "integer"); a name that's genuinely different (not just cased differently) or a type-family mismatch (e.g. string vs numeric) is flagged as a deviation.

### Session 2026-07-23

- Q: Should schema comparison (FR-001) cover only the 5 required columns, or every column in the files? → A: Every column, full schema validation — but with a severity split: deviations in the 5 required columns are critical findings; deviations in any other column are still flagged, but as a lower-severity finding deferred to the modeling phase (feature 004) to decide on.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Confirm schema consistency across months before assuming uniformity (Priority: P1)

As the case author, I need to know whether the 5 monthly raw files share the
same column names and types, so I don't silently assume a uniform schema
that later modeling and contract work would then be built on incorrectly.

**Why this priority**: NYC TLC source files are known to vary schema
between months. Discovering this after contract/quality-rule work has
already assumed a fixed schema would invalidate that work — this is the
single biggest unknown blocking every later profiling and modeling step,
the same role network reachability played in feature 002.

**Independent Test**: Compare the schema (column names and types) of all 5
landed files against each other, across every column present — not just
the 5 required ones — and produce a documented list of any differences
found, independent of any other profiling metric.

**Acceptance Scenarios**:

1. **Given** the 5 monthly files are landed in the bronze volume, **When**
   their full schemas (every column) are compared, **Then** a documented
   result states either "identical schema across all 5 months" or lists
   exactly which columns differ, in which months, and at which severity.
2. **Given** a required column (`VendorID`, `passenger_count`,
   `total_amount`, `tpep_pickup_datetime`, `tpep_dropoff_datetime`) is
   missing, genuinely renamed, or has a type-family mismatch in some month
   (casing differences alone don't count), **When** the schema comparison
   runs, **Then** that deviation is explicitly flagged as **critical**, not
   silently defaulted or ignored.
3. **Given** a non-required column differs across months (missing, added,
   renamed, or a type-family mismatch), **When** the schema comparison
   runs, **Then** that deviation is flagged at **informational** severity
   and deferred for a modeling-phase decision (feature 004), rather than
   being treated as a blocking issue or silently dropped from the report.

---

### User Story 2 - Volumetry per month is documented (Priority: P2)

As the case author, I need the row count of each monthly file recorded, so
I have a baseline scale reference for every later profiling and quality
metric (e.g. "X% of rows" is meaningless without a documented denominator).

**Why this priority**: Every other profiling metric in this feature is
expressed as a rate or count against total rows — volumetry has to exist
first for those numbers to be interpretable, but it doesn't depend on the
schema comparison's outcome (a row count is schema-oblivious).

**Independent Test**: Read each of the 5 landed files independently and
record its row count, without requiring any other profiling step to have
run first.

**Acceptance Scenarios**:

1. **Given** the 5 monthly files are landed, **When** each is counted,
   **Then** a documented table lists row count per month.
2. **Given** a month's row count is unexpectedly low or high relative to
   its file size (from feature 002's landing record), **When** volumetry
   completes, **Then** the discrepancy is flagged for follow-up rather than
   silently accepted.

---

### User Story 3 - Completeness (null-rate) profiling of the required columns (Priority: P3)

As the case author, I need to know the null/missing-value rate for each of
the 5 required columns, per month, so the data-quality rules designed in
later features are based on measured reality, not assumption.

**Why this priority**: This is one of the two concrete data-defect
categories the constitution requires quantified before any quality rule is
written (Principle I) — it depends on User Story 1's column mapping being
known, so it's sequenced after schema confirmation.

**Independent Test**: For each of the 5 required columns, compute the
percentage of null/missing values per month and confirm the result is
documented, independent of the descriptive-statistics story.

**Acceptance Scenarios**:

1. **Given** the 5 files and their confirmed column mapping, **When** null
   rates are computed, **Then** a documented table shows the null rate for
   each of the 5 required columns, for each of the 5 months.
2. **Given** `passenger_count` has null or zero values (a known defect in
   this dataset), **When** the profiling runs, **Then** the exact count and
   percentage of affected rows is reported, not just a yes/no flag.

---

### User Story 4 - Descriptive statistics and outliers for `total_amount` and `passenger_count` (Priority: P4)

As the case author, I need descriptive statistics (min, max, mean, and key
percentiles) for `total_amount` and `passenger_count`, per month, so
outliers and invalid values (e.g. negative amounts) are identified before
they reach the two analytical questions this case must answer.

**Why this priority**: This directly feeds both the data-quality rules
(negative/zero `total_amount`) and the case's two analytical questions
(average `total_amount` per month, average `passenger_count` by hour in
May) — but it's the most granular metric and benefits from schema and
volumetry already being confirmed, so it's sequenced last.

**Independent Test**: For each month, compute min/max/mean/percentiles for
`total_amount` and `passenger_count` and confirm the result is documented,
independent of the null-rate story.

**Acceptance Scenarios**:

1. **Given** the 5 files, **When** descriptive statistics are computed,
   **Then** a documented table shows min/max/mean/percentiles for both
   columns, per month.
2. **Given** `total_amount` contains negative or zero values (a known
   defect in this dataset), **When** statistics are computed, **Then** the
   count of such records is explicitly reported alongside the overall
   distribution, not averaged away silently.

---

### Edge Cases

- If a required column is missing or renamed in a given month's file, that
  month's profiling for the other stories MUST still proceed for the
  columns that do exist, with the missing column explicitly flagged rather
  than causing the entire month's profiling to fail silently.
- If a column that should be numeric or datetime contains values that
  can't be parsed as such, those unparseable values MUST be counted and
  reported as a distinct finding, not dropped without a record.
- If `tpep_pickup_datetime` or `tpep_dropoff_datetime` falls entirely
  outside the January-May 2023 window, the count of such out-of-range
  records MUST be reported per month, not silently included in in-range
  statistics. Records that "leak" between adjacent months but still fall
  inside the overall window (e.g. an April-dated record inside the March
  file) are not flagged by this check — see Assumptions.
- If two files report identical row-for-row content (full-row duplicates),
  the count of duplicate rows MUST be reported — this feature documents the
  volume, it does not decide whether to drop them (that policy decision
  belongs to features 004/005).

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The schema (column names and types) of **every column** in
  all 5 monthly files MUST be compared against each other — not only the 5
  required columns — and any differences MUST be documented before any
  later story assumes a uniform schema. Column names are compared
  case-insensitively; data types are compared by type family (e.g. all
  integer widths count as one family) rather than requiring an exact type
  match, per the 2026-07-22 clarification.
- **FR-002**: The row count of each of the 5 monthly files MUST be
  computed and documented.
- **FR-003**: The null/missing-value rate for each of the 5 required
  columns (`VendorID`, `passenger_count`, `total_amount`,
  `tpep_pickup_datetime`, `tpep_dropoff_datetime`) MUST be computed and
  documented, per month.
- **FR-004**: Descriptive statistics (minimum, maximum, mean, and key
  percentiles) for `total_amount` and `passenger_count` MUST be computed
  and documented, per month.
- **FR-005**: Records whose `tpep_pickup_datetime` or
  `tpep_dropoff_datetime` fall entirely outside the January-May 2023
  window MUST be counted and reported per month. Adjacent-month leakage
  within the window (e.g. an April record inside the March file) is a
  distinct, out-of-scope concern per the 2026-07-22 clarification — see
  Assumptions.
- **FR-006**: The count of full-row duplicate records MUST be computed and
  reported.
- **FR-007**: All profiling findings MUST be recorded as versioned,
  reviewable artifacts in the repository — not left only as ephemeral
  notebook output — so features 004 and 005 can reference them when
  designing the data contract and quality rules.
- **FR-008**: This feature MUST NOT write, alter, or filter any persisted
  table from the bronze data — it is read-only analysis; no silver table
  or transformed data is produced here.
- **FR-009**: If a **required** column is missing, genuinely renamed (not
  just differently cased), or has a type-family mismatch in any month's
  file, this MUST be explicitly flagged as a **critical** schema deviation
  finding, not silently defaulted or ignored.
- **FR-010**: If a **non-required** column is missing, genuinely renamed,
  added, or has a type-family mismatch in any month's file, this MUST
  still be flagged as a schema deviation finding, but at **informational**
  severity — deferred for a decision at modeling time (feature 004), not a
  blocker for this feature's own completion (2026-07-23 clarification).

### Key Entities

- **Profiling Finding**: One documented result per (month × metric)
  combination — schema comparison result (with a severity of critical or
  informational for schema deviations), row count, null rate per required
  column, descriptive statistics per required numeric column, out-of-range
  date count, duplicate count. Read-only output; does not modify the
  underlying bronze files.
- **Monthly Trip Record File**: The raw file per month landed by feature
  002 (`ifood_case.bronze.yellow_taxi_raw`) — the read-only input to this
  feature. No attribute of it is changed here.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A reader can determine, from documented profiling output
  alone, whether the 5 months share an identical schema across every
  column, and if not, exactly which columns differ, where, and whether
  each difference is critical (a required column) or informational (any
  other column).
- **SC-002**: Row count, null rate (for all 5 required columns), and
  descriptive statistics (for `total_amount` and `passenger_count`) are
  documented for all 5 months — 100% coverage, no month skipped.
- **SC-003**: Every data-quality risk named in the constitution (negative
  or zero `total_amount`, null or zero `passenger_count`, out-of-range
  dates, duplicate records) has a quantified count/percentage in the
  profiling output — not a qualitative yes/no statement.
- **SC-004**: The profiling output alone is sufficient for a reader to
  draft the data-quality rules for feature 005 without re-reading the raw
  files themselves.

## Assumptions

- This feature reads from the landing zone volume created by feature 002
  (`ifood_case.bronze.yellow_taxi_raw`) and lands no new files itself.
- Schema comparison (FR-001) covers every column in the source files, not
  just the 5 required ones (2026-07-23 clarification) — but null-rate
  profiling (User Story 3) and descriptive statistics (User Story 4) stay
  bounded to the 5 required columns, since those are the only columns that
  carry forward to the silver layer per the case brief.
- "Duplicate record" is measured here as an exact full-row duplicate. This
  feature reports the count; it does not decide a dedup policy — that
  belongs to features 004 (contract) and 005 (quality rules).
- The out-of-range date check (FR-005) is scoped to the whole Jan-May 2023
  window, not per-file adjacent-month leakage (2026-07-22 clarification).
  If leakage between adjacent in-window months later proves material, it
  would be a follow-up profiling metric, not part of this feature's
  baseline scope.
- Schema comparison (FR-001/FR-009) treats casing differences (e.g.
  `VendorID` vs `vendorid`) as the same column, and groups numeric types by
  family (integer, floating-point) rather than exact width — only a
  genuinely different column name, a missing column, or a cross-family
  type mismatch (e.g. string vs numeric) counts as a flagged deviation
  (2026-07-22 clarification).
- Standard percentiles (p25/p50/p75/p95/p99) are a sufficient default for
  "key percentiles" in FR-004 unless a later phase determines otherwise.
- No new landing zone location or file format decision is needed — this
  feature is purely analytical/read-only against feature 002's output.
