<!-- AUTO-GENERATED from UC-4.2.57.json — DO NOT EDIT -->

---
id: "4.2.57"
title: "Azure Managed Disk Performance Throttling"
criticality: "high"
splunkPillar: "Observability"
---

# UC-4.2.57 · Azure Managed Disk Performance Throttling

## Description

Azure managed disks have IOPS and throughput caps based on tier and size. When VMs hit these limits, disk I/O is throttled, causing application slowdowns that are hard to diagnose without platform metrics.

## Value

Azure managed disks have IOPS and throughput caps based on tier and size. When VMs hit these limits, disk I/O is throttled, causing application slowdowns that are hard to diagnose without platform metrics.

## Implementation

Collect Azure Monitor metrics for managed disks. Monitor `Composite Disk Read/Write IOPS` against the disk SKU IOPS limit and `Composite Disk Read/Write Bytes/sec` against the throughput limit. For burstable disks, track `BurstIOCreditsConsumedPercentage` — when credits exhaust, performance drops to baseline. Alert when consumption exceeds 90% of provisioned capacity sustained over 15 minutes.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_microsoft-cloudservices` (Azure Monitor metrics).
• Ensure the following data sources are available: `sourcetype=azure:monitor:metric` (Microsoft.Compute/disks).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Collect Azure Monitor metrics for managed disks. Monitor `Composite Disk Read/Write IOPS` against the disk SKU IOPS limit and `Composite Disk Read/Write Bytes/sec` against the throughput limit. For burstable disks, track `BurstIOCreditsConsumedPercentage` — when credits exhaust, performance drops to baseline. Alert when consumption exceeds 90% of provisioned capacity sustained over 15 minutes.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=cloud sourcetype="azure:monitor:metric" resource_type="microsoft.compute/disks"
| where metric_name IN ("DiskIOPSReadWrite","DiskMBpsReadWrite","BurstIOCreditsConsumedPercentage")
| timechart span=5m avg(average) as value by metric_name, resource_name
```

Understanding this SPL

**Azure Managed Disk Performance Throttling** — Azure managed disks have IOPS and throughput caps based on tier and size. When VMs hit these limits, disk I/O is throttled, causing application slowdowns that are hard to diagnose without platform metrics.

Documented **Data sources**: `sourcetype=azure:monitor:metric` (Microsoft.Compute/disks). **App/TA** (typical add-on context): `Splunk_TA_microsoft-cloudservices` (Azure Monitor metrics). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: cloud; **sourcetype**: azure:monitor:metric. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=cloud, sourcetype="azure:monitor:metric". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Filters the current rows with `where metric_name IN ("DiskIOPSReadWrite","DiskMBpsReadWrite","BurstIOCreditsConsumedPercentage")` — typically the threshold or rule expression for this monitoring goal.
• `timechart` plots the metric over time using **span=5m** buckets with a separate series **by metric_name, resource_name** — ideal for trending and alerting on this use case.

Optional CIM / accelerated variant (same use case, normalized fields via Common Information Model):

```spl
| tstats `summariesonly` avg(Performance.storage_free_percent) as free_pct
  from datamodel=Performance where nodename=Performance.Storage
  by Performance.host span=1h
| sort 10 free_pct
```

Understanding this CIM / accelerated SPL

**Azure Managed Disk Performance Throttling** — Azure managed disks have IOPS and throughput caps based on tier and size.

If you map cloud vendor fields into the CIM, this variant uses normalized names and `tstats` on accelerated models. The raw vendor search in Step 2 is still the first stop for troubleshooting.

**Pipeline walkthrough**

• Uses `tstats` on the `Performance` data model (Storage node)—enable that model in Data Models and the CIM add-on, or the search may return no rows.

• Uses `sort` to rank results; add `head` to limit the table.

Enable Data Model Acceleration (and the right field aliases) for the models or datasets above; otherwise `tstats` may not find summaries.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Gauge (IOPS vs. limit), Line chart (throughput and burst credits), Table (disks hitting limits).

## SPL

```spl
index=cloud sourcetype="azure:monitor:metric" resource_type="microsoft.compute/disks"
| where metric_name IN ("DiskIOPSReadWrite","DiskMBpsReadWrite","BurstIOCreditsConsumedPercentage")
| timechart span=5m avg(average) as value by metric_name, resource_name
```

## CIM SPL

```spl
| tstats `summariesonly` avg(Performance.storage_free_percent) as free_pct
  from datamodel=Performance where nodename=Performance.Storage
  by Performance.host span=1h
| sort 10 free_pct
```

## Visualization

Gauge (IOPS vs. limit), Line chart (throughput and burst credits), Table (disks hitting limits).

## References

- [Splunk_TA_microsoft-cloudservices](https://splunkbase.splunk.com/app/3110)
- [Splunk Add-on for Google Cloud Platform](https://splunkbase.splunk.com/app/3088)
- [CIM: Performance](https://docs.splunk.com/Documentation/CIM/latest/User/Performance)
