# Content gap analysis — Phase 0.2

> **Status:** Phase 0.2 snapshot, generated 2026-04-16 from
> `data/inventory/ucs.csv` and `data/inventory/gap-analysis.json`.
> **Sources:**
>   * Inventory — `python3 scripts/inventory_ucs.py --stats`
>   * Gap analysis — `python3 scripts/gap_analysis.py`
> **Regenerate:** run the two scripts in order; they are deterministic.
> **Purpose:** characterise the existing catalogue's regulatory coverage
> so Phase 1 knows exactly where to invest content work.

---

## 1. Headline numbers

| Metric | Value |
|---|---:|
| Total use cases in the catalogue | **6 304** |
| Use cases carrying a `Regulations:` tag | **1 162** (18.4 %) |
| Distinct regulation labels in those tags | **70** |
| Tier-1 frameworks recognised by the draft regulation index | **10** |
| Tier-2 frameworks not yet in the index (unknown labels) | **60** |
| Use cases with a tag resolving to ≥ 1 tier-1 framework | **510** |
| Use cases with a tag that does NOT resolve to a tier-1 framework | **652** |

**Key reading:** almost exactly half of the regulatory-tagged UCs
currently map to something outside our tier-1 index. That is the single
biggest coverage investment for Phase 1.3.

---

## 2. Tier-1 coverage (recognised frameworks)

Each tier-1 framework in `data/regulations.draft.json` with the number
of UCs that tag it and the cat-22 subcategory that currently owns the
content.

| # | Framework | UCs | Subcategory owning | Clauses in index |
|---:|---|---:|---|---:|
| 1 | PCI-DSS v4.0 | 90 | `22.11` | 18 |
| 2 | NIST SP 800-53 Rev. 5 | 80 | `22.14` | 19 |
| 3 | HIPAA Security Rule | 55 | `22.10` | 12 |
| 4 | NIST CSF 2.0 | 50 | `22.7` | 15 |
| 5 | GDPR | 50 | `22.1` | 12 |
| 6 | ISO/IEC 27001:2022 | 45 | `22.6` | 19 |
| 7 | NIS2 | 45 | `22.2` | 12 |
| 8 | DORA | 40 | `22.3` | 14 |
| 9 | SOX-ITGC (PCAOB AS 2201) | 35 | `22.12` | 11 |
| 10 | SOC 2 (TSC 2017) | 30 | `22.8` | 16 |

**Structural finding #1 — one-to-one framework → subcategory lock-in.**
Every tier-1 framework is owned by *exactly one* subcategory of cat-22.
There is no cross-subcategory reuse. That means GDPR-relevant
authentication UCs live in `22.1` even if a near-identical detection
exists in `cat-09` (identity) — the operator of the other category cannot
see the relevance without reading `cat-22` separately. Phase 1 must
either (a) lift the regulatory mapping out of the subcategory into a
transversal layer, or (b) duplicate tags across the categories that
already produce the detection.

**Structural finding #2 — shallow clause surface.**
The tier-1 index currently lists between 11 and 19 clauses per
framework, deliberately limited to the auditor-reachable subset. Phase 1
brings this up to the full NIST OLIR / OSCAL catalogue surface so that
every UC can claim a precise, version-stamped clause rather than a
framework-level tag.

**Structural finding #3 — assurance language is flat.**
Every UC today carries a single `Regulations:` free-text bullet.
Phase 1's JSON sidecar schema (`schemas/uc.schema.json`) requires a
structured `compliance[]` array with `clauseUrl`, `assurance`, `mode`,
and `controlTest` — none of which are recoverable from today's content.
Phase 1.2 must re-author every regulatory UC.

---

## 3. Tier-2 frameworks not in the draft index

Labels appearing in the `Regulations:` tag that did not resolve. All
live under one or two cat-22 subcategories, showing the tier-2
structure mirrors tier-1's "one subcategory per framework" pattern.

| UCs | Label | Subcategory |
|---:|---|---|
| 70 | NERC CIP | `22.13` |
| 55 | IEC 62443 | `22.15` |
| 35 | API RP 1164 | `22.18` |
| 35 | EU AML | `22.25` |
| 35 | CFT framework | `22.25` |
| 33 | FISMA | `22.19, 22.32` |
| 30 | TSA Pipeline Security Directive | `22.16` |
| 30 | PSD2 | `22.22` |
| 25 | CCPA | `22.4` |
| 25 | MiFID II | `22.5` |
| 25 | FDA 21 CFR Part 11 | `22.17` |
| 25 | FedRAMP | `22.19` |
| 25 | EU AI Act | `22.21` |
| 20 | CMMC 2.0 | `22.20` |
| 20 | EU Cyber Resilience Act (CRA) | `22.23` |
| 17 | CPRA | `22.4` |
| 15 | eIDAS 2.0 | `22.27` |
| 15 | EU trust services | `22.27` |
| 12 | SWIFT CSP | `22.22` |
| 11 | APRA CPS 234 | `22.29` |
| … | (40 more tags, 1–10 UCs each) | various |

Phase 1.3 promotes the top ~20 of these into the tier-1 index (they all
have public, clause-level authoritative sources and at least 15 UCs
already describing them).

---

## 4. Coverage depth gaps (within tier-1 frameworks)

Even inside the tier-1 list, several framework clauses that matter most
to auditors are under-evidenced. This is a qualitative read of the UCs
that currently live in each subcategory; Phase 0.1 auditor interviews
confirm or rebalance this list.

### 4.1 GDPR (`22.1`, 50 UCs, 12 clauses in index)
* Art. 32 (security of processing) — well covered (detection + response).
* Art. 33–34 (breach notification) — adequate, but no evidence that the
  **72-hour clock** is demonstrably driven by log timestamps rather than
  manual incident tickets.
* Art. 25 (data-protection by design) — **minimal** coverage; no UCs
  demonstrating privacy-by-default configuration monitoring.
* Art. 28 (processors) — **absent**; no UCs covering processor access
  or supply-chain monitoring.

### 4.2 PCI-DSS v4.0 (`22.11`, 90 UCs, 18 clauses)
* Req. 10 (logging and monitoring) — deeply covered, the catalogue's
  strongest suit.
* Req. 11 (testing) — moderate; vulnerability-scan UCs exist but
  authenticated-scan coverage thin.
* Req. 12.10 (incident response) — 2–3 UCs only.
* Req. 4 (transmission encryption) — **minimal**; no TLS inventory /
  weak-cipher detection UCs tagged PCI-DSS.

### 4.3 HIPAA (`22.10`, 55 UCs, 12 clauses)
* §164.312(b) (audit controls) — well covered.
* §164.308(a)(6) (security incident procedures) — adequate.
* §164.308(a)(7) (contingency plan) — **minimal**; no DR/BC drills UCs.
* §164.312(e)(1) (transmission security) — **minimal**.

### 4.4 SOC-2 (`22.8`, 30 UCs, 16 clauses)
* CC7.2 (system monitoring for anomalies) — adequate.
* CC7.3 (evaluated events and incidents) — adequate.
* CC6.1 (logical access) — **minimal**; only 2 UCs tagged despite rich
  access-control content in `cat-09`. Classic structural finding #1.
* CC8.1 (change management) — **minimal** despite rich `cat-12`
  content.

### 4.5 SOX-ITGC (`22.12`, 35 UCs, 11 clauses)
* Access management & SoD — covered.
* Change management — adequate.
* Backup / restore — 1–2 UCs.
* Operations / batch scheduling — **minimal**.

### 4.6 ISO 27001:2022 (`22.6`, 45 UCs, 19 clauses)
* A.8.15 (logging) and A.8.16 (monitoring activities) — well covered.
* A.8.17 (clock synchronisation) — covered but lightly.
* A.5.23 (cloud services security) — **minimal**.
* A.5.24–A.5.26 (incident management lifecycle) — partial.

### 4.7 NIST CSF 2.0 and 800-53 Rev 5 (`22.7` and `22.14`)
Strongest programmatic coverage because the catalogue is authored with
these in mind. Gap is clause-level precision, not volume: of the ~180
800-53 controls relevant to logging and monitoring, 80 are touched by
at least one UC; the rest are untagged. NIST OLIR ingestion in
Phase 1.3 delivers the full surface.

### 4.8 NIS2 (`22.2`) and DORA (`22.3`)
Early EU frameworks; content drafted from regulation text rather than
practitioner feedback. Phase 0.1 interviews with EU DPO/ISMS personas
will validate whether the existing mappings are useful to a
supervisory authority.

---

## 5. Cross-category reuse opportunities

The catalogue already contains 5 142 non-regulatory UCs across 22
categories that — with the right mapping — satisfy or detect violations
of tier-1 framework clauses. High-leverage areas:

| Category | UCs | Likely tier-1 frameworks | Action |
|---|---:|---|---|
| `cat-09` identity & access | 104 | SOC-2 CC6.x, SOX-ITGC access, ISO A.5.15, HIPAA §164.312(a) | tag + reuse |
| `cat-10` security infrastructure | 2 402 | PCI-DSS 10–11, NIS2 Art.21, DORA Art.9–10, 800-53 SI-4 | selective tag |
| `cat-12` DevOps / CI-CD | 88 | SOC-2 CC8.1, SOX-ITGC change, ISO A.8.25 | tag + reuse |
| `cat-04` cloud infrastructure | 227 | ISO A.5.23, NIS2 supply chain, DORA Art.28 | tag + reuse |
| `cat-07` database & data platforms | 122 | PCI-DSS 3.x, GDPR Art.32, HIPAA §164.312 | tag + reuse |

A conservative estimate: applying the Phase 1 `compliance[]` sidecar
schema to ~800 existing non-regulatory UCs would more than *double*
the catalogue's regulatory surface without writing any new detections.

---

## 6. Empty `Regulations:` tag (in cat-22)

Five cat-22 UCs have no `Regulations:` bullet at all. These are the
"trending" meta-KPI UCs under `22.9` (compliance posture trending). They
describe measurement, not detection, and arguably do not belong in the
`compliance[]` schema at all; they should be tagged with a
`controlFamily: "posture-measurement"` attribute instead.

| UC ID | Title |
|---|---|
| `UC-22.9.1` | Compliance Posture Score Trending |
| `UC-22.9.2` | Audit Finding Closure Rate Trending |
| `UC-22.9.3` | Control Effectiveness Trending |
| `UC-22.9.4` | Regulatory Incident Response Time Trending |
| `UC-22.9.5` | Policy Violation Volume Trending |

---

## 7. Prioritised recommendations for Phase 1

1. **Phase 1.1 (schema)** — lock `schemas/uc.schema.json`; keep the
   JSON-first sidecar; enforce clause-level `compliance[]` with
   `clauseUrl`, `assurance`, `mode`, `controlTest`.
2. **Phase 1.2 (authoring)** — migrate the 1 162 regulatory UCs into
   JSON sidecars and populate clause mappings from
   `data/regulations.draft.json`.
3. **Phase 1.3 (tier-2 promotion)** — promote the 20 tier-2 frameworks
   above into the recognised index; ingest NIST OLIR crosswalks for
   CSF 2.0 ↔ 800-53 Rev 5 and CSF ↔ ISO 27001:2022.
4. **Phase 1.4 (cross-category reuse)** — select ~800 non-regulatory UCs
   (prioritising cat-09, -10, -12) and attach `compliance[]` sidecars.
5. **Phase 2 (auditor validation)** — regenerate evidence packs for
   10 representative UCs and hand them to the auditor research
   respondents from Phase 0.1 for acceptance testing.

---

## 8. Provenance

* Inventory CSV — `data/inventory/ucs.csv`, produced by
  `scripts/inventory_ucs.py`.
* Gap-analysis JSON — `data/inventory/gap-analysis.json`, produced by
  `scripts/gap_analysis.py`.
* Regulations index — `data/regulations.draft.json`.
* Both scripts are deterministic: rerun to regenerate this analysis.
