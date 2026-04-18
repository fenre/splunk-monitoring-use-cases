# SME review guide (Phase 5.2 QA gate)

> **Status:** active from Phase 5.2 onwards.
> **Audience:** project maintainers coordinating subject-matter expert
> (SME) review, and the SMEs they work with.
> **What this is.** The rubric used when a SPL-bearing, tier-1-claiming
> use case must be reviewed by a qualified subject-matter expert before
> it is allowed to claim the `full` assurance level on a regulatory
> clause. SME review is the last of three QA gates (peer review →
> legal review → SME review) and is scoped to technical correctness
> and regulatory-evidence acceptability — *not* clause-number accuracy
> (legal) and *not* schema hygiene (peer).

---

## 1. Scope of SME review

SME review covers the **technical and evidentiary** surface of a UC:
does the SPL actually produce the claimed signal against the
authoring data source, and is the resulting evidence acceptable to
an auditor for the cited regulation?

### 1.1 Content that triggers SME review

A PR triggers the Phase 5.2 SME-review gate when **any** of the
following are true for a UC sidecar under `use-cases/cat-*/uc-*.json`:

- The UC is **new** and carries `compliance[].assurance == "full"`
  against at least one **tier-1 regulation** (GDPR, UK GDPR, PCI DSS,
  HIPAA, SOX/ITGC, SOC 2, ISO 27001, NIST CSF, NIST 800-53, NIS2,
  DORA, CMMC).
- The UC's SPL materially changes for an existing tier-1 `full`
  mapping — any diff to the query body, base search, eval/stats
  pipeline, or `controlTest.spl` counts.
- A new `controlTest` block is added **or** an existing block's
  `fixtureRef` / positive / negative events are edited.
- The UC raises its `compliance[].assurance` from `contributing` or
  `partial` to `full` against a tier-1 regulation.
- The UC's `provenance` changes from `derived-from-parent` to
  `author:hand-authored` (the author is now asserting first-party
  technical correctness rather than inheriting it).
- A Splunk app under `splunk-apps/splunk-uc-<reg>/` ships a saved
  search, dashboard, or lookup that is not byte-identical to its
  generator input — i.e. a hand-authored addition inside the
  generated tree.

### 1.2 Content that does **not** trigger SME review

- New UCs that only claim `partial` or `contributing` assurance on
  tier-1 regulations (peer review is sufficient for those).
- Tier-2/tier-3 regulation-only UCs (CCPA, nFADP, LGPD, APPI, PIPEDA,
  POPIA, AU Privacy, KVKK, NIST 800-171, FedRAMP, NIST SSDF,
  IEC 62443, NERC CIP, TISAX, CSA CCM, SWIFT CSCF, etc.).
- Derivative content propagated by
  `scripts/generate_phase3_3_derivatives.py`. Derivatives inherit the
  parent's SME review — the derivation is mechanical and one-way
  (assurance never rises).
- UC sidecar edits that change metadata only (primer text, `notes`,
  `references`, `industry`, `tags`) without SPL or `controlTest`
  changes.
- Build-pipeline changes, generator code, CI configuration, scorecard
  CSS, `non-technical-view.js`, `docs/regulatory-primer.md` (the last
  is covered by legal review).
- Mini-category UCs (22.35–22.49) that carry `contributing` assurance
  against tier-1 regulations (peer review covers the SPL hygiene, and
  legal review covers the clause accuracy; no fixture-replay SME
  review is required because no `full`-assurance auditor-evidence
  claim is being made).

### 1.3 Relationship to the other two QA gates

Peer review (Phase 4.5a), legal review (Phase 4.5b) and SME review
(Phase 5.2) are **distinct and sequential** for tier-1 `full`
content:

1. **Peer review** — is the sidecar schema-valid, are the mappings
   internally consistent, does the symmetric index reconcile?
   Engineer-to-engineer. Blocks merge on any `fail`.
2. **Legal review** — is the clause citation correct, does the
   primer say what the regulator actually says, is `mode: "satisfies"`
   an honest claim? Counsel. Blocks merge on `rejected`;
   `approved-with-revisions` gates the final commit.
3. **SME review** (this guide) — does the SPL actually detect what
   it claims when run against the authoring data source, and would
   an auditor for the cited regulation accept the resulting Splunk
   output as evidence? Subject-matter expert. Blocks merge on
   `rejected`; `conditional` requires an `smeCaveat` on the
   sidecar.

A single SME may cover the SPL-correctness dimension **or** the
auditor-evidence dimension but not both unless their credentials
warrant it (see §2). Two-SME reviews are explicitly supported: one
signoff record per SME, both pointing at the same commit.

## 2. Who can perform an SME review

SME review is performed by a reviewer in one of five roles. The
reviewer's role is recorded in the `reviewerRole` field of the
signoff.

| `reviewerRole`          | Who it means                                                   | Typical content                                                                 |
| ----------------------- | -------------------------------------------------------------- | ------------------------------------------------------------------------------- |
| `splunk-engineer`       | Professional-services or customer-success Splunk engineer.     | SPL correctness against the authoring data source; AppInspect-friendly constructs; field-extraction prerequisites. |
| `regulatory-auditor`    | Qualified auditor holding a recognised credential.             | Auditor-evidence acceptability; retention / redaction posture; mapping of the SPL output to the cited clause. |
| `security-architect`    | Enterprise security architect with detection-engineering depth. | Detection logic robustness, false-positive posture, cross-UC correlation, ATT&CK coverage. |
| `industry-sme`          | Industry-specific expert.                                       | Domain-specific realism (e.g. clinician for HIPAA, controller for SOX/ITGC, power-system engineer for NERC CIP). |
| `internal-review-board` | Multi-member internal panel.                                    | Scope where no single SME covers the full rubric; the panel records one consolidated signoff with individual roles in `notes`. |

Recommended credentials per role (recorded in the optional
`credentials[]` field of the signoff):

- `splunk-engineer`: Splunk Core Certified Power User, Splunk Core
  Certified Consultant, Splunk Enterprise Certified Architect.
- `regulatory-auditor`:
  - PCI DSS → QSA (Qualified Security Assessor) or ISA.
  - HIPAA → HITRUST CCSFP, HCISPP.
  - SOX/ITGC → CISA, CPA (with ITGC specialisation).
  - SOC 2 → CPA firm issuing AT-C 205 / SSAE 18 reports.
  - ISO 27001 → ISO 27001 Lead Auditor.
  - GDPR / UK GDPR → CIPP/E, CIPM, DPO certification.
  - NIST 800-53 / CSF / CMMC → C3PAO assessors, CISSP, CGRC.
  - NIS2 / DORA → national regulator equivalent (e.g. ENISA-endorsed
    auditor, FCA / ECB supervisory expert).
- `security-architect`: CISSP-ISSAP, SABSA, TOGAF, GIAC-GSE; at
  minimum 5 years of Splunk detection engineering.
- `industry-sme`: Clinical Informatics (HIPAA), FCA / SEC registered
  principal (SOX), ICSE / GICSP (OT for NERC CIP / IEC 62443).

A reviewer who does **not** hold one of the recognised credentials
above may still serve as an SME, but the project lead must note the
competency rationale in `notes` and escalate the signoff to a second
SME (see §5).

## 3. The six-point SME rubric

Every SME review walks these six checks in order. A single "fail"
blocks the outcome from being `approved`. The SME may still sign off
with `approved-with-revisions`, `conditional`, `scope-downgrade`, or
`rejected` — see §3.7.

### 3.1 SPL correctness (`splCorrectness`)

**Question.** Does the SPL produce the claimed signal when replayed
against the committed `controlTest.fixtureRef` (or an equivalent
SME-sourced fixture)?

**How to check.**

1. Load the UC sidecar and read `controlTest.spl` (or the UC's
   primary SPL if `controlTest` is absent — rare for `full`
   assurance).
2. Find `controlTest.fixtureRef` and load the positive + negative
   fixtures from `sample-data/uc-<id>/…`.
3. Replay the SPL against the positive fixture on a Splunk instance
   (search head, sandbox, or a local `| inputlookup` of the fixture
   as a CSV). Confirm it returns at least one event.
4. Replay against the negative fixture. Confirm it returns zero
   events.
5. Record the result in `fixtureReplayResult`:
   ```json
   "fixtureReplayResult": {
     "replayed": true,
     "positiveDetected": true,
     "negativeSilent": true,
     "notes": "Replayed on Splunk Cloud 9.2.2404, search head cluster, no accelerated tstats."
   }
   ```

**Fail modes.** Positive fixture silent; negative fixture fires
(false positive); SPL errors out because a required field is not
extracted by the authoring data source; SPL depends on an
uninstalled TA or a lookup not shipped in the repo.

**`n/a` is permitted when.** The UC is a `satisfies`-only
record-keeping control with no detection SPL (e.g. "Retains
authentication logs for 1 year"); `fixtureReplayResult.replayed`
must be `false` in that case.

### 3.2 Data-source realism (`dataSourceRealism`)

**Question.** Is the authoring data source realistic for the
regulation's deployment context?

**How to check.**

- The UC's `dataSources` / `authoringData` / `sourcetypes[]` fields
  must list data sources that are actually available in regulated
  organisations. A fabricated sourcetype (e.g. `custom:acme:pci`)
  that does not correspond to a published vendor integration is a
  red flag.
- Where the UC cites a vendor TA (e.g. `TA-meraki`), the SME
  confirms the TA's CIM fields and version pins are realistic for
  the current Splunkbase release.
- Where the UC cites CIM-only fields (`Authentication`,
  `Change`, `Endpoint`), the SME confirms the CIM data model is
  achievable without exotic acceleration for the UC's latency claim.

**Fail modes.** Authoring data source is a made-up sourcetype;
required fields require a TA the project does not ship or reference;
the UC's latency claim is incompatible with the data-source ingest
pattern (e.g. "<1 min" on a source that only ingests daily).

### 3.3 Splunk compatibility (`splunkCompat`)

**Question.** Does the SPL pass Splunk Cloud vetting and AppInspect
without warnings relevant to the UC's deployment target?

**How to check.**

1. Run `scripts/audit_splunk_cloud_compat.py` locally; the SME
   confirms the UC has no `severity=fail` entries.
2. Inspect the SPL for AppInspect-incompatible constructs:
   - Custom scripted commands (`| script …`, `| custom_cmd …`) are
     **forbidden** in Splunk Cloud apps.
   - Deprecated commands (`| input …`, `| indexpreview`,
     `| convert dur2sec`) are **forbidden**.
   - External lookups (`| lookup external.py …`) must be shipped in
     the repo under `lookups/` with a matching `transforms.conf`.
3. If the UC ships in a per-regulation Splunk app (`splunk-apps/`),
   the SME confirms the generated `savedsearches.conf` stanza
   round-trips through Splunk AppInspect (or through the project's
   packaged AppInspect gate once it lands).

**Fail modes.** Custom scripted commands; missing TAs; SPL that
only works in an on-prem SH with legacy commands; dashboard that
queries a live index rather than the shipped `uc_compliance_mappings`
lookup.

### 3.4 Evidence completeness (`evidenceCompleteness`)

**Question.** Is the evidence path complete for the cited
regulation's audit expectations?

**How to check.** The SME walks the UC's `evidence` field (and the
regulation's evidence pack under `docs/evidence-packs/<reg>.md`) and
confirms each of the following is addressed:

1. **Retention.** The UC's SPL returns events within the retention
   window required by the regulation (e.g. 6 years for HIPAA, 1
   year for PCI DSS, 5 years for SOX/ITGC). If the regulation
   requires retention longer than the typical Splunk hot/warm/cold
   policy, the UC must cite an archive or summary-indexing pattern.
2. **Redaction.** PII fields in the UC's output are redacted /
   hashed where the regulation requires it (e.g. cardholder data
   under PCI DSS must be masked; patient IDs under HIPAA must be
   stripped from ad-hoc search results).
3. **Queryability.** An auditor can reproduce the UC's result with
   a search string that is documented in the evidence pack (not
   hidden behind a scheduled search or a saved KV store).
4. **Chain of custody.** The SPL output is immutable or append-only
   on the Splunk side; the evidence pack describes how the auditor
   verifies non-repudiation (access logs, role separation, HSM
   signing, etc.).

**Fail modes.** UC's output only retains 90 days when the regulation
requires 6 years; PII is returned in clear text on a UC that cites
GDPR Art. 32; evidence path assumes an ad-hoc search that cannot be
reproduced deterministically.

### 3.5 Regulation applicability (`regulationApplicability`)

**Question.** Would an auditor for the cited regulation accept the
UC's Splunk output as evidence of compliance with the cited clause?

**How to check.** The SME reads the `compliance[]` entry and asks:

- Is the `mode` honest for the control family? `satisfies` is a
  strong claim that should only be used for audit-evidence
  controls (e.g. "Logs privileged account access" satisfies SOX
  ITGC "PC 1 Privileged Access"); `detects-violation-of` is the
  correct mode for anomaly / threshold controls.
- Is the `assurance` level honest given the rubric in
  `docs/coverage-methodology.md` §2? `full` requires a working
  `controlTest` with positive + negative fixture AND the SME
  confirming that the SPL output, on its own, is sufficient to
  show the clause is met.
- Does the UC's output include the minimum fields an auditor would
  expect (user, timestamp, source IP, action, outcome)?

**Fail modes.** `mode: "satisfies"` on a control that is
informational only; `assurance: "full"` on a control where the SPL
output would not persuade an auditor (e.g. logs a dashboard widget
but cannot be re-run against historical data).

### 3.6 False-positive assessment (`falsePositiveAssessment`)

**Question.** Are the known false-positive scenarios enumerated and
acknowledged?

**How to check.**

- The UC sidecar's `knownFalsePositives[]` (or
  `notes` / `exclusions[]`) lists at least one FP scenario the SME
  recognises from their deployment experience.
- If no FP scenarios are listed, the SME confirms in `notes` that
  they have considered FP surface and judged it low (e.g. "Detects
  only on the HIPAA audit log sourcetype, which is
  administratively privileged and not user-accessible; no realistic
  FP surface identified").

**Fail modes.** No FP discussion on a detection UC; FP list is
fabricated (unrecognisable scenarios that the SME has never seen in
the wild).

**`n/a` is permitted when.** The UC is a pure record-keeping
control (`mode: "satisfies"`, no detection). FP assessment does not
apply — `controlTest` should also be absent or minimal.

### 3.7 Outcome matrix

| Outcome                    | Effect on PR                                                                 |
| -------------------------- | ---------------------------------------------------------------------------- |
| `approved`                 | PR unblocks. Signoff records SME name, role, date, and all six `pass` checks. |
| `approved-with-revisions`  | PR must be updated with the requested revisions before unblocking. SME signs off on the revised commit. `revisionsRequested[]` is required. |
| `rejected`                 | PR reverts the UC's `full` assurance claim. UC may be reauthored as `partial` or `contributing` to avoid the contested claim. `rejectionReason` is required. |
| `conditional`              | PR lands with `smeCaveat` fields added to the UC sidecar's `compliance[]` entries spelling out the SME's caveats. `caveats[]` is required. |
| `scope-downgrade`          | PR lands but the UC's `compliance[].assurance` is reduced (typically `full` → `partial`). No caveat required; the assurance change itself is the disposition. |

## 4. How to record a sign-off

The signoff file `data/provenance/sme-signoffs.json` is append-only.
To add a record, edit the file on the same PR that contains the
reviewed content. CI validates the file against
`schemas/sme-review-signoff.schema.json` and enforces semantic
invariants via `scripts/audit_sme_review_signoffs.py`.

Example record:

```json
{
  "pr": "#142",
  "date": "2026-05-20",
  "commit": "4f7a1b2",
  "reviewer": "Alex Hernandez, Splunk Professional Services",
  "reviewerRole": "splunk-engineer",
  "credentials": ["Splunk Core Certified Consultant", "CISSP"],
  "scope": {
    "ucs": ["22.14.3", "22.14.5", "22.14.8"],
    "regulations": ["GDPR", "UK-GDPR"],
    "fixtures": ["sample-data/uc-22.14.3/positive.json", "sample-data/uc-22.14.3/negative.json"]
  },
  "outcome": "approved-with-revisions",
  "checks": {
    "splCorrectness": "pass",
    "dataSourceRealism": "pass",
    "splunkCompat": "pass",
    "evidenceCompleteness": "pass",
    "regulationApplicability": "pass",
    "falsePositiveAssessment": "fail"
  },
  "revisionsRequested": [
    "UC-22.14.3: add `knownFalsePositives[]` entry for the Windows printer-spooler service account that legitimately triggers Event 4740 every 15 minutes on Windows Server 2019 print servers."
  ],
  "caveats": [],
  "fixtureReplayResult": {
    "replayed": true,
    "positiveDetected": true,
    "negativeSilent": true,
    "notes": "Replayed on Splunk Cloud Classic 9.2.2405 against the committed JSONL fixture; CIM Authentication alignment confirmed."
  },
  "notes": "Reviewed against a large German healthcare deployment on Epic EHR + Microsoft Active Directory; Art. 32 mapping is consistent with that auditor's typical evidence expectations."
}
```

### 4.1 SME caveats in UC sidecars

When an SME gives a `conditional` sign-off, the maintainer adds an
`smeCaveat` field on the relevant `compliance[]` entry in the UC
sidecar. The project's JSON schema (`schemas/uc.schema.json`)
already permits the field; it is rendered on the scorecard and in
the generated Splunk app help text. Example:

```json
{
  "regulation": "HIPAA",
  "version": "2013-final",
  "clause": "\u00a7164.312(b)",
  "mode": "satisfies",
  "assurance": "full",
  "rationale": "Audit control: logs all access to ePHI storage volumes under \u00a7164.312(b).",
  "smeCaveat": "Only applies to deployments where the EHR vendor's audit-log shipping is enabled at the application layer. On Epic deployments this requires the Epic Audit Repository; on Cerner/Oracle Health deployments this requires the AuditLogSync v4+ module. Field-level audit granularity below the patient-record boundary is NOT guaranteed and must be supplemented by UC-22.14.41."
}
```

### 4.2 Fixture replay records

`fixtureReplayResult` is optional but strongly encouraged. When
present, it MUST be self-consistent:

- `replayed: false` → `checks.splCorrectness` should be `n/a` (the
  SME did not actually run the SPL against the fixture; they
  assessed the SPL structurally only).
- `replayed: true` → `positiveDetected` and `negativeSilent` MUST
  agree with `checks.splCorrectness`:
  - Both `true` → `pass`.
  - Either `false` → `fail` (and `notes` must explain).

The audit script surfaces inconsistencies as warnings (not hard
failures) so that an SME can record a realistic fixture replay with
notes like "positive fixture fires on Event 4624 but the intended
detection is on Event 4625; the UC's polarity was corrected before
merge."

## 5. Escalation and dual-SME review

Certain content mandates **two** independent SME sign-offs,
typically one `splunk-engineer` and one `regulatory-auditor`:

- Any UC claiming `assurance: "full"` on a high-penalty tier-1
  clause (GDPR Art. 32/33/34, HIPAA \u00a7164.308, PCI DSS Req. 10,
  SOX ITGC Change Management).
- Any UC cited in the top-12 evidence pack for its regulation as the
  headline evidence for a clause (see
  `docs/evidence-packs/<reg>.md` §"Headline UCs").
- Any Splunk app under `splunk-apps/` that introduces a hand-authored
  saved search, dashboard, or lookup outside the generator's default
  output.

Two signoff records are appended — one per SME — each pointing at
the same commit. The audit script tolerates multiple records per
commit so long as the `reviewer` differs.

## 6. Privacy of the SME's identity

SME names are recorded in the public signoff file. Reviewers who
prefer not to be named publicly may instead be recorded as
`"<Employer> — Senior Consultant"` (or similar); the concrete
individual name is kept in an internal (non-public) ledger
maintained by the project lead. The public signoff must still
allow an external auditor to contact the employing firm and verify
the review.

## 7. Historical baseline

Content authored before Phase 5.2 was landed without explicit SME
sign-offs. That content is grandfathered and does not block merges
retroactively. The baseline cut-off is the commit that introduces
`data/provenance/sme-signoffs.json` (see `baseline_commit`). New
edits to grandfathered content that trigger the §1.1 conditions
**do** produce a new SME review.

## 8. Process timeline expectations

SME reviews are more time-intensive than peer reviews but shorter
than legal reviews:

- **`splunk-engineer` review** — typically completes within 1–2
  business days. Replaying a fixture against a Splunk instance and
  reviewing AppInspect compatibility is a routine task.
- **`regulatory-auditor` review** — 3–10 business days depending on
  the regulation's complexity and the auditor's current caseload.
- **`industry-sme` review** — variable; some domains (healthcare,
  energy, financial services) require specialised access or
  sandbox deployments that take weeks to provision.

Maintainers can split a PR into "SPL-first" and "regulatory-mapping-
second" commits to keep the SME review asynchronous from the legal
review — the former goes through peer + SME `splunk-engineer`
review, the latter through legal + SME `regulatory-auditor` review.
The final commit must pass **all three** gates before merge.

---

## See also

- `docs/peer-review-guide.md` — engineering peer-review rubric
  (Phase 4.5a).
- `docs/legal-review-guide.md` — regulatory claim review rubric
  (Phase 4.5b).
- `docs/regulatory-change-watch.md` — Phase 5.3 regulatory
  change-watch gate. SME reviewers should confirm that any regulation
  cited in `scope.regulations` has a fresh `lastCheckedAt`.
- `docs/signed-provenance.md` — Phase 5.4 signed provenance ledger.
  Every SME-reviewed `(UC, clause, mode, assurance)` tuple is hashed
  into a cryptographically verifiable merkle-root ledger; the
  reviewer's signoff PR number is snapshotted into the ledger entry's
  `signoffStatus.sme.latestSignoffPr` field on the next regeneration.
- `docs/coverage-methodology.md` — how `full` / `partial` /
  `contributing` assurance levels are defined.
- `docs/evidence-packs/README.md` — the headline UCs referenced in
  §5 escalation rules.
- `schemas/sme-review-signoff.schema.json` — machine-readable schema
  the signoff file validates against.
- `scripts/audit_sme_review_signoffs.py` — CI validator.
- [`LEGAL.md`](../LEGAL.md) — project-wide licence, attribution, and
  disclaimer document.
