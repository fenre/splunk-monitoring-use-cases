# Kraftberedskapsforskriften — Splunk monitoring methodology

This methodology defines the Splunk-based monitoring and evidence framework for **Norwegian Kraftberedskapsforskriften** (`no-kbf-nve`) in this repository. It supports engineering, SOC, GRC, and audit-readiness work for **KBO-enheter** (kraftforsyningens beredskapsorganisasjon). It does **not** certify legal compliance or replace NVE tilsyn, counsel, or the NVE digital veileder.

## Source hierarchy

1. [Kraftberedskapsforskriften on Lovdata](https://lovdata.no/dokument/SF/forskrift/2012-12-07-1157) and amendments (notably [SF/forskrift/2026-05-04-717](https://lovdata.no/dokument/SF/forskrift/2026-05-04-717) for §4-1).
2. [NVE digital veileder](https://veiledere.nve.no/kraftberedskapsforskriften/).
3. NVE høringsdokumenter and rapporter.
4. Industry OT/SIEM patterns only for engineering design — never as the first source for a compliance claim.

Machine-readable source metadata: `data/no-kbf-nve-source-map.json`.  
Coverage matrix: `data/per-regulation/no-kbf-nve-coverage-expansion.json`.

## Coverage taxonomy

| Type | Meaning |
|------|---------|
| `direct` | Splunk can directly produce operational evidence from integrated telemetry. |
| `partial` | Splunk proves a meaningful part; policy/process completion remains outside Splunk. |
| `contributing` | Splunk provides supporting context, not the primary control. |
| `not-monitorable` | Obligation is physical, legal, or organisational — tracked for scope only. |

No UC may claim `full` assurance unless the SPL and data sources genuinely prove the monitorable obligation. Governance items default to `partial` or `contributing`.

## Splunk evidence design

Every matrix row and UC must name a concrete evidence artifact: saved search, dashboard, lookup, alert history, SOAR run log, ITSM/GRC task, or `index=audit_evidence` export. Prefer machine-verifiable records over screenshots.

Operational searches for Norwegian KBO deployments should use **Europe/Oslo** time semantics for reporting cutoffs where applicable.

## Cross-framework strategy

Norwegian grid operators may also be subject to **NIS2** (national transposition), **IEC 62443**, and **NERC CIP** (for international benchmarking). This catalogue:

- Adds **dual `compliance[]` entries** on shared OT UCs (cat-14, cat-05) rather than duplicating SPL.
- Does **not** use `derivesFrom` automatic inheritance — KBF clause numbers and Norwegian terminology require explicit mapping.

Related Norwegian frameworks in subcategory 22.26: Sikkerhetsloven (`no-sikkerhetsloven`), Petroleumsforskriften, Personopplysningsloven.

## Privacy and minimisation

Access, HR, supplier, and incident evidence may contain personal data. Ingest only fields needed to prove the control; prefer lookup keys and status timestamps over free text.

## Maintenance

Review quarterly and after: NVE veileder updates, Lovdata amendments, material Splunk product changes, or external audit findings. Update the source map, matrix, affected UCs, evidence pack, and compliance reports together.

Run after matrix or UC changes:

```bash
make audit-regulation-alignment
make audit-compliance-mappings
make audit-compliance-gaps
make generate-evidence-packs
make generate-api-surface
```

## No-overclaiming policy

This repository may describe a best-in-class Splunk-based KBF monitoring and evidence framework. It must not state that Splunk or this catalogue guarantees NVE acceptance, legal compliance, or certification.
