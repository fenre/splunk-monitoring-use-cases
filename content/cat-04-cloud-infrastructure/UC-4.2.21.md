<!-- AUTO-GENERATED from UC-4.2.21.json — DO NOT EDIT -->

---
id: "4.2.21"
title: "Azure Container Registry Pull/Push and Vulnerability Scan"
criticality: "medium"
splunkPillar: "Security"
---

# UC-4.2.21 · Azure Container Registry Pull/Push and Vulnerability Scan

## Description

ACR stores container images. Unusual pull/push or image scan findings indicate abuse or vulnerable images in use.

## Value

ACR stores container images. Unusual pull/push or image scan findings indicate abuse or vulnerable images in use.

## Implementation

Enable ACR diagnostic logs. Baseline pull/push by identity and repo; alert on anomalies. Ingest vulnerability scan results from Defender or ACR task; alert on critical/high in production repos.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_microsoft-cloudservices`.
• Ensure the following data sources are available: ACR diagnostic logs (Pull, Push), Defender for Containers / ACR vulnerability scan.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Enable ACR diagnostic logs. Baseline pull/push by identity and repo; alert on anomalies. Ingest vulnerability scan results from Defender or ACR task; alert on critical/high in production repos.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=azure sourcetype="mscs:azure:diagnostics" ResourceType="MICROSOFT.CONTAINERREGISTRY/REGISTRIES" OperationName="Pull"
| stats count by identity_claim_upn repository
| eventstats avg(count) as avg_pull, stdev(count) as stdev_pull
| where count > avg_pull + 2*stdev_pull
```

Understanding this SPL

**Azure Container Registry Pull/Push and Vulnerability Scan** — ACR stores container images. Unusual pull/push or image scan findings indicate abuse or vulnerable images in use.

Documented **Data sources**: ACR diagnostic logs (Pull, Push), Defender for Containers / ACR vulnerability scan. **App/TA** (typical add-on context): `Splunk_TA_microsoft-cloudservices`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: azure; **sourcetype**: mscs:azure:diagnostics, MICROSOFT.CONTAINERREGISTRY/REGISTRIES. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=azure, sourcetype="mscs:azure:diagnostics". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `stats` rolls up events into metrics; results are split **by identity_claim_upn repository** so each row reflects one combination of those dimensions.
• `eventstats` aggregates the pipeline (counts, distinct values, sums, percentiles, etc.) into fewer rows.
• Filters the current rows with `where count > avg_pull + 2*stdev_pull` — typically the threshold or rule expression for this monitoring goal.

Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (user, repo, pulls), Bar chart (top pullers), Table (image, CVE, severity).

## SPL

```spl
index=azure sourcetype="mscs:azure:diagnostics" ResourceType="MICROSOFT.CONTAINERREGISTRY/REGISTRIES" OperationName="Pull"
| stats count by identity_claim_upn repository
| eventstats avg(count) as avg_pull, stdev(count) as stdev_pull
| where count > avg_pull + 2*stdev_pull
```

## Visualization

Table (user, repo, pulls), Bar chart (top pullers), Table (image, CVE, severity).

## References

- [Splunk_TA_microsoft-cloudservices](https://splunkbase.splunk.com/app/3110)
