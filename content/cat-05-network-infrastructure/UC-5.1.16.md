<!-- AUTO-GENERATED from UC-5.1.16.json — DO NOT EDIT -->

---
id: "5.1.16"
title: "Route Table Flapping"
criticality: "critical"
splunkPillar: "Observability"
---

# UC-5.1.16 · Route Table Flapping

> **Criticality:** Critical &middot; **Difficulty:** Intermediate &middot; **Pillar:** Observability &middot; **Type:** Anomaly

*We help you know early when something looks wrong with route table flapping so the team can act before it grows into a bigger outage.*

---

## Description

Unstable routes cause packet loss and reachability failures. Detecting flapping routes prevents cascading network outages across your infrastructure.

## Value

Network engineers detect routing table instability including route flapping, excessive SPF recalculations, and damping events that cause traffic path oscillation and convergence delays.

## Implementation

Collect syslog from all routers. Alert on >5 route changes for the same prefix in 10 minutes. Correlate with interface flaps. Use `streamstats` to detect patterns.

## Detailed Implementation

### Prerequisites
* Route table change syslog messages. Data in `index=network` with `sourcetype=cisco:ios` or vendor-specific sourcetypes. Key events: route additions/withdrawals, next-hop changes. BGP: `%BGP-5-ADJCHANGE`, route flap damping. OSPF: `%OSPF-5-ADJCHG`, SPF recalculations.
* Route flapping: rapid alternation of route availability or next-hop changes. Causes traffic path oscillation, increased CPU on routers processing updates, and potential black-holing during convergence. BGP route flap damping can suppress unstable routes.

### Step 1 — - Configure data collection
```
# Cisco IOS -- route change logging
# BGP debug (use cautiously in production):
# debug ip bgp updates (generates high volume)
# Better: use EEM script to detect flapping

# SNMP: poll ipCidrRouteTable periodically
# Or use BGP-4-MIB for prefix count trending
```
Verify:
```spl
index=network earliest=-4h
| where match(_raw, "(?i)route.*flap|route.*damp|SPF.*calc|route.*withdraw|route.*install|next.?hop.*change")
| stats count by host
```

### Step 2 — - Create the search and alert

**Primary search -- Route flapping detection:**
```spl
index=network earliest=-4h
| where match(_raw, "(?i)BGP.*ADJ|OSPF.*ADJ|route.*change|route.*flap|SPF.*calc|route.*withdraw|route.*install|next.?hop.*change|route.*unreachable")
| eval device=coalesce(host, device_name)
| eval protocol=case(
    match(_raw, "(?i)BGP"), "BGP",
    match(_raw, "(?i)OSPF"), "OSPF",
    match(_raw, "(?i)EIGRP"), "EIGRP",
    match(_raw, "(?i)ISIS|IS-IS"), "IS-IS",
    match(_raw, "(?i)static"), "STATIC",
    1==1, "ROUTING")
| eval event_type=case(
    match(_raw, "(?i)withdraw|remove|unreachable|down|lost"), "ROUTE_WITHDRAWN",
    match(_raw, "(?i)install|add|learned|up"), "ROUTE_INSTALLED",
    match(_raw, "(?i)SPF|calc"), "SPF_CALCULATION",
    match(_raw, "(?i)flap|damp"), "ROUTE_DAMPENED",
    1==1, "ROUTE_CHANGE")
| bin _time span=5m
| stats count as events count(eval(event_type="ROUTE_WITHDRAWN")) as withdrawals count(eval(event_type="SPF_CALCULATION")) as spf_runs by _time, device, protocol
| eval severity=case(
    events > 100, "CRITICAL -- severe route instability (".events." events/5min)",
    spf_runs > 5, "WARNING -- excessive SPF recalculations",
    withdrawals > 20, "WARNING -- high route withdrawal rate",
    events > 20, "INFO -- moderate routing activity",
    1==1, "OK")
| where severity != "OK"
| sort severity, -events
```

### Step 3 — - Validate
(a) CLI: `show ip route summary` -- check route count and stability.
(b) CLI: `show ip bgp flap-statistics` (if BGP) -- check damped prefixes.
(c) CLI: `show ip ospf statistics` -- check SPF run count.

### Step 4 — - Operationalize
Dashboard ("Network -- Route Stability"):
* Row 1 -- Single-value: "Routing events (4h)", "SPF runs", "Routes dampened".
* Row 2 -- Routing event rate timechart by protocol.

Alert: Critical (>100 routing events in 5 min): major routing instability.

### Step 5 — - Troubleshooting

* **BGP route flapping** -- Check peer stability (UC-5.1.4). Enable BGP route flap damping to suppress unstable prefixes: `bgp dampening`. Identify the upstream source of instability.

* **OSPF SPF storms** -- Frequent SPF recalculations indicate topology changes. Tune SPF timers: `timers throttle spf <initial> <hold> <max>`. Identify the link/area causing changes.

* **Route black-hole during convergence** -- Traffic may be dropped while routes reconverge. Implement BFD (Bidirectional Forwarding Detection) for faster failure detection and convergence.

**IPv6 Coverage:** IPv6 and IPv4 routing tables are separate RIBs — instability in one does not necessarily affect the other. Add `show ipv6 route summary` and `show bgp ipv6 unicast flap-statistics` to validation.

## SPL

```spl
index=network sourcetype="cisco:ios" "ROUTING" OR "RT_ENTRY" OR "%DUAL-5-NBRCHANGE" OR "%BGP-5-ADJCHANGE" OR "%OSPF-5-ADJCHG"
| rex "(?<protocol>BGP|OSPF|EIGRP).*?(?<prefix>(?:\d+\.){3}\d+(?:/\d+)?|[0-9a-fA-F:.]+/[0-9]{1,3})"
| bin _time span=10m | stats count as changes by _time, host, protocol, prefix
| where changes > 5 | sort -changes
```

## Visualization

Timeline (flapping events), Table (prefix, host, count), Line chart (change frequency).

## Known False Positives

Policy or static edits, redistribution experiments, and upstream path changes can move routes. Verify against maintenance windows and lab VRFs.

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
