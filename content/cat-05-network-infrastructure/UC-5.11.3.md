<!-- AUTO-GENERATED from UC-5.11.3.json — DO NOT EDIT -->

---
id: "5.11.3"
title: "BGP Peer State Change Detection via ON_CHANGE"
criticality: "critical"
splunkPillar: "Observability"
---

# UC-5.11.3 · BGP Peer State Change Detection via ON_CHANGE

> **Criticality:** Critical &middot; **Difficulty:** Intermediate &middot; **Pillar:** Observability &middot; **Type:** Availability

*We help you know the moment a BGP neighbor drops, which matters when one lost session can steer traffic the wrong way in a data center or WAN.*

---

## Description

Syslog-based BGP monitoring depends on log forwarding latency and parsing reliability. gNMI ON_CHANGE subscriptions to BGP neighbor state deliver sub-second notification when a peer leaves Established — faster than syslog and with structured data. For VXLAN EVPN fabrics where BGP is both underlay and overlay, a single peer drop can black-hole tenant traffic within seconds.

## Value

Network operations teams receive sub-second notification when BGP peers leave Established state, enabling rapid response to fabric partitions, EVPN overlay failures, and WAN outages before applications are impacted.

## Implementation

Subscribe to `/network-instances/network-instance/protocols/protocol/bgp/neighbors/neighbor/state` using `subscription_mode = "on_change"`. BGP session state is represented as integer (1=Idle through 6=Established). Alert on any state != 6 (Established). For Cisco IOS XR, use native YANG path `Cisco-IOS-XR-ipv4-bgp-oper:bgp/instances/instance`. Correlate with interface flaps (UC-5.11.1) and optical health (UC-5.11.5) for root cause.

## Detailed Implementation

### Prerequisites
- Telegraf gNMI collector configured with ON_CHANGE subscription mode for BGP state. ON_CHANGE mode sends updates only when the value changes (not at regular intervals), making it ideal for state transitions — you get sub-second notification when a BGP peer drops.
- OpenConfig path: `/network-instances/network-instance/protocols/protocol/bgp/neighbors/neighbor/state`. Key leaf: `session-state` (enum: 1=Idle, 2=Connect, 3=Active, 4=OpenSent, 5=OpenConfirm, 6=Established). Vendor-specific alternatives: Cisco IOS-XR: `Cisco-IOS-XR-ipv4-bgp-oper:bgp/instances/instance/instance-active/default-vrf/neighbors/neighbor`; Arista EOS: supports OpenConfig natively; Juniper: `openconfig-bgp` or `juniper-bgp`.
- gNMI ON_CHANGE support varies by platform: Arista EOS (full ON_CHANGE), Cisco NX-OS (limited — may require SAMPLE as fallback with 10s interval), Juniper (ON_CHANGE for most state leaves), Nokia SR Linux (full ON_CHANGE). Test subscription mode before deploying to production.
- Build a `bgp_peers.csv` lookup: `host,neighbor_address,peer_asn,peer_role,peer_description` (e.g., `spine-01,10.0.0.2,65001,spine-peer,Spine-02 eBGP underlay`). This provides context when a peer drops.
- In VXLAN EVPN fabrics, BGP serves as both underlay (eBGP for loopback reachability) and overlay (iBGP/eBGP for EVPN type-2/type-5 routes). A single peer drop can black-hole tenant traffic within seconds.

### Step 1 — Configure data collection
Telegraf subscription for BGP state (ON_CHANGE):
```toml
[[inputs.gnmi.subscription]]
  name = "openconfig_bgp"
  origin = "openconfig"
  path = "/network-instances/network-instance/protocols/protocol/bgp/neighbors/neighbor/state"
  subscription_mode = "on_change"
```

Verify BGP state data in Splunk:
```spl
| mstats latest("openconfig_bgp.session_state") AS state WHERE index=gnmi_metrics BY host, neighbor_address
| eval state_label=case(state==1, "Idle", state==2, "Connect", state==3, "Active", state==4, "OpenSent", state==5, "OpenConfirm", state==6, "Established", 1==1, "Unknown-".state)
| stats count by state_label
```
In a healthy environment, all peers should be Established (state=6). If you see any non-6 states, those peers are currently down or transitioning.

### Step 2 — Create the search and alert

**Primary search — Non-established BGP peers:**
```spl
| mstats latest("openconfig_bgp.session_state") AS state WHERE index=gnmi_metrics BY host, neighbor_address span=1m
| where state != 6
| eval state_label=case(state==1, "Idle", state==2, "Connect", state==3, "Active", state==4, "OpenSent", state==5, "OpenConfirm", state==6, "Established", 1==1, "Unknown")
| lookup bgp_peers.csv host neighbor_address OUTPUT peer_asn peer_role peer_description
| eval severity=case(peer_role=="spine-peer" OR peer_role=="wan-uplink", "CRITICAL", peer_role=="evpn-overlay", "HIGH", 1==1, "WARNING")
| eval impact=case(state==1, "Peer completely down - no TCP connection", state==2 OR state==3, "TCP connecting but no BGP open - possible config mismatch or filter", state==4 OR state==5, "BGP negotiating - possible capability mismatch", 1==1, "Unknown state")
| sort severity, -_time
```

#### Understanding this SPL: `latest()` gets the most recent session state for each peer. Any state other than 6 (Established) means the session is down or transitioning. The `peer_role` from the lookup determines severity — losing a spine uplink (which carries all fabric traffic) is more critical than losing a route reflector client. The `impact` field provides immediate diagnostic context based on which BGP FSM state the peer is stuck in.

**BGP flap detection (state oscillation):**
```spl
| mstats latest("openconfig_bgp.session_state") AS state WHERE index=gnmi_metrics BY host, neighbor_address span=1m earliest=-1h
| streamstats window=5 dc(state) AS state_changes count AS samples by host, neighbor_address
| where state_changes > 2 AND samples >= 5
| lookup bgp_peers.csv host neighbor_address OUTPUT peer_asn peer_description
| stats max(state_changes) AS max_state_changes latest(state) AS current_state by host, neighbor_address, peer_description
| where max_state_changes > 2
| sort -max_state_changes
```

#### Understanding this SPL: Detects BGP session flapping — peers that repeatedly transition between Established and other states. A peer changing state more than twice in a 5-minute window is flapping. Flapping BGP sessions are more disruptive than a clean down/up because each transition triggers route withdrawal and re-advertisement, causing convergence storms across the fabric.

**Fabric-wide BGP health summary:**
```spl
| mstats latest("openconfig_bgp.session_state") AS state WHERE index=gnmi_metrics BY host, neighbor_address
| eval is_established=if(state==6, 1, 0)
| stats count as total_peers sum(is_established) as up_peers by host
| eval down_peers=total_peers - up_peers
| eval health_pct=round(100*up_peers/total_peers, 1)
| eval status=case(health_pct==100, "HEALTHY", health_pct >= 90, "DEGRADED", 1==1, "CRITICAL")
| sort health_pct
```

### Step 3 — Validate
(a) On a router, verify BGP state: `show bgp summary` (or platform equivalent). The number of Established peers should match the Splunk count.
(b) Test ON_CHANGE latency: shut down a BGP peer interface (`shutdown`) and time how quickly the state change appears in Splunk. Target: < 5 seconds from shutdown to Splunk alert.
(c) Verify the `bgp_peers.csv` lookup: spot-check 10 peers to ensure `neighbor_address`, `peer_asn`, and `peer_role` are correct.
(d) During a planned maintenance window (peer graceful restart), verify the alert fires and correctly identifies the peer.

### Step 4 — Operationalize
Dashboard ("Network — BGP Session Health"):
- Row 1 — Single-value tiles: "Total BGP peers", "Established", "Non-Established", "Flapping (1h)".
- Row 2 — Status grid: each cell = one peer (green=Established, red=down, yellow=flapping). Organized by host.
- Row 3 — Down/flapping peers table: host, neighbor, state_label, peer_role, severity, impact.
- Row 4 — BGP state change timeline: horizontal bar chart showing state transitions over 24h.

Alerting:
- Critical (spine peer or WAN uplink drops from Established): page NOC immediately — potential fabric partition or WAN outage.
- High (EVPN overlay peer drops): alert within 1 minute — tenant traffic may be impacted.
- Warning (any peer flapping > 3 state changes in 5 minutes): schedule investigation — flapping is worse than a clean outage.

Runbook (owner: Network Operations):
1. **Spine/fabric peer down**: Check the physical link (UC-5.11.2 for errors, UC-5.11.5 for optics). If physical layer is clean, check BGP configuration: `show bgp neighbor <ip>` for last error message (hold timer expired, notification received, etc.).
2. **BGP stuck in Active state**: This usually means the remote peer is not responding to TCP SYN on port 179. Check: (a) ACL blocking BGP, (b) remote device down, (c) incorrect neighbor IP configuration.
3. **BGP flapping**: Common causes: MTU mismatch (BGP OPEN succeeds but UPDATE fails), hold timer too short, CPU overload on one peer, unstable underlying link.

### Step 5 — Troubleshooting

- **ON_CHANGE not sending updates** — Some platforms (especially NX-OS) have limited ON_CHANGE support. Fall back to SAMPLE mode with a 10-second interval. Test with `gnmic subscribe --mode on_change --path <path>`.

- **Session state always shows 6 (Established) even when peer is down** — If ON_CHANGE events are missed (Telegraf reconnection, network partition), the last known state persists. Add a staleness check: `| eval minutes_since_update=round((now()-_time)/60, 1) | where minutes_since_update > 5` to flag stale data.

- **Peer address format differs between gNMI and lookup** — gNMI may report `10.0.0.2` while the lookup has `10.0.0.2/32`. Normalize addresses: `| rex field=neighbor_address "(?<clean_ip>\d+\.\d+\.\d+\.\d+)"` before the lookup.

- **Too many alerts during planned maintenance** — Implement a maintenance window mechanism: use a lookup or KV store with maintenance periods, and suppress alerts for devices in maintenance.

**IPv6 Coverage:** Add IPv6 AFI sensor path: `openconfig-bgp:bgp/neighbors/neighbor[neighbor-address=*]/afi-safis/afi-safi[afi-safi-name=IPV6_UNICAST]/state`

## SPL

```spl
| mstats latest("openconfig_bgp.session_state") AS state WHERE index=gnmi_metrics BY host, neighbor_address span=1m
| where state != 6
| eval state_label=case(state=1, "Idle", state=2, "Connect", state=3, "Active", state=4, "OpenSent", state=5, "OpenConfirm", state=6, "Established", 1=1, "Unknown")
| table _time, host, neighbor_address, state_label
| sort -_time
```

## Visualization

Status grid (BGP peer matrix — green=Established, red=down), Timeline (state change events), Table (non-established peers).

## Known False Positives

Telemetry pauses during device reboots, cert renewals, or transport changes; subscription restarts and path renames can look like drops without a live fault.

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
