# Roadmap

> The plan below is indicative, not contractual. Dates can slip; priorities
> can change based on user feedback and contributor bandwidth. The **source of
> truth** for *what has shipped* is [`CHANGELOG.md`](CHANGELOG.md).

## Current release

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

See [`CHANGELOG.md`](CHANGELOG.md) for the full v6.0 release notes.

### Shipped outcomes

- Every Quick-Start UC with a fixture passes automated SPL execution tests
- No regressions introduced by SPL refactors go undetected
- Users can quickly judge the quality / maturity of any given category
- Splunk Cloud customers know in advance what works and what needs tuning

---

## Previous releases

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

## Next up: v6.1 — Expand & Refine *(target: 2026-Q3)*

Building on the v6.0 foundation, the v6.1 focus is **raising the scorecard
grades** — most categories currently sit in "Needs work" because KFP, MITRE
mappings, reviewed-dates and sample fixtures haven't been authored for
non-security UCs.

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

---

## v6.2 – v6.x backlog *(no fixed date)*

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
