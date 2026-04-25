<!-- AUTO-GENERATED from UC-4.1.26.json — DO NOT EDIT -->

---
id: "4.1.26"
title: "DynamoDB Throttled Requests and Consumed Capacity"
criticality: "high"
splunkPillar: "Observability"
---

# UC-4.1.26 · DynamoDB Throttled Requests and Consumed Capacity

## Description

Throttling causes request failures and degraded application performance. Capacity monitoring supports right-sizing and auto-scaling.

## Value

Throttling causes request failures and degraded application performance. Capacity monitoring supports right-sizing and auto-scaling.

## Implementation

Collect DynamoDB metrics per table. Alert on any ThrottledRequests. Dashboard consumed vs. provisioned capacity to tune throughput. Consider on-demand capacity if spikes are unpredictable.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_aws`.
• Ensure the following data sources are available: CloudWatch DynamoDB metrics (ThrottledRequests, ConsumedReadCapacityUnits, ConsumedWriteCapacityUnits).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Collect DynamoDB metrics per table. Alert on any ThrottledRequests. Dashboard consumed vs. provisioned capacity to tune throughput. Consider on-demand capacity if spikes are unpredictable.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=aws sourcetype="aws:cloudwatch" namespace="AWS/DynamoDB" metric_name="ThrottledRequests"
| where Sum > 0
| timechart span=5m sum(Sum) by TableName, Operation
```

Understanding this SPL

**DynamoDB Throttled Requests and Consumed Capacity** — Throttling causes request failures and degraded application performance. Capacity monitoring supports right-sizing and auto-scaling.

Documented **Data sources**: CloudWatch DynamoDB metrics (ThrottledRequests, ConsumedReadCapacityUnits, ConsumedWriteCapacityUnits). **App/TA** (typical add-on context): `Splunk_TA_aws`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: aws; **sourcetype**: aws:cloudwatch. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=aws, sourcetype="aws:cloudwatch". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Filters the current rows with `where Sum > 0` — typically the threshold or rule expression for this monitoring goal.
• `timechart` plots the metric over time using **span=5m** buckets with a separate series **by TableName, Operation** — ideal for trending and alerting on this use case.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Line chart (throttled, consumed by table), Table (top throttled tables), Gauge (utilization %).

## SPL

```spl
index=aws sourcetype="aws:cloudwatch" namespace="AWS/DynamoDB" metric_name="ThrottledRequests"
| where Sum > 0
| timechart span=5m sum(Sum) by TableName, Operation
```

## CIM SPL

```spl
| tstats `summariesonly` max(Performance.cpu_load_percent) as peak
  from datamodel=Performance.Performance
  by Performance.object Performance.host span=1h
| where isnotnull(peak)
| sort - peak
```

## Visualization

Line chart (throttled, consumed by table), Table (top throttled tables), Gauge (utilization %).

## References

- [Splunk_TA_aws](https://splunkbase.splunk.com/app/1876)
