# Mapsift specs index

A one-line catalog of the documents in `specs/`. Read the document itself for its content; this index only
says what each is and where it lives. It is a convenience, not an authority.

## The ID namespaces

Every prefix used across the canon, so a newcomer does not have to derive the map by reading everything.

| Prefix | Lives in | What it is |
|---|---|---|
| **I1 to I11** | foundation section 11 | invariants, each with the scar of the bug it prevents |
| **OQ-1 to OQ-24** | foundation section 13 | open questions, deliberately not answered |
| **C1 to C14** | `CLAUDE.md` | the enforceable constraints, one per invariant, each with a pass/fail test |
| **A to K** | PRD section 1 | Layer 1 capability families (access, map and import, schema, editing, inspect, styling, analysis, collaboration, insight, output, workspace) |
| **AR1 to AR5** | PRD section 2 | anti-requirements, behaviours deliberately rejected |
| **T1 to T9** | PRD section 5 | Layer 2, transversal system behaviours |
| **M1 to M16** | PRD section 6 | Layer 3, the data model and the contracts |
| **S1 to S10** | PRD section 7 | Layer 4, surfaces and platform |
| **N1 to N12** | PRD section 8 | non-functional requirements |
| **U1 to U12** | PRD section 9 | the design system |
| **ADR-NNNN** | `adr/` | code-shape decisions, kept current and edited with dated change notes |
| **MAP-NNN** | `tasks/` | the spec-per-task an implementing window reads, one file per Linear issue that needs one |
| **SP-N** | `spikes/` | risk spikes, throwaway code and a surviving ADR |
| **MC-01 to MC-05** | `market-reserarch.md` | market codes standing in for competitor names |
| **FAM-xx, REQ-xx, Z.x, DEV-A/B/C** | `market-reserarch.md` | the reverse-engineered competitor catalog those codes index |

A bare "section N" always means the foundation unless it is written as "PRD section N" or names another document.

---

- **`mapsift-foundation.md`** — the constitution and single source of truth: the what and the why, the
  invariants (I1 to I11, each with a scar), and the open-question log (OQ-1 to OQ-24). Every other document
  derives from it and must not contradict it.
- **`PRD.md`** — the product requirements, one layer above code (the how). Derives from the foundation; turns
  closed decisions into pass/fail requirements and marks open questions as gaps. Drafted: Layer 1 (native
  capability floor), the anti-requirements, the extension catalog, Layer 2 (transversal system behaviors,
  T1 to T9), Layer 3 (data model and contracts, M1 to M16), Layer 4 (surfaces and platform, S1 to S10), the
  non-functional requirements (N1 to N12), and the design system (U1 to U12). The prose is complete; section 10
  is the document's own gap list (decisions, artifacts, and measurements).
- **`tasks/`** — the spec-per-task the authority chain ends at, one file per Linear issue that needs one, named
  by its issue ID. It **assembles and cites** what the foundation, the PRD and the ADRs already decided into the
  one contract two windows read, and it decides nothing of its own; where it disagrees with a document it cites,
  the cited document wins. Not every issue needs one: it earns its place when the requirements an implementer
  must hold at once are spread across several documents. On disk:
  - **`tasks/README.md`** — the shape of one of these files and the two rules that make it worth having: it
    cites and never restates, and it is written at pickup rather than at backlog creation, because task specs
    written twenty at a time go stale before anybody reads them.
  - **`tasks/MAP-3-account-tree.md`** — the first product code in the repository: the five entities of M1, the
    tenant identifier, and the ADR-0005 wall in the same migration, with the split between what window A tests
    and what window B implements written out.
  - **`tasks/MAP-5-layers-and-features.md`** — the layer and the feature as persisted shapes, with the storage
    class that decides whether a feature enters the operation queue at all (M2), the geometry in the M5 storage
    frame, and both tables inside the same wall. It scopes the slice explicitly (the attribute schema, the
    legal-weight marker, style and import provenance are each deferred with the owner that holds them) and
    carries the two things reading the code found: `Project` lacks the `UNIQUE (tenant_id, id)` a composite
    reference needs, and `django.contrib.gis` is absent from `INSTALLED_APPS` while the engine is already the
    PostGIS backend.
  - **`tasks/MAP-7-operation-envelope.md`** — the envelope of M8 as a generated cross-language contract, with
    the acceptance split between what a Rust test can pin and what only the generated Python and TypeScript
    forms can, and the ADR-0009 section 5 guard rules carried as part of the task's acceptance.
  - **`tasks/MAP-8-operation-catalog.md`** — the closed operation catalog of M9 and the one target path per
    operation, whose review turned the type-to-target-kind pairing from a metadata reading into structural
    contract and sharpened M9's acceptance in the process.
  - **`tasks/MAP-9-version-axes.md`** — the five version axes of M10 as five types rather than five field
    names, and the per-project version reaching code for the first time. Its evidence block is the worked
    example of the rule this folder's README states: a handed-over measurement was generalized past the
    configuration it was taken in, and the block was rewritten mid-task rather than left to be believed.
  - **`tasks/MAP-27-login-membership-policy.md`** — the login question answered without a hole in the wall,
    the single deliberate exception ADR-0005 section 8 names, `FOR SELECT` only.
- **`spikes/`** — the plan for each risk spike: the question it answers, the harness, the pass/fail exit criteria,
  and what it delivers. Spike code is throwaway; what survives is the ADR and the numbers. On disk:
  - **`spikes/SP-1-postgres-ordered-sync.md`** — **closed 2026-07-31.** Answered foundation OQ-10 and the
    resync-cursor hole it exposed in PRD M10, in two stages (the database ordering strategy first, with a negative
    control that had to catch the known sequence trap, then the protocol loop under deliberate chaos). The plan
    stays on disk so a reader can check that what ran is what was planned; the decision lives in ADR-0004.
- **`testing.md`** — the canonical method document: Red/Green/Refactor in two clean-context windows, behaviour over
  implementation, the decision-versus-effect split that makes it possible, the kinds of test in this project
  (including the shared cross-runtime golden corpus and why measurements are not CI gates), where tests live,
  and the traceability rule from a requirement ID to a test. **Section 1.1 is the contract every window brief
  satisfies** and **1.2 is why sizing the slice is a first-class step** rather than something discovered
  afterwards. Read before writing any test or any code.
- **`dependencies.md`** — the dependency survey: the canonical home for external-dependency versions and for the
  particularity of each one that bites, serving the external-dependency rule. Distinguishes a **ratified choice**
  from a **pinned version** (only a lockfile pins), carries a verification date on every claim, and ends with the
  dependency-gated ADR agenda.
- **`data-and-tooling-references.md`** — the reference catalog for the test corpus (data sources, formats,
  CRS, fixtures) and for per-tool expected behavior (the analysis tools' canonical docs and the CRS rule). A
  reference, not a test plan; the test plan points here.
- **`domain-questions.md`** *(internal, kept out of version control since 2026-08-01, like the market research)* — the questions whose owner is the domain authority rather than software engineering, each one blocking a decision the canon deliberately left open (OQ-8, OQ-5, OQ-1's exit criterion, OQ-11, OQ-12, OQ-20, and the PRD J2 acceptance). Written to be answered asynchronously: every item carries what is **verified** with its source, the **proposal** the software side offers for confirmation or correction, and what is explicitly **not pinned**, so nobody confirms something the software side invented. It asks and decides nothing; the answers close their OQs by the normal fan-out. **It is the one document in `specs/` written in Brazilian Portuguese, and the exception is written rather than assumed** in its own header: the reader is the Brazilian specialist, the norms it cites are in Portuguese, and round-tripping terms like "área de uso consolidado" through English introduces error in the document that arms legal weight. The answers enter the canon in English. It also carries **section V, the verification of the answer round against primary sources**, which is where a claim is graded before it is allowed into the canon; one input failed that grading and did not enter.
- **`session-handoff.md`** *(internal, kept out of version control since 2026-08-01)* — bootstraps a fresh clean-context session with the working context that lives
  outside the foundation and PRD: the method, the empirical base, the settled objections, the governance
  discipline, the Linear workflow, and the .claude inheritance discipline. Section 0 is the live state, updated
  each window.
- **`log.md`** — a grep-able derived index of the foundation's section 15 changelog plus the closed decisions
  that did not bump the foundation. Not a source of truth; the foundation's changelog is.
- **`market-reserarch.md`** — the internal market-research document that defines the MC-xx codes the specs use
  in place of competitor names. Internal by nature and kept out of version control (the on-disk filename
  carries the historical misspelling `reserarch`, referenced as-is by the foundation and CLAUDE.md).
- **`adr/`** — code-shape decisions in Context/Decision/Consequences form, numbered `NNNN-kebab-title.md`. An
  ADR is kept current: a changed decision is edited in place with a dated note of what changed and why
  (convention revised 2026-08-05 in ADR-0001). On disk:
  - **`adr/0001-architecture-baseline.md`** — the immutable baseline the scaffold is created from: the repository
    layout by unit of deploy, the language roles, containerised from the first commit, configuration and secrets,
    generated contracts, the CI gates, test placement, and the explicit list of what must not be scaffolded yet
    with the gate that unlocks each. It states the ADR conventions, being the first one.
  - **`adr/0002-code-layout-and-generation.md`** — code shape inside a stack: CLI-first generation in every
    stack, the Angular component file layout with its bounded inline exception, the countable folder-split
    threshold, naming from the installed schematic, and the three-level split between the ADR (the decision),
    the path-scoped `.claude/rules/*.md` (the enforcement), and a per-stack `CLAUDE.md` (operational residue,
    after the scaffold).
  - **`adr/0003-angular-project-conventions.md`** — the Angular decisions that are Mapsift's own rather than the
    official style guide restated: every feature route lazy loaded, signal-based data access as the default with
    `HttpClient` as the exception, one forms API per surface with an interim no-mixing rule, and library imports
    from the barrel only. Draws the line between citing an external authority and taking a decision.
  - **`adr/0004-sync-ordering-strategy.md`** — the ordering strategy the SP-1 spike decided: the per-project
    version, chosen on failure mode rather than throughput, with the two engineering rules that are part of the
    decision (allocate the whole range in one statement, take the allocation last), the eliminated candidates and
    why, and the two conditions that would bring the rejected one back. Delivers the spike's exit and the fifth
    version axis PRD M10 had declared missing.
  - **`adr/0005-tenant-isolation-and-the-tile-session.md`** — the I4 wall as it is actually built: row-level
    security with per-tenant views rejected, four unprivileged roles with `BYPASSRLS` granted to none, the
    tenant bound transaction-scoped and parameterised through a guarded cast, composite keys closing the
    referential-integrity channel that no policy closes, and the contract any tile server must satisfy to
    carry a verified tenant into its own database session. Its defeat conditions were measured against
    PostgreSQL 18.4 rather than argued, and the measurements are in the ADR.
  - **`adr/0006-client-generated-identifier-variant.md`** — the client-minted identifier is a random 128-bit
    value rather than a time-ordered one, decided on a measurement that inverted the expected trade: the index
    locality a time-ordered identifier buys is contingent on the device clock being right, and with a fifth of
    the rows minted on a skewed clock the index came out 2.45 times the well-behaved ordered one and roughly
    twice the random one. Also records that a time-ordered identifier is not opaque, since PostgreSQL reads
    its creation instant back out, which M3 forbids and N9's logging path would carry everywhere.
  - **`adr/0007-api-layout-and-the-dependency-direction.md`** — where a file goes in `apps/api` and what it may
    import: one application package `mapsift/` with a subpackage per domain and never per layer, `config/` never
    holding domain code, the per-package file roles (`rules.py` pure, `selectors.py` reads, `services.py` writes,
    `capabilities.py` the published surface, one django-ninja `api.py`), the tier direction enforced by an
    `import-linter` contract rather than by a reviewer, and the home a named capability gets before the first one
    exists. Fires the trigger ADR-0002 section 5 named for itself.
  - **`adr/0008-development-workflow-and-tracking.md`** — the working method as one decision: git owns the
    contract and Linear owns execution state bridged by the task identifier, what may become an issue and what
    one issue is, the personal-workspace team structure with its labels, the two-window protocol under an
    orchestrator with sequential dispatch (the method itself stays in `specs/testing.md` section 1), the rule
    that a skill injects the spec it depends on, the one-pull-request rule for crossing changes, the refusal
    of autonomous issue-to-pull-request automation with its reopening gate, and worktrees for parallel work.
  - **`adr/0009-type-generation-toolchain.md`** — the envelope contract's generation toolchain, decided after
    a verification round refuted two survey assumptions: Rust is the single source; schemars pinned to JSON
    Schema 2020-12 emits the schema; datamodel-code-generator generates the Pydantic v2 model with its native
    check as the CI freshness gate; tsify lands the named TypeScript in the wasm-pack pkg with ts-rs into
    `libs/contracts` as the recorded exit path; the OpenAPI side references the core-generated type and never
    redeclares it; the Dart half stays open on the `apps/mobile` trigger.
