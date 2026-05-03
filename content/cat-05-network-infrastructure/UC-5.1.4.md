<!-- AUTO-GENERATED from UC-5.1.4.json — DO NOT EDIT -->

---
id: "5.1.4"
title: "BGP Peer State Changes"
criticality: "critical"
splunkPillar: "Observability"
---

# UC-5.1.4 · BGP Peer State Changes

> **Criticality:** Critical &middot; **Difficulty:** Beginner &middot; **Pillar:** Observability &middot; **Type:** Availability

*We tell you when a BGP session to another network drops or bounces, because that can make whole paths unreachable for many people at once.*

---

## Description

BGP session drops cause routing convergence, potentially making networks unreachable. IPv6 BGP AFI/SAFI sessions are tracked separately from IPv4 — monitor instability in both address families.

## Value

NOC teams track BGP peer state transitions across routers, detecting session failures and flapping that cause routing instability and potential traffic black-holes.

## Implementation

Forward syslog from all BGP speakers. Critical alert on adjacency down. Include neighbor IP and AS number.

## Detailed Implementation

### Prerequisites
* BGP peer state change syslog messages. Data in `index=network` with `sourcetype=cisco:ios`, `sourcetype=juniper:srx:structured`, or vendor-specific sourcetypes. Key syslog mnemonics: Cisco `%BGP-5-ADJCHANGE`, `%BGP-3-NOTIFICATION`; Juniper `RPD_BGP_NEIGHBOR_STATE_CHANGED`; Arista `BGP-5-ADJCHANGE`.
* BGP peering: establishes routing adjacency between autonomous systems. State transitions (Idle → Connect → OpenSent → OpenConfirm → Established → back to Idle) indicate session instability. Common causes: route flaps, authentication failure, hold timer expiry, prefix limit exceeded.

### Step 1 — - Configure data collection
```
# Cisco IOS -- ensure BGP logging
router bgp 65000
 bgp log-neighbor-changes

# Syslog forwarding
logging host <splunk-syslog-ip>
logging trap informational
```
Verify:
```spl
index=network earliest=-24h
| where match(_raw, "(?i)BGP.*ADJ|BGP.*NEIGHBOR|BGP.*state|bgp.*established|bgp.*idle")
| stats count by host
```

### Step 2 — - Create the search and alert

**Primary search -- BGP peer state change tracking:**
```spl
index=network earliest=-24h
| where match(_raw, "(?i)BGP.*ADJ|BGP.*NEIGHBOR.*STATE|bgp.*state|BGP.*NOTIFICATION")
| rex field=_raw "(?i)neighbor\s+(?<peer_ip>\d+\.\d+\.\d+\.\d+)"
| rex field=_raw "(?i)(?:state|went)\s+(?:to\s+)?(?<bgp_state>\w+)"
| rex field=_raw "(?i)AS\s+(?<peer_asn>\d+)"
| eval peer=coalesce(peer_ip, neighbor, bgp_neighbor)
| eval state=lower(coalesce(bgp_state, new_state))
| eval device=coalesce(host, device_name)
| sort device, peer, _time
| stats count as events count(eval(state="idle" OR state="active")) as down_events count(eval(state="established")) as up_events latest(state) as current_state latest(_time) as last_event by device, peer, peer_asn
| eval flapping=if(events > 4, "YES", "NO")
| eval severity=case(
    current_state!="established" AND flapping="YES", "CRITICAL -- BGP peer DOWN and flapping",
    current_state!="established", "WARNING -- BGP peer not Established (state: ".current_state.")",
    flapping="YES", "WARNING -- BGP peer flapping (currently established)",
    1==1, "OK")
| where severity != "OK"
| eval last_time=strftime(last_event, "%Y-%m-%d %H:%M:%S")
| sort severity, -events
```

### Step 3 — - Validate
(a) CLI: `show bgp summary` -- verify peer states and uptime.
(b) CLI: `show bgp neighbors <peer_ip>` -- check last reset reason.
(c) Verify route count: `show bgp ipv4 unicast summary` -- prefix limits.

### Step 4 — - Operationalize
Dashboard ("Network -- BGP Peering"):
* Row 1 -- Single-value: "Peers DOWN", "Flapping peers", "Total state changes (24h)".
* Row 2 -- BGP state change timeline.
* Row 3 -- Current BGP peer status table.

Alert: Critical (eBGP peer DOWN): routing impact, page NOC.

### Step 5 — - Troubleshooting

* **Hold timer expired** -- Peer not sending keepalives. Check: remote device health, CPU utilization on both ends (high CPU can delay BGP processing), and network path between peers.

* **Prefix limit exceeded** -- Peer sending more routes than configured maximum. CLI: `show bgp neighbors <ip> | include Prefix`. Increase limit or filter with route-map.

* **Authentication failure** -- MD5 password mismatch. Check: `neighbor <ip> password` on both sides. Verify clocks are synchronized (affects TCP MD5).

**IPv6 Coverage:** BGP IPv6 AFI/SAFI sessions use separate TCP connections from IPv4 BGP. Add `show bgp ipv6 unicast summary` to validation. Configure under `address-family ipv6 unicast`. IPv4 and IPv6 BGP instability may be independent — monitor both.

## SPL

```spl
index=network sourcetype="cisco:ios" "%BGP-5-ADJCHANGE" OR "%BGP-3-NOTIFICATION"
| rex "neighbor (?<neighbor_ip>\d+\.\d+\.\d+\.\d+|[0-9a-fA-F:]+)" | table _time host neighbor_ip _raw | sort -_time
```

## Visualization

Events timeline (critical), Status panel per BGP session, Table.

## Known False Positives

BGP sessions reset during planned maintenance, route policy changes, or upstream provider maintenance windows.

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
