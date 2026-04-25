<!-- AUTO-GENERATED from UC-4.1.11.json — DO NOT EDIT -->

---
id: "4.1.11"
title: "RDS Performance Insights"
criticality: "high"
splunkPillar: "Observability"
---

# UC-4.1.11 · RDS Performance Insights

## Description

Database performance issues directly impact application experience. Monitoring connections, CPU, IOPS, and replica lag catches problems before users notice.

## Value

Database performance issues directly impact application experience. Monitoring connections, CPU, IOPS, and replica lag catches problems before users notice.

## Implementation

Enable CloudWatch metric collection for RDS namespace. Also forward RDS logs (slow query, error, general) to Splunk via CloudWatch Logs. Alert on ReplicaLag >30s, CPU >80%, or connection count nearing max.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_aws`.
• Ensure the following data sources are available: `sourcetype=aws:cloudwatch` (RDS namespace), RDS logs.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Enable CloudWatch metric collection for RDS namespace. Also forward RDS logs (slow query, error, general) to Splunk via CloudWatch Logs. Alert on ReplicaLag >30s, CPU >80%, or connection count nearing max.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=aws sourcetype="aws:cloudwatch" namespace="AWS/RDS" (metric_name="CPUUtilization" OR metric_name="DatabaseConnections" OR metric_name="ReadLatency" OR metric_name="ReplicaLag")
| timechart span=5m avg(Average) by metric_name, DBInstanceIdentifier
```

Understanding this SPL

**RDS Performance Insights** — Database performance issues directly impact application experience. Monitoring connections, CPU, IOPS, and replica lag catches problems before users notice.

Documented **Data sources**: `sourcetype=aws:cloudwatch` (RDS namespace), RDS logs. **App/TA** (typical add-on context): `Splunk_TA_aws`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: aws; **sourcetype**: aws:cloudwatch. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=aws, sourcetype="aws:cloudwatch". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `timechart` plots the metric over time using **span=5m** buckets with a separate series **by metric_name, DBInstanceIdentifier** — ideal for trending and alerting on this use case.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Multi-metric line chart, Gauge (connections vs. max), Table.

## SPL

```spl
index=aws sourcetype="aws:cloudwatch" namespace="AWS/RDS" (metric_name="CPUUtilization" OR metric_name="DatabaseConnections" OR metric_name="ReadLatency" OR metric_name="ReplicaLag")
| timechart span=5m avg(Average) by metric_name, DBInstanceIdentifier
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

Multi-metric line chart, Gauge (connections vs. max), Table.

## References

- [Splunk_TA_aws](https://splunkbase.splunk.com/app/1876)
