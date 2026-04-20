---
id: "4.3.16"
title: "Artifact Registry Push/Pull and Vulnerability Scan"
criticality: "medium"
splunkPillar: "Security"
---

# UC-4.3.16 · Artifact Registry Push/Pull and Vulnerability Scan

## Description

Unusual push/pull may indicate abuse. Vulnerability scan findings in images require remediation before deployment.

## Value

Unusual push/pull may indicate abuse. Vulnerability scan findings in images require remediation before deployment.

## Implementation

Forward Artifact Registry audit logs via Pub/Sub. Ingest Container Analysis for CVE findings. Alert on critical/high in production repos. Baseline push/pull by principal; alert on anomalies.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_google-cloudplatform`.
• Ensure the following data sources are available: Audit logs (Artifact Registry API), Container Analysis (vulnerability occurrences).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Forward Artifact Registry audit logs via Pub/Sub. Ingest Container Analysis for CVE findings. Alert on critical/high in production repos. Baseline push/pull by principal; alert on anomalies.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=gcp sourcetype="google:gcp:pubsub:message" protoPayload.serviceName="artifactregistry.googleapis.com"
| spath output=method path=protoPayload.methodName
| stats count by method resource.labels.repository
| sort -count
```

Understanding this SPL

**Artifact Registry Push/Pull and Vulnerability Scan** — Unusual push/pull may indicate abuse. Vulnerability scan findings in images require remediation before deployment.

Documented **Data sources**: Audit logs (Artifact Registry API), Container Analysis (vulnerability occurrences). **App/TA** (typical add-on context): `Splunk_TA_google-cloudplatform`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: gcp; **sourcetype**: google:gcp:pubsub:message. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=gcp, sourcetype="google:gcp:pubsub:message". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Extracts structured paths (JSON/XML) with `spath`.
• `stats` rolls up events into metrics; results are split **by method resource.labels.repository** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (repo, method, count), Bar chart (top push/pull), Table (image, CVE, severity).

## SPL

```spl
index=gcp sourcetype="google:gcp:pubsub:message" protoPayload.serviceName="artifactregistry.googleapis.com"
| spath output=method path=protoPayload.methodName
| stats count by method resource.labels.repository
| sort -count
```

## Visualization

Table (repo, method, count), Bar chart (top push/pull), Table (image, CVE, severity).

## References

- [Splunk_TA_google-cloudplatform](https://splunkbase.splunk.com/app/3088)
