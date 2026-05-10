<!-- AUTO-GENERATED from UC-5.20.46.json — DO NOT EDIT -->

---
id: "5.20.46"
title: "IS-IS IPv6 Multi-Topology Reachability Monitoring"
status: "verified"
criticality: "high"
splunkPillar: "IT Operations"
---

# UC-5.20.46 · IS-IS IPv6 Multi-Topology Reachability Monitoring

> **Criticality:** High &middot; **Difficulty:** Advanced &middot; **Pillar:** IT Operations &middot; **Type:** Availability &middot; **Wave:** Run &middot; **Status:** Verified

*IS-IS is another road-mapping system that big internet carriers use. It can keep separate road maps for IPv4 and IPv6 — like having one map for cars and another for bicycles. If the bicycle map gets a torn page but the car map is fine, only bicycle riders get lost. We watch both maps separately to make sure neither one has missing pages.*

---

## Description

Monitors IS-IS IPv6 reachability for networks using IS-IS as the IPv6 IGP, with specific focus on Multi-Topology (MT-IS-IS) IPv6 topology health, SPF run frequency, and adjacency stability. IS-IS is the dominant IGP in service provider, data center, and SRv6 environments. IPv6 reachability failures in IS-IS can partition the IPv6 underlay while IPv4 remains healthy — a particularly dangerous condition in multi-topology mode where the two topologies are independent.

## Value

In multi-topology IS-IS, the IPv6 topology can fail independently of IPv4. A link that supports only IPv4 but is included in IS-IS without IPv6 capability creates a gap in the IPv6 topology, potentially partitioning the network. The IPv4 topology shows everything as healthy while IPv6 traffic is blackholed. Monitoring the IPv6 topology (MT-ID 2) specifically catches these split-brain scenarios. SPF run frequency monitoring detects routing instability — excessive SPF runs indicate flapping links or LSP storms.

## Implementation

Collect IS-IS syslog events including adjacency changes, SPF run notifications, and LSP events. Track IPv6-specific topology (MT-ID 2) health. Alert on adjacency losses, excessive SPF runs, and IPv6 reachability withdrawals.

## Detailed Implementation

### Prerequisites
- IS-IS configured as the IPv6 IGP (either multi-topology or single-topology with IPv6 address families).
- Syslog forwarding at severity 5 (notification) for IS-IS events.
- Understanding of the IS-IS topology mode (single-topology vs multi-topology).

### Step 1 — Configure data collection

**Cisco IOS-XE — IS-IS event logging for multi-topology:**
```
router isis CORE
 address-family ipv6
  multi-topology
  log-adjacency-changes
```

**Cisco IOS-XR (service provider):**
```
router isis CORE
 address-family ipv6 unicast
  multi-topology
 log adjacency changes
```

**Juniper Junos:**
```
set protocols isis traceoptions flag state
set protocols isis topologies ipv6-unicast
```

**IS-IS syslog messages to monitor:**
```
%ISIS-5-ADJCHANGE: Adjacency state changed - neighbor system-id: 0100.0000.0001, interface: GigabitEthernet0/0/0, level: 2, state: Up -> Down
%ISIS-4-MULTITOPOLOGY_UNREACHABLE: MT-2 (IPv6) - destination 2001:db8:cafe::/48 unreachable via system 0100.0000.0002
%ISIS-5-SPF_RUN: Level-2 SPF run triggered for topology IPv6 Unicast
```

**Verification:**
```spl
index=network sourcetype="cisco:ios" ("%ISIS" OR "%CLNS") earliest=-7d
| stats count by host
```

### Step 2 — Create the search and alert

**IS-IS adjacency down alert:**
```spl
index=network sourcetype="cisco:ios" "%ISIS" "ADJCHANGE" "Down" earliest=-1h
| rex field=_raw "system-id:\s*(?<neighbor_sysid>[0-9a-fA-F.]+)"
| rex field=_raw "interface:\s*(?<interface>\S+)"
| rex field=_raw "level:\s*(?<level>\d)"
| eval alert="IS-IS adjacency DOWN: " . host . " → " . neighbor_sysid . " on " . interface . " (L" . level . ")"
| table _time, host, neighbor_sysid, interface, level, alert
```

**Excessive SPF run detection:**
```spl
index=network sourcetype="cisco:ios" "%ISIS" "SPF" earliest=-1h
| stats count as spf_runs by host
| where spf_runs > 10
| eval alert="IS-IS SPF storm: " . spf_runs . " SPF runs in 1 hour on " . host . " — investigate routing instability"
```
Trigger: more than 10 SPF runs per hour indicates routing instability (normal is 1-3).

**IPv6 multi-topology reachability loss:**
```spl
index=network sourcetype="cisco:ios" "%ISIS" "MULTITOPOLOGY" "unreachable" "MT-2" earliest=-1h
| rex field=_raw "destination\s+(?<lost_prefix>[0-9a-fA-F:/]+)"
| rex field=_raw "system\s+(?<via_system>[0-9a-fA-F.]+)"
| eval severity="CRITICAL — IPv6 prefix unreachable in IS-IS topology while IPv4 may still be reachable"
| table _time, host, lost_prefix, via_system, severity
```
This specifically catches the split-brain condition where IPv6 topology is partitioned but IPv4 remains connected.

### Step 3 — Validate
(a) **Adjacency flap (lab).** Shut/no-shut an IS-IS interface. Verify adjacency DOWN and UP events appear.

(b) **Multi-topology gap.** In a lab, remove IPv6 from a link that is in the IS-IS multi-topology. Verify the IPv6 unreachability alert fires for prefixes behind that link.

(c) **SPF run count.** After a controlled adjacency flap, verify one SPF run is logged per topology change.

### Step 4 — Operationalize

**Dashboard** ("IPv6 — IS-IS Routing Health"):
- Row 1 — Single-value: IS-IS adjacencies UP, SPF runs today, IPv6 unreachability events.
- Row 2 — Table: recent adjacency changes.
- Row 3 — Timechart: SPF runs per hour over 7 days.
- Row 4 — Alert panel: active IPv6 unreachability events.

**Scheduling:** Adjacency alerts real-time. SPF monitoring hourly. Multi-topology unreachability continuous.

**Runbook:**
1. Adjacency DOWN: check physical link, IS-IS hello interval/multiplier match, area/level configuration match.
2. Excessive SPF: identify the triggering LSPs (`show isis database verbose`). Find the source of instability.
3. MT-2 unreachable: verify IPv6 is enabled on all links in the IS-IS topology. In multi-topology mode, every link must explicitly participate in the IPv6 topology.

### Step 5 — Troubleshooting

- **Single-topology IPv6 gap** — In single-topology mode, if any link in the IS-IS topology lacks IPv6, the SPF calculation may produce suboptimal or broken IPv6 paths. Multi-topology avoids this by computing independent topologies.

- **IS-IS level mismatch** — IS-IS Level-1 and Level-2 adjacencies are independent. A Level-2 adjacency loss affects inter-area routing; a Level-1 loss affects intra-area only. Ensure alerts include the level for proper impact assessment.

- **LSP fragmentation** — Large LSPs (many TLVs) may fragment. If a fragment is lost, partial topology information may cause SPF to compute incorrect paths. Monitor for LSP fragment counts on large routers.

## SPL

```spl
index=network sourcetype="cisco:ios" ("%ISIS" OR "%CLNS") earliest=-24h
| eval isis_event=case(
    match(_raw, "(?i)ADJCHANGE|adjacency.?change"), "adjacency_change",
    match(_raw, "(?i)SPF|spf_run|spf-calculation"), "spf_run",
    match(_raw, "(?i)LSP|lsp.?flood|lsp.?purge"), "lsp_event",
    match(_raw, "(?i)ipv6.*unreachable|MT-2.*unreachable"), "ipv6_unreachable",
    1=1, null())
| where isnotnull(isis_event)
| rex field=_raw "(?:neighbor|Nbr|adjacency).*?(?<neighbor_id>[0-9a-fA-F.]+)"
| rex field=_raw "(?:state|State).*?(?<new_state>Up|Down|Init|Waiting)"
| eval severity=case(
    isis_event="ipv6_unreachable", "CRITICAL",
    match(new_state, "(?i)down"), "CRITICAL",
    isis_event="spf_run", "INFO",
    match(new_state, "(?i)up"), "INFO",
    1=1, "WARNING")
| table _time, host, isis_event, neighbor_id, new_state, severity
| sort -severity
```

## Visualization

(1) Table: IS-IS adjacency state with IPv6 topology status. (2) Timechart: SPF runs over 24 hours — should be low and event-driven. (3) Single-value: IS-IS adjacencies UP vs total. (4) Drilldown: LSP details for recent topology changes.

## Known False Positives

**Planned maintenance.** IS-IS adjacency flaps during router upgrades or link maintenance are expected.

**SPF run after configuration change.** Any IS-IS configuration change triggers an SPF run. This is normal. Excessive SPF runs are only concerning when there is no corresponding configuration change.

**Single-topology to multi-topology migration.** During migration from single-topology to multi-topology IS-IS, adjacency resets and SPF runs are expected as the topology is restructured.

## References

- [RFC 5120 — M-IS-IS: Multi Topology Routing in IS-IS](https://www.rfc-editor.org/rfc/rfc5120)
- [RFC 5308 — Routing IPv6 with IS-IS (IPv6 reachability TLVs)](https://www.rfc-editor.org/rfc/rfc5308)
- [RFC 5305 — IS-IS Extensions for Traffic Engineering](https://www.rfc-editor.org/rfc/rfc5305)
