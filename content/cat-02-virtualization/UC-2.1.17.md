<!-- AUTO-GENERATED from UC-2.1.17.json — DO NOT EDIT -->

---
id: "2.1.17"
title: "VM Disk IOPS Trending and Throttling"
criticality: "high"
splunkPillar: "Observability"
---

# UC-2.1.17 · VM Disk IOPS Trending and Throttling

## Description

Tracks read/write IOPS per VM to identify storage-hungry workloads before they impact other VMs on the same datastore. When Storage I/O Control (SIOC) throttles a VM, it appears as increased latency inside the guest — this use case exposes the throttling at the hypervisor level.

## Value

Tracks read/write IOPS per VM to identify storage-hungry workloads before they impact other VMs on the same datastore. When Storage I/O Control (SIOC) throttles a VM, it appears as increased latency inside the guest — this use case exposes the throttling at the hypervisor level.

## Implementation

Collected via Splunk_TA_vmware. Baseline per-VM IOPS over 7 days. Alert when a VM exceeds 2x its baseline sustained for 15 minutes. Track SIOC injector latency counters to detect throttling. Correlate high-IOPS VMs with datastore latency spikes from UC-2.1.4.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_vmware`.
• Ensure the following data sources are available: `sourcetype=vmware:perf:datastore`, vCenter disk performance metrics.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Collected via Splunk_TA_vmware. Baseline per-VM IOPS over 7 days. Alert when a VM exceeds 2x its baseline sustained for 15 minutes. Track SIOC injector latency counters to detect throttling. Correlate high-IOPS VMs with datastore latency spikes from UC-2.1.4.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=vmware sourcetype="vmware:perf:datastore" (counter="datastore.numberReadAveraged.average" OR counter="datastore.numberWriteAveraged.average")
| eval metric=case(counter="datastore.numberReadAveraged.average", "read_iops", counter="datastore.numberWriteAveraged.average", "write_iops")
| stats avg(Value) as avg_val by vm_name, host, datastore, metric
| eval avg_val=round(avg_val, 0)
| stats sum(avg_val) as total_iops, values(eval(metric . "=" . avg_val)) as breakdown by vm_name, host, datastore
| where total_iops > 500
| sort -total_iops
| table vm_name, host, datastore, total_iops, breakdown
```

Understanding this SPL

**VM Disk IOPS Trending and Throttling** — Tracks read/write IOPS per VM to identify storage-hungry workloads before they impact other VMs on the same datastore. When Storage I/O Control (SIOC) throttles a VM, it appears as increased latency inside the guest — this use case exposes the throttling at the hypervisor level.

Documented **Data sources**: `sourcetype=vmware:perf:datastore`, vCenter disk performance metrics. **App/TA** (typical add-on context): `Splunk_TA_vmware`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: vmware; **sourcetype**: vmware:perf:datastore. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=vmware, sourcetype="vmware:perf:datastore". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `eval` defines or adjusts **metric** — often to normalize units, derive a ratio, or prepare for thresholds.
• `stats` rolls up events into metrics; results are split **by vm_name, host, datastore, metric** so each row reflects one combination of those dimensions.
• `eval` defines or adjusts **avg_val** — often to normalize units, derive a ratio, or prepare for thresholds.
• `stats` rolls up events into metrics; results are split **by vm_name, host, datastore** so each row reflects one combination of those dimensions.
• Filters the current rows with `where total_iops > 500` — typically the threshold or rule expression for this monitoring goal.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.
• Pipeline stage (see **VM Disk IOPS Trending and Throttling**): table vm_name, host, datastore, total_iops, breakdown

Optional CIM / accelerated variant (same use case, normalized fields via Common Information Model):

```spl
| tstats `summariesonly` sum(Performance.read_ops) as read_ops sum(Performance.write_ops) as write_ops
  from datamodel=Performance where nodename=Performance.Storage
  by Performance.host Performance.mount span=15m
| eval total_iops=read_ops + write_ops
| where total_iops > 500
```

Understanding this CIM / accelerated SPL

**VM Disk IOPS Trending and Throttling** — Tracks read/write IOPS per VM to identify storage-hungry workloads before they impact other VMs on the same datastore. When Storage I/O Control (SIOC) throttles a VM, it appears as increased latency inside the guest — this use case exposes the throttling at the hypervisor level.

Documented **Data sources**: `sourcetype=vmware:perf:datastore`, vCenter disk performance metrics. **App/TA** (typical add-on context): `Splunk_TA_vmware`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

This **CIM or accelerated** block uses normalized field names and/or `tstats` over data models. Enable **acceleration** on the referenced models (and correct CIM knowledge objects) or the search may return nothing.

**Pipeline walkthrough**

• Uses `tstats` against accelerated summaries for data model `Performance` — enable acceleration for that model.
• `eval` defines or adjusts **total_iops** — often to normalize units, derive a ratio, or prepare for thresholds.
• Filters the current rows with `where total_iops > 500` — typically the threshold or rule expression for this monitoring goal.

Enable Data Model Acceleration (and metric indexes for `mstats`) for the models or datasets referenced above; otherwise `tstats`/`mstats` may return no results from summaries.

Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Line chart (IOPS per VM over time), Stacked bar chart (read vs write), Table (top IOPS consumers).

## SPL

```spl
index=vmware sourcetype="vmware:perf:datastore" (counter="datastore.numberReadAveraged.average" OR counter="datastore.numberWriteAveraged.average")
| eval metric=case(counter="datastore.numberReadAveraged.average", "read_iops", counter="datastore.numberWriteAveraged.average", "write_iops")
| stats avg(Value) as avg_val by vm_name, host, datastore, metric
| eval avg_val=round(avg_val, 0)
| stats sum(avg_val) as total_iops, values(eval(metric . "=" . avg_val)) as breakdown by vm_name, host, datastore
| where total_iops > 500
| sort -total_iops
| table vm_name, host, datastore, total_iops, breakdown
```

## CIM SPL

```spl
| tstats `summariesonly` sum(Performance.read_ops) as read_ops sum(Performance.write_ops) as write_ops
  from datamodel=Performance where nodename=Performance.Storage
  by Performance.host Performance.mount span=15m
| eval total_iops=read_ops + write_ops
| where total_iops > 500
```

## Visualization

Line chart (IOPS per VM over time), Stacked bar chart (read vs write), Table (top IOPS consumers).

## References

- [CIM: Performance](https://docs.splunk.com/Documentation/CIM/latest/User/Performance)
