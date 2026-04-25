<!-- AUTO-GENERATED from UC-4.1.28.json — DO NOT EDIT -->

---
id: "4.1.28"
title: "EBS Volume Status and Burst Balance"
criticality: "high"
splunkPillar: "Observability"
---

# UC-4.1.28 · EBS Volume Status and Burst Balance

## Description

EBS status checks and burst balance (gp2/gp3) indicate volume health and risk of I/O throttling when credits are exhausted.

## Value

EBS status checks and burst balance (gp2/gp3) indicate volume health and risk of I/O throttling when credits are exhausted.

## Implementation

Collect EBS metrics. Alert on VolumeStatusCheckFailed. For gp2/gp3, alert when BurstBalancePercentage < 20%. Consider io1/io2 or gp3 with higher baseline IOPS for steady high I/O.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_aws`.
• Ensure the following data sources are available: CloudWatch EBS metrics (VolumeStatusCheckFailed, BurstBalancePercentage).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Collect EBS metrics. Alert on VolumeStatusCheckFailed. For gp2/gp3, alert when BurstBalancePercentage < 20%. Consider io1/io2 or gp3 with higher baseline IOPS for steady high I/O.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=aws sourcetype="aws:cloudwatch" namespace="AWS/EBS" (metric_name="VolumeStatusCheckFailed" OR metric_name="BurstBalancePercentage")
| where VolumeStatusCheckFailed > 0 OR BurstBalancePercentage < 20
| table _time VolumeId metric_name Average
```

Understanding this SPL

**EBS Volume Status and Burst Balance** — EBS status checks and burst balance (gp2/gp3) indicate volume health and risk of I/O throttling when credits are exhausted.

Documented **Data sources**: CloudWatch EBS metrics (VolumeStatusCheckFailed, BurstBalancePercentage). **App/TA** (typical add-on context): `Splunk_TA_aws`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: aws; **sourcetype**: aws:cloudwatch. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=aws, sourcetype="aws:cloudwatch". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Filters the current rows with `where VolumeStatusCheckFailed > 0 OR BurstBalancePercentage < 20` — typically the threshold or rule expression for this monitoring goal.
• Pipeline stage (see **EBS Volume Status and Burst Balance**): table _time VolumeId metric_name Average


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (volume, status, burst %), Single value (volumes with low burst), Timeline.

## SPL

```spl
index=aws sourcetype="aws:cloudwatch" namespace="AWS/EBS" (metric_name="VolumeStatusCheckFailed" OR metric_name="BurstBalancePercentage")
| where VolumeStatusCheckFailed > 0 OR BurstBalancePercentage < 20
| table _time VolumeId metric_name Average
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

Table (volume, status, burst %), Single value (volumes with low burst), Timeline.

## References

- [Splunk_TA_aws](https://splunkbase.splunk.com/app/1876)
