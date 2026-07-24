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

### User Story 4 - Results are readable as a chart, not just a table of numbers (Priority: P4)

As a business stakeholder reviewing the case (not necessarily
comfortable reading a raw numeric table), I need each answer presented
as a visual chart in addition to the plain numbers, so trends across
months/hours are obvious at a glance — while still being able to run the
underlying SQL directly myself if I prefer numbers over pictures.

**Why this priority**: Directly serves "clareza na comunicação dos
resultados," one of the case's own stated evaluation criteria — but it's
additive to User Stories 1-3 (the numeric answers already satisfy the
case brief's literal requirement on their own), so it's sequenced last.

**Independent Test**: Open `analysis/` and confirm a chart image exists
for each question, independent of whether anyone runs the SQL.

**Acceptance Scenarios**:

1. **Given** both questions' results are computed, **When** they are
   delivered, **Then** each also has a saved chart image (e.g., a bar
   chart of average `total_amount` by month; a bar or line chart of
   average `passenger_count` by hour) — viewable directly in the
   repository, with no need to open Databricks or re-run anything to see
   it.
2. **Given** a business user prefers to query the data directly instead
   of looking at a chart, **When** they open the plain `.sql` file for
   either question, **Then** it runs standalone against
   `ifood_case.silver.yellow_taxi_trips` with no dependency on the chart
   or notebook — the raw-SQL path from User Story 3 is not replaced by
   this story, only complemented.

---

### User Story 5 - Bonus: daily trip volume, trend and seasonality (Priority: P5)

As the case evaluator looking for creativity beyond the two required
questions, I need to see how the *daily* number of trips across the
whole Jan-May 2023 window behaves over time — whether it's trending up
or down, and whether it follows a repeating weekly pattern — presented
visually, so I can assess a differentiator analysis that goes beyond a
simple average.

**Why this priority**: Explicitly a bonus/differentiator, not part of
the case brief's two required questions (User Stories 1-2) — sequenced
last and must never be confused with, or substitute for, the required
answers. Directly serves the case's own "criatividade" evaluation
criterion, matching this project's existing pattern of clearly labeling
differentiator content separately from official deliverables (see
`DECISOES_PROJETO.md`'s treatment of the roadmap's own POC
feature).

**Independent Test**: Open `analysis/` and confirm a daily trip-count
time series exists with a trend/seasonality decomposition and a chart,
clearly labeled as bonus content, independent of whether the two
required questions (User Stories 1-2) are being reviewed.

**Acceptance Scenarios**:

1. **Given** `ifood_case.silver.yellow_taxi_trips` contains cleaned
   trips across January-May 2023, **When** trips are counted per
   calendar day of `tpep_pickup_datetime`, **Then** one row per day
   is produced covering the full date range with no gaps invented or
   assumed away.
2. **Given** the daily trip-count series, **When** it is decomposed into
   trend and seasonality components, **Then** both an overall trend
   (rising/falling/flat) and a repeating weekly pattern (e.g., weekday
   vs. weekend ridership) are identifiable from the output.
3. **Given** the decomposition is complete, **When** it is delivered,
   **Then** it is saved as chart image(s) in `analysis/`, visually
   distinct from and clearly labeled apart from the two required
   questions' charts (User Story 4) — a reader must not mistake this
   bonus analysis for a required answer.

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
- **FR-006**: Each question's result MUST also be delivered as a saved
  chart image in `analysis/`, in addition to the raw SQL and the
  tabular numbers (FR-004) — the chart is an additional presentation of
  the same result, not a replacement for the plain-SQL path (FR-004
  still applies unchanged; a business user who prefers SQL over a chart
  is never blocked from that).
- **FR-007**: A bonus analysis MUST compute the daily trip count across
  the full January-May 2023 window in
  `ifood_case.silver.yellow_taxi_trips` — one row per calendar day of
  `tpep_pickup_datetime`, whole fleet, no additional filtering beyond
  what the silver table already guarantees.
- **FR-008**: The daily trip-count series MUST be decomposed into a
  trend component and a weekly seasonality component, so both the
  overall direction of ridership and any repeating day-of-week pattern
  are identifiable.
- **FR-009**: The trend/seasonality decomposition MUST be saved as
  chart image(s) in `analysis/`, and MUST be clearly labeled as bonus/
  differentiator content — distinct from, and never presented as a
  substitute for, the two required questions' answers (FR-001/FR-002).

### Key Entities

- **Analytical Answer**: one per question — the question text, the
  query that answers it, the actual computed result rows, a chart image
  representing those rows, and when it was computed. Two instances:
  monthly average `total_amount` (5 rows), hourly average
  `passenger_count` for May (24 rows).
- **Daily Trip Volume Decomposition** (bonus): the daily trip-count
  series (~151 rows, one per calendar day Jan 1-May 31, 2023), its
  trend component, its weekly seasonality component, one or more chart
  images representing the decomposition, and when it was computed. Not
  one of the two required Analytical Answers — a separate, clearly
  labeled differentiator entity.

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
- **SC-005**: A reader can see each answer as a chart image in
  `analysis/` without opening Databricks, running any code, or
  configuring a visualization themselves.
- **SC-006**: A reader can see the daily trip-count trend and weekly
  seasonality pattern as chart image(s) in `analysis/` without running
  anything, and the material is clearly distinguishable as bonus content
  rather than one of the two required answers.

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
  convention. In practice this means both exist side by side: a
  PySpark/notebook path that also produces the chart (FR-006), and a
  plain, standalone `.sql` file per question that a business user can
  run directly with no notebook or chart involved (FR-004) — one
  doesn't replace the other.
- Chart type (FR-006) is left as an implementation choice (e.g., bar
  chart for both questions is a reasonable default) — the business
  requirement is "visually readable at a glance," not a specific chart
  library or format.
- The bonus daily trip-volume analysis (User Story 5 / FR-007-009) is
  explicitly a differentiator, added after the case's two required
  questions, at the user's own request (2026-07-23) — its scope,
  library choice, and depth are implementation decisions (planning
  phase), not part of the case brief's literal requirements. It must
  never be presented in a way that could be mistaken for one of the two
  required answers.
