---
id: "6.1.26"
title: "Deduplication Savings Ratio"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-6.1.26 · Deduplication Savings Ratio

## Description

Deduplication ratio trending validates efficiency features and detects anomalies (sudden ratio drop may indicate new data types or misconfiguration).

## Value

Deduplication ratio trending validates efficiency features and detects anomalies (sudden ratio drop may indicate new data types or misconfiguration).

## Implementation

Poll dedupe stats weekly or daily. Baseline savings ratio per aggregate. Alert on significant drop vs 30-day average (e.g., >20% relative drop).

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: Vendor TA (NetApp, Dell, Pure).
• Ensure the following data sources are available: Logical vs physical used, dedupe savings API fields.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Poll dedupe stats weekly or daily. Baseline savings ratio per aggregate. Alert on significant drop vs 30-day average (e.g., >20% relative drop).

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=storage sourcetype="storage:dedupe"
| eval savings_ratio=round((logical_used_bytes-physical_used_bytes)/nullif(logical_used_bytes,0)*100,1)
| timechart span=1d avg(savings_ratio) as ratio by aggregate_name
| where ratio < 30
```

Understanding this SPL

**Deduplication Savings Ratio** — Deduplication ratio trending validates efficiency features and detects anomalies (sudden ratio drop may indicate new data types or misconfiguration).

Documented **Data sources**: Logical vs physical used, dedupe savings API fields. **App/TA** (typical add-on context): Vendor TA (NetApp, Dell, Pure). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: storage; **sourcetype**: storage:dedupe. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=storage, sourcetype="storage:dedupe". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `eval` defines or adjusts **savings_ratio** — often to normalize units, derive a ratio, or prepare for thresholds.
• `timechart` plots the metric over time using **span=1d** buckets with a separate series **by aggregate_name** — ideal for trending and alerting on this use case.
• Filters the current rows with `where ratio < 30` — typically the threshold or rule expression for this monitoring goal.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Line chart (savings ratio over time), Table (aggregate, logical, physical, ratio), Single value (fleet average ratio).

## SPL

```spl
index=storage sourcetype="storage:dedupe"
| eval savings_ratio=round((logical_used_bytes-physical_used_bytes)/nullif(logical_used_bytes,0)*100,1)
| timechart span=1d avg(savings_ratio) as ratio by aggregate_name
| where ratio < 30
```

## Visualization

Line chart (savings ratio over time), Table (aggregate, logical, physical, ratio), Single value (fleet average ratio).

## References

- [Cisco DC Networking Application for Splunk](https://splunkbase.splunk.com/app/7777)
