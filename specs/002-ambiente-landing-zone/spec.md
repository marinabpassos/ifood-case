# Feature Specification: Ambiente & Landing Zone

**Feature Branch**: `002-ambiente-landing-zone`

**Created**: 2026-07-22

**Status**: Draft

**Input**: User description: "feature 002 - Ambiente & Landing Zone"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Validate environment constraints before designing ingestion (Priority: P1)

As the case author, I need to confirm whether the target environment can
reach the NYC TLC data source directly, so I know whether to build a
direct-download ingestion path or fall back to a local-download-and-upload
path — before committing design time to either.

**Why this priority**: This is the single biggest unknown carried over
from prior project decisions and blocks the design of every later
ingestion step. Discovering a network restriction late would waste the
most time of anything in this feature.

**Independent Test**: Attempt to reach the NYC TLC parquet source from
within the target environment and record a documented pass/fail result,
independent of whether any file has been landed yet.

**Acceptance Scenarios**:

1. **Given** the target environment is provisioned, **When** a connection
   to the NYC TLC data source is attempted from inside it, **Then** the
   outcome (reachable or blocked) is recorded in project documentation.
2. **Given** the source is found unreachable, **When** the case author
   proceeds with ingestion, **Then** a documented fallback path is used
   instead, not a silent workaround.

---

### User Story 2 - Governed landing location exists (Priority: P2)

As the case author, I need a governed storage location (catalog, schema,
and volume, or platform equivalent) created in the workspace, so there is
a known, discoverable place to land raw files before any table exists.

**Why this priority**: Nothing can be ingested without somewhere to put
it, but this is independent of *how* files arrive (User Story 1) — it can
be created in parallel with that investigation.

**Independent Test**: List the workspace's catalogs/schemas/volumes
through standard platform tooling and confirm the expected landing
location exists and is accessible, without landing any file yet.

**Acceptance Scenarios**:

1. **Given** the workspace is provisioned, **When** the case author
   inspects the catalog, **Then** the landing zone's catalog, schema, and
   volume are present and listable.
2. **Given** the landing location exists, **When** any other project
   feature needs to read or write raw files, **Then** it has a single,
   unambiguous location to use — no ambiguity about which of multiple
   candidate locations is "the" landing zone.

---

### User Story 3 - Raw source files are landed (Priority: P3)

As the case author, I need the five months of Yellow Taxi trip record
files (January-May 2023) landed in the landing zone, unmodified from
source, so later profiling and transformation always start from a known,
complete, and untouched raw dataset.

**Why this priority**: This is the actual ingestion deliverable. It
depends on knowing the ingestion path (User Story 1) and having somewhere
to land files (User Story 2), so it is sequenced last even though it's
the most visible output.

**Independent Test**: List the contents of the landing zone and confirm
five file-sets exist, one per month (Jan-May 2023), each verified
non-empty and readable.

**Acceptance Scenarios**:

1. **Given** the landing zone exists and the ingestion path is chosen,
   **When** ingestion runs for a given month, **Then** that month's file
   appears in the landing zone unmodified from its original source format.
2. **Given** all five months have been processed, **When** the case
   author inspects the landing zone, **Then** exactly five monthly
   file-sets are present, none of them empty or corrupted.
3. **Given** a monthly file fails to download or arrives corrupted,
   **When** ingestion completes, **Then** the failure is visible (not
   silently skipped) and the month is retried or explicitly flagged as
   incomplete.

---

### Edge Cases

- If outbound access to the NYC TLC domain is blocked from the target
  environment, the fallback path (download outside the environment,
  upload into the landing zone through the platform's own tooling) MUST
  be used and its use documented as a deliberate, justified deviation —
  not discovered and worked around silently.
- If a monthly file is unusually small, unusually large, or fails
  integrity checks, it MUST be flagged and retried rather than accepted
  as-is or silently dropped — an incomplete raw dataset would
  invalidate every downstream profiling/quality conclusion.
- Environment dormancy (the workspace risking deactivation from prolonged
  inactivity) is an operational reminder tracked in project decisions, not
  an acceptance condition of this feature.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The environment MUST be validated for outbound network
  access to the NYC TLC data source before the ingestion approach is
  finalized, and the result (reachable or not) MUST be documented.
- **FR-002**: If direct access is unavailable, a fallback ingestion path
  MUST be used instead, and its use MUST be documented as a deliberate,
  justified deviation from the direct-download approach.
- **FR-003**: A governed storage location (catalog, schema, and volume, or
  platform equivalent) MUST exist to serve as the landing zone before any
  file is landed.
- **FR-004**: The five months of Yellow Taxi trip record files for
  January-May 2023 MUST be landed in the landing zone, unmodified from
  their original source format.
- **FR-005**: Each landed file MUST be verified as non-empty and readable
  before ingestion for that month is considered complete.
- **FR-006**: The landing zone MUST NOT contain any transformed, cleaned,
  or retyped data — only files exactly as received, consistent with the
  project's bronze-layer definition.
- **FR-007**: Environment constraints encountered during this feature
  (compute type, warehouse size, network restrictions, or any other
  Free-Edition limitation) MUST be documented together with how each was
  resolved.

### Key Entities

- **Landing Zone**: The governed catalog/schema/volume location that
  holds raw files before any table is modeled. Not a table itself — a
  storage container with no schema enforcement.
- **Monthly Trip Record File**: One raw file per month (Jan-May 2023) as
  downloaded from the source, identified by its month, with attributes
  such as source origin, file size, and landed timestamp — content is
  opaque to this feature (no columns are inspected or typed here).

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A reader can determine, from project documentation alone,
  whether direct download from the data source works in this environment
  and which ingestion path was ultimately used.
- **SC-002**: 100% of the five required monthly files (Jan-May 2023) are
  present and verified non-empty in the landing zone.
- **SC-003**: The landing zone's location is discoverable and listable
  through the platform's standard tooling, with no additional ad hoc setup
  needed to find it.
- **SC-004**: No file in the landing zone differs from its original
  downloaded form — a byte-for-byte or row-count comparison against the
  source confirms no transformation occurred.

## Assumptions

- The landing zone is implemented as a Unity Catalog Volume (or DBFS
  equivalent), per `DECISOES_PROJETO.md` §3 — the exact technology choice
  is a planning-phase decision, not re-litigated here.
- The target platform (Databricks Free Edition) is already fixed by prior
  project decisions; this feature validates operational constraints
  within that platform, it does not reconsider the platform choice itself.
- "Five months" means January, February, March, April, and May 2023
  Yellow Taxi trip data, per the case brief.
- Workspace access/credentials already exist (the case author has an
  active Databricks Free Edition account); provisioning the account
  itself is out of scope.
