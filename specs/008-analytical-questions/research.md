# Phase 0 Research: Análises Analíticas

**Input**: [spec.md](./spec.md) · Constitution `.specify/memory/constitution.md` ·
`ifood_case.silver.yellow_taxi_trips` (features 004-006)

No `[NEEDS CLARIFICATION]` markers remain in the spec. Decision 1 below
was revised once, before `/speckit-tasks`, based on explicit user
feedback that a genuine Databricks notebook was wanted for the chart
requirement (FR-006) — not a local script — since the notebook is
itself meant to demonstrate the platform's analysis/visualization
capability, not just be the shortest path to a number. Decisions 6-8
were added in a second pre-`/speckit-tasks` revision, for the bonus
Prophet-based daily trip-volume analysis (User Story 5 / FR-007-009)
the user requested as a differentiator on top of the two required
questions.

## 1. Notebook + standalone SQL, not SQL-only (revised twice)

- **Decision**: Ship both: two plain, standalone `.sql` files (unchanged
  from the original plan) for a business user who wants to run only
  SQL, **and** a single genuine Databricks notebook,
  `analysis/analise.py` — real cell structure (`# COMMAND ----------`
  cell breaks), not a flat script: one section per question, each a
  markdown cell with the question text, a `%sql` cell whose rendered
  result table *is* the answer, and a Python cell that turns that same
  result (via Databricks' implicit `_sqldf` variable) into a chart.
- **Rationale**: The case brief allows "SQL ou PySpark estruturado," and
  the user explicitly asked (first revision) for a notebook specifically
  because it doubles as "uma amostra do uso da ferramenta" (a
  demonstration of tool usage) — a legitimate, already-approved
  requirement (spec FR-006/SC-005), not scope creep. A second revision
  (2026-07-23, post-implementation user feedback) rejected the first
  notebook draft (`generate_answers.py`, a single flat script with no
  cell markers, matching every prior feature's pipeline-notebook
  convention) as not what was wanted for a *presentation* artifact — the
  user explicitly asked for real markdown/query/chart cells per
  question, renamed to `analise.py`. Keeping the plain `.sql` files too
  (rather than replacing them with the notebook) preserves User Story
  3's original "a business user can run this with nothing but SQL"
  promise.
- **Alternatives considered**: Local Python + `matplotlib` reading query
  results fetched via the CLI's SQL Warehouse query path — rejected per
  explicit user correction: this would be a local-tooling shortcut, not
  a Databricks notebook, and would miss the point of demonstrating the
  platform itself. Notebook-only (dropping the standalone `.sql` files)
  — rejected, that would remove the direct-SQL path the user separately
  asked to keep ("a pessoa de negócio sempre poderá analisar via query
  SQL também"). A flat single-cell script (the first draft) — rejected
  on explicit user feedback in favor of genuine markdown/`%sql`/Python
  cells.

## 2. Query text: one copy per audience, not a runtime read (revised)

- **Decision (revised)**: The notebook's `%sql` cells contain the query
  text directly (character-identical to each standalone `.sql` file),
  not a `spark.sql(open(path).read())` runtime read of the uploaded
  `.sql` file. Each question's SQL now exists in exactly two places: the
  standalone `.sql` file (business-SQL audience) and the notebook's own
  `%sql` cell (notebook-reading audience) — both hand-kept in sync.
- **Rationale**: A genuine multi-cell notebook is the whole point of the
  2026-07-23 revision (decision 1) — a `%sql` cell is what makes the
  query *and* its rendered result table appear natively in the notebook
  when someone opens and runs it in the Databricks UI, which a
  `spark.sql(open(path).read())` call inside a Python cell does not give
  you (it hides the actual SQL text and the auto-rendered result table
  behind a file read). The original single-source-of-truth concern
  (avoiding drift) is a smaller risk here than it looks: both the two
  required questions' queries are finished, stable aggregations (no
  active development), not evolving pipeline logic.
- **Alternatives considered**: The original runtime-read approach
  (`open(path).read()`) — rejected because it's incompatible with a
  `%sql` cell (magic commands don't accept dynamically-read SQL text)
  and defeats the purpose of the cell-structure revision. Templating or
  code-generating the notebook from the `.sql` files at build time —
  rejected as unnecessary infrastructure for two small, stable queries.

## 3. Getting chart images out of Databricks and into the repo

- **Decision**: Each chart is rendered with `plotly` inside the notebook
  (revised post-implementation from `matplotlib` — decision 10) and
  exported to PNG bytes via `fig.to_image()` (Kaleido engine),
  base64-encoded, and included in the notebook's JSON result (the same
  `dbutils.notebook.exit(json.dumps(...))` pattern every prior feature
  already uses). Locally, the JSON is decoded and each chart's base64
  payload is written to a `.png` file under `analysis/charts/`.
  `fig.to_image()` returns bytes directly — no `io.BytesIO`/`savefig`
  buffer dance needed the way matplotlib required.
- **Rationale**: Avoids inventing new infrastructure (no Unity Catalog
  Volume just to stage a handful of small images) — the existing "run a
  job, get JSON back, transcribe it locally" mechanism already handles
  arbitrary text payloads (base64 is just text), so four ~30-400KB PNGs
  round-trip through it without any new mechanism. Switching the
  rendering library (decision 10) didn't need to change this transport
  mechanism at all — only the one line producing the bytes changed.
- **Alternatives considered**: Writing the PNGs to a Unity Catalog
  Volume and downloading via `databricks fs cp` — rejected as an extra
  Volume just for a few small images, more moving parts than the
  already-proven JSON-output round-trip. Manual screenshot (feature
  007's lineage-evidence pattern) — rejected here since these charts
  are *generatable* content (unlike a UI-only lineage graph), so there's
  no reason to require a human screenshot when the notebook can produce
  the exact image deterministically.

## 4. Query design (unchanged from the original plan)

- **Decision**: Same as originally planned:
  - Q1: `GROUP BY date_format(tpep_pickup_datetime, 'yyyy-MM')`,
    `AVG(total_amount)` rounded to 2 decimals, plus `COUNT(*)`.
  - Q2: `WHERE year(tpep_pickup_datetime) = 2023 AND month(tpep_pickup_datetime) = 5`,
    `GROUP BY hour(tpep_pickup_datetime)`, `AVG(passenger_count)` rounded
    to 2 decimals, plus `COUNT(*)`.
- **Rationale**: `tpep_pickup_datetime` is guaranteed non-null and within
  Jan-May 2023 by the silver contract's rules (features 005-006), so no
  additional `WHERE` is needed for Q1. Matches the same precision already
  used in feature 006's own `dq-run-log.md` sample query.
- **Alternatives considered**: See the original research (unchanged) —
  a single combined query was rejected for mixing two different grains
  for no benefit.

## 5. Chart type

- **Decision**: A bar chart for both questions (month on the x-axis for
  Q1, hour of day for Q2) — a bar chart is the most direct, unambiguous
  way to compare discrete categories (5 months; 24 hours), and needs no
  justification beyond "the simplest chart that shows the trend clearly"
  (spec's own FR-006 leaves chart type as an implementation choice).
- **Alternatives considered**: A line chart for Q2 (hour of day is
  ordinal/continuous-ish) — a reasonable alternative, not chosen only
  because a bar chart is marginally more consistent visually with Q1
  without materially changing readability at 24 categories.

## 6. Bonus analysis: Prophet availability and installation mechanism

- **Decision (revised twice after implementation)**: Prophet is **not**
  pre-installed on Databricks Runtime (unlike `matplotlib`).
  - *First attempt*: a task-level PyPI library declaration,
    `"libraries": [{"pypi": {"package": "prophet"}}]` — rejected outright
    at submit time on this workspace's serverless compute (`Error:
    Libraries field is not supported for serverless task, please specify
    libraries in environment.`).
  - *Second attempt*: a job-level `environments` entry referenced by the
    task's `environment_key` (`{"spec": {"client": "2", "dependencies":
    ["prophet"]}}`, `client: "1"` rejected first with `Invalid platform
    channel Client-1`). This worked for `databricks jobs submit` runs,
    but the user reported it failing when the notebook was instead run
    interactively/attached inside the Databricks UI — the job-level
    dependency declaration only applies to that specific job's task, not
    to an interactive attach-and-run.
  - **Final decision**: `%pip install prophet` as the notebook's own
    first code cell, followed by `dbutils.library.restartPython()`, then
    a single cell with every import the notebook needs (`base64`, `io`,
    `json`, `matplotlib.pyplot`, `prophet.Prophet`) — all *before* any
    question/chart cell. This makes the notebook self-installing:
    correct whether opened and run interactively or run unattended via
    `databricks jobs submit` with a plain task (no `libraries` or
    `environments` field needed at all). Verified working both ways
    (job run: `analise_run_pip_install`, `result_state: SUCCESS`,
    identical row counts/chart output to the `environment_key` run).
- **Rationale**: The `environments`/`environment_key` mechanism is
  job-scoped, not notebook-scoped — it doesn't help someone who opens
  `analise.py` directly in the Databricks UI and clicks "Run all," which
  is exactly the failure the user hit. `%pip install` + `restartPython()`
  is the standard idiom for exactly this situation (a notebook that must
  be self-sufficient regardless of how it's attached/run) and doesn't
  interfere with the Spark session or the later `%sql`/`_sqldf` cells
  (`restartPython()` only resets the Python interpreter, not the Spark
  session).
- **Alternatives considered**: The task-level `libraries` field —
  rejected, the platform itself rejects it for serverless tasks. The
  job-level `environments`/`environment_key` pair — works for job runs
  but not interactive runs, which is the scenario that surfaced the bug;
  kept as a documented dead end, not the shipped mechanism. A
  cluster-scoped init script or a persistent library — rejected as
  unnecessary infrastructure for a single read-only bonus analysis on
  serverless compute.

## 7. Bonus analysis: daily trip-count query and decomposition design

- **Decision**: `analysis/daily_trip_counts.sql` computes
  `GROUP BY date(tpep_pickup_datetime)`, `COUNT(*)` across the whole
  silver table (no month filter) — one row per calendar day, ~151 rows
  for Jan 1-May 31, 2023. The notebook collects this to a pandas
  DataFrame (`ds`/`y` columns, Prophet's required shape), fits
  `Prophet(yearly_seasonality=False, weekly_seasonality=True,
  daily_seasonality=False)`, and calls `.predict()` on the same
  historical dates (no forecast into unseen future dates — the ask was
  to see trend/seasonality in the existing data, not to forecast).
- **Rationale**: Yearly seasonality is explicitly disabled because
  ~5 months of data cannot support a meaningful yearly-cycle estimate —
  Prophet would either error or fit an overfit, meaningless yearly
  curve on less than one full period. Weekly seasonality is exactly the
  "repeating pattern" the user asked to see (weekday vs. weekend
  ridership). Daily seasonality doesn't apply since the series is
  already aggregated to one point per day (no sub-daily resolution to
  decompose).
- **Alternatives considered**: Forecasting future (June+) trip counts —
  rejected, out of scope for "ver sazonalidade, tendência" (the user
  asked to see the existing pattern, not predict unseen data). A
  from-scratch statsmodels STL decomposition instead of Prophet —
  rejected, the user explicitly named Prophet.

## 8. Bonus analysis: chart output

- **Decision**: Two chart images, both clearly labeled as bonus/
  differentiator content and kept visually and by-filename distinct
  from the two required questions' charts: `daily_trip_volume_trend.png`
  (`model.plot(forecast)` — actual daily counts with the fitted
  trend/seasonality curve overlaid) and
  `daily_trip_volume_components.png` (`model.plot_components(forecast)`
  — separate trend and weekly-seasonality subplots, Prophet's own
  standard decomposition view). Both round-trip through the same
  base64-in-JSON-output mechanism as decision 3 above.
- **Rationale**: `plot_components` is Prophet's own built-in,
  purpose-built way to show trend and seasonality separately — no
  need to hand-roll a custom decomposition chart when the library
  already produces the standard one.
- **Alternatives considered**: A single combined figure — rejected,
  `plot()` and `plot_components()` serve different, complementary
  purposes (raw fit vs. decomposed components) and Prophet returns them
  as two separate figures natively.

## 9. Execution mechanism

- **Decision**: `analise.py` is a Databricks notebook-source script
  (with real `# COMMAND ----------` cell breaks — decision 1), imported
  and run via `databricks jobs submit` on serverless compute — same
  `jobs submit`/`get-run-output` round trip as features 002/003/004/
  006/007, now carrying a multi-cell notebook instead of a flat script.
  The two standalone `.sql` files are run directly against the SQL
  Warehouse via `databricks experimental aitools tools query` (or any
  SQL client), with no job/notebook involved for that path.
- **Rationale**: Two different audiences, two different execution paths
  — a business user never needs to touch a notebook or job to get the
  numbers; the notebook is specifically for the chart-generation
  requirement. The `jobs submit` payload needs no special JSON for the
  bonus analysis's Prophet dependency — the notebook installs it itself
  (decision 6) — so the same plain single-task payload used for the
  required questions also runs the bonus section.

## 10. Chart styling: iFood brand color, Portuguese labels (added post-implementation, user feedback)

- **Decision**: All 4 charts recolored to a single iFood-brand red
  (`#EA1D2C`) as the sole mark color — each chart is one series, so per
  the `dataviz` skill's color-formula this is a single fixed hue with no
  legend needed (the title already names the series), not a multi-color
  categorical palette requiring the skill's CVD/adjacency validator.
  Contrast-checked against white via the skill's own
  `validate_palette.js` `contrast()` export: 4.46:1, clearing the 3:1
  mark-vs-surface floor. All titles/axis labels/tick labels translated
  to Portuguese (Prophet's weekly-component chart auto-generates English
  weekday names — mapped to `Dom`/`Seg`/.../`Sáb`). Direct value labels
  added selectively (dataviz skill: never label every point) — all 5
  bars for Q1 (small n, all meaningful), only min/max for Q2's 24
  hourly bars.
- **Rationale**: User request, 2026-07-23 ("gráficos mais bonitos...
  cores do iFood"). The `dataviz` skill's procedure (form already
  chosen — bar/line; color assigned by job, computed not eyeballed;
  recessive gridlines; selective labels; text never wears the data
  color) applies to a static exported PNG the same way it would to an
  HTML/SVG chart — only the interactivity-specific sections (hover
  layer, filters) don't apply to a non-interactive exported image.
- **Alternatives considered**: Recoloring only the two required
  questions' bar charts and leaving the bonus Prophet charts in the
  library's default blue — rejected for visual inconsistency across one
  notebook's charts; restyled all 4 for a single coherent look.

## 11. Chart rendering library: Plotly + Kaleido, replacing matplotlib (added post-implementation, user feedback)

- **Decision**: Switched all 4 charts from `matplotlib` to
  `plotly.graph_objects` (bars) and `prophet.plot.{plot_plotly,
  plot_components_plotly}` (bonus), exported to static PNG via
  `fig.to_image()` (Kaleido engine, pinned `kaleido==0.2.1` —
  decision 3). Same iFood-red palette and PT-BR labels as decision 10,
  just re-implemented on the new library: a `style_layout()` helper for
  titles/axes/grid/font, and direct trace mutation (`fig.data[i].line.
  color = IFOOD_RED`, matched by trace role) to recolor what Prophet's
  own plotting functions already draw, mirroring the matplotlib
  version's `restyle_prophet_axis()` approach but on Plotly's trace
  API instead of matplotlib's `Line2D`/`Collection` objects.
- **Rationale**: Running the notebook interactively, the user hit a
  wall of matplotlib `findfont: Font family 'Helvetica Neue'/'Arial'
  not found` warnings — Databricks Runtime only ships DejaVu Sans, and
  matplotlib's font-fallback prints a warning per lookup (not silent).
  While fixing that, the user asked to evaluate Plotly instead of just
  patching the font list. Two additional reasons favored the switch
  once tried: Kaleido's Chromium-based static render is visibly crisper
  than matplotlib's for the same chart, and Chromium's CSS font-stack
  fallback is silent by design (no `findfont`-style warning spam) even
  when naming fonts (`Helvetica Neue, Arial, sans-serif`) not literally
  installed in the container.
- **Alternatives considered**: Just pinning `font.family` to `"DejaVu
  Sans"` in matplotlib (tried first, worked, no warnings) — kept only
  as an intermediate fix until Plotly was evaluated and preferred per
  the user's explicit request. Kaleido ≥1.0 — rejected: that major
  version replaced its bundled Chromium with a separate
  `pio.get_chrome()` download at first use, a poor fit for Databricks
  Free Edition's restricted outbound network (constitution Principle
  IV); `0.2.1` is the last version with Chromium bundled in the pip
  package itself, so the `%pip install` step is fully self-contained
  like every other dependency this notebook installs.
- **Verification method**: Before writing final styling code, a
  throwaway probe script (`analysis/_probe_plotly.py`, deleted after
  use — local and workspace copy) ran `plot_plotly`/
  `plot_components_plotly` once and returned each trace's `name`/
  `mode`/`fill`/color via `dbutils.notebook.exit()` (print-statement
  stdout isn't retrievable via `databricks jobs get-run-output` without
  log delivery configured — learned this the first probe attempt).
  This caught two things that would otherwise have been guessed wrong:
  the exact trace order/roles inside `plot_plotly`'s 4-trace output
  (observed points, invisible upper-bound line, the visible "Predicted"
  line which *also* carries the upper-half fill, invisible lower-bound
  line carrying the lower-half fill), and that the weekly-seasonality
  subplot's x-axis is a plain date axis over Prophet's fixed 2017-01-01
  (Sun) - 2017-01-07 (Sat) reference week with no pre-set weekday tick
  labels (unlike matplotlib's version, which had text tick labels to
  pattern-match against).
