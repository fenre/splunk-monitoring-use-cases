<!-- AUTO-GENERATED from UC-5.20.48.json — DO NOT EDIT -->

---
id: "5.20.48"
title: "IPv6 Default Route Presence and Redundancy Verification"
status: "verified"
criticality: "critical"
splunkPillar: "IT Operations"
---

# UC-5.20.48 · IPv6 Default Route Presence and Redundancy Verification

> **Criticality:** Critical &middot; **Difficulty:** Intermediate &middot; **Pillar:** IT Operations &middot; **Type:** Availability &middot; **Wave:** Walk &middot; **Status:** Verified

*Every router needs to know the main road out to the internet — that's the default route. If this road disappears, the router is lost and can't send anything to the outside world. We check every router to make sure it knows at least one road out, and preferably two in case one road is closed.*

---

## Description

Verifies the presence, source, and redundancy of the IPv6 default route (`::/0`) on every router and L3 switch. A missing IPv6 default route means zero IPv6 internet connectivity — but in dual-stack networks, this failure is often silent because IPv4 continues to work. Users may experience subtle symptoms: IPv6-only services fail, Happy Eyeballs (RFC 8305) falls back to IPv4 adding latency, and AAAA-only domains become unreachable. This use case detects the missing or non-redundant default route before users report 'some websites are slow.'

## Value

The IPv6 default route is the single most important route in the routing table. Its absence breaks all IPv6 internet connectivity. In dual-stack environments, this failure is insidious because IPv4 masks the problem — users get slow fallback instead of complete failure, making the root cause harder to identify. Monitoring default route presence proactively catches the failure at the network layer, minutes before application-layer symptoms appear. Default route redundancy verification ensures that a single ISP or uplink failure does not remove the only IPv6 default route.

## Implementation

Periodically check the IPv6 routing table for the presence of ::/0. Verify it exists on all routers that should have it. Verify redundancy (multiple next-hops or multiple source protocols). Alert on default route loss or single-path non-redundancy.

## Detailed Implementation

### Prerequisites
- IPv6 default route configured on all routers that provide internet connectivity.
- A reference list of routers that SHOULD have an IPv6 default route.
- SNMP or CLI-based routing table collection.

### Step 1 — Configure data collection

**SNMP-based approach — poll inetCidrRouteTable for ::/0:**
```yaml
# SC4SNMP profile to check for IPv6 default route
profile: ipv6_default_route
frequency: 300
varBinds:
  - ['1.3.6.1.2.1.4.24.7.1.7.2.16.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0']  # inetCidrRouteIfIndex for ::/0
```

**CLI-based approach — periodic `show ipv6 route ::/0`:**
```
show ipv6 route ::/0
  Routing entry for ::/0
    Known via "bgp 65001", distance 20, metric 0
    Last update from 2001:db8:ffff::1 00:05:12 ago
    Routing Descriptor Blocks:
    * 2001:db8:ffff::1, from 2001:db8:ffff::1, 00:05:12 ago
      2001:db8:ffff::2, from 2001:db8:ffff::2, 00:05:12 ago
```

**Create the expected-default-route lookup:**
```csv
host,should_have_default_v6,minimum_paths
border-rtr-01,true,2
border-rtr-02,true,2
core-sw-01,true,1
access-sw-01,false,0
```
Upload as `ipv6_default_route_requirements.csv`.

**Verification:**
```spl
index=network sourcetype="cisco:ios" "::/0" earliest=-24h
| stats count by host
| lookup ipv6_default_route_requirements.csv host OUTPUT should_have_default_v6
| where should_have_default_v6="true"
```

### Step 2 — Create the search and alert

**Missing default route detection:**
```spl
| inputlookup ipv6_default_route_requirements.csv
| where should_have_default_v6="true"
| join type=left host [
    search index=network sourcetype="cisco:ios" "::/0" earliest=-1h
    | rex field=_raw "(?:via|next-hop)\s+(?<next_hop>[0-9a-fA-F:.]+)"
    | stats count values(next_hop) as active_next_hops by host
  ]
| eval status=case(
    isnull(count) OR count=0, "CRITICAL — no IPv6 default route",
    mvcount(active_next_hops) < minimum_paths, "WARNING — insufficient default route redundancy",
    1=1, "OK")
| where status != "OK"
| table host, status, active_next_hops, minimum_paths
```
Trigger: any CRITICAL result (missing default route) or WARNING (non-redundant).

**Default route withdrawal detection (real-time):**
```spl
index=network sourcetype="cisco:ios" (::/0 OR "default route") ("withdraw" OR "removed" OR "deleted" OR "unreachable") earliest=-15m
| rex field=_raw "(?:via|from)\s+(?<withdrawn_via>[0-9a-fA-F:.]+)"
| eval alert="IPv6 default route withdrawn via " . withdrawn_via . " on " . host
| table _time, host, withdrawn_via, alert
```

### Step 3 — Validate
(a) **Default route present.** On a router with a known IPv6 default route, verify the search confirms its presence.

(b) **Default route removed.** Remove the default route (`no ipv6 route ::/0 ...`). Verify the missing default route alert fires within 15 minutes.

(c) **Redundancy check.** On a router with two default routes (primary and backup), remove one. Verify the redundancy warning fires.

### Step 4 — Operationalize

**Dashboard** ("IPv6 — Default Route Health"):
- Row 1 — Single-value: routers with default route / total required, routers with redundant default routes / total required.
- Row 2 — Status table: per-router default route status (green=redundant OK, yellow=single path, red=missing).
- Row 3 — Timechart: default route events (withdrawals, additions) over 7 days.

**Scheduling:** Missing default route check every 15 minutes. Redundancy check hourly. Withdrawal detection continuous.

**Runbook:**
1. Missing default route: check BGP session to upstream provider (UC-5.20.44). Check static route configuration. Check OSPFv3 default-information originate.
2. Non-redundant: evaluate adding a second default route path (second ISP, second uplink).
3. Default route withdrawn: check upstream BGP session. If BGP, check for session reset or max-prefix violation.

### Step 5 — Troubleshooting

- **IPv6 default route via RA vs routing table** — Hosts learn their default gateway from Router Advertisements. Routers learn their default route from BGP/OSPF/static. These are different mechanisms. A router may have no `::/0` in its routing table but still send RAs to hosts with itself as default gateway. The RA gateway is based on the router's link-local address, not the routing table.

- **VRF-aware default route** — In VRF environments, the default route must be present in the correct VRF routing table. Check `show ipv6 route vrf <name> ::/0`.

- **Equal-cost multipath (ECMP)** — When two default routes have equal metrics, the router load-balances across both. The routing table shows both next-hops. If one next-hop fails, the router continues using the other. Monitor for the transition from 2 next-hops to 1 as a redundancy degradation.

## SPL

```spl
index=network sourcetype="cisco:ios" ("ipv6 route ::/0" OR "default route" OR "%BGP" OR "%OSPF" OR "%ISIS") ("::/0" OR "default") earliest=-1h
| rex field=_raw "(?:via|next-hop|nexthop)\s+(?<next_hop>[0-9a-fA-F:.]+)"
| rex field=_raw "(?:metric|distance|ad)\s+(?<metric>\d+)"
| eval protocol=case(
    match(_raw, "(?i)bgp"), "BGP",
    match(_raw, "(?i)ospf"), "OSPFv3",
    match(_raw, "(?i)isis"), "IS-IS",
    match(_raw, "(?i)static"), "Static",
    match(_raw, "(?i)connected"), "Connected",
    1=1, "unknown")
| stats count values(next_hop) as next_hops values(protocol) as source_protocols by host
| eval redundant=if(mvcount(next_hops) >= 2, "yes", "NO — single default route")
| eval has_default=if(count > 0, "yes", "NO DEFAULT ROUTE")
```

## Visualization

(1) Status table: per-router default route presence (green=redundant, yellow=single, red=missing). (2) Timechart: default route events over 7 days — should be flat/stable. (3) Single-value: routers without IPv6 default route. (4) Map: geographic distribution of default route health.

## Known False Positives

**Stub networks.** Small stub networks that use a single ISP connection will legitimately have only one default route. Assess redundancy requirements based on network criticality.

**VRF-specific routing.** VRFs may have different default route configurations. A VRF used for management traffic may not need an IPv6 default route if IPv6 management is not required.

**Default route via RA.** On some network segments, the default route is provided by Router Advertisements to hosts. The L3 switch serving these hosts may not have a default route in its own routing table if it is a stub/access switch — the default route is handled by the distribution/core layer.

## References

- [RFC 8305 — Happy Eyeballs Version 2: Better Connectivity Using Concurrency (dual-stack fallback behaviour)](https://www.rfc-editor.org/rfc/rfc8305)
- [RFC 9099 — Operational Security Considerations for IPv6 Networks (§2.2 — default route considerations)](https://www.rfc-editor.org/rfc/rfc9099)
