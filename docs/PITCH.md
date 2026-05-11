# Splunk Monitoring Use Cases

### *The open, verifiable gold standard for Splunk detections.*

---

> **7,364 production-grade use cases.
> 23 technology domains.
> 3 Splunkbase-ready content packs.
> One browser tab. Zero license cost.**

A curated, machine-readable, continuously-verified catalog of IT
infrastructure and security monitoring use cases for Splunk — with
ready-to-run SPL, CIM mappings, MITRE ATT&CK coverage, quality grades,
and automated Splunk Cloud compatibility checks.

MIT-licensed. Static-hosted. Drop-in deployable. Built on Python stdlib,
no framework, no database, no vendor lock-in.

---

## The problem

Splunk is the most deployed observability and security platform on the
planet — and every serious customer eventually hits the same wall:

| Pain | Why it hurts |
|---|---|
| **Blank-slate syndrome** | A fresh Splunk install has the power of a spacecraft and the dashboard of a text editor. What do you *actually* monitor? |
| **The "just trust us" gap** | Commercial SPL catalogs hand you 500 queries. Which ones work? Which ones fail AppInspect? Which are plagiarised from a 2014 blog? No one tells you. |
| **Cloud migration roulette** | Half your saved searches quietly stop working when you move to Splunk Cloud. You find out in production. |
| **SOC vs. ITOps silos** | Security teams have ESCU. Platform teams have IT Essentials. Cloud teams have…a spreadsheet. No shared vocabulary, no shared catalog. |
| **Scale without quality signal** | More use cases is not the same as better use cases. How do you tell a gold-standard detection from a hastily-cut-and-pasted one? |

Every one of those pains has a $0 or $1M solution. We're the $0 one —
and we're open about exactly how we got here.

---

## The solution in one paragraph

An open-source catalog of **7,364 infrastructure and security use cases**,
each written in a strict authoring contract, each producing **ready-to-run
SPL**, each automatically graded on six quality dimensions, each audited
for **Splunk Cloud compatibility** on every commit, each traceable to its
**source of truth** (Splunk docs / vendor docs / MITRE ATT&CK / threat
intel / community), and each packaged into three **Splunkbase-ready content
packs** (TA, ITSI, ES) that install with a single click.

Everything is authored in plain markdown. Everything compiles with one
command. Everything runs in a browser as a static site. Everything is
free forever.

---

## Proof by numbers

### Scale

| Metric | Value |
|---|---|
| Use cases | **7,364** |
| Categories | **23** (infrastructure · security · cloud · application · industry · compliance · business) |
| Subcategories | **212** |
| Lines of curated markdown | **~169,000** |
| Ready-to-run SPL queries | **7,364** |
| Industry verticals covered | Energy, manufacturing, healthcare, telecom, transportation, retail, aviation, insurance |
| Compliance frameworks | **69** — GDPR<sup class="ref">[<a href="#ref-2">2</a>]</sup>, NIS2<sup class="ref">[<a href="#ref-1">1</a>]</sup>, DORA<sup class="ref">[<a href="#ref-3">3</a>]</sup>, HIPAA<sup class="ref">[<a href="#ref-12">12</a>]</sup>, PCI DSS, ISO 27001, NIST CSF, SOC 2, SOX<sup class="ref">[<a href="#ref-10">10</a>]</sup> ITGC, CCPA, MiFID II, and 58 more |
| Equipment vendors tagged | **206+** — Cisco, Palo Alto, Fortinet, F5, VMware, Microsoft, AWS, Azure, GCP, Nutanix, Dell, HPE, … |

### Quality

| Signal | Value |
|---|---|
| UCs with complete `References:` | **100 %** |
| UCs cited from **official Splunk docs** | **72 %** |
| UCs cited from **official vendor docs** | 9 % |
| UCs cited from **threat intelligence** (Mandiant, Unit 42, CISA, …) | 7 % |
| UCs mapped to **MITRE ATT&CK** | 5 % (≥80 % on security categories) |
| UCs cited from **NIST / CIS / ISO / PCI** | 1.5 % |
| Unclassified / unknown source | **2.4 %** |
| Splunk Cloud pack-level audit findings | **0** |

### Engineering

| Metric | Value |
|---|---|
| Lines of Python in `scripts/` | **10,323** |
| Automation scripts | **38** |
| CI workflows | **7** |
| Runtime dependencies | **Python stdlib only.** No npm, no pip, no DB. |
| Build time, full pipeline | **~3 seconds** |
| Dashboard page weight | 40 MB (lazy-loaded, virtual-scrolled) |

---

## What you get

### 1. The catalog (the content)

A curated three-level tree of **Category → Subcategory → Use Case**, every
node with a stable numeric ID that appears in its URL, its markdown
heading, and its JSON representation. Every use case carries:

- **Criticality / difficulty** — ⚪ quick glance before you commit
- **Ready-to-run SPL** — copy-paste into Splunk, it runs
- **CIM / Data Model mapping** — `tstats`-accelerated variant included
- **MITRE ATT&CK** — technique IDs for every security detection
- **App/TA requirement** — exactly which Splunkbase add-on you need
- **Data sources** — index, sourcetype, onboarding pointers
- **Known false positives** — tuning guidance, not just "here's the query"
- **Implementation steps** — how to roll it out and monitor it
- **Visualization recommendation** — table? single value? timechart?
- **References** — clickable links to the primary source

### 2. The dashboard (the experience)

A single static HTML file — open `index.html`, that's it — with:

- Unified filter strip (pillar, criticality, difficulty, regulation, monitoring type)
- Grouped sidebar navigation across 6 collapsible pillars
- Full-text search (`Cmd/Ctrl+K`), deep-linkable URLs
- Equipment filter ("show me everything for Cisco ASA")
- Virtual scrolling for 7,364 cards
- Light / dark mode, mobile-first, print-optimised
- Non-technical "outcomes" view for executive audiences
- Colour-coded provenance badge on every card — **instantly see if this came from Splunk docs or a random blog**

### 3. The three Splunkbase content packs

Rebuilt from the same catalog on every release. All three ship with
searches **disabled by default** and pass **AppInspect Cloud vetting**.

| Pack | Ships | Target |
|---|---|---|
| **Technology Add-on** (`TA-splunk-use-cases`) | ~115 Quick-Start saved searches, index macros, eventtype aliases | Platform admins |
| **ITSI content pack** (`DA-ITSI-monitoring-use-cases`) | 6 KPI base searches, 3 threshold templates, 4 KPI templates, 3 service templates | ITOps / SRE |
| **ES content pack** (`DA-ESS-monitoring-use-cases`) | 650 correlation searches, MITRE ATT&CK governance, analytic stories, CIM eventtypes & tags, RBA seeds | SOC / Detection Engineering |

Drop the `.spl` into Splunk. Done.

### 4. The machine-readable feeds

For integrators, CMDB owners, LLM-tool builders and anyone who wants to
wire the catalog into their own platform:

- `catalog.json` — single-file, 42 MB, complete catalog
- `api/cat-<n>.json` — per-category sharded endpoints
- `llms.txt` / `llms-full.txt` — AI-readable site indices
- `provenance.json` — per-UC source classification
- `scorecard.json` — per-category quality grade
- `openapi.yaml` — OpenAPI 3.1 spec
- `api-docs.html` — self-hosted Swagger UI

### 5. The quality system

This is what separates us from every other Splunk use-case catalog.

**Provenance ledger.** For every use case, automated classification of
every citation URL into one of 9 source categories (official docs, vendor
docs, MITRE ATT&CK, threat intel, standards, blogs, community…). Rendered
as a colour-coded badge on every UC card.

**Quality scorecard.** Every category gets a **Gold / Silver / Bronze /
Needs work** letter grade based on six weighted dimensions: references %,
provenance authority, freshness, KFP coverage, MITRE coverage, sample
fixtures %. Re-computed on every build. Published to
[`docs/scorecard.md`](scorecard.md) and
[`scorecard.json`](../scorecard.json).

**Sample-event fixtures + test harness.** Real log lines under
`samples/UC-<id>/`, fed into a disposable Splunk 9.4 Docker container, SPL
run via the REST API, results asserted against expectations. JUnit XML
emitted. CI fails on regression.

**Splunk Cloud compatibility audit.** Every SPL query and every `.conf`
file scanned for patterns that fail AppInspect —
custom search commands, scripted inputs, `restmap.conf`, python2,
`| runshellscript`, unbounded `| map`, …. First audit: **zero** pack-level
findings, **five** SPL warnings (all legitimate `dbxquery` callouts).

### 6. Companion tools

- **Data Sizing Assessment Tool** — `tools/data-sizing/` — estimate ingest
  volume from 206+ equipment entries, output GB/day, EPS, license-tier
  recommendations, storage estimates, CSV export.
- **Dashboard Studio exports** — 46-panel Quick-Start catalog dashboard
  with synthetic `makeresults` data for instant demos.
- **Executive health dashboard** — single-pane-of-glass for the C-suite.
- **Datagen POC** — Cribl Stream / HEC playbook for 10 representative
  use cases, with sample logs.
- **MCP server** — expose the catalog as tools for AI agents (see
  [`mcp/`](../mcp/) for the Python `splunk-uc-mcp` package and
  [`docs/mcp-server.md`](mcp-server.md) for the integration guide).
- **Replication starter** — ~30-line `build.py` fork template for porting
  the architecture to any query language (KQL, DQL, SignalFlow, YARA-L).

---

## Who it's for

| Persona | What they get |
|---|---|
| **CISO / IT Director** | Defensible catalog of what your platform should be monitoring, mapped to 9 compliance frameworks. Show the board. |
| **Splunk Sales Engineer** | Open the dashboard in front of a customer. Filter by their stack. Drop a `.spl` pack into their POC. Deal accelerated. |
| **SOC detection engineer** | 1,874 MITRE-mapped correlation searches pre-written, pre-cited. Clone, tune, deploy. |
| **ITOps / SRE** | 4,430 infrastructure-monitoring UCs. Stop reinventing disk-usage alerts. |
| **Splunk admin on a new job** | "What should we monitor?" — solved in one click. |
| **Splunk consultant** | A shared vocabulary with the client. A shared artefact. A measurable deliverable. |
| **Integrator / tool-builder** | Machine-readable feeds, stable IDs, OpenAPI spec, semver. Build on us. |
| **AI / LLM tooling author** | `llms.txt`, `llms-full.txt`, and the `mcp/` Python server (`splunk-uc-mcp`) that turns the catalog into agent tools over JSON-RPC stdio. |
| **Researcher / academic** | `CITATION.cff` for proper attribution. Reproducible, open, auditable. |

---

## How it's different

### vs. Splunk IT Essentials / ITSI / ESCU

- **Broader scope.** Splunk's own content packs cover slices. We span
  all 23 domains (infra + security + cloud + app + industry + compliance
  + business) in one unified catalog.
- **Provenance and grade.** Splunk doesn't tell you which of its
  detections come from official docs vs. community submissions. We do.
- **We ship everything they ship.** TA, ITSI, ES packs — all three —
  built from the same source of truth.

### vs. commercial SPL marketplaces (Splunkbase paid, third-party vendors)

- **$0.** MIT license, forever.
- **No lock-in.** Fork it, host it internally, ship your own variant.
- **Transparent quality signal.** Public scorecard, public provenance,
  public CI. No marketing claims hiding a 2015 blog post.

### vs. "just write your own"

- **10,323 lines of automation** so you don't have to. Ours.
- **7,657 UCs of curated content.** Would take a team of four three
  years to write from scratch.
- **Zero runtime dependencies.** It'll still build in 2035.

### vs. "our SOAR / XDR has built-in detections"

- **Portable.** The same catalog powers Splunk, Sentinel (via replication),
  Datadog (via replication), Chronicle (via replication). Vendors come
  and go. Detections should not.

---

## What makes the moat work

Every claim on this page is reproducible. Clone the repo. Run
`make build`. Run `make serve`. Open the dashboard. All the numbers match.

**Audit-gated content.** Every pull request passes automated checks for
UC-ID uniqueness, structural completeness, schema conformance, link
integrity, Splunk Cloud compatibility, release-note sync, and
generated-file drift. Nothing ships unverified.

**Reversible everything.** Categories are numbered without gaps.
Renumbering triggers a major version bump. Breaking changes are named
and versioned. Integrators can pin to a commit.

**Deterministic builds.** Same input, same output, byte for byte. CI
re-runs the build on every PR and fails if the committed artefacts
disagree with what `build.py` produces. Drift is impossible.

**Open governance.** [`GOVERNANCE.md`](../GOVERNANCE.md) documents the
decision process. [`docs/adr/`](adr/) records every architectural
decision with context, consequences, and alternatives. No surprises.

**Citation-ready.** [`CITATION.cff`](../CITATION.cff) ships the metadata
for academic citation. This catalog is how platform-engineering
research should look.

---

## Vision

**v6.0 (shipped):** Verifiable quality — every shipped SPL demonstrably
correct, every metric transparently measured.

**v7.0–v7.3 (shipped):** 195 detections rewritten to true-gold standard.
69 regulatory frameworks with clause-level provenance. Interactive
knowledge graph. Cisco Catalyst Center, OpenShift, and NIS2 deep-dives.
MCP server with ten tools for AI-agent integration.

**v7.x backlog:** Industry-specific bundles (Finance, OT, Healthcare,
Public Sector). Cloud-provider deep dives at parity with cat-10.
AI / LLM observability subcategory. OCSF parity (every detection in
CIM *and* OCSF). CLI (`pip install splunk-monitoring-use-cases`).
Terraform provider. VS Code extension. Translations. Monthly community
call.

**v8 north star:** Every Splunk deployment on Earth starts from this
catalog. Every commercial Splunk vendor builds on top of it. Every
academic paper about detection engineering cites it.

---

## Get started in 90 seconds

```bash
git clone https://github.com/fenre/splunk-monitoring-use-cases
cd splunk-monitoring-use-cases
python3 -m http.server 8080
# open http://localhost:8080/
```

Or just visit [**fenre.github.io/splunk-monitoring-use-cases**](https://fenre.github.io/splunk-monitoring-use-cases/).

Or drop one of the three `.spl` packs from the latest
[GitHub Release](https://github.com/fenre/splunk-monitoring-use-cases/releases)
into your Splunk instance and click install.

---

## Asks

- ⭐ **Star us** on GitHub if this is useful.
- 🍴 **Fork us** if you want to stand up a private, organization-specific
  variant — we built the [replication starter](../templates/replication-starter/)
  to make that a weekend project.
- 🐛 **File feedback** on any use case directly from the dashboard
  ("Report issue on GitHub" button) — we read every one.
- 🛠 **Contribute a sample event fixture** — fastest path from "Bronze"
  to "Silver" on your favourite category. See [`samples/README.md`](../samples/README.md).
- 💬 **Cite us** if you use the catalog in research or production —
  metadata in [`CITATION.cff`](../CITATION.cff).

---

## The one-line pitch (memorable version)

> **We're the Wikipedia of Splunk detections — 7,364 articles, every
> one cited, graded, and runnable.**

---

*Project stats, release notes and full architecture document:
[`CHANGELOG.md`](../CHANGELOG.md) · [`docs/DESIGN.md`](DESIGN.md) ·
[`ROADMAP.md`](../ROADMAP.md). Current release: **v7.3**. MIT licensed. Hosted on GitHub Pages.
No backend, no login, no telemetry.*

---

<!-- BEGIN-AUTOGENERATED-SOURCES -->

## References

*Auto-generated by `scripts/generate_doc_references.py` from `data/source-references.json` and `data/source-mappings.json`. Edit those files (or the document body) to change citations; this footer is rewritten on every run.*

### Supporting sources

<a id="ref-1"></a>**[1]** European Parliament and Council of the European Union. (2022, December). *Directive (EU) 2022/2555 — NIS2 Directive on cybersecurity*. Official Journal of the European Union, L 333. ELI: dir/2022/2555. https://eur-lex.europa.eu/eli/dir/2022/2555/oj

<a id="ref-2"></a>**[2]** European Parliament and Council of the European Union. (2016, April). *Regulation (EU) 2016/679 — General Data Protection Regulation*. Official Journal of the European Union, L 119. ELI: reg/2016/679. https://eur-lex.europa.eu/eli/reg/2016/679/oj

<a id="ref-3"></a>**[3]** European Parliament and Council of the European Union. (2022, December). *Regulation (EU) 2022/2554 — Digital Operational Resilience Act (DORA)*. Official Journal of the European Union, L 333. ELI: reg/2022/2554. https://eur-lex.europa.eu/eli/reg/2022/2554/oj

<a id="ref-4"></a>**[4]** Payment Card Industry Security Standards Council. (2018). *Payment Card Industry Data Security Standard v3.2.1* (v3.2.1). PCI SSC. https://www.pcisecuritystandards.org/document_library/?category=pcidss

<a id="ref-5"></a>**[5]** Payment Card Industry Security Standards Council. (2022). *Payment Card Industry Data Security Standard v4.0* (v4.0). PCI SSC. https://www.pcisecuritystandards.org/document_library/?category=pcidss

<a id="ref-6"></a>**[6]** Splunk Inc. (2026). *Splunk Enterprise Documentation*. Splunk LLC, a Cisco company. Retrieved May 11, 2026, from https://docs.splunk.com/Documentation/Splunk

<a id="ref-7"></a>**[7]** Splunk Inc. (2026). *Splunk Enterprise Security Administration Manual*. Splunk LLC, a Cisco company. Retrieved May 11, 2026, from https://docs.splunk.com/Documentation/ES

<a id="ref-8"></a>**[8]** Splunk Inc. (2026). *Splunk IT Service Intelligence Administration Manual*. Splunk LLC, a Cisco company. Retrieved May 11, 2026, from https://docs.splunk.com/Documentation/ITSI

<a id="ref-9"></a>**[9]** Splunk Inc. (2026). *Splunk Observability Cloud Documentation*. Splunk LLC, a Cisco company. Retrieved May 11, 2026, from https://docs.splunk.com/observability/en/

<a id="ref-10"></a>**[10]** U.S. Congress. (2002). *Sarbanes-Oxley Act of 2002 — Public Company Accounting Reform and Investor Protection Act*. U.S. Government. Pub. L. 107–204. https://www.sec.gov/about/laws/soa2002.pdf

<a id="ref-11"></a>**[11]** U.S. Department of Health & Human Services. (2002). *HIPAA Privacy Rule (45 CFR Parts 160 and 164, Subparts A and E)*. Office for Civil Rights, HHS. 45 CFR 160, 164. https://www.hhs.gov/hipaa/for-professionals/privacy/index.html

<a id="ref-12"></a>**[12]** U.S. Department of Health & Human Services. (2013). *HIPAA Security Rule (45 CFR Parts 160 and 164, Subparts A and C)*. Office for Civil Rights, HHS. 45 CFR 160, 164. https://www.hhs.gov/hipaa/for-professionals/security/index.html

<!-- END-AUTOGENERATED-SOURCES -->
