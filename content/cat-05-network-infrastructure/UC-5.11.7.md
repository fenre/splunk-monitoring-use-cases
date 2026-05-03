<!-- AUTO-GENERATED from UC-5.11.7.json — DO NOT EDIT -->

---
id: "5.11.7"
title: "LLDP Topology Change Detection"
criticality: "medium"
splunkPillar: "Security"
---

# UC-5.11.7 · LLDP Topology Change Detection

> **Criticality:** Medium &middot; **Difficulty:** Beginner &middot; **Pillar:** Security &middot; **Type:** Change, Inventory

*We help you notice when a neighbor on a port changes without a work order, which can be a simple unplug—or something connected that should not be there.*

---

## Description

In a properly cabled data center, the LLDP neighbor table should not change unless someone moves a cable, adds a device, or swaps a switch. gNMI ON_CHANGE subscriptions to `/lldp/interfaces/interface/neighbors` provide instant notification of topology drift — a new neighbor appearing on a spine port, a missing neighbor on a leaf uplink, or an unauthorized device connected to a reserved port.

## Value

Network operations teams detect physical topology changes in real time via LLDP streaming, catching cable moves, missing connections, and unauthorized devices before they impact network services.

## Implementation

Subscribe to `/lldp/interfaces/interface/neighbors` using ON_CHANGE mode. Build a baseline LLDP topology table as a lookup (host, interface, expected_neighbor). Alert on any deviation from baseline. In data centers, unexpected LLDP changes often indicate cabling errors during maintenance. In campus networks, new neighbors on access ports may indicate unauthorized switches.

## Detailed Implementation

### Prerequisites
- Telegraf gNMI collector with ON_CHANGE subscription to LLDP neighbor state. OpenConfig path: `/lldp/interfaces/interface/neighbors/neighbor/state`. Key fields: `system-name`, `system-description`, `port-id`, `port-description`, `management-address`, `chassis-id`. ON_CHANGE mode delivers updates only when a neighbor changes (appears, disappears, or modifies).
- LLDP (Link Layer Discovery Protocol) provides Layer 2 topology information — which device is physically connected to which port. Changes in LLDP neighbors indicate: (a) cable moves, (b) device additions/removals, (c) unauthorized devices connecting, (d) accidental cable changes during maintenance. In data center fabrics, an unexpected LLDP change can indicate a miswiring that causes traffic loops or partitions.
- Build a `lldp_expected_topology.csv` baseline: `host,name,expected_neighbor,expected_port` (e.g., `leaf-01,Ethernet1/49,spine-01,Ethernet1/1`). This represents the "golden" physical topology.
- ON_CHANGE support for LLDP: Arista EOS (supported), Cisco NX-OS (supported via DME streaming), Juniper (supported), Nokia SR Linux (supported). If ON_CHANGE is not supported, use SAMPLE with 60s interval as a fallback.

### Step 1 — Configure data collection
Telegraf subscription:
```toml
[[inputs.gnmi.subscription]]
  name = "openconfig_lldp"
  origin = "openconfig"
  path = "/lldp/interfaces/interface/neighbors/neighbor/state"
  subscription_mode = "on_change"
```

Verify LLDP data:
```spl
| mstats latest("openconfig_lldp.system_name") AS neighbor WHERE index=gnmi_metrics BY host, name span=5m
| stats count by host
```

### Step 2 — Create the search and alert

**Primary search — LLDP topology mismatch detection:**
```spl
| mstats latest("openconfig_lldp.system_name") AS current_neighbor latest("openconfig_lldp.port_id") AS current_port WHERE index=gnmi_metrics BY host, name
| lookup lldp_expected_topology.csv host name OUTPUT expected_neighbor expected_port
| eval neighbor_match=if(current_neighbor==expected_neighbor, "match", "MISMATCH")
| eval port_match=if(current_port==expected_port, "match", "MISMATCH")
| where neighbor_match="MISMATCH" OR port_match="MISMATCH" OR isnull(expected_neighbor)
| eval issue_type=case(isnull(expected_neighbor) AND isnotnull(current_neighbor), "New/Unknown connection", isnull(current_neighbor) AND isnotnull(expected_neighbor), "Expected neighbor MISSING", neighbor_match="MISMATCH", "Wrong neighbor (cable moved?)", port_match="MISMATCH", "Wrong port on correct neighbor", 1==1, "Unknown")
| sort issue_type
```

#### Understanding this SPL: Compares current LLDP neighbors against the expected topology baseline. A `MISMATCH` in neighbor means a cable was moved to a different device. A `MISMATCH` in port means the cable was moved to a different port on the same device. A "New/Unknown" connection means a device appeared that's not in the baseline — could be an authorized new deployment or an unauthorized device. A "Missing" neighbor means a previously connected device is no longer detected — possible cable pull or device failure.

**LLDP neighbor disappearance detection (link down):**
```spl
| mstats latest("openconfig_lldp.system_name") AS neighbor WHERE index=gnmi_metrics BY host, name span=1m earliest=-1h
| where isnull(neighbor) OR neighbor=""
| lookup lldp_expected_topology.csv host name OUTPUT expected_neighbor
| where isnotnull(expected_neighbor)
| eval alert_msg="Expected neighbor ".expected_neighbor." MISSING on ".host.":".name
| sort host, name
```

**Topology change timeline:**
```spl
| mstats latest("openconfig_lldp.system_name") AS neighbor WHERE index=gnmi_metrics BY host, name span=5m earliest=-24h
| streamstats window=2 current=f last(neighbor) AS prev_neighbor by host, name
| where neighbor!=prev_neighbor AND isnotnull(prev_neighbor)
| eval change=prev_neighbor." -> ".neighbor
| table _time, host, name, prev_neighbor, neighbor, change
| sort -_time
```

### Step 3 — Validate
(a) On the device, check LLDP neighbors: `show lldp neighbors detail` (Cisco/Arista) or `show lldp neighbor` (Juniper). Compare with the `mstats` output.
(b) Test: disconnect a cable between two devices and verify the LLDP disappearance alert fires within 2 minutes (LLDP hold timer default = 120s).
(c) Verify the `lldp_expected_topology.csv` baseline by running a full topology discovery and comparing with the lookup.

### Step 4 — Operationalize
Dashboard ("Network — Physical Topology (LLDP)"):
- Row 1 — Single-value tiles: "Topology mismatches", "Missing neighbors", "New/unknown connections", "Total monitored links".
- Row 2 — Table: mismatches with host, interface, expected_neighbor, current_neighbor, issue_type.
- Row 3 — Timeline: topology changes over 24h.
- Row 4 — Topology map (if Splunk Network Diagram Viz is installed): visual representation of LLDP adjacencies.

Alerting:
- Critical (expected fabric link neighbor missing — spine-to-leaf or leaf-to-leaf): possible link failure or cable pull during maintenance — page NOC.
- High (neighbor mismatch on any fabric port): cable moved incorrectly — investigate before traffic is impacted.
- Warning (new/unknown LLDP neighbor on access port): possible unauthorized device — alert security.

Runbook:
1. **Missing expected neighbor**: Check the physical cable at both ends. Check interface status (UC-5.11.2). If the interface is up but LLDP is missing, the remote device may have LLDP disabled or is rebooting.
2. **Wrong neighbor on fabric port**: A cable was likely moved during maintenance. Cross-reference with change management records. Correct the wiring to match the topology plan.
3. **Unknown device on access port**: Identify the device from LLDP system-name and system-description. If it's a network device, it may be a new deployment. If it's an end-host, check 802.1X authentication status.

### Step 5 — Troubleshooting

- **LLDP data not updating** — LLDP has a default advertisement interval of 30 seconds and a hold timer of 120 seconds. If using ON_CHANGE, verify the platform supports it for LLDP. Fall back to SAMPLE mode with 60s interval.

- **LLDP neighbor names inconsistent** — Different platforms report `system-name` differently (FQDN vs. hostname only). Normalize: `| rex field=current_neighbor "^(?<short_name>[^.]+)"` to extract just the hostname.

- **Too many topology changes during maintenance** — Suppress alerts during planned maintenance windows using a maintenance lookup or KV store filter.

- **LLDP disabled on some interfaces** — Some interfaces (management, loopback) don't run LLDP. Exclude these from the baseline and alerting.

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

## Known False Positives

Telemetry pauses during device reboots, cert renewals, or transport changes; subscription restarts and path renames can look like drops without a live fault.

## References

- [CIM: Change](https://docs.splunk.com/Documentation/CIM/latest/User/Change)
