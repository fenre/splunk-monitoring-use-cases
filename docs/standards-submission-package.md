# Standards submission package — NIST / OASIS / OCSF

> **Status:** Maintainer-ready draft (Lane E, Task E-2).  
> **Audience:** Lead maintainer preparing formal submissions to standards bodies.  
> **Live catalogue:** [https://fenre.github.io/splunk-monitoring-use-cases/](https://fenre.github.io/splunk-monitoring-use-cases/)  
> **Repository:** [https://github.com/fenre/splunk-monitoring-use-cases](https://github.com/fenre/splunk-monitoring-use-cases)

This document is copy-paste input for work-item proposals. It does **not** constitute a submission by itself; the maintainer performs outreach, form submission, and meeting attendance.

---

## 1. Executive summary

The Splunk Monitoring Use Cases catalogue is a curated, machine-readable, versioned taxonomy of **7,929** Splunk monitoring use cases across 23 technology domains — not a SIEM rules feed. Each use case carries executable SPL, CIM data-model alignment, optional MITRE ATT&CK mapping, and clause-level regulatory mappings where applicable. The project bridges fragmented vendor documentation and operationalisable detections through a deterministic build pipeline, a frozen `/api/v1/` JSON surface (documented in [`docs/api-versioning.md`](api-versioning.md), generated per [`api/README.md`](../api/README.md)), NIST OSCAL component definitions and catalog normalisations, and auditor-facing evidence packs. The catalogue is content-only: it does not execute searches against a live Splunk deployment.

---

## 2. Problem statement

Operational security and compliance teams face a structural gap between **vendor documentation** (textual, product-scoped, rarely mapped to controls) and **operationalisable detections** (executable SPL, normalised fields, alert thresholds, false-positive guidance). Splunk practitioners manually translate product manuals into saved searches, CIM tags, and audit evidence — work that is duplicated across organisations and rarely published in a machine-verifiable form.

The catalogue addresses this gap by:

1. **Structuring** each monitoring intent as a JSON sidecar validated against [`schemas/uc.schema.json`](../schemas/uc.schema.json) (schema version **1.7.0** at time of drafting).
2. **Mapping** detections to regulatory clauses via `compliance[]` entries with assurance levels, control objectives, and evidence artefacts (see [`docs/coverage-methodology.md`](coverage-methodology.md)).
3. **Publishing** deterministic API exports — compliance roll-ups, OSCAL catalog slices, MITRE coverage — under `/api/v1/` (see [`docs/api-versioning.md`](api-versioning.md)).
4. **Preserving provenance** through reproducible builds, CI audit gates, and Sigstore attestation on GitHub Pages releases (see [`.github/workflows/pages.yml`](../.github/workflows/pages.yml)).

The catalogue does **not** claim to replace vendor documentation, certified assessors, or production tuning; SPL queries are starting points requiring environment-specific validation (see [`ai.txt`](../ai.txt)).

---

## 3. Proposed contribution per body

### 3.1 OCSF (Open Cybersecurity Schema Framework)

**Current posture:** CIM-first; OCSF aspirational.

The catalogue's primary normalisation path is Splunk CIM, documented in [`docs/cim-and-data-models.md`](cim-and-data-models.md). Use cases declare CIM models in `cimModels[]` and optional accelerated queries in `cimSpl`. The optional `schema` field in [`docs/catalog-schema.md`](catalog-schema.md) (`a` / `schema` keys in `catalog.json`) may indicate `CIM`, `OCSF`, or combined values when a use case aligns with OCSF classes.

**Proposed contribution:**

| Source field | OCSF mapping intent |
|---|---|
| `monitoringType[]` (e.g. `Performance`, `Compliance`, `Authentication`) | Map to OCSF event categories / classes for observability and security telemetry |
| `cimModels[]` | Crosswalk table: CIM data model → nearest OCSF class (reference mapping, not normalisation) |
| `schema` when set to OCSF | Documented author intent for OCSF-first implementations |

**Honest scope limits:**

- Full OCSF normalisation of all 7,929 use cases is **not** shipped today.
- OCSF alignment is described as aspirational in [`docs/cim-and-data-models.md`](cim-and-data-models.md); most corpus entries assume CIM/tstats paths.
- A concrete deliverable for OCSF would be a **published crosswalk artefact** (CSV or JSON) derived from existing `monitoringType` + `cimModels` fields, submitted for community review — not a claim of complete OCSF compliance.

**Relevant repo assets:**

- [`docs/cim-and-data-models.md`](cim-and-data-models.md) — CIM vs OCSF positioning
- [`schemas/uc.schema.json`](../schemas/uc.schema.json) — `monitoringType`, `cimModels`, `schema` fields
- [`docs/catalog-schema.md`](catalog-schema.md) — abbreviated key reference

### 3.2 OASIS

**Scope clarification:** Monitoring track, not an active submission track at this time.

The catalogue **ingests** OASIS-related security standards data where upstream crosswalks exist:

- **MITRE ATT&CK** (STIX 2.1 bundles) — ingested via [`src/splunk_uc/ingest/attack.py`](../src/splunk_uc/ingest/attack.py) into `data/crosswalks/attack/`; MITRE endpoints documented in [`docs/api-versioning.md`](api-versioning.md).
- **STIX export** — bulk security-UC bundle at `/exports/catalog.stix.json` (documented in [`docs/url-scheme.md`](url-scheme.md)).

**CSAF (Common Security Advisory Framework):** No CSAF ingest pipeline or schema mapping exists in the repository at time of drafting. Do **not** submit a CSAF-specific proposal until a concrete mapping design exists.

**Recommended OASIS stance:**

- **Monitor** CSAF and related OASIS cybersecurity TC outputs for alignment with the catalogue's compliance and evidence-pack model.
- **Defer** formal OASIS submission until a maintainer-identified work item (e.g. STIX export schema promotion, CSAF advisory ↔ UC crosswalk) has community demand and implementation bandwidth.
- **Do not** claim OASIS standards leadership; cite ingestion of existing STIX corpora only.

### 3.3 NIST (strongest pitch)

**Proposed contribution:** OSCAL-aligned component definitions and NIST CSF / SP 800-53 clause coverage via the compliance API.

| Asset | Location | Role |
|---|---|---|
| OSCAL catalog normalisations | `data/crosswalks/oscal/nist-sp-800-53-r5.normalised.json` (and sibling files in [`data/crosswalks/oscal/`](../data/crosswalks/oscal/)) | NIST CSF v2, SP 800-53 r5 (baseline slices), SP 800-171 r3, SSDF |
| OSCAL component definitions | `data/crosswalks/oscal/component-definition-uc-22.35.1.json`; generated `/api/v1/oscal/component-definitions/` (see [`docs/api-versioning.md`](api-versioning.md)) | Per-UC OSCAL component-definition JSON where authored |
| Compliance API | [`docs/api-versioning.md`](api-versioning.md) (`/api/v1/compliance/` endpoints) | Clause coverage, gaps, per-UC compliance sidecars |
| Regulation catalogue | [`data/regulations.json`](../data/regulations.json) | **82** frameworks (22 tier-1, 58 tier-2, 2 tier-3) with `commonClauses[]`, priority weights, `derivesFrom` graph |
| Coverage metrics | [`reports/compliance-coverage.json`](../reports/compliance-coverage.json) | Machine-readable roll-up from `audit-compliance-mappings` |
| Evidence packs | [`docs/evidence-packs/`](evidence-packs/) | Auditor-facing markdown for tier-1 regulations (12 core frameworks documented in [`docs/regulatory-primer.md`](regulatory-primer.md)) |
| UC schema story layer | [`schemas/uc.schema.json`](../schemas/uc.schema.json) | `controlObjective`, `evidenceArtifact`, `requires_sme_review` |

**Coverage snapshot** (from `python -m splunk_uc audit-compliance-mappings`, 2026-05-19 on branch `E/standards-submission`):

| Scope | Clause % | Priority-weighted % | Assurance-adjusted % |
|---|---:|---:|---:|
| Global | 92.99 | 93.19 | 71.02 |
| Tier-1 | 90.89 | 90.90 | 74.95 |
| Tier-2 | 97.55 | 98.05 | 62.78 |
| Tier-3 | 100.00 | 100.00 | 50.00 |

- **7,929** UC sidecars scanned; **2,790** compliance entries; **0** blocking audit errors.
- Metrics are **engineering metrics**, not certification scores ([`docs/coverage-methodology.md`](coverage-methodology.md), `LEGAL.md`).

**NIST-specific ask:** Accept a reference implementation that demonstrates how OSCAL component definitions and catalog crosswalks can be generated deterministically from a structured detection catalogue, with open API endpoints for assessors and GRC tooling.

---

## 4. Evidence of adoption

| Surface | Evidence | Notes |
|---|---|---|
| **MCP server** | [`mcp/`](../mcp/), [`docs/mcp-server.md`](mcp-server.md) | **11** tools (`search_use_cases`, `get_use_case`, `get_use_case_markdown`, `list_categories`, `list_regulations`, `get_regulation`, `list_equipment`, `get_equipment`, `find_compliance_gap`, `get_clause_coverage`, `list_uncovered_clauses`); **4** URI schemes (`uc://`, `reg://`, `equipment://`, `ledger://`) |
| **LLM index** | `dist/llms.txt`, `dist/llms-full.txt` | Generated by `tools/build/render_meta.py` / `make build`; published on GitHub Pages |
| **Per-UC markdown twins** | `/uc/UC-X.Y.Z/uc.md` | Documented in [`docs/url-scheme.md`](url-scheme.md); LLM-friendly plain markdown per use case |
| **OpenAPI** | [`openapi.yaml`](../openapi.yaml) | OpenAPI 3.1; mirrored at `/api/v1/openapi.yaml` when API surface is generated |
| **JSON API** | [`docs/api-versioning.md`](api-versioning.md), [`api/README.md`](../api/README.md) | Frozen `/api/v1/` contract; generated by `python -m splunk_uc generate-api-surface` |
| **Dataset citation** | [`CITATION.cff`](../CITATION.cff) | CFF 1.2.0 metadata for research/production citation |
| **AI usage policy** | [`ai.txt`](../ai.txt) | Crawl/index/RAG permissions and attribution preferences |

**Not yet on this branch:** RAG chunk corpus (`dist/rag/chunks/`) and retrieval-eval baseline generators are documented on `main` in project planning materials but are **not** present in the `O/substrate` lineage at time of drafting. Do not cite chunk counts or BM25 baselines in NIST/OCSF submissions until those artefacts ship on the release branch.

**Adoption honesty:** The project is maintainer-led ([`GOVERNANCE.md`](../GOVERNANCE.md)); download/analytics for GitHub Pages and MCP installs are not published here. Cite MCP tool surface and API stability commitments, not download volume.

---

## 5. Governance

| Mechanism | Reference |
|---|---|
| Decision-making | [`GOVERNANCE.md`](../GOVERNANCE.md) — lead maintainer; lightweight issue-first process for non-trivial changes |
| Architecture decisions | [`docs/adr/`](adr/) — ADR index (e.g. ADR-0007 JSON SSOT, ADR-0013 frontend scaffold) |
| Reproducible builds | `make audit-reproducibility` — two consecutive `--reproducible` builds must produce byte-identical `dist/integrity.json` |
| Supply-chain attestation | [`.github/workflows/pages.yml`](../.github/workflows/pages.yml) — Sigstore keyless attestation via `actions/attest-build-provenance@v4` |
| API stability | [`docs/api-versioning.md`](api-versioning.md) — additive-only within `/api/v1/`; URL freeze audit |
| Schema stability | [`docs/schema-versioning.md`](schema-versioning.md) — UC schema changelog at [`schemas/changelogs/uc.md`](../schemas/changelogs/uc.md) |
| Licence | MIT ([`LICENSE`](../LICENSE)); AI policy in [`ai.txt`](../ai.txt) |

**Representative CI audit gates** (from [`.github/workflows/validate.yml`](../.github/workflows/validate.yml)):

1. `audit-uc-structure --full` — required fields and schema conformance across all sidecars
2. `audit-compliance-mappings` — compliance tuple validation + coverage metrics drift guard
3. `audit-compliance-gaps` — uncovered-clause roll-up for tier frameworks
4. `audit-prerequisites --check` — implementation-order DAG (cycles, unknown IDs)
5. `audit-spl-grammar --check` and `audit-spl-hallucinations` — SPL sanity gates
6. `audit-splunk-version-matrix --check` — Splunk version vocabulary parity
7. Build reproducibility workflow (`.github/workflows/build-reproducibility.yml`) — integrity byte identity

---

## 6. Lane C honesty — SME review and assurance

**SME review pipeline:** Aspirational, partially instrumented.

The UC schema defines `requires_sme_review` on compliance entries when `controlObjective` / `evidenceArtifact` were machine-generated and not yet vetted ([`schemas/uc.schema.json`](../schemas/uc.schema.json)). The field `signedBy` and `data/provenance/sme-signoffs.json` support auditor-reviewed provenance, but a standing SME review board is **not** operational.

**What the audits actually measure today:**

- `audit-compliance-mappings` validates tuple grammar, unknown regulations, assurance rationale, and story-layer completeness on tier-1 cat-22 UCs.
- **Assurance-adjusted coverage** (global **71.02%**) reflects declared assurance levels (`full`, `partial`, `contributing`) and status multipliers — not third-party attestation.
- **0** entries baselined in `tests/golden/audit-baseline.json` at last run; golden tests (**52/52** passed) pin expected audit behaviour, not human SME sign-off.

**Do not claim** independent SME certification of clause mappings. Frame submissions as **structured, auditable engineering artefacts** open to community and regulator review.

---

## 7. Submission checklist

### 7.1 NIST (OSCAL / NCCoE / CSF community)

| Step | Action | Owner | Status |
|---|---|---|---|
| 1 | Identify contact: [NIST OSCAL program / CSF community contact: TBD] | Maintainer | ☐ |
| 2 | Prepare 1-page proposal (§9.3 below) + links to `/api/v1/oscal/` and compliance API | Maintainer | ☐ |
| 3 | Attach sample artefacts: `data/crosswalks/oscal/nist-sp-800-53-r5.normalised.json`, one component-definition JSON | Maintainer | ☐ |
| 4 | Submit via [NIST submission channel: TBD — e.g. GitHub discussion, workshop CFP, or email] | Maintainer | ☐ |
| 5 | Log outcome in §10 Submission log | Maintainer | ☐ |

**Expected timeline:** [TBD — typical 4–12 weeks for community review, depending on channel]

### 7.2 OCSF

| Step | Action | Owner | Status |
|---|---|---|---|
| 1 | Identify contact: [OCSF Schema Council / contribution process: TBD] | Maintainer | ☐ |
| 2 | Draft CIM→OCSF crosswalk scope (§9.3 below) | Maintainer + [OT/security SME: TBD] | ☐ |
| 3 | Publish crosswalk draft in-repo (future PR under `data/crosswalks/` — not part of this package) | Maintainer | ☐ |
| 4 | Submit via [OCSF contribution URL: TBD] | Maintainer | ☐ |
| 5 | Log outcome in §10 | Maintainer | ☐ |

**Expected timeline:** [TBD]

### 7.3 OASIS (monitoring only)

| Step | Action | Owner | Status |
|---|---|---|---|
| 1 | Subscribe to [OASIS CSAF TC / Open CSAF list: TBD] | Maintainer | ☐ |
| 2 | Re-evaluate when CSAF ↔ compliance mapping design exists | Maintainer | ☐ |
| 3 | **No submission** until concrete proposal — mark checklist deferred | — | Deferred |

---

## 8. Kill condition tracking

Abandon formal submission efforts and publish this document as **awareness-only** if sustained outreach yields no work-item acceptance.

| Body | First outreach | Last follow-up | Responses | Work item opened? | Kill date | Decision |
|---|---|---|---|---|---|---|
| NIST | [TBD] | [TBD] | [TBD] | ☐ Yes / ☐ No | [TBD] | Active / Killed |
| OCSF | [TBD] | [TBD] | [TBD] | ☐ Yes / ☐ No | [TBD] | Active / Killed |
| OASIS | [TBD] | [TBD] | [TBD] | ☐ Yes / ☐ No | [TBD] | Deferred |

**Kill criteria (maintainer judgement):**

- No substantive response after **≥3** follow-ups over **≥90** days per body, **or**
- Body declines reference implementation / crosswalk contribution with no alternate venue, **or**
- Maintainer capacity falls below solo-mode threshold ([`docs/capacity-and-staffing.md`](capacity-and-staffing.md)).

---

## 9. Suggested work-item wording

### 9.1 NIST — OSCAL reference implementation (~300 words)

**Title:** Open OSCAL component definitions and compliance crosswalks from a structured Splunk monitoring catalogue

**Summary:** The Splunk Monitoring Use Cases project maintains 7,929 versioned monitoring use cases as JSON sidecars, each optionally mapping to regulatory clauses with assurance levels, control objectives, and evidence artefacts. The build pipeline emits deterministic NIST OSCAL artefacts: normalised catalog slices (NIST CSF v2, SP 800-53 Rev. 5 baseline profiles, SP 800-171 Rev. 3, SSDF) under `data/crosswalks/oscal/`, and per-use-case OSCAL component definitions exposed at `/api/v1/oscal/component-definitions/`. A parallel compliance API (`/api/v1/compliance/`) publishes clause coverage, priority-weighted coverage, and assurance-adjusted coverage across 82 regulatory frameworks indexed in `data/regulations.json`.

We propose contributing this pipeline as a **reference implementation** demonstrating how detection catalogues can generate assessor-consumable OSCAL JSON without binding to a single vendor SIEM. The implementation is reproducible (`make audit-reproducibility`), API-stable under documented additive-only rules (`docs/api-versioning.md`), and accompanied by tier-1 evidence packs for auditors. Current global clause coverage is 92.99% (engineering metric, not certification). Assurance-adjusted coverage is 71.02%, reflecting honest partial-assurance declarations rather than binary check-box mappings.

**Requested NIST action:** Review the OSCAL export shape for alignment with NIST OSCAL 1.1.x guidance; identify whether the component-definition-per-detection pattern fits NCCoE or OSCAL community example libraries; suggest canonical metadata fields for mapping operational detections to 800-53 controls.

**Evidence URLs:** GitHub repository (MIT licence), live API manifest at `https://fenre.github.io/splunk-monitoring-use-cases/api/v1/manifest.json`, schema at `schemas/uc.schema.json`, coverage methodology at `docs/coverage-methodology.md`.

### 9.2 OCSF — CIM crosswalk proposal (~300 words)

**Title:** Reference mapping from Splunk CIM monitoring types to OCSF classes

**Summary:** The Splunk Monitoring Use Cases catalogue normalises monitoring intent primarily through Splunk's Common Information Model (CIM), with optional `schema` metadata indicating OCSF alignment where authors have declared it. Each use case carries `monitoringType[]` (e.g. Performance, Compliance, Authentication) and `cimModels[]` (e.g. Network_Traffic, Authentication). Full OCSF event normalisation is **not** claimed today; [`docs/cim-and-data-models.md`](cim-and-data-models.md) documents CIM as the default path and OCSF as aspirational.

We propose a **community-reviewed crosswalk** from the catalogue's existing CIM and monitoring-type vocabulary to OCSF categories/classes. The crosswalk would be derived mechanically from fields already present in 7,929 public JSON records, published as open data under MIT licence, and versioned with the catalogue's schema semver. This avoids duplicating OCSF schema work inside Splunk-specific SPL; instead it gives OCSF consumers a starting point for correlating operational monitoring patterns with normalized event classes.

**Requested OCSF action:** Advise on mapping granularity (class vs. category vs. profile); identify existing OCSF profiles closest to IT operations telemetry (performance, capacity, change) versus security-centric classes; recommend submission format (GitHub PR to OCSF schema repo vs. standalone companion document).

**Scope limit:** We will not assert OCSF compliance for CIM/tstats queries until field-level mapping is reviewed. Initial deliverable is a reference table, not a transformation engine.

### 9.3 OASIS — monitoring note (no submission text)

No formal work-item wording is recommended for OASIS at this time. The catalogue ingests MITRE ATT&CK STIX bundles and exports a STIX bundle of security use cases (`/exports/catalog.stix.json`). CSAF advisory mapping is **out of scope** until a design exists. Revisit when the maintainer identifies a specific OASIS TC deliverable that aligns with published compliance API endpoints.

---

## 10. Submission log

| Date | Body | Channel | Submitted by | Reference ID | Response date | Outcome | Notes |
|---|---|---|---|---|---|---|---|
| | NIST | | | | | | |
| | OCSF | | | | | | |
| | OASIS | | | | | | |

---

## Appendix A — Key repository paths (verification reference)

| Path | Exists in git | Role |
|---|---|---|
| [`docs/standards-submission-package.md`](standards-submission-package.md) | Yes | This document |
| [`docs/api-versioning.md`](api-versioning.md) | Yes | API contract |
| [`api/README.md`](../api/README.md) | Yes | Generated `api/v1/` documentation |
| [`schemas/uc.schema.json`](../schemas/uc.schema.json) | Yes | UC authoring schema v1.7.0 |
| [`data/regulations.json`](../data/regulations.json) | Yes | 82-framework catalogue |
| [`data/crosswalks/oscal/`](../data/crosswalks/oscal/) | Yes | OSCAL normalisations |
| [`reports/compliance-coverage.json`](../reports/compliance-coverage.json) | Yes | Latest coverage metrics |
| [`openapi.yaml`](../openapi.yaml) | Yes | OpenAPI 3.1 root spec |
| [`docs/evidence-packs/`](../docs/evidence-packs/) | Yes | Auditor evidence packs |
| [`GOVERNANCE.md`](../GOVERNANCE.md) | Yes | Governance model |
| [`CITATION.cff`](../CITATION.cff) | Yes | Dataset citation |
| `api/v1/` tree | Generated (gitignored) | Run `python -m splunk_uc generate-api-surface`; see [`api/README.md`](../api/README.md) |
| `dist/llms.txt` | Generated (gitignored) | Run `make build` |

---

*Drafted for Lane E Task E-2. Maintainer fills §7 placeholders, §8–§10 tables, and performs external submission.*
