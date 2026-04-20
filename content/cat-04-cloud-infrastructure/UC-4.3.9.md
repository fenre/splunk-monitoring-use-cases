---
id: "4.3.9"
title: "Cloud Load Balancing Backend Health and Request Count"
criticality: "critical"
splunkPillar: "Observability"
---

# UC-4.3.9 · Cloud Load Balancing Backend Health and Request Count

## Description

Unhealthy backends receive no traffic; request count and latency indicate load and performance. Essential for global and regional LB reliability.

## Value

Unhealthy backends receive no traffic; request count and latency indicate load and performance. Essential for global and regional LB reliability.

## Implementation

Collect Load Balancing metrics. Alert when backend health is unhealthy or backend_utilization >90%. Monitor request_count and latency by backend and URL map.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_google-cloudplatform`.
• Ensure the following data sources are available: Cloud Monitoring (loadbalancing.googleapis.com/https/request_count, backend_utilization).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Collect Load Balancing metrics. Alert when backend health is unhealthy or backend_utilization >90%. Monitor request_count and latency by backend and URL map.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=gcp sourcetype="google:gcp:monitoring" metric.type="loadbalancing.googleapis.com/https/backend_utilization"
| where value > 0.9
| timechart span=5m avg(value) by resource.labels.backend_name
```

Understanding this SPL

**Cloud Load Balancing Backend Health and Request Count** — Unhealthy backends receive no traffic; request count and latency indicate load and performance. Essential for global and regional LB reliability.

Documented **Data sources**: Cloud Monitoring (loadbalancing.googleapis.com/https/request_count, backend_utilization). **App/TA** (typical add-on context): `Splunk_TA_google-cloudplatform`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: gcp; **sourcetype**: google:gcp:monitoring. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=gcp, sourcetype="google:gcp:monitoring". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Filters the current rows with `where value > 0.9` — typically the threshold or rule expression for this monitoring goal.
• `timechart` plots the metric over time using **span=5m** buckets with a separate series **by resource.labels.backend_name** — ideal for trending and alerting on this use case.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Status panel (backend health), Line chart (requests, latency by backend), Table (backend, utilization).

## SPL

```spl
index=gcp sourcetype="google:gcp:monitoring" metric.type="loadbalancing.googleapis.com/https/backend_utilization"
| where value > 0.9
| timechart span=5m avg(value) by resource.labels.backend_name
```

## Visualization

Status panel (backend health), Line chart (requests, latency by backend), Table (backend, utilization).

## References

- [Splunk_TA_google-cloudplatform](https://splunkbase.splunk.com/app/3088)
