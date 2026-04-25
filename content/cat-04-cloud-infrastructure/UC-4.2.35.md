<!-- AUTO-GENERATED from UC-4.2.35.json — DO NOT EDIT -->

---
id: "4.2.35"
title: "Cost Management Anomaly Detection"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-4.2.35 · Cost Management Anomaly Detection

## Description

Built-in Cost Management alerts help, but statistical baselines on daily spend catch unusual service charges early.

## Value

Built-in Cost Management alerts help, but statistical baselines on daily spend catch unusual service charges early.

## Implementation

Ingest daily actual cost by service and resource group. Use `predict` or manual z-score as shown. Alert finance and owners on anomalies. Exclude known one-time purchases via lookup.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_microsoft-cloudservices`, Cost Management export.
• Ensure the following data sources are available: `sourcetype=mscs:azure:cost` or amortized cost CSV to blob/Event Hub.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Ingest daily actual cost by service and resource group. Use `predict` or manual z-score as shown. Alert finance and owners on anomalies. Exclude known one-time purchases via lookup.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=azure sourcetype="mscs:azure:cost"
| timechart span=1d sum(pretax_cost) as daily by ServiceName
| eventstats avg(daily) as mu, stdev(daily) as sigma by ServiceName
| eval z=if(sigma>0, (daily-mu)/sigma, 0)
| where z > 3
```

Understanding this SPL

**Cost Management Anomaly Detection** — Built-in Cost Management alerts help, but statistical baselines on daily spend catch unusual service charges early.

Documented **Data sources**: `sourcetype=mscs:azure:cost` or amortized cost CSV to blob/Event Hub. **App/TA** (typical add-on context): `Splunk_TA_microsoft-cloudservices`, Cost Management export. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: azure; **sourcetype**: mscs:azure:cost. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=azure, sourcetype="mscs:azure:cost". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `timechart` plots the metric over time using **span=1d** buckets with a separate series **by ServiceName** — ideal for trending and alerting on this use case.
• `eventstats` rolls up events into metrics; results are split **by ServiceName** so each row reflects one combination of those dimensions.
• `eval` defines or adjusts **z** — often to normalize units, derive a ratio, or prepare for thresholds.
• Filters the current rows with `where z > 3` — typically the threshold or rule expression for this monitoring goal.

Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Line chart (daily cost by service), Table (service, z-score), Single value (anomaly count).

## SPL

```spl
index=azure sourcetype="mscs:azure:cost"
| timechart span=1d sum(pretax_cost) as daily by ServiceName
| eventstats avg(daily) as mu, stdev(daily) as sigma by ServiceName
| eval z=if(sigma>0, (daily-mu)/sigma, 0)
| where z > 3
```

## Visualization

Line chart (daily cost by service), Table (service, z-score), Single value (anomaly count).

## References

- [Splunk_TA_microsoft-cloudservices](https://splunkbase.splunk.com/app/3110)
