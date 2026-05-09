<!-- AUTO-GENERATED from UC-5.5.21.json — DO NOT EDIT -->

---
id: "5.5.21"
title: "VMware VeloCloud Orchestrator Tunnel Health"
status: "community"
criticality: "critical"
splunkPillar: "Observability"
---

# UC-5.5.21 · VMware VeloCloud Orchestrator Tunnel Health

> **Criticality:** Critical &middot; **Difficulty:** Intermediate &middot; **Pillar:** Observability &middot; **Type:** Availability, Performance &middot; **Wave:** Crawl &middot; **Status:** Community

*We watch the network connections between branch offices and headquarters. When voice or video calls start sounding choppy because a link is dropping data or running slow, we catch it before the branch employees have to call the help desk.*

---

## Description

Polls the VMware VeloCloud Orchestrator API for per-link latency, jitter, and loss across the SD-WAN fabric, then aggregates by edge appliance and link. Surfaces transports whose receive-direction latency exceeds 100 ms, whose jitter crosses 30 ms, or whose loss climbs above 1% — the conventional thresholds that put real-time voice and video at risk.

## Value

VMware SD-WAN (VeloCloud) sits on the WAN edge for thousands of branch sites in retail, manufacturing, and logistics. Without orchestrator-side polling, branch outages depend on someone at the branch noticing — a 2-hour mean-time-to-detect that retail customers cannot accept on a sale day. This UC turns the orchestrator's own per-link telemetry into a Splunk-native alerting surface so the NOC sees the degradation before the branch staff do, and lets capacity planning trend WAN quality across the entire estate.

## Implementation

Configure a scripted input (Python or PowerShell) to poll the VeloCloud Orchestrator `/monitoring/aggregate/edge/link` endpoint at 5-minute intervals. Store the API key in `passwords.conf` (NEVER inline). Normalise the link-state enum (UP / DOWN / STANDBY) into a consistent value before alerting; the Orchestrator returns slightly different shapes depending on edge model and software version.

## SPL

```spl
index=sdwan sourcetype="velocloud:link"
| stats avg(latencyMsRx) as rx_latency, avg(latencyMsTx) as tx_latency, avg(jitterMsRx) as jitter, avg(lossPctRx) as loss_pct by edgeName, linkName
| where rx_latency > 100 OR jitter > 30 OR loss_pct > 1
| sort - rx_latency
```

## Visualization

Line chart (latency / jitter per edge over time), Table (top-N degraded links sorted by loss), Status grid (per-site link health, coloured red / amber / green).

## Known False Positives

**Cellular failover transports.** LTE / 5G backup transports legitimately run with much higher latency and jitter than fibre links, but the SD-WAN policy may already be steering away from them. Filter on `linkType` to avoid over-alerting on a transport whose role is to be the slow path.

**Saturday-night residential links.** Branches whose primary transport is a residential broadband line will see jitter and loss climb on Saturday evenings as the local ISP loads up. This is a capacity-planning signal, not an outage; aggregate over a 7-day window before raising the priority.

**Edge appliance reboots / upgrades.** Scheduled VeloCloud Edge reboots produce a brief tunnel-down + path-recovery sequence. Suppress alerts during announced maintenance windows.

## References

- [VMware SD-WAN documentation](https://docs.vmware.com/en/VMware-SD-WAN/index.html)
- [VeloCloud Orchestrator API reference](https://docs.vmware.com/en/VMware-SD-WAN/4.5/vmware-sd-wan-api-reference/GUID-D4FC6FAC-D053-4FE3-A09F-D5547BFD7CA5.html)
