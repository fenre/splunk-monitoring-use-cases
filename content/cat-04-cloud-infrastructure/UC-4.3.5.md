---
id: "4.3.5"
title: "Security Command Center"
criticality: "critical"
splunkPillar: "Security"
---

# UC-4.3.5 · Security Command Center

## Description

SCC provides vulnerability findings and threat detections across GCP. Centralizing in Splunk enables multi-cloud security correlation.

## Value

SCC provides vulnerability findings and threat detections across GCP. Centralizing in Splunk enables multi-cloud security correlation.

## Implementation

Configure SCC to publish findings to Pub/Sub. Ingest via Splunk TA. Alert on CRITICAL and HIGH severity findings.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_google-cloudplatform`.
• Ensure the following data sources are available: SCC findings via Pub/Sub notification.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Configure SCC to publish findings to Pub/Sub. Ingest via Splunk TA. Alert on CRITICAL and HIGH severity findings.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=gcp sourcetype="google:gcp:pubsub:message" resource.type="scc_finding"
| spath output=severity path=finding.severity
| spath output=category path=finding.category
| where severity="CRITICAL" OR severity="HIGH"
| table _time category severity finding.resourceName finding.description
| sort -_time
```

Understanding this SPL

**Security Command Center** — SCC provides vulnerability findings and threat detections across GCP. Centralizing in Splunk enables multi-cloud security correlation.

Documented **Data sources**: SCC findings via Pub/Sub notification. **App/TA** (typical add-on context): `Splunk_TA_google-cloudplatform`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: gcp; **sourcetype**: google:gcp:pubsub:message. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=gcp, sourcetype="google:gcp:pubsub:message". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Extracts structured paths (JSON/XML) with `spath`.
• Extracts structured paths (JSON/XML) with `spath`.
• Filters the current rows with `where severity="CRITICAL" OR severity="HIGH"` — typically the threshold or rule expression for this monitoring goal.
• Pipeline stage (see **Security Command Center**): table _time category severity finding.resourceName finding.description
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table by severity, Bar chart (finding categories), Trend line.

## SPL

```spl
index=gcp sourcetype="google:gcp:pubsub:message" resource.type="scc_finding"
| spath output=severity path=finding.severity
| spath output=category path=finding.category
| where severity="CRITICAL" OR severity="HIGH"
| table _time category severity finding.resourceName finding.description
| sort -_time
```

## Visualization

Table by severity, Bar chart (finding categories), Trend line.

## References

- [Splunk_TA_google-cloudplatform](https://splunkbase.splunk.com/app/3088)
