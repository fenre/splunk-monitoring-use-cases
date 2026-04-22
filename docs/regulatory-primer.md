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
4. [Tier-1 regulation deep dives](#4-tier-1-regulation-deep-dives) — 11 in-depth entries
5. [Derivative regulations (propagated via `derivesFrom`)](#5-derivative-regulations-propagated-via-derivesfrom)
6. [Appendix A — All 34 per-regulation subcategories at a glance](#appendix-a--all-34-per-regulation-subcategories-at-a-glance)
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
- **By regulation** — 11 tier-1 frameworks covered deeply, plus 34 per-regulation
  subcategories (cat-22 subcategories 22.1 through 22.34) and an additional 48
  tier-2 frameworks in the appendix. Regulation-level reading is the right
  choice when you are answering a specific audit, mapping against a specific
  RFP, or preparing a regulator response.

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
| `T1`  | **Tier 1** — a top-priority regulation the catalogue targets at 100% common-clauses coverage. 11 frameworks; see `api/v1/compliance/coverage.json`. |
| `T2`  | **Tier 2** — authored to meaningful partial coverage; 56 frameworks including all 5 derivative privacy regulations. |
| `T3`  | **Tier 3** — referenced or meta-frameworks; 1 today (`meta-multi`). |

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
produces an inherited UK GDPR Art.32 entry at `partial`, never `full`.

### Clause citations

Clauses are cited using the regulator's own notation exactly as it appears in
the authoritative source:

- `Art.32(1)(b)` — Article 32, paragraph 1, sub-point (b) (GDPR style).
- `§1798.100` — California Civil Code section 1798.100 (CCPA style).
- `3.5.1`  — PCI DSS-style numbered requirement.
- `AC-2`   — NIST 800-53-style control identifier.
- `CC6.1`  — SOC 2 / AICPA Trust Services Criterion identifier.

Every clause in `data/regulations.json` is validated against a regulator-
specific regular expression (`clauseGrammar`) so free-text values like
`"Art.  32  para. 1"` fail CI before they reach the API.

### Regulation priority weights

`priorityWeight` is a per-clause weight applied by the coverage methodology.
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
in this section is tagged against 3 – 6 tier-1 regulations and, after
Phase 3.3, against the derivative privacy regulations too.

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
[`use-cases/cat-22-regulatory-compliance.md` §22.35](../use-cases/cat-22-regulatory-compliance.md)
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
(non-discrimination); LGPD Art.18 (data subject rights); APPI Arts.32 – 34
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
assessment) evidence packs, adequacy-decision age tracking, model-contractual-
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
access); CMMC AC.L2-3.1.5 (least privilege); NIS2 Art.21.2(j) (access control
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

**Why it matters:** vulnerability management is where compliance meets
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
reporting with compensating-control attestation, SBOM-driven dependency
scanning, zero-day emergency patching workflow attestation.

**Where to look in the catalogue:**
§22.43 (UC-22.43.1 through UC-22.43.5) · `api/v1/compliance/ucs/22.43.1.json` ff.

### 3.10 22.44 — Third-party and supply-chain risk

**Control question:** can the organisation prove that every third party with
access to data or systems is identified, tiered, contracted appropriately,
reviewed on cadence, and monitored continuously for the relevant risk
indicators?

**Why it matters:** SolarWinds, Kaseya, Log4j, MOVEit, and the broader
2023-2025 enforcement of supply-chain-focused rules (NIS2, DORA, SEC
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
(vendor management); CMMC SA.L2-3.4.x (supply-chain protection).

**What the catalogue delivers:** continuous vendor-risk-score ingestion,
SBOM-to-vendor cross-reference, vendor-access expiry automation,
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
TRM 11.2 (segregation of duties); MiFID II Delegated Regulation Art.26
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

**Regulation:** Regulation (EU) 2016/679 (*GDPR*), in force 25 May 2018.
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
`full` or `partial` assurance. Full artefacts: cat-22 §22.1 (13 native UCs)
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
above. Phase 3.3 of the catalogue applies the `derivesFrom` graph to
propagate every GDPR mapping into UK GDPR with one-step assurance
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

**Regulation:** PCI DSS v4.0 (30 Mar 2024 effective; v3.2.1 sunset 31 Mar
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
43 dedicated PCI DSS UCs (22.11.1 through 22.11.65 with gaps),
including cardholder-data-environment boundary detection, CHD-in-logs
prevention, PAN-in-email detection, key-custody attestation, and PCI
DSS 4.0 customised-approach-alternative evidence packaging.

**Where to look:** §22.11 · `api/v1/compliance/regulations/pci-dss.json` ·
[`api/v1/compliance/regulations/pci-dss@v4.0.json`](../api/v1/compliance/regulations/pci-dss@v4.0.json).

### 4.4 HIPAA Security — Health Insurance Portability and Accountability Act Security Rule (US) · `T1`

**Regulation:** HIPAA Security Rule, 45 CFR Part 160 and Part 164
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
dedicated HIPAA UCs covering ePHI access logging, audit-trail gap
detection, encryption of ePHI at rest and in transit, minimum-necessary
rule enforcement, workforce-termination access revocation, and
breach-risk-assessment artefact generation.

**Where to look:** §22.10 · `api/v1/compliance/regulations/hipaa-security.json`.

### 4.5 SOX ITGC — Sarbanes-Oxley IT General Controls (US) · `T1`

**Regulation:** Sarbanes-Oxley Act §302 and §404 (management assertion and
external auditor attestation of internal control over financial reporting),
operationalised through **PCAOB AS 2201** and **COBIT** / **COSO 2013**
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
dedicated SOX ITGC UCs plus the cross-cutting SoD family (22.48).
The catalogue is designed to produce both point-in-time evidence (snapshot
at year-end) and period-of-operation evidence (continuous-control-monitoring
dashboards) which aligns with the SOX Type 2-equivalent testing model.

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

**What the catalogue delivers:** 100 % tier-1 coverage. §22.8 ships 75 UCs
dedicated to SOC 2 controls with particular focus on continuous control
monitoring, which is the hallmark of a mature Type 2 programme.

**Where to look:** §22.8 · `api/v1/compliance/regulations/soc-2.json`.

### 4.7 ISO 27001:2022 — Information Security Management System (GLOBAL) · `T1`

**Regulation:** ISO/IEC 27001:2022 (*Information security, cybersecurity
and privacy protection — Information security management systems —
Requirements*), with Annex A controls aligned to ISO/IEC 27002:2022
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
§22.6 ships 105 UCs dedicated to ISO 27001 Annex A controls.

**Where to look:** §22.6 · `api/v1/compliance/regulations/iso-27001.json`.

### 4.8 NIST CSF 2.0 — Cybersecurity Framework (US / GLOBAL) · `T1`

**Regulation:** NIST Cybersecurity Framework 2.0 (Feb 2024 revision of the
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

**What the catalogue delivers:** 100 % tier-1 coverage; every CSF function
has dedicated UCs in §22.7 plus cross-cutting coverage.

**Where to look:** §22.7 · `api/v1/compliance/regulations/nist-csf.json`.

### 4.9 NIST 800-53 Rev.5 — Security and Privacy Controls (US) · `T1`

**Regulation:** NIST Special Publication 800-53 Revision 5 (*Security and
Privacy Controls for Information Systems and Organizations*), with
controls organised into 20 families (AC, AU, CM, IA, IR, SC, SI, …).
Baseline catalogues: Low, Moderate, High, Privacy. The **800-53B** baseline
document defines which controls apply to each impact level.

**Who must comply:** US federal information systems (FISMA), most
DoD systems (via DFARS), and contractually by FedRAMP-authorised cloud
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
138 UCs dedicated to 800-53 Rev.5 controls with `controlFamily` tags
that align with the OSCAL component-definition facade at
`api/v1/oscal/component-definitions/*`.

**Where to look:** §22.14 · `api/v1/compliance/regulations/nist-800-53.json`
· [`api/v1/oscal/catalogs/nist-sp-800-53-r5.normalised.json`](../api/v1/oscal/catalogs/nist-sp-800-53-r5.normalised.json).

### 4.10 NIS2 — Network and Information Security Directive 2 (EU) · `T1`

**Regulation:** Directive (EU) 2022/2555 (*NIS2 Directive*), adopted 14
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

**What the catalogue delivers:** 100 % tier-1 coverage. §22.2 ships 63
dedicated NIS2 UCs.

**Where to look:** §22.2 · `api/v1/compliance/regulations/nis2.json`.

### 4.11 DORA — Digital Operational Resilience Act (EU) · `T1`

**Regulation:** Regulation (EU) 2022/2554 (*DORA*), adopted 14 Dec 2022,
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
dedicated DORA UCs with particular focus on Art.19 incident-reporting
(the single most-audited DORA clause in 2025).

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
derived from NIST 800-171 Rev.2, so the catalogue coverage shares most
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

**What the catalogue delivers:** 100 % tier-1 coverage.

**Where to look:** §22.20 · `api/v1/compliance/regulations/cmmc.json`.

---

## 5. Derivative regulations (propagated via `derivesFrom`)

Derivative regulations re-use the substance of a parent framework. The
catalogue propagates compliance entries from parents to derivatives
mechanically in Phase 3.3, with full traceability via the
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

## Appendix A — All 34 per-regulation subcategories at a glance

| Subcategory | Regulation | Jurisdiction | Tier | UCs | API endpoint |
|-------------|------------|--------------|------|-----|--------------|
| 22.1 | GDPR | EU/EEA | T1 | 13 + derivative fan-out | `regulations/gdpr.json` |
| 22.2 | NIS2 | EU | T1 | 63 | `regulations/nis2.json` |
| 22.3 | DORA | EU | T1 | ~30 | `regulations/dora.json` |
| 22.4 | CCPA / CPRA | US-CA | T2 | inherit | `regulations/ccpa.json` |
| 22.5 | MiFID II | EU | T2 | see §22.5 | `regulations/mifid-ii.json` |
| 22.6 | ISO 27001 | GLOBAL | T1 | 105 | `regulations/iso-27001.json` |
| 22.7 | NIST CSF | US/GLOBAL | T1 | 54 | `regulations/nist-csf.json` |
| 22.8 | SOC 2 | US/GLOBAL | T1 | 75 | `regulations/soc-2.json` |
| 22.9 | Compliance trending | cross-framework | n/a | dashboards | `compliance/coverage.json` |
| 22.10 | HIPAA Security | US | T1 | 76 | `regulations/hipaa-security.json` |
| 22.11 | PCI DSS v4.0 | GLOBAL | T1 | 137 | `regulations/pci-dss.json` |
| 22.12 | SOX / ITGC | US | T1 | 71 | `regulations/sox-itgc.json` |
| 22.13 | NERC CIP | US/CA | T2 | see §22.13 | `regulations/nerc-cip.json` |
| 22.14 | NIST 800-53 Rev.5 | US | T1 | 138 | `regulations/nist-800-53.json` |
| 22.15 | IEC 62443 | GLOBAL | T2 | see §22.15 | `regulations/iec-62443.json` |
| 22.16 | TSA Pipeline Security | US | T2 | see §22.16 | `regulations/tsa-sd.json` |
| 22.17 | FDA 21 CFR Part 11 | US | T2 | see §22.17 | `regulations/fda-part-11.json` |
| 22.18 | API 1164 SCADA Security | US | T2 | see §22.18 | `regulations/api-rp-1164.json` |
| 22.19 | FISMA / FedRAMP | US | T2 | see §22.19 | `regulations/fedramp.json` + `regulations/fisma.json` |
| 22.20 | CMMC 2.0 | US | T1 | see §22.20 | `regulations/cmmc.json` |
| 22.21 | EU AI Act | EU | T2 | see §22.21 | `regulations/eu-ai-act.json` |
| 22.22 | PSD2 / Payment Services | EU | T2 | see §22.22 | `regulations/psd2.json` |
| 22.23 | EU Cyber Resilience Act (CRA) | EU | T2 | see §22.23 | `regulations/eu-cra.json` |
| 22.24 | eIDAS 2.0 | EU | T2 | see §22.24 | `regulations/eidas.json` |
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

For the full 60-framework inventory (tier-1, tier-2, and meta), consult
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
| PIPL | CN | 1 Nov 2021 | independent | CAC |
| SA PDPL | SA | 14 Sep 2023 | independent | SDAIA |
| HIPAA Privacy | US | 14 Apr 2003 | independent (sectoral — healthcare) | HHS OCR |

All of these are covered in `data/regulations.json`; derivative propagation
is applied in Phase 3.3.

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
inherited from a parent regulation. Phase 3.3 propagates parent-clause
coverage to derivatives via the `derivesFrom` graph.

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
regulation and version. The `data/provenance/retrieval-manifest.json` file
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
