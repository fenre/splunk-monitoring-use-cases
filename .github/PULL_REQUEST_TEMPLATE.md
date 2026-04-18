<!--
Thanks for contributing to splunk-monitoring-use-cases!

Please fill in the sections below. Delete anything that doesn't apply.
-->

## Summary

<!-- One or two sentences describing what this PR changes and why. -->

## Type of change

<!-- Tick one or more. -->

- [ ] New use case(s) added
- [ ] Existing use case(s) improved (SPL, fields, KFP, references, MITRE, …)
- [ ] Build pipeline / script change
- [ ] Dashboard (UI / UX) change
- [ ] Splunkbase content pack (TA / ITSI / ES) change
- [ ] Documentation-only change
- [ ] Governance / process change
- [ ] Bug fix

## Affected use cases / categories

<!-- List UC IDs, subcategory ranges, or category numbers touched. -->

## Validation

<!-- Confirm the things that automated CI cannot. -->

- [ ] Ran `python3 build.py` locally and committed all regenerated artefacts
      (`data.js`, `catalog.json`, `llms.txt`, `llms-full.txt`, `sitemap.xml`,
      `api/*.json`).
- [ ] Ran `python3 validate_md.py` (or `python3 scripts/audit_uc_structure.py --full`).
- [ ] SPL examples have been eyeballed for syntax errors.
- [ ] If adding a new **Splunkbase app reference**, the `Splunkbase #NNNN`
      ID is correct (verified on splunkbase.splunk.com).
- [ ] If adding a new **MITRE ATT&CK** mapping, the technique ID is valid.
- [ ] If adding a new category or subcategory, updated `non-technical-view.js`
      (per `.cursor/rules/non-technical-sync.mdc`).
- [ ] If bumping the version, `VERSION`, `CHANGELOG.md` and the release-notes
      block in `index.html` all agree (per `.cursor/rules/versioning.mdc`).

## Phase 4.5 QA gate — peer review checklist

<!--
Every PR that touches compliance content (cat-22, schemas/uc.schema.json,
data/regulations.json, docs/regulatory-primer.md, docs/evidence-packs/**,
tests/golden/compliance-mappings.yaml, or any UC sidecar under
use-cases/cat-*/uc-*.json) MUST be peer-reviewed against this checklist
and recorded in `data/provenance/peer-review-signoffs.json` before merge.
Non-compliance PRs may delete this section.
Detailed rubric: `docs/peer-review-guide.md`.
-->

- [ ] **Reviewer identity** — a second engineer (not the author) has reviewed
      every added or changed UC sidecar, clause mapping, and narrative copy.
- [ ] **Clause precision** — every `compliance[].clause` value is a real
      clause that exists in `data/regulations.json` for the cited version;
      the rationale explains how the SPL satisfies or detects-violation-of
      that specific clause (no "covers GDPR" hand-wave).
- [ ] **Assurance honesty** — `full` is reserved for UCs with a complete
      `controlTest` (positive + negative fixture + assertion); `partial`
      for UCs with SPL but no fixture; `contributing` for informational
      telemetry. No UC claims `full` without a matching fixture.
- [ ] **MITRE / OSCAL cross-refs** — new ATT&CK techniques resolve in
      `vendor/attack/enterprise-attack.json`; new OSCAL catalog IDs resolve
      in `vendor/oscal/*`; every crosswalk is symmetric (if UC cites
      technique X, the D3FEND / ATT&CK index in `api/v1/mitre/` lists
      the UC).
- [ ] **Provenance** — `provenance` field lists the authoritative source
      (Splunk Security Content commit SHA, vendor doc URL + retrieval date,
      or `author:hand-authored`). Unsourced content blocks merge.
- [ ] **Signoff recorded** — reviewer name/handle, date, commit SHA, and
      scope (UC IDs reviewed) appended to
      `data/provenance/peer-review-signoffs.json` and validated against
      `schemas/peer-review-signoff.schema.json`.

## Phase 4.5 QA gate — legal review (compliance content only)

<!--
Tier-1 regulation content (GDPR, UK GDPR, PCI-DSS, HIPAA, SOX/ITGC,
SOC 2, ISO 27001, NIST CSF, NIST 800-53, NIS2, DORA, CMMC) and every
evidence pack under `docs/evidence-packs/` MUST be flagged for legal
review. Legal counsel does not need to approve the SPL, only the
regulatory citations, primer summaries, and evidence-pack claims.
Detailed rubric: `docs/legal-review-guide.md`.
-->

- [ ] **Legal counsel flagged** — tier-1 regulatory content changes have
      been surfaced to the project's designated legal reviewer (see
      `docs/legal-review-guide.md` §1).
- [ ] **Citations verified** — every clause number, recital, article, or
      subpart cited in the primer / evidence pack has been cross-checked
      against the official publication version listed in
      `data/regulations.json.publicationUrl`.
- [ ] **Derivatives honest** — where UK GDPR / CCPA / nFADP / LGPD / APPI
      entries are derived from a parent regulation, the `derivationSource`
      field names the parent and the one-step assurance degradation
      applies (per `docs/coverage-methodology.md`). No UK GDPR entry
      claims a higher assurance than its GDPR parent.
- [ ] **Signoff recorded** — if a legal review was performed, the result
      is appended to `data/provenance/legal-review-signoffs.json`.

## Phase 5.2 QA gate — SME review (SPL + auditor-evidence content)

<!--
Use cases that claim `compliance[].assurance == "full"` against a
tier-1 regulation, or that ship SPL material to a hand-authored
Splunk app under `splunk-apps/`, MUST pass an SME review. The SME
validates (1) that the SPL actually detects what it claims on the
authoring data source, and (2) that an auditor for the cited
regulation would accept the Splunk output as evidence. Detailed
rubric: `docs/sme-review-guide.md`.
-->

- [ ] **SME identity recorded** — a qualified SME has been identified
      per their `reviewerRole` (`splunk-engineer`, `regulatory-auditor`,
      `security-architect`, `industry-sme`, or `internal-review-board`).
      Credentials noted where recognised (QSA, CIPP/E, Splunk Certified
      Consultant, etc.).
- [ ] **SPL correctness replayed** — the SME replayed the positive +
      negative `controlTest.fixtureRef` on a Splunk instance, and the
      result is recorded in `fixtureReplayResult` (or `replayed=false`
      is explained alongside `checks.splCorrectness='n/a'`).
- [ ] **Six-point rubric graded** — every `checks.*` entry is
      `pass`/`fail`/`n/a` (splCorrectness, dataSourceRealism,
      splunkCompat, evidenceCompleteness, regulationApplicability,
      falsePositiveAssessment). An `approved` outcome has no `fail`
      grades.
- [ ] **Dual-SME review where required** — content listed in
      `docs/sme-review-guide.md` \u00a75 (high-penalty tier-1 clauses,
      headline evidence-pack UCs, hand-authored Splunk-app additions)
      carries two independent signoff records on the same commit.
- [ ] **Caveats mirrored in UC sidecar** — where `outcome=='conditional'`,
      each `caveats[]` entry is copied into an `smeCaveat` field on the
      relevant `compliance[]` entry of the UC sidecar.
- [ ] **Signoff recorded** — if SME review was performed, the result
      is appended to `data/provenance/sme-signoffs.json` and validated
      by `scripts/audit_sme_review_signoffs.py`.

## Screenshots / SPL excerpts

<!-- Paste renderings, before/after SPL, or dashboard screenshots if the
     change is visual. -->

## Related issues

<!-- "Fixes #NNN", "Refs #NNN", "Closes #NNN", or "None". -->
