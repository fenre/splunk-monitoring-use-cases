<!-- AUTO-GENERATED from UC-6.1.23.json — DO NOT EDIT -->

---
id: "6.1.23"
title: "LUN Latency Trending"
criticality: "critical"
splunkPillar: "Observability"
---

# UC-6.1.23 · LUN Latency Trending

## Description

Per-LUN latency separates noisy neighbors and misaligned workloads from array-wide issues. Supports QoS and datastore placement decisions.

## Value

Per-LUN latency separates noisy neighbors and misaligned workloads from array-wide issues. Supports QoS and datastore placement decisions.

## Implementation

Ingest per-LUN latency at 5m granularity. Set SLA thresholds (e.g., p95 >20ms). Split by workload tier. Correlate with IOPS saturation.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: Vendor TA, VMware vSphere performance (if LUN mapped).
• Ensure the following data sources are available: Array LUN performance API, VMware `disk.latency` per datastore.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Ingest per-LUN latency at 5m granularity. Set SLA thresholds (e.g., p95 >20ms). Split by workload tier. Correlate with IOPS saturation.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=storage sourcetype="storage:lun_perf"
| timechart span=5m perc95(read_latency_ms) as p95_read, perc95(write_latency_ms) as p95_write by lun_id, array_name
| where p95_read > 20 OR p95_write > 20
```

Understanding this SPL

**LUN Latency Trending** — Per-LUN latency separates noisy neighbors and misaligned workloads from array-wide issues. Supports QoS and datastore placement decisions.

Documented **Data sources**: Array LUN performance API, VMware `disk.latency` per datastore. **App/TA** (typical add-on context): Vendor TA, VMware vSphere performance (if LUN mapped). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: storage; **sourcetype**: storage:lun_perf. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=storage, sourcetype="storage:lun_perf". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `timechart` plots the metric over time using **span=5m** buckets with a separate series **by lun_id, array_name** — ideal for trending and alerting on this use case.
• Filters the current rows with `where p95_read > 20 OR p95_write > 20` — typically the threshold or rule expression for this monitoring goal.


Step 3 — Validate
Compare the same metric, object name, and interval in the vendor or cloud console (array, backup, or object store) that is the source of truth for this feed.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Point on-call to the ONTAP or array runbook, Cisco SAN references, and SNMP/REST credentials already used in production—not generic platform steps only. Consider visualizations: Line chart (p95 read/write per LUN), Heatmap (LUN × hour), Table (worst LUNs).

## SPL

```spl
index=storage sourcetype="storage:lun_perf"
| timechart span=5m perc95(read_latency_ms) as p95_read, perc95(write_latency_ms) as p95_write by lun_id, array_name
| where p95_read > 20 OR p95_write > 20
```

## Visualization

Line chart (p95 read/write per LUN), Heatmap (LUN × hour), Table (worst LUNs).

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
