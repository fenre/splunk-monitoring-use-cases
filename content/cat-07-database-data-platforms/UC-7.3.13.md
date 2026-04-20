---
id: "7.3.13"
title: "Cloud SQL Storage Auto-Grow Events"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-7.3.13 · Cloud SQL Storage Auto-Grow Events

## Description

Automatic storage increases for GCP Cloud SQL (and similar) signal rapid data growth and cost impact.

## Value

Automatic storage increases for GCP Cloud SQL (and similar) signal rapid data growth and cost impact.

## Implementation

Parse patch operations that change disk size. Alert when more than one resize per week per instance. Forecast disk from `disk_utilization` metrics.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: GCP audit logs, Cloud SQL Admin API events.
• Ensure the following data sources are available: `storageResize`, disk size change operations.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Parse patch operations that change disk size. Alert when more than one resize per week per instance. Forecast disk from `disk_utilization` metrics.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=gcp sourcetype="gcp:audit" protoPayload.methodName="*.sql.instances.patch"
| spath output=new_disk_gb protoPayload.request.settings.dataDiskSizeGb
| where isnotnull(new_disk_gb)
| table _time, resourceName, new_disk_gb, protoPayload.authenticationInfo.principalEmail
```

Understanding this SPL

**Cloud SQL Storage Auto-Grow Events** — Automatic storage increases for GCP Cloud SQL (and similar) signal rapid data growth and cost impact.

Documented **Data sources**: `storageResize`, disk size change operations. **App/TA** (typical add-on context): GCP audit logs, Cloud SQL Admin API events. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: gcp; **sourcetype**: gcp:audit. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=gcp, sourcetype="gcp:audit". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Extracts structured paths (JSON/XML) with `spath`.
• Filters the current rows with `where isnotnull(new_disk_gb)` — typically the threshold or rule expression for this monitoring goal.
• Pipeline stage (see **Cloud SQL Storage Auto-Grow Events**): table _time, resourceName, new_disk_gb, protoPayload.authenticationInfo.principalEmail


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Timeline (resize events), Table (instance, new size GB), Line chart (disk size over time).

## SPL

```spl
index=gcp sourcetype="gcp:audit" protoPayload.methodName="*.sql.instances.patch"
| spath output=new_disk_gb protoPayload.request.settings.dataDiskSizeGb
| where isnotnull(new_disk_gb)
| table _time, resourceName, new_disk_gb, protoPayload.authenticationInfo.principalEmail
```

## Visualization

Timeline (resize events), Table (instance, new size GB), Line chart (disk size over time).

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
