---
id: "4.3.19"
title: "Cloud Billing Budget Alerts and Anomaly"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-4.3.19 · Cloud Billing Budget Alerts and Anomaly

## Description

Budget alerts and spend anomalies prevent cost overruns. Early detection enables corrective action before invoice.

## Value

Budget alerts and spend anomalies prevent cost overruns. Early detection enables corrective action before invoice.

## Implementation

Enable billing export. Ingest daily/monthly cost data. Create budget alerts and forward to Splunk. Calculate baseline and alert on 2-sigma anomaly by service or project.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_google-cloudplatform`.
• Ensure the following data sources are available: Billing export to BigQuery or Pub/Sub, Budget alert notifications.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Enable billing export. Ingest daily/monthly cost data. Create budget alerts and forward to Splunk. Calculate baseline and alert on 2-sigma anomaly by service or project.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=gcp sourcetype="gcp:billing"
| bin _time span=1d
| stats sum(cost) as daily_cost by _time, service
| eventstats avg(daily_cost) as avg_cost, stdev(daily_cost) as stdev_cost by service
| where daily_cost > avg_cost + 2*stdev_cost
```

Understanding this SPL

**Cloud Billing Budget Alerts and Anomaly** — Budget alerts and spend anomalies prevent cost overruns. Early detection enables corrective action before invoice.

Documented **Data sources**: Billing export to BigQuery or Pub/Sub, Budget alert notifications. **App/TA** (typical add-on context): `Splunk_TA_google-cloudplatform`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: gcp; **sourcetype**: gcp:billing. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=gcp, sourcetype="gcp:billing". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Discretizes time or numeric ranges with `bin`/`bucket`.
• `stats` rolls up events into metrics; results are split **by _time, service** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• `eventstats` rolls up events into metrics; results are split **by service** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• Filters the current rows with `where daily_cost > avg_cost + 2*stdev_cost` — typically the threshold or rule expression for this monitoring goal.

Enable Data Model Acceleration (and metric indexes for `mstats`) for the models or datasets referenced above; otherwise `tstats`/`mstats` may return no results from summaries.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Line chart (cost with threshold), Table (service, cost, anomaly), Stacked area (cost by service).

## SPL

```spl
index=gcp sourcetype="gcp:billing"
| bin _time span=1d
| stats sum(cost) as daily_cost by _time, service
| eventstats avg(daily_cost) as avg_cost, stdev(daily_cost) as stdev_cost by service
| where daily_cost > avg_cost + 2*stdev_cost
```

## Visualization

Line chart (cost with threshold), Table (service, cost, anomaly), Stacked area (cost by service).

## References

- [Splunk_TA_google-cloudplatform](https://splunkbase.splunk.com/app/3088)
