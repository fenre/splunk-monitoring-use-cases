# Roadmap

> The plan below is indicative, not contractual. Dates can slip; priorities
> can change based on user feedback and contributor bandwidth. The **source of
> truth** for *what has shipped* is [`CHANGELOG.md`](CHANGELOG.md).

## Current release

**v7.1 — Non-Technical Everywhere** *(shipped 2026-04-20)*

Theme: **"every use case is explainable without jargon, everywhere, in
one sentence."** v7.1 extends v7.0's per-UC content architecture with a
first-class plain-language summary on every UC and a wholesale rewrite
of the non-technical UI so that toggle hides *all* technical chrome
behind a single disclosure.

- New required-at-runtime `grandmaExplanation` field on every UC
  sidecar (schema v1.5.0, 20–400 chars, `we` voice, no Splunk/SPL/CIM/
  MITRE/TA acronyms) — populated deterministically by
  [`scripts/generate_grandma_explanations.py`](scripts/generate_grandma_explanations.py)
  from the existing title/description/value copy
- Non-technical view now renders `grandmaExplanation` as the primary
  UC text on UC cards, search results, subcategory lists, recently-added,
  and at the top of the UC detail panel; technical sections (SPL, CIM,
  MITRE, data sources, etc.) collapse behind a single *Show technical
  details* disclosure that follows the mode toggle
- Sidebar subcategory clicks and hash deep-links stay in non-technical
  mode (new `renderNonTechnicalSubcategory` path + `restoreFromHash`
  fixes); UC rows in non-technical area lists are now clickable and
  prefer the per-UC `ge` over curated `why` copy
- CI guard: `scripts/generate_grandma_explanations.py --check` runs on
  every PR and blocks merge if any UC sidecar is missing the field
- Runtime fallback in `build.py` for markdown-only UCs so the UI never
  shows an empty plain-language card even before a UC sidecar lands
- Authoring and maintenance guide at [`docs/grandma-explanations.md`](docs/grandma-explanations.md);
  full narrative in [`docs/v7.1-release-report.md`](docs/v7.1-release-report.md)

See [`CHANGELOG.md`](CHANGELOG.md) for the full v7.1 release notes.

### Shipped outcomes

- Non-technical users see a coherent jargon-free summary on every UC
  surface, not just the subset (~10 %) previously covered by curated
  `why` lines
- The technical view is unchanged — collapsed sections expand by default,
  preserving the v7.0 detail panel layout
- Drift is impossible: adding a UC without regenerating plain-language
  copy fails CI before merge

---

## Previous releases

**v7.0 — Per-UC Content Architecture** *(shipped 2026-04-19)*

Theme: **"every use case is its own file, every build is reproducible,
every URL is permanent."**  v7.0 replaced the monolithic per-category
markdown files with individually authored per-UC file pairs and
introduced a Python stdlib-only build pipeline that generates the
entire site from source.

- 23 monolithic `cat-*.md` files exploded into 6,449 individual
  `content/cat-NN-slug/UC-X.Y.Z.md` prose files paired with 6,470
  `UC-X.Y.Z.json` structured-metadata sidecars
- New build pipeline (`tools/build/build.py`) — single Python 3.12
  entrypoint, no Node/npm, reproducible builds with Sigstore attestation
- Extracted source assets (`src/styles/`, `src/scripts/`) with content-hash
  fingerprinting and immutable cache headers
- Sharded full-text search (16 MiniSearch shards, ~100 KB each) replacing
  the 39 MB linear scan over `data.js`
- CI quality gates (`tools/audits/`) — asset drift, bundle budgets,
  schema-diff, schema-meta, URL-freeze
- New schemas (`schemas/v2/`) — `catalog-index` and `search-index`
- Architecture contract (`docs/architecture.md`), URL scheme
  (`docs/url-scheme.md`), schema versioning (`docs/schema-versioning.md`)
- 6,447 UCs across 23 categories

**v6.1 — Verifiable Compliance Coverage** *(shipped 2026-04-16)*

- Six-phase regulation-coverage gap closure; 100% clause coverage on
  tier-1 + tier-2 frameworks
- Phase 5.5 structured equipment tagging on every cat-22 UC
- Phase 6 MCP server (`splunk-uc-mcp`) with eight read-only tools
- Regulatory primer reader (`regulatory-primer.html`)
- Branding updated to "Community Reference"
- Catalogue grew 6,424 → 6,447 UCs

**v6.0 — Verifiable Quality** *(shipped 2026-04-16)*

Theme: **"trust but verify"** — every shipped SPL should be demonstrably
correct and every quality signal transparently measured.

- Sample-event fixtures ([`samples/`](samples/)) with JSON-Schema-validated
  manifests — 15 golden fixtures at launch, expanding throughout v6.x
- UC test harness ([`scripts/run_uc_tests.py`](scripts/run_uc_tests.py))
  ingests samples via HEC, runs each UC's SPL in an ephemeral Splunk 9.4
  container, asserts on results, emits JUnit XML
- End-to-end CI workflow ([`.github/workflows/uc-tests.yml`](.github/workflows/uc-tests.yml))
- Splunk Cloud compatibility audit — see
  [`docs/splunk-cloud-compat.md`](docs/splunk-cloud-compat.md) for the
  rolling report (0 pack-level findings, 5 SPL-level warnings)
- Provenance ledger — 9-way source classification on every UC, rendered as
  a colour-coded dashboard badge (see
  [`docs/provenance-coverage.md`](docs/provenance-coverage.md))
- Quality scorecard — per-category Gold/Silver/Bronze letter grades across
  six quality dimensions (see [`docs/scorecard.md`](docs/scorecard.md))
- Two new API endpoints: `GET /provenance.json`, `GET /scorecard.json`
- OpenAPI spec bumped to 6.0.0

**v5.2 — Enterprise Packaging** *(shipped 2026-04-16)*

- Three Splunkbase-ready content packs: TA, ITSI, ES
- OpenAPI 3.1 spec + Swagger UI (self-hosted)
- Automated release workflow (`.github/workflows/release.yml`)
- Enterprise deployment guide
- Cross-cutting governance scaffolding (this document, `GOVERNANCE.md`,
  `CODE_OF_CONDUCT.md`, `SECURITY.md`, `CODEOWNERS`, PR/issue templates,
  `CITATION.cff`)

**v5.1 — Gold Standard Quality Pass** *(shipped 2026-04-16)*

- 100 % references coverage across 6,304 UCs
- 100 % KFP coverage on security categories
- MITRE ATT&CK coverage ≥80 % on security categories
- Weekly link-check workflow
- Per-UC quality metadata chips (Status, Last reviewed, Splunk versions)

See [`CHANGELOG.md`](CHANGELOG.md) for full release notes.

---

## Next up: v7.2 — Expand & Refine *(no fixed date)*

With the v7.0 per-UC architecture and the v7.1 non-technical rewrite in
place, the v7.2 focus shifts to **raising the scorecard grades** and
completing the SSG page generation — most categories currently sit in
"Needs work" because KFP, MITRE mappings, reviewed-dates and sample
fixtures haven't been authored for non-security UCs.

### Content + tooling work targeted for v7.2

- **Top-200 sample-event coverage** — Expand the `samples/` tree from 15
  fixtures to 200, targeting the most-used UCs identified by dashboard
  analytics. Goal: every Quick-Start UC has an authoritative fixture.
- **Scorecard targets** — Push at least 5 categories into **Silver** and
  push the current 3 Silver categories into **Gold** by backfilling KFP,
  MITRE mappings, reviewed-dates and sample coverage.
- **Test-harness scale** — Parallelize `run_uc_tests.py` and cache
  Splunk Docker images to keep the full-suite CI run under 15 minutes
  as fixture count grows.
- **Provenance refinement** — Drive the 2.4 % "unclassified" bucket below
  1 % by extending the host-rule allow-list and adding a heuristic
  fallback that inspects URL path/title.
- **Phase E SME-uplift continuation** — Walk the remaining tier-1 +
  tier-2 clause coverage entries from `assurance: contributing` to
  `partial` / `full` via SME judgment.  Phase E v6.1 lifted global
  assurance-adjusted coverage to 59.89 %; the realistic v7.2 target is
  ≥75 % tier-1 / ≥55 % tier-2 without artificial uplift.
- **`grandmaExplanation` hand-polish pass** — Deterministic generator
  text is "good enough to ship"; v7.2 adds a curator review loop to
  raise quality (voice, warmth, concreteness) on the 500 most-viewed
  UCs without regenerating the rest.

---

## v7.3+ backlog *(no fixed date)*

The following ideas are under consideration but not yet scheduled. Pull
requests or issues advocating for any of them are welcome.

### Content

- **Industry-specific bundles** — Standalone content packs for Finance, OT,
  Healthcare, Public Sector (subset of existing UCs plus industry-specific
  framework mappings).
- **Cloud-provider deep dives** — Expand cat-4 with dedicated subcategories
  per provider (AWS/Azure/GCP) at the same depth as cat-10.
- **AI / LLM observability** — Dedicated subcategory under cat-13 covering
  prompt injection, token-cost monitoring, RAG retrieval quality, drift
  detection.
- **OCSF parity** — Second set of normalised SPL that produces OCSF-format
  output alongside the existing CIM-format queries.

### Tooling

- **CLI** — `pip install splunk-monitoring-use-cases` giving a `suc` CLI to
  query the catalog locally, export UC subsets, generate custom TAs for a
  specific category.
- **Terraform provider** — Declarative UC management for customers that manage
  Splunk via IaC.
- **VS Code extension** — Autocomplete for UC IDs, hover for UC summaries,
  quick-insert of SPL snippets into `.spl` or SPL scratch files.
- **MCP server (`splunk-uc-mcp`) — follow-ups after Phase 6.** Publish
  `splunk-uc-mcp` to PyPI (currently installed from source via
  `pip install -e mcp/`), add HTTP streaming transport as an opt-in for
  remote single-tenant deployments (stdio stays the default and the
  recommended mode per CoSAI guidance), expose a `list_mitre_techniques`
  tool (currently only filterable, not enumerable), add a
  `subscribe_use_cases` streaming resource so long-running agent sessions
  can be notified of new catalogue commits, and wire structured prompts
  (MCP `prompts/`) for the two canonical personas (compliance officer,
  detection engineer).

### Community & process

- **Translations** — `custom-text.js` is designed to allow UI translation;
  pilot translation to one additional language (likely Norwegian or German).
- **Contribution gamification** — Recognize top contributors per quarter in
  release notes; badges on the dashboard.
- **Monthly community call** — Public 30-minute call to review the roadmap,
  discuss RFCs, and onboard new contributors.

---

## Deprecated / declined ideas

Some things we have *decided not* to build. Each entry is linked to the issue
or discussion where the decision was made (once those exist).

- **Hosted SaaS** — The project stays static-site-first. Anyone can fork and
  host; we won't run infrastructure.
- **Commercial edition** — No paid tier, no premium content pack. Everything
  in the project is MIT-licensed.
- **Generated SPL by LLM** — We accept AI-assisted *authoring* via pull
  requests that are reviewed by humans, but we will not auto-publish LLM
  output to the catalog.

---

## How to influence the roadmap

- **Vote** with 👍 on existing issues.
- **Propose** new items by opening an issue with the `enhancement` label.
- **Advocate** for a backlog item by picking it up — maintainers prioritize
  items with active contributors.

See [`GOVERNANCE.md`](GOVERNANCE.md) for the full decision-making process.
