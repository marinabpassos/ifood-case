# Phase 0 Research: Repo Scaffold

No items in Technical Context were marked `NEEDS CLARIFICATION` — the
stack, layout, and constraints were already fixed by prior project
decisions (`DECISOES_PROJETO.md`) and the case brief PDF. The research
below covers the remaining open implementation questions: *how* to
structure the scaffold artifacts well, not *what* the stack is.

## Persisting empty directories in git

**Decision**: Use a `.gitkeep` placeholder file inside each structural
directory that has no real content yet (`src/`, `analysis/`, `contracts/`,
`data/`).

**Rationale**: Git does not track empty directories. A `.gitkeep` is the
lightest-weight, most widely recognized convention for keeping a directory
present in the tree without implying real content — cheaper than a
per-folder `README.md` and avoids `data/` being invisible to a fresh clone
before `.gitignore`'s `data/*` rule has any real files to apply to.

**Alternatives considered**:
- *Per-folder README.md*: rejected as heavier than needed for folders that
  will be populated by later features anyway — the top-level `README.md`
  already documents each folder's purpose (FR-005), so a second copy per
  folder would duplicate that and violate Constitution Principle VI (lean
  docs).
- *Leave directories out until a later feature needs them*: rejected
  because the spec (FR-001/FR-002) requires the full layout to exist from
  this feature, so a newcomer sees the complete intended structure
  immediately rather than discovering it incrementally across commits.

## README structure for a graded case submission

**Decision**: `README.md` sections, in order: Objetivo, Arquitetura (short
summary + layer diagram reference), Estrutura do Repositório (table:
folder → purpose, explicitly marking which folders are case-brief minimum
vs. project additions), Stack Tecnológica, Como Executar (placeholder,
completed by the implementation feature), Perguntas Analíticas Respondidas
(placeholder linking to `analysis/`).

**Rationale**: The case's evaluation criteria include "clareza na
comunicação dos resultados" and "justificativa das escolhas técnicas."
Structuring the README around exactly those two criteria — a clear map of
the repo, and an explicit minimum-vs-addition table — makes both criteria
directly verifiable by a reader in under a minute (spec `SC-001`,
`SC-003`), instead of leaving that judgment implicit.

**Alternatives considered**:
- *Minimal README (just a title + folder list)*: rejected — satisfies
  FR-003 literally but not `SC-001`/`SC-003`, which require the
  minimum-vs-addition distinction to be visible, not just the layout.
- *Full run instructions written now*: rejected — the pipeline doesn't
  exist yet (this feature is scaffold-only per FR-006), so real "how to
  run" content would be fiction; a clearly labeled placeholder section is
  more honest and gets completed by the feature that actually builds the
  pipeline.

## requirements.txt scope

**Decision**: Keep the existing `requirements.txt` as-is (pyspark,
delta-spark, pyyaml as active dependencies; databricks-sdk and
ydata-profiling listed as commented-out future additions). No changes
needed for this feature.

**Rationale**: The file already matches the fixed stack documented in the
Constitution's Technology Stack section and in `DECISOES_PROJETO.md` §3.
This feature's job (FR-004) is to confirm the manifest exists and is
installable, not to expand it — new dependencies get added by the feature
that actually needs them, keeping the file itself is evidence of a
"deliberate addition" discipline (Constitution Principle IV).

**Alternatives considered**: None — re-authoring a file that already
satisfies the requirement would be unjustified churn.
