---
id: "2.1.47"
title: "VM Network Packet Loss and Retransmit"
criticality: "high"
splunkPillar: "Security"
---

# UC-2.1.47 · VM Network Packet Loss and Retransmit

## Description

Per-VM network quality metrics including packet loss and retransmission. Dropped packets at the vNIC indicate congestion, driver issues, or misconfigured traffic shaping. Hypervisor-level counters capture drops invisible to the guest — essential for diagnosing application network issues.

## Value

Per-VM network quality metrics including packet loss and retransmission. Dropped packets at the vNIC indicate congestion, driver issues, or misconfigured traffic shaping. Hypervisor-level counters capture drops invisible to the guest — essential for diagnosing application network issues.

## Implementation

TA-vmware collects net.droppedRx/Tx.summation. Alert when any VM shows >0 dropped packets sustained over 5 minutes. Compute loss percentage when packet counters available. Correlate with net.usage.average for saturation. Check dvSwitch policies, physical NIC utilization, and VMXNET3 driver version.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_vmware`.
• Ensure the following data sources are available: `sourcetype=vmware:perf:net` (net.droppedRx.summation, net.droppedTx.summation).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
TA-vmware collects net.droppedRx/Tx.summation. Alert when any VM shows >0 dropped packets sustained over 5 minutes. Compute loss percentage when packet counters available. Correlate with net.usage.average for saturation. Check dvSwitch policies, physical NIC utilization, and VMXNET3 driver version.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=vmware sourcetype="vmware:perf:net" (counter="net.droppedRx.summation" OR counter="net.droppedTx.summation" OR counter="net.packetsRx.summation" OR counter="net.packetsTx.summation")
| stats sum(eval(if(counter="net.droppedRx.summation", Value, 0))) as dropped_rx, sum(eval(if(counter="net.droppedTx.summation", Value, 0))) as dropped_tx, sum(eval(if(counter="net.packetsRx.summation", Value, 0))) as packets_rx, sum(eval(if(counter="net.packetsTx.summation", Value, 0))) as packets_tx by vm_name, host
| eval total_packets = packets_rx + packets_tx
| eval loss_pct = if(total_packets > 0, round((dropped_rx + dropped_tx) / total_packets * 100, 4), 0)
| where dropped_rx > 0 OR dropped_tx > 0
| sort -dropped_rx
| table vm_name, host, dropped_rx, dropped_tx, total_packets, loss_pct
```

Understanding this SPL

**VM Network Packet Loss and Retransmit** — Per-VM network quality metrics including packet loss and retransmission. Dropped packets at the vNIC indicate congestion, driver issues, or misconfigured traffic shaping. Hypervisor-level counters capture drops invisible to the guest — essential for diagnosing application network issues.

Documented **Data sources**: `sourcetype=vmware:perf:net` (net.droppedRx.summation, net.droppedTx.summation). **App/TA** (typical add-on context): `Splunk_TA_vmware`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: vmware; **sourcetype**: vmware:perf:net. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=vmware, sourcetype="vmware:perf:net". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `stats` rolls up events into metrics; results are split **by vm_name, host** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• `eval` defines or adjusts **total_packets** — often to normalize units, derive a ratio, or prepare for thresholds.
• `eval` defines or adjusts **loss_pct** — often to normalize units, derive a ratio, or prepare for thresholds.
• Filters the current rows with `where dropped_rx > 0 OR dropped_tx > 0` — typically the threshold or rule expression for this monitoring goal.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.
• Pipeline stage (see **VM Network Packet Loss and Retransmit**): table vm_name, host, dropped_rx, dropped_tx, total_packets, loss_pct


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (VM, host, drops, loss %), Line chart (drops over time), Bar chart (top VMs by packet loss).

## SPL

```spl
index=vmware sourcetype="vmware:perf:net" (counter="net.droppedRx.summation" OR counter="net.droppedTx.summation" OR counter="net.packetsRx.summation" OR counter="net.packetsTx.summation")
| stats sum(eval(if(counter="net.droppedRx.summation", Value, 0))) as dropped_rx, sum(eval(if(counter="net.droppedTx.summation", Value, 0))) as dropped_tx, sum(eval(if(counter="net.packetsRx.summation", Value, 0))) as packets_rx, sum(eval(if(counter="net.packetsTx.summation", Value, 0))) as packets_tx by vm_name, host
| eval total_packets = packets_rx + packets_tx
| eval loss_pct = if(total_packets > 0, round((dropped_rx + dropped_tx) / total_packets * 100, 4), 0)
| where dropped_rx > 0 OR dropped_tx > 0
| sort -dropped_rx
| table vm_name, host, dropped_rx, dropped_tx, total_packets, loss_pct
```

## Visualization

Table (VM, host, drops, loss %), Line chart (drops over time), Bar chart (top VMs by packet loss).

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
