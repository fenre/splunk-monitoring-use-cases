<!-- AUTO-GENERATED from UC-5.20.45.json — DO NOT EDIT -->

---
id: "5.20.45"
title: "IPv6 Routing Table Size and Prefix Churn Monitoring"
status: "verified"
criticality: "high"
splunkPillar: "IT Operations"
---

# UC-5.20.45 · IPv6 Routing Table Size and Prefix Churn Monitoring

> **Criticality:** High &middot; **Difficulty:** Intermediate &middot; **Pillar:** IT Operations &middot; **Type:** Performance, Availability &middot; **Wave:** Walk &middot; **Status:** Verified

*Every router keeps a big address book of how to reach every part of the IPv6 internet. This address book keeps growing as more networks connect. But the router's memory for this book has a limit — like a filing cabinet that can only hold so many folders.*

---

## Description

Monitors the IPv6 routing table size, prefix churn rate, and TCAM/FIB utilization across the router fleet. IPv6 routing table growth impacts memory consumption and hardware forwarding capacity. Excessive prefix churn — rapid route additions and withdrawals — indicates routing instability and can overwhelm CPU on lower-end platforms. TCAM/FIB exhaustion causes routes to be processed in software (slow path), dramatically degrading forwarding performance.

## Value

TCAM/FIB exhaustion is a cliff event — performance is fine until the table is full, then it degrades catastrophically as routes overflow to software forwarding. Monitoring utilisation and trending allows proactive upgrades or route-filtering adjustments before the cliff is reached. Prefix churn monitoring detects routing instability (flapping peers, route oscillation, redistribution loops) that may not be visible in individual session monitoring (UC-5.20.43, UC-5.20.44) because the churn may come from many sources simultaneously.

## Implementation

Poll IPv6 routing table counters via SNMP (ipCidrRouteNumber / inetCidrRouteNumber for IPv6) or CLI (`show ipv6 route summary`). Track total prefix count, per-protocol counts, and TCAM/FIB utilization. Baseline and alert on anomalies.

## Detailed Implementation

### Prerequisites
- SNMP polling configured for routing table MIBs (IP-FORWARD-MIB for inetCidrRouteNumber, CISCO-CEF-MIB for cefFIBSummary).
- Alternatively, periodic CLI collection: `show ipv6 route summary` and `show platform hardware fed switch active fwd-asic resource tcam utilization`.
- Baseline data of at least 7 days for meaningful trend analysis.

### Step 1 — Configure data collection

**SNMP polling via SC4SNMP:**
```yaml
profile: ipv6_routing_table
frequency: 300
varBinds:
  - ['1.3.6.1.2.1.4.24.6']  # inetCidrRouteNumber (total routes including IPv6)
  - ['1.3.6.1.4.1.9.9.492.1.1.1.1.1']  # cefFIBSummaryFwdPrefixes (Cisco CEF)
```

**CLI-based collection (Cisco IOS-XE):**
```
show ipv6 route summary
  Route Source    Networks    Subnets     Replicates  Overhead    Memory (bytes)
  connected       4           4           0           384         1024
  static          1           1           0           96          256
  ospf 1          45          45          0           4320        11520
  bgp 65001       220450      220450      0           21163200    56435200
  Total           220500      220500      0           21168000    56448000
```

**TCAM utilization (Cisco Catalyst 9000):**
```
show platform hardware fed switch active fwd-asic resource tcam utilization
  CAM Utilization for ASIC [0]
  Table     Max       Used      %Used
  IPv6      16384     12500     76%
```

**Verification:**
```spl
index=network (sourcetype="sc4snmp:metric" metric_name="ipv6.routes*") OR (sourcetype="cisco:ios" "route summary") earliest=-24h
| stats count by sourcetype
```

### Step 2 — Create the search and alert

**TCAM/FIB utilization alert:**
```spl
index=network sourcetype="sc4snmp:metric" metric_name="ipv6.tcam_utilization" OR metric_name="ipv6.fib_utilization"
| stats latest(metric_value) as utilization_pct by host
| where utilization_pct > 80
| eval severity=case(
    utilization_pct > 95, "CRITICAL — TCAM nearly full, routes will overflow to software",
    utilization_pct > 90, "HIGH — upgrade TCAM or apply route filters",
    utilization_pct > 80, "WARNING — approaching TCAM capacity")
| eval action="Consider: (1) route summarisation, (2) prefix-list filtering, (3) SDM template change, (4) hardware upgrade"
```
Trigger: >80% utilization.

**Prefix churn detection:**
```spl
index=network sourcetype="cisco:ios" ("%BGP" OR "%OSPF" OR "%ISIS") ("install" OR "withdraw" OR "add" OR "delete") ("ipv6" OR "IPv6" OR "inet6") earliest=-1h
| eval route_event=case(
    match(_raw, "(?i)install|add|announce"), "add",
    match(_raw, "(?i)withdraw|delete|remove"), "remove",
    1=1, "other")
| timechart span=5m count by route_event
| eval total_churn=(add + remove)
| where total_churn > 500
```
Trigger: more than 500 route additions + withdrawals in 5 minutes indicates routing instability.

**Routing table growth projection:**
```spl
index=network sourcetype="sc4snmp:metric" metric_name="ipv6.routes_total" earliest=-30d
| timechart span=1d avg(metric_value) as daily_routes by host
| predict daily_routes as predicted_routes algorithm=LLP5 future_timespan=30
```

### Step 3 — Validate
(a) **Routing table count accuracy.** Compare Splunk metric values with `show ipv6 route summary` on 5 routers. Values should match within 1%.

(b) **TCAM validation.** Compare Splunk TCAM metric with `show platform hardware fed switch active fwd-asic resource tcam utilization`. Values should match.

(c) **Churn test.** Flap an OSPFv3 adjacency that carries 50+ IPv6 prefixes. Verify the churn detection fires.

### Step 4 — Operationalize

**Dashboard** ("IPv6 — Routing Table Health"):
- Row 1 — Gauges: TCAM/FIB utilization per router platform (green <70%, yellow 70-85%, red >85%).
- Row 2 — Timechart: IPv6 routing table size over 30 days with trend projection.
- Row 3 — Stacked bar: prefix count by protocol (BGP, OSPFv3, IS-IS, connected, static).
- Row 4 — Rate chart: prefix churn (adds + removes) per hour.
- Row 5 — Table: routers with TCAM utilization >70%, sorted by utilization.

**Scheduling:** TCAM alert every 5 minutes. Churn detection every 5 minutes. Trend projection daily.

**Runbook:**
1. TCAM >90%: immediate — evaluate route filters, summarisation, or SDM template change.
2. TCAM >95%: emergency — routes will overflow to software forwarding. Impact: packet loss, high CPU.
3. High churn: identify the routing protocol source. Check for flapping adjacencies, redistribution loops, or upstream instability.
4. Growth projection exceeds TCAM: plan hardware upgrade or route-filtering strategy.

### Step 5 — Troubleshooting

- **SNMP MIB differences** — `inetCidrRouteNumber` counts both IPv4 and IPv6 routes. For IPv6-only counts, use platform-specific MIBs (Cisco CEF MIB, Juniper routing-table MIB) or parse CLI output.

- **TCAM partitioning varies by platform** — Different Cisco Catalyst 9000 SDM templates allocate different amounts of TCAM to IPv6. The `network-advantage` template allocates more than `vlan-default`. Check `show sdm prefer` to understand the current allocation.

- **Route count vs prefix count** — A single prefix may have multiple routes (ECMP paths, backup routes). The routing table 'route count' may be higher than the 'prefix count'. TCAM stores prefixes (after best-path selection), not all routes.

## SPL

```spl
index=network sourcetype="sc4snmp:metric" (metric_name="ipv6.routes_total" OR metric_name="ipv6.routes_by_protocol.*" OR metric_name="ip.fib_utilization") earliest=-7d
| timechart span=1h avg(metric_value) as route_count by metric_name
```

## Visualization

(1) Timechart: IPv6 routing table size over 30 days — trend line with projection. (2) Gauge: TCAM/FIB utilization % per platform. (3) Stacked area: prefix count by protocol (BGP, OSPF, connected, static). (4) Rate chart: prefix additions/withdrawals per hour.

## Known False Positives

**BGP full table reception.** When a router first receives a full BGP IPv6 table from an upstream provider, the routing table jumps from near-zero to ~220K prefixes. This is expected during initial peering or session re-establishment.

**Route summarization changes.** Deploying or removing route summarisation changes the prefix count significantly. This is an expected operational event.

**TCAM partitioning.** On platforms with configurable TCAM partitioning (e.g., Cisco Catalyst 9000 SDM templates), changing the IPv6 TCAM allocation changes the utilization percentage without changing the number of routes.

## References

- [APNIC IPv6 Routing Table Size Report — real-time DFZ tracking](https://bgp.potaroo.net/v6/as2.0/index.html)
- [RFC 9099 — Operational Security Considerations for IPv6 Networks (§2.2.2 — routing table management)](https://www.rfc-editor.org/rfc/rfc9099)
- [Cisco FIB/TCAM Architecture and Capacity Planning Guide](https://www.cisco.com/c/en/us/)
