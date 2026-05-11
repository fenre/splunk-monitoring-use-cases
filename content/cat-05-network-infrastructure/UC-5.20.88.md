<!-- AUTO-GENERATED from UC-5.20.88.json — DO NOT EDIT -->

---
id: "5.20.88"
title: "VXLAN/EVPN IPv6 Underlay and Overlay Health Monitoring"
status: "verified"
criticality: "high"
splunkPillar: "IT Operations"
---

# UC-5.20.88 · VXLAN/EVPN IPv6 Underlay and Overlay Health Monitoring

> **Criticality:** High &middot; **Difficulty:** Advanced &middot; **Pillar:** IT Operations &middot; **Type:** Availability, Performance &middot; **Wave:** Run &middot; **Status:** Verified

*In a modern factory (data center), all the machines are connected by a sophisticated conveyor belt system (VXLAN/EVPN fabric). The conveyor system now uses the new address system (IPv6) for routing packages between sections. If the address system fails between any two sections, packages can't move.*

---

## Description

Monitors VXLAN/EVPN data center fabric health with specific focus on IPv6 underlay (BGP Unnumbered, link-local peering, VTEP reachability) and IPv6 overlay (EVPN Type-2/Type-5 route distribution, NDP suppression, dual-stack tenant VRF health). Modern spine-leaf fabrics increasingly use IPv6 for the underlay network, which introduces NDP dependencies and IPv6-specific failure modes not present in IPv4-based underlays.

## Value

Data center fabric failures impact all tenant workloads. IPv6-specific underlay issues (NDP failures between spine-leaf, link-local BGP session drops, VTEP loopback unreachability) can take down the entire fabric while IPv4-based monitoring shows no issues. This use case provides fabric-specific IPv6 visibility that complements general routing protocol monitoring (UC-5.20.43, UC-5.20.44).

## Implementation

Monitor BGP Unnumbered sessions between spine and leaf switches. Track VTEP peer reachability via IPv6. Monitor EVPN route distribution for IPv6 prefixes. Verify NDP suppression is functioning in the overlay.

## Detailed Implementation

### Prerequisites
- VXLAN/EVPN fabric with BGP Unnumbered or IPv6 underlay.
- Syslog forwarding from all spine and leaf switches.
- Understanding of the fabric topology (spine count, leaf count, VNI assignments).

### Step 1 — Configure data collection

**BGP Unnumbered IPv6 configuration (NX-OS spine-leaf):**
```
! Leaf configuration
router bgp 65001
 neighbor Ethernet1/49 remote-as 65000
  address-family ipv4 unicast
  address-family ipv6 unicast
  address-family l2vpn evpn
   send-community extended
!
interface Ethernet1/49
 medium p2p
 ip unnumbered loopback0
 ipv6 link-local use-link-local-only
```

**Enable fabric-specific syslog logging:**
```
logging level bgp 5
logging level vxlan 5
logging level evpn 5
logging level nve 5
```

**Verification:**
```spl
index=network sourcetype="cisco:nxos:syslog" ("%BGP" OR "%NVE" OR "%EVPN") | stats count by host, sourcetype
```

### Step 2 — Create monitoring searches

**Underlay BGP Unnumbered session health:**
```spl
index=network sourcetype="cisco:nxos:syslog" "%BGP-5-ADJCHANGE" earliest=-24h
| rex field=_raw "neighbor\s+(?<neighbor>[0-9a-fA-F:.]+)"
| rex field=_raw "(?<bgp_state>Up|Down)"
| eval is_ipv6_session=if(match(neighbor, ":") OR match(_raw, "(?i)link-local|unnumbered"), "yes", "no")
| stats latest(bgp_state) as current_state count(eval(bgp_state="Down")) as down_events by host, neighbor, is_ipv6_session
| where current_state="Down" OR down_events > 2
| eval severity=case(
    current_state="Down" AND is_ipv6_session="yes", "CRITICAL — IPv6 underlay BGP session DOWN",
    down_events > 5, "WARNING — unstable BGP session (" . down_events . " flaps)",
    1=1, "INFO")
```

**EVPN IPv6 route distribution:**
```spl
index=network sourcetype="cisco:nxos:syslog" "EVPN" earliest=-1h
| eval route_type=case(
    match(_raw, "[Tt]ype.?2"), "MAC/IP (host route)",
    match(_raw, "[Tt]ype.?5"), "IP prefix route",
    1=1, "other")
| eval has_ipv6=if(match(_raw, "[0-9a-fA-F]{1,4}(:[0-9a-fA-F]{1,4}){2,}"), 1, 0)
| where has_ipv6=1
| stats count by host, route_type
```

**NDP suppression verification:**
```spl
index=network sourcetype="cisco:nxos:syslog" "nve" "suppress" earliest=-24h
| stats count as suppressed_ndp by host
| eval status=if(suppressed_ndp > 0, "NDP suppression active", "NDP suppression NOT active — multicast NDP flooding")
```

### Step 3 — Validate
(a) **BGP Unnumbered verification.** SSH to a leaf switch. Run `show bgp l2vpn evpn summary`. Verify IPv6 underlay sessions are established.

(b) **VTEP reachability.** From a leaf, ping the VTEP loopback of another leaf via IPv6. Verify VXLAN tunnel is established with `show nve peers`.

(c) **Tenant IPv6 test.** From a VM on leaf-1, ping6 a VM on leaf-2 in the same tenant VRF. Verify VXLAN encapsulated traffic crosses the fabric.

### Step 4 — Operationalize

**Dashboard** ("IPv6 — DC Fabric Health"):
- Row 1 — Topology diagram: spine-leaf with BGP session status colour coding.
- Row 2 — Table: all BGP Unnumbered sessions with state and flap count.
- Row 3 — Single-value: EVPN IPv6 route count (Type-2 and Type-5).
- Row 4 — Timechart: BGP events and VTEP state changes.

**Alert:** IPv6 underlay BGP session DOWN — critical. Impacts all VXLAN tunnels through the affected link.

**Runbook:**
1. BGP Unnumbered session down: Check physical link (`show interface`). Verify NDP is resolving (`show ipv6 neighbors`). Check for CoPP drops on BGP.
2. VTEP peer unreachable: Verify underlay reachability via `traceroute6`. Check ECMP paths. Verify loopback is advertised.
3. EVPN route missing: Check `show bgp l2vpn evpn` for the expected prefix. Verify VNI-to-VRF mapping. Check route-target import/export.

### Step 5 — Troubleshooting

- **Link-local BGP peering failures.** BGP Unnumbered uses the interface link-local address for peering. If NDP fails to resolve the neighbor's link-local, the BGP session cannot establish. Verify with `show ipv6 neighbors interface <intf>`.

- **MTU issues.** VXLAN adds 50-54 bytes of overhead. With an IPv6 underlay (40-byte header vs 20-byte IPv4), the overhead is 70-74 bytes. Ensure fabric links have MTU ≥ 9214 to avoid PMTUD issues.

- **Arista EOS differences.** Arista uses `neighbor <intf> peer group SPINE` with `redistribute connected` instead of `ip unnumbered`. The NDP and BGP session behaviour is equivalent but the configuration syntax differs.

## SPL

```spl
index=network (sourcetype="cisco:nxos:syslog" OR sourcetype="cisco:iosxe") earliest=-24h
  ("%BGP-5-ADJCHANGE" OR "%VXLAN" OR "%EVPN" OR "%NVE" OR "nve1")
| eval event_type=case(
    match(_raw, "BGP.*ADJCHANGE.*Down"), "BGP_DOWN",
    match(_raw, "BGP.*ADJCHANGE.*Up"), "BGP_UP",
    match(_raw, "NVE.*peer.*[Dd]own"), "VTEP_PEER_DOWN",
    match(_raw, "NVE.*peer.*[Uu]p"), "VTEP_PEER_UP",
    match(_raw, "EVPN.*route.*withdraw"), "EVPN_ROUTE_WITHDRAWN",
    1=1, "OTHER")
| eval is_ipv6=if(match(_raw, "[0-9a-fA-F]{1,4}(:[0-9a-fA-F]{1,4}){2,}") OR match(_raw, "(?i)ipv6|AFI.*2"), 1, 0)
| stats count as events by host, event_type, is_ipv6
| eval concern=case(
    event_type="BGP_DOWN" AND is_ipv6=1, "IPv6 BGP underlay session DOWN — fabric connectivity at risk",
    event_type="VTEP_PEER_DOWN", "VTEP peer DOWN — VXLAN tunnel failure",
    event_type="EVPN_ROUTE_WITHDRAWN" AND is_ipv6=1, "IPv6 EVPN route withdrawn — tenant IPv6 connectivity impacted",
    1=1, null())
| where isnotnull(concern)
| sort -events
```

## Visualization

(1) Fabric topology diagram with IPv6 BGP session status. (2) Table: VTEP peers with reachability status. (3) Timechart: EVPN IPv6 route count over time. (4) Single-value: IPv6 underlay BGP session health percentage.

## Known False Positives

**Planned maintenance.** Spine-leaf BGP sessions go down during planned switch upgrades. Correlate with change management windows.

**ISSU/ISSD events.** In-service software upgrades may cause brief BGP session flaps. These are typically self-recovering within 60 seconds.

**Multi-site EVPN.** In multi-site EVPN deployments, border gateway BGP sessions may use different session characteristics than internal spine-leaf sessions.

## References

- [RFC 7938 — Use of BGP for Routing in Large-Scale Data Centers (BGP Unnumbered with IPv6 link-local)](https://www.rfc-editor.org/rfc/rfc7938)
- [RFC 8365 — A Network Virtualization Overlay Solution Using EVPN](https://www.rfc-editor.org/rfc/rfc8365)
- [Cisco VXLAN/EVPN Configuration Guide for NX-OS (IPv6 underlay and overlay)](https://www.cisco.com/c/en/us/td/docs/dcn/nx-os/nexus9000/103x/configuration/vxlan/cisco-nexus-9000-series-nx-os-vxlan-configuration-guide-release-103x.html)
