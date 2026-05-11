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

- [ ] Ran `make build` locally and committed regenerated artefacts as required by CI
      (the freshness check in `.github/workflows/validate.yml` verifies
      `provenance.json`, `provenance.js`, `docs/provenance-coverage.md`,
      `scorecard.json`, `docs/scorecard.md`; the legacy root-level
      `catalog.json`, `data.js`, `llms*.txt`, `sitemap.xml` were retired
      in v8.2.0 and are now build-only outputs under `dist/`).
- [ ] Ran `make audit-structure` (or `python3 -m splunk_uc audit-uc-structure --full`).
- [ ] SPL examples have been eyeballed for syntax errors.
- [ ] If adding a new **Splunkbase app reference**, the `Splunkbase #NNNN`
      ID is correct (verified on splunkbase.splunk.com).
- [ ] If adding a new **MITRE ATT&CK** mapping, the technique ID is valid.
- [ ] If adding a new category or subcategory, updated `non-technical-view.js`
      (per `.cursor/rules/non-technical-sync.mdc`).
- [ ] If adding or renaming a doc under `docs/`, or adding a UC that exemplifies
      an existing doc, updated `docs-uc-map.js`
      (per `.cursor/rules/docs-uc-map-sync.mdc`).
- [ ] If bumping the version, `VERSION`, `CHANGELOG.md` and the release-notes
      block in `index.html` all agree (per `.cursor/rules/versioning.mdc`).

## Phase 4.5 QA gate — peer review checklist

<!--
Every PR that touches compliance content (cat-22, schemas/uc.schema.json,
data/regulations.json, docs/regulatory-primer.md, docs/evidence-packs/**,
tests/golden/compliance-mappings.yaml, or any UC sidecar under
`content/cat-*/UC-*.json`) MUST be peer-reviewed against this checklist
and recorded in `data/provenance/peer-review-signoffs.json` before merge.
Non-compliance PRs may delete this section.
Detailed rubric: `docs/peer-review-guide.md`.
-->

- [ ] **Reviewer identity** — a second engineer (not the author) has reviewed
      every added or changed UC sidecar, clause mapping, and narrative copy.
- [ ] **Clause precision** — every `compliance[].clause` value is a real
      clause that exists in `data/regulations.json` for the cited version;
      the rationale explains how the SPL satisfies or detects-violation-of
      that specific clause (no "covers GDPR<sup class="ref">[<a href="#ref-2">2</a>]</sup>" hand-wave).
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
Tier-1 regulation content (GDPR, UK GDPR<sup class="ref">[<a href="#ref-8">8</a>]</sup>, PCI-DSS, HIPAA<sup class="ref">[<a href="#ref-7">7</a>]</sup>, SOX<sup class="ref">[<a href="#ref-5">5</a>]</sup>/ITGC,
SOC 2, ISO 27001, NIST CSF, NIST 800-53, NIS2<sup class="ref">[<a href="#ref-1">1</a>]</sup>, DORA<sup class="ref">[<a href="#ref-3">3</a>]</sup>, CMMC) and every
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
      by `python -m splunk_uc audit-sme-review-signoffs`.

## Screenshots / SPL excerpts

<!-- Paste renderings, before/after SPL, or dashboard screenshots if the
     change is visual. -->

## Related issues

<!-- "Fixes #NNN", "Refs #NNN", "Closes #NNN", or "None". -->

---

<!-- BEGIN-AUTOGENERATED-SOURCES -->

## References

*Auto-generated by `scripts/generate_doc_references.py` from `data/source-references.json` and `data/source-mappings.json`. Edit those files (or the document body) to change citations; this footer is rewritten on every run.*

### Supporting sources

<a id="ref-1"></a>**[1]** European Parliament and Council of the European Union. (2022, December). *Directive (EU) 2022/2555 — NIS2 Directive on cybersecurity*. Official Journal of the European Union, L 333. ELI: dir/2022/2555. https://eur-lex.europa.eu/eli/dir/2022/2555/oj

<a id="ref-2"></a>**[2]** European Parliament and Council of the European Union. (2016, April). *Regulation (EU) 2016/679 — General Data Protection Regulation*. Official Journal of the European Union, L 119. ELI: reg/2016/679. https://eur-lex.europa.eu/eli/reg/2016/679/oj

<a id="ref-3"></a>**[3]** European Parliament and Council of the European Union. (2022, December). *Regulation (EU) 2022/2554 — Digital Operational Resilience Act (DORA)*. Official Journal of the European Union, L 333. ELI: reg/2022/2554. https://eur-lex.europa.eu/eli/reg/2022/2554/oj

<a id="ref-4"></a>**[4]** Public Company Accounting Oversight Board. (2007). *Auditing Standard 2201 — An Audit of Internal Control Over Financial Reporting*. PCAOB. PCAOB AS 2201. https://pcaobus.org/oversight/standards/auditing-standards/details/AS2201

<a id="ref-5"></a>**[5]** U.S. Congress. (2002). *Sarbanes-Oxley Act of 2002 — Public Company Accounting Reform and Investor Protection Act*. U.S. Government. Pub. L. 107–204. https://www.sec.gov/about/laws/soa2002.pdf

<a id="ref-6"></a>**[6]** U.S. Department of Health & Human Services. (2002). *HIPAA Privacy Rule (45 CFR Parts 160 and 164, Subparts A and E)*. Office for Civil Rights, HHS. 45 CFR 160, 164. https://www.hhs.gov/hipaa/for-professionals/privacy/index.html

<a id="ref-7"></a>**[7]** U.S. Department of Health & Human Services. (2013). *HIPAA Security Rule (45 CFR Parts 160 and 164, Subparts A and C)*. Office for Civil Rights, HHS. 45 CFR 160, 164. https://www.hhs.gov/hipaa/for-professionals/security/index.html

<a id="ref-8"></a>**[8]** United Kingdom Parliament. (2018). *Data Protection Act 2018 (UK GDPR, retained EU law)*. The Stationery Office. 2018 c. 12. https://www.legislation.gov.uk/ukpga/2018/12/contents

<!-- END-AUTOGENERATED-SOURCES -->
