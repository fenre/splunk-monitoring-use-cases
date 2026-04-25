<!-- AUTO-GENERATED from UC-2.1.43.json — DO NOT EDIT -->

---
id: "2.1.43"
title: "VM Disk I/O Latency per Datastore"
criticality: "high"
splunkPillar: "Observability"
---

# UC-2.1.43 · VM Disk I/O Latency per Datastore

## Description

Correlate VM disk latency to specific datastores to identify storage bottlenecks. When multiple VMs on the same datastore show high latency, the datastore or underlying storage is the culprit rather than individual VM workload.

## Value

Correlate VM disk latency to specific datastores to identify storage bottlenecks. When multiple VMs on the same datastore show high latency, the datastore or underlying storage is the culprit rather than individual VM workload.

## Implementation

Splunk_TA_vmware collects per-VM disk latency. Use datastore dimension to group VMs by backing storage. Alert when any VM-datastore pair exceeds 20ms average latency over 10 minutes. Correlate with datastore-level latency (UC-2.1.4) to distinguish VM workload from shared storage contention.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_vmware`.
• Ensure the following data sources are available: `sourcetype=vmware:perf:datastore` (datastore.totalReadLatency.average, datastore.totalWriteLatency.average — per VM when object is VM).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Splunk_TA_vmware collects per-VM disk latency. Use datastore dimension to group VMs by backing storage. Alert when any VM-datastore pair exceeds 20ms average latency over 10 minutes. Correlate with datastore-level latency (UC-2.1.4) to distinguish VM workload from shared storage contention.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=vmware sourcetype="vmware:perf:datastore" (counter="datastore.totalReadLatency.average" OR counter="datastore.totalWriteLatency.average")
| eval read_latency = if(counter="datastore.totalReadLatency.average", Value, null())
| eval write_latency = if(counter="datastore.totalWriteLatency.average", Value, null())
| stats avg(read_latency) as avg_read_ms, avg(write_latency) as avg_write_ms by vm_name, host, datastore
| eval avg_latency = max(coalesce(avg_read_ms, 0), coalesce(avg_write_ms, 0))
| where avg_latency > 20
| sort -avg_latency
| table vm_name, host, datastore, avg_read_ms, avg_write_ms, avg_latency
```

Understanding this SPL

**VM Disk I/O Latency per Datastore** — Correlate VM disk latency to specific datastores to identify storage bottlenecks. When multiple VMs on the same datastore show high latency, the datastore or underlying storage is the culprit rather than individual VM workload.

Documented **Data sources**: `sourcetype=vmware:perf:datastore` (datastore.totalReadLatency.average, datastore.totalWriteLatency.average — per VM when object is VM). **App/TA** (typical add-on context): `Splunk_TA_vmware`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: vmware; **sourcetype**: vmware:perf:datastore. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=vmware, sourcetype="vmware:perf:datastore". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `eval` defines or adjusts **read_latency** — often to normalize units, derive a ratio, or prepare for thresholds.
• `eval` defines or adjusts **write_latency** — often to normalize units, derive a ratio, or prepare for thresholds.
• `stats` rolls up events into metrics; results are split **by vm_name, host, datastore** so each row reflects one combination of those dimensions.
• `eval` defines or adjusts **avg_latency** — often to normalize units, derive a ratio, or prepare for thresholds.
• Filters the current rows with `where avg_latency > 20` — typically the threshold or rule expression for this monitoring goal.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.
• Pipeline stage (see **VM Disk I/O Latency per Datastore**): table vm_name, host, datastore, avg_read_ms, avg_write_ms, avg_latency

Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Heatmap (VMs vs datastores, colored by latency), Table (top latency by VM/datastore), Line chart (latency trend per datastore).

## SPL

```spl
index=vmware sourcetype="vmware:perf:datastore" (counter="datastore.totalReadLatency.average" OR counter="datastore.totalWriteLatency.average")
| eval read_latency = if(counter="datastore.totalReadLatency.average", Value, null())
| eval write_latency = if(counter="datastore.totalWriteLatency.average", Value, null())
| stats avg(read_latency) as avg_read_ms, avg(write_latency) as avg_write_ms by vm_name, host, datastore
| eval avg_latency = max(coalesce(avg_read_ms, 0), coalesce(avg_write_ms, 0))
| where avg_latency > 20
| sort -avg_latency
| table vm_name, host, datastore, avg_read_ms, avg_write_ms, avg_latency
```

## Visualization

Heatmap (VMs vs datastores, colored by latency), Table (top latency by VM/datastore), Line chart (latency trend per datastore).

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
