# Feature Specification: Análises Analíticas

**Feature Branch**: `008-analytical-questions`

**Created**: 2026-07-23

**Status**: Draft

**Input**: User description: "feature 008 - Análises Analíticas: SQL/PySpark em analysis/ respondendo as duas perguntas do case (média de total_amount por mês; média de passenger_count por hora em maio), considerando todos os yellow táxis da frota"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Average total charged per month across the whole fleet (Priority: P1)

As the case evaluator, I need the average `total_amount` for each of the
5 months (January-May 2023), across every yellow taxi in the fleet, so I
can see how average fare revenue moved month over month over the case's
data window.

**Why this priority**: This is the first of the two analytical questions
the case brief requires answered — the primary deliverable of this
feature, and the reason features 002-007 (landing through observability)
were built first.

**Independent Test**: Compute the average `total_amount` grouped by
month directly from `ifood_case.silver.yellow_taxi_trips` and confirm
one value exists for each of the 5 months, independent of the second
question.

**Acceptance Scenarios**:

1. **Given** `ifood_case.silver.yellow_taxi_trips` contains only valid,
   cleaned trip records (features 004-006), **When** the average
   `total_amount` is computed grouped by month, **Then** exactly 5
   values are produced (January through May 2023), one per month,
   covering every trip in the silver table with no additional filtering.
2. **Given** the answer has already been computed once as part of
   feature 006's own verification (`dq-run-log.md`: ~27.46 / 27.37 /
   28.29 / 28.78 / 29.45 for Jan-May), **When** this feature computes the
   same aggregation as its own deliverable, **Then** the result matches
   those figures exactly — confirming this is the same, stable
   computation, not a newly-invented one.

---

### User Story 2 - Average passengers by hour of day in May (Priority: P2)

As the case evaluator, I need the average `passenger_count` for each
hour of the day (0-23), restricted to trips that started in May 2023,
across every yellow taxi in the fleet, so I can see how ridership size
varies by time of day.

**Why this priority**: The second of the two required analytical
questions. Sequenced after User Story 1 only because the case brief
lists it second — the two questions are otherwise independent (different
column, different grouping, different month filter).

**Independent Test**: Compute the average `passenger_count` grouped by
hour of `tpep_pickup_datetime`, filtered to May 2023, directly from
`ifood_case.silver.yellow_taxi_trips`, independent of the first
question.

**Acceptance Scenarios**:

1. **Given** `ifood_case.silver.yellow_taxi_trips` contains only trips
   with a valid (non-null, non-zero) `passenger_count` (feature 006's
   cleaning rule), **When** the average is computed grouped by hour of
   `tpep_pickup_datetime` for May 2023 trips only, **Then** exactly 24
   values are produced (hour 0 through hour 23).
2. **Given** "hour of day a taxi was caught" means the pickup event
   specifically, **When** the hour is derived, **Then** it comes from
   `tpep_pickup_datetime`, not `tpep_dropoff_datetime`.

---

### User Story 3 - Both answers exist as versioned artifacts, not ad hoc output (Priority: P3)

As the case evaluator, I need both analytical answers delivered as
files in `analysis/` — query plus the actual computed result — so I can
read and re-run them without re-deriving anything from a chat transcript
or a one-off notebook cell.

**Why this priority**: Directly required by the case brief ("Entregar
como SQL ou PySpark estruturado em `analysis/`") and by this project's
own Development Workflow documentation ("delivered as versioned
artifacts in `analysis/`, not ad hoc query results"). Lowest priority
only because it's about *how* the first two answers are delivered, not
computing anything new.

**Independent Test**: Open `analysis/` without running anything and
confirm both questions' queries and their actual computed answers are
readable there.

**Acceptance Scenarios**:

1. **Given** both questions have been answered, **When** the results are
   saved, **Then** each has its own versioned file (or files) in
   `analysis/` containing both the query and the actual computed
   numbers — not just a query with no recorded result.
2. **Given** a future reader has SQL Warehouse or notebook access,
   **When** they re-run the saved query, **Then** it executes directly
   against `ifood_case.silver.yellow_taxi_trips` with no setup beyond
   what features 002-006 already established.

---

### Edge Cases

- If a given hour of the day in May has zero trips (unlikely at this
  data volume, but not impossible), that hour simply has no row in the
  result — this feature does not need to invent a zero-filled entry for
  an hour that genuinely has no data.
- This feature MUST NOT apply any additional filtering or cleaning
  beyond what the silver table already guarantees (features 004-006) —
  no re-deriving business rules that belong to an earlier layer.
- If `ifood_case.silver.yellow_taxi_trips` were ever rebuilt with
  different row counts (a future re-run), these two queries would
  naturally reflect the new data — this feature answers the two
  questions as of whenever it's run, it does not freeze a single
  point-in-time snapshot as the only valid answer.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The average `total_amount` MUST be computed grouped by
  month (January-May 2023), across every row in
  `ifood_case.silver.yellow_taxi_trips` — the whole fleet, no additional
  filtering.
- **FR-002**: The average `passenger_count` MUST be computed grouped by
  hour of day (0-23) derived from `tpep_pickup_datetime`, restricted to
  trips whose `tpep_pickup_datetime` falls in May 2023.
- **FR-003**: Both computations MUST read exclusively from
  `ifood_case.silver.yellow_taxi_trips` — not bronze, not landing, and
  with no extra cleaning or filtering step of this feature's own
  invention.
- **FR-004**: Both the query (SQL or structured PySpark, per the case
  brief) and the actual computed result values MUST be saved as
  versioned files under `analysis/` — a query without its result, or a
  result without its query, does not satisfy this requirement.
- **FR-005**: This feature MUST NOT modify
  `ifood_case.silver.yellow_taxi_trips`, its contract, or any upstream
  pipeline (features 002-007) — it is read-only analysis.

### Key Entities

- **Analytical Answer**: one per question — the question text, the
  query that answers it, the actual computed result rows, and when it
  was computed. Two instances: monthly average `total_amount` (5 rows),
  hourly average `passenger_count` for May (24 rows).

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A reader can find the exact average `total_amount` for
  each of the 5 months in `analysis/` without running any query
  themselves.
- **SC-002**: A reader can find the exact average `passenger_count` for
  each of the 24 hours in May in `analysis/` without running any query
  themselves.
- **SC-003**: Both queries in `analysis/` are directly re-runnable
  against `ifood_case.silver.yellow_taxi_trips` by anyone with SQL
  Warehouse or notebook access — no undocumented setup step.
- **SC-004**: Both answers are computed with zero additional
  cleaning/filtering beyond what the silver table already guarantees —
  validating feature 006's own promise (its SC-004) that silver is
  analysis-ready as-is.

## Assumptions

- This feature depends on feature 006 (silver data quality), complete
  and merged; feature 007 (observability) is unrelated to this
  feature's own logic but is already merged too.
- "Hour of day a taxi was caught" (case brief wording) means the pickup
  event — the hour is derived from `tpep_pickup_datetime`, not
  `tpep_dropoff_datetime`.
- "Average total_amount received in a month" (case brief wording) means
  one average per calendar month across the 5-month window (5 results),
  not a single grand average collapsing all 5 months into one number —
  matching how feature 006 already computed and reported this exact
  aggregation as its own SC-004 verification sample.
- Whether the deliverable format is SQL or structured PySpark (the case
  brief allows either) is a planning-phase decision, not a business
  requirement — this spec stays technology-agnostic per Spec Kit
  convention.
