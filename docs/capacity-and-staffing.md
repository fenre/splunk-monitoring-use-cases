# Capacity and staffing

> **Audience.** Anyone reading [`ROADMAP.md`](../ROADMAP.md) trying to
> figure out why a particular item is "in scope this year" or "deferred",
> and any prospective contributor wondering what the catalogue actually
> commits to maintain.

## TL;DR

The roadmap was sized for a small, mostly-solo team: **1–2 platform engineers** (1.0 typical, 2.0 peak), **0.5 FTE curator**, plus as-needed tier-1 legal-review capacity.

| Role | FTE | What they do |
| --- | --- | --- |
| **Platform engineer** | 1–2 (peak), 1.0 typical | Build pipeline, audits, CI, scripts, frontend chrome, security gates, schema work. |
| **Curator** | 0.5 FTE | Gold-standard authoring, GE review, prereq-graph maintenance, regulatory primer upkeep, SME outreach. |
| **Tier-1 legal-reviewer** | as-needed (≈0.1 over the year) | Cat-22 evidence-pack review for tier-1 regulations (GDPR<sup class="ref">[<a href="#ref-2">2</a>]</sup>, HIPAA<sup class="ref">[<a href="#ref-7">7</a>]</sup>, PCI, SOX<sup class="ref">[<a href="#ref-5">5</a>]</sup>, NIS2<sup class="ref">[<a href="#ref-1">1</a>]</sup>, DORA<sup class="ref">[<a href="#ref-3">3</a>]</sup>, ISO 27001, NIST 800-53, NIST CSF, SOC 2, UK GDPR<sup class="ref">[<a href="#ref-8">8</a>]</sup>, CMMC). |

When standing capacity dips below that line, three calibrated **operating modes** scope the work down rather than letting the catalogue rot. They are paired with [`docs/rollback-playbook.md`](rollback-playbook.md) — capacity says which phases ship, the rollback playbook says how each merge unwinds.

## Operating modes

### Full mode

**Trigger.** The standing capacity above is available.

**In scope.**

- All P0–P19 phases on plan-of-record cadence.
- Quarterly minor releases.
- Tier-1 cat-22 regulations refreshed within 30 days of any amendment.
- Contributor PR median triage ≤ 10 business days.

### Reduced mode

**Trigger.** Any one of: a single active maintainer for ≥30 consecutive days; curator capacity ≤0.25 FTE over a 90-day window; CI green-rate on `main` <90% over 30 days.

**In scope.**

- P0–P4 phases (the SSOT and CI backbone).
- Security gates: CodeQL, Dependency Review, gitleaks, SBOM, Sigstore. Non-negotiable.
- Audit suite stays green (`make audit-full`).
- Cat-22 in current state — no regression, no new regulations.
- Bi-annual minor releases.

**Out of scope.**

- P5 frontend bundler ramp beyond what already ships.
- P9 monorepo restructure.
- P10 perf budgets enforcement (budgets land but stay advisory).
- P19 i18n.
- New cat-22 tier-1 regulations beyond the existing 12.

### Solo mode

**Trigger.** Any one of: a single maintainer with <0.5 FTE for ≥60 days; zero curator capacity for ≥90 days; an extended unavailability of the lead maintainer without a designated deputy.

**In scope.**

- Audit suite stays green. Period.
- Security gates remain enforced (CodeQL, dependency-review high-severity blocks, gitleaks).
- The catalogue compiles: `make build` succeeds on every push to `main`.
- Cat-22 evidence packs remain valid (no edits, but signatures and links stay unbroken).
- Yearly tag (vX.Y) with a "minimal release; capacity-constrained" note.

**Out of scope** (deferred):

- P5 frontend bundler / component library / data.js retire.
- P6 scripts taxonomy.
- P7 search-API edge layer.
- P8 metrics emission.
- **P9 monorepo restructure.**
- P10 perf budgets.
- P11 release polish beyond security baseline.
- P16 coverage burndown.
- P17 AI-readiness / LLM eval.
- P18 Splunk version compat matrix beyond what already ships.
- P19 i18n.
- New use cases — content additions paused; only content corrections accepted.

Solo mode preserves the SSOT (P0/P1/P2/P3/P4 plus the ADRs that constrain them). When capacity returns, deferred phases resume from a known-good base.

## Transitions

Mode transitions are explicit, not silent. The lead maintainer:

1. Opens an issue with the `capacity-mode` label naming the trigger, start date, and planned review date.
2. Updates the project status banner in `README.md`.
3. Adds a `CHANGELOG.md` "Unreleased" entry: `Operating mode: <mode> (<trigger>)`.

The transition stays in effect until the trigger resolves or a subsequent declaration changes the mode.

## Anti-patterns

- **Silently picking solo-mode scope while claiming full-mode cadence.** If capacity has shrunk, the project status banner and release notes must reflect it.
- **Letting security gates lapse to keep CI green.** Any PR that adds `continue-on-error: true` to a security workflow must cite the operating mode that authorises the relaxation.
- **Backlogging cat-22 tier-1 reviews.** Tier-1 evidence packs that go >12 months without legal-review must move to `assurance: contributing`. The catalogue should be honest about what it can defend.

## Links

- [`GOVERNANCE.md`](../GOVERNANCE.md) — roles and decision-making.
- [`docs/rollback-playbook.md`](rollback-playbook.md) — per-phase rollback contract.
- [`docs/external-consumer-matrix.md`](external-consumer-matrix.md) — the release contract every operating mode must preserve.
- ADRs that constrain operating-mode behaviour: [ADR-0007](adr/0007-json-as-source-of-truth.md), [ADR-0008](adr/0008-canonical-constants.md), [ADR-0009](adr/0009-generated-artefact-policy.md).

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

### Related repository documents

- [`docs/adr/0007-json-as-source-of-truth.md`](adr/0007-json-as-source-of-truth.md)
- [`docs/adr/0008-canonical-constants.md`](adr/0008-canonical-constants.md)
- [`docs/adr/0009-generated-artefact-policy.md`](adr/0009-generated-artefact-policy.md)

### Cited by

- [`docs/ci-architecture.md`](ci-architecture.md)

<!-- END-AUTOGENERATED-SOURCES -->
