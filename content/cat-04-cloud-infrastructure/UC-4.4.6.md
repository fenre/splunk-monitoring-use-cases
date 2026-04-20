---
id: "4.4.6"
title: "Multi-Cloud Security Posture (CSPM) Findings"
criticality: "high"
splunkPillar: "Security"
---

# UC-4.4.6 · Multi-Cloud Security Posture (CSPM) Findings

## Description

CSPM tools (or native Security Hub, Defender, SCC) produce findings across clouds. Centralizing in Splunk enables unified prioritization and remediation tracking.

## Value

CSPM tools (or native Security Hub, Defender, SCC) produce findings across clouds. Centralizing in Splunk enables unified prioritization and remediation tracking.

## Implementation

Ingest Security Hub, Defender for Cloud, and SCC findings into a common index. Normalize severity and finding type. Alert on new critical/high. Dashboard open findings by cloud, severity, and category (e.g. encryption, networking).

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: Splunk TAs for each cloud, or CSPM product integration (e.g. Prisma Cloud, Wiz).
• Ensure the following data sources are available: AWS Security Hub, Azure Defender/Security Center, GCP Security Command Center, or third-party CSPM API.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Ingest Security Hub, Defender for Cloud, and SCC findings into a common index. Normalize severity and finding type. Alert on new critical/high. Dashboard open findings by cloud, severity, and category (e.g. encryption, networking).

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=security (sourcetype=aws:securityhub OR sourcetype=azure:defender OR sourcetype=gcp:scc)
| eval cloud=case(like(sourcetype, "aws%"), "AWS", like(sourcetype, "azure%"), "Azure", like(sourcetype, "gcp%"), "GCP", true(), "Other")
| eval severity=coalesce(severity, Severity, 'finding.severity')
| where severity="CRITICAL" OR severity="HIGH"
| stats count by cloud, severity, finding_type
| sort -count
```

Understanding this SPL

**Multi-Cloud Security Posture (CSPM) Findings** — CSPM tools (or native Security Hub, Defender, SCC) produce findings across clouds. Centralizing in Splunk enables unified prioritization and remediation tracking.

Documented **Data sources**: AWS Security Hub, Azure Defender/Security Center, GCP Security Command Center, or third-party CSPM API. **App/TA** (typical add-on context): Splunk TAs for each cloud, or CSPM product integration (e.g. Prisma Cloud, Wiz). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: security; **sourcetype**: aws:securityhub, azure:defender, gcp:scc. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=security, sourcetype=aws:securityhub. Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `eval` defines or adjusts **cloud** — often to normalize units, derive a ratio, or prepare for thresholds.
• `eval` defines or adjusts **severity** — often to normalize units, derive a ratio, or prepare for thresholds.
• Filters the current rows with `where severity="CRITICAL" OR severity="HIGH"` — typically the threshold or rule expression for this monitoring goal.
• `stats` rolls up events into metrics; results are split **by cloud, severity, finding_type** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (cloud, severity, type, count), Bar chart (findings by cloud), Trend line (findings over time).

## SPL

```spl
index=security (sourcetype=aws:securityhub OR sourcetype=azure:defender OR sourcetype=gcp:scc)
| eval cloud=case(like(sourcetype, "aws%"), "AWS", like(sourcetype, "azure%"), "Azure", like(sourcetype, "gcp%"), "GCP", true(), "Other")
| eval severity=coalesce(severity, Severity, 'finding.severity')
| where severity="CRITICAL" OR severity="HIGH"
| stats count by cloud, severity, finding_type
| sort -count
```

## Visualization

Table (cloud, severity, type, count), Bar chart (findings by cloud), Trend line (findings over time).

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
