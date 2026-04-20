---
id: "4.1.41"
title: "Redshift Cluster Health and Connection Count"
criticality: "high"
splunkPillar: "Observability"
---

# UC-4.1.41 · Redshift Cluster Health and Connection Count

## Description

Redshift cluster health and connection exhaustion impact analytics workloads. Monitoring supports capacity and connection limit management.

## Value

Redshift cluster health and connection exhaustion impact analytics workloads. Monitoring supports capacity and connection limit management.

## Implementation

Collect Redshift metrics. Alert when DatabaseConnections approaches max (e.g. 90% of limit) or CPUUtilization/PercentageDiskSpaceUsed is high. Correlate with query queue length.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_aws`.
• Ensure the following data sources are available: CloudWatch Redshift metrics (DatabaseConnections, CPUUtilization, PercentageDiskSpaceUsed).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Collect Redshift metrics. Alert when DatabaseConnections approaches max (e.g. 90% of limit) or CPUUtilization/PercentageDiskSpaceUsed is high. Correlate with query queue length.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=aws sourcetype="aws:cloudwatch" namespace="AWS/Redshift" metric_name="DatabaseConnections"
| bin _time span=5m
| stats avg(Average) as connections by _time, ClusterIdentifier
| where connections > 80
```

Understanding this SPL

**Redshift Cluster Health and Connection Count** — Redshift cluster health and connection exhaustion impact analytics workloads. Monitoring supports capacity and connection limit management.

Documented **Data sources**: CloudWatch Redshift metrics (DatabaseConnections, CPUUtilization, PercentageDiskSpaceUsed). **App/TA** (typical add-on context): `Splunk_TA_aws`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: aws; **sourcetype**: aws:cloudwatch. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=aws, sourcetype="aws:cloudwatch". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Discretizes time or numeric ranges with `bin`/`bucket`.
• `stats` rolls up events into metrics; results are split **by _time, ClusterIdentifier** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• Filters the current rows with `where connections > 80` — typically the threshold or rule expression for this monitoring goal.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Line chart (connections, CPU, disk by cluster), Table (cluster, metrics), Gauge (connection %).

## SPL

```spl
index=aws sourcetype="aws:cloudwatch" namespace="AWS/Redshift" metric_name="DatabaseConnections"
| bin _time span=5m
| stats avg(Average) as connections by _time, ClusterIdentifier
| where connections > 80
```

## Visualization

Line chart (connections, CPU, disk by cluster), Table (cluster, metrics), Gauge (connection %).

## References

- [Splunk_TA_aws](https://splunkbase.splunk.com/app/1876)
