---
id: "4.3.6"
title: "GCE Instance Monitoring"
criticality: "medium"
splunkPillar: "Security"
---

# UC-4.3.6 · GCE Instance Monitoring

## Description

Compute Engine VM performance monitoring for capacity planning and baseline trending without guest-level agents.

## Value

Compute Engine VM performance monitoring for capacity planning and baseline trending without guest-level agents.

## Implementation

Configure Cloud Monitoring metric collection in the Splunk TA. Collect CPU utilization, disk I/O, and network metrics. Alert on sustained high utilization.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_google-cloudplatform`.
• Ensure the following data sources are available: Cloud Monitoring metrics via API.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Configure Cloud Monitoring metric collection in the Splunk TA. Collect CPU utilization, disk I/O, and network metrics. Alert on sustained high utilization.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=gcp sourcetype="google:gcp:monitoring" metric.type="compute.googleapis.com/instance/cpu/utilization"
| timechart span=1h avg(value) by resource.labels.instance_id
```

Understanding this SPL

**GCE Instance Monitoring** — Compute Engine VM performance monitoring for capacity planning and baseline trending without guest-level agents.

Documented **Data sources**: Cloud Monitoring metrics via API. **App/TA** (typical add-on context): `Splunk_TA_google-cloudplatform`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: gcp; **sourcetype**: google:gcp:monitoring. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=gcp, sourcetype="google:gcp:monitoring". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `timechart` plots the metric over time using **span=1h** buckets with a separate series **by resource.labels.instance_id** — ideal for trending and alerting on this use case.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Line chart, Heatmap, Gauge.

## SPL

```spl
index=gcp sourcetype="google:gcp:monitoring" metric.type="compute.googleapis.com/instance/cpu/utilization"
| timechart span=1h avg(value) by resource.labels.instance_id
```

## Visualization

Line chart, Heatmap, Gauge.

## References

- [Splunk_TA_google-cloudplatform](https://splunkbase.splunk.com/app/3088)
