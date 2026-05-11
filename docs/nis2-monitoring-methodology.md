# NIS2 Splunk monitoring methodology

This methodology defines the best practical Splunk-based NIS2 monitoring and evidence framework implemented in this repository. It is designed for engineering, security operations, GRC, and audit-readiness work. It does **not** certify legal compliance and does not replace counsel, national competent-authority guidance, or regulator decisions.

## Source hierarchy

1. EUR-Lex NIS2 Directive<sup class="ref">[<a href="#ref-1">1</a>]</sup> and Commission Implementing Regulation 2024/2690.
2. ENISA implementation guidance and European Commission material.
3. Member-state guidance and national transposition deltas.
4. Industry commentary only for engineering patterns, never as the first source for a compliance claim.

Machine-readable source metadata lives in `data/nis2-source-map.json`; the no-gap matrix lives in `data/per-regulation/nis2-coverage-expansion.json`.

## Coverage and assurance taxonomy

- `direct`: Splunk can directly produce operational evidence from events or workflow data.
- `partial`: Splunk proves a meaningful part of the obligation, but policy/process completion remains outside Splunk.
- `contributing`: Splunk provides context or supporting records, not the primary control.
- `not-monitorable`: the obligation is legal, state, authority, or regulator-side. Splunk tracks references, tasks, and evidence boundaries only.

No UC may claim `full` assurance unless the data source and SPL genuinely prove the whole monitorable obligation. Governance and legal-process items default to `partial` or `contributing` unless the workflow source of record is integrated.

## Evidence-first design

Every NIS2 row and UC must name a concrete evidence artifact: saved search, dashboard, lookup, alert history, SOAR run log, ITSM/GRC task, signed export, or evidence-pack section. Evidence should be retained in a restricted evidence repository or `index=audit_evidence`, with source hashes or signatures where available.

Operational evidence should prefer machine-verifiable records over screenshots: saved-search results, lookup snapshots, alert history, SOAR run logs, ITSM/GRC ticket history, signed exports, and immutable evidence-index records. Screenshots can support a review narrative, but they are not the primary evidence standard.

## Testability

High-value UCs include positive and negative control-test scenarios and fixture references under `sample-data/`. The no-gap audit is `python3 scripts/audit_nis2_no_gap.py` and fails when matrix rows or NIS2 UC compliance entries lose source traceability, evidence artifacts, owners, assurance rationale, or official source URLs.

Self-validation evidence is tracked in `docs/nis2-self-validation.md`. The deep coverage overview is exposed inside the canonical compliance story page at `compliance-story.html?reg=nis2` (rendered from `api/v1/compliance/story/nis2.json`); it summarises source coverage, assurance limits, review confidence, control-family rollups, and legal-boundary rows for the repository compliance section.

## Privacy and minimisation

HR, training, access, customer notification, incident, supplier, and background-check evidence can contain personal data. Ingest only fields needed to prove the control; prefer lookup keys, salted identifiers, retention class, status, and timestamp fields over unnecessary free text. Use Splunk Edge Processor or ingest-time transforms where redaction is required.

## Maintenance process

Review this model quarterly and after: new Commission implementing acts, ENISA guidance updates, national transposition changes, material Splunk product changes, major incidents, or external audit findings. Update `data/nis2-source-map.json`, the matrix, affected UCs, generated evidence packs, compliance reports, and web story payloads together.

## No-overclaiming policy

This repository may describe the result as a best-in-class Splunk-based NIS2 monitoring and evidence framework. It must not say that Splunk or this catalogue guarantees legal compliance, certification, regulator acceptance, or national-law applicability. Rows that require legal or competent-authority interpretation must keep `reviewConfidence=requires-legal-review` and an explicit Splunk boundary statement.

## Reviewer workflow

1. Start with `data/nis2-source-map.json` and `docs/research/nis2-source-map.md` to verify the authority hierarchy and retrieval dates.
2. Review `data/per-regulation/nis2-coverage-expansion.json` for every obligation, coverage type, assurance target, owner, evidence artifact, and legal boundary.
3. Open `compliance-story.html?reg=nis2` (or fetch `api/v1/compliance/story/nis2.json`) to inspect repository UC coverage, matrix summaries, source-authority rollups, and legal-boundary rows in the same surface used for every other regulation.
4. Use `sample-data/uc-22.2.*-fixture.json` with the control-test scenarios in each UC to validate representative positive and negative outcomes.
5. Re-run the validation commands in `docs/nis2-self-validation.md` after any matrix, UC, generator, or source-map change.

## Key NIS2 use cases in this catalog

The following use cases implement the core NIS2 monitoring obligations covered by this methodology:

- UC-22.2.1 — NIS2 Art.23(4)(a): 24-Hour Early-Warning Notification Readiness
- UC-22.2.2 — NIS2 Art.21(2)(a): Risk Analysis Policy Evidence
- UC-22.2.3 — NIS2 Art.21(2)(b): Incident Handling Workflow Compliance

See also the [Evidence Pack — NIS2](evidence-packs/nis2.md), the [NIS2 Maturity Benchmark](nis2-maturity-benchmark.md), and the [Compliance & Business Analytics Domain Guide](guides/compliance-business.md) for broader regulatory context.

---

<!-- BEGIN-AUTOGENERATED-SOURCES -->

## References

*Auto-generated by `scripts/generate_doc_references.py` from `data/source-references.json` and `data/source-mappings.json`. Edit those files (or the document body) to change citations; this footer is rewritten on every run.*

### Primary sources

<a id="ref-1"></a>**[1]** European Parliament and Council of the European Union. (2022, December). *Directive (EU) 2022/2555 — NIS2 Directive on cybersecurity*. Official Journal of the European Union, L 333. ELI: dir/2022/2555. https://eur-lex.europa.eu/eli/dir/2022/2555/oj

### Supporting sources

<a id="ref-2"></a>**[2]** International Electrotechnical Commission. (2018). *IEC 62443 — Industrial communication networks — Network and system security*. IEC. https://webstore.iec.ch/en/publication/7029

<a id="ref-3"></a>**[3]** International Organization for Standardization. (2022). *ISO/IEC 27001:2022 — Information security, cybersecurity and privacy protection — Information security management systems — Requirements*. ISO/IEC. ISO/IEC 27001:2022. https://www.iso.org/standard/27001

<a id="ref-4"></a>**[4]** MITRE Corporation. (2026). *MITRE ATT&CK Knowledge Base*. MITRE Engenuity. https://attack.mitre.org/

<a id="ref-5"></a>**[5]** National Institute of Standards and Technology. (2024). *Cybersecurity Framework (CSF) 2.0* (2.0). U.S. Department of Commerce. NIST CSWP 29. https://www.nist.gov/cyberframework

<a id="ref-6"></a>**[6]** Splunk Inc. (2026). *Search Reference: SPL Commands and Functions*. Splunk LLC, a Cisco company. Retrieved May 11, 2026, from https://docs.splunk.com/Documentation/Splunk/latest/SearchReference/WhatsInThisManual

<a id="ref-7"></a>**[7]** Splunk Inc. (2026). *Splunk Enterprise Security Administration Manual*. Splunk LLC, a Cisco company. Retrieved May 11, 2026, from https://docs.splunk.com/Documentation/ES

<a id="ref-8"></a>**[8]** Splunk Inc. (2026). *Splunk IT Service Intelligence Administration Manual*. Splunk LLC, a Cisco company. Retrieved May 11, 2026, from https://docs.splunk.com/Documentation/ITSI

### Related repository documents

- [`docs/evidence-packs/nis2.md`](evidence-packs/nis2.md)
- [`docs/guides/compliance-business.md`](guides/compliance-business.md)
- [`docs/nis2-maturity-benchmark.md`](nis2-maturity-benchmark.md)

### Cited by

- [`docs/nis2-external-review-pack.md`](nis2-external-review-pack.md)
- [`docs/nis2-maturity-benchmark.md`](nis2-maturity-benchmark.md)
- [`docs/nis2-self-validation.md`](nis2-self-validation.md)
- [`docs/research/nis2-source-map.md`](research/nis2-source-map.md)

<!-- END-AUTOGENERATED-SOURCES -->
