# Evidence Packs

> Auditor-ready evidence packs for the 12 highest-priority regulations tracked by this catalogue. Each pack bundles clause-level coverage, evidence-collection guidance, retention expectations, role matrices, authoritative sources, and common audit deficiencies. Machine-readable twins live under [`api/v1/evidence-packs/`](../../api/v1/evidence-packs/) for integration into GRC tools and audit-request pipelines.

## How to use these packs

1. **Regulators and external auditors**: start with the pack for the regulation under review; the coverage table in section 4 identifies the UCs that evidence each clause and the assurance level each one provides.
2. **Compliance and privacy officers**: use section 11 (gaps) to drive the remediation backlog and section 12 (auditor questions) to pre-test readiness.
3. **Internal audit**: use section 6 (testing procedures) and section 7 (roles) to build walk-through and control-test scripts.
4. **Executives and boards**: section 3 (coverage at a glance) gives a one-screen summary; section 10 (enforcement) provides the penalty context for risk-appetite discussions.

## Pack catalogue

| Regulation | Tier | Jurisdiction | Version | Coverage | Priority-weighted | Pack |
|---|---|---|---|---|---|---|
| **GDPR<sup class="ref">[<a href="#ref-3">3</a>]</sup>** | Tier 1 | EU, EEA | `2016/679` | 100.0% | 100.0% | [`gdpr.md`](gdpr.md) |
| **UK GDPR<sup class="ref">[<a href="#ref-15">15</a>]</sup>** | Tier 2 | UK | `post-Brexit` | 75.0% | 76.3% | [`uk-gdpr.md`](uk-gdpr.md) |
| **PCI DSS** | Tier 1 | GLOBAL | `v4.0` | 100.0% | 100.0% | [`pci-dss.md`](pci-dss.md) |
| **HIPAA<sup class="ref">[<a href="#ref-14">14</a>]</sup> Security** | Tier 1 | US | `2013-final` | 100.0% | 100.0% | [`hipaa-security.md`](hipaa-security.md) |
| **SOX<sup class="ref">[<a href="#ref-11">11</a>]</sup> ITGC** | Tier 1 | US | `PCAOB AS 2201` | 100.0% | 100.0% | [`sox-itgc.md`](sox-itgc.md) |
| **SOC 2<sup class="ref">[<a href="#ref-1">1</a>]</sup>** | Tier 1 | US, GLOBAL | `2017 TSC` | 100.0% | 100.0% | [`soc-2.md`](soc-2.md) |
| **ISO 27001<sup class="ref">[<a href="#ref-5">5</a>]</sup>** | Tier 1 | GLOBAL | `2022` | 100.0% | 100.0% | [`iso-27001.md`](iso-27001.md) |
| **NIST CSF<sup class="ref">[<a href="#ref-6">6</a>]</sup>** | Tier 1 | US, GLOBAL | `2.0` | 100.0% | 100.0% | [`nist-csf.md`](nist-csf.md) |
| **NIST 800-53<sup class="ref">[<a href="#ref-7">7</a>]</sup>** | Tier 1 | US | `Rev. 5` | 100.0% | 100.0% | [`nist-800-53.md`](nist-800-53.md) |
| **NIS2<sup class="ref">[<a href="#ref-2">2</a>]</sup>** | Tier 1 | EU | `Directive (EU) 2022/2555` | 100.0% | 100.0% | [`nis2.md`](nis2.md) |
| **DORA<sup class="ref">[<a href="#ref-4">4</a>]</sup>** | Tier 1 | EU | `Regulation (EU) 2022/2554` | 100.0% | 100.0% | [`dora.md`](dora.md) |
| **CMMC<sup class="ref">[<a href="#ref-12">12</a>]</sup>** | Tier 1 | US | `2.0` | 100.0% | 100.0% | [`cmmc.md`](cmmc.md) |

## Structure of an evidence pack

Every pack follows the same section layout so that an auditor or compliance officer opening any pack finds the same information in the same place:

1. **Purpose** — plain-language regulation summary.
2. **Scope** — who must comply and where.
3. **Catalogue coverage at a glance** — single-row summary of clause count, covered count, priority-weighted coverage, contributing UC count.
4. **Clause-by-clause coverage** — one table row per clause, with priority weight, assurance level, and contributing UC IDs.
5. **Evidence collection** — common sources, retention table with legal citations, evidence-integrity baseline.
6. **Control testing procedures** — how regulators typically test this regulation, plus reporting cadence.
7. **Roles and responsibilities** — role matrix.
8. **Authoritative guidance** — links to official regulator, certification-body, or standards-body sources.
9. **Common audit deficiencies** — typical findings for pre-testing.
10. **Enforcement and penalties** — monetary, operational, and reputational consequences.
11. **Pack gaps and remediation backlog** — clauses not yet covered by the catalogue, ranked by priority.
12. **Questions an auditor should ask** — ready-made question list for preparers.
13. **Machine-readable twin** — link to the JSON pack and related API surfaces.
14. **Provenance and regeneration** — inputs, generation metadata, regeneration commands.

## Regeneration

The packs are generated deterministically from [`data/regulations.json`](../../data/regulations.json), [`data/evidence-pack-extras.json`](../../data/evidence-pack-extras.json), the UC sidecars under [`content/cat-*/`](../../content), and the pre-computed coverage metrics under [`api/v1/compliance/regulations/`](../../api/v1/compliance/regulations/).

```bash
# Regenerate all packs (writes docs/evidence-packs/*.md
# and api/v1/evidence-packs/*.json)
python3 scripts/generate_evidence_packs.py

# Verify no drift (for CI and local guard-rails)
python3 scripts/generate_evidence_packs.py --check
```

Last regenerated against catalogue version `8.2.0`.

## Related documentation

- [`docs/regulatory-primer.md`](../regulatory-primer.md) — plain-language primer covering 15 cross-cutting families and 12 tier-1 regulations.
- [`docs/coverage-methodology.md`](../coverage-methodology.md) — how clause coverage, priority-weighted coverage, and assurance-adjusted coverage are computed.
- [`docs/compliance-coverage.md`](../compliance-coverage.md) — global coverage summary across all regulations.
- [`docs/compliance-gaps.md`](../compliance-gaps.md) — auto-generated gap report across all tracked regulations.
- [`api/README.md`](../../api/README.md) — API surface quick start and endpoint catalogue.
- [`CHANGELOG.md`](../../CHANGELOG.md) — release history, including the Phase 4.2 evidence-pack roll-out.

---

<!-- BEGIN-AUTOGENERATED-SOURCES -->

## References

*Auto-generated by `scripts/generate_doc_references.py` from `data/source-references.json` and `data/source-mappings.json`. Edit those files (or the document body) to change citations; this footer is rewritten on every run.*

### Supporting sources

<a id="ref-1"></a>**[1]** American Institute of Certified Public Accountants. (2017). *Trust Services Criteria (2017) for Security, Availability, Processing Integrity, Confidentiality, and Privacy*. AICPA & CIMA. SOC 2 / TSP Section 100. https://www.aicpa-cima.com/topic/audit-assurance/soc-suite-of-services

<a id="ref-2"></a>**[2]** European Parliament and Council of the European Union. (2022, December). *Directive (EU) 2022/2555 — NIS2 Directive on cybersecurity*. Official Journal of the European Union, L 333. ELI: dir/2022/2555. https://eur-lex.europa.eu/eli/dir/2022/2555/oj

<a id="ref-3"></a>**[3]** European Parliament and Council of the European Union. (2016, April). *Regulation (EU) 2016/679 — General Data Protection Regulation*. Official Journal of the European Union, L 119. ELI: reg/2016/679. https://eur-lex.europa.eu/eli/reg/2016/679/oj

<a id="ref-4"></a>**[4]** European Parliament and Council of the European Union. (2022, December). *Regulation (EU) 2022/2554 — Digital Operational Resilience Act (DORA)*. Official Journal of the European Union, L 333. ELI: reg/2022/2554. https://eur-lex.europa.eu/eli/reg/2022/2554/oj

<a id="ref-5"></a>**[5]** International Organization for Standardization. (2022). *ISO/IEC 27001:2022 — Information security, cybersecurity and privacy protection — Information security management systems — Requirements*. ISO/IEC. ISO/IEC 27001:2022. https://www.iso.org/standard/27001

<a id="ref-6"></a>**[6]** National Institute of Standards and Technology. (2024). *Cybersecurity Framework (CSF) 2.0* (2.0). U.S. Department of Commerce. NIST CSWP 29. https://www.nist.gov/cyberframework

<a id="ref-7"></a>**[7]** National Institute of Standards and Technology. (2020). *Security and Privacy Controls for Information Systems and Organizations* (Revision 5). U.S. Department of Commerce. NIST SP 800-53 Rev. 5. https://csrc.nist.gov/pubs/sp/800/53/r5/upd1/final

<a id="ref-8"></a>**[8]** Payment Card Industry Security Standards Council. (2018). *Payment Card Industry Data Security Standard v3.2.1* (v3.2.1). PCI SSC. https://www.pcisecuritystandards.org/document_library/?category=pcidss

<a id="ref-9"></a>**[9]** Payment Card Industry Security Standards Council. (2022). *Payment Card Industry Data Security Standard v4.0* (v4.0). PCI SSC. https://www.pcisecuritystandards.org/document_library/?category=pcidss

<a id="ref-10"></a>**[10]** Public Company Accounting Oversight Board. (2007). *Auditing Standard 2201 — An Audit of Internal Control Over Financial Reporting*. PCAOB. PCAOB AS 2201. https://pcaobus.org/oversight/standards/auditing-standards/details/AS2201

<a id="ref-11"></a>**[11]** U.S. Congress. (2002). *Sarbanes-Oxley Act of 2002 — Public Company Accounting Reform and Investor Protection Act*. U.S. Government. Pub. L. 107–204. https://www.sec.gov/about/laws/soa2002.pdf

<a id="ref-12"></a>**[12]** U.S. Department of Defense. (2024). *Cybersecurity Maturity Model Certification (CMMC) 2.0* (2.0). Office of the Under Secretary of Defense for Acquisition and Sustainment. https://dodcio.defense.gov/CMMC/

<a id="ref-13"></a>**[13]** U.S. Department of Health & Human Services. (2002). *HIPAA Privacy Rule (45 CFR Parts 160 and 164, Subparts A and E)*. Office for Civil Rights, HHS. 45 CFR 160, 164. https://www.hhs.gov/hipaa/for-professionals/privacy/index.html

<a id="ref-14"></a>**[14]** U.S. Department of Health & Human Services. (2013). *HIPAA Security Rule (45 CFR Parts 160 and 164, Subparts A and C)*. Office for Civil Rights, HHS. 45 CFR 160, 164. https://www.hhs.gov/hipaa/for-professionals/security/index.html

<a id="ref-15"></a>**[15]** United Kingdom Parliament. (2018). *Data Protection Act 2018 (UK GDPR, retained EU law)*. The Stationery Office. 2018 c. 12. https://www.legislation.gov.uk/ukpga/2018/12/contents

### Cited by

- [`docs/regulatory-primer.md`](../regulatory-primer.md)
- [`docs/sme-review-guide.md`](../sme-review-guide.md)

<!-- END-AUTOGENERATED-SOURCES -->
