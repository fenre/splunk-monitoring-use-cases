---
id: "7.5.21"
title: "Elasticsearch Ingest Pipeline Error Rate"
criticality: "high"
splunkPillar: "Observability"
---

# UC-7.5.21 · Elasticsearch Ingest Pipeline Error Rate

## Description

Ingest pipeline failures silently drop or corrupt documents before indexing. Monitoring error rates per pipeline ensures data quality and completeness.

## Value

Ingest pipeline failures silently drop or corrupt documents before indexing. Monitoring error rates per pipeline ensures data quality and completeness.

## Implementation

Poll `GET _nodes/stats/ingest` and extract per-pipeline `count` and `failed` counters. Compute deltas between samples. Alert when any pipeline shows a non-zero failure rate. Investigate pipeline processor errors in Elasticsearch logs. Common causes include grok pattern mismatches, script errors, and date parsing failures.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: Custom REST scripted input (`_nodes/stats/ingest`).
• Ensure the following data sources are available: `sourcetype=elasticsearch:ingest_stats`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Poll `GET _nodes/stats/ingest` and extract per-pipeline `count` and `failed` counters. Compute deltas between samples. Alert when any pipeline shows a non-zero failure rate. Investigate pipeline processor errors in Elasticsearch logs. Common causes include grok pattern mismatches, script errors, and date parsing failures.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=database sourcetype="elasticsearch:ingest_stats"
| eval fail_rate=round(ingest.pipelines.failed/max(1,ingest.pipelines.count)*100,2)
| where fail_rate > 1 OR ingest.pipelines.failed > 0
| timechart span=5m sum(ingest.pipelines.failed) as failures by pipeline_name
```

Understanding this SPL

**Elasticsearch Ingest Pipeline Error Rate** — Ingest pipeline failures silently drop or corrupt documents before indexing. Monitoring error rates per pipeline ensures data quality and completeness.

Documented **Data sources**: `sourcetype=elasticsearch:ingest_stats`. **App/TA** (typical add-on context): Custom REST scripted input (`_nodes/stats/ingest`). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: database; **sourcetype**: elasticsearch:ingest_stats. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=database, sourcetype="elasticsearch:ingest_stats". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `eval` defines or adjusts **fail_rate** — often to normalize units, derive a ratio, or prepare for thresholds.
• Filters the current rows with `where fail_rate > 1 OR ingest.pipelines.failed > 0` — typically the threshold or rule expression for this monitoring goal.
• `timechart` plots the metric over time using **span=5m** buckets with a separate series **by pipeline_name** — ideal for trending and alerting on this use case.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Line chart (failures per pipeline), Table (pipeline error details), Single value (total ingest failures).

## SPL

```spl
index=database sourcetype="elasticsearch:ingest_stats"
| eval fail_rate=round(ingest.pipelines.failed/max(1,ingest.pipelines.count)*100,2)
| where fail_rate > 1 OR ingest.pipelines.failed > 0
| timechart span=5m sum(ingest.pipelines.failed) as failures by pipeline_name
```

## Visualization

Line chart (failures per pipeline), Table (pipeline error details), Single value (total ingest failures).

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
