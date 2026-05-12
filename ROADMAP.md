# Roadmap

> The plan below is indicative, not contractual. Dates can slip; priorities
> can change based on user feedback and contributor bandwidth. The **source of
> truth** for *what has shipped* is [`CHANGELOG.md`](CHANGELOG.md).

## Current release

**v8.2.0 — Scripts Taxonomy Closed** *(shipped 2026-05-11)*

Theme: **`scripts/` is no longer the canonical entry point.** v8.2.0
closes the Phase 6 "scripts taxonomy" rebuild — every recurring script
under `scripts/` previously had a sibling implementation under
`src/splunk_uc/` plus a thin compatibility shim. With the dispatcher
exercised continuously by CI, the shims are now retired and the
package is the single Python surface.

- **`python -m splunk_uc <verb>`** is the single dispatcher for 83
  audits / generators / ingestors / migrations / feasibility tools /
  utilities. The 85 sibling shims under `scripts/` were deleted in
  one pass.
- **`splunk-uc` console script** wired via `pyproject.toml`
  (`[project.scripts]`); `pip install -e .` exposes the CLI globally.
  Tier 4 packaging shape lives at
  `[tool.hatch.build.targets.wheel].packages = ["src/splunk_uc"]`.
- **128 callers rewired in one pass** — workflows, Makefile,
  pre-commit hook, MCP server, tests, docs, templates,
  `AGENTS.md` / `README.md` / `CONTRIBUTING.md`.
- **76 deliberate Python files** remain in `scripts/` — underscore-
  prefixed one-shots, content-burndown helpers, gitignored Splunk-
  deployment generators, doc generators. All catalogued in
  [`docs/scripts-taxonomy.md`](docs/scripts-taxonomy.md).
- **F1 / F2 / F3 / F4 / F6 / F7 / F9 / F11 / F15** from the
  [`Repo Health Check plan`](docs/health-check-2026-progress.md) all
  resolved at v8.2.0 (with F7 closed 2026-05-12).

See [`CHANGELOG.md`](CHANGELOG.md) for the full v8.2.0 release notes
and the v8.0 → v8.2 line.

### Shipped outcomes

- One canonical CLI entry point (`splunk-uc <verb>`) for the entire
  build / audit / generate / ingest surface; legacy `python3
  scripts/foo.py` invocations no longer work.
- Foundation in place for `mypy --strict` ratchets and a future PyPI
  publish (the latter is P9 work; the infrastructure is ready).
- The catalog now counts **7,677 UCs** across **23 categories /
  239 subcategories / 69 mapped regulations / 106 equipment slugs /
  18 schemas**.

---

## Previous releases

**v7.1 — Non-Technical Everywhere** *(shipped 2026-04-20)*

Theme: **"every use case is explainable without jargon, everywhere, in
one sentence."** v7.1 extends v7.0's per-UC content architecture with a
first-class plain-language summary on every UC and a wholesale rewrite
of the non-technical UI so that toggle hides *all* technical chrome
behind a single disclosure.

- New required-at-runtime `grandmaExplanation` field on every UC
  sidecar (schema v1.6.1, 20–400 chars, `we` voice, no Splunk/SPL/CIM/
  MITRE/TA acronyms) — populated deterministically by
  `python3 -m splunk_uc generate-grandma-explanations` from the
  existing title/description/value copy
- Non-technical view now renders `grandmaExplanation` as the primary
  UC text on UC cards, search results, subcategory lists, recently-added,
  and at the top of the UC detail panel; technical sections (SPL, CIM,
  MITRE, data sources, etc.) collapse behind a single *Show technical
  details* disclosure that follows the mode toggle
- CI guard: `python3 -m splunk_uc generate-grandma-explanations --check`
  runs on every PR and blocks merge if any UC sidecar is missing the
  field
- Authoring and maintenance guide at
  [`docs/grandma-explanations.md`](docs/grandma-explanations.md); full
  narrative in [`docs/v7.1-release-report.md`](docs/v7.1-release-report.md)

**v7.0 — Per-UC Content Architecture** *(shipped 2026-04-19)*

Theme: **"every use case is its own file, every build is reproducible,
every URL is permanent."**  v7.0 replaced the monolithic per-category
markdown sources with individually authored per-UC file pairs and
introduced the current Python stdlib-only build pipeline (`tools/build/build.py`, `make build`).

- 23 monolithic `cat-*.md` files exploded into 6,449 individual
  `content/cat-NN-slug/UC-X.Y.Z.md` prose files paired with 6,470
  `UC-X.Y.Z.json` structured-metadata sidecars
- New build pipeline (`tools/build/build.py`) — single Python 3.12
  entrypoint, no Node/npm, reproducible builds with Sigstore attestation
- Extracted source assets (`src/styles/`, `src/scripts/`) with content-hash
  fingerprinting and immutable cache headers
- Sharded full-text search (16 MiniSearch shards, ~100 KB each) replacing
  the legacy linear scan over a single giant `data.js` payload
- CI quality gates (`tools/audits/`) — asset drift, bundle budgets,
  schema-diff, schema-meta, URL-freeze
- New schemas (`schemas/v2/`) — `catalog-index` and `search-index`
- Architecture contract (`docs/architecture.md`), URL scheme
  (`docs/url-scheme.md`), schema versioning (`docs/schema-versioning.md`)
- The catalog counted **7,364** UCs across 23 categories at v7.0 ship *(see [`CHANGELOG.md`](CHANGELOG.md); current count at HEAD is 7,677 — see the v8.2.0 entry above)*

### v6.x — monolithic markdown pipeline *(historical)*

The v6 line used per-category markdown under `use-cases/` and the root `build.py` workflow. It is **retired** in favour of **`content/` + `tools/build/build.py`** above.

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
- MITRE ATT&CK<sup class="ref">[<a href="#ref-3">3</a>]</sup> coverage ≥80 % on security categories
- Weekly link-check workflow
- Per-UC quality metadata chips (Status, Last reviewed, Splunk versions)

See [`CHANGELOG.md`](CHANGELOG.md) for full release notes.

---

## Next up: v8.3 — Gold Standard content uplift continues *(in progress)*

> The Gold Standard infrastructure shipped progressively over v7.2 →
> v7.4.x → v8.0; the *content* uplift itself is a continuous program
> that runs in parallel with platform work. Current distribution as of
> 2026-05-12: 724 Gold (9.4%) / 38 Silver (0.5%) / 6,106 Bronze (79.5%)
> / 809 below profile (10.5%) across 7,677 UCs. The goal is to grow
> Gold and Silver year-over-year while keeping the non-blocking
> summary gate visible in CI (see `audit-gold-profile --summary` in
> `validate.yml`). The platform infrastructure side of v8.3 is the
> [Repo Health Check plan](docs/health-check-2026-progress.md) work,
> tracked separately; this section covers the content side.

With the v7.0 per-UC architecture and the v7.1 non-technical rewrite in
place, **this program elevates content quality across the entire catalog**
to match the standard set by the Catalyst Center<sup class="ref">[<a href="#ref-2">2</a>]</sup> subcategory (5.13). The guiding
principle: *quality is operational utility, not field-count compliance;
fewer excellent UCs beat many shallow ones.*

### Gold Standard initiative

The Gold Standard defines tiered quality profiles (Gold / Silver / Bronze)
based on **operational completeness** — can someone implement a UC end-to-end
from this page alone?

Infrastructure shipped:
- **Quality profile schema** (`schemas/uc-profile-gold.json`) — tiered
  requirements emphasizing depth and product-specific detail
- **Template guide** (`docs/gold-standard-template.md`) — the quality
  contract: 5-step structure, anti-patterns, exemplar UC-5.13.1
- **Cursor authoring rule** (`.cursor/rules/gold-standard-authoring.mdc`) —
  AI authoring contract guiding agents to product-specific depth, not
  template filling
- **Depth audit** (`python3 -m splunk_uc audit-gold-profile`) — quality gate measuring
  substance, detecting shallow boilerplate and consolidation candidates
- **Build-time quality scores** — per-UC depth score and tier with actionable
  gap descriptions injected by `parse_content.py`, aggregated per subcategory
- **UI quality indicators** — depth badges on UC cards, quality progress bars
  on subcategory cards, quality gaps in the detail panel, category quality
  summaries, and a dedicated Quality review tab
- **Scorecard integration** — content depth is now a 20% weighted dimension
  in `generate_scorecard.py`
- **Markdown generation** (`python3 -m splunk_uc generate-md-from-json`) — JSON is the
  single source of truth; companion `.md` under `content/`, when present, is optional

### Content uplift workflow

Each subcategory is uplifted via Cursor agent sessions, branch per
subcategory, human review via PR:

1. Agent reads subcategory context and assesses holistically
2. Agent consolidates redundant UCs and deepens remaining ones
3. `audit_gold_profile.py` validates depth and flags gaps
4. PR review ensures product knowledge accuracy

### Ongoing content-uplift targets

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
  assurance-adjusted coverage to 59.89 %; the current target is
  ≥75 % tier-1 / ≥55 % tier-2 without artificial uplift.
- **`grandmaExplanation` hand-polish pass** — Deterministic generator
  text is "good enough to ship"; the curator review loop raises
  quality (voice, warmth, concreteness) on the 500 most-viewed UCs
  without regenerating the rest.

---

## v8.4+ backlog *(no fixed date)*

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

---

<!-- BEGIN-AUTOGENERATED-SOURCES -->

## References

*Auto-generated by `scripts/generate_doc_references.py` from `data/source-references.json` and `data/source-mappings.json`. Edit those files (or the document body) to change citations; this footer is rewritten on every run.*

### Supporting sources

<a id="ref-1"></a>**[1]** Anthropic, et al. (2026). *Model Context Protocol Specification*. Anthropic PBC. Retrieved May 11, 2026, from https://modelcontextprotocol.io/

<a id="ref-2"></a>**[2]** Cisco Systems, Inc. (2026). *Cisco Catalyst Center Documentation*. Retrieved May 11, 2026, from https://www.cisco.com/site/us/en/products/networking/catalyst-center/index.html

<a id="ref-3"></a>**[3]** MITRE Corporation. (2026). *MITRE ATT&CK Knowledge Base*. MITRE Engenuity. https://attack.mitre.org/

<a id="ref-4"></a>**[4]** Splunk Inc. (2026). *Search Reference: SPL Commands and Functions*. Splunk LLC, a Cisco company. Retrieved May 11, 2026, from https://docs.splunk.com/Documentation/Splunk/latest/SearchReference/WhatsInThisManual

<a id="ref-5"></a>**[5]** Splunk Inc. (2026). *Splunk Cloud Platform Documentation*. Splunk LLC, a Cisco company. Retrieved May 11, 2026, from https://docs.splunk.com/Documentation/SplunkCloud

<a id="ref-6"></a>**[6]** Splunk Inc. (2026). *Splunk IT Service Intelligence Administration Manual*. Splunk LLC, a Cisco company. Retrieved May 11, 2026, from https://docs.splunk.com/Documentation/ITSI

### Cited by

- [`docs/enterprise-deployment.md`](docs/enterprise-deployment.md)

<!-- END-AUTOGENERATED-SOURCES -->
