# LEGAL — Licence, attribution, and disclaimers

This document accompanies the **Splunk Monitoring Use Cases** catalogue and its machine-readable compliance artefacts (under `data/`, `api/v1/`, `docs/` and `schemas/`). It is version-controlled and updated in lockstep with the regulatory content.

## 1. Not legal advice

**Nothing in this repository constitutes legal advice.** The catalogue and its compliance mappings are an engineering artefact — a machine-readable index that relates Splunk detections to clauses in published regulations, standards, and frameworks. They are **not** a substitute for:

- A qualified lawyer, solicitor, or licensed legal counsel for legal interpretation of any regulation.
- A credentialed assessor (QSA for PCI DSS; CPA / CIA for SOC 2 and SOX; NERC CIP compliance auditor; certified ISO 27001 Lead Auditor; ENISA-registered auditor for NIS2/DORA; etc.) for formal assessment or certification.
- Regulator-issued guidance. Where this repository cites a regulator URL, the regulator's own text always takes precedence over any interpretation here.

Organisations adopting this catalogue remain solely responsible for their own regulatory posture, including the correctness of any clause mapping claimed by a use case (UC).

## 2. Project licence

The catalogue source code, schemas, and content in this repository are licensed under the terms of [`LICENSE`](LICENSE) at the root of the repository.

## 3. Third-party content attributions

### 3.1 NIST (public domain, 17 U.S.C. § 105)

The following NIST materials are in the US public domain. Where this project ingests them, the retrieved files are stored under `data/crosswalks/` with a SHA-256 and a retrieval manifest.

- **NIST Online Informative References (OLIR)** — crosswalks such as NIST CSF ↔ NIST SP 800-53 Rev. 5.
  Source: <https://csrc.nist.gov/projects/olir>
- **NIST SP 800-53 Rev. 5 in OSCAL** — control catalogue, baselines, and profiles.
  Source: <https://github.com/usnistgov/oscal-content>
- **NIST Cybersecurity Framework 2.0** — discussion-text and subcategories.
  Source: <https://www.nist.gov/cyberframework>
- **NIST Cybersecurity and Privacy Reference Tool (CPRT)** — machine-readable reference data and mappings for NIST frameworks (including CSF subcategory and 800-53 control exports).
  Source: <https://csrc.nist.gov/Projects/cprt>

### 3.2 MITRE (LICENSE.txt, permissive)

- **MITRE ATT&CK** — techniques, tactics, and subtechnique IDs.
  Licence: MITRE ATT&CK Terms of Use, <https://attack.mitre.org/resources/terms-of-use/>.
  Source: <https://github.com/mitre/cti>
- **MITRE D3FEND** — countermeasure graph.
  Licence: CC BY 4.0 + trademark notice, <https://d3fend.mitre.org/terms-of-use>.

### 3.3 Atomic Red Team (Apache License 2.0)

- **Atomic Red Team** test definitions used for UC control-test simulation in the Phase 4.5 quality gate.
  Licence: Apache 2.0, <https://github.com/redcanaryco/atomic-red-team/blob/master/LICENSE.txt>.

### 3.4 Center for Threat-Informed Defense Mappings Explorer (Apache License 2.0)

- **CTID Mappings Explorer** cross-framework OLIR-style mappings, used under Apache 2.0.
  Source: <https://github.com/center-for-threat-informed-defense/mappings-explorer>
  This repository ingests the NIST SP 800-53 rev5 ↔ ATT&CK, CRI Profile ↔ ATT&CK, and CSA CCM ↔ ATT&CK JSON files. Only capability identifiers (e.g. `AC-2`, `STA-16`) and CTID's own rationale prose are retained; no upstream prose from CSA CCM, NIST, or CRI is redistributed.

### 3.5 Regulations cited by URL only (not redistributed)

The following sources are cited by URL in `data/regulations.json` and in individual UC references. Their text is **not** reproduced in this repository because the relevant licences prohibit redistribution or require paid access:

- **PCI DSS** (PCI SSC — published under a restricted licence; cited but not reproduced).
- **ISO/IEC 27001:2022** (ISO — commercial standard; cited by clause reference only).
- **IEC 62443 series** (IEC — commercial standard; cited by clause reference only).
- **SOC 2 Trust Services Criteria** (AICPA-CIMA — cited by criteria code only).
- **API RP 1164** (API — cited by section only).
- **SWIFT CSP CSCF** (SWIFT — cited by control number only).
- **EU regulations** (Eur-Lex — reproduction terms vary; clause citations only).

If you need the full text of any of these, retrieve it from the authoritative source under the licence the publisher provides.

### 3.6 Excluded sources

The following otherwise-useful sources are **deliberately not ingested** in this repository because their licences prohibit redistribution or derivative works:

- **Secure Controls Framework (SCF)** — CC BY-ND prevents derivative redistribution.
- **CIS Controls and CIS Benchmarks** — CC BY-NC-ND.
- **Cloud Security Alliance CCM full prose** — CC BY-NC-ND prevents prose redistribution. We ingest only CCM *identifiers* via the CTID Mappings Explorer (§ 3.4) which releases that index under Apache 2.0; the authoritative CCM prose itself is not reproduced.

We link to these projects where a catalogue user would benefit, but we do not redistribute their content.

## 4. Mapping methodology limits

- Every `compliance[]` entry in a UC JSON sidecar records a **regulation + version + clause + mode (satisfies | detects-violation-of) + assurance level + rationale**. The assurance level is bounded by the authoring evidence available at the time of the mapping; it is not a legal determination.
- Where NIST OLIR contradicts a mapping, `scripts/audit_compliance_mappings.py` reports the divergence. It is the maintainer's and SME's responsibility to resolve it.
- The three coverage metrics (clause %, priority-weighted %, assurance-adjusted %) are engineering metrics; they are useful for prioritisation and trend analysis but they are **not** a certification score.

## 5. QA review gates

Compliance content moves through three distinct and sequential QA gates before it is allowed to claim `compliance[].assurance == "full"` against a tier-1 regulation, backed by a fourth (scheduled) gate that keeps the regulatory provenance fresh:

1. **Peer review** (Phase 4.5a, §5a) — engineering rubric, blocks on schema hygiene and clause precision.
2. **Legal review** (Phase 4.5b, §5b) — regulatory-claim surface, blocks on citation accuracy and primer/evidence-pack prose.
3. **SME review** (Phase 5.2, §5c) — SPL technical correctness against the authoring data source and auditor-evidence acceptability, blocks on fixture replay and regulation-applicability grading.
4. **Regulatory change-watch** (Phase 5.3, §5d) — continuous external-truth gate, blocks when a tier-1 regulator's upstream artefact is older than the staleness policy permits.

A PR that lands `full`-assurance tier-1 content without recording all three human sign-offs fails CI (see §5a–§5c for each gate's audit script). The change-watch gate fails CI whenever the local watchlist falls outside the freshness envelope (see §5d).

## 5a. Peer review gate (Phase 4.5a)

Every pull request that adds or changes compliance content (cat-22, `schemas/uc.schema.json`, `data/regulations.json`, `docs/regulatory-primer.md`, `docs/evidence-packs/**`, `tests/golden/compliance-mappings.yaml`, or any UC sidecar under `use-cases/cat-*/uc-*.json`) MUST be peer-reviewed against the six-point rubric in [`docs/peer-review-guide.md`](docs/peer-review-guide.md) by an engineer who is **not** the author. The review is recorded as a sign-off in `data/provenance/peer-review-signoffs.json` and validated by `scripts/audit_peer_review_signoffs.py` in CI. This is an engineering gate — reviewers check clause precision, assurance honesty, MITRE/OSCAL cross-refs, provenance, derivative correctness, and build hygiene. It does **not** replace the legal gate in §5b or the SME gate in §5c.

## 5b. Legal review gate (Phase 4.5b)

Content that touches the **regulatory claim surface** of a tier-1 regulation (GDPR, UK GDPR, PCI DSS, HIPAA, SOX/ITGC, SOC 2, ISO 27001, NIST CSF, NIST 800-53, NIS2, DORA, CMMC) MUST be surfaced to qualified legal counsel for review before merge. The review process, trigger list, and recording workflow are documented in [`docs/legal-review-guide.md`](docs/legal-review-guide.md). Sign-offs are recorded in `data/provenance/legal-review-signoffs.json` against `schemas/legal-review-signoff.schema.json` and validated by `scripts/audit_legal_review_signoffs.py` in CI.

Legal review is explicitly limited to:

- Clause-number accuracy against the published regulation version.
- Appropriateness of the `mode` field (`satisfies` vs. `detects-violation-of`).
- Accuracy of primer and evidence-pack prose.
- Jurisdiction scope and effective-date correctness.

Legal review does **not** cover SPL correctness, deployment-time applicability, or whether a UC is "sufficient for compliance" — those remain the responsibility of the adopting organisation and its assessors (see §1).

When counsel returns an `approved-with-revisions`, `conditional`, or `scope-downgrade` outcome, the UC sidecar's `compliance[]` entry may carry a `legalCaveat` field (grammar defined in `schemas/uc.schema.json`) that is mirrored to the compliance scorecard and any generated Splunk app. The presence of `legalCaveat` is informational; it does not by itself affect a UC's assurance weighting.

## 5c. SME review gate (Phase 5.2)

Content that claims `compliance[].assurance == "full"` against a tier-1 regulation, that materially changes the SPL for an existing `full`-assurance mapping, that adds a new `controlTest` block, or that ships a hand-authored saved search, dashboard, or lookup inside a per-regulation Splunk app under `splunk-apps/` MUST pass an SME review before merge. The review process, trigger list, reviewer-role taxonomy, and recording workflow are documented in [`docs/sme-review-guide.md`](docs/sme-review-guide.md). Sign-offs are recorded in `data/provenance/sme-signoffs.json` against `schemas/sme-review-signoff.schema.json` and validated by `scripts/audit_sme_review_signoffs.py` in CI.

SME review is explicitly concerned with:

- **SPL correctness.** The SME replays the committed positive + negative `controlTest.fixtureRef` on a Splunk instance and confirms the SPL produces the claimed signal. The replay result is recorded in `fixtureReplayResult`.
- **Data-source realism.** The authoring data source (sourcetype, TA version, CIM fields) is realistic for the regulation's deployment context.
- **Splunk compatibility.** The SPL passes Splunk Cloud vetting and AppInspect; generated app stanzas round-trip cleanly.
- **Evidence completeness.** Retention, redaction, queryability, and chain-of-custody posture meet the regulation's audit expectations.
- **Regulation applicability.** An auditor for the cited regulation would accept the Splunk output as evidence of compliance with the cited clause.
- **False-positive assessment.** Known FP scenarios are enumerated, or the SME explicitly records that FP surface was considered and judged low.

Each check grades `pass`, `fail`, or `n/a`. An `approved` outcome requires no `fail` grades; `approved-with-revisions`, `conditional`, `scope-downgrade`, and `rejected` outcomes each carry specific recording obligations (see `docs/sme-review-guide.md` §3.7).

High-penalty tier-1 clauses (GDPR Art. 32/33/34, HIPAA §164.308, PCI DSS Req. 10, SOX/ITGC Change Management), the headline evidence-pack UCs for each regulation, and any hand-authored Splunk-app additions require **two** independent SME sign-offs on the same commit (typically one `splunk-engineer` and one `regulatory-auditor` — see `docs/sme-review-guide.md` §5).

When an SME returns a `conditional` outcome, the UC sidecar's `compliance[]` entry carries an `smeCaveat` field (grammar defined in `schemas/uc.schema.json`) that is mirrored to the compliance scorecard and any generated Splunk app. Typical caveat content: field-extraction prerequisites, TA version pins, industry-specific applicability constraints. Like `legalCaveat`, the presence of `smeCaveat` is informational; it does not by itself affect assurance weighting.

SME review does **not** cover clause-number accuracy (that is legal review's job in §5b) nor schema hygiene (that is peer review's job in §5a). A fully-vetted tier-1 `full`-assurance UC therefore carries three sign-offs — one per gate.

## 5d. Regulatory change-watch gate (Phase 5.3)

Peer, legal, and SME review all depend on the underlying regulation being the *current* one. The change-watch gate provides auditable evidence that the repository is tracking the live publisher state of every tier-1 regulation and the MITRE crosswalks we depend on. The ledger at `data/regulations-watch.json` records, per regulation, (i) the detection strategy (SHA256 drift on an OSCAL catalog, `http-head` on an EUR-Lex URL, RSS match on the HHS HIPAA feed, manual-review for paywalled standards), (ii) the last observation, and (iii) a staleness threshold beyond which CI will block release. The gate is implemented by `scripts/audit_regulatory_change_watch.py` and refreshed weekly by the scheduled GitHub Actions workflow `.github/workflows/regulatory-watch.yml`. The full rubric, operator runbook, and adding-a-new-regulation procedure live in [`docs/regulatory-change-watch.md`](docs/regulatory-change-watch.md).

When the scheduled probe detects a material upstream change, the workflow (i) commits a ledger refresh, (ii) opens a GitHub issue labelled `regulatory-change-watch`, and (iii) writes a finding to the watchlist entry's `openFinding` block. The finding remains open until a reviewer adopts the upstream change (via the Phase 1.4 ingest scripts and the three human gates above) and clears the block in a follow-up PR.

## 5e. Signed provenance ledger (Phase 5.4)

The Phase 4.5/5.2/5.3 gates above produce reviewer signal; Phase 5.4 renders that signal into a cryptographically verifiable artefact. The signed provenance ledger at `data/provenance/mapping-ledger.json` is a content-addressable, sorted-leaf merkle-rolled SHA-256 record of **every** clause-level compliance mapping the catalogue claims. Each entry carries a `canonicalHash` over `(mappingId, ucId, regulationId, regulationVersion, clause, mode, assurance, derivationSource)`; the top-level `merkleRoot` is a SHA-256 over the concatenation of those per-entry hashes in `mappingId` order. Each entry additionally snapshots the peer, legal, and SME review state at ledger-generation time, and records the `firstSeenCommit` and `lastModifiedCommit` in git history.

The ledger is regenerated and audited on every pull request by `scripts/generate_mapping_ledger.py --check` and `scripts/audit_mapping_ledger.py` (both wired into `.github/workflows/validate.yml`). On `v*.*.*` release tags, `scripts/stamp_ledger_release.py` copies the in-repo ledger to `dist/`, promotes `signature.state` from `unsigned` to `attested`, and `actions/attest-build-provenance@v2` produces a Sigstore bundle (`dist/mapping-ledger.sigstore.bundle.json`) that binds the merkle root to the specific commit, workflow ref, and run id that produced the release. Downstream consumers verify a release with `gh attestation verify mapping-ledger.json --owner fenre --bundle mapping-ledger.sigstore.bundle.json` followed by `python3 scripts/audit_mapping_ledger.py --require-signature --verify-signature`. The full verification protocol, operator runbooks, and the scope of what the ledger does and does not prove are in [`docs/signed-provenance.md`](docs/signed-provenance.md).

The ledger does not replace any of the review gates above: it is the audit trail that makes their outcomes tamper-evident. A failed `gh attestation verify` is a material fact that any downstream consumer should treat as provenance compromise.

## 6. Signing and provenance

Generated artefacts under `api/v1/`, `data/crosswalks/`, and `dist/` are SHA-256-hashed at build time. Release tags are signed (GPG or Sigstore). The provenance ledger at `provenance.json` records every release. The signed compliance-mapping ledger (§5e) provides a separate, clause-level audit trail for every regulatory claim the catalogue makes.

## 7. Contact

Security issues: see [`SECURITY.md`](SECURITY.md).
Governance questions: see [`GOVERNANCE.md`](GOVERNANCE.md).
Legal concerns about the licence, attribution, or redistribution of any content in this repository: file an issue tagged `legal`.
