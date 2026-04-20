---
id: "2.1.16"
title: "VM Network I/O and Dropped Packets"
criticality: "high"
splunkPillar: "Security"
---

# UC-2.1.16 · VM Network I/O and Dropped Packets

## Description

Dropped packets at the vNIC level indicate network saturation, driver issues, or misconfigured traffic shaping policies. Unlike guest OS network stats, hypervisor-level counters capture drops the VM never sees — making this the only reliable way to detect silent packet loss that degrades application performance.

## Value

Dropped packets at the vNIC level indicate network saturation, driver issues, or misconfigured traffic shaping policies. Unlike guest OS network stats, hypervisor-level counters capture drops the VM never sees — making this the only reliable way to detect silent packet loss that degrades application performance.

## Implementation

Collected via Splunk_TA_vmware performance counters. Alert when any VM shows >0 dropped packets sustained over 5 minutes. Correlate with VM network usage to determine if drops correlate with saturation. Check dvSwitch traffic shaping policies and physical NIC utilization on the host.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_vmware`.
• Ensure the following data sources are available: `sourcetype=vmware:perf:net`, vCenter network performance metrics.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Collected via Splunk_TA_vmware performance counters. Alert when any VM shows >0 dropped packets sustained over 5 minutes. Correlate with VM network usage to determine if drops correlate with saturation. Check dvSwitch traffic shaping policies and physical NIC utilization on the host.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=vmware sourcetype="vmware:perf:net" (counter="net.droppedRx.summation" OR counter="net.droppedTx.summation" OR counter="net.usage.average")
| stats sum(eval(if(counter="net.droppedRx.summation", Value, 0))) as dropped_rx, sum(eval(if(counter="net.droppedTx.summation", Value, 0))) as dropped_tx, avg(eval(if(counter="net.usage.average", Value, 0))) as avg_kbps by host, vm_name
| where dropped_rx > 0 OR dropped_tx > 0
| sort -dropped_rx
| table vm_name, host, avg_kbps, dropped_rx, dropped_tx
```

Understanding this SPL

**VM Network I/O and Dropped Packets** — Dropped packets at the vNIC level indicate network saturation, driver issues, or misconfigured traffic shaping policies. Unlike guest OS network stats, hypervisor-level counters capture drops the VM never sees — making this the only reliable way to detect silent packet loss that degrades application performance.

Documented **Data sources**: `sourcetype=vmware:perf:net`, vCenter network performance metrics. **App/TA** (typical add-on context): `Splunk_TA_vmware`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: vmware; **sourcetype**: vmware:perf:net. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=vmware, sourcetype="vmware:perf:net". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `stats` rolls up events into metrics; results are split **by host, vm_name** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• Filters the current rows with `where dropped_rx > 0 OR dropped_tx > 0` — typically the threshold or rule expression for this monitoring goal.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.
• Pipeline stage (see **VM Network I/O and Dropped Packets**): table vm_name, host, avg_kbps, dropped_rx, dropped_tx


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (VM, host, throughput, drops), Line chart (drops over time), Bar chart (top VMs by drops).

## SPL

```spl
index=vmware sourcetype="vmware:perf:net" (counter="net.droppedRx.summation" OR counter="net.droppedTx.summation" OR counter="net.usage.average")
| stats sum(eval(if(counter="net.droppedRx.summation", Value, 0))) as dropped_rx, sum(eval(if(counter="net.droppedTx.summation", Value, 0))) as dropped_tx, avg(eval(if(counter="net.usage.average", Value, 0))) as avg_kbps by host, vm_name
| where dropped_rx > 0 OR dropped_tx > 0
| sort -dropped_rx
| table vm_name, host, avg_kbps, dropped_rx, dropped_tx
```

## Visualization

Table (VM, host, throughput, drops), Line chart (drops over time), Bar chart (top VMs by drops).

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
