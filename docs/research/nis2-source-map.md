# NIS2 authoritative source map

> This note supports Splunk monitoring and evidence design. It is not legal advice.

## Source hierarchy

1. **binding-law** — Official EU law published by EUR-Lex
2. **official-guidance** — ENISA and European Commission implementation guidance
3. **national-guidance** — Member-state competent-authority guidance and draft measures
4. **industry-interpretation** — Vendor or practitioner commentary used only for engineering patterns

## Sources

### Directive (EU) 2022/2555 (NIS2)

- URL: https://eur-lex.europa.eu/eli/dir/2022/2555/oj
- Type: `binding-law`
- Binding status: `binding-directive-transposed-through-national-law`
- Retrieved: 2026-04-29
- Use in this implementation: Primary source for scope, governance, risk-management measures, incident reporting, registration, supervision, enforcement, and Annex I/II sectors.

### Commission Implementing Regulation (EU) 2024/2690

- URL: https://eur-lex.europa.eu/eli/reg_impl/2024/2690/oj
- Type: `binding-law`
- Binding status: `binding-implementing-act-for-specified-digital-entity-types`
- Retrieved: 2026-04-29
- Use in this implementation: Concrete technical and methodological domains behind NIS2 Article 21 for relevant entity classes.

### ENISA NIS2 Technical Implementation Guidance

- URL: https://www.enisa.europa.eu/publications/nis2-technical-implementation-guidance
- Type: `official-guidance`
- Binding status: `advisory-guidance`
- Retrieved: 2026-04-29
- Use in this implementation: Evidence examples, implementation practices, and standard mappings used for assurance calibration.

### ENISA NIS2 policy and implementation hub

- URL: https://www.enisa.europa.eu/topics/cybersecurity-policy/nis-directive-new
- Type: `official-guidance`
- Binding status: `advisory-guidance`
- Retrieved: 2026-04-29
- Use in this implementation: Update-watch source for new guidance, Cooperation Group outputs, and implementation material.

### Ireland NCSC draft NIS2 risk-management-measures guidance

- URL: https://www.ncsc.gov.ie/pdfs/NIS2_Risk_Management_Measures_Guidance.pdf
- Type: `national-guidance`
- Binding status: `national-draft-guidance`
- Retrieved: 2026-04-29
- Use in this implementation: Practical national interpretation signal for RMM-style evidence, used only where consistent with official EU sources.

## Key NIS2 use cases sourced from these authorities

- UC-22.2.1 — NIS2 Art.23(4)(a): 24-Hour Early-Warning Notification Readiness
- UC-22.2.2 — NIS2 Art.21(2)(a): Risk Analysis Policy Evidence
- UC-22.2.3 — NIS2 Art.21(2)(b): Incident Handling Workflow Compliance

Related documentation: [NIS2 Monitoring Methodology](../nis2-monitoring-methodology.md), [Evidence Pack — NIS2](../evidence-packs/nis2.md).

