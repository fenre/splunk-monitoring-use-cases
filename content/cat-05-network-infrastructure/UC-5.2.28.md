<!-- AUTO-GENERATED from UC-5.2.28.json — DO NOT EDIT -->

---
id: "5.2.28"
title: "BGP Peering Status and Route Stability (Meraki MX)"
criticality: "high"
splunkPillar: "Observability"
---

# UC-5.2.28 · BGP Peering Status and Route Stability (Meraki MX)

> **Criticality:** High &middot; **Difficulty:** Beginner &middot; **Pillar:** Observability &middot; **Type:** Availability

*We watch border gateway and route health messages on the same gear so a bad neighbor or wobbly path is easier to spot early.*

---

## Description

Ensures BGP peers remain established and routing remains stable for multi-ISP designs.

## Value

Operations teams monitor Meraki MX BGP peering state transitions and route stability, detecting peer failures and flapping that cause routing disruptions.

## Implementation

Monitor BGP event syslog. Alert on neighbor state changes.

## Detailed Implementation

### Prerequisites
* Meraki MX BGP peering events via syslog or API. Data in `index=meraki` with `sourcetype=meraki:events`. Key events: BGP peer state changes (Established/Active/Idle/OpenConfirm), route advertisements, route withdrawals.
* BGP on Meraki MX: used for dynamic routing with upstream ISPs or data center interconnects. Available on MX with concentrator mode or data center MX. BGP peer flapping causes routing instability.

### Step 1 — - Configure data collection
```
# Dashboard > Security & SD-WAN > Addressing & VLANs > Routing > BGP
# Configure BGP AS number and peers
# Syslog > Roles: Event log
```
Verify:
```spl
index=meraki sourcetype="meraki:events" earliest=-7d
| where match(_raw, "(?i)bgp|peer.*(state|change|up|down)|route.*(adverti|withdraw|received)")
| stats count by host
```

### Step 2 — - Create the search and alert

**Primary search -- BGP peering status and route stability:**
```spl
index=meraki sourcetype="meraki:events" earliest=-7d
| where match(_raw, "(?i)bgp")
| eval bgp_event=case(match(_raw, "(?i)established|peer.*up"), "PEER_UP", match(_raw, "(?i)idle|down|peer.*down|notification"), "PEER_DOWN", match(_raw, "(?i)active|openconfirm|opensent|connect"), "NEGOTIATING", match(_raw, "(?i)route.*withdraw|route.*removed"), "ROUTE_WITHDRAWN", match(_raw, "(?i)route.*adverti|route.*received"), "ROUTE_RECEIVED", 1==1, "BGP_EVENT")
| rex "peer\s+(?<peer_ip>[0-9.]+)"
| rex "AS\s*(?<peer_asn>\d+)"
| stats count as events latest(_time) as last_event by host, bgp_event, peer_ip, peer_asn
| eval severity=case(bgp_event="PEER_DOWN", "CRITICAL -- BGP peer down", bgp_event="ROUTE_WITHDRAWN" AND events > 10, "HIGH -- route instability", bgp_event="NEGOTIATING" AND events > 20, "WARNING -- peer flapping", 1==1, "INFO")
| where severity != "INFO"
| sort severity, -events
```

### Step 3 — - Validate
(a) Dashboard: Security & SD-WAN > Routing > BGP -- check peer status.
(b) Verify BGP routes: Dashboard shows received and advertised routes.
(c) Compare with ISP/partner BGP peer status.

### Step 4 — - Operationalize
Dashboard ("Meraki MX -- BGP"):
* Row 1 -- Single-value: "BGP peers down", "Route withdrawals", "Flapping peers".
* Row 2 -- BGP event timeline.

Alerting:
* Critical (BGP peer down): routing to/from ISP lost.
* Warning (> 20 state changes for single peer in 7d): peer flapping.

### Step 5 — - Troubleshooting

* **BGP peer down** -- Check: (1) WAN link connectivity, (2) BGP peer IP reachability (ping), (3) ISP-side BGP configuration, (4) BGP timers (hold time/keepalive).

* **Peer flapping** -- Rapidly going up/down. Check: (1) WAN link stability, (2) BGP hold timer too aggressive (increase to 90s), (3) ISP-side issue, (4) MTU issues on BGP TCP session.

* **Routes withdrawn** -- ISP may be withdrawing routes due to: (1) maintenance, (2) prefix filter change, (3) BGP community changes. Verify with ISP.

## SPL

```spl
index=cisco_network sourcetype="meraki" type=security_event signature="*BGP*" (signature="*neighbor*" OR signature="*route*")
| stats count as bgp_event_count by bgp_neighbor, event_type
| where bgp_event_count > 5
```

## Visualization

BGP peer status table; route change timeline; peering stability gauge.

## Known False Positives

Reconvergence, ISPs, and lab peers can jolt route tables; confirm whether the next hop is still intended.

## References

- [Splunkbase app 5580](https://splunkbase.splunk.com/app/5580)
