<!-- AUTO-GENERATED from UC-6.1.18.json — DO NOT EDIT -->

---
id: "6.1.18"
title: "NetApp ONTAP Performance Counters"
criticality: "high"
splunkPillar: "Observability"
---

# UC-6.1.18 · NetApp ONTAP Performance Counters

## Description

Counter-based throughput, latency, and queue depth from ONTAP complement volume-level views. Trending counters catches node or aggregate saturation before user-visible latency spikes.

## Value

Counter-based throughput, latency, and queue depth from ONTAP complement volume-level views. Trending counters catches node or aggregate saturation before user-visible latency spikes.

## Implementation

Enable performance counter polling (15m) for volumes/LUNs. Map instance to SVM and export. Baseline p95 latency and IOPS; alert on sustained deviation from baseline.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `TA-netapp_ontap`, REST API scripted input.
• Ensure the following data sources are available: ONTAP REST `/api/cluster/counter/tables/*` or ZAPI `perf-object-get-list`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Enable performance counter polling (15m) for volumes/LUNs. Map instance to SVM and export. Baseline p95 latency and IOPS; alert on sustained deviation from baseline.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=storage sourcetype="netapp:ontap:counter"
| where object_name="volume" OR object_name="lun"
| timechart span=5m avg(read_latency) as read_ms, avg(write_latency) as write_ms, avg(total_ops) as iops by instance_name
| where read_ms > 15 OR write_ms > 15
```

Understanding this SPL

**NetApp ONTAP Performance Counters** — Counter-based throughput, latency, and queue depth from ONTAP complement volume-level views. Trending counters catches node or aggregate saturation before user-visible latency spikes.

Documented **Data sources**: ONTAP REST `/api/cluster/counter/tables/*` or ZAPI `perf-object-get-list`. **App/TA** (typical add-on context): `TA-netapp_ontap`, REST API scripted input. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: storage; **sourcetype**: netapp:ontap:counter. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=storage, sourcetype="netapp:ontap:counter". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Filters the current rows with `where object_name="volume" OR object_name="lun"` — typically the threshold or rule expression for this monitoring goal.
• `timechart` plots the metric over time using **span=5m** buckets with a separate series **by instance_name** — ideal for trending and alerting on this use case.
• Filters the current rows with `where read_ms > 15 OR write_ms > 15` — typically the threshold or rule expression for this monitoring goal.


Step 3 — Validate
Compare volume, aggregate, or SnapMirror state with NetApp ONTAP System Manager, the ONTAP CLI, or NetApp Active IQ Unified Manager for the same object and interval.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Point on-call to the ONTAP or array runbook, Cisco SAN references, and SNMP/REST credentials already used in production—not generic platform steps only. Consider visualizations: Line chart (latency and IOPS by object), Table (top latency contributors), Single value (max read/write ms).

## SPL

```spl
index=storage sourcetype="netapp:ontap:counter"
| where object_name="volume" OR object_name="lun"
| timechart span=5m avg(read_latency) as read_ms, avg(write_latency) as write_ms, avg(total_ops) as iops by instance_name
| where read_ms > 15 OR write_ms > 15
```

## Visualization

Line chart (latency and IOPS by object), Table (top latency contributors), Single value (max read/write ms).

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
