<!-- AUTO-GENERATED from UC-4.1.49.json — DO NOT EDIT -->

---
id: "4.1.49"
title: "FSx for Lustre/Windows Capacity and Throughput"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-4.1.49 · FSx for Lustre/Windows Capacity and Throughput

## Description

FSx capacity and throughput metrics support HPC and Windows file share capacity planning and performance troubleshooting.

## Value

FSx capacity and throughput metrics support HPC and Windows file share capacity planning and performance troubleshooting.

## Implementation

Collect FSx metrics. Alert when free capacity is low. Monitor read/write throughput for Lustre; for Windows, track client connections and IOPS. Correlate with backup completion.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_aws`.
• Ensure the following data sources are available: CloudWatch FSx metrics (DataReadBytes, DataWriteBytes, FreeDataStorageCapacity).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Collect FSx metrics. Alert when free capacity is low. Monitor read/write throughput for Lustre; for Windows, track client connections and IOPS. Correlate with backup completion.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=aws sourcetype="aws:cloudwatch" namespace="AWS/FSx" metric_name="FreeDataStorageCapacity"
| timechart span=1d avg(Average) by FileSystemId
| eval free_gb = FreeDataStorageCapacity / 1024 / 1024 / 1024
| where free_gb < 100
```

Understanding this SPL

**FSx for Lustre/Windows Capacity and Throughput** — FSx capacity and throughput metrics support HPC and Windows file share capacity planning and performance troubleshooting.

Documented **Data sources**: CloudWatch FSx metrics (DataReadBytes, DataWriteBytes, FreeDataStorageCapacity). **App/TA** (typical add-on context): `Splunk_TA_aws`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: aws; **sourcetype**: aws:cloudwatch. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=aws, sourcetype="aws:cloudwatch". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `timechart` plots the metric over time using **span=1d** buckets with a separate series **by FileSystemId** — ideal for trending and alerting on this use case.
• `eval` defines or adjusts **free_gb** — often to normalize units, derive a ratio, or prepare for thresholds.
• Filters the current rows with `where free_gb < 100` — typically the threshold or rule expression for this monitoring goal.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Line chart (capacity, throughput by filesystem), Table (filesystem, free GB), Gauge (used %).

## SPL

```spl
index=aws sourcetype="aws:cloudwatch" namespace="AWS/FSx" metric_name="FreeDataStorageCapacity"
| timechart span=1d avg(Average) by FileSystemId
| eval free_gb = FreeDataStorageCapacity / 1024 / 1024 / 1024
| where free_gb < 100
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

Line chart (capacity, throughput by filesystem), Table (filesystem, free GB), Gauge (used %).

## References

- [Splunk_TA_aws](https://splunkbase.splunk.com/app/1876)
