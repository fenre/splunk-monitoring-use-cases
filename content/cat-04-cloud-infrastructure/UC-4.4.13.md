---
id: "4.4.13"
title: "Cloud Provider Status and Incident Correlation"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-4.4.13 · Cloud Provider Status and Incident Correlation

## Description

When AWS/Azure/GCP have outages, correlating provider status with your alerts prevents wasted troubleshooting and supports customer communication.

## Value

When AWS/Azure/GCP have outages, correlating provider status with your alerts prevents wasted troubleshooting and supports customer communication.

## Implementation

Poll provider status APIs (e.g. status.aws.amazon.com, status.azure.com) or ingest RSS. Normalize to common schema. When your alerts spike, search status index for same time window and provider. Dashboard active incidents by provider.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: Custom input (status page API or RSS), or status page integration.
• Ensure the following data sources are available: AWS Service Health Dashboard, Azure Status, GCP Status (APIs or scraped).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Poll provider status APIs (e.g. status.aws.amazon.com, status.azure.com) or ingest RSS. Normalize to common schema. When your alerts spike, search status index for same time window and provider. Dashboard active incidents by provider.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=cloud_status provider=* status=*impact*
| table _time provider service status description
| sort -_time
```

Understanding this SPL

**Cloud Provider Status and Incident Correlation** — When AWS/Azure/GCP have outages, correlating provider status with your alerts prevents wasted troubleshooting and supports customer communication.

Documented **Data sources**: AWS Service Health Dashboard, Azure Status, GCP Status (APIs or scraped). **App/TA** (typical add-on context): Custom input (status page API or RSS), or status page integration. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: cloud_status.

**Pipeline walkthrough**

• Scopes the data: index=cloud_status. Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Pipeline stage (see **Cloud Provider Status and Incident Correlation**): table _time provider service status description
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (provider, service, status), Timeline (incidents), Single value (active incidents).

## SPL

```spl
index=cloud_status provider=* status=*impact*
| table _time provider service status description
| sort -_time
```

## Visualization

Table (provider, service, status), Timeline (incidents), Single value (active incidents).

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
