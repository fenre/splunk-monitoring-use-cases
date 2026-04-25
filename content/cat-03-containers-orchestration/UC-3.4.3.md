<!-- AUTO-GENERATED from UC-3.4.3.json — DO NOT EDIT -->

---
id: "3.4.3"
title: "Storage Quota Monitoring"
criticality: "low"
splunkPillar: "Observability"
---

# UC-3.4.3 · Storage Quota Monitoring

## Description

Registry storage exhaustion prevents image pushes, blocking CI/CD pipelines. Monitoring enables proactive cleanup policy tuning.

## Value

Registry storage exhaustion prevents image pushes, blocking CI/CD pipelines. Monitoring enables proactive cleanup policy tuning.

## Implementation

Poll registry API for storage metrics. Alert when usage exceeds 80%. Review and tune image retention/garbage collection policies.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: Custom API input.
• Ensure the following data sources are available: Registry storage API metrics.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Poll registry API for storage metrics. Alert when usage exceeds 80%. Review and tune image retention/garbage collection policies.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=containers sourcetype="registry:metrics"
| stats latest(storage_used_bytes) as used, latest(storage_quota_bytes) as quota by registry
| eval used_pct = round(used / quota * 100, 1)
| where used_pct > 80
```

Understanding this SPL

**Storage Quota Monitoring** — Registry storage exhaustion prevents image pushes, blocking CI/CD pipelines. Monitoring enables proactive cleanup policy tuning.

Documented **Data sources**: Registry storage API metrics. **App/TA** (typical add-on context): Custom API input. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: containers; **sourcetype**: registry:metrics. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=containers, sourcetype="registry:metrics". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `stats` rolls up events into metrics; results are split **by registry** so each row reflects one combination of those dimensions.
• `eval` defines or adjusts **used_pct** — often to normalize units, derive a ratio, or prepare for thresholds.
• Filters the current rows with `where used_pct > 80` — typically the threshold or rule expression for this monitoring goal.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Gauge (storage usage), Line chart (growth trend), Table.

## SPL

```spl
index=containers sourcetype="registry:metrics"
| stats latest(storage_used_bytes) as used, latest(storage_quota_bytes) as quota by registry
| eval used_pct = round(used / quota * 100, 1)
| where used_pct > 80
```

## Visualization

Gauge (storage usage), Line chart (growth trend), Table.

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
