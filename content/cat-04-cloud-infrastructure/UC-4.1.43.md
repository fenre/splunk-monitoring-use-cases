<!-- AUTO-GENERATED from UC-4.1.43.json — DO NOT EDIT -->

---
id: "4.1.43"
title: "EFS Burst Credit Balance and Throughput"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-4.1.43 · EFS Burst Credit Balance and Throughput

## Description

EFS burst credits deplete under sustained high throughput; performance then drops to baseline. Monitoring prevents unexpected slowdowns.

## Value

EFS burst credits deplete under sustained high throughput; performance then drops to baseline. Monitoring prevents unexpected slowdowns.

## Implementation

Collect EFS metrics. Alert when BurstCreditBalance falls below threshold (e.g. 500M). Consider provisioned throughput for consistent high I/O. Dashboard read/write IOPS and throughput.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_aws`.
• Ensure the following data sources are available: CloudWatch EFS metrics (BurstCreditBalance, DataReadIOBytes, DataWriteIOBytes).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Collect EFS metrics. Alert when BurstCreditBalance falls below threshold (e.g. 500M). Consider provisioned throughput for consistent high I/O. Dashboard read/write IOPS and throughput.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=aws sourcetype="aws:cloudwatch" namespace="AWS/EFS" metric_name="BurstCreditBalance"
| where Average < 500000000
| timechart span=1h avg(Average) by FileSystemId
```

Understanding this SPL

**EFS Burst Credit Balance and Throughput** — EFS burst credits deplete under sustained high throughput; performance then drops to baseline. Monitoring prevents unexpected slowdowns.

Documented **Data sources**: CloudWatch EFS metrics (BurstCreditBalance, DataReadIOBytes, DataWriteIOBytes). **App/TA** (typical add-on context): `Splunk_TA_aws`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: aws; **sourcetype**: aws:cloudwatch. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=aws, sourcetype="aws:cloudwatch". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Filters the current rows with `where Average < 500000000` — typically the threshold or rule expression for this monitoring goal.
• `timechart` plots the metric over time using **span=1h** buckets with a separate series **by FileSystemId** — ideal for trending and alerting on this use case.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Line chart (burst balance, IOPS by filesystem), Table (filesystem, balance), Gauge (balance %).

## SPL

```spl
index=aws sourcetype="aws:cloudwatch" namespace="AWS/EFS" metric_name="BurstCreditBalance"
| where Average < 500000000
| timechart span=1h avg(Average) by FileSystemId
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

Line chart (burst balance, IOPS by filesystem), Table (filesystem, balance), Gauge (balance %).

## References

- [Splunk_TA_aws](https://splunkbase.splunk.com/app/1876)
