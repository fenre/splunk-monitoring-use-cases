---
id: "4.1.14"
title: "Cost Anomaly Detection"
criticality: "medium"
splunkPillar: "Security"
---

# UC-4.1.14 · Cost Anomaly Detection

## Description

Unexpected spend spikes indicate runaway resources, cryptomining attacks, or misconfigured services. Catching anomalies early saves money.

## Value

Unexpected spend spikes indicate runaway resources, cryptomining attacks, or misconfigured services. Catching anomalies early saves money.

## Implementation

Enable CUR reports to S3. Ingest via Splunk_TA_aws (billing input). Calculate daily baselines per service. Alert when daily spend exceeds 2 standard deviations from the 30-day average.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_aws`, AWS Cost and Usage Report (CUR).
• Ensure the following data sources are available: `sourcetype=aws:billing` or CUR data.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Enable CUR reports to S3. Ingest via Splunk_TA_aws (billing input). Calculate daily baselines per service. Alert when daily spend exceeds 2 standard deviations from the 30-day average.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=aws sourcetype="aws:billing"
| timechart span=1d sum(BlendedCost) as daily_cost by ProductName
| eventstats avg(daily_cost) as avg_cost, stdev(daily_cost) as stdev_cost by ProductName
| eval threshold = avg_cost + (2 * stdev_cost)
| where daily_cost > threshold
```

Understanding this SPL

**Cost Anomaly Detection** — Unexpected spend spikes indicate runaway resources, cryptomining attacks, or misconfigured services. Catching anomalies early saves money.

Documented **Data sources**: `sourcetype=aws:billing` or CUR data. **App/TA** (typical add-on context): `Splunk_TA_aws`, AWS Cost and Usage Report (CUR). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: aws; **sourcetype**: aws:billing. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=aws, sourcetype="aws:billing". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `timechart` plots the metric over time using **span=1d** buckets with a separate series **by ProductName** — ideal for trending and alerting on this use case.
• `eventstats` rolls up events into metrics; results are split **by ProductName** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• `eval` defines or adjusts **threshold** — often to normalize units, derive a ratio, or prepare for thresholds.
• Filters the current rows with `where daily_cost > threshold` — typically the threshold or rule expression for this monitoring goal.

Enable Data Model Acceleration (and metric indexes for `mstats`) for the models or datasets referenced above; otherwise `tstats`/`mstats` may return no results from summaries.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Line chart (daily spend with threshold), Table (anomalous services), Stacked area (spend by service).

## SPL

```spl
index=aws sourcetype="aws:billing"
| timechart span=1d sum(BlendedCost) as daily_cost by ProductName
| eventstats avg(daily_cost) as avg_cost, stdev(daily_cost) as stdev_cost by ProductName
| eval threshold = avg_cost + (2 * stdev_cost)
| where daily_cost > threshold
```

## Visualization

Line chart (daily spend with threshold), Table (anomalous services), Stacked area (spend by service).

## References

- [Splunk_TA_aws](https://splunkbase.splunk.com/app/1876)
