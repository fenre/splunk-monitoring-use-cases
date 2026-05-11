# Auditor discovery findings — template

> **Status:** Phase 0.1 template, produced 2026-04-16.
> **Purpose:** the skeleton that `docs/auditor-research/findings.md` will
> follow. Before the first interview, copy this file to
> `findings.md` and populate as data arrives. Keep this template file
> unchanged so future research cycles can re-use it.
> **Hard rules:** no respondent-level traceability. Every sentence in the
> published findings must be supportable either by an aggregated count, a
> consented anonymised quote, or a count + quote pair.

---

## 1. Executive summary *(to populate)*

*2–4 sentences, written last. Reader is the Phase 1 schema designer.
Answer: does the draft UC schema (`schemas/uc.schema.json`) land with
the auditors we spoke to? Where does it need to change?*

---

## 2. Sample description

| Metric | Target (Phase 0.1 floor) | Actual |
|---|---|---|
| Interviews completed | ≥ 6 | _ |
| Distinct interview personas | ≥ 3 | _ |
| Survey responses | ≥ 40 | _ |
| Distinct survey personas | ≥ 3 | _ |
| Frameworks covered (interview) | list | _ |
| Frameworks covered (survey) | list | _ |
| Geographies represented | list (EU / UK / US / APAC / other) | _ |
| Fieldwork window | start date — end date | _ |

**Limitations.** *(populate honestly — e.g. "skewed toward EU-based DPOs,
under-representation of APAC").*

---

## 3. Interview findings

Grouped by the interview guide sections. For every finding in this
section, cite: *"N=X interviews (P personas)"* and, where possible, one
anonymised quote.

### 3.1 Evidence-pack reality *(interview §2)*

* Most common format actually received by auditors.
* Most common rejection reason.
* Machine-generated vs manually-assembled evidence: trend and opinion.
* Disqualifying formats (union of the "hard no" answers).
* Timestamp / timezone expectations.

### 3.2 Framework-specific findings *(interview §3)*

#### 3.2.1 SOC-2 (TSC 2017)
#### 3.2.2 PCI-DSS v4.x
#### 3.2.3 GDPR / UK-GDPR
#### 3.2.4 HIPAA Security Rule
#### 3.2.5 ISO/IEC 27001:2022
#### 3.2.6 SOX / PCAOB AS 2201 ITGCs
#### 3.2.7 NIS2 / DORA

For each framework include:

1. What counts as good evidence.
2. What's most commonly under-evidenced.
3. Language preferences (e.g. "satisfies" vs "detects violation of").
4. Any clause-level insight that should be added to
   `data/regulations.draft.json`.

### 3.3 Catalogue value test *(interview §4)*

* Does the current `UC-22.35.1` exemplar make sense to auditors?
* Assurance vocabulary: `full | partial | contributing` —
  accept / reject / rename?
* Mode vocabulary: `satisfies | detects-violation-of` —
  accept / reject / rename?
* Ordering of the ideal evidence pack (most → least useful).
* Missing UC-schema fields. *(This is the most important bucket —
  it directly drives Phase 1.1 schema edits.)*

---

## 4. Survey results

Export the CSV from the survey host (with IPs discarded), run the
synthesis script and paste aggregated outputs here. No raw responses.

### 4.1 Section A — respondent profile
* Role distribution.
* Frameworks touched.
* Audit volume.
* Deployment environment.

### 4.2 Section B — evidence-pack structure
* Minimum expected artefacts (top 5).
* Single most important artefact.
* Evidence-pack format rank.
* Acceptable timestamp formats.
* Attitude to SIEM-generated evidence.
* Importance of tamper-evidence (1-5 distribution).

### 4.3 Section C — control mapping language
* "satisfies" rating distribution.
* "detects violations of" rating distribution.
* Preferred wording for partial coverage.
* Preferred display for multi-clause mappings.

### 4.4 Section D — catalogue-specific
* Awareness of the catalogue.
* Usefulness rating distribution.
* Trust drivers (top 3 per persona).
* "Don't want to see" free-text themes.

### 4.5 Section E — free text
* Themes in E1 ("wish evidence packs contained…").

---

## 5. Triangulation — interview vs. survey

Where do interviews and surveys agree? Where do they diverge? This
section protects us from a one-source confirmation bias.

---

## 6. Implications for Phase 1

Each implication must point to a specific artefact we will change.

### 6.1 `schemas/uc.schema.json` changes *(highest priority)*
- Field additions.
- Field removals.
- Vocabulary changes.
- Validation-rule tightening.

### 6.2 `data/regulations.draft.json` changes
- Clauses to add.
- Clauses to prune.
- Naming / versioning standardisation.

### 6.3 Evidence-pack generator requirements
- Mandatory artefacts.
- Optional artefacts.
- Signing / timestamping requirements.
- Formats to produce.

### 6.4 Catalogue UX implications
- Display decisions (flat list, grouped, matrix).
- Filtering / faceting requirements.
- Exports.

### 6.5 Governance & trust
- What we commit to ship alongside findings (e.g. signed releases,
  reviewer attributions, provenance stamps).

---

## 7. Consented anonymised quotes

Quotes re-usable under respondent consent (see `interview-guide.md` §5).
Every quote is tagged with:

* `persona` — e.g. `QSA`, `SOC-2-practitioner`.
* `framework` — e.g. `PCI-DSS v4.0`.
* Opaque identifier (e.g. `R-04`) — not linkable to any individual.

Quotes never include names, firms, clients, tools or geography details
beyond the persona tag.

---

## 8. Methodology note

* Interview guide version:
  `docs/auditor-research/interview-guide.md` at commit `<sha>`.
* Survey version:
  `docs/auditor-research/survey.md` at commit `<sha>`.
* Recruitment channels used (see `recruitment.md`).
* Synthesis method (single-pass thematic coding, populated rubric).
* Reviewer of findings before publication (role, not name).

---

## 9. Reproducibility & retention

* Raw artefacts retained for 12 months under access control.
* Aggregation scripts (if any) versioned in `scripts/`.
* Findings document published under the repository's existing licence.
* Previous-cycle findings archived at
  `docs/auditor-research/archive/findings-YYYY-MM-DD.md` before this
  file is overwritten.

---

<!-- BEGIN-AUTOGENERATED-SOURCES -->

## References

*Auto-generated by `scripts/generate_doc_references.py` from `data/source-references.json` and `data/source-mappings.json`. Edit those files (or the document body) to change citations; this footer is rewritten on every run.*

### Supporting sources

<a id="ref-1"></a>**[1]** European Parliament and Council of the European Union. (2022, December). *Directive (EU) 2022/2555 — NIS2 Directive on cybersecurity*. Official Journal of the European Union, L 333. ELI: dir/2022/2555. https://eur-lex.europa.eu/eli/dir/2022/2555/oj

<a id="ref-2"></a>**[2]** European Parliament and Council of the European Union. (2016, April). *Regulation (EU) 2016/679 — General Data Protection Regulation*. Official Journal of the European Union, L 119. ELI: reg/2016/679. https://eur-lex.europa.eu/eli/reg/2016/679/oj

<a id="ref-3"></a>**[3]** European Parliament and Council of the European Union. (2022, December). *Regulation (EU) 2022/2554 — Digital Operational Resilience Act (DORA)*. Official Journal of the European Union, L 333. ELI: reg/2022/2554. https://eur-lex.europa.eu/eli/reg/2022/2554/oj

<a id="ref-4"></a>**[4]** International Organization for Standardization. (2022). *ISO/IEC 27001:2022 — Information security, cybersecurity and privacy protection — Information security management systems — Requirements*. ISO/IEC. ISO/IEC 27001:2022. https://www.iso.org/standard/27001

<a id="ref-5"></a>**[5]** Public Company Accounting Oversight Board. (2007). *Auditing Standard 2201 — An Audit of Internal Control Over Financial Reporting*. PCAOB. PCAOB AS 2201. https://pcaobus.org/oversight/standards/auditing-standards/details/AS2201

<a id="ref-6"></a>**[6]** U.S. Congress. (2002). *Sarbanes-Oxley Act of 2002 — Public Company Accounting Reform and Investor Protection Act*. U.S. Government. Pub. L. 107–204. https://www.sec.gov/about/laws/soa2002.pdf

<a id="ref-7"></a>**[7]** U.S. Department of Health & Human Services. (2002). *HIPAA Privacy Rule (45 CFR Parts 160 and 164, Subparts A and E)*. Office for Civil Rights, HHS. 45 CFR 160, 164. https://www.hhs.gov/hipaa/for-professionals/privacy/index.html

<a id="ref-8"></a>**[8]** U.S. Department of Health & Human Services. (2013). *HIPAA Security Rule (45 CFR Parts 160 and 164, Subparts A and C)*. Office for Civil Rights, HHS. 45 CFR 160, 164. https://www.hhs.gov/hipaa/for-professionals/security/index.html

<!-- END-AUTOGENERATED-SOURCES -->
