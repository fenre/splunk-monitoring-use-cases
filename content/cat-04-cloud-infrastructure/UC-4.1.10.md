<!-- AUTO-GENERATED from UC-4.1.10.json — DO NOT EDIT -->

---
id: "4.1.10"
title: "EC2 Performance Monitoring"
criticality: "medium"
splunkPillar: "Security"
---

# UC-4.1.10 · EC2 Performance Monitoring

## Description

CloudWatch metrics provide host-level performance data without agents. Baseline trending for capacity planning and anomaly detection.

## Value

CloudWatch metrics provide host-level performance data without agents. Baseline trending for capacity planning and anomaly detection.

## Implementation

Configure CloudWatch metric collection in Splunk_TA_aws for EC2 namespace. Collect CPUUtilization, NetworkIn/Out, DiskReadOps, DiskWriteOps. Set polling interval (300s minimum).

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_aws`.
• Ensure the following data sources are available: `sourcetype=aws:cloudwatch` (EC2 namespace).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Configure CloudWatch metric collection in Splunk_TA_aws for EC2 namespace. Collect CPUUtilization, NetworkIn/Out, DiskReadOps, DiskWriteOps. Set polling interval (300s minimum).

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=aws sourcetype="aws:cloudwatch" metric_name="CPUUtilization" namespace="AWS/EC2"
| timechart span=1h avg(Average) as avg_cpu by metric_dimensions
| where avg_cpu > 80
```

Understanding this SPL

**EC2 CloudWatch metrics** — CloudWatch metrics provide host-level performance data without agents. Baseline trending for capacity planning and anomaly detection.

Documented **Data sources**: `sourcetype=aws:cloudwatch` (EC2 namespace). **App/TA** (typical add-on context): `Splunk_TA_aws`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: aws; **sourcetype**: aws:cloudwatch. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=aws, sourcetype="aws:cloudwatch". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `timechart` plots the metric over time using **span=1h** buckets with a separate series **by metric_dimensions** — ideal for trending and alerting on this use case.
• Filters the current rows with `where avg_cpu > 80` — typically the threshold or rule expression for this monitoring goal.

Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Line chart per instance, Heatmap across fleet, Gauge.


## SPL

```spl
index=aws sourcetype="aws:cloudwatch" metric_name="CPUUtilization" namespace="AWS/EC2"
| timechart span=1h avg(Average) as avg_cpu by metric_dimensions
| where avg_cpu > 80
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

Line chart per instance, Heatmap across fleet, Gauge.

## References

- [Splunk_TA_aws](https://splunkbase.splunk.com/app/1876)
