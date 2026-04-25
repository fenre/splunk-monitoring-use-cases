<!-- AUTO-GENERATED from UC-5.11.7.json — DO NOT EDIT -->

---
id: "5.11.7"
title: "LLDP Topology Change Detection"
criticality: "medium"
splunkPillar: "Security"
---

# UC-5.11.7 · LLDP Topology Change Detection

## Description

In a properly cabled data center, the LLDP neighbor table should not change unless someone moves a cable, adds a device, or swaps a switch. gNMI ON_CHANGE subscriptions to `/lldp/interfaces/interface/neighbors` provide instant notification of topology drift — a new neighbor appearing on a spine port, a missing neighbor on a leaf uplink, or an unauthorized device connected to a reserved port.

## Value

In a properly cabled data center, the LLDP neighbor table should not change unless someone moves a cable, adds a device, or swaps a switch. gNMI ON_CHANGE subscriptions to `/lldp/interfaces/interface/neighbors` provide instant notification of topology drift — a new neighbor appearing on a spine port, a missing neighbor on a leaf uplink, or an unauthorized device connected to a reserved port.

## Implementation

Subscribe to `/lldp/interfaces/interface/neighbors` using ON_CHANGE mode. Build a baseline LLDP topology table as a lookup (host, interface, expected_neighbor). Alert on any deviation from baseline. In data centers, unexpected LLDP changes often indicate cabling errors during maintenance. In campus networks, new neighbors on access ports may indicate unauthorized switches.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: Telegraf (`inputs.gnmi` plugin) → Splunk HEC.
• Ensure the following data sources are available: gNMI path: `/lldp/interfaces/interface/neighbors/neighbor/state` (ON_CHANGE); Telegraf metric: `openconfig_lldp`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Subscribe to `/lldp/interfaces/interface/neighbors` using ON_CHANGE mode. Build a baseline LLDP topology table as a lookup (host, interface, expected_neighbor). Alert on any deviation from baseline. In data centers, unexpected LLDP changes often indicate cabling errors during maintenance. In campus networks, new neighbors on access ports may indicate unauthorized switches.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
| mstats latest("openconfig_lldp.neighbor_system_name") AS neighbor WHERE index=gnmi_metrics BY host, name span=5m
| streamstats current=f last(neighbor) AS prev_neighbor by host, name
| where neighbor != prev_neighbor AND isnotnull(prev_neighbor)
| table _time, host, name, prev_neighbor, neighbor
| eval change_type=if(isnotnull(neighbor) AND isnull(prev_neighbor), "NEW", if(isnull(neighbor) AND isnotnull(prev_neighbor), "REMOVED", "CHANGED"))
```

Understanding this SPL

**LLDP Topology Change Detection** — In a properly cabled data center, the LLDP neighbor table should not change unless someone moves a cable, adds a device, or swaps a switch. gNMI ON_CHANGE subscriptions to `/lldp/interfaces/interface/neighbors` provide instant notification of topology drift — a new neighbor appearing on a spine port, a missing neighbor on a leaf uplink, or an unauthorized device connected to a reserved port.

Documented **Data sources**: gNMI path: `/lldp/interfaces/interface/neighbors/neighbor/state` (ON_CHANGE); Telegraf metric: `openconfig_lldp`. **App/TA** (typical add-on context): Telegraf (`inputs.gnmi` plugin) → Splunk HEC. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: gnmi_metrics.

**Pipeline walkthrough**

• Uses `mstats` to query metrics indexes (pre-aggregated metric data).
• `streamstats` rolls up events into metrics; results are split **by host, name** so each row reflects one combination of those dimensions.
• Filters the current rows with `where neighbor != prev_neighbor AND isnotnull(prev_neighbor)` — typically the threshold or rule expression for this monitoring goal.
• Pipeline stage (see **LLDP Topology Change Detection**): table _time, host, name, prev_neighbor, neighbor
• `eval` defines or adjusts **change_type** — often to normalize units, derive a ratio, or prepare for thresholds.


Step 3 — Validate
After a test cable move, confirm LLDP neighbor change appears in `mstats` and in `show lldp` within the same time bucket; use change tickets to rule out false moves.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Network topology map (overlay LLDP changes), Table (recent topology changes), Status grid (ports with unexpected neighbors).

## SPL

```spl
| mstats latest("openconfig_lldp.neighbor_system_name") AS neighbor WHERE index=gnmi_metrics BY host, name span=5m
| streamstats current=f last(neighbor) AS prev_neighbor by host, name
| where neighbor != prev_neighbor AND isnotnull(prev_neighbor)
| table _time, host, name, prev_neighbor, neighbor
| eval change_type=if(isnotnull(neighbor) AND isnull(prev_neighbor), "NEW", if(isnull(neighbor) AND isnotnull(prev_neighbor), "REMOVED", "CHANGED"))
```

## Visualization

Network topology map (overlay LLDP changes), Table (recent topology changes), Status grid (ports with unexpected neighbors).

## References

- [CIM: Change](https://docs.splunk.com/Documentation/CIM/latest/User/Change)
