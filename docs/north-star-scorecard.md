# North-star scorecard

> **Audience.** Maintainers, contributors planning where to invest the
> next quarter, and external readers calibrating how seriously to take
> each long-arc goal in [`ROADMAP.md`](../ROADMAP.md).

> **Cadence.** Refreshed quarterly. The scoring is deliberately
> coarse (1–5 per goal); the value is in the trend across quarters,
> not in any single point-in-time number.

This document is the project's self-assessment against seven long-arc
goals. It is **not** the per-UC content quality scorecard
([`docs/scorecard.md`](scorecard.md)) — that one measures whether each
use case is gold/silver/bronze. This one measures whether the project
itself is achieving its strategic goals.

## Why these seven

The seven north-star goals are the answer to "what does the catalogue
need to be in five years?" — written down so each PR, audit, and
roadmap decision can be checked against them. They are picked to
cover the whole project surface:

- **Goals 1, 2, 3** cover the *content* dimension: trust, AI substrate,
  compliance source of truth.
- **Goal 4** covers the *engineering* dimension: reproducibility.
- **Goals 5, 6, 7** cover the *project* dimension: multi-language,
  navigable layout, forkability.

Adding an eighth goal requires an ADR. Removing or renaming one of
the seven also requires an ADR.

## Scoring rubric

Each goal is scored 1–5 against criteria specific to that goal
(defined inline below). The rubric is intentionally loose — the
trend across quarters is what matters.

| Score | Generic meaning |
|---|---|
| **5** | World-class. The project is the reference implementation other projects copy. |
| **4** | Strong. We meet the standard, with named gaps that are actively closing. |
| **3** | Working. The foundation is in place; quality and reach are the open work. |
| **2** | In progress. Visible commitment, partial implementation, real gaps. |
| **1** | Aspirational. The intent is documented; the work has barely begun. |

Two-decimal averages are reported (e.g. 2.57) so quarter-on-quarter
movement is legible even when individual goals stay flat.

## The seven goals

### 1. The world's most trusted open Splunk use-case catalogue

**What we mean.** Largest, most rigorously-curated, most actively-cited
open catalogue of Splunk use cases — the one a Splunk admin reaches
for first when they need a place to start.

**What moves the score.**

- **5** — The default reference. Splunk's own documentation links to
  us; SI partners use the catalogue as a sales aid; multiple
  organisations cite individual UC IDs in their internal runbooks.
- **4** — > 90 % of UCs at Silver+ in
  [`docs/scorecard.md`](scorecard.md); peer reviewers from outside
  the project actively contribute; coverage gaps named publicly.
- **3** — Largest UC count in the open ecosystem; quality is uneven
  but the gold-standard authoring playbook is enforced for new work.
- **2** — Catalogue exists; quality and curation are not yet
  consistent.
- **1** — Documented intent only.

### 2. AI substrate

**What we mean.** Every UC, regulation, and equipment slug is
machine-readable in the way an LLM (or RAG pipeline, or autonomous
agent) actually wants it: indexed, chunked, embedding-friendly,
benchmarked.

**What moves the score.**

- **5** — Public LLM eval harness with hallucination-rate scorecards,
  prompt-injection canaries, p50/p99/p999 MCP-tool benchmarks, RAG
  chunks pinned to commit; consumed by named third-party agents.
- **4** — All of the above except external-consumer adoption is
  still emerging.
- **3** — `llms.txt`, `llms-full.txt`, `ai.txt`, per-UC `ge` plain-
  language explanations, MCP server with non-trivial tool surface;
  no formal eval harness yet.
- **2** — Some LLM-friendly artefacts exist; coverage is partial
  and inconsistent.
- **1** — Documented intent only.

### 3. Compliance source of truth

**What we mean.** For each tier-1 regulation we cover (GDPR<sup class="ref">[<a href="#ref-2">2</a>]</sup>, HIPAA<sup class="ref">[<a href="#ref-10">10</a>]</sup>,
PCI, SOX<sup class="ref">[<a href="#ref-8">8</a>]</sup>, NIS2<sup class="ref">[<a href="#ref-1">1</a>]</sup>, DORA<sup class="ref">[<a href="#ref-3">3</a>]</sup>, ISO 27001, NIST 800-53, NIST CSF, SOC 2,
UK GDPR<sup class="ref">[<a href="#ref-11">11</a>]</sup>, CMMC), an auditor can pull the evidence pack and verify
that what we claim about the regulation matches the regulatory text
and that what we claim about Splunk's coverage matches the actual
detections.

**What moves the score.**

- **5** — All 12 tier-1 evidence packs reviewed within the last 12
  months by an external legal reviewer; tier-1 assurance-adjusted
  coverage ≥ 90 %; tier-2 ≥ 75 %; quarterly regulatory-change-watch
  reports automated.
- **4** — Tier-1 ≥ 75 % assurance-adjusted, tier-2 ≥ 55 %; legal
  reviewer in place; primer freshness < 12 months.
- **3** — Cat-22 carries 1,000+ UCs across all 12 tier-1
  regulations; evidence packs exist; assurance-adjusted coverage
  in the 50–75 % band on tier-1.
- **2** — Cat-22 exists with mixed depth; primer hooks present but
  legal review intermittent.
- **1** — Cat-22 is mostly stub UCs.

### 4. Reproducible build

**What we mean.** `make build` produces byte-identical output across
runs given identical input. Sigstore attestation chains are
verifiable end-to-end. Consumers can pin a commit and prove what
they got.

**What moves the score.**

- **5** — All ~32,000 build artefacts byte-identical across runs;
  CI gate enforces it on every PR; Sigstore attestation verified
  for every release; documented bisect path for any drift.
- **4** — > 99 % of artefacts byte-identical; the residue (e.g.
  `BUILD-INFO.json` timestamp, MiniSearch shard ordering) is
  named, tracked, and bounded.
- **3** — The load-bearing artefacts (`catalog.json`,
  `llms*.txt`, `data.js`) are byte-identical and gated by parity
  tests. Other artefacts drift across runs.
- **2** — Builds work; reproducibility is incidental, not gated.
- **1** — Builds depend on transient state (PATH, time, network).

### 5. Multi-language

**What we mean.** A non-English-speaking Splunk admin can read the
catalogue, file PRs, and consume the JSON API in their language
without losing fidelity to the SPL or the regulatory text.

**What moves the score.**

- **5** — At least three languages in production with curator-
  reviewed translations; UI strings localised; MCP `lang` parameter
  honoured; per-language SEO; native-speaker proofread on
  cat-22 tier-1.
- **4** — Two languages in production; translation pipeline
  documented and enforced; English remains canonical.
- **3** — One non-English language shipped, even if partial.
- **2** — Schema hooks (`n_lang`, `v_lang`) documented; pipeline
  prototype exists; no production language ships.
- **1** — Documented intent only.

### 6. Navigable monorepo

**What we mean.** A new contributor opening the repo for the first
time finds what they're looking for in three clicks. Each top-level
directory has a single, obvious purpose. Tooling builds, tests,
and lints are uniform across the tree.

**What moves the score.**

- **5** — Clean `apps/` × `packages/` × `content/` split; one
  build orchestrator (Turborepo, Nx, or `make` workspaces);
  one test runner per language; CONTRIBUTING walks new
  contributors through it; CODEBASE-DIAGRAM still accurate.
- **4** — Most of the structural reorganisation is done; one or
  two legacy directories remain in transition.
- **3** — `pyproject.toml` exists, devcontainer exists, CI gates
  exist. `tools/build/`, `scripts/`, `content/`, `mcp/` are still
  the de-facto top-level. No `apps/` or `packages/` yet.
- **2** — Mixed conventions across subtrees; multiple build
  systems coexist.
- **1** — Single monolithic build script; no formal taxonomy.

### 7. Forkable platform

**What we mean.** A team that wants to build their own Datadog /
Grafana / Sentinel / Elastic catalogue with the same shape as ours
can fork the repo and have a working catalogue scaffold in a
weekend.

**What moves the score.**

- **5** — At least three named forks publishing their own catalogues
  (different tools, different sectors); replication guide reviewed
  by fork maintainers; reproducible across fork events.
- **4** — At least one named fork in production. Replication
  template (`templates/replication-starter/`) tested in CI;
  documented end-to-end fork walkthrough.
- **3** — Replication template + replication guide + ADRs +
  permissive license. No documented external fork yet.
- **2** — License + scattered docs. Replication is theoretically
  possible but not paved.
- **1** — License only.

## Current scorecard — Q2 2026

Baseline captured 2026-05-08, immediately after the P1/P2/P4 SSOT and
security-hardening work landed.

| # | Goal | Score | Rationale |
|---|---|---|---|
| 1 | World's most trusted open Splunk catalogue | **3** | 7,657 UCs across 23 categories — the largest open catalogue we are aware of. Composite quality 70.6 (Silver per [`scorecard.md`](scorecard.md)); 0 categories at Gold, 11 at Silver, 12 at Bronze. No external SME network yet beyond `CODEOWNERS`. |
| 2 | AI substrate | **3** | `llms.txt`, `llms-full.txt`, `ai.txt`, MCP server (10 tools), every UC carries a `ge` plain-language explanation. No nightly LLM eval harness, no RAG-chunk emission, no MCP latency benchmarks (P17 deferred). |
| 3 | Compliance source of truth | **3** | 1,310 cat-22 UCs across 12 tier-1 regulations; evidence packs and primer anchors in place. Phase E v6.1 lifted assurance-adjusted coverage to 59.89 %; the v7.2 target (≥75 % tier-1 / ≥55 % tier-2) is in flight. Legal reviewer capacity is sporadic. |
| 4 | Reproducible build | **3** | The load-bearing legacy artefacts (`catalog.json`, `llms*.txt`, `data.js`) are byte-reproducible and gated by 32 parity tests. The wider `dist/` tree (~32,000 files) is not — `BUILD-INFO.json` timestamp, `manifest.json`/`openapi.yaml` `generatedAt`, and MiniSearch shard ordering all drift across runs. Tracked as `p4-build-reproducibility`. |
| 5 | Multi-language | **1** | Schema is English-only. `n_lang` / `v_lang` localisation surface documented in [`DESIGN.md §12.4`](DESIGN.md). P19 is the 2027 milestone; no implementation yet. |
| 6 | Navigable monorepo | **2** | `pyproject.toml` + devcontainer + Makefile + ADRs + 11 Cursor rules + structured `CONTRIBUTING.md`. Top-level still mixes legacy `build.py` + `tools/build/` + `scripts/` + `content/` + `mcp/`. P6 (scripts taxonomy) and P9 (apps/× packages/ split) deferred. |
| 7 | Forkable platform | **3** | MIT license, [`templates/replication-starter/`](../templates/replication-starter/), [`docs/replication-guide.md`](replication-guide.md), nine ADRs, devcontainer image pinned by digest. No publicly-named external fork yet. |

**Average score:** `(3 + 3 + 3 + 3 + 1 + 2 + 3) / 7 = 2.57`

The headline reading for Q2 2026: **the project is at the "working,
not yet world-class" tier across five of seven dimensions, with
multi-language as the obvious laggard and reproducibility / monorepo
as the next two leverage points.**

## Trend (will accumulate)

| Quarter | Date | 1. Trust | 2. AI | 3. Compl. | 4. Repro | 5. i18n | 6. Mono | 7. Fork | Avg | Notes |
|---|---|---|---|---|---|---|---|---|---|---|
| Q2 2026 | 2026-05-08 | 3 | 3 | 3 | 3 | 1 | 2 | 3 | 2.57 | Baseline; immediately after P1 SSOT + P2.5 action-pin honesty + ADR-0008/0009 + capacity-and-staffing landed. |

## How to update this scorecard

The scorecard is refreshed at the end of each calendar quarter. The
process:

1. **Reread this document** in full. Each goal's "What moves the
   score" rules are the contract; do not score against unstated
   criteria.
2. **Run `make audit-full && make build`** so any score that depends
   on audit output (goal 1, 3, 4) is grounded in the current repo
   state, not memory.
3. **Add a new row to the trend table.** Each row is append-only;
   never edit a historical row to "correct" hindsight.
4. **Update the "Current scorecard" section** in place. The current
   scorecard always reflects the most recent quarter.
5. **Open a PR titled `chore: q<N> 20<YY> north-star scorecard`**
   with the updated `docs/north-star-scorecard.md` and *only* this
   document modified. The PR is reviewed by at least one maintainer
   who was active that quarter.
6. **If a score moves by more than ±1**, the PR description must
   name the specific PR, audit, or external event that drove the
   shift. "It feels stronger this quarter" is not adequate.
7. **If the average falls below 2.0**, the project moves into
   reduced operating mode (see
   [`docs/capacity-and-staffing.md`](capacity-and-staffing.md))
   regardless of the maintainer-pool trigger. A consistently
   sub-2.0 north-star average is an outage signal.

## Anti-patterns

These are common ways scorecards rot. We explicitly reject them:

- **Vanity inflation.** Scoring goal 7 a "5" because the license
  is MIT, ignoring the absence of a single named external fork.
  The rubric requires named adoption at the upper tiers.
- **Scoring against intent.** "We *plan* to do X next quarter" is
  not evidence that scoring should rise this quarter. The
  scorecard reflects what shipped, not what's documented in
  `ROADMAP.md`.
- **Silent goal substitution.** If a goal becomes uninteresting,
  the right move is to open an ADR retiring it, not quietly
  scoring it differently. The seven goals are append-only.
- **Confusing this scorecard with the content scorecard.** The
  per-category Gold/Silver/Bronze grading lives in
  [`scorecard.md`](scorecard.md) and is auto-generated. This
  document is the human-judgement scorecard; the two should be
  consistent but answer different questions.

## Links

- Per-UC content scorecard (auto-generated):
  [`docs/scorecard.md`](scorecard.md).
- Roadmap (cadence sized per scorecard goals):
  [`ROADMAP.md`](../ROADMAP.md).
- Capacity calibration (the staffing the cadence assumes):
  [`docs/capacity-and-staffing.md`](capacity-and-staffing.md).
- Rollback playbook (how a regression in goal 4 unwinds):
  [`docs/rollback-playbook.md`](rollback-playbook.md).
- ADRs that constrain the goals: [ADR-0007](adr/0007-json-as-source-of-truth.md)
  (UC content), [ADR-0008](adr/0008-canonical-constants.md)
  (constants), [ADR-0009](adr/0009-generated-artefact-policy.md)
  (artefacts).

---

<!-- BEGIN-AUTOGENERATED-SOURCES -->

## References

*Auto-generated by `scripts/generate_doc_references.py` from `data/source-references.json` and `data/source-mappings.json`. Edit those files (or the document body) to change citations; this footer is rewritten on every run.*

### Supporting sources

<a id="ref-1"></a>**[1]** European Parliament and Council of the European Union. (2022, December). *Directive (EU) 2022/2555 — NIS2 Directive on cybersecurity*. Official Journal of the European Union, L 333. ELI: dir/2022/2555. https://eur-lex.europa.eu/eli/dir/2022/2555/oj

<a id="ref-2"></a>**[2]** European Parliament and Council of the European Union. (2016, April). *Regulation (EU) 2016/679 — General Data Protection Regulation*. Official Journal of the European Union, L 119. ELI: reg/2016/679. https://eur-lex.europa.eu/eli/reg/2016/679/oj

<a id="ref-3"></a>**[3]** European Parliament and Council of the European Union. (2022, December). *Regulation (EU) 2022/2554 — Digital Operational Resilience Act (DORA)*. Official Journal of the European Union, L 333. ELI: reg/2022/2554. https://eur-lex.europa.eu/eli/reg/2022/2554/oj

<a id="ref-4"></a>**[4]** Public Company Accounting Oversight Board. (2007). *Auditing Standard 2201 — An Audit of Internal Control Over Financial Reporting*. PCAOB. PCAOB AS 2201. https://pcaobus.org/oversight/standards/auditing-standards/details/AS2201

<a id="ref-5"></a>**[5]** Splunk Inc. (2026). *Splunk Common Information Model Add-on Manual*. Splunk LLC, a Cisco company. Retrieved May 11, 2026, from https://docs.splunk.com/Documentation/CIM

<a id="ref-6"></a>**[6]** Splunk Inc. (2026). *Splunk Enterprise Security Administration Manual*. Splunk LLC, a Cisco company. Retrieved May 11, 2026, from https://docs.splunk.com/Documentation/ES

<a id="ref-7"></a>**[7]** Splunk Inc. (2026). *Splunk IT Service Intelligence Administration Manual*. Splunk LLC, a Cisco company. Retrieved May 11, 2026, from https://docs.splunk.com/Documentation/ITSI

<a id="ref-8"></a>**[8]** U.S. Congress. (2002). *Sarbanes-Oxley Act of 2002 — Public Company Accounting Reform and Investor Protection Act*. U.S. Government. Pub. L. 107–204. https://www.sec.gov/about/laws/soa2002.pdf

<a id="ref-9"></a>**[9]** U.S. Department of Health & Human Services. (2002). *HIPAA Privacy Rule (45 CFR Parts 160 and 164, Subparts A and E)*. Office for Civil Rights, HHS. 45 CFR 160, 164. https://www.hhs.gov/hipaa/for-professionals/privacy/index.html

<a id="ref-10"></a>**[10]** U.S. Department of Health & Human Services. (2013). *HIPAA Security Rule (45 CFR Parts 160 and 164, Subparts A and C)*. Office for Civil Rights, HHS. 45 CFR 160, 164. https://www.hhs.gov/hipaa/for-professionals/security/index.html

<a id="ref-11"></a>**[11]** United Kingdom Parliament. (2018). *Data Protection Act 2018 (UK GDPR, retained EU law)*. The Stationery Office. 2018 c. 12. https://www.legislation.gov.uk/ukpga/2018/12/contents

### Related repository documents

- [`docs/adr/0007-json-as-source-of-truth.md`](adr/0007-json-as-source-of-truth.md)
- [`docs/adr/0008-canonical-constants.md`](adr/0008-canonical-constants.md)
- [`docs/adr/0009-generated-artefact-policy.md`](adr/0009-generated-artefact-policy.md)

<!-- END-AUTOGENERATED-SOURCES -->
