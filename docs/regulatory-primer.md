# Regulatory primer

> **Audience:** privacy, legal, risk, audit, and executive readers who need to
> understand *what each regulation demands* and *how this catalogue turns a
> Splunk detection into defensible compliance evidence* — without reading SPL.
>
> **Companion reading:** [`docs/coverage-methodology.md`](coverage-methodology.md)
> explains how clause coverage, priority-weighted coverage, and
> assurance-adjusted coverage are computed;
> [`docs/compliance-gaps.md`](compliance-gaps.md) lists every authoritative
> clause and whether at least one UC claims it; the versioned JSON API at
> `api/v1/compliance/*` is the machine-readable view of the same facts.

---

## Table of contents

1. [How to read this primer](#1-how-to-read-this-primer)
2. [Legend and terminology](#2-legend-and-terminology)
3. [Cross-cutting regulatory families (22.35 – 22.49)](#3-cross-cutting-regulatory-families-2235--2249)
4. [Tier-1 regulation deep dives](#4-tier-1-regulation-deep-dives) — 12 tier-1 + 1 tier-2 (NCA OTCC) in-depth entries
5. [Derivative regulations (propagated via `derivesFrom`)](#5-derivative-regulations-propagated-via-derivesfrom)
6. [Appendix A — Per-regulation subcategories at a glance](#appendix-a--per-regulation-subcategories-at-a-glance)
7. [Appendix B — Data-protection / privacy regulations worldwide](#appendix-b--data-protection--privacy-regulations-worldwide)
8. [Appendix C — Glossary](#appendix-c--glossary)
9. [Appendix D — Provenance and authoritative sources](#appendix-d--provenance-and-authoritative-sources)

---

## 1. How to read this primer

This primer is organised around two axes that match the way most compliance
programmes think:

- **By family** — 15 cross-cutting *families* (cat-22 subcategories 22.35
  through 22.49). A family answers a control question every major framework
  asks in some form, for example "can you prove your log data has not been
  tampered with?" or "can you demonstrate that breach notifications were sent
  within the statutory window?". Most auditors ask family-level questions
  long before they ask a clause-level question.
- **By regulation** — 18 tier-1 frameworks covered deeply, plus 48 per-regulation
  subcategories (cat-22 subcategories 22.1 through 22.34 and 22.50 through 22.63)
  and an additional 58 tier-2 frameworks in the appendix. Regulation-level reading
  is the right choice when you are answering a specific audit, mapping against a
  specific RFP, or preparing a regulator response.

Every entry — family or regulation — ends with a **"Where to look in the
catalogue"** block listing the exact cat-22 subcategory, a sampling of
representative UC IDs, and the relevant `api/v1/compliance/*` endpoint that
exposes the same information as machine-readable JSON.

This primer **does not** author new compliance opinions. Every clause citation,
authoritative URL, and topic summary in this document comes from
`data/regulations.json` (the single source of truth for regulatory metadata in
this repository), supplemented by public, non-proprietary regulator guidance
referenced in [Appendix D](#appendix-d--provenance-and-authoritative-sources).

---

## 2. Legend and terminology

### Tier badges

| Badge | Meaning |
|-------|---------|
| `T1`  | **Tier 1** — a top-priority regulation the catalogue targets at 100% common-clauses coverage. 22 frameworks; see `api/v1/compliance/coverage.json`. |
| `T2`  | **Tier 2** — authored to meaningful partial coverage; 58 frameworks including all 5 derivative privacy regulations. |
| `T3`  | **Tier 3** — referenced or meta-frameworks; 2 today (`meta-multi`, `ferc-cip`). |

### Assurance levels

Every `compliance[]` entry on every UC carries an `assurance` field with three
legal values:

| Assurance | Plain-language meaning | Audit implication |
|-----------|-------------------------|-------------------|
| `full` | The UC on its own satisfies the clause. | Defensible as primary evidence. |
| `partial` | The UC satisfies part of the clause but not all of it. | Defensible when combined with at least one other UC or control documented elsewhere. |
| `contributing` | The UC provides useful but non-primary evidence. | Supports assurance argument; should not be cited alone. |

Inherited entries (provenance = `derived-from-parent`) are always degraded one
step from the parent assurance. A UC that satisfies GDPR Art.32 at `full`
produces an inherited UK GDPR<sup class="ref">[<a href="#ref-41">41</a>]</sup> Art.32 entry at `partial`, never `full`.

### Clause citations

Clauses are cited using the regulator's own notation exactly as it appears in
the authoritative source:

- `Art.32(1)(b)` — Article 32, paragraph 1, sub-point (b) (GDPR style).
- `§1798.100` — California Civil Code section 1798.100 (CCPA<sup class="ref">[<a href="#ref-3">3</a>]</sup> style).
- `3.5.1`  — PCI DSS-style numbered requirement.
- `AC-2`   — NIST 800-53<sup class="ref">[<a href="#ref-23">23</a>]</sup>-style control identifier.
- `CC6.1`  — SOC 2<sup class="ref">[<a href="#ref-1">1</a>]</sup> / AICPA Trust Services Criterion identifier.

Every clause in `data/regulations.json` is validated against a regulator-
specific regular expression (`clauseGrammar`) so free-text values like
`"Art.  32  para. 1"` fail CI before they reach the API.

### Regulation priority weights

`priorityWeight` is a per-clause weight applied by the [coverage methodology](coverage-methodology.md).
Interpretation:

- `1.0` — **High** priority. Clause is widely cited, appears in the majority of
  audit questionnaires for that regulation, or is directly tied to a breach-
  notification or sanctionable obligation.
- `0.7` — **Medium** priority. Clause is commonly cited but is secondary to
  `1.0` clauses in most assessments.
- `0.5` and below — **Low** priority. Clause is normative but rarely the
  first question asked.

The `priorityWeightRubric` section of `data/regulations.json` documents the
full scale.

### Jurisdiction codes

This document uses ISO 3166-1 alpha-2 codes for jurisdictions (`US`, `EU`,
`UK`, `CH`, `BR`, `JP`, …) plus two multi-jurisdiction markers: `GLOBAL`
(international standards such as ISO 27001) and `EEA` (European Economic Area
— EU member states plus Iceland, Liechtenstein, Norway).

---

## 3. Cross-cutting regulatory families (22.35 – 22.49)

A **family** is a control question that virtually every tier-1 framework
asks in some form. The catalogue authors each family as a dedicated
subcategory of cat-22 (subcategories 22.35 – 22.49; each ships 5 UCs = 75 UCs
total). Families are the fastest path to multi-regulation evidence: every UC
in this section is tagged against 3 – 6 tier-1 regulations and against
the derivative privacy regulations too.

### 3.1 22.35 — Evidence continuity and log integrity

**Control question:** can the organisation prove that its log records — the
evidence on which every other control claim rests — have not been deleted,
altered, or gap-filled?

**Why it matters:** every regulation that demands audit trails implicitly
demands that those audit trails themselves be trustworthy. An auditor who
finds gaps in the log stream will discount every downstream control claim.

**Regulations that require this family:** GDPR Art.30 (records of
processing); PCI DSS 10.5.x (protect audit trails); HIPAA Security
§164.312(b) (audit controls); SOX ITGC (records retention); NIS2 Art.21.2(e)
(security of network and information systems — logging and monitoring);
ISO 27001:2022 A.8.15 (logging); NIST 800-53 AU-9 (protection of audit
information); SOC 2 CC7.2 (monitoring controls).

**What the catalogue delivers:** WORM-mode index settings audits, hash-chain
integrity verification, stream-ingest gap detection, UBA-like "search deleted"
detection on Splunk admin events, forwarder-to-indexer lag tracking with
alerting thresholds, HEC token rotation evidence, acknowledgement-mode
confirmation, and cross-cluster replication attestation.

**Where to look in the catalogue:**
[`content/cat-22-regulatory-compliance/` §22.35](../content/cat-22-regulatory-compliance/)
(UC-22.35.1 through UC-22.35.5) · `api/v1/compliance/ucs/22.35.1.json` ff.

### 3.2 22.36 — Data subject rights fulfillment

**Control question:** when a regulator, a data subject, or a court requests
access, correction, erasure, restriction, or portability of personal data,
can the organisation prove the request was fulfilled completely, on time,
and without collateral damage?

**Why it matters:** data subject rights (DSRs) are the civic face of every
modern privacy regime. Regulators treat DSR failures as an indicator of
deeper operational problems and will escalate to a formal investigation on
fewer than 100 unresolved requests in many EU member states.

**Regulations that require this family:** GDPR Art.15 – 22 (the "data
subject rights" chapter); UK GDPR Art.15 – 22 (identical onshoring);
CCPA §1798.100 (right to know), §1798.105 (right to delete), §1798.110
(right to portability), §1798.120 (right to opt-out of sale), §1798.125
(non-discrimination); LGPD<sup class="ref">[<a href="#ref-15">15</a>]</sup> Art.18 (data subject rights); APPI Arts.32 – 34
(disclosure, correction, cessation); Swiss nFADP Art.25 (right of access),
Art.26 (right to rectification). Operationally cited under HIPAA Privacy
§164.524 (access), §164.526 (amendment).

**What the catalogue delivers:** SLA-tracking dashboards per regulation and
per right, automated evidence generation on fulfilment (before-and-after
data-source diffs, record export hashes, tombstone confirmation across
downstream systems), denial-reason audit trails, identity-verification
anti-abuse heuristics, cross-system completeness attestation.

**Where to look in the catalogue:**
§22.36 (UC-22.36.1 through UC-22.36.5) · `api/v1/compliance/ucs/22.36.1.json` ff.

### 3.3 22.37 — Consent lifecycle and lawful basis

**Control question:** can the organisation prove, for every collection of
personal data, that a valid lawful basis existed at the moment of collection
and throughout the entire retention period? For consent specifically, can the
organisation replay every grant, change, and withdrawal with the exact
UI that was shown to the data subject?

**Why it matters:** lawful basis is the structural load-bearing element of
EU-style privacy regimes. A challenge that the stated basis was invalid
invalidates the processing *ab initio* and can force deletion of every
downstream analytical asset derived from that data.

**Regulations that require this family:** GDPR Art.6 (lawful basis), Art.7
(conditions for consent), Art.9 (special categories); UK GDPR Art.6, Art.7,
Art.9; LGPD Art.7 (lawful basis), Art.8 (consent); APPI Art.17 – 18
(acquisition, purpose limitation); CCPA §1798.120 (opt-out of sale) and the
new CPRA sensitive-personal-information opt-out; ePrivacy Directive
(cookie-layer consent). Operationally cited against PCI DSS-style "data
minimisation" audits for cardholder data.

**What the catalogue delivers:** consent-UI screenshot-hash verification,
consent-database immutable append log, lawful-basis-per-purpose inventory
with age-out alerting, granular consent-withdrawal propagation across
downstream systems, pre-authorisation legitimate-interest assessment
artefact tracking, special-category evidence-of-explicit-consent tagging.

**Where to look in the catalogue:**
§22.37 (UC-22.37.1 through UC-22.37.5) · `api/v1/compliance/ucs/22.37.1.json` ff.

### 3.4 22.38 — Cross-border transfer controls

**Control question:** can the organisation demonstrate, for every flow of
personal data that leaves a restricted jurisdiction, that a lawful transfer
mechanism existed at the moment of the transfer, has not been invalidated
since, and has complete contractual and technical safeguards backing it?

**Why it matters:** Schrems II (EU → US) and its successor cases have made
transfer mechanisms a live area of regulatory enforcement. A data-flow map
that cannot be reconstructed from logs is indistinguishable, from an
auditor's perspective, from a data-flow map that does not exist.

**Regulations that require this family:** GDPR Chapter V (Art.44 – 50 —
transfers to third countries), with particular focus on Art.46 (safeguards)
and Art.49 (derogations); UK GDPR Chapter V (the UK's International Data
Transfer Agreement plus the Addendum); CCPA §1798.140 (service-provider /
contractor distinction with out-of-state transfer implications); LGPD
Art.33 (international transfer); APPI Art.24 (cross-border transfer).

**What the catalogue delivers:** real-time destination-country detection on
cloud data flows, Schrems-II-aware DPIA refresh alerting, SCC-version
verification at connection-establishment time, TIA (transfer impact
assessment) [evidence packs](evidence-packs/README.md), adequacy-decision age tracking, model-contractual-
clauses-to-country mapping attestation.

**Where to look in the catalogue:**
§22.38 (UC-22.38.1 through UC-22.38.5) · `api/v1/compliance/ucs/22.38.1.json` ff.

### 3.5 22.39 — Incident notification timeliness

**Control question:** when an incident occurs, can the organisation prove
the discovery time, the risk-assessment decision, the notification to each
required recipient (regulators, data subjects, contractual counterparties),
and that every notification was sent within the statutory window?

**Why it matters:** the 72-hour GDPR breach-notification window, the
24-hour NIS2 early warning, and the 4-day DORA major-ICT-incident initial
notification are all hard statutory deadlines that produce automatic
sanctions on missed-by-minutes basis. Proving the timing is not optional;
failing to prove it converts a timely response into a non-compliant one.

**Regulations that require this family:** GDPR Art.33 (notification to
supervisory authority) and Art.34 (communication to data subjects); NIS2
Art.23 (incident reporting — 24h early warning, 72h notification, 1-month
final); DORA Art.19 (major ICT-related incident reporting); HIPAA Breach
Notification Rule §164.400 – 414 (Secretary of HHS, affected individuals);
CCPA §1798.82 (Cal. Civil Code breach notification); LGPD Art.48
(communication to ANPD); APPI Art.26 (mandatory leakage reporting);
Swiss nFADP Art.24 (notification to FDPIC); PCI DSS 12.10.x (incident
response plan with notification procedures).

**What the catalogue delivers:** incident-clock dashboards per regulation
with countdown-to-deadline visibility, notification-send proof extraction
(email gateway headers, regulator-portal API receipts), incident-severity
auto-routing with tailored notification templates, post-incident
retrospective evidence packaging.

**Where to look in the catalogue:**
§22.39 (UC-22.39.1 through UC-22.39.5) · `api/v1/compliance/ucs/22.39.1.json` ff.

### 3.6 22.40 — Privileged access evidence

**Control question:** for every action taken by a privileged account, can
the organisation prove the identity of the human behind the account, the
business justification, the approval chain, the session recording (where
required), and that access was revoked when the justification expired?

**Why it matters:** privileged access abuse is the largest single contributor
to breach costs in IBM's annual Cost of a Data Breach report. Every
regulation treats privileged access as a higher-assurance control tier with
dedicated clauses rather than folding it into general access management.

**Regulations that require this family:** SOX ITGC (CC6.1 / CC6.3 —
privileged-access governance); PCI DSS 7.2.x (privileged-access management),
8.3.x (MFA for privileged admin), 10.2.1 (logging of administrative
access); HIPAA Security §164.308(a)(4) (access authorisation); NIST
800-53 AC-2(7) (privileged accounts), AC-5 (separation of duties); ISO
27001:2022 A.8.2 (privileged access rights); SOC 2 CC6.3 (privileged
access); CMMC<sup class="ref">[<a href="#ref-34">34</a>]</sup> AC.L2-3.1.5 (least privilege); NIS2 Art.21.2(j) (access control
policies).

**What the catalogue delivers:** just-in-time (JIT) access grant attestation,
standing-privilege drift detection, privileged-session recording linkage,
impossible-travel on break-glass accounts, orphaned-sudoer discovery, PAM
vault-reconciliation audits, service-account-as-human detection.

**Where to look in the catalogue:**
§22.40 (UC-22.40.1 through UC-22.40.5) · `api/v1/compliance/ucs/22.40.1.json` ff.

### 3.7 22.41 — Encryption and key management attestation

**Control question:** can the organisation prove, for every dataset subject
to an encryption obligation, that the cipher is current, the keys are
rotated on schedule, the key-management service has no unauthorised access,
and that no long-lived plaintext or legacy-cipher exposure exists?

**Why it matters:** encryption is the most-commonly-cited mitigant for
breach-notification purposes (many jurisdictions allow a *sealed-envelope*
exception when the breached data was encrypted and the keys were not
compromised), so an audit failure here is a compound failure: it increases
both the probability and the impact of future breach notifications.

**Regulations that require this family:** GDPR Art.32(1)(a) (encryption as
an exemplar measure); UK GDPR Art.32(1)(a); HIPAA Security §164.312(a)(2)(iv)
and §164.312(e)(2)(ii) (addressable encryption); PCI DSS 3.5.x (protection
of stored account data) and 3.6.x (key-management processes); NIST 800-53
SC-12 (cryptographic key establishment and management), SC-13 (cryptographic
protection), SC-28 (protection of information at rest); ISO 27001:2022
A.8.24 (use of cryptography); NIS2 Art.21.2(h) (policies on cryptography
and encryption); DORA Art.9(4)(b) (cryptographic controls).

**What the catalogue delivers:** KMS audit-log ingestion with cipher-suite
drift alerting, certificate-expiry and weak-cipher inventorying, key-rotation
attestation with prior-key-hash linkage, HSM utilisation monitoring,
bring-your-own-key (BYOK) custody audits, TDE (transparent data encryption)
enablement verification.

**Where to look in the catalogue:**
§22.41 (UC-22.41.1 through UC-22.41.5) · `api/v1/compliance/ucs/22.41.1.json` ff.

### 3.8 22.42 — Change management and configuration baseline

**Control question:** can the organisation prove that every production
change (application deployment, infrastructure mutation, configuration drift
correction) was requested, approved, tested, audited, and reversible, and
that unauthorised changes are detected and corrected?

**Why it matters:** change management is the single most cited ITGC control
in SOX audits and the most common cause of material weakness findings.
Regulators also use change-management evidence as a probe for deeper
governance: if an organisation cannot reconstruct what changed in
production last Tuesday, the auditor assumes it cannot reconstruct anything
that follows from that change either.

**Regulations that require this family:** SOX ITGC (CC8.1 — change
management); PCI DSS 6.5.x (change-control procedures); ISO 27001:2022
A.8.32 (change management); NIST 800-53 CM-2 (baseline configuration), CM-3
(change control), CM-5 (access restrictions for change), CM-6 (configuration
settings), CM-8 (system component inventory); SOC 2 CC8.1 (change-management
controls); CMMC CM.L2-3.4.x (configuration management); NIS2 Art.21.2(i)
(basic cyber hygiene practices and cybersecurity training).

**What the catalogue delivers:** unauthorised-change detection across
IaC/OS/network layers, configuration-baseline drift dashboards with
per-environment tolerances, change-request-to-deployment trace reconciliation,
emergency-change retrospective evidence capture, pre-production-to-production
promotion attestation.

**Where to look in the catalogue:**
§22.42 (UC-22.42.1 through UC-22.42.5) · `api/v1/compliance/ucs/22.42.1.json` ff.

### 3.9 22.43 — Vulnerability management and patch SLAs

**Control question:** can the organisation prove that vulnerabilities are
discovered on a documented cadence, prioritised against a documented rubric,
patched within documented SLAs, and that exceptions (waivers) have a
documented compensating control and sunset date?

**Why it matters:** [vulnerability management](guides/vulnerability-management.md) is where compliance meets
live threat intelligence. Regulators increasingly expect CVSS-aware and
EPSS-aware prioritisation, so a vulnerability-management programme that
treats all CVEs equally will be flagged even if patch-latency metrics are
excellent.

**Regulations that require this family:** PCI DSS 6.3.x (vulnerability
identification and ranking), 11.3.x (scanning); NIST 800-53 RA-5
(vulnerability monitoring and scanning), SI-2 (flaw remediation), SI-5
(security alerts and directives); ISO 27001:2022 A.8.8 (management of
technical vulnerabilities); NIS2 Art.21.2(f) (vulnerability handling and
disclosure); DORA Art.8 (identification); CMMC RA.L2-3.11.x (risk
assessment); HIPAA Security §164.308(a)(1)(ii)(A) (risk analysis).

**What the catalogue delivers:** CVSS + EPSS combined prioritisation
dashboards, patch-latency percentile tracking per asset class, waiver-age
reporting with compensating-control attestation, [SBOM](license-inventory.md)-driven dependency
scanning, zero-day emergency patching workflow attestation.

**Where to look in the catalogue:**
§22.43 (UC-22.43.1 through UC-22.43.5) · `api/v1/compliance/ucs/22.43.1.json` ff.

### 3.10 22.44 — Third-party and supply-chain risk

**Control question:** can the organisation prove that every third party with
access to data or systems is identified, tiered, contracted appropriately,
reviewed on cadence, and monitored continuously for the relevant risk
indicators?

**Why it matters:** SolarWinds, Kaseya, Log4j, MOVEit, and the broader
2023-2025 enforcement of [supply-chain](signed-provenance.md)-focused rules (NIS2, DORA, SEC
four-day rule, EU CRA) have elevated third-party risk from a procurement
checklist to a primary auditable control domain. Regulators now treat
third-party failure as if it were first-party failure, except for
contractually-limited liability windows.

**Regulations that require this family:** NIS2 Art.21.2(d) (supply chain
security); DORA Art.28 – 30 (ICT third-party risk management); SOX ITGC
(service-organisation control reports); PCI DSS 12.8.x (third-party service
providers), 12.9 (due diligence); ISO 27001:2022 A.5.19 – 5.23 (supplier
relationships); NIST 800-53 SR-2 (supply chain risk management plan);
HIPAA Security §164.308(b) (business associate contracts); SOC 2 CC9.2
(vendor management); CMMC SA.L2-3.4.x ([supply-chain](signed-provenance.md) protection).

**What the catalogue delivers:** continuous vendor-risk-score ingestion,
[SBOM](license-inventory.md)-to-vendor cross-reference, vendor-access expiry automation,
contract-renewal-triggered risk-review workflows, subprocessor discovery,
external-attack-surface-management (EASM) correlation with owned third
parties.

**Where to look in the catalogue:**
§22.44 (UC-22.44.1 through UC-22.44.5) · `api/v1/compliance/ucs/22.44.1.json` ff.

### 3.11 22.45 — Backup integrity and recovery testing

**Control question:** can the organisation prove that backups are created,
encrypted, isolated (air-gapped where required), tested for restorability,
and that the RTO/RPO commitments have been exercised in the past 12 months
with documented results?

**Why it matters:** ransomware-era regulators and insurers alike have
shifted the compliance conversation from "do you have backups?" to "can you
restore from them on demand?". An untested backup is treated as a failed
control even if the storage layer is compliant, because failure is only
visible at restore time.

**Regulations that require this family:** NIS2 Art.21.2(c) (business
continuity, backup management and crisis management); DORA Art.12 –14
(backup policies and restoration); HIPAA Security §164.308(a)(7) (contingency
plan); PCI DSS 12.10.x (incident response plan — includes recovery); ISO
27001:2022 A.8.13 (information backup); NIST 800-53 CP-9 (system backup),
CP-10 (system recovery and reconstitution); SOX ITGC (disaster-recovery
and business-continuity controls); SOC 2 A1.2 (system availability).

**What the catalogue delivers:** restore-test success-rate dashboards,
RPO/RTO measurement at bar-raising granularity, air-gap integrity
verification, immutable-backup-policy attestation, cross-region replication
lag alerting, restore-to-clean-room attestation for ransomware scenarios.

**Where to look in the catalogue:**
§22.45 (UC-22.45.1 through UC-22.45.5) · `api/v1/compliance/ucs/22.45.1.json` ff.

### 3.12 22.46 — Training and awareness

**Control question:** can the organisation prove that every role-relevant
staff member received training, passed comprehension assessments, received
refreshers on cadence, and that new hires are trained within the
onboarding SLA?

**Why it matters:** training is the only control that regulators assume
will degrade over time without active maintenance. Regulators therefore
expect both point-in-time completion evidence *and* cadence evidence,
and treat stale training as a material weakness in every financial and
healthcare framework.

**Regulations that require this family:** HIPAA Security §164.308(a)(5)
(security awareness and training); PCI DSS 12.6.x (security awareness
programme); ISO 27001:2022 A.6.3 (information security awareness,
education and training); NIST 800-53 AT-2 (literacy training and awareness),
AT-3 (role-based training), AT-4 (training records); NIS2 Art.20 (governance);
DORA Art.13 (ICT-related incident learning and evolving — training);
CMMC AT.L2-3.2.x (awareness and training); SOC 2 CC1.4 (competence).

**What the catalogue delivers:** role-based training-completion dashboards,
phishing-simulation campaign evidence packaging, refresher-cadence drift
alerting, new-hire training-SLA reporting, regulator-specific training-
topic-mapping attestation.

**Where to look in the catalogue:**
§22.46 (UC-22.46.1 through UC-22.46.5) · `api/v1/compliance/ucs/22.46.1.json` ff.

### 3.13 22.47 — Control testing evidence freshness

**Control question:** for every control claimed in a management assertion
(SOC 2 Type 2, SOX 404, ISO 27001 Statement of Applicability, PCI DSS RoC),
can the organisation prove that the control was operating effectively
during the entire assessment period and that the evidence demonstrating
effectiveness is itself fresh?

**Why it matters:** most tier-1 audits are period-of-operation audits, not
point-in-time audits. A control that was effective in January and July but
not in April is a failed control for an annual attestation. Regulators and
external auditors therefore demand continuous evidence of operating
effectiveness rather than periodic snapshots.

**Regulations that require this family:** SOX ITGC (management assertion
and external auditor attestation — operating effectiveness); SOC 2
(AICPA TSP 100 — operating effectiveness); ISO 27001:2022 Clause 9
(performance evaluation), A.5.35 (independent review of information
security); PCI DSS 12.11 (documentation and review); NIST CSF IMPROVE
function; SOC 2 CC1.5 (accountability).

**What the catalogue delivers:** continuous-control-monitoring (CCM)
dashboards per framework, operating-effectiveness sampling automation,
control-owner-review-attestation workflows, exception-investigation audit
trails, period-of-operation heatmaps for external audits.

**Where to look in the catalogue:**
§22.47 (UC-22.47.1 through UC-22.47.5) · `api/v1/compliance/ucs/22.47.1.json` ff.

### 3.14 22.48 — Segregation of duties enforcement

**Control question:** for every critical transaction flow (payment
initiation, privileged-access change, data-export authorisation, financial
close), can the organisation prove that the initiator, approver, and
reviewer roles are held by distinct individuals and that conflicting-role
combinations are either absent or compensated?

**Why it matters:** segregation of duties (SoD) is the structural defence
against insider fraud and is tested automatically in every major ERP and
financial audit. A breached SoD rule is treated by SOX auditors as
presumptively material until the organisation can prove no fraudulent
transaction resulted — a burden of proof that is expensive to discharge.

**Regulations that require this family:** SOX ITGC (segregation-of-duties
across application access and change management); NIST 800-53 AC-5
(separation of duties); ISO 27001:2022 A.5.3 (segregation of duties);
SOC 2 CC6.3; PCI DSS 6.4.x (change management and SoD); HIPAA Security
§164.308(a)(3)(ii)(A) (workforce-clearance procedure implicit SoD); MAS
TRM 11.2 (segregation of duties); MiFID II<sup class="ref">[<a href="#ref-8">8</a>]</sup> Delegated Regulation Art.26
(record-keeping and SoD).

**What the catalogue delivers:** conflict-matrix-driven access analysis,
transaction-level SoD-violation detection, compensating-control-evidence
packaging, emergency-SoD-override attestation, sensitive-access-review
(SAR) workflow integration.

**Where to look in the catalogue:**
§22.48 (UC-22.48.1 through UC-22.48.5) · `api/v1/compliance/ucs/22.48.1.json` ff.

### 3.15 22.49 — Retention and disposal automation

**Control question:** for every data class subject to a retention obligation
(minimum retention for SOX, maximum retention for GDPR, conditional
retention for litigation hold), can the organisation prove that records
are retained exactly as long as required — no less, no more — and
disposed of securely with evidence of disposal?

**Why it matters:** retention obligations are simultaneously a floor (don't
delete too early) and a ceiling (don't keep too long). They are also
contradictory across jurisdictions — GDPR's "data minimisation and storage
limitation" pulls towards deletion while SOX's "records retention" pulls
towards preservation for the same dataset. The catalogue provides the
evidence that the organisation has resolved the contradiction in a
documented, auditable way.

**Regulations that require this family:** GDPR Art.5(1)(e) (storage
limitation), Art.17 (right to erasure); UK GDPR Art.5(1)(e), Art.17;
CCPA §1798.100(d) (reasonable retention), §1798.105 (right to delete);
LGPD Art.6(V) (necessity), Art.16 (termination of processing); SOX
§103 (public-accounting records retention); HIPAA §164.316(b)(2)(i)
(six-year retention of policies and procedures); PCI DSS 3.2.x (keep
cardholder data storage to a minimum), 9.10 (cryptographic erasure);
ISO 27001:2022 A.5.33 (protection of records); NIST 800-53 SI-12
(information management and retention); Swiss nFADP Art.6(4) (data
retention minimisation).

**What the catalogue delivers:** per-data-class retention-policy engines
with TTL (time-to-live) enforcement across warm and cold storage,
legal-hold override attestation, verifiable cryptographic-erasure
evidence, cross-system deletion-propagation audit, retention-policy-drift
alerting.

**Where to look in the catalogue:**
§22.49 (UC-22.49.1 through UC-22.49.5) · `api/v1/compliance/ucs/22.49.1.json` ff.

---

## 4. Tier-1 regulation deep dives

Each entry is structured as **overview · who must comply · key clauses ·
what the catalogue delivers · where to look**. Authoritative URLs and
clause-grammar regexes for every regulation are in `data/regulations.json`.

### 4.1 GDPR — General Data Protection Regulation (EU/EEA) · `T1`

**Regulation:** Regulation (EU) 2016/679<sup class="ref">[<a href="#ref-9">9</a>]</sup> (*GDPR*), in force 25 May 2018.
Applies to the processing of personal data in the European Economic Area,
plus extraterritorial reach to non-EEA controllers that offer goods or
services to EEA data subjects (Art.3).

**Who must comply:** all controllers and processors handling EEA personal
data. Public authorities with specific carve-outs in Art.2.

**Key clauses and catalogue coverage:**

| Clause | Topic | Priority | Catalogue coverage |
|--------|-------|----------|---------------------|
| Art.5 | Principles of processing | 1.0 | full — cross-cutting via 22.37, 22.49 |
| Art.6 | Lawful basis | 1.0 | full — cross-cutting via 22.37 |
| Art.7 | Conditions for consent | 0.7 | full — cross-cutting via 22.37 |
| Art.15 | Right of access | 1.0 | full — cross-cutting via 22.36 |
| Art.16 | Right to rectification | 0.7 | full — cross-cutting via 22.36 |
| Art.17 | Right to erasure | 1.0 | full — 22.36 + 22.49 |
| Art.18 | Right to restrict processing | 0.7 | full — 22.36 |
| Art.20 | Right to data portability | 0.7 | full — 22.36 |
| Art.21 | Right to object | 0.7 | full — 22.36 |
| Art.22 | Automated decision making | 0.7 | partial — 22.1 dedicated UCs |
| Art.25 | Data protection by design and by default | 1.0 | partial — 22.1 + cross-cutting |
| Art.30 | Records of processing activities | 1.0 | full — 22.35 |
| Art.32 | Security of processing | 1.0 | full — 22.1 + 22.40 + 22.41 + 22.42 |
| Art.33 | Notification to supervisory authority | 1.0 | full — 22.39 |
| Art.34 | Communication to data subjects | 1.0 | full — 22.39 |
| Art.35 | Data protection impact assessment | 1.0 | partial — 22.1 |
| Art.44 | General principle for transfers | 1.0 | full — 22.38 |
| Art.46 | Transfers subject to safeguards | 1.0 | full — 22.38 |
| Art.49 | Derogations | 0.5 | partial — 22.38 |
| Art.50 | International cooperation | 0.3 | not authored — outside Splunk scope |

**What the catalogue delivers:** 100 % of the tier-1 `commonClauses` are
covered. Every clause above `0.3` priority-weight has at least one UC with
`full` or `partial` assurance. Full artefacts: cat-22 §22.1 (50 dedicated UCs)
plus 15 cross-cutting families (22.35 – 22.49) that each tag GDPR where
applicable.

**Where to look:** §22.1 (GDPR) · `api/v1/compliance/regulations/gdpr.json`
· [`api/v1/compliance/regulations/gdpr@2016-679.json`](../api/v1/compliance/regulations/gdpr@2016-679.json).

### 4.2 UK GDPR — UK General Data Protection Regulation (UK) · `T2` · derivative

**Regulation:** UK GDPR as onshored via the European Union (Withdrawal) Act
2018 and amended by the Data Protection, Privacy and Electronic
Communications (Amendments etc.) (EU Exit) Regulations 2019/419. Clause
numbering is preserved 1:1 with EU GDPR. Supervisory authority is the
Information Commissioner's Office (ICO).

**Who must comply:** all controllers and processors handling UK personal
data, including non-UK organisations targeting the UK market.

**Key clauses and catalogue coverage:** identical clause numbering to GDPR
above. The catalogue applies the `derivesFrom` graph to propagate every
GDPR mapping into UK GDPR with one-step assurance
degradation (GDPR `full` → UK GDPR `partial`, GDPR `partial` → UK GDPR
`contributing`). Known divergences flagged as `derivationSource.divergenceNote`:

- **Art.45 (Adequacy decisions):** UK adequacy decisions are managed by
  the ICO and the UK government; not by the European Commission.
- **Art.50 (International cooperation):** the UK has its own international
  cooperation mechanisms outside the EU framework.

**What the catalogue delivers:** the entire UK GDPR coverage position is
inherited from GDPR; no UK-specific clauses require native UCs today.
Organisations operating under both regimes simultaneously can cite a single
UC for both obligations, with the derivation object tracing the inference.

**Where to look:** `api/v1/compliance/regulations/uk-gdpr.json` · shared
evidence flows with §22.1.

### 4.3 PCI DSS v4.0 — Payment Card Industry Data Security Standard (GLOBAL) · `T1`

**Regulation:** PCI DSS v4.0<sup class="ref">[<a href="#ref-28">28</a>]</sup> (30 Mar 2024 effective; v3.2.1 sunset 31 Mar
2024). Issued by the PCI Security Standards Council (PCI SSC); mandated
contractually by card brands. Supplemented by **PCI DSS v4.0.1** (Jun 2024)
minor clarification.

**Who must comply:** every entity that stores, processes, or transmits
cardholder data or sensitive authentication data — merchants, processors,
acquirers, issuers, and service providers.

**Key clauses and catalogue coverage:**

| Clause | Topic | Priority | Catalogue coverage |
|--------|-------|----------|---------------------|
| 1.4.x | Network security controls | 1.0 | full — §22.11 |
| 3.5.x | Protection of stored account data | 1.0 | full — §22.11 + 22.41 |
| 6.3.x | Identify and manage vulnerabilities | 1.0 | full — §22.11 + 22.43 |
| 7.2.x | Privileged-access management | 1.0 | full — §22.11 + 22.40 |
| 8.3.x | MFA for administrative access | 1.0 | full — §22.11 + 22.40 |
| 10.2.x | Audit logs | 1.0 | full — §22.11 + 22.35 |
| 11.3.x | Vulnerability scanning and pen-testing | 1.0 | full — §22.11 + 22.43 |

**What the catalogue delivers:** 100 % tier-1 coverage. §22.11 ships
220 dedicated PCI DSS UCs, including cardholder-data-environment
boundary detection, CHD-in-logs prevention, PAN-in-email detection,
key-custody attestation, and PCI DSS 4.0 customised-approach-alternative
evidence packaging.

**Cisco ISE evidence.** Cisco Identity Services Engine<sup class="ref">[<a href="#ref-4">4</a>]</sup> is a primary
evidence source for clauses 1.4 (segmentation around the CDE), 4.2
(strong cryptography for CHD in transit), 8.3-8.6 (strong
authentication, MFA, and per-account credentials), and 10.2 (audit
logs for every authentication and access-policy decision). Strong
authentication for CDE access is captured by EAP-TLS posture
([UC-17.1.38](../content/cat-17-network-security-zero-trust/UC-17.1.38.json),
[UC-17.1.69](../content/cat-17-network-security-zero-trust/UC-17.1.69.json),
[UC-17.1.70](../content/cat-17-network-security-zero-trust/UC-17.1.70.json));
account lockout and brute-force resistance by
[UC-17.1.71](../content/cat-17-network-security-zero-trust/UC-17.1.71.json);
TrustSec/SGT segmentation evidence by
[UC-17.1.36](../content/cat-17-network-security-zero-trust/UC-17.1.36.json) and
[UC-17.1.75](../content/cat-17-network-security-zero-trust/UC-17.1.75.json);
TACACS+ command audit for CDE network device administration by
[UC-17.1.43](../content/cat-17-network-security-zero-trust/UC-17.1.43.json).
The cat-22 wrappers UC-22.11.107 through UC-22.11.110 package these
into auditor-ready evidence under the customised-approach pattern.
See [`docs/guides/cisco-ise.md`](guides/cisco-ise.md) for the full
reference architecture.

**Where to look:** §22.11 · `api/v1/compliance/regulations/pci-dss.json` ·
[`api/v1/compliance/regulations/pci-dss@v4.0.json`](../api/v1/compliance/regulations/pci-dss@v4.0.json).

### 4.4 HIPAA Security — Health Insurance Portability and Accountability Act Security Rule (US) · `T1`

**Regulation:** HIPAA Security Rule<sup class="ref">[<a href="#ref-37">37</a>]</sup>, 45 CFR Part 160 and Part 164
Subparts A and C (*Security Standards for the Protection of Electronic
Protected Health Information*). Supplemented by the **HITECH Act** breach
notification provisions and the **Omnibus Rule 2013**.

**Who must comply:** *covered entities* (healthcare providers, health
plans, healthcare clearinghouses) and their *business associates*.

**Key clauses and catalogue coverage:**

| Clause | Topic | Priority | Catalogue coverage |
|--------|-------|----------|---------------------|
| §164.308(a)(1) | Security management process | 1.0 | full — §22.10 |
| §164.308(a)(3) | Workforce security | 1.0 | full — §22.10 + 22.40 |
| §164.308(a)(4) | Information access management | 1.0 | full — §22.10 + 22.40 |
| §164.308(a)(5) | Security awareness and training | 1.0 | full — §22.10 + 22.46 |
| §164.308(a)(6) | Security incident procedures | 1.0 | full — §22.10 + 22.39 |
| §164.308(a)(7) | Contingency plan | 1.0 | full — §22.10 + 22.45 |
| §164.310 | Physical safeguards | 0.7 | partial — §22.10 |
| §164.312(a) | Access control | 1.0 | full — §22.10 + 22.40 |
| §164.312(b) | Audit controls | 1.0 | full — §22.10 + 22.35 |
| §164.312(c) | Integrity | 1.0 | full — §22.10 |
| §164.312(d) | Person or entity authentication | 1.0 | full — §22.10 |
| §164.312(e) | Transmission security | 1.0 | full — §22.10 + 22.41 |
| §164.316 | Policies and procedures | 0.7 | partial — §22.10 |
| Breach Notification §164.400-414 | Breach notification | 1.0 | full — §22.10 + 22.39 |

**What the catalogue delivers:** 100 % tier-1 coverage. §22.10 ships
58 dedicated HIPAA UCs covering ePHI access logging, audit-trail gap
detection, encryption of ePHI at rest and in transit, minimum-necessary
rule enforcement, workforce-termination access revocation, and
breach-risk-assessment artefact generation.

**[Cisco ISE](guides/cisco-ise.md) evidence.** For workforce access to ePHI-bearing systems,
Cisco ISE provides the §164.308(a)(4) information-access-management
record (Active-Directory-driven authorisation policies attested by
[UC-17.1.29](../content/cat-17-network-security-zero-trust/UC-17.1.29.json)),
the §164.312(a)(1) access-control evidence (segmentation drift via
[UC-17.1.36](../content/cat-17-network-security-zero-trust/UC-17.1.36.json),
[UC-17.1.75](../content/cat-17-network-security-zero-trust/UC-17.1.75.json)),
the §164.312(b) audit-control trail (TACACS+ command-accounting via
[UC-17.1.43](../content/cat-17-network-security-zero-trust/UC-17.1.43.json),
ANC actions via
[UC-17.1.42](../content/cat-17-network-security-zero-trust/UC-17.1.42.json)),
and the §164.312(d) person-or-entity-authentication evidence (EAP-TLS
via
[UC-17.1.38](../content/cat-17-network-security-zero-trust/UC-17.1.38.json)).
The cat-22 wrappers UC-22.10.57 (access control) and UC-22.10.58
(audit controls) package this evidence per clause for OCR submission.

**Where to look:** §22.10 · `api/v1/compliance/regulations/hipaa-security.json`.

### 4.5 SOX ITGC — Sarbanes-Oxley IT General Controls (US) · `T1`

**Regulation:** Sarbanes-Oxley<sup class="ref">[<a href="#ref-33">33</a>]</sup> Act §302 and §404 (management assertion and
external auditor attestation of internal control over financial reporting),
operationalised through **PCAOB AS 2201<sup class="ref">[<a href="#ref-29">29</a>]</sup>** and **COBIT** / **COSO 2013**
frameworks. IT general controls (ITGC) are the IT subset that financial
controls depend on.

**Who must comply:** US public companies (SEC registrants) and non-US
filers on US markets. SOX ITGC is also adopted as a de facto standard
for private-equity-backed companies pursuing IPO readiness.

**Key clauses and catalogue coverage:** SOX ITGC is organised by control
objective rather than numbered clause. The catalogue maps to standard
objective taxonomy:

| Objective | Topic | Priority | Catalogue coverage |
|-----------|-------|----------|---------------------|
| CC6.1 | Logical access controls | 1.0 | full — §22.12 + 22.40 |
| CC6.3 | Privileged access | 1.0 | full — §22.12 + 22.40 |
| CC7.1 | Monitoring of controls | 1.0 | full — §22.12 + 22.47 |
| CC7.2 | System monitoring for anomalies | 1.0 | full — §22.12 + 22.35 |
| CC8.1 | Change management | 1.0 | full — §22.12 + 22.42 |
| CC9.1 | Incident management | 1.0 | full — §22.12 + 22.39 |
| CC9.2 | Vendor management | 1.0 | full — §22.12 + 22.44 |

**What the catalogue delivers:** 100 % tier-1 coverage. §22.12 ships
86 dedicated SOX ITGC UCs plus the cross-cutting SoD family (22.48).
The catalogue is designed to produce both point-in-time evidence (snapshot
at year-end) and period-of-operation evidence (continuous-control-monitoring
dashboards) which aligns with the SOX Type 2-equivalent testing model.

**Cisco ISE evidence.** For the *Logical Access* objective (network
device administration, the hidden third leg of access management
behind application access and infrastructure access), Cisco ISE
generates the per-administrator command-accounting trail through
TACACS+ ([UC-17.1.43](../content/cat-17-network-security-zero-trust/UC-17.1.43.json))
and the AD-Connector authorisation provenance
([UC-17.1.29](../content/cat-17-network-security-zero-trust/UC-17.1.29.json)).
For the *Change Management* objective, ISE upgrade tracking
([UC-17.1.49](../content/cat-17-network-security-zero-trust/UC-17.1.49.json))
provides the change-window evidence auditors expect. The cat-22
wrappers UC-22.12.41 (privileged access), UC-22.12.42 (segregation
of duties), and UC-22.12.43 (change authorisation) package this for
PCAOB AS 2201 walkthroughs.

**Where to look:** §22.12 · `api/v1/compliance/regulations/sox-itgc.json`.

### 4.6 SOC 2 — AICPA Trust Services Criteria (US / GLOBAL) · `T1`

**Regulation:** SOC 2 reports attest against the AICPA **Trust Services
Criteria** (TSC 2017, revised 2022) covering Security, Availability,
Processing Integrity, Confidentiality, and Privacy. Unlike ISO 27001
which certifies, SOC 2 attests — a report is produced by a CPA firm
describing the service organisation's controls and the operating
effectiveness during a period (Type 2).

**Who must comply:** cloud service providers, SaaS vendors, managed-
service providers, and any organisation with contractual obligations
that require SOC 2 reports for downstream customers.

**Key clauses and catalogue coverage:**

| TSC | Topic | Priority | Catalogue coverage |
|-----|-------|----------|---------------------|
| CC1.x | Control environment | 0.7 | partial — §22.8 |
| CC2.x | Communication and information | 0.7 | partial — §22.8 |
| CC3.x | Risk assessment | 0.7 | partial — §22.8 + 22.43 |
| CC4.x | Monitoring activities | 1.0 | full — §22.8 + 22.35 + 22.47 |
| CC5.x | Control activities | 1.0 | full — §22.8 |
| CC6.x | Logical and physical access controls | 1.0 | full — §22.8 + 22.40 |
| CC7.x | System operations | 1.0 | full — §22.8 + 22.39 |
| CC8.x | Change management | 1.0 | full — §22.8 + 22.42 |
| CC9.x | Risk mitigation | 1.0 | full — §22.8 + 22.44 |
| A1.x | Availability | 0.7 | partial — §22.8 + 22.45 |

**What the catalogue delivers:** 100 % tier-1 coverage. §22.8 ships 80 UCs
dedicated to SOC 2 controls with particular focus on continuous control
monitoring, which is the hallmark of a mature Type 2 programme.

**Cisco ISE evidence.** For *CC6.1 Logical access* and *CC6.6
Segmentation*, Cisco ISE provides population-level evidence that
controls operated continuously over the audit period: AD-store
health and authentication coverage
([UC-17.1.29](../content/cat-17-network-security-zero-trust/UC-17.1.29.json)),
EAP-TLS posture and lockout
([UC-17.1.38](../content/cat-17-network-security-zero-trust/UC-17.1.38.json),
[UC-17.1.71](../content/cat-17-network-security-zero-trust/UC-17.1.71.json)),
auto-quarantine effectiveness
([UC-17.1.41](../content/cat-17-network-security-zero-trust/UC-17.1.41.json)),
and TrustSec/dACL segmentation drift
([UC-17.1.36](../content/cat-17-network-security-zero-trust/UC-17.1.36.json),
[UC-17.1.75](../content/cat-17-network-security-zero-trust/UC-17.1.75.json),
[UC-17.1.76](../content/cat-17-network-security-zero-trust/UC-17.1.76.json)).
The cat-22 wrapper UC-22.8.40 packages logical-access and
segmentation evidence into a SOC 2 Type 2 deliverable.

**Where to look:** §22.8 · `api/v1/compliance/regulations/soc-2.json`.

### 4.7 ISO 27001:2022 — Information Security Management System (GLOBAL) · `T1`

**Regulation:** ISO/IEC 27001:2022<sup class="ref">[<a href="#ref-17">17</a>]</sup> (*Information security, cybersecurity
and privacy protection — Information security management systems —
Requirements*), with Annex A controls aligned to ISO/IEC 27002:2022<sup class="ref">[<a href="#ref-18">18</a>]</sup>
(reduced from 114 controls in the 2013 edition to **93 controls** in 4
themes: organisational, people, physical, technological).

**Who must comply:** any organisation seeking ISO 27001 certification, and
contractual adoption is common in EU public-sector and regulated-industry
procurement.

**Key clauses and catalogue coverage:**

| Clause | Topic | Priority | Catalogue coverage |
|--------|-------|----------|---------------------|
| A.5.x | Organisational controls (37) | 0.7 | partial — §22.6 |
| A.6.x | People controls (8) | 0.5 | partial — §22.6 + 22.46 |
| A.7.x | Physical controls (14) | 0.5 | partial — §22.6 |
| A.8.x | Technological controls (34) | 1.0 | full — §22.6 + cross-cutting |
| Clause 9 | Performance evaluation | 1.0 | full — §22.6 + 22.47 |

**What the catalogue delivers:** 100 % tier-1 `commonClauses` coverage.
§22.6 ships 116 UCs dedicated to ISO 27001 Annex A controls.

**Cisco ISE evidence.** For Annex A.5 organisational controls and A.8
technological controls related to identity and network access, Cisco
ISE provides direct evidence: A.5.16 identity management
([UC-17.1.29](../content/cat-17-network-security-zero-trust/UC-17.1.29.json),
[UC-17.1.38](../content/cat-17-network-security-zero-trust/UC-17.1.38.json),
[UC-17.1.71](../content/cat-17-network-security-zero-trust/UC-17.1.71.json)),
A.5.30 ICT readiness for business continuity
([UC-17.1.28](../content/cat-17-network-security-zero-trust/UC-17.1.28.json),
[UC-17.1.30](../content/cat-17-network-security-zero-trust/UC-17.1.30.json),
[UC-17.1.49](../content/cat-17-network-security-zero-trust/UC-17.1.49.json)),
A.8.2 privileged access rights (TACACS+ via
[UC-17.1.43](../content/cat-17-network-security-zero-trust/UC-17.1.43.json)),
and A.8.15 logging
([UC-17.1.42](../content/cat-17-network-security-zero-trust/UC-17.1.42.json)).
The cat-22 wrappers UC-22.6.56, UC-22.6.57, and UC-22.6.58 package
this for ISMS audits.

**Where to look:** §22.6 · `api/v1/compliance/regulations/iso-27001.json`.

### 4.8 NIST CSF 2.0 — Cybersecurity Framework (US / GLOBAL) · `T1`

**Regulation:** NIST Cybersecurity Framework<sup class="ref">[<a href="#ref-21">21</a>]</sup> 2.0 (Feb 2024 revision of the
original 2014 framework). Organised around six functions: **Govern,
Identify, Protect, Detect, Respond, Recover**. Adopted by US federal
sector-specific regulators (TSA, FERC, CISA) and globally as a voluntary
framework that is frequently mandated contractually.

**Who must comply:** CSF is voluntary but widely mandated. US federal
contractors with FISMA obligations, US critical-infrastructure operators,
and increasingly EU/UK NIS2-aligned operators use CSF as an organising
framework.

**Key clauses and catalogue coverage:**

| Function | Topic | Priority | Catalogue coverage |
|----------|-------|----------|---------------------|
| GOVERN | Governance | 1.0 | full — §22.7 |
| IDENTIFY | Asset and risk identification | 1.0 | full — §22.7 + 22.43 + 22.44 |
| PROTECT | Controls and training | 1.0 | full — §22.7 + 22.40 + 22.41 + 22.46 |
| DETECT | Detection | 1.0 | full — §22.7 + 22.35 + 22.47 |
| RESPOND | Incident response | 1.0 | full — §22.7 + 22.39 |
| RECOVER | Recovery | 1.0 | full — §22.7 + 22.45 |

**What the catalogue delivers:** 100 % tier-1 coverage. §22.7 ships 50 UCs;
every CSF function has dedicated UCs plus cross-cutting coverage.

**Where to look:** §22.7 · `api/v1/compliance/regulations/nist-csf.json`.

### 4.9 NIST 800-53 Rev.5 — Security and Privacy Controls (US) · `T1`

**Regulation:** NIST Special Publication 800-53 Revision 5 (*Security and
Privacy Controls for Information Systems and Organizations*), with
controls organised into 20 families (AC, AU, CM, IA, IR, SC, SI, …).
Baseline catalogues: Low, Moderate, High, Privacy. The **800-53B** baseline
document defines which controls apply to each impact level.

**Who must comply:** US federal information systems (FISMA), most
DoD systems (via DFARS), and contractually by FedRAMP<sup class="ref">[<a href="#ref-39">39</a>]</sup>-authorised cloud
service providers. Widely adopted as a reference control catalogue by
non-federal organisations worldwide.

**Key clauses and catalogue coverage:**

| Family | Topic | Priority | Catalogue coverage |
|--------|-------|----------|---------------------|
| AC | Access control | 1.0 | full — §22.14 + 22.40 |
| AU | Audit and accountability | 1.0 | full — §22.14 + 22.35 |
| CM | Configuration management | 1.0 | full — §22.14 + 22.42 |
| IA | Identification and authentication | 1.0 | full — §22.14 |
| IR | Incident response | 1.0 | full — §22.14 + 22.39 |
| RA | Risk assessment | 1.0 | full — §22.14 + 22.43 |
| SC | System and communications protection | 1.0 | full — §22.14 + 22.41 |
| SI | System and information integrity | 1.0 | full — §22.14 + 22.43 |
| SR | Supply chain risk management | 1.0 | full — §22.14 + 22.44 |
| CP | Contingency planning | 1.0 | full — §22.14 + 22.45 |
| AT | Awareness and training | 0.7 | full — §22.14 + 22.46 |

**What the catalogue delivers:** 100 % tier-1 coverage. §22.14 ships
81 UCs dedicated to 800-53 Rev.5 controls with `controlFamily` tags
that align with the OSCAL component-definition facade at
`api/v1/oscal/component-definitions/*`.

**Cisco ISE evidence.** Cisco ISE is one of the deepest evidence
sources in the catalogue for the AC, AU, IA, IR, and SI families:
AC-2/3/6 access enforcement and least privilege via
[UC-17.1.29](../content/cat-17-network-security-zero-trust/UC-17.1.29.json),
[UC-17.1.43](../content/cat-17-network-security-zero-trust/UC-17.1.43.json),
[UC-17.1.51](../content/cat-17-network-security-zero-trust/UC-17.1.51.json);
IA-2/5/8 strong authentication and credential management via
[UC-17.1.38](../content/cat-17-network-security-zero-trust/UC-17.1.38.json),
[UC-17.1.39](../content/cat-17-network-security-zero-trust/UC-17.1.39.json),
[UC-17.1.69](../content/cat-17-network-security-zero-trust/UC-17.1.69.json),
[UC-17.1.71](../content/cat-17-network-security-zero-trust/UC-17.1.71.json);
AU-2/6/12 audit logging via
[UC-17.1.42](../content/cat-17-network-security-zero-trust/UC-17.1.42.json),
[UC-17.1.58](../content/cat-17-network-security-zero-trust/UC-17.1.58.json);
IR-4/5 incident response via
[UC-17.1.41](../content/cat-17-network-security-zero-trust/UC-17.1.41.json),
[UC-17.1.80](../content/cat-17-network-security-zero-trust/UC-17.1.80.json);
SI-4 system monitoring via
[UC-17.1.40](../content/cat-17-network-security-zero-trust/UC-17.1.40.json),
[UC-17.1.67](../content/cat-17-network-security-zero-trust/UC-17.1.67.json),
[UC-17.1.68](../content/cat-17-network-security-zero-trust/UC-17.1.68.json),
[UC-17.1.74](../content/cat-17-network-security-zero-trust/UC-17.1.74.json).
The cat-22 wrapper UC-22.14.81 packages identity-and-authentication
evidence to the OSCAL component-definition facade.

**Where to look:** §22.14 · `api/v1/compliance/regulations/nist-800-53.json`
· [`api/v1/oscal/catalogs/nist-sp-800-53-r5.normalised.json`](../api/v1/oscal/catalogs/nist-sp-800-53-r5.normalised.json).

### 4.10 NIS2 — Network and Information Security Directive 2 (EU) · `T1`

**Regulation:** Directive (EU) 2022/2555<sup class="ref">[<a href="#ref-7">7</a>]</sup> (*NIS2 Directive*), adopted 14
Dec 2022, member-state transposition deadline 17 Oct 2024. Expands the
original NIS Directive (2016/1148) to cover a much larger population of
*essential* and *important* entities across 18 sectors.

**Who must comply:** essential entities in high-criticality sectors (energy,
transport, banking, financial market infrastructures, health, drinking
water, waste water, digital infrastructure, ICT service management,
public administration, space) and important entities in other critical
sectors. Small and micro enterprises are generally out of scope unless
they are sole providers in a member state.

**Key clauses and catalogue coverage:**

| Clause | Topic | Priority | Catalogue coverage |
|--------|-------|----------|---------------------|
| Art.20 | Governance | 1.0 | full — §22.2 |
| Art.21.2(a) | Risk analysis and information system security policies | 1.0 | full — §22.2 + 22.43 |
| Art.21.2(b) | Incident handling | 1.0 | full — §22.2 + 22.39 |
| Art.21.2(c) | Business continuity, backup and crisis management | 1.0 | full — §22.2 + 22.45 |
| Art.21.2(d) | Supply chain security | 1.0 | full — §22.2 + 22.44 |
| Art.21.2(e) | Security in network and information systems acquisition | 1.0 | full — §22.2 |
| Art.21.2(f) | Policies and procedures on assessing effectiveness | 1.0 | full — §22.2 + 22.43 |
| Art.21.2(g) | Basic cyber hygiene practices | 0.7 | full — §22.2 + 22.42 + 22.46 |
| Art.21.2(h) | Policies on cryptography and encryption | 1.0 | full — §22.2 + 22.41 |
| Art.21.2(i) | Human resources security, access control policies | 1.0 | full — §22.2 + 22.40 |
| Art.21.2(j) | Use of MFA and secured communications | 1.0 | full — §22.2 + 22.40 |
| Art.23 | Reporting obligations | 1.0 | full — §22.2 + 22.39 |

**What the catalogue delivers:** 100 % tier-1 coverage. §22.2 ships 59
dedicated NIS2 UCs.

**Cisco ISE evidence.** For Art.21(2)(d) supply-chain security and
network access policy, Cisco ISE attests how every authenticated
session entering the network is profiled, posture-checked, and bound
to a TrustSec policy
([UC-17.1.36](../content/cat-17-network-security-zero-trust/UC-17.1.36.json),
[UC-17.1.55](../content/cat-17-network-security-zero-trust/UC-17.1.55.json),
[UC-17.1.66](../content/cat-17-network-security-zero-trust/UC-17.1.66.json),
[UC-17.1.75](../content/cat-17-network-security-zero-trust/UC-17.1.75.json)).
For Art.21(2)(g) basic cyber hygiene, ISE platform health
([UC-17.1.28](../content/cat-17-network-security-zero-trust/UC-17.1.28.json),
[UC-17.1.32](../content/cat-17-network-security-zero-trust/UC-17.1.32.json),
[UC-17.1.40](../content/cat-17-network-security-zero-trust/UC-17.1.40.json),
[UC-17.1.77](../content/cat-17-network-security-zero-trust/UC-17.1.77.json))
keeps the access-policy-decision-point operating reliably. The cat-22
wrappers UC-22.2.58 (access control) and UC-22.2.59 (supply-chain
NAD vendor risk) package this for ENISA-aligned evidence submission.

**Where to look:** §22.2 · `api/v1/compliance/regulations/nis2.json`.

**Methodology and self-validation.** The end-to-end methodology that
governs how the catalogue maps to NIS2 (clause selection, evidence
modes, assurance levels, gap-detection) lives in
[`docs/nis2-monitoring-methodology.md`](nis2-monitoring-methodology.md).
A standalone, customer-facing self-validation worksheet that an
obligated entity can run before an external auditor visits is at
[`docs/nis2-self-validation.md`](nis2-self-validation.md). The
machine-readable provenance (which authoritative source clause-by-clause
text was sourced from, and the SHA-256 of every drift-detected page) is
in [`docs/research/nis2-source-map.md`](research/nis2-source-map.md).
For the ENISA / external-review packaging, see
[`docs/nis2-external-review-pack.md`](nis2-external-review-pack.md), and
the cross-firm benchmark of the catalogue's coverage is in
[`docs/nis2-maturity-benchmark.md`](nis2-maturity-benchmark.md).

### 4.11 DORA — Digital Operational Resilience Act (EU) · `T1`

**Regulation:** Regulation (EU) 2022/2554<sup class="ref">[<a href="#ref-10">10</a>]</sup> (*DORA*), adopted 14 Dec 2022,
application 17 Jan 2025. Establishes a uniform digital operational
resilience framework for the EU financial sector.

**Who must comply:** credit institutions, payment institutions, electronic-
money institutions, investment firms, crypto-asset service providers,
central securities depositories, central counterparties, trading venues,
trade repositories, AIFMs, UCITS management companies, data-reporting
service providers, insurance and reinsurance undertakings, intermediaries,
institutions for occupational retirement provision, credit rating agencies,
administrators of critical benchmarks, crowdfunding service providers,
securitisation repositories, and ICT third-party service providers
designated as "critical".

**Key clauses and catalogue coverage:**

| Clause | Topic | Priority | Catalogue coverage |
|--------|-------|----------|---------------------|
| Art.5 | Governance and organisation | 1.0 | full — §22.3 |
| Art.6 | ICT risk management framework | 1.0 | full — §22.3 |
| Art.8 | Identification | 1.0 | full — §22.3 + 22.43 |
| Art.9 | Protection and prevention | 1.0 | full — §22.3 + 22.41 |
| Art.10 | Detection | 1.0 | full — §22.3 + 22.35 |
| Art.11 | Response and recovery | 1.0 | full — §22.3 + 22.39 + 22.45 |
| Art.12 | Backup policies and restoration | 1.0 | full — §22.3 + 22.45 |
| Art.13 | Learning and evolving | 0.7 | full — §22.3 + 22.46 |
| Art.14 | Communication | 0.7 | full — §22.3 |
| Art.17 | ICT incident management process | 1.0 | full — §22.3 + 22.39 |
| Art.18 | Classification of ICT-related incidents | 1.0 | full — §22.3 + 22.39 |
| Art.19 | Reporting of major ICT-related incidents | 1.0 | full — §22.3 + 22.39 |
| Art.24 | Testing ICT tools and systems | 1.0 | full — §22.3 + 22.43 + 22.47 |
| Art.28-30 | ICT third-party risk management | 1.0 | full — §22.3 + 22.44 |

**What the catalogue delivers:** 100 % tier-1 coverage. §22.3 ships
94 dedicated DORA UCs with particular focus on Art.19 incident-reporting
(the single most-audited DORA clause in 2025).

**Cisco ISE evidence.** For Art.6 ICT risk management Cisco ISE supplies
the always-on identity-and-segmentation control plane (replication
health [UC-17.1.28](../content/cat-17-network-security-zero-trust/UC-17.1.28.json),
license capacity
[UC-17.1.32](../content/cat-17-network-security-zero-trust/UC-17.1.32.json),
PSN load
[UC-17.1.78](../content/cat-17-network-security-zero-trust/UC-17.1.78.json)).
For Art.9 protection and prevention, EAP-TLS strong authentication
([UC-17.1.38](../content/cat-17-network-security-zero-trust/UC-17.1.38.json),
[UC-17.1.69](../content/cat-17-network-security-zero-trust/UC-17.1.69.json),
[UC-17.1.70](../content/cat-17-network-security-zero-trust/UC-17.1.70.json))
and CoA enforcement
([UC-17.1.56](../content/cat-17-network-security-zero-trust/UC-17.1.56.json))
provide direct evidence. For Art.28-30 ICT third-party risk, pxGrid
client approval
([UC-17.1.35](../content/cat-17-network-security-zero-trust/UC-17.1.35.json))
and ANC audit
([UC-17.1.42](../content/cat-17-network-security-zero-trust/UC-17.1.42.json),
[UC-17.1.51](../content/cat-17-network-security-zero-trust/UC-17.1.51.json))
demonstrate vendor and partner control. Cat-22 wrappers UC-22.3.46
(third-party governance) and UC-22.3.47 (strong authentication for
ICT systems) package the evidence per Article.

**Where to look:** §22.3 · `api/v1/compliance/regulations/dora.json`.

### 4.12 CMMC 2.0 — Cybersecurity Maturity Model Certification (US) · `T1`

**Regulation:** Cybersecurity Maturity Model Certification version 2.0 (51
practices at Level 1 Foundational, 110 practices at Level 2 Advanced,
superset at Level 3 Expert). Codified in 32 CFR Part 170 with phased
rollout through the DoD contract base from Q3 2025 through 2028.

**Who must comply:** all Defense Industrial Base (DIB) contractors
handling Federal Contract Information (Level 1) or Controlled
Unclassified Information (Level 2+).

**Key practices and catalogue coverage:** CMMC Level 2 practices are
derived from NIST 800-171<sup class="ref">[<a href="#ref-22">22</a>]</sup> Rev.2, so the catalogue coverage shares most
of its evidence base with NIST 800-53 coverage.

| Family | Topic | Priority | Catalogue coverage |
|--------|-------|----------|---------------------|
| AC | Access Control | 1.0 | full — §22.20 + 22.40 |
| AU | Audit and Accountability | 1.0 | full — §22.20 + 22.35 |
| CM | Configuration Management | 1.0 | full — §22.20 + 22.42 |
| IA | Identification and Authentication | 1.0 | full — §22.20 |
| IR | Incident Response | 1.0 | full — §22.20 + 22.39 |
| MA | Maintenance | 0.7 | partial — §22.20 |
| MP | Media Protection | 0.7 | partial — §22.20 + 22.49 |
| PS | Personnel Security | 0.7 | partial — §22.20 + 22.40 |
| PE | Physical Protection | 0.5 | partial — §22.20 |
| RA | Risk Assessment | 1.0 | full — §22.20 + 22.43 |
| CA | Security Assessment | 1.0 | full — §22.20 + 22.47 |
| SC | System and Communications Protection | 1.0 | full — §22.20 + 22.41 |
| SI | System and Information Integrity | 1.0 | full — §22.20 + 22.43 |
| SR | Supply Chain Risk Management | 1.0 | full — §22.20 + 22.44 |
| AT | Awareness and Training | 0.7 | full — §22.20 + 22.46 |

**What the catalogue delivers:** 100 % tier-1 coverage. §22.20 ships
21 dedicated CMMC UCs.

**Cisco ISE evidence.** Because CMMC AC, AU, IA, IR, and SC families
are derivative of NIST 800-171 / 800-53, every Cisco ISE UC that
serves NIST 800-53 also serves CMMC. The cat-22 wrapper UC-22.20.21
ties together AC.L1-3.1.1 (authorised access), AU.L2-3.3.1
(auditable events), and IA.L2-3.5.3 (multi-factor authentication for
network access) into a single CCP-package evidence bundle citing
[UC-17.1.38](../content/cat-17-network-security-zero-trust/UC-17.1.38.json),
[UC-17.1.42](../content/cat-17-network-security-zero-trust/UC-17.1.42.json),
[UC-17.1.43](../content/cat-17-network-security-zero-trust/UC-17.1.43.json),
[UC-17.1.69](../content/cat-17-network-security-zero-trust/UC-17.1.69.json),
and [UC-17.1.71](../content/cat-17-network-security-zero-trust/UC-17.1.71.json).
DIB contractors should also reference the wireless-protected-Wi-Fi
trail
([UC-17.1.74](../content/cat-17-network-security-zero-trust/UC-17.1.74.json))
when WPA3-Enterprise is in scope.

**Where to look:** §22.20 · `api/v1/compliance/regulations/cmmc.json`.

---

### 4.13 NCA OTCC — Saudi OT Cybersecurity Controls (KSA) · `T2`

**Regulation:** *Operational Technology Cybersecurity Controls
(OTCC-1:2022)*, published by Saudi Arabia's
[National Cybersecurity Authority (NCA)](https://nca.gov.sa/en/regulatory-documents/controls-list/3).
OTCC sits alongside the NCA *Essential Cybersecurity Controls (ECC-1:2018)*
and *Critical Systems Cybersecurity Controls (CSCC-1:2019)* but applies
specifically to operational technology — industrial control systems,
SCADA, distributed control systems (DCS), safety instrumented systems
(SIS), HMIs, historians, RTUs, PLCs, and the industrial demilitarised
zones that connect them to enterprise IT and cloud services.

**Who must comply:**

- Saudi-domiciled organisations designated as critical national
  infrastructure (CNI) by the NCA — energy production and distribution
  (Saudi Aramco, SEC, Ma'aden, SABIC and downstream), water and
  wastewater utilities (NWC, SWPC), refining and petrochemicals,
  transport (Saudi Ports Authority, SAR, GACA-regulated ground
  systems), critical manufacturing, healthcare OT, and government OT.
- Foreign operators, EPC contractors, OEMs, and managed-service
  providers that own, operate, host, or support OT inside the
  Kingdom — OTCC reaches them through contractual flow-down, NCA
  directive, and the *Personal Data Protection Law (PDPL)* data
  residency regime.
- The ICT supply chain that supplies engineering software, firmware,
  remote-access tooling, or hosted services to in-scope OT operators —
  caught by OTCC §4 (Third-Party and Cloud Cybersecurity).

**Domain structure and catalogue coverage.** OTCC organises 47
controls across four domains; this catalogue release ships 28
monitored clauses (subcategory §22.51) and tracks the remainder under
the wider cat-22 cross-cutting families. Priority weights follow the
catalogue's *`priorityWeightRubric`* — `1.0` for safety / availability
/ regulator-reporting clauses, `0.7` for material assurance clauses,
`0.5` for procedural / training clauses.

| Domain | Topic | Monitored clauses | Priority spread | Catalogue coverage |
|--------|-------|-------------------|-----------------|---------------------|
| 1 Governance | Policy, risk, training, audits | OTCC-1-2-1-1, 1-5-1-1, 1-7-1-1, 1-9-1-1 | 1.0 / 1.0 / 0.7 / 1.0 | full — §22.51.1, §22.51.2, §22.51.25, §22.51.27 |
| 2 Defence | Asset, access, segmentation, baselines, vuln, patch, malware, removable media, wireless, segmentation, crypto, backup, logging, ICS protocol, email, IR, physical, SIS | OTCC-2-1-1-1 through 2-15-1-1 (18 clauses) | mostly 1.0; 0.7 on cryptography, wireless, email | full — §22.51.3 – §22.51.19 + §22.51.22, §22.51.24, §22.51.26 |
| 3 Resilience | BCP exercises, RTO / RPO | OTCC-3-1-1-1, 3-1-2-1 | 1.0 / 0.7 | full — §22.51.20, §22.51.21 |
| 4 Third-Party | Supply chain, cloud and hosting | OTCC-4-1-1-1, 4-2-1-1 | 1.0 / 0.7 | full — §22.51.23, §22.51.28 |

**What the catalogue delivers:** 100 % coverage of the 28 monitored
clauses. Subcategory §22.51 ships 28 dedicated NCA OTCC UCs, each
sidecar carrying an `obligationRef` of the form
`nca-otcc@current#OTCC-X-Y-Z-N`. The clause-by-clause coverage matrix
is rendered in
[`docs/evidence-packs/nca-otcc.md`](evidence-packs/nca-otcc.md) §4
and the canonical clause list is in
[`data/regulations.json`](../data/regulations.json) under
`id: nca-otcc`.

**OT-specific evidence patterns.** Because OTCC inherits the layered
defence model from IEC 62443<sup class="ref">[<a href="#ref-16">16</a>]</sup>
and the safety-aware patch-and-change discipline from IEC 61508 /
61511, every UC in §22.51 carries:

- a `controlFamily` tag rooted in the OTCC domain (`policy`,
  `asset-management`, `access-control`, `segmentation`,
  `configuration-baseline`, `vulnerability-management`,
  `patch-management`, `malware-protection`, `removable-media`,
  `wireless-control`, `cryptography`, `backup-recovery`,
  `logging`, `industrial-protocol-monitoring`, `email-borne-threats`,
  `incident-response`, `physical-access`, `sis-protection`,
  `business-continuity`, `rto-rpo`, `supply-chain`, `training`,
  `audits-and-reviews`, `cloud-hosting`);
- explicit `prerequisiteUseCases` linking back to upstream
  ingest / CIM / monitoring UCs in cat-3 (asset inventory),
  cat-9 (logging), cat-11 (incident detection), cat-17 (network
  segmentation, privileged access), cat-19 (vulnerability and patch),
  and cat-20 (industrial / OT) so the OT evidence chain is auditable
  end-to-end;
- a `dataResidency` posture aligned to PDPL — KSA-only summary
  indexes and lookups for clauses §22.51.24, §22.51.26, and §22.51.28
  that touch identity, cryptographic material, or cloud workload
  metadata;
- `notification.regulator = "NCA"` on every IR-related UC so the
  reporting clock is unambiguous from notable-event to NCA submission.

**Cisco Cyber Vision and ISA / IEC 62443 alignment.** OTCC §2.1
(asset inventory) and §2.12 (industrial-protocol monitoring) map
cleanly onto the deep-packet inspection of Cisco Cyber Vision, the
flow telemetry of Cisco ISE for IoT, and the segmentation evidence
captured by the cat-17 zero-trust UCs. Operators running a
combined Cyber Vision + ISE + Splunk topology can reuse the
[UC-17.1.38](../content/cat-17-network-security-zero-trust/UC-17.1.38.json),
[UC-17.1.69](../content/cat-17-network-security-zero-trust/UC-17.1.69.json),
and
[UC-17.1.71](../content/cat-17-network-security-zero-trust/UC-17.1.71.json)
evidence trails to satisfy OTCC §2-2-1-1 (privileged access),
§2-2-3-1 (vendor remote access), and §2-5-3-1 (segmentation) without
duplicating tooling.

**Cloud / hosting (OTCC §4.2) and CCC alignment.** OTCC §4.2 ties
into the NCA *Cloud Cybersecurity Controls (CCC-1:2020)* — every
cloud workload that supports KSA OT must hold a current CCC
attestation appropriate to its data classification, must keep KSA
data in-Kingdom (Saudi cloud regions only for confidential and
restricted data), and must surface customer-managed key custody and
incident-response coordination to NCA. UC-22.51.28 captures the
continuous-evidence posture for this clause.

**Where to look:** §22.51 ·
[`api/v1/compliance/regulations/nca-otcc.json`](../api/v1/compliance/regulations/nca-otcc.json) ·
[`docs/evidence-packs/nca-otcc.md`](evidence-packs/nca-otcc.md) ·
official source: [NCA OTCC controls list](https://nca.gov.sa/en/regulatory-documents/controls-list/3).

---

### 4.14 SOCI Act + CIRMP Rules (Australia) · `T1`

**Regulation:** *Security of Critical Infrastructure Act 2018 (Cth)*,
as amended by the *Security Legislation Amendment (Critical
Infrastructure Protection) Act 2022* (SLACIP), and the *Security of
Critical Infrastructure (Critical Infrastructure Risk Management
Program) Rules 2023* (CIRMP Rules). Together they form an all-hazards
regime for critical infrastructure, administered by the
[Cyber and Infrastructure Security Centre (CISC)](https://www.cisc.gov.au)
within the Department of Home Affairs, with cyber-incident-handling
support from the [Australian Signals Directorate (ASD)](https://www.cyber.gov.au).

**Who must comply:**

- **Responsible entities** (operators / licensees) and **direct
  interest holders** (10 % or greater holders) for assets across 11
  declared critical-infrastructure sectors: electricity, gas, liquid
  fuels, water and sewerage, telecommunications, broadcasting, postal,
  financial services and markets, transport (aviation, ports, freight
  rail, freight road), space, data storage and processing, hospitals,
  higher education and research, food and grocery, and defence
  industry. The asset-trigger thresholds are listed in the SOCI Act
  Rules under each sector.
- **Foreign-owned operators with Australian operations** — SOCI
  applies extraterritorially through the asset's connection to
  Australian territory, customers, or services. Foreign investment
  triggers a parallel review under the *Foreign Acquisitions and
  Takeovers Act 1975* with SOCI inputs.
- **Service providers to in-scope assets** — managed-service providers,
  EPC contractors, OEMs, and cloud providers are caught through the
  responsible entity's supply-chain hazard management obligations
  under CIRMP Rule 8.

**Regime structure and catalogue coverage.** SOCI is a layered regime;
this catalogue release ships 28 monitored clauses (subcategory §22.52)
covering the obligations most directly evidenced through Splunk:

| Pillar | Topic | Monitored clauses | Catalogue coverage |
|--------|-------|--------------------|---------------------|
| Asset registration | Register of Critical Infrastructure Assets currency | SOCI-s18, SOCI-Register-Currency | §22.52.1 |
| Risk management programme (CIRMP) | Cyber, personnel, supply-chain, physical hazards; annual review; cyber framework attestation | SOCI-s30AC, SOCI-CIRMP-r5, r5.2, r6, r6.2, r6.3, r7, r7.2, r8, r8.2, r9, r10 | §22.52.2 – 4, §22.52.13 – 23 |
| Critical cyber incident reporting | 12-hour and 72-hour reporting to ASD; written follow-up | SOCI-s30BC, SOCI-s30CD | §22.52.5, §22.52.6 |
| Systems of National Significance | Enhanced cybersecurity obligations: IR plans, exercises, vulnerability assessments, system-information reporting | SOCI-Pt2C-r12, r13, r14 | §22.52.7 – 12 |
| Enhanced Cybersecurity Obligation (ECSO) | 14-day Notice of Operations | SOCI-ECSO-NoOps | §22.52.26 |
| Government Assistance Powers (Part 3A) | Information-gathering, action, and intervention directions | SOCI-Pt3A | §22.52.27 |
| Protected Information (Part 6A) | Secrecy of SOCI data, lawful disclosure, on-disclosure offences | SOCI-Pt6A, SOCI-Pt6A-LawfulDisclosure | §22.52.24, §22.52.25 |
| Cross-cutting | Compliance-health rollup | SOCI-CrossCutting-Health | §22.52.28 |

**What the catalogue delivers:** 100 % coverage of the 28 monitored
clauses. Subcategory §22.52 ships 28 dedicated SOCI UCs, each sidecar
carrying an `obligationRef` of the form
`soci@2022-SLACIP+CIRMP-2023#SOCI-X-Y`. The clause-by-clause coverage
matrix is rendered in
[`docs/evidence-packs/soci.md`](evidence-packs/soci.md) §4 and the
canonical clause list is in
[`data/regulations.json`](../data/regulations.json) under
`id: soci`.

**All-hazards evidence patterns.** Because the CIRMP Rules require an
*all-hazards* programme spanning cyber, personnel, supply-chain, and
physical / natural hazards, every UC in §22.52 carries:

- a `controlFamily` tag aligned to the CIRMP pillar (`asset-register`,
  `cirmp-currency`, `incident-reporting`, `sons-ir`, `critical-worker`,
  `supply-chain`, `physical-hazard`, `cyber-physical-convergence`,
  `annual-report`, `protected-information`, `ecso`, `gap`,
  `compliance-health`);
- `prerequisiteUseCases` linking back to upstream ingest / CIM /
  monitoring UCs in cat-3 (asset inventory), cat-9 (logging),
  cat-11 (incident detection), and cat-17 (network segmentation,
  privileged access) so the asset-and-IR evidence chain is auditable
  end-to-end;
- `notification.regulator = "CISC"` (CIRMP, asset register, Rule 10
  annual report) or `"ASD"` (s30BC critical-cyber-incident, s30CD
  cyber-incident, written follow-up) so the regulator-routing is
  unambiguous from notable-event to formal submission;
- Essential Eight maturity tagging on every Rule 6(3) cyber-framework
  attestation UC so the catalogue can roll up an Essential Eight
  maturity heatmap by SoNS asset.

**Where to look:** §22.52 ·
[`api/v1/compliance/regulations/soci.json`](../api/v1/compliance/regulations/soci.json) ·
[`docs/evidence-packs/soci.md`](evidence-packs/soci.md) ·
official sources: [CISC SOCI Act page](https://www.cisc.gov.au/legislation-regulation-and-compliance/soci-act-2018)
and the [CIRMP Rules 2023](https://www.legislation.gov.au/F2023L00112/latest/text).

---

### 4.15 AWIA s2013 + EPA/CISA Water Sector Cybersecurity (US) · `T2`

**Regulation:** *Section 2013 of America's Water Infrastructure Act of
2018* (Pub.L. 115-270), which amended *Section 1433 of the Safe
Drinking Water Act* (42 U.S.C. § 300i-2), together with the EPA *Top
Actions for Securing Water Systems*, the CISA *Pathway to Cybersecurity
for the Water and Wastewater Sector*, and (in adopting states) the
EPA *July 2024 Cybersecurity Action Plan* covering sanitary-survey
cyber readiness. Administered by EPA's
[Office of Water (Office of Water Resilience)](https://www.epa.gov/waterresilience)
with cyber-incident-handling support from
[CISA](https://www.cisa.gov/water) and
[WaterISAC](https://www.waterisac.org).

**Who must comply:**

- **Community water systems (CWS)** within the meaning of the SDWA
  serving **more than 3,300 persons** in all 50 US states, DC, Puerto
  Rico, US Virgin Islands, Guam, American Samoa, and the Northern
  Mariana Islands. Three statutory population tiers determine the
  original RRA / ERP deadlines and continue to drive the 5-year
  recertification cycle.
- **Tribal CWS** served by an EPA Region.
- **Wastewater utilities** — not statutorily in scope of s1433 but
  covered by EPA's parallel water-sector resilience programme and
  increasingly expected to meet similar cyber-readiness standards
  under EPA's water-sector cybersecurity portfolio.

**Regime structure and catalogue coverage.** AWIA is a statutory-cycle
regime, with cyber depth provided by EPA Top Actions and CISA
guidance; this catalogue release ships 28 monitored clauses
(subcategory §22.53):

| Pillar | Topic | Monitored clauses | Catalogue coverage |
|--------|-------|--------------------|---------------------|
| Statutory base (RRA / ERP / certification) | RRA currency and content, ERP currency, partner coordination, certification audit | AWIA-s1433a, b, c, g | §22.53.1 – 5 |
| RRA threat coverage | Malevolent acts, natural hazards, electronic systems, monitoring practices, chemicals, financial infrastructure | AWIA-RRA-malevolent-acts, natural-hazards, electronic-systems, monitoring-practices, chemicals, financial | §22.53.6 – 11 |
| ERP procedures | Strategies and actions, detection, cyber-IR, mutual aid, review | AWIA-ERP-strategies-actions, detection, cyber-incident-response, mutual-aid, review | §22.53.12 – 16 |
| EPA / CISA cyber overlay | EPA / WaterISAC reporting, sanitary-survey readiness, EPA top-actions checklist, J100 / M19 / VSAT methodology | AWIA-EPA-cwc-reporting, sanitary-survey, aware-checklist, vsat-j100 | §22.53.17 – 20 |
| EPA / CISA top actions | MFA on remote access, IT/OT segmentation, backup, default credentials, training, vulnerability management, asset inventory | AWIA-EPA-mfa-remote-access, network-segmentation, backup-recovery, default-creds, training, vuln-mgmt, asset-inventory | §22.53.21 – 27 |
| Records retention | RRA / ERP / certification retention | AWIA-EPA-records-retention | §22.53.28 |

**What the catalogue delivers:** 100 % coverage of the 28 monitored
clauses. Subcategory §22.53 ships 28 dedicated AWIA UCs, each sidecar
carrying an `obligationRef` of the form
`awia@2018-amended-SDWA-1433#AWIA-X-Y`. The clause-by-clause coverage
matrix is rendered in
[`docs/evidence-packs/awia.md`](evidence-packs/awia.md) §4 and the
canonical clause list is in
[`data/regulations.json`](../data/regulations.json) under
`id: awia`.

**Water-sector evidence patterns.** AWIA is the only US statutory
regime that requires water-sector OT cybersecurity evidence on a
mandatory 5-year cycle; every UC in §22.53 carries:

- a `controlFamily` tag aligned to the AWIA pillar (`rra-currency`,
  `rra-coverage`, `erp-currency`, `erp-coordination`, `certification`,
  `monitoring-integrity`, `chemical-dosing`, `cyber-incident-reporting`,
  `sanitary-survey`, `top-actions`, `mfa-remote-access`,
  `network-segmentation`, `backup-recovery`, `default-creds`,
  `training`, `vuln-mgmt`, `asset-inventory`, `records-retention`);
- alignment with the
  [CISA AA23-335A advisory](https://www.cisa.gov/news-events/cybersecurity-advisories/aa23-335a)
  on Iranian-affiliated compromise of US water-sector PLCs — UC-22.53.22
  (segmentation), UC-22.53.21 (MFA), and UC-22.53.24 (default
  credentials) all explicitly evidence the controls that would have
  prevented the AA23-335A intrusions;
- `prerequisiteUseCases` linking back to ingest / CIM / OT monitoring
  UCs in cat-3 (asset inventory), cat-9 (logging), cat-11 (incident
  detection), cat-17 (network segmentation, privileged access), and
  cat-20 (industrial / OT) so the water-sector evidence chain is
  auditable;
- `notification.regulator = "EPA"` for AWIA certification, sanitary
  survey, RRA / ERP retention; `"WaterISAC"` for sector-wide cyber
  reporting; `"CISA"` for CIRCIA covered-cyber-incident reporting
  (once the final rule is in force) so the multi-regulator routing is
  unambiguous from notable-event to formal submission.

**Sanitary-survey cyber overlay.** In states that have voluntarily
adopted the EPA July 2024 Cybersecurity Action Plan, sanitary surveys
now include a cybersecurity component aligned to EPA Top Actions.
UC-22.53.18 captures the continuous-evidence posture for
sanitary-survey readiness so a CWS can satisfy the cyber-survey
question set on inspection day rather than scramble in the days
before.

**Where to look:** §22.53 ·
[`api/v1/compliance/regulations/awia.json`](../api/v1/compliance/regulations/awia.json) ·
[`docs/evidence-packs/awia.md`](evidence-packs/awia.md) ·
official sources: [EPA AWIA Section 2013](https://www.epa.gov/waterresilience/awia-section-2013)
and the [CISA Water and Wastewater Sector page](https://www.cisa.gov/water).

---

### 4.16 CIRCIA + 6 USC 681b — US CISA Cyber Incident Reporting (US) · `T1`

**Regulation:** *Cyber Incident Reporting for Critical Infrastructure
Act of 2022*, enacted as Division Y of the *Consolidated Appropriations
Act, 2022* (Pub. L. 117-103), codified at 6 U.S.C. § 681 et seq., as
operationalised by the CISA *Notice of Proposed Rulemaking* published
4 April 2024 (89 FR 23644). Administered by
[CISA](https://www.cisa.gov/topics/cyber-threats-and-advisories/information-sharing/cyber-incident-reporting-critical-infrastructure-act-2022-circia)
in coordination with the *Cyber Incident Reporting Council* and the
sector-specific reporting regimes administered by NRC, FCC, FDA, FAA,
FERC, SEC, EPA, FBI, and Secret Service.

**Who must comply:**

- **Covered entities** in 16 critical-infrastructure sectors enumerated
  in *Presidential Policy Directive 21* — Chemical, Commercial
  Facilities, Communications, Critical Manufacturing, Dams, Defense
  Industrial Base, Emergency Services, Energy, Financial Services, Food
  and Agriculture, Government Facilities, Healthcare and Public Health,
  Information Technology, Nuclear, Transportation Systems, Water and
  Wastewater Systems.
- **Non-US parent companies** with covered US subsidiaries are reached
  through the subsidiary's obligation.

**Regime structure and catalogue coverage.** CIRCIA is a federal
cyber-incident-reporting regime with two SLA clocks (72 hours for
covered cyber incidents, 24 hours for ransom payments) and a 10-year
records-preservation requirement; this catalogue release ships 28
monitored clauses (subcategory §22.54):

| Pillar | Topic | Monitored clauses | Catalogue coverage |
|--------|-------|--------------------|---------------------|
| Statutory base (s2242) | Covered-entity definition, 72-hour clock, 24-hour ransom clock, supplemental reports, RFI tracking | CIRCIA-s2242a / a(1) / b / c, CIRCIA-NPRM-covered-entity, covered-incident, 72hr-reporting, 24hr-ransom, supplemental-report | §22.54.1 – 7 |
| Report quality and authority | Report content, third-party reporter (CIRCIA Agreement), records preservation, recordkeeping quality | CIRCIA-NPRM-report-content, third-party-reporter, records-preservation, recordkeeping-quality | §22.54.8 – 11 |
| Submission and coordination | CISA Portal health, voluntary interim posture, SRMA coordination, OT/ICS detection | CIRCIA-CISA-portal-submission-health, voluntary-interim, srma-coordination, ot-ics-incident-detection | §22.54.12 – 15 |
| Board and SEC | Board fiduciary brief, Form 8-K materiality, tabletop, liability protection | CIRCIA-NPRM-board-fiduciary, sec-form-8k, annual-tabletop, liability-protection | §22.54.6, §22.54.16 – 18 |
| Records and quality | 10-year report retention, quarterly attestation, forensic imaging, annual SLA review | CIRCIA-NPRM-records-retention, quarterly-attestation, forensic-imaging, annual-sla-review | §22.54.19 – 22, §22.54.24 |
| Cross-cutting | Compliance-health rollup | CIRCIA-CrossCutting-Health | §22.54.23, §22.54.25 – 28 |

**What the catalogue delivers:** 100 % coverage of the 28 monitored
clauses. Subcategory §22.54 ships 28 dedicated CIRCIA UCs, each sidecar
carrying an `obligationRef` of the form
`circia@2022-act-with-2024-nprm#CIRCIA-X-Y`. The clause-by-clause
coverage matrix is rendered in
[`docs/evidence-packs/circia.md`](evidence-packs/circia.md) §4 and the
canonical clause list is in
[`data/regulations.json`](../data/regulations.json) under
`id: circia`.

**Multi-regulator triangulation.** CIRCIA is unique among US federal
regimes in covering all 16 critical-infrastructure sectors with a single
72-hour clock; UC-22.54.17 triangulates the CIRCIA 72-hour clock with
the SEC Form 8-K Item 1.05 4-business-day materiality clock for public
companies, and UC-22.54.3 synchronises the 24-hour ransom-payment clock
with OFAC sanctioned-entity screening and FinCEN SAR coordination.

**Liability protection and CIRCIA Agreements.** Submissions to CISA
carry liability protection under 6 U.S.C. § 681e; UC-22.54.6 instruments
the liability-protection coversheet workflow and UC-22.54.9 instruments
the CIRCIA Agreement third-party-reporter authority pathway. The
catalogue records the legal basis on every submission so the protected
status is preserved.

**Where to look:** §22.54 ·
[`api/v1/compliance/regulations/circia.json`](../api/v1/compliance/regulations/circia.json) ·
[`docs/evidence-packs/circia.md`](evidence-packs/circia.md) ·
official sources: [CIRCIA at CISA](https://www.cisa.gov/topics/cyber-threats-and-advisories/information-sharing/cyber-incident-reporting-critical-infrastructure-act-2022-circia)
and the [2024 NPRM (89 FR 23644)](https://www.federalregister.gov/documents/2024/04/04/2024-06526/cyber-incident-reporting-for-critical-infrastructure-act-circia-reporting-requirements).

---

### 4.17 CLC/TS 50701 — CENELEC Railway Cybersecurity (EU / EEA / UK / CH) · `T2`

**Regulation:** *CENELEC Technical Specification 50701:2021 — Railway
applications - Cybersecurity*, published August 2021 by CENELEC TC 9X
and forward-aligned with the in-development IEC 63452. Administered by
national rail-cyber regulators
([ANSSI](https://cyber.gouv.fr/) in France,
[BSI](https://www.bsi.bund.de/) in Germany,
[NCSC](https://www.ncsc.gov.uk/) in the UK,
[ENISA](https://www.enisa.europa.eu/topics/threat-risk-management/) at
EU level) and coordinated with the
[European Union Agency for Railways (ERA)](https://www.era.europa.eu/).
The standard inherits IEC 62443 zone-and-conduit modelling, IEC
62443-3-3 Foundational Requirements / Security Levels, and IEC 62443-4-2
Component Security Requirements.

**Who must comply:**

- **Rail operators and infrastructure managers** — passenger rail
  (heavy rail, metro, light rail, tram, high-speed) and freight rail
  across the EU/EEA, Switzerland, and the UK.
- **Rolling-stock manufacturers, signalling-equipment suppliers, and
  rail-component suppliers** delivering into EU markets must
  demonstrate compliance via IEC 62443-4-2 / ISA Secure / TÜV
  certification.
- **Carve-outs:** heritage / preservation railways, fairground rail,
  mining rail (covered by mining-sector regulations).

**Regime structure and catalogue coverage.** CLC/TS 50701 is a risk-
based rail-OT cybersecurity standard with deep coordination with the
EN 50126/8/9/50657 safety case; this catalogue release ships 28
monitored clauses (subcategory §22.55):

| Pillar | Topic | Monitored clauses | Catalogue coverage |
|--------|-------|--------------------|---------------------|
| Cybersecurity Management System (CSMS) | Charter, governance roles, asset inventory | CLC-TS-50701-c5-1, c5-2, c5-3 | §22.55.1 – 3 |
| Risk assessment | Zone-and-conduit risk, threat scenarios, risk treatment | CLC-TS-50701-c6-1, c6-2, c6-3, c6-4 | §22.55.4 – 6 |
| Security requirements | SL-T coverage, IEC 62443-3-3 SR, IEC 62443-4-2 CR | CLC-TS-50701-c7-2, c7-4, c7-3, c9-2 | §22.55.7 – 9, §22.55.26 |
| Cybersecurity assurance | Vulnerability handling, patch with safety case, maintenance, decommissioning | CLC-TS-50701-c8-1, c8-2, c8-3, c8-4 | §22.55.10, §22.55.11, §22.55.23, §22.55.24 |
| Incident detection / response | Rail-OT detection, cyber-safety coordinated IR, NIS2 / ERA / NSA reporting | CLC-TS-50701-c8-4 (cont.) | §22.55.12 – 14 |
| Supply chain / procurement | Supplier deliverables, supplier remote access, procurement cyber evaluation | CLC-TS-50701-c9-1, c9-5, c9-3, c9-4 | §22.55.15 – 17 |
| Safety coordination | EN 50126/8/9/50657 coordination, joint risk acceptance | CLC-TS-50701-c10-1, c10-2 | §22.55.18, §22.55.19 |
| Operator continuous obligations | Daily/weekly/monthly checks, training, sharing, audit cycle | CLC-TS-50701-c11-1, c11-2, c11-3, c11-4 | §22.55.20, §22.55.21, §22.55.22, §22.55.27, §22.55.28 |
| Threat intelligence | Rail-relevant threat actors and MITRE ATT&CK ICS coverage | CLC-TS-50701-c6-3 (cont.) | §22.55.25 |

**What the catalogue delivers:** 100 % coverage of the 28 monitored
clauses. Subcategory §22.55 ships 28 dedicated CLC/TS 50701 UCs, each
sidecar carrying an `obligationRef` of the form
`clc-ts-50701@2021-with-iec63452-alignment#CLC-TS-50701-X-Y`. The
clause-by-clause coverage matrix is rendered in
[`docs/evidence-packs/clc-ts-50701.md`](evidence-packs/clc-ts-50701.md)
§4 and the canonical clause list is in
[`data/regulations.json`](../data/regulations.json) under
`id: clc-ts-50701`.

**Rail-cyber + safety integration.** CLC/TS 50701 is unique in
mandating coordination between cyber controls and the EN 50126/8/9
safety case; UC-22.55.11 enforces that no patch to a safety-significant
asset is deployed without Head-of-Safety sign-off (the most-cited
rail-cyber audit finding), UC-22.55.13 enforces joint command between
the IR Commander and the Safety Lead, and UC-22.55.19 enforces joint
risk-acceptance signatures from the cyber lead, safety lead, and
operations director.

**NIS2 transport-sector enforcement.** CLC/TS 50701 is the de-facto
baseline that EU NSAs / NSBs use to evaluate transport-sector NIS2
Article 21 risk-management measures and Article 23 incident reporting;
UC-22.55.14 instruments the NIS2 24-hour early-warning and 72-hour
incident-notification clocks against the rail-cyber incident workflow,
and UC-22.55.28 instruments the annual self-assessment package that
NSAs / NSBs request on inspection.

**Where to look:** §22.55 ·
[`api/v1/compliance/regulations/clc-ts-50701.json`](../api/v1/compliance/regulations/clc-ts-50701.json) ·
[`docs/evidence-packs/clc-ts-50701.md`](evidence-packs/clc-ts-50701.md) ·
official sources: [CLC/TS 50701 at CENELEC](https://standards.cencenelec.eu/dyn/www/f?p=205:110:0::::FSP_ORG_ID,FSP_PROJECT:1258376,73987)
and the [ENISA Rail Threat Landscape](https://www.enisa.europa.eu/topics/threat-risk-management/).

---

### 4.18 IMO MSC.428(98) + MSC-FAL.1/Circ.3 + IACS UR E26/E27 — Maritime Cyber Risk Management (Global Shipping) · `T1` {#imo-msc-428-98}

**Regulation:** *IMO Resolution MSC.428(98) — Maritime Cyber Risk
Management in Safety Management Systems* (adopted 16 June 2017 by the
IMO Maritime Safety Committee), with the operational guidance set out
in *MSC-FAL.1/Circ.3 Rev.2 — Guidelines on Maritime Cyber Risk
Management* (June 2022) and the new-build equipment-level requirements
in *IACS UR E26 — Cyber Resilience of Ships* (Rev.4 2024) and
*IACS UR E27 — Cyber Resilience of On-board Systems and Equipment*
(Rev.3 2024). Reads alongside the *BIMCO Guidelines on Cyber Security
Onboard Ships* (v5, 2025), jointly published with INTERTANKO, ICS,
INTERCARGO, OCIMF and IUMI. Administered globally by the
[International Maritime Organization (IMO)](https://www.imo.org/en/OurWork/Security/Pages/Cyber-security.aspx),
operationally enforced by flag-State administrations (Panama, Liberia,
Marshall Islands, Bahamas, Malta, Singapore, etc., typically via
Recognised Organisations — the vessel's class society) under the
International Safety Management (ISM) Code on the Document of
Compliance (DoC) annual verification, by Port State Control inspectors
under the
[Paris MoU](https://www.parismou.org/),
[Tokyo MoU](https://www.tokyo-mou.org/), Caribbean, Indian Ocean,
Riyadh, Black Sea, Abuja, Viña del Mar, and Mediterranean MoUs, and by
classification societies (DNV CyberSecure, ABS CyberSafety,
LR ShipRight, BV Cyber Resilient, ClassNK Cyber) at the IACS UR E26 +
E27 cyber survey.

**Who must comply:**

- **Ship-operating companies under the ISM Code** — every company
  operating one or more SOLAS-Chapter-IX-in-scope vessels (≥ 500 GT
  on international voyages). Approximately 50,000 companies and
  99,000 ships worldwide. The cyber-SMS obligation entered practical
  force on the first annual DoC verification after 1 January 2021.
- **Ships contracted on or after 1 July 2024** under an IACS class
  society — additional IACS UR E26 (ship-level) and UR E27
  (equipment-level) cyber-resilience requirements; existing vessels
  are grandfathered but may voluntarily adopt.
- **Recognised Organisations (ROs)** — the classification societies
  (DNV, ABS, LR, BV, ClassNK, CCS, KR, RINA, IRS, RS, PRS, CRS)
  that perform statutory surveys on behalf of flag-States.
- **Carve-outs:** warships, naval auxiliaries, fishing vessels below
  the ISM threshold, and ships solely engaged in domestic voyages
  under the SOLAS Chapter I carve-outs. Most flag-States nevertheless
  apply the regime by reference.

**Regime structure and catalogue coverage.** The maritime cyber-risk
regime is a multi-instrument framework: a one-paragraph IMO
Resolution, a NIST-CSF-shaped operational guideline, and a pair of
IACS unified requirements at ship and equipment level. This catalogue
release ships 17 monitored clauses (subcategory §22.59):

| Pillar | Topic | Monitored clauses | Catalogue coverage |
|--------|-------|--------------------|---------------------|
| Resolution (administrative) | DoC cyber-SMS verification register, evidence chain | IMO-MSC-428-98-p1, p2, p3 | §22.59.1, §22.59.17 |
| Identify (MSC-FAL §2.1) | DPA + CySO roster, Cyber Risk Asset Register, §3.1 cyber-vulnerable systems enumeration | IMO-MSC-FAL-Circ-3-s2-1, s3-1 | §22.59.2, §22.59.3 |
| Protect (MSC-FAL §2.2) | IT/OT segregation, IBS baseline, USB/removable media, satcom PAM, crew/passenger Wi-Fi | IMO-MSC-FAL-Circ-3-s2-2 | §22.59.4, §22.59.7, §22.59.10, §22.59.11, §22.59.12 |
| Detect (MSC-FAL §2.3) | ECDIS / ENC chart-update integrity, AIS / GMDSS / VDES / GNSS, propulsion / DP anomaly, cargo system integrity | IMO-MSC-FAL-Circ-3-s2-3 | §22.59.5, §22.59.6, §22.59.8, §22.59.9 |
| Respond (MSC-FAL §2.4) | 24-hour multi-authority incident clock: flag State + RO + USCG NRC + port State | IMO-MSC-FAL-Circ-3-s2-4, IMO-ISM-Code-s8-2 | §22.59.13 |
| Recover (MSC-FAL §2.5) | Annual cyber-drill + tabletop after-action register | IMO-MSC-FAL-Circ-3-s2-5, IMO-ISM-Code-s8-2 | §22.59.14 |
| IACS attestation | UR E26 ship-level + UR E27 equipment-level cyber-resilience register | IACS-UR-E26-r4, IACS-UR-E27-r3 | §22.59.15, §22.59.16 |
| BIMCO bridge-systems guidance | IBS / ECDIS / GMDSS / VDR hardening | BIMCO-Cyber-bridge-systems | §22.59.5, §22.59.6, §22.59.7 |

**What the catalogue delivers:** 100 % coverage of the 17 monitored
clauses. Subcategory §22.59 ships 17 dedicated IMO UCs, each sidecar
carrying an `obligationRef` of the form
`imo-msc-428-98@2017-msc-428-98-with-2022-circ-3-rev-2-and-2024-iacs-e26-e27#<clause>`.
The clause-by-clause coverage matrix is rendered in
[`docs/evidence-packs/imo-msc-428-98.md`](evidence-packs/imo-msc-428-98.md)
§4 and the canonical clause list is in
[`data/regulations.json`](../data/regulations.json) under
`id: imo-msc-428-98`.

**Three-layer enforcement.** The maritime regime is enforced at three
independent layers: the flag State (DoC annual verification under ISM
Code §13, typically delegated to a Recognised Organisation), the port
State (PSC inspection under one of nine MoU regimes, with periodic
Concentrated Inspection Campaigns on cyber risk management — the Paris
MoU 2023 cyber CIC issued detentions), and the classification society
(IACS UR E26 / E27 surveys and the resulting class notation). A
deficiency at any one layer can detain the vessel and lock it out of
its trade route; loss of class triggers loss of insurance and
charterer rejection. UC-22.59.17 anchors the cross-layer audit-
evidence retrieval ledger so a PSC inspector, flag-State auditor, or
class-society surveyor can pull a 90-day evidence packet in five
minutes.

**Maritime-specific evidence patterns.** §22.59 carries OT-specific
controls that are unique to the maritime domain and not covered by
adjacent regulations:

- **ECDIS / ENC chart-update integrity** — UC-22.59.5 verifies digital
  signatures and authorised-publisher cryptographic chains on every
  electronic chart update applied to a bridge worldwide; fake-chart
  attacks are the highest-impact bridge-system threat (a fake
  shoaling chart can drive a VLCC aground).
- **AIS / GMDSS / VDES / GNSS integrity** — UC-22.59.6 monitors
  communication systems for jamming, spoofing and impossible-track
  anomalies; GNSS spoofing in the Black Sea, Persian Gulf and Strait
  of Hormuz is documented and routinely tracked by C4ADS, MarineLink
  and the US Maritime Administration's MSCI advisories.
- **IBS configuration-baseline drift** — UC-22.59.7 tracks Integrated
  Bridge System (Furuno, Wärtsilä SAM, NAUDEQ, Northrop Grumman
  Sperry Marine, Kongsberg) configuration against a golden baseline
  signed by the master and the IBS vendor.
- **Propulsion / Power Management System (PMS) / Dynamic Positioning
  System (DPS) anomaly** — UC-22.59.8 detects cyber-driven anomalies
  in engine and control systems by statistical deviation from
  baseline (MAN Energy Solutions, Wärtsilä, Caterpillar, Rolls-Royce
  marine engines; ABB, Siemens, Kongsberg DPS).
- **Cargo Management System (CMS) integrity** — UC-22.59.9 monitors
  tank gauging (Emerson Rosemount Tank Gauging, Honeywell Enraf),
  inert-gas, and cargo-handling systems on tankers, chemical, LNG,
  and dry-bulk vessels for integrity events.
- **Shore-to-ship satcom remote access** — UC-22.59.11 enforces PAM
  (CyberArk PSM, BeyondTrust), MFA, session recording and What-You-
  See-Is-What-You-Sign (WYSIWYS) for every shore-to-ship satcom
  remote-access session that touches OT.
- **Crew / passenger Wi-Fi segregation** — UC-22.59.12 ensures strict
  isolation between administrative, crew welfare, and passenger
  networks and CBS (Computer-Based Systems) on cruise ships, ferries
  and offshore-support vessels.

**Flag-State + Recognised Organisation routing.** Most flag-States
delegate the annual DoC verification to the vessel's class society
(the "Recognised Organisation"). For incident reporting, UC-22.59.13
parallelises submissions across the flag-State portal (e.g. Panama
SEGUMAR PRA, Liberia LISCR, Marshall Islands IRI), the RO portal
(DNV CSManager, ABS Eagle.org, LR Class Direct, BV Veristar), the
USCG National Response Center (for US-port-visiting vessels under 33
CFR 101), and the relevant PSC MoU portal — all within the 24-hour
window required by MSC-FAL.1/Circ.3 §2.4.

**Convergence with adjacent regimes.** Cat-22 §22.2 (NIS2) overlaps
for EU-flagged vessels and maritime-transport "essential entities".
Cat-22 §22.51 (NCA OTCC) overlaps for vessels operating to Saudi
ports. Cat-22 §22.54 (SOCI Act) overlaps for Australian-port-visiting
vessels under the maritime CI rules. The 24-hour clock in UC-22.59.13
is deliberately conservative against the most aggressive of these
regimes so that a single notable event produces compliant evidence
across every overlapping regulator.

**Where to look:** §22.59 ·
[`api/v1/compliance/regulations/imo-msc-428-98.json`](../api/v1/compliance/regulations/imo-msc-428-98.json) ·
[`docs/evidence-packs/imo-msc-428-98.md`](evidence-packs/imo-msc-428-98.md) ·
official sources: [IMO Maritime Cyber Risk page](https://www.imo.org/en/OurWork/Security/Pages/Cyber-security.aspx),
[IMO Resolution MSC.428(98)](https://wwwcdn.imo.org/localresources/en/OurWork/Security/Documents/Resolution%20MSC.428(98).pdf),
[IMO MSC-FAL.1/Circ.3 Rev.2 Guidelines](https://wwwcdn.imo.org/localresources/en/OurWork/Security/Documents/MSC-FAL.1-Circ.3-Rev.2.pdf),
the [IACS Unified Requirements register](https://iacs.org.uk/publications/unified-requirements/),
the [BIMCO Cyber Security Onboard Ships Guidelines](https://www.bimco.org/about-us-and-our-members/publications/the-guidelines-on-cyber-security-onboard-ships),
the [Paris MoU Cyber CIC 2023](https://www.parismou.org/inspections-risk/library-faq/cic),
and the [USCG Maritime Cyber Strategic Outlook](https://www.uscg.mil/maritimecyber/).

### 4.19 RTCA DO-326A / EUROCAE ED-202A + DO-355A + DO-356A + FAA AC 20-186 + EASA AMC 20-42 + EASA Part-IS — Airworthiness Security (Global Aviation) · `T1` {#do-326a}

**Regulation:** *RTCA DO-326A "Airworthiness Security Process
Specification"* (RTCA Inc., 6 August 2014) and the identical
*EUROCAE ED-202A* (Edition 2, June 2014) — the joint US/EU industry
standard for airworthiness security certification of civil aircraft.
DO-326A is the process spec; *DO-356A / ED-203A "Airworthiness
Security Methods and Considerations"* (2018) provides the methods
(threat scenarios, risk assessment, security architecture);
*DO-355A / ED-204A "Information Security Guidance for Continuing
Airworthiness"* (2020) extends the obligation to in-service
operation; *DO-391 / ED-205 "Aeronautical Information System Security
(AISS) Framework Guidance"* covers ground systems supporting
connected aircraft. Accepted by the
[FAA via Advisory Circular 20-186](https://www.faa.gov/regulations_policies/advisory_circulars/index.cfm/go/document.information/documentid/1039753)
and by the
[EASA via Acceptable Means of Compliance AMC 20-42](https://www.easa.europa.eu/en/document-library/acceptable-means-of-compliance-and-guidance-materials).
Parallel ISMS obligation under
[EASA Part-IS](https://www.easa.europa.eu/en/the-agency/faqs/information-security)
([Commission Implementing Regulation (EU) 2022/1645](https://eur-lex.europa.eu/eli/reg_impl/2022/1645/oj)
and [Commission Delegated Regulation (EU) 2023/203](https://eur-lex.europa.eu/eli/reg_del/2023/203/oj)),
binding for every approved EU/EEA aviation organisation from
**22 February 2026**. Aircraft network architecture anchored on
*ARINC 811 — Commercial Aircraft Information Security Concepts of
Operation and Process Framework* (four trust domains: ACD / AISD /
PIESD / POD).

**Who must comply:**

- **Type-certificate (TC) and supplemental type-certificate (STC)
  applicants** where Information Security is identified as an issue
  by the FAA Aircraft Certification Service or the EASA project
  certification manager (PCM) — covers Airbus, Boeing, Embraer,
  Bombardier, Dassault Aviation, Gulfstream, Textron Aviation,
  Pilatus, Honda Aircraft, Diamond Aircraft, Mitsubishi SpaceJet
  (suspended), COMAC, UAC, and every Part-21 design organisation.
- **Continuing Airworthiness Management Organisations (CAMOs)** under
  EASA Part-CAMO and Part-145 maintenance organisations — DO-355A
  applies to every in-service aircraft.
- **Every approved EU/EEA aviation organisation under EASA Part-IS**
  (Part-21 design / production, Part-145 maintenance, Part-CAMO,
  Part-CAO, Part-AeMC, Part-ATCO, Part-FCL, Part-MED, Part-ORO /
  Part-CAT, Part-NCC, Part-NCO, Part-SPO, Part-ANS, Part-ATM/ANS,
  ADR.OR) — binding from 22 February 2026.
- **Cross-recognition:** FAA, EASA, Transport Canada Civil Aviation
  (TCCA), Brazilian ANAC, Japan JCAB, Civil Aviation Authority of
  Singapore (CAAS), UK CAA, Australian CASA, and other Tier-1
  authorities accept DO-326A under bilateral aviation-safety
  agreements (BASAs).
- **Carve-outs:** military / state aviation (governed by the relevant
  national defence-aviation rules), experimental and amateur-built
  aircraft below the relevant Information Security threshold.

**Regime structure and catalogue coverage.** The DO-326A regime is
multi-document: a process spec, a methods companion, a continuing-
airworthiness extension, a ground-system extension, two regulator
acceptance documents, an ISMS implementing regulation, and an
underlying network-architecture concept. This catalogue release
ships 17 monitored clauses (subcategory §22.60):

| Pillar | Topic | Monitored clauses | Catalogue coverage |
|--------|-------|--------------------|---------------------|
| PSecAA | Plan for Security Aspects of Certification milestone tracker | DO-326A-s2-2, FAA-AC-20-186-s5, EASA-AMC-20-42-s4 | §22.60.1 |
| CSI + SRA | Cyber Security Item inventory + Security Risk Assessment per airframe type | DO-326A-s2-1, DO-326A-s3-1 | §22.60.2 |
| ARINC 811 segregation | ACD / AISD / PIESD / POD trust-domain segregation drift detection | DO-326A-s6-3, ARINC-811-s4-2 | §22.60.3, §22.60.12 |
| LSAP integrity | Loadable Software Aircraft Part digital-signature audit at load time | DO-355A-s2-3 | §22.60.4 |
| AD / SB compliance | Cyber-AD and security-SB compliance tracker per tail | DO-355A-s2-1 | §22.60.5 |
| PMAT governance | Portable Maintenance Access Terminal / maintenance-laptop governance | DO-355A-s3-4 | §22.60.6 |
| EFB posture | Electronic Flight Bag Class 2/3 security posture monitoring | DO-356A-s5-2 | §22.60.7 |
| Datalink integrity | ACARS / CPDLC / VDL Mode 2 message integrity + injection detection | DO-356A-s3-1 | §22.60.8 |
| GNSS / GPS spoofing | GNSS spoofing and jamming detection from RAIM + position-anomaly | DO-356A-s3-1 | §22.60.9 |
| ADS-B injection | ADS-B / Mode S Squitter integrity + ghost-target detection | DO-356A-s3-1 | §22.60.10 |
| Engine OEM remote access | Engine OEM remote-monitoring channel governance via PAM + WYSIWYS | EASA-Part-IS-IS-OR-220 | §22.60.11 |
| Incident reporting | EASA Part-IS 72-hour preliminary + 1-month final reporting clock | EASA-Part-IS-IS-OR-230 | §22.60.13 |
| ISMS audit | EASA Part-IS ISMS audit-evidence register and scope coverage | EASA-Part-IS-IS-OR-200 | §22.60.14 |
| SBOM CVE monitoring | Airborne software cyber-SBOM vulnerability monitoring | DO-355A-s2-1, EASA-Part-IS-IS-OR-205 | §22.60.15 |
| Training cadence | Pilot + maintenance cyber-incident training cadence + drill register | EASA-Part-IS-IS-OR-240 | §22.60.16 |
| Aeronautical DB integrity | NAV / FMS / TERRAIN / EGPWS database digital-signature audit | DO-355A-s3-1, DO-326A-s3-3 | §22.60.17 |

**What the catalogue delivers:** 100 % coverage of the 19 monitored
clauses. Subcategory §22.60 ships 17 dedicated DO-326A UCs, each
sidecar carrying an `obligationRef` of the form
`do-326a@2014-do-326a-with-2020-do-355a-and-2026-easa-part-is#<clause>`.
The clause-by-clause coverage matrix is rendered in
[`docs/evidence-packs/do-326a.md`](evidence-packs/do-326a.md) §4
and the canonical clause list is in
[`data/regulations.json`](../data/regulations.json) under
`id: do-326a`.

**Four-layer enforcement.** The airworthiness-security regime is
enforced at four independent layers: type-certification (FAA ACO /
EASA PCM finding-of-non-compliance can delay a TC by 3-12 months,
costing the applicant hundreds of millions of dollars per
programme), continuing-airworthiness (FAA Aircraft Maintenance
Division / EASA Continuing Airworthiness Department / NCA can issue
cyber-ADs that ground affected fleets), EASA Part-IS / NIS2 (NCA
inspection with up to EUR 10 million / 2 % of worldwide turnover
under NIS2 overlap), and Air Operator Certificate (suspension or
revocation of the AOC prevents flight operations). The Accountable
Manager personally signs the operator-certificate attestation; in
some EU/EEA Member States this can rise to administrative or
criminal liability for a Part-IS / NIS2 failure leading to a
safety-impacting incident.

**Aviation-specific evidence patterns.** §22.60 carries aviation-
specific controls that are unique to the airworthiness-security
domain and not covered by adjacent regulations:

- **PSecAA milestone tracker** — UC-22.60.1 reconciles every active
  TC/STC project against its PSecAA acceptance and downstream
  milestones (CSI register baseline, SRA completion, security
  architecture freeze, security verification, CASI delivery).
- **ARINC 811 trust-domain segregation** — UC-22.60.3 continuously
  monitors information flows between the Aircraft Control Domain
  (ACD), Airline Information Services Domain (AISD), Passenger
  Information & Entertainment Services Domain (PIESD), and Passenger
  Owned Devices (POD); any cross-domain flow not in the documented
  security-architecture allowlist triggers a critical event.
- **LSAP digital-signature audit** — UC-22.60.4 verifies every
  Loadable Software Aircraft Part (LSAP) load against the TC-holder
  authorised-signer allowlist; a load with an engineering certificate
  (or any non-production signer) is blocked.
- **PMAT governance** — UC-22.60.6 enforces device posture and USB
  policy on Portable Maintenance Access Terminals (laptops used by
  line- and base-maintenance to talk to the aircraft via the data
  loader); the PMAT is the highest-risk insider-threat ingress path.
- **EFB posture monitoring** — UC-22.60.7 monitors Class 2 EFB
  tablets (Surface Pro / iPad) for MDM check-in cadence, app-
  inventory drift, OS-version posture; out-of-policy EFBs are
  blocked from cockpit use.
- **ACARS / CPDLC / VDL Mode 2 integrity** — UC-22.60.8 detects
  injection of false ATC clearances, unauthorised CPDLC messages,
  and VDL Mode 2 anomalies against flight-plan and crew-acknowledged
  baseline; cross-references with the FANS-1/A and FANS-2/A
  expected-routing tables.
- **GNSS spoofing / jamming detection** — UC-22.60.9 monitors RAIM
  warnings, GPS satellite-vehicle-count anomalies, and impossible-
  track events; documented GNSS spoofing in the Black Sea, Persian
  Gulf, Eastern Mediterranean, and over conflict zones is routinely
  surfaced (OPSGROUP, Sentinel, EUROCONTROL bulletins).
- **ADS-B injection detection** — UC-22.60.10 cross-checks ADS-B
  Squitter messages against MLAT and radar tracks to detect ghost-
  target injection on the cockpit display.
- **Aeronautical database integrity** — UC-22.60.17 verifies signer-
  pinning and signature validity on every NAV / FMS / TERRAIN /
  EGPWS / PERFORMANCE / SYNTHETIC-VISION database load at the LRU
  upload point; an unsigned or wrong-signer database triggers a
  NO-DESPATCH workflow.

**EASA Part-IS 72-hour + 1-month clock.** UC-22.60.13 parallelises
submissions to the National Competent Authority under
[Commission Delegated Regulation (EU) 2023/203](https://eur-lex.europa.eu/eli/reg_del/2023/203/oj)
Art.6 (72-hour preliminary report) and Art.7 (1-month final
report), plus the FAA (where US-registered) and any other Tier-1
authority with a parallel obligation, all within the EASA Part-IS
window required by IS.OR.230.

**Convergence with adjacent regimes.** Cat-22 §22.56.4 (TSA Surface
SD-1582 aviation) overlaps for US-registered cyber-relevant
operators. Cat-22 §22.2 (NIS2) overlaps for EU-flagged operators
under the "air transport" essential-entity category. Cat-22 §22.50
(NCA OTCC) overlaps for operators with Saudi-registered aircraft.
Cat-22 §22.54 (SOCI Act) overlaps for Australian-registered
operators under the aviation CI rules. The 72-hour clock in
UC-22.60.13 is deliberately conservative against the most aggressive
of these regimes so that a single notable event produces compliant
evidence across every overlapping regulator.

**Where to look:** §22.60 ·
[`api/v1/compliance/regulations/do-326a.json`](../api/v1/compliance/regulations/do-326a.json) ·
[`docs/evidence-packs/do-326a.md`](evidence-packs/do-326a.md) ·
official sources: [RTCA standards list](https://www.rtca.org/standards/list-of-available-documents/),
[EUROCAE standards list](https://www.eurocae.net/about-us/list-of-publications/),
[FAA AC 20-186](https://www.faa.gov/regulations_policies/advisory_circulars/index.cfm/go/document.information/documentid/1039753),
[EASA Acceptable Means of Compliance library](https://www.easa.europa.eu/en/document-library/acceptable-means-of-compliance-and-guidance-materials),
[EASA Part-IS Information Security FAQ](https://www.easa.europa.eu/en/the-agency/faqs/information-security),
[Commission Implementing Regulation (EU) 2022/1645](https://eur-lex.europa.eu/eli/reg_impl/2022/1645/oj),
[Commission Delegated Regulation (EU) 2023/203](https://eur-lex.europa.eu/eli/reg_del/2023/203/oj),
the [ICAO Cybersecurity in Civil Aviation page](https://www.icao.int/Security/Pages/Cybersecurity.aspx),
[ARINC 811 specification](https://aviation-ia.sae-itc.com/standards/arinc811-0-arinc-specification-811-0-commercial-aircraft-information-security-concepts-operation-and-process),
the [A-ISAC](https://www.a-isac.com/) and
the [European Centre for Cybersecurity in Aviation (ECCSA)](https://www.eccsa.eu/).

### 4.20 China CSL / DSL / PIPL / CII Regulations / MLPS 2.0 — Cybersecurity, Data, Privacy, and CII Regime (PRC) · `T1` {#cn-csl}

**Regulation:** China's layered cybersecurity-and-data legal regime,
anchored on the *Cybersecurity Law of the People's Republic of China*
(CSL — adopted 7 November 2016, effective 1 June 2017), tightened
progressively by the *Data Security Law* (DSL — effective 1 September
2021) and the *Personal Information Protection Law* (PIPL — effective
1 November 2021), operationalised on critical infrastructure by the
*Regulations on Security Protection of Critical Information
Infrastructure* (State Council Order No. 745 — effective 1 September
2021), screened for procurement risk by the *Cybersecurity Review
Measures* (CRM — 2022 revision, effective 15 February 2022), and on
data export by the
[CAC Measures for Security Assessment of Outbound Data Transfers](https://www.cac.gov.cn/2022-07/07/c_1658811536396503.htm)
(effective 1 September 2022) and the
*Standard Contract for the Outbound Cross-Border Transfer of Personal
Information* (effective 1 June 2023). Technical implementation of CSL
Art.21 is the
[Multi-Level Protection Scheme 2.0 (MLPS 2.0 — GB/T 22239-2019)](https://openstd.samr.gov.cn/bzgk/gb/index)
with five grades; Level 3 and above require an annual independent
assessment by a Ministry of Public Security (MPS)-accredited testing
organisation. Administered by the
[Cyberspace Administration of China (CAC)](https://www.cac.gov.cn/),
the [Ministry of Public Security (MPS)](https://www.mps.gov.cn/),
the [Ministry of Industry and Information Technology (MIIT)](https://www.miit.gov.cn/),
the [State Administration for Market Regulation (SAMR)](https://www.samr.gov.cn/),
and sectoral CIIO-protection departments (PBOC for finance, NEA for
energy, NRTA for radio/TV, MoT for transport, etc.).

**Who must comply:**

- **Every network operator in the PRC** — defined extremely broadly as
  the owner, manager, or service provider of a network in China.
  Effectively every commercial enterprise with PRC operations.
- **Critical Information Infrastructure Operators (CIIOs)** designated
  by sectoral protection departments per CIIO Regulations Article 8 —
  finance, energy, telecom, water, transport, e-government, health,
  education, scientific research, and other sectors at the regulator's
  discretion. Designation triggers data-localization (CSL Art.37),
  annual self-assessment (CSL Art.38), CRM procurement filing (CSL
  Art.35), and personnel-security screening obligations.
- **Personal Information Handlers (PIHs)** under PIPL Art.3(2)
  extraterritorial reach — any organisation outside the PRC that
  processes personal information of individuals in the PRC for the
  purpose of providing products / services, analysing / evaluating
  behaviour, or other circumstances specified by law. PIPL Art.53
  requires non-PRC handlers to establish a designated representative
  in the PRC and file the representative's contact details with the
  CAC.
- **Significant Personal Information Handlers** — processors handling
  personal information of >1 million data subjects, or specific
  high-risk processing categories, are subject to the most onerous
  PIPL obligations (DPO appointment, periodic compliance audit, ADM
  transparency under PIPL Art.24).
- **Important Data Handlers** under DSL Art.21 — every operator
  designated by sectoral catalogues as handling Important Data
  (重要数据) — subject to risk assessment, incident reporting, and
  cross-border-transfer security-assessment obligations.
- **Carve-outs:** the law has been applied in practice with sectoral
  variations (e.g. health-sector data has additional rules under NHC
  Measures; finance-sector data under PBOC notices). Military, state-
  security, and party / government systems are governed by separate
  regimes (BMB / 16-Office) and are out of scope of this catalogue.

**Regime structure and catalogue coverage.** The PRC cybersecurity-
and-data regime is the most complex statutory stack in any major
jurisdiction — four primary statutes (CSL / DSL / PIPL / CIIO
Regulations), a procurement-review measure (CRM), three cross-border
mechanisms (CAC assessment / standard contract / certification), one
technical implementation standard (MLPS 2.0), and dozens of CAC and
sectoral implementing notices. This catalogue release ships 14
monitored clauses (subcategory §22.61):

| Pillar | Topic | Monitored clauses | Catalogue coverage |
|--------|-------|--------------------|---------------------|
| CSL — MLPS implementation | MLPS 2.0 grading register, L2+ filing, and L3+ independent-assessment cycle (CSL Art.21 vehicle) | CSL-Art-21, MLPS-2-0-L3, MLPS-2-0-annual | §22.61.1 |
| CSL — CIIO designation + annual self-assessment | CIIO designation register + Art.38 annual cybersecurity inspection and risk assessment | CSL-Art-38, CIIO-Reg-Art-8 | §22.61.2 |
| CSL — incident reporting | Cybersecurity incident emergency-response plan + tiered reporting (Levels 1-4) | CSL-Art-25, DSL-Art-29 | §22.61.3 |
| CSL — CIIO data localization | CIIO Art.37 outbound personal-information and important-data egress detector | CSL-Art-37, PIPL-Art-38, DSL-Art-21 | §22.61.4 |
| DSL — Important Data catalogue | DSL Art.21 classification register + sectoral Important Data List alignment | DSL-Art-21 | §22.61.5 |
| DSL / PIPL — blocking statute | DSL Art.36 + PIPL Art.41 foreign judicial / law-enforcement demand workflow | DSL-Art-36, PIPL-Art-38 | §22.61.6 |
| PIPL — cross-border transfers | PIPL Art.38 three-mechanism register (CAC assessment / standard contract / certification) | PIPL-Art-38 | §22.61.7 |
| PIPL — DPO + PIPIA | PIPL Art.51/52/55/56 — internal management, DPO appointment, PIPIA freshness | PIPL-Art-51, PIPL-Art-55 | §22.61.8 |
| PIPL — ADM transparency | PIPL Art.24 automated decision-making transparency + opt-out audit | PIPL-Art-55 | §22.61.9 |
| CIIO — Cybersecurity Review Measures | CIIO Reg Art.14 + CRM 2022 pre-procurement Cybersecurity Review filing tracker | CIIO-Reg-Art-14 | §22.61.10 |
| MLPS 2.0 Level 3+ | Annual independent assessment scheduling, MPS-accredited assessor freshness, finding-remediation closure | MLPS-2-0-annual, MLPS-2-0-L3 | §22.61.11 |
| CSL / DSL — universal log retention | ≥6-month security-log retention with integrity protection and tamper detection | CSL-Art-21, MLPS-2-0-L3, DSL-Art-29 | §22.61.12 |

**What the catalogue delivers:** 100 % coverage of the 14 monitored
clauses. Subcategory §22.61 ships 12 dedicated UCs (some clauses are
covered by more than one UC), each sidecar carrying an
`obligationRef` of the form
`cn-csl@2017-csl-with-2021-dsl-pipl-and-2022-ciio-cross-border#<clause>`.
The clause-by-clause coverage matrix is rendered in
[`docs/evidence-packs/cn-csl.md`](evidence-packs/cn-csl.md) §4 and the
canonical clause list is in
[`data/regulations.json`](../data/regulations.json) under
`id: cn-csl`.

**Four-layer enforcement.** The PRC cybersecurity-and-data regime is
enforced at four independent layers: the **CAC** (top-level coordination
on cybersecurity policy, cross-border data transfer, important-data
designation, PIPIA enforcement, ADM transparency); the **MPS** (MLPS
filing and grading, MLPS L3+ annual assessment, public-security
investigations under CSL Art.27); **sectoral protection departments**
(CIIO designation, CIIO annual self-assessment under CSL Art.38, CRM
procurement-review filing); and the **SAMR** (administrative fines on
illegal data processing). Cross-cutting enforcement powers include
warnings, fines (RMB 1,000,000 on the entity + RMB 50,000-500,000 on
responsible individuals under DSL Art.45-46), suspension of business,
revocation of licences, and possible criminal liability under PRC
Criminal Law Articles 286 / 287 / 287-1 / 287-2 / 253-1.

**PRC-specific evidence patterns.** §22.61 carries PRC-specific
controls that are unique to the Chinese statutory regime and not
covered by adjacent regulations:

- **MLPS 2.0 grading register and L3+ annual independent assessment
  (CSL Art.21 implementation)** — UC-22.61.1 anchors the catalogue
  view of every in-scope system's MLPS grade (Level 1-5), Level-2+
  MPS filing status, and Level-3+ assessment cycle, while UC-22.61.11
  tracks the assessor's MPS accreditation freshness and finding-
  remediation closure. Lapsed L3+ annual assessment is the most-cited
  MPS PINSS inspection finding and is a precondition for PRC business
  continuity.
- **6-month network log retention with tamper evidence (CSL Art.21
  via DSL Art.29 + MLPS-2-0-L3)** — UC-22.61.12 maintains a source-
  aware integrity-protected archive of every regulated log source
  with monthly anchor publication; an MPS inspector pulling 180 days
  of evidence receives an integrity-attestation receipt as part of
  the evidence chain.
- **CIIO designation + Art.38 annual self-assessment** — UC-22.61.2
  maintains the CIIO designation register against the sectoral
  protection departments' designation notices and the annual self-
  assessment report submission archive, including third-party
  assessor identity and finding-remediation traceability.
- **CSL Art.37 outbound data-egress detector for CIIOs** — UC-22.61.4
  detects any outbound flow of personal information or important data
  from a CIIO that is not backed by an active CAC Cross-Border
  Security Assessment approval (alongside PIPL-Art-38 cross-border
  mechanism and DSL-Art-21 important-data classification).
- **Cross-border data transfer (PIPL Art.38)** — UC-22.61.7 tracks
  every approved transfer mechanism (CAC security assessment, CAC
  standard contract, or PIPL Art.38(2) certification) with bi-annual
  review and volume reconciliation against actual outbound personal-
  information flow; the most onerous data-export approval pipeline
  in any major jurisdiction, where a missed renewal halts every
  outbound flow.
- **DSL Art.36 / PIPL Art.41 blocking statute** — UC-22.61.6 captures
  every foreign judicial or law-enforcement data demand, opens the
  competent-PRC-authority approval workflow before any response is
  provided, and archives the Ministry of Justice / CAC approval
  documentation. Without this workflow, a multinational facing a US
  subpoena cannot lawfully comply with the foreign court without
  violating PRC law (the classic blocking-statute conflict).
- **CSL Art.25 tiered incident clock + DSL Art.29 8-hour Significant /
  24-hour Ordinary clock** — UC-22.61.3 starts the CAC + MPS +
  sectoral-regulator submission queue the instant a confirmed
  cybersecurity / data-security event is classified, with the
  bilingual incident-summary template (Chinese + English) auto-
  generated for parallel submissions. The most-cited CSL / DSL
  enforcement finding.
- **CIIO Cybersecurity Review (CIIO Reg Art.14 + CRM 2022)** —
  UC-22.61.10 captures every CIIO procurement of network products
  and services that affects or may affect national security, opens
  the Article 14 / CRM filing workflow, and archives the Office of
  Cybersecurity Review approval determination prior to contract
  execution.
- **PIPL Art.24 ADM transparency** — UC-22.61.9 enforces the PIPL
  Article 24 requirement that automated decision-making affecting
  individuals must be transparent, fair, and impartial — Significant
  Handlers must offer an opt-out mechanism for personalised
  recommendations and must justify automated decisions on request.
  This is the closest analogue to GDPR Article 22 in the PRC regime
  and is increasingly enforced by the CAC (notably the 2024 CAC
  ADM-on-platforms compliance audit).
- **PIPL Art.51/52/55/56 internal management + DPO + PIPIA** —
  UC-22.61.8 maintains the Significant Personal Information Handler
  programme: DPO appointment register, periodic compliance audits,
  and Personal Information Impact Assessment freshness for high-risk
  processing categories.
- **DSL Art.21 Important Data Catalogue** — UC-22.61.5 tracks the
  freshness of the operator's Important Data Catalogue against
  sectoral Important Data Lists (industrial data, financial data,
  health data, etc.) and the operator's classification coverage.

**Convergence with adjacent regimes.** Cat-22 §22.1 (GDPR) overlaps
on personal-data principles for multinationals subject to both PIPL
(extraterritorial) and GDPR (EU operations). Cat-22 §22.51 (NCA OTCC)
overlaps for Saudi operations of PRC multinationals. Cat-22 §22.54
(SOCI Act) overlaps for Australian operations. The DSL Art.29 8-hour
Significant clock and the DSL Art.36 / PIPL Art.41 blocking statute
are PRC-specific and have no direct equivalent in any other major
jurisdiction.

**Where to look:** §22.61 ·
[`api/v1/compliance/regulations/cn-csl.json`](../api/v1/compliance/regulations/cn-csl.json) ·
[`docs/evidence-packs/cn-csl.md`](evidence-packs/cn-csl.md) ·
official sources: the [Cyberspace Administration of China (CAC)](https://www.cac.gov.cn/),
the [Ministry of Public Security (MPS)](https://www.mps.gov.cn/),
the [National People's Congress legislation portal](http://www.npc.gov.cn/),
the [CAC Measures for Security Assessment of Outbound Data Transfers](https://www.cac.gov.cn/2022-07/07/c_1658811536396503.htm),
the [Cybersecurity Review Measures (2022)](https://www.cac.gov.cn/2022-01/04/c_1642894602182845.htm),
the [Standard Contract for the Outbound Cross-Border Transfer of Personal Information (2023)](https://www.cac.gov.cn/2023-02/24/c_1678884830036414.htm),
the [MLPS 2.0 standard family GB/T 22239-2019 (TC260)](https://openstd.samr.gov.cn/bzgk/gb/index),
and the [TC260 national cybersecurity standardization technical committee](https://www.tc260.org.cn/).

### 4.21 CERT-In Directions 2022 + DPDP Act 2023 — Cybersecurity Incident Reporting + Data Protection (India) · `T1` {#cert-in}

**Regulation:**
[*CERT-In Directions of 28 April 2022* (No. 20(3)/2022-CERT-In)](https://www.cert-in.org.in/Directions70B.jsp)
issued by the Indian Computer Emergency Response Team under
[Section 70B(6) of the Information Technology Act 2000](https://www.indiacode.nic.in/handle/123456789/1999),
binding from 27 June 2022. Operates alongside the
[*Digital Personal Data Protection Act 2023*](https://www.meity.gov.in/content/digital-personal-data-protection-act-2023)
(DPDP — passed 11 August 2023, in phased commencement during 2024-2026)
and the
[Data Protection Board of India](https://www.meity.gov.in/data-protection-framework),
together with the legacy
[*Information Technology (Reasonable Security Practices and
Procedures and Sensitive Personal Data or Information) Rules 2011*](https://www.meity.gov.in/writereaddata/files/GSR313E_10511(1).pdf)
(SPDI Rules) under IT Act Section 43A. Administered by
[CERT-In](https://www.cert-in.org.in/)
(Ministry of Electronics and Information Technology, MeitY) for
cybersecurity-incident reporting, by the Data Protection Board for
personal-data breach notification, and by sectoral regulators (RBI,
SEBI, IRDAI, TRAI) for additional sector-specific obligations.

**Who must comply:**

- **Every body corporate, intermediary, data centre, VPS provider,
  cloud-service provider, and government organisation** operating in
  or providing services to users in India — regardless of nationality
  of the operating entity. The Directions apply by reference to all 20
  enumerated incident categories.
- **Virtual Private Server (VPS) providers, virtual private network
  (VPN) service providers, and cloud-service providers** — additional
  KYC retention obligations under Direction 5(1) covering seven
  subscriber data elements for at least 5 years post-cancellation.
- **Virtual Asset Service Providers (VASPs) / crypto-exchanges** —
  additional 5-year transaction-record retention under Direction 6 of
  KYC and financial-transaction records.
- **Data Fiduciaries under DPDP Act 2023** — every entity that, alone
  or jointly with others, determines the purpose and means of
  personal-data processing. Subject to consent, lawful-purpose, and
  breach-notification obligations.
- **Significant Data Fiduciaries (SDFs)** designated by the Central
  Government under DPDP Section 10 — additional obligations including
  Indian-resident DPO, periodic Data Protection Impact Assessment
  (DPIA), annual independent audit, and algorithmic-transparency
  review.
- **Carve-outs:** SPDI Rules pre-empted by DPDP for in-scope personal
  data once DPDP is fully commenced; specific carve-outs in DPDP
  Sections 17 (research, archival, statistical, state-purpose
  processing) and the Right-to-Information Act 2005 overlap.

**Regime structure and catalogue coverage.** The Indian regime is a
two-track stack: CERT-In Directions on the cybersecurity-incident /
infrastructure side (operational, technical, with the shortest
incident-reporting clock in any major jurisdiction at 6 hours), and
DPDP on the personal-data side (rights-based, with a 72-hour breach
clock to the Data Protection Board). This catalogue release ships 11
monitored clauses (subcategory §22.62):

| Pillar | Topic | Monitored clauses | Catalogue coverage |
|--------|-------|--------------------|---------------------|
| CERT-In Dir.2 + IT Act Sec.70B | 6-hour cybersecurity incident reporting (20 enumerated categories) | CERT-In-Dir-2, IT-Act-Sec-70B | §22.62.1 |
| CERT-In Dir.3 | NTP synchronisation to NIC / NPL Indian time servers | CERT-In-Dir-3 | §22.62.2 |
| CERT-In Dir.4 | Designated 24×7 Point-of-Contact (POC) + 7-day change notification | CERT-In-Dir-4 | §22.62.3 |
| CERT-In Dir.5 | 180-day rolling ICT log retention within Indian jurisdiction | CERT-In-Dir-5 | §22.62.4 |
| CERT-In Dir.5(1) | VPN / VPS / cloud-provider subscriber KYC + 5-year retention | CERT-In-Dir-5-1 | §22.62.5 |
| CERT-In Dir.6 + IT Act Sec.43A | VASP / crypto-exchange customer KYC + 5-year transaction-record retention | CERT-In-Dir-6, IT-Act-Sec-43A | §22.62.6 |
| DPDP Sec.10 (SDF) + IT Act Sec.43A | Indian-resident DPO + DPIA + annual independent audit (SDF programme) | DPDP-Sec-8, IT-Act-Sec-43A | §22.62.7 |
| DPDP Sec.8(6) + IT Act Sec.43A | 72-hour breach notification to Data Protection Board of India + parallel Data Principal notification | DPDP-Sec-8, IT-Act-Sec-43A | §22.62.8 |

**What the catalogue delivers:** 100 % coverage of the 11 monitored
clauses. Subcategory §22.62 ships 8 dedicated UCs (several clauses are
covered by composite UCs), each sidecar carrying an
`obligationRef` of the form
`cert-in@2022-04-28-cert-in-directions-with-2023-dpdp#<clause>`.
The clause-by-clause coverage matrix is rendered in
[`docs/evidence-packs/cert-in.md`](evidence-packs/cert-in.md) §4 and
the canonical clause list is in
[`data/regulations.json`](../data/regulations.json) under
`id: cert-in`.

**Three-layer enforcement.** The Indian regime is enforced at three
layers: **CERT-In** (statutory authority under IT Act Section 70B —
non-compliance with Directions is punishable under Section 70B(7) with
imprisonment up to 1 year or fine up to INR 1,00,000 or both); the
**Data Protection Board of India** (DPB — established under DPDP
Section 18; imposes penalties up to INR 250 crore for breach of
DPDP obligations under DPDP Schedule); and **sectoral regulators**
(RBI for banks, SEBI for capital-market intermediaries, IRDAI for
insurers, TRAI for telecom, MeitY for intermediaries — each can
impose additional sector-specific cybersecurity directions).
Non-compliance with CERT-In Directions is widely reported as a
recurring inspection finding in RBI and SEBI audits; the IT Ministry
maintains a public list of enforcement notices.

**India-specific evidence patterns.** §22.62 carries Indian-specific
controls that are unique to the regime and not covered by adjacent
regulations:

- **6-hour incident-reporting clock (CERT-In Direction 2)** — UC-22.62.1
  is the shortest such clock in any major jurisdiction. The CERT-In
  Portal submission is automated via SOAR the instant a confirmed
  event matches any of 20 enumerated incident categories (targeted
  scanning / probing, compromise of critical systems / information,
  unauthorised access of IT systems / data, defacement of website or
  intrusion into a website and unauthorised changes such as inserting
  malicious code, links to external websites, etc., malicious code
  attacks such as the spreading of virus / worm / Trojan / botnet /
  spyware / ransomware / cryptominers, attack on servers such as
  database, mail and DNS, and network devices such as routers,
  identity theft, spoofing and phishing attacks, denial-of-service
  (DoS) and distributed denial-of-service (DDoS) attacks, attacks on
  critical infrastructure, SCADA and operational technology systems
  and wireless networks, attacks on applications such as e-governance,
  e-commerce, fake mobile apps, unauthorised access to social media
  accounts, attacks or malicious / suspicious activities affecting
  cloud computing systems / servers / software / applications, attacks
  or malicious / suspicious activities affecting systems / servers /
  networks / software / applications related to Big Data, Block chain,
  virtual assets, virtual asset exchanges, custodian wallets, robotics,
  3D and 4D Printing, additive manufacturing, drones, attacks or
  malicious / suspicious activities affecting systems / servers /
  software / applications related to Artificial Intelligence and
  Machine Learning, data breach, data leak, attacks on Internet of
  Things devices and associated systems / networks / software / servers,
  attacks or incidents affecting digital payment systems, attacks
  through malicious mobile apps, fake mobile apps, unauthorised access
  to systems / servers / software / databases / applications and the
  receipt and archive the CERT-In acknowledgement.
- **NTP synchronisation (Direction 3)** — UC-22.62.2 enforces every
  ICT system to synchronise its system clocks with the Network Time
  Protocol (NTP) Server of the National Informatics Centre (NIC —
  `samay1.nic.in` / `samay2.nic.in`) or National Physical Laboratory
  (NPL — `time.npl.res.in`) or with NTP servers traceable to these
  NTP servers, for synchronisation of all their ICT systems clocks.
  Any drift beyond ± 100 ms triggers a remediation workflow.
- **POC register (Direction 4)** — UC-22.62.3 maintains the designated
  CERT-In Point-of-Contact register with 24×7 contactability tests,
  a 7-day change-notification workflow, and the CERT-In Form-A
  submission archive. Stale POC details are the most-cited CERT-In
  inspection finding.
- **180-day log retention within Indian jurisdiction (Direction 5)**
  — UC-22.62.4 proves rolling 180-day ICT log retention for every
  regulated source within the territorial jurisdiction of India.
  A sourcetype that drops below 180 days or that is persisted to a
  non-Indian region of public cloud is the most-common CERT-In
  Direction (iv) finding; this UC anchors the territorial-residency
  audit-evidence chain.
- **VASP customer KYC + 5-year transaction records (Direction 6)**
  — UC-22.62.6 maintains the VASP customer KYC register and the
  5-year retention of all transaction records (chain of crypto-asset,
  fiat-currency leg, customer wallet identifier, beneficiary wallet
  identifier, amount, timestamp, and IP address) — the strictest
  VASP record-retention regime in any major jurisdiction.
- **DPDP 72-hour breach clock + parallel Data Principal notification
  (Section 8(6))** — UC-22.62.8 starts both clocks the instant a
  confirmed personal-data breach is classified, with the Data
  Protection Board of India submission and the parallel Data
  Principal notification queued automatically; the dual-track clock
  design ensures neither obligation is missed.

**Convergence with adjacent regimes.** Cat-22 §22.16 (CIRCIA US)
overlaps for US-headquartered multinationals with Indian operations.
Cat-22 §22.10 (NIS2 EU) overlaps for EU-headquartered multinationals.
Cat-22 §22.1 (GDPR) overlaps where Indian residents' data flows to
EU recipients. The CERT-In 6-hour clock is the shortest such clock
in any major jurisdiction; UC-22.62.1 is therefore the master
incident-reporting trigger for any global enterprise with Indian
operations — every other jurisdiction's clock starts later than the
CERT-In clock for the same event.

**Where to look:** §22.62 ·
[`api/v1/compliance/regulations/cert-in.json`](../api/v1/compliance/regulations/cert-in.json) ·
[`docs/evidence-packs/cert-in.md`](evidence-packs/cert-in.md) ·
official sources: [CERT-In Directions of 28 April 2022](https://www.cert-in.org.in/Directions70B.jsp),
the [CERT-In statutory home page](https://www.cert-in.org.in/),
the [Digital Personal Data Protection Act 2023 (MeitY)](https://www.meity.gov.in/content/digital-personal-data-protection-act-2023),
the [Ministry of Electronics and Information Technology (MeitY)](https://www.meity.gov.in/),
the [IT Act 2000 (India Code)](https://www.indiacode.nic.in/handle/123456789/1999),
the [SPDI Rules 2011](https://www.meity.gov.in/writereaddata/files/GSR313E_10511(1).pdf),
the [NIC Network Time Protocol service (samay.nic.in)](https://samay.nic.in/),
and the [National Physical Laboratory time service](https://www.nplindia.org/time-and-frequency/).

### 4.22 IEC 61508 / 61511 + ISA-TR84.00.09 + IEC 62443-3-2 / 62443-3-3 — Functional Safety with Cybersecurity Overlay (Global Process Industries) · `T1` {#iec-61511}

**Regulation:** the universally-recognised Good Engineering Practice
(RAGAGEP) stack for Safety Instrumented Systems in the process
industries:
[*IEC 61511 Edition 2 (2016) — Functional safety: Safety Instrumented
Systems for the process industry sector*](https://webstore.iec.ch/publication/24241)
(applies to process industries), with the parent
[*IEC 61508 (2010)*](https://webstore.iec.ch/publication/5515)
(generic functional-safety framework for E/E/PE safety-related systems),
the cybersecurity overlay
[*ISA-TR84.00.09 (2017) — Cybersecurity Related to the Functional
Safety Lifecycle*](https://www.isa.org/standards-and-publications/isa-standards/isa-standards-committees/isa84),
and the cybersecurity risk-assessment frameworks
[*IEC 62443-3-2:2020 — Security risk assessment for system design*](https://webstore.iec.ch/publication/30727)
and
*IEC 62443-3-3:2013 — System security requirements and security levels*.
Incorporated by reference into
[OSHA Process Safety Management (PSM) 29 CFR 1910.119](https://www.osha.gov/laws-regs/regulations/standardnumber/1910/1910.119),
[EPA Risk Management Program (RMP) 40 CFR Part 68](https://www.ecfr.gov/current/title-40/chapter-I/subchapter-C/part-68),
[HSE COMAH 2015](https://www.hse.gov.uk/comah/),
[Seveso III Directive 2012/18/EU](https://eur-lex.europa.eu/eli/dir/2012/18/oj),
[MSIHC Rules 1989 (India)](https://www.indiacode.nic.in/),
[KOSHA PSM (Korea)](https://www.kosha.or.kr/),
and most major process-safety legal regimes worldwide. The IEC 61511
Edition 2 (2016) introduced Clause 8.2.4 mandating a SIS Cybersecurity
Risk Assessment via ISA-TR84.00.09 — the bridge between functional
safety and OT cybersecurity.

**Who must comply:**

- **Every operator of a Safety Instrumented System (SIS) in the
  process industries** — oil & gas (upstream / midstream / downstream),
  refining, petrochemicals, specialty chemicals, pharmaceuticals,
  power generation (where SIS protects against process-safety hazards),
  water and wastewater (where SIS protects against chemical-release
  hazards), mining (where SIS protects against process-safety
  hazards), pulp and paper, food processing, and any other industry
  with an SIS-protected process. Approximately every Tier-1 chemical
  / refining / pharmaceutical / LNG / FPSO facility worldwide.
- **Functional Safety Managers (FSMs)** with documented competence
  certified under TÜV FSE / FSEng, exida CFSE / CFSP, or equivalent
  national functional-safety competence schemes.
- **Process Safety Managers and Plant Managers** who carry the
  process-safety accountability under OSHA PSM / EPA RMP / COMAH /
  Seveso / MSIHC etc.
- **OT Security Leads and SIS Cybersecurity Managers** with documented
  competence under IEC 62443 personnel-competence levels — the role
  introduced by ISA-TR84.00.09 to bridge functional safety and OT
  cybersecurity.
- **SIS Vendors and System Integrators** — required to deliver
  systematic-capability evidence (IEC 61508 Part 2 / Part 3), to
  certify their products against TÜV / exida third-party assessment,
  and to maintain SIL-rated devices in their catalogue.
- **Carve-outs:** machinery safety (IEC 62061 / ISO 13849), nuclear
  power (IEC 61513), railway (CENELEC EN 50126/29/657), aviation
  (DO-178C / DO-254), automotive (ISO 26262), and medical-device
  (IEC 62304 / IEC 60601) are governed by sector-specific functional-
  safety derivatives of IEC 61508. SIS in those sectors is
  out of scope of this catalogue's §22.63 (covered elsewhere).

**Regime structure and catalogue coverage.** The IEC 61511 regime is
a multi-document family: a 16-phase safety lifecycle (61511 Part 1),
methods and examples (61511 Part 2), guidance on the determination of
SIL (61511 Part 3 + LOPA), the cybersecurity bridge (ISA-TR84.00.09),
and the cybersecurity risk-assessment framework (IEC 62443-3-2 + 3-3).
This catalogue release ships 9 monitored clauses (subcategory §22.63):

| Pillar | Topic | Monitored clauses | Catalogue coverage |
|--------|-------|--------------------|---------------------|
| IEC 61511 Cl.5 + IEC 61508 Cl.7.4 | 16-phase SIS safety lifecycle register + Functional Safety Assessment | IEC-61511-Cl-5, IEC-61508-Pt-1-Cl-7-4 | §22.63.1 |
| IEC 61511 Cl.8.2.4 + ISA-TR84.00.09 §4 + IEC 62443-3-2 | SIS Cybersecurity Risk Assessment (CRA) freshness + methodology | IEC-61511-Cl-8-2-4, ISA-TR84-00-09-s4, IEC-62443-3-2 | §22.63.2 |
| IEC 61511 Cl.11 + Cl.11.7.6 | SIS-BPCS separation + override / bypass / inhibit / force operational restrictions and logging | IEC-61511-Cl-11, IEC-61511-Cl-11-7-6 | §22.63.3 |
| IEC 61511 Cl.16.3 + IEC 61508 Cl.7.4 | SIS proof-test interval + demand-rate + spurious-trip-rate trending | IEC-61511-Cl-16-3, IEC-61508-Pt-1-Cl-7-4 | §22.63.4 |
| IEC 61511 Cl.17.2 + Cl.8.2.4 | SIS Management of Change (MoC) + SIL impact + CRA refresh + PSSR closure | IEC-61511-Cl-17-2, IEC-61511-Cl-8-2-4 | §22.63.5 |
| ISA-TR84.00.09 §4 + §5 | Integrated cybersecurity programme feedback loop into CRA + PHA | ISA-TR84-00-09-s4, ISA-TR84-00-09-s5 | §22.63.6 |
| IEC 62443-3-2 + IEC 61511 Cl.8.2.4 | SIS zone-and-conduit SL-T / SL-C / SL-A evidence + exception register | IEC-62443-3-2, IEC-61511-Cl-8-2-4 | §22.63.7 |

**What the catalogue delivers:** 100 % coverage of the 9 monitored
clauses. Subcategory §22.63 ships 7 dedicated UCs (several clauses
are covered by composite UCs covering the lifecycle, the cybersecurity
bridge, and the zone-and-conduit evidence chain), each sidecar
carrying an `obligationRef` of the form
`iec-61511@2016-iec-61511-ed-2-with-isa-tr84-00-09#<clause>`.
The clause-by-clause coverage matrix is rendered in
[`docs/evidence-packs/iec-61511.md`](evidence-packs/iec-61511.md) §4
and the canonical clause list is in
[`data/regulations.json`](../data/regulations.json) under
`id: iec-61511`.

**Three-layer assurance.** Unlike most cat-22 regulations, IEC 61511
is enforced at three independent layers and is rarely a direct
regulator-issued fine. The first layer is the **process-safety
regulator** (OSHA / EPA / HSE / Seveso CA / DGFASLI / KOSHA /
PEMEX / ANP / NMA / DEMA / SEPA): a process-safety incident with a
SIS-attributed root cause triggers regulatory action under the
parent PSM / RMP / COMAH / Seveso / MSIHC regime, with civil
penalties typically in the USD 5M-150M range for the worst incidents
and criminal liability for responsible managers in some jurisdictions
(UK Corporate Manslaughter Act, US Federal Worker Endangerment).
The second layer is the **certifying body** (TÜV Süd / TÜV Rheinland /
exida / DEKRA / Bureau Veritas / Lloyd's Register / DNV / SIRIM): a
functional-safety-management failure can result in suspension or
revocation of the SIL certification on a vendor product, and of the
Functional Safety Management (FSM) certificate on an operator's
process. The third layer is the **insurer** (Allianz / Munich Re /
Zurich / AIG / Marsh — every Tier-1 chemical and refining operator
carries IEC 61511 functional-safety attestation as a precondition of
HPL or BIPD insurance, and a documented IEC 61511 gap triggers
material-information disclosure and premium loading).

**Process-safety-specific evidence patterns.** §22.63 carries OT- and
process-safety-specific controls that are unique to the IEC 61511
regime and not covered by adjacent regulations:

- **16-phase safety lifecycle register (Clause 5)** — UC-22.63.1
  tracks every SIS through Hazard and Risk Assessment, Allocation of
  Safety Functions to Protection Layers, SIS Safety Requirements
  Specification, SIS Design and Engineering, SIS Installation and
  Commissioning, SIS Operation and Maintenance, SIS Modification,
  and SIS Decommissioning — with deliverable / verification /
  Functional Safety Assessment completion records. This is the master
  evidence chain demanded by every PSM / COMAH / Seveso / MSIHC
  auditor and every certifying body.
- **SIS Cybersecurity Risk Assessment (Clause 8.2.4)** — UC-22.63.2
  tracks every SIS CRA for freshness and methodology alignment with
  ISA-TR84.00.09 + IEC 62443-3-2. A CRA over 5 years old, or a CRA
  that does not partition the System Under Consideration (SUC) into
  zones and conduits per IEC 62443-3-2, is the most-cited finding in
  a TÜV / exida re-certification audit.
- **SIS-BPCS separation + override / bypass / inhibit / force discipline
  (Clauses 11 + 11.7.6 + 14)** — UC-22.63.3 verifies physical and
  logical separation between the SIS and the Basic Process Control
  System (BPCS), and authorises / time-bounds / annunciates every
  SIF override, bypass, inhibit, or force. An undisclosed permanent
  bypass on an SIF is one of the most consistent root-cause findings
  in major process-safety incidents (Buncefield 2005, Williams
  Olefins 2013, West Fertilizer 2013).
- **Proof-test discipline (Clause 16.3)** — UC-22.63.4 monitors every
  SIF's proof-test execution against the design interval with
  PFD-vs-demand-rate-vs-spurious-trip-rate trending. A proof-test
  interval that has been extended without a documented PFD re-analysis
  is the most common reason an SIF's actual PFD drifts above its
  target SIL.
- **Management of Change (Clause 17.2)** — UC-22.63.5 enforces the
  MoC discipline (classification + SIL-impact + CRA refresh + PSSR +
  lifecycle-deliverable update). Misclassification of an SIS-affecting
  change as "replacement-in-kind" is the most consistent root-cause
  finding across major process-safety incidents; every change must
  clear SIL-impact + CRA refresh + Pre-Startup Safety Review before
  restart.
- **ISA-TR84.00.09 §4 integrated cybersecurity programme (UC-22.63.6)**
  — operates the SLA between SIS-zone cyber events and the safety
  lifecycle: every SIS-zone cyber event acknowledged within 5
  minutes, linked to a CRA finding within 8 hours, and a PHA-refresh
  decision recorded within 24 hours. This is the operational glue
  between OT cybersecurity detection and the safety-lifecycle.
- **IEC 62443-3-2 zone-and-conduit SL-T / SL-C / SL-A evidence chain
  (UC-22.63.7)** — maintains the SL-T target vs SL-C component
  capability vs SL-A achieved measurement across all seven IEC
  62443-3-3 Foundational Requirements (FR1 identification +
  authentication, FR2 use control, FR3 system integrity, FR4 data
  confidentiality, FR5 restricted data flow, FR6 timely response,
  FR7 resource availability). Any FR with SL-A < SL-T without a
  documented and approved exception is a TÜV / exida finding.

**Convergence with adjacent regimes.** Cat-22 §22.15 (AWIA water
sector) overlaps for water-sector SIS in the US. Cat-22 §22.51
(NCA OTCC) overlaps for Saudi Aramco / SABIC / chemical SIS. Cat-22
§22.54 (SOCI Act) overlaps for Australian energy / chemical SIS.
ISA / IEC 62443 (in cat-22 §22.32) provides the broader OT
cybersecurity framework that ISA-TR84.00.09 binds into the SIS
safety lifecycle. The 5-minute / 8-hour / 24-hour ISA-TR84.00.09 §4
SLA in UC-22.63.6 is deliberately conservative against the most
aggressive process-safety regulator clock so that a single SIS-zone
cyber event produces compliant evidence for the SIS Cybersecurity
Risk Assessment refresh and for the PHA refresh decision.

**Where to look:** §22.63 ·
[`api/v1/compliance/regulations/iec-61511.json`](../api/v1/compliance/regulations/iec-61511.json) ·
[`docs/evidence-packs/iec-61511.md`](evidence-packs/iec-61511.md) ·
official sources: [IEC 61511 Edition 2 (2016)](https://webstore.iec.ch/publication/24241),
[IEC 61508 (2010)](https://webstore.iec.ch/publication/5515),
the [ISA84 standards committee (ISA-TR84.00.09)](https://www.isa.org/standards-and-publications/isa-standards/isa-standards-committees/isa84),
[IEC 62443-3-2:2020](https://webstore.iec.ch/publication/30727),
the [OSHA PSM standard 29 CFR 1910.119](https://www.osha.gov/laws-regs/regulations/standardnumber/1910/1910.119),
the [EPA RMP regulation 40 CFR Part 68](https://www.ecfr.gov/current/title-40/chapter-I/subchapter-C/part-68),
the [HSE COMAH guidance](https://www.hse.gov.uk/comah/),
the [Seveso III Directive 2012/18/EU](https://eur-lex.europa.eu/eli/dir/2012/18/oj),
the [CSB process-safety incident library](https://www.csb.gov/),
and the
[TÜV functional-safety certification scheme overview](https://www.tuv.com/world/en/functional-safety.html).

---

## 5. Derivative regulations (propagated via `derivesFrom`)

Derivative regulations re-use the substance of a parent framework. The
catalogue propagates compliance entries from parents to derivatives
mechanically, with full traceability via the
`derivationSource` object on every inherited entry.

### 5.1 UK GDPR ← GDPR (identity mode)

**Inheritance mode:** `identity` — clause numbers preserved 1:1. Parent
`Art.N` → derivative `Art.N` for every clause not listed in `divergences`.

**Divergences:**
- `Art.45` (adequacy decisions): UK-managed by the ICO / UK government.
- `Art.50` (international cooperation): UK has its own mechanisms.

### 5.2 CCPA / CPRA ← GDPR (mapped mode)

**Inheritance mode:** `mapped` — parent clauses propagate only if listed
in `clauseMapping`.

**Clause mappings:**
- GDPR `Art.15` → CCPA `§1798.100` (right to know)
- GDPR `Art.17` → CCPA `§1798.105` (right to delete)
- GDPR `Art.34` → CCPA `§1798.150` (private right of action on data breach)

### 5.3 Swiss nFADP ← GDPR (mapped mode)

**Inheritance mode:** `mapped`.

**Clause mappings:**
- GDPR `Art.25` → nFADP `Art.7` (privacy by design and by default)
- GDPR `Art.33` → nFADP `Art.24` (breach notification to FDPIC)

### 5.4 LGPD ← GDPR (mapped mode)

**Inheritance mode:** `mapped`.

**Clause mappings:**
- GDPR `Art.32` → LGPD `Art.46` (security measures)
- GDPR `Art.33` → LGPD `Art.48` (communication to ANPD)
- GDPR `Art.34` → LGPD `Art.48` (communication to data subjects — same article as to ANPD)

### 5.5 APPI ← GDPR (mapped mode)

**Inheritance mode:** `mapped`.

**Clause mappings:**
- GDPR `Art.32` → APPI `Art.23` (security control of personal data)
- GDPR `Art.33` → APPI `Art.26` (mandatory leakage reporting)
- GDPR `Art.34` → APPI `Art.26` (same article covers both supervisory and subject notification)

**Where to look for all derivative coverage:** every UC that tags GDPR
now also carries derivative entries tagged with `provenance:
"derived-from-parent"` and a full `derivationSource` object. The API
surface at `api/v1/compliance/regulations/{uk-gdpr,ccpa,swiss-nfadp,lgpd,appi}.json`
is the machine-readable view.

---

## Appendix A — Per-regulation subcategories at a glance

| Subcategory | Regulation | Jurisdiction | Tier | UCs | API endpoint |
|-------------|------------|--------------|------|-----|--------------|
| 22.1 | GDPR | EU/EEA | T1 | 50 | `regulations/gdpr.json` |
| 22.2 | NIS2 | EU | T1 | 59 | `regulations/nis2.json` |
| 22.3 | DORA | EU | T1 | 94 | `regulations/dora.json` |
| 22.4 | CCPA / CPRA | US-CA | T2 | inherit | `regulations/ccpa.json` |
| 22.5 | MiFID II | EU | T2 | see §22.5 | `regulations/mifid-ii.json` |
| 22.6 | ISO 27001 | GLOBAL | T1 | 116 | `regulations/iso-27001.json` |
| 22.7 | NIST CSF | US/GLOBAL | T1 | 50 | `regulations/nist-csf.json` |
| 22.8 | SOC 2 | US/GLOBAL | T1 | 80 | `regulations/soc-2.json` |
| 22.9 | Compliance trending | cross-framework | n/a | dashboards | `compliance/coverage.json` |
| 22.10 | HIPAA Security | US | T1 | 58 | `regulations/hipaa-security.json` |
| 22.11 | PCI DSS v4.0 | GLOBAL | T1 | 220 | `regulations/pci-dss.json` |
| 22.12 | SOX / ITGC | US | T1 | 86 | `regulations/sox-itgc.json` |
| 22.13 | NERC CIP<sup class="ref">[<a href="#ref-24">24</a>]</sup> | US/CA | T2 | see §22.13 | `regulations/nerc-cip.json` |
| 22.14 | NIST 800-53 Rev.5 | US | T1 | 81 | `regulations/nist-800-53.json` |
| 22.15 | IEC 62443<sup class="ref">[<a href="#ref-16">16</a>]</sup> | GLOBAL | T2 | see §22.15 | `regulations/iec-62443.json` |
| 22.16 | TSA Pipeline Security | US | T2 | see §22.16 | `regulations/tsa-sd.json` |
| 22.17 | FDA 21 CFR Part 11 | US | T2 | see §22.17 | `regulations/fda-part-11.json` |
| 22.18 | API 1164 SCADA Security | US | T2 | see §22.18 | `regulations/api-rp-1164.json` |
| 22.19 | FISMA / FedRAMP | US | T2 | see §22.19 | `regulations/fedramp.json` + `regulations/fisma.json` |
| 22.20 | CMMC 2.0 | US | T1 | 21 | `regulations/cmmc.json` |
| 22.21 | EU AI Act<sup class="ref">[<a href="#ref-13">13</a>]</sup> | EU | T2 | see §22.21 | `regulations/eu-ai-act.json` |
| 22.22 | PSD2<sup class="ref">[<a href="#ref-6">6</a>]</sup> / Payment Services | EU | T2 | see §22.22 | `regulations/psd2.json` |
| 22.23 | EU Cyber Resilience Act<sup class="ref">[<a href="#ref-14">14</a>]</sup> (CRA) | EU | T2 | see §22.23 | `regulations/eu-cra.json` |
| 22.24 | eIDAS<sup class="ref">[<a href="#ref-11">11</a>]</sup> 2.0 | EU | T2 | see §22.24 | `regulations/eidas.json` |
| 22.25 | EU AML / CFT | EU | T2 | see §22.25 | `regulations/eu-aml.json` |
| 22.26 | Norwegian Regulatory Framework | NO | T2 | see §22.26 | `regulations/no-{sikkerhetsloven,kbf-nve,personopplysningsloven,petroleumsforskriften}.json` |
| 22.27 | UK Regulations (NIS + FCA/PRA) | UK | T2 | see §22.27 | `regulations/uk-nis.json`, `fca-ss1-21.json`, `pra-ss2-21.json`, `fca-smcr.json`, `uk-cyber-essentials.json` |
| 22.28 | German KRITIS / BSI | DE | T2 | see §22.28 | `regulations/bsi-kritisv.json`, `it-grundschutz.json`, `it-sig-2.json`, `bait-kait.json` |
| 22.29 | APAC Data Protection | various | T2 | see §22.29 | `regulations/{appi,lgpd,pipl,sg-pdpa,au-privacy-act,sa-pdpl}.json` |
| 22.30 | APAC Financial Regulation | various | T2 | see §22.30 | `regulations/{mas-trm,hkma-tm-g-2,rbi-cyber,apra-cps-234,sama-csf}.json` |
| 22.31 | Australia & New Zealand | AU, NZ | T2 | see §22.31 | `regulations/{asd-e8,apra-cps-234,nzism,au-privacy-act}.json` |
| 22.32 | Americas Regulations | various | T2 | see §22.32 | `regulations/{lgpd,ccpa}.json` |
| 22.33 | Middle East Cybersecurity | various | T2 | see §22.33 | `regulations/{nesa-uae-ias,qcb-cyber,sa-pdpl,sama-csf}.json` |
| 22.34 | SWIFT CSP | GLOBAL | T2 | see §22.34 | `regulations/swift-csp.json` |
| 22.51 | NCA OTCC (Saudi OT) | KSA | T2 | 28 | `regulations/nca-otcc.json` |
| 22.52 | SOCI Act + CIRMP Rules | Australia | T1 | 28 | `regulations/soci.json` |
| 22.53 | AWIA s2013 + EPA/CISA Water | US | T2 | 28 | `regulations/awia.json` |

For the full 82-framework inventory (tier-1, tier-2, and meta), consult
`data/regulations.json` or `api/v1/compliance/index.json`.

---

## Appendix B — Data-protection / privacy regulations worldwide

Because data-protection regulations are the most commonly requested
multi-jurisdiction coverage question, this appendix lists them in
derivative-aware form. **P** indicates parent; **D** indicates derivative
(with inheritance mode noted).

| Reg | Jurisdiction | Effective | Parent / relation | Supervisory authority |
|-----|--------------|-----------|-------------------|------------------------|
| GDPR | EU/EEA | 25 May 2018 | **P** (the paradigmatic data-protection parent) | Member-state DPAs (EDPB cooperation) |
| UK GDPR | UK | 31 Dec 2020 | **D** identity from GDPR | ICO |
| CCPA / CPRA | US-CA | 1 Jan 2020 / 1 Jan 2023 | **D** mapped from GDPR | CPPA |
| LGPD | BR | 18 Sep 2020 | **D** mapped from GDPR | ANPD |
| APPI | JP | 1 Apr 2022 (2020 amendment) | **D** mapped from GDPR | PPC |
| Swiss nFADP | CH | 1 Sep 2023 | **D** mapped from GDPR | FDPIC |
| SG PDPA | SG | 2 Jul 2014 (2021 amendment) | independent (cross-references GDPR) | PDPC |
| AU Privacy Act | AU | 21 Dec 1988 (continuous amendment) | independent | OAIC |
| PIPL<sup class="ref">[<a href="#ref-32">32</a>]</sup> | CN | 1 Nov 2021 | independent | CAC |
| SA PDPL | SA | 14 Sep 2023 | independent | SDAIA |
| HIPAA Privacy | US | 14 Apr 2003 | independent (sectoral — healthcare) | HHS OCR |

All of these are covered in `data/regulations.json`; derivative propagation
is applied automatically by the [build pipeline](build-artefacts-reference.md).

---

## Appendix C — Glossary

**AEAD** — Authenticated Encryption with Associated Data. A cipher mode
(AES-GCM, ChaCha20-Poly1305) that provides both confidentiality and
integrity in a single primitive.

**Assurance level** — the strength of the claim that a UC satisfies a
clause. Catalogue values: `full`, `partial`, `contributing`.

**Clause grammar** — the regex that validates clause citations for a
specific regulation version. Defined in `data/regulations.json`.

**Common clauses** — the hand-curated list in `data/regulations.json`
of clauses the catalogue targets for coverage measurement. Smaller than
the full clause set; chosen for real-world audit relevance.

**Derivative regulation** — a regulation whose substance is materially
inherited from a parent regulation. The [build pipeline](build-artefacts-reference.md) propagates
parent-clause coverage to derivatives via the `derivesFrom` graph.

**DSR** — Data Subject Request (GDPR terminology; synonymous with
*consumer request* under CCPA, *holder request* under LGPD, etc.).

**Family** — a cross-cutting control question (cat-22 subcategories
22.35 – 22.49). Distinct from *family root* (a regulation's top-level
`derivesFrom` ancestor used in coverage per-family tables).

**OSCAL** — Open Security Controls Assessment Language. A NIST-maintained
standard for machine-readable security controls and assessment results.

**Priority weight** — a per-clause weight used in priority-weighted
coverage calculation. Defined in `data/regulations.json` →
`priorityWeightRubric`.

**Provenance** — where a `compliance[]` entry came from: `maintainer`
(hand-authored), `auditor-reviewed`, `olir-crosswalk` (NIST OLIR-sourced),
`nist-cprt-ingest` (NIST CPRT-sourced), or `derived-from-parent`
(propagated via `derivesFrom`).

**Tier** — authoring priority for a regulation. Tier 1 = 100 % common-clauses
coverage goal. Tier 2 = meaningful partial coverage. Tier 3 = meta /
reference only.

---

## Appendix D — Provenance and authoritative sources

Every clause citation in this document is validated against
`data/regulations.json`, which in turn carries authoritative URLs for every
regulation and version. The `data/provenance/ingest-manifest.json` file
records the SHA-256 of every ingested regulator document. No SME opinions
in this primer are un-sourced.

For high-stakes interpretations — particularly around breach-notification
timing, cross-border transfer validity, and DPIA requirements — consult
your own counsel and the relevant regulator's guidance directly before
relying on the catalogue's coverage claims as legal conclusions.

See also:

- `LEGAL.md` — copyright and licensing for ingested authoritative sources.
- `docs/coverage-methodology.md` — precise definitions of clause %,
  priority-weighted %, and assurance-adjusted % coverage.
- `docs/compliance-gaps.md` — the current machine-generated gap report.
- `docs/api-versioning.md` — semver governance for `api/v1/*`.

---

<!-- BEGIN-AUTOGENERATED-SOURCES -->

## References

*Auto-generated by `scripts/generate_doc_references.py` from `data/source-references.json` and `data/source-mappings.json`. Edit those files (or the document body) to change citations; this footer is rewritten on every run.*

### Supporting sources

<a id="ref-1"></a>**[1]** American Institute of Certified Public Accountants. (2017). *Trust Services Criteria (2017) for Security, Availability, Processing Integrity, Confidentiality, and Privacy*. AICPA & CIMA. SOC 2 / TSP Section 100. https://www.aicpa-cima.com/topic/audit-assurance/soc-suite-of-services

<a id="ref-2"></a>**[2]** Australian Cyber Security Centre. (2023). *Essential Eight Maturity Model*. Australian Signals Directorate. https://www.cyber.gov.au/resources-business-and-government/essential-cybersecurity/essential-eight

<a id="ref-3"></a>**[3]** California Office of the Attorney General. (2020). *California Consumer Privacy Act / California Privacy Rights Act*. State of California. CA Civ Code § 1798.100 et seq. https://oag.ca.gov/privacy/ccpa

<a id="ref-4"></a>**[4]** Cisco Systems, Inc. (2026). *Cisco Identity Services Engine (ISE) Documentation*. Retrieved May 11, 2026, from https://www.cisco.com/c/en/us/support/security/identity-services-engine/series.html

<a id="ref-5"></a>**[5]** Cybersecurity and Infrastructure Security Agency. (2026). *CISA Known Exploited Vulnerabilities Catalog*. U.S. Department of Homeland Security. Retrieved May 11, 2026, from https://www.cisa.gov/known-exploited-vulnerabilities-catalog

<a id="ref-6"></a>**[6]** European Parliament and Council of the European Union. (2015, November). *Directive (EU) 2015/2366 — Payment Services Directive 2 (PSD2)*. Official Journal of the European Union, L 337. ELI: dir/2015/2366. https://eur-lex.europa.eu/eli/dir/2015/2366/oj

<a id="ref-7"></a>**[7]** European Parliament and Council of the European Union. (2022, December). *Directive (EU) 2022/2555 — NIS2 Directive on cybersecurity*. Official Journal of the European Union, L 333. ELI: dir/2022/2555. https://eur-lex.europa.eu/eli/dir/2022/2555/oj

<a id="ref-8"></a>**[8]** European Parliament and Council of the European Union. (2014). *Directive 2014/65/EU — Markets in Financial Instruments Directive (MiFID II)*. Official Journal of the European Union, L 173. ELI: dir/2014/65. https://eur-lex.europa.eu/eli/dir/2014/65/oj

<a id="ref-9"></a>**[9]** European Parliament and Council of the European Union. (2016, April). *Regulation (EU) 2016/679 — General Data Protection Regulation*. Official Journal of the European Union, L 119. ELI: reg/2016/679. https://eur-lex.europa.eu/eli/reg/2016/679/oj

<a id="ref-10"></a>**[10]** European Parliament and Council of the European Union. (2022, December). *Regulation (EU) 2022/2554 — Digital Operational Resilience Act (DORA)*. Official Journal of the European Union, L 333. ELI: reg/2022/2554. https://eur-lex.europa.eu/eli/reg/2022/2554/oj

<a id="ref-11"></a>**[11]** European Parliament and Council of the European Union. (2024). *Regulation (EU) 2024/1183 — eIDAS 2.0 (European Digital Identity)*. Official Journal of the European Union. ELI: reg/2024/1183. https://eur-lex.europa.eu/eli/reg/2024/1183/oj

<a id="ref-12"></a>**[12]** European Parliament and Council of the European Union. (2024). *Regulation (EU) 2024/1624 — Anti-Money Laundering Regulation (AMLR)*. Official Journal of the European Union. https://eur-lex.europa.eu/eli/reg/2024/1624/oj

<a id="ref-13"></a>**[13]** European Parliament and Council of the European Union. (2024, June). *Regulation (EU) 2024/1689 — EU Artificial Intelligence Act*. Official Journal of the European Union. ELI: reg/2024/1689. https://eur-lex.europa.eu/eli/reg/2024/1689/oj

<a id="ref-14"></a>**[14]** European Parliament and Council of the European Union. (2024, October). *Regulation (EU) 2024/2847 — Cyber Resilience Act*. Official Journal of the European Union. ELI: reg/2024/2847. https://eur-lex.europa.eu/eli/reg/2024/2847/oj

<a id="ref-15"></a>**[15]** Federative Republic of Brazil. (2018). *Lei Geral de Proteção de Dados Pessoais (LGPD)*. Government of Brazil. Lei nº 13.709/2018. https://www.gov.br/anpd/pt-br

<a id="ref-16"></a>**[16]** International Electrotechnical Commission. (2018). *IEC 62443 — Industrial communication networks — Network and system security*. IEC. https://webstore.iec.ch/en/publication/7029

<a id="ref-17"></a>**[17]** International Organization for Standardization. (2022). *ISO/IEC 27001:2022 — Information security, cybersecurity and privacy protection — Information security management systems — Requirements*. ISO/IEC. ISO/IEC 27001:2022. https://www.iso.org/standard/27001

<a id="ref-18"></a>**[18]** International Organization for Standardization. (2022). *ISO/IEC 27002:2022 — Information security controls*. ISO/IEC. ISO/IEC 27002:2022. https://www.iso.org/standard/75652.html

<a id="ref-19"></a>**[19]** International Organization for Standardization. (2019). *ISO/IEC 27701:2019 — Privacy information management*. ISO/IEC. ISO/IEC 27701:2019. https://www.iso.org/standard/71670.html

<a id="ref-20"></a>**[20]** National Cyber Security Centre (UK). (2025). *Cyber Essentials — Montpellier (2025)*. NCSC, IASME Consortium. https://www.ncsc.gov.uk/cyberessentials/overview

<a id="ref-21"></a>**[21]** National Institute of Standards and Technology. (2024). *Cybersecurity Framework (CSF) 2.0* (2.0). U.S. Department of Commerce. NIST CSWP 29. https://www.nist.gov/cyberframework

<a id="ref-22"></a>**[22]** National Institute of Standards and Technology. (2024). *Protecting Controlled Unclassified Information in Nonfederal Systems and Organizations* (Revision 3). U.S. Department of Commerce. NIST SP 800-171 Rev. 3. https://csrc.nist.gov/pubs/sp/800/171/r3/final

<a id="ref-23"></a>**[23]** National Institute of Standards and Technology. (2020). *Security and Privacy Controls for Information Systems and Organizations* (Revision 5). U.S. Department of Commerce. NIST SP 800-53 Rev. 5. https://csrc.nist.gov/pubs/sp/800/53/r5/upd1/final

<a id="ref-24"></a>**[24]** North American Electric Reliability Corporation. (2024). *NERC Critical Infrastructure Protection (CIP) Reliability Standards*. NERC. https://www.nerc.com/pa/Stand/Pages/CIPStandards.aspx

<a id="ref-25"></a>**[25]** Norwegian Ministry of Justice and Public Security. (2018). *Personopplysningsloven — Norwegian Personal Data Act*. Lovdata. https://lovdata.no/dokument/NL/lov/2018-06-15-38

<a id="ref-26"></a>**[26]** Office of the Australian Information Commissioner. (1988). *Privacy Act 1988 (Cth) and Australian Privacy Principles*. Australian Government. https://www.oaic.gov.au/privacy/the-privacy-act

<a id="ref-27"></a>**[27]** Payment Card Industry Security Standards Council. (2018). *Payment Card Industry Data Security Standard v3.2.1* (v3.2.1). PCI SSC. https://www.pcisecuritystandards.org/document_library/?category=pcidss

<a id="ref-28"></a>**[28]** Payment Card Industry Security Standards Council. (2022). *Payment Card Industry Data Security Standard v4.0* (v4.0). PCI SSC. https://www.pcisecuritystandards.org/document_library/?category=pcidss

<a id="ref-29"></a>**[29]** Public Company Accounting Oversight Board. (2007). *Auditing Standard 2201 — An Audit of Internal Control Over Financial Reporting*. PCAOB. PCAOB AS 2201. https://pcaobus.org/oversight/standards/auditing-standards/details/AS2201

<a id="ref-30"></a>**[30]** Royal Norwegian Ministry of Defence. (2018). *Sikkerhetsloven — Norwegian Security Act 2018*. Lovdata. https://lovdata.no/dokument/NL/lov/2018-06-01-24

<a id="ref-31"></a>**[31]** Splunk Inc. (2026). *Search Reference: SPL Commands and Functions*. Splunk LLC, a Cisco company. Retrieved May 11, 2026, from https://docs.splunk.com/Documentation/Splunk/latest/SearchReference/WhatsInThisManual

<a id="ref-32"></a>**[32]** Standing Committee of the National People's Congress (China). (2021). *Personal Information Protection Law of the People's Republic of China*. National People's Congress. http://en.npc.gov.cn.cdurl.cn/2021-12/29/c_694559.htm

<a id="ref-33"></a>**[33]** U.S. Congress. (2002). *Sarbanes-Oxley Act of 2002 — Public Company Accounting Reform and Investor Protection Act*. U.S. Government. Pub. L. 107–204. https://www.sec.gov/about/laws/soa2002.pdf

<a id="ref-34"></a>**[34]** U.S. Department of Defense. (2024). *Cybersecurity Maturity Model Certification (CMMC) 2.0* (2.0). Office of the Under Secretary of Defense for Acquisition and Sustainment. https://dodcio.defense.gov/CMMC/

<a id="ref-35"></a>**[35]** U.S. Department of Education. (1974). *Family Educational Rights and Privacy Act (FERPA)*. U.S. Government. 20 USC § 1232g. https://www2.ed.gov/policy/gen/guid/fpco/ferpa/index.html

<a id="ref-36"></a>**[36]** U.S. Department of Health & Human Services. (2002). *HIPAA Privacy Rule (45 CFR Parts 160 and 164, Subparts A and E)*. Office for Civil Rights, HHS. 45 CFR 160, 164. https://www.hhs.gov/hipaa/for-professionals/privacy/index.html

<a id="ref-37"></a>**[37]** U.S. Department of Health & Human Services. (2013). *HIPAA Security Rule (45 CFR Parts 160 and 164, Subparts A and C)*. Office for Civil Rights, HHS. 45 CFR 160, 164. https://www.hhs.gov/hipaa/for-professionals/security/index.html

<a id="ref-38"></a>**[38]** U.S. Federal Trade Commission. (2023). *FTC Safeguards Rule (16 CFR Part 314, 2023 amendments)*. Federal Trade Commission. 16 CFR 314. https://www.ftc.gov/legal-library/browse/rules/safeguards-rule

<a id="ref-39"></a>**[39]** U.S. General Services Administration / FedRAMP PMO. (2023). *FedRAMP Security Controls Baseline, Rev. 5* (Rev. 5). FedRAMP Program Management Office. https://www.fedramp.gov/rev5/baselines/

<a id="ref-40"></a>**[40]** U.S. Transportation Security Administration. (2023). *TSA Security Directive Pipeline-2021-02 series*. U.S. Department of Homeland Security. https://www.tsa.gov/news/press/releases/2022/07/21/tsa-revises-and-reissues-cybersecurity-requirements-pipeline-owners

<a id="ref-41"></a>**[41]** United Kingdom Parliament. (2018). *Data Protection Act 2018 (UK GDPR, retained EU law)*. The Stationery Office. 2018 c. 12. https://www.legislation.gov.uk/ukpga/2018/12/contents

### Related repository documents

- [`docs/build-artefacts-reference.md`](build-artefacts-reference.md)
- [`docs/coverage-methodology.md`](coverage-methodology.md)
- [`docs/evidence-packs/README.md`](evidence-packs/README.md)
- [`docs/guides/cisco-ise.md`](guides/cisco-ise.md)
- [`docs/guides/vulnerability-management.md`](guides/vulnerability-management.md)
- [`docs/license-inventory.md`](license-inventory.md)
- [`docs/signed-provenance.md`](signed-provenance.md)

### Cited by

- [`docs/clause-navigator-guide.md`](clause-navigator-guide.md)
- [`docs/compliance-story-guide.md`](compliance-story-guide.md)
- [`docs/guides/regulatory-compliance-master.md`](guides/regulatory-compliance-master.md)
- [`docs/non-technical-view.md`](non-technical-view.md)
- [`docs/site-user-guide.md`](site-user-guide.md)

<!-- END-AUTOGENERATED-SOURCES -->
