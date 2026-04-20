---
id: "4.4.19"
title: "Multi-Cloud Cost Anomaly and Spike Detection"
criticality: "high"
splunkPillar: "Security"
---

# UC-4.4.19 · Multi-Cloud Cost Anomaly and Spike Detection

## Description

Sudden cost spikes across AWS, Azure, or GCP indicate misconfiguration, abuse, or runaway resources. Early detection limits financial impact and supports FinOps review.

## Value

Sudden cost spikes across AWS, Azure, or GCP indicate misconfiguration, abuse, or runaway resources. Early detection limits financial impact and supports FinOps review.

## Implementation

Ingest daily (or hourly) cost by provider and service. Compute rolling mean and standard deviation per provider. Alert when daily cost exceeds 2 standard deviations. Correlate with resource inventory for top contributors.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_aws`, Azure Cost Management export, GCP Billing export.
• Ensure the following data sources are available: AWS CUR, Azure Cost Management, GCP Billing export (BigQuery or file).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Ingest daily (or hourly) cost by provider and service. Compute rolling mean and standard deviation per provider. Alert when daily cost exceeds 2 standard deviations. Correlate with resource inventory for top contributors.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=cloud sourcetype="billing:daily" (provider=aws OR provider=azure OR provider=gcp)
| timechart span=1d sum(unblended_cost) as cost by provider
| eventstats avg(cost) as avg_cost, stdev(cost) as std_cost by provider
| eval z_score=if(std_cost>0, (cost-avg_cost)/std_cost, 0)
| where z_score > 2
| table _time provider cost avg_cost z_score
```

Understanding this SPL

**Multi-Cloud Cost Anomaly and Spike Detection** — Sudden cost spikes across AWS, Azure, or GCP indicate misconfiguration, abuse, or runaway resources. Early detection limits financial impact and supports FinOps review.

Documented **Data sources**: AWS CUR, Azure Cost Management, GCP Billing export (BigQuery or file). **App/TA** (typical add-on context): `Splunk_TA_aws`, Azure Cost Management export, GCP Billing export. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: cloud; **sourcetype**: billing:daily. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=cloud, sourcetype="billing:daily". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `timechart` plots the metric over time using **span=1d** buckets with a separate series **by provider** — ideal for trending and alerting on this use case.
• `eventstats` rolls up events into metrics; results are split **by provider** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• `eval` defines or adjusts **z_score** — often to normalize units, derive a ratio, or prepare for thresholds.
• Filters the current rows with `where z_score > 2` — typically the threshold or rule expression for this monitoring goal.
• Pipeline stage (see **Multi-Cloud Cost Anomaly and Spike Detection**): table _time provider cost avg_cost z_score

Enable Data Model Acceleration (and metric indexes for `mstats`) for the models or datasets referenced above; otherwise `tstats`/`mstats` may return no results from summaries.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Line chart (cost by provider over time), Table (anomalous days), Single value (current day vs baseline).

## SPL

```spl
index=cloud sourcetype="billing:daily" (provider=aws OR provider=azure OR provider=gcp)
| timechart span=1d sum(unblended_cost) as cost by provider
| eventstats avg(cost) as avg_cost, stdev(cost) as std_cost by provider
| eval z_score=if(std_cost>0, (cost-avg_cost)/std_cost, 0)
| where z_score > 2
| table _time provider cost avg_cost z_score
```

## Visualization

Line chart (cost by provider over time), Table (anomalous days), Single value (current day vs baseline).

## References

- [Splunk_TA_aws](https://splunkbase.splunk.com/app/1876)
