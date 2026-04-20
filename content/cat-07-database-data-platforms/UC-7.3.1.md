---
id: "7.3.1"
title: "RDS/Aurora Performance Insights"
criticality: "high"
splunkPillar: "Observability"
---

# UC-7.3.1 · RDS/Aurora Performance Insights

## Description

Performance Insights identifies top SQL and wait events without agent installation. Enables rapid diagnosis of managed database bottlenecks.

## Value

Performance Insights identifies top SQL and wait events without agent installation. Enables rapid diagnosis of managed database bottlenecks.

## Implementation

Enable Enhanced Monitoring and Performance Insights on RDS instances. Ingest CloudWatch metrics via Splunk Add-on for AWS. Enable RDS log exports (slow query, error, general) to CloudWatch Logs for deeper analysis.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_aws` (CloudWatch).
• Ensure the following data sources are available: RDS Performance Insights API, CloudWatch Enhanced Monitoring.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Enable Enhanced Monitoring and Performance Insights on RDS instances. Ingest CloudWatch metrics via Splunk Add-on for AWS. Enable RDS log exports (slow query, error, general) to CloudWatch Logs for deeper analysis.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=aws sourcetype="aws:cloudwatch" namespace="AWS/RDS"
| where metric_name IN ("CPUUtilization","DatabaseConnections","ReadLatency","WriteLatency")
| timechart span=5m avg(Average) by metric_name, DBInstanceIdentifier
```

Understanding this SPL

**RDS/Aurora Performance Insights** — Performance Insights identifies top SQL and wait events without agent installation. Enables rapid diagnosis of managed database bottlenecks.

Documented **Data sources**: RDS Performance Insights API, CloudWatch Enhanced Monitoring. **App/TA** (typical add-on context): `Splunk_TA_aws` (CloudWatch). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: aws; **sourcetype**: aws:cloudwatch. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=aws, sourcetype="aws:cloudwatch". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Filters the current rows with `where metric_name IN ("CPUUtilization","DatabaseConnections","ReadLatency","WriteLatency")` — typically the threshold or rule expression for this monitoring goal.
• `timechart` plots the metric over time using **span=5m** buckets with a separate series **by metric_name, DBInstanceIdentifier** — ideal for trending and alerting on this use case.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Multi-line chart (CPU, connections, latency), Table (top wait events), Single value (current active sessions).

## SPL

```spl
index=aws sourcetype="aws:cloudwatch" namespace="AWS/RDS"
| where metric_name IN ("CPUUtilization","DatabaseConnections","ReadLatency","WriteLatency")
| timechart span=5m avg(Average) by metric_name, DBInstanceIdentifier
```

## Visualization

Multi-line chart (CPU, connections, latency), Table (top wait events), Single value (current active sessions).

## References

- [Splunk_TA_aws](https://splunkbase.splunk.com/app/1876)
