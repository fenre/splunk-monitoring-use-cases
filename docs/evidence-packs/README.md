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
| **GDPR** | Tier 1 | EU, EEA | `2016/679` | 100.0% | 100.0% | [`gdpr.md`](gdpr.md) |
| **UK GDPR** | Tier 2 | UK | `post-Brexit` | 100.0% | 100.0% | [`uk-gdpr.md`](uk-gdpr.md) |
| **PCI DSS** | Tier 1 | GLOBAL | `v4.0` | 100.0% | 100.0% | [`pci-dss.md`](pci-dss.md) |
| **HIPAA Security** | Tier 1 | US | `2013-final` | 100.0% | 100.0% | [`hipaa-security.md`](hipaa-security.md) |
| **SOX ITGC** | Tier 1 | US | `PCAOB AS 2201` | 100.0% | 100.0% | [`sox-itgc.md`](sox-itgc.md) |
| **SOC 2** | Tier 1 | US, GLOBAL | `2017 TSC` | 100.0% | 100.0% | [`soc-2.md`](soc-2.md) |
| **ISO 27001** | Tier 1 | GLOBAL | `2022` | 100.0% | 100.0% | [`iso-27001.md`](iso-27001.md) |
| **NIST CSF** | Tier 1 | US, GLOBAL | `2.0` | 100.0% | 100.0% | [`nist-csf.md`](nist-csf.md) |
| **NIST 800-53** | Tier 1 | US | `Rev. 5` | 100.0% | 100.0% | [`nist-800-53.md`](nist-800-53.md) |
| **NIS2** | Tier 1 | EU | `Directive (EU) 2022/2555` | 100.0% | 100.0% | [`nis2.md`](nis2.md) |
| **DORA** | Tier 1 | EU | `Regulation (EU) 2022/2554` | 100.0% | 100.0% | [`dora.md`](dora.md) |
| **CMMC** | Tier 1 | US | `2.0` | 100.0% | 100.0% | [`cmmc.md`](cmmc.md) |

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

The packs are generated deterministically from [`data/regulations.json`](../../data/regulations.json), [`data/evidence-pack-extras.json`](../../data/evidence-pack-extras.json), the UC sidecars under [`use-cases/cat-*/`](../../use-cases), and the pre-computed coverage metrics under [`api/v1/compliance/regulations/`](../../api/v1/compliance/regulations/).

```bash
# Regenerate all packs (writes docs/evidence-packs/*.md
# and api/v1/evidence-packs/*.json)
python3 scripts/generate_evidence_packs.py

# Verify no drift (for CI and local guard-rails)
python3 scripts/generate_evidence_packs.py --check
```

Last regenerated against catalogue version `7.1`.

## Related documentation

- [`docs/regulatory-primer.md`](../regulatory-primer.md) — plain-language primer covering 15 cross-cutting families and 12 tier-1 regulations.
- [`docs/coverage-methodology.md`](../coverage-methodology.md) — how clause coverage, priority-weighted coverage, and assurance-adjusted coverage are computed.
- [`docs/compliance-coverage.md`](../compliance-coverage.md) — global coverage summary across all regulations.
- [`docs/compliance-gaps.md`](../compliance-gaps.md) — auto-generated gap report across all tracked regulations.
- [`api/README.md`](../../api/README.md) — API surface quick start and endpoint catalogue.
- [`CHANGELOG.md`](../../CHANGELOG.md) — release history, including the Phase 4.2 evidence-pack roll-out.
