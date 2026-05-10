<!-- AUTO-GENERATED from UC-5.20.44.json — DO NOT EDIT -->

---
id: "5.20.44"
title: "BGP IPv6 (MP-BGP AFI/SAFI 2/1) Session and Prefix Monitoring"
status: "verified"
criticality: "critical"
splunkPillar: "IT Operations"
---

# UC-5.20.44 · BGP IPv6 (MP-BGP AFI/SAFI 2/1) Session and Prefix Monitoring

> **Criticality:** Critical &middot; **Difficulty:** Advanced &middot; **Pillar:** IT Operations &middot; **Type:** Availability, Performance &middot; **Wave:** Walk &middot; **Status:** Verified

*The big highway routers that connect different parts of the internet share their road maps using BGP. For IPv6, they use a special section of BGP called 'IPv6 unicast.' If the connection between two highway routers drops, thousands of roads disappear from their maps instantly and traffic gets lost.*

---

## Description

Monitors MP-BGP IPv6 unicast (AFI 2/SAFI 1) session state and prefix stability across all BGP peerings — both eBGP (internet/transit providers) and iBGP (internal route distribution). A BGP session reset in the IPv6 address family can withdraw thousands of IPv6 prefixes in seconds, causing widespread connectivity loss. Unlike IPv4 BGP which has decades of operational maturity, IPv6 BGP is still being deployed in many enterprises, and misconfiguration is common — especially around next-hop resolution, address family activation, and maximum prefix limits.

## Value

BGP is the backbone routing protocol for IPv6 internet connectivity and increasingly for enterprise WAN (SD-WAN underlay, EVPN-VXLAN). A single BGP session carrying the IPv6 full table (200,000+ prefixes as of 2026) that resets withdraws all those prefixes simultaneously, causing a traffic black hole until the session re-establishes and the routes are re-advertised. Monitoring BGP IPv6 sessions provides the earliest possible warning of internet connectivity loss — typically 30-90 seconds before users report 'IPv6 internet is down'. Maximum prefix limit monitoring catches route leaks and hijacks before they impact production.

## Implementation

Collect BGP session state changes and prefix events from syslog. Track IPv6 address family specifically (AFI 2). Alert on session drops, max prefix violations, and prefix count anomalies. Correlate with peer AS information for external peering.

## Detailed Implementation

### Prerequisites
- BGP IPv6 address family configured on border and core routers.
- Syslog forwarding at severity 5 (notification) for BGP events.
- Knowledge of expected BGP IPv6 peer count, prefix counts, and AS relationships.

### Step 1 — Configure data collection

**Cisco IOS-XE — BGP event logging:**
```
router bgp 65001
 address-family ipv6 unicast
  bgp log-neighbor-changes
  neighbor 2001:db8:ffff::1 maximum-prefix 250000 80 restart 30
```
`bgp log-neighbor-changes` logs session state transitions. `maximum-prefix 250000 80 restart 30` sets a limit of 250,000 prefixes with a warning at 80% and automatic restart after 30 minutes if violated.

**Juniper Junos:**
```
set protocols bgp group transit-v6 family inet6 unicast prefix-limit maximum 250000 teardown 80 idle-timeout 30
```

Key syslog messages:
```
%BGP-5-NBR_RESET: Neighbor 2001:db8:ffff::1 reset (Peer closed the session)
%BGP-3-MAXPFX: No. of IPv6 Unicast prefixes received from 2001:db8:ffff::1 (VRF default) reaches 200000, max 250000
%BGP-5-ADJCHANGE: neighbor 2001:db8:ffff::1 Up
%BGP-5-ADJCHANGE: neighbor 2001:db8:ffff::1 Down BGP Notification sent/received
```

**Verification:**
```spl
index=network sourcetype="cisco:ios" "%BGP" earliest=-7d
| stats count by host
```

### Step 2 — Create the search and alert

**BGP IPv6 session down alert:**
```spl
index=network sourcetype="cisco:ios" "%BGP" ("ADJCHANGE" OR "NBR_RESET" OR "neighbor" AND ("Down" OR "down" OR "reset")) earliest=-1h
| rex field=_raw "(?:neighbor|Neighbor|peer)\s+(?<peer_addr>[0-9a-fA-F:.]+)"
| rex field=_raw "(?<reason>(?:Peer closed|Hold Timer|Notification|Admin|Interface flap|Route refresh|Prefix limit).*)"
| where match(peer_addr, ":")
| eval alert="BGP IPv6 session DOWN: " . host . " → " . peer_addr . " reason: " . coalesce(reason, "unknown")
| table _time, host, peer_addr, reason, alert
```
The `match(peer_addr, ":")` filter ensures only IPv6 peers (containing colons) are matched, excluding IPv4 BGP events.

**Maximum prefix violation alert:**
```spl
index=network sourcetype="cisco:ios" "%BGP" "MAXPFX" "IPv6" earliest=-1h
| rex field=_raw "(?:neighbor|Neighbor|peer)\s+(?<peer_addr>[0-9a-fA-F:.]+)"
| rex field=_raw "reaches\s+(?<current_count>\d+).*max\s+(?<max_limit>\d+)"
| eval pct_used=round(current_count / max_limit * 100, 1)
| eval severity=case(
    pct_used >= 100, "CRITICAL — session will be torn down",
    pct_used >= 90, "HIGH — approaching limit",
    pct_used >= 80, "WARNING — threshold warning",
    1=1, "INFO")
| table _time, host, peer_addr, current_count, max_limit, pct_used, severity
```

**IPv6 prefix count trending (via SNMP/gNMI):**
```spl
index=network sourcetype="sc4snmp:metric" metric_name="bgp.ipv6_prefixes_received" earliest=-7d
| timechart span=1h avg(metric_value) as avg_prefixes by host
| predict avg_prefixes as predicted algorithm=LLP5 future_timespan=0
| eval anomaly=if(abs(avg_prefixes - predicted) > predicted * 0.1, 1, 0)
```

### Step 3 — Validate
(a) **Session reset test (lab).** Reset a BGP IPv6 session (`clear bgp ipv6 unicast <peer>`). Verify the DOWN event appears in Splunk within 30 seconds.

(b) **Maximum prefix test (lab).** Set a low maximum prefix limit (e.g., 10) and advertise more than 10 prefixes from the peer. Verify the MAXPFX warning and session teardown are detected.

(c) **IPv6 vs IPv4 filter.** Verify the search correctly filters IPv6 peers (addresses with colons) from IPv4 peers (addresses with dots only).

### Step 4 — Operationalize

**Dashboard** ("IPv6 — BGP Routing Health"):
- Row 1 — Single-value: BGP IPv6 sessions Established/Total, sessions DOWN, max prefix warnings.
- Row 2 — Status table: all BGP IPv6 peers with current state, prefix count, and uptime.
- Row 3 — Timechart: session state events over 7 days.
- Row 4 — Prefix trending: IPv6 prefix count per peer over 30 days.

**Scheduling:** Session down alert real-time. Max prefix alert every 15 minutes. Prefix trending daily.

**Runbook:**
1. Session DOWN: check link status, verify BGP configuration, check for hold timer expiry (CPU overload or link quality), check notification message reason code.
2. Max prefix violation: verify with upstream provider — is this a legitimate growth or a route leak? Contact the peer NOC if unexpected.
3. Prefix count anomaly: check for route leaks, hijacks, or unintended route policy changes.

### Step 5 — Troubleshooting

- **BGP session carries both IPv4 and IPv6** — A single BGP session reset affects both address families. The syslog may show a generic `ADJCHANGE` without specifying the address family. Use `show bgp ipv6 unicast summary` to verify the IPv6 address family state specifically.

- **Next-hop resolution failure** — A common IPv6 BGP issue: the IPv6 next-hop advertised by the peer is not resolvable in the local routing table. The session remains Established but routes are not installed. Check `show bgp ipv6 unicast` for routes with `inaccessible` next-hop.

- **Route Reflector considerations** — In iBGP with route reflectors, the RR must have the IPv6 address family activated for each RR client. Missing AF activation means IPv6 routes are not reflected even though the BGP session is Established.

## SPL

```spl
index=network sourcetype="cisco:ios" "%BGP" earliest=-24h
| eval bgp_event=case(
    match(_raw, "(?i)neighbor.*(?:down|up|established|idle|active|connect)"), "session_change",
    match(_raw, "(?i)max.?prefix|maxprefix"), "max_prefix_violation",
    match(_raw, "(?i)ipv6.*(?:withdraw|update|announce)"), "prefix_event",
    1=1, null())
| where isnotnull(bgp_event)
| rex field=_raw "(?:neighbor|Neighbor|peer|Peer)\s+(?<peer_addr>[0-9a-fA-F:.]+)"
| rex field=_raw "(?:vrf|VRF)\s+(?<vrf_name>\S+)"
| rex field=_raw "(?:state|State).*?(?:to|->)\s*(?<new_state>\S+)"
| eval severity=case(
    match(new_state, "(?i)idle|down"), "CRITICAL",
    match(_raw, "max.?prefix"), "HIGH",
    match(new_state, "(?i)established"), "INFO",
    1=1, "WARNING")
| table _time, host, peer_addr, vrf_name, bgp_event, new_state, severity
```

## Visualization

(1) Status table: all BGP IPv6 sessions with current state. (2) Timechart: session events over 24 hours. (3) Single-value: sessions in Established state vs total configured. (4) Prefix trending: IPv6 prefix count over time per peer.

## Known False Positives

**Planned maintenance.** Peer router reboots or circuit maintenance cause expected session resets. Correlate with change windows.

**BGP graceful restart.** Peers with graceful restart (RFC 4724) maintain routes during a session reset. The session goes DOWN but routes are preserved for the restart timer duration. This is by design.

**Soft reconfiguration.** `clear bgp ipv6 unicast * soft` refreshes routes without resetting the session. Route refresh (RFC 2918) does the same. These generate prefix events but no session events.

**Route policy changes.** Applying a new route-map or prefix-list to a BGP peer may change the number of accepted/advertised prefixes. This is expected after configuration changes.

## References

- [RFC 4760 — Multiprotocol Extensions for BGP-4 (MP-BGP specification)](https://www.rfc-editor.org/rfc/rfc4760)
- [RFC 2545 — Use of BGP-4 Multiprotocol Extensions for IPv6 Inter-Domain Routing](https://www.rfc-editor.org/rfc/rfc2545)
- [RFC 9099 — Operational Security Considerations for IPv6 Networks (§2.2 — routing security)](https://www.rfc-editor.org/rfc/rfc9099)
