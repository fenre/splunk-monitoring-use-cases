<!-- AUTO-GENERATED from UC-5.1.66.json — DO NOT EDIT -->

---
id: "5.1.66"
title: "NDP Neighbor Table Size Trending and Capacity Monitoring"
status: "verified"
criticality: "high"
splunkPillar: "Observability"
---

# UC-5.1.66 · NDP Neighbor Table Size Trending and Capacity Monitoring

> **Criticality:** High &middot; **Difficulty:** Intermediate &middot; **Pillar:** Observability &middot; **Type:** Capacity, Availability &middot; **Wave:** Walk &middot; **Status:** Verified

*We keep track of how full the IPv6 address book is on each router. Unlike the old phone book (ARP), the new one (NDP) fills up faster because every device has multiple entries. If the address book gets full, the router can't find new devices and they lose network access. We watch the fill level and warn before it overflows.*

---

## Description

Tracks the IPv6 NDP neighbor cache size over time and alerts when approaching the platform's maximum capacity. This is the IPv6 counterpart to ARP table size monitoring. IPv6 generates significantly more neighbor entries than IPv4 ARP because each host registers multiple addresses (link-local, global unicast, temporary/privacy addresses).

## Value

When the NDP neighbor cache fills up, the router cannot resolve new IPv6 addresses, causing traffic blackholing for any host not already in the cache. Unlike ARP tables, IPv6 NDP caches fill faster due to multiple addresses per host and are more susceptible to exhaustion attacks (RFC 6583). Proactive trending prevents silent outages and identifies subnets that need NDP cache tuning or smaller prefix assignments.

## Implementation

Poll NDP neighbor table size via SNMP (ipv6NetToMediaTable). Supplement with syslog monitoring for table overflow events. Alert on >80% utilization.

## Detailed Implementation

### Prerequisites
- SNMP polling of IPv6 MIBs enabled on routers and Layer 3 switches.
- SC4SNMP or SNMP Modular Input configured to poll `ipv6NetToMediaTable` (OID 1.3.6.1.2.1.55.1.12).
- Create `ndp_cache_limits.csv` lookup with columns: `host`, `max_entries`. Populate from platform documentation:
  - Cisco Catalyst 9300: default 16384 entries (`ipv6 nd cache interface-limit`)
  - Cisco ASR 1000: default 65536 entries
  - Juniper MX: default varies by PFE type (~131072)
  - Linux: `cat /proc/sys/net/ipv6/neigh/default/gc_thresh3` (typically 1024 default)
- Syslog from routers/switches via `TA-cisco_ios` for overflow events.

### Step 1 — Configure SNMP polling
Add ipv6NetToMediaTable to the SNMP polling profile in SC4SNMP:
```yaml
profiles:
  ndp_cache:
    frequency: 300
    varBinds:
      - ['1.3.6.1.2.1.55.1.12']
```
Alternatively, poll via CLI and send to Splunk:
```bash
show ipv6 neighbors statistics | include Total
```
This returns the total NDP entries per interface.

### Step 2 — Create monitoring searches

**Primary search (SNMP-based):**
The main SPL query (above) trends NDP cache utilization against platform limits.

**Syslog-based overflow detection (immediate):**
```spl
index=network (sourcetype="cisco:ios" OR sourcetype="cisco:iosxe") earliest=-4h
  ("ND" AND ("table full" OR "overflow" OR "limit reached" OR "adjacency limit"))
| stats count as overflow_events by host
| where overflow_events > 0
```

**Growth rate analysis (capacity planning):**
```spl
index=network sourcetype="sc4snmp:metric" metric_name="ipv6NetToMediaTable.count" earliest=-30d
| timechart span=1d avg(metric_value) as daily_avg by host
| untable _time host daily_avg
| eventstats first(daily_avg) as start_val last(daily_avg) as end_val by host
| eval growth_pct=round((end_val-start_val)/start_val*100, 1)
| dedup host
| where growth_pct > 20
| table host, start_val, end_val, growth_pct
```

### Step 3 — Validate
(a) On a router, compare `show ipv6 neighbors statistics` output with the SNMP-polled values in Splunk. They should match within one poll interval.
(b) Verify the `ndp_cache_limits.csv` lookup contains accurate platform limits by checking `show running-config | include nd cache` on each platform.
(c) Confirm the growth rate analysis produces reasonable projections over 30 days.
(d) Expected NDP entries per host: 2-5 addresses (1 link-local + 1 global + 0-3 temporary privacy addresses). Multiply by active host count to estimate baseline.

### Step 4 — Operationalize
Dashboard ("NDP Cache Capacity"):
- Row 1 — Gauge or single-value: worst NDP cache utilization across fleet.
- Row 2 — Table: host, current_entries, cache_limit, utilization_pct, status. Sorted by utilization descending.
- Row 3 — Timechart: NDP cache size trend over 30 days per router (identify growth trajectory).
- Row 4 — Growth rate table: routers with >20% monthly growth.

Alerting:
- >80% NDP cache utilization: Page network operations. Investigate if growth is organic (more hosts) or attack (NDP exhaustion, RFC 6583).
- Syslog table overflow: Immediate page — active connectivity impact.

### Step 5 — Troubleshooting
- **NDP cache growing unexpectedly fast.** Check for NDP exhaustion attack (see UC-5.20.139). An attacker scanning the /64 forces the router to create INCOMPLETE entries for each probed address.
- **Cache filled with STALE entries.** NDP entries don't expire as aggressively as ARP. Tune with `ipv6 nd cache expire 300` (5 minutes) on Cisco to age out STALE entries faster.
- **Linux hosts: gc_thresh3 too low.** Default is often 1024, insufficient for busy routers. Increase: `sysctl -w net.ipv6.neigh.default.gc_thresh3=16384`.
- **Point-to-point links: use /127 or /126.** On router-to-router links, using /64 creates a massive attack surface for NDP exhaustion. Use /127 (RFC 6164) to limit the neighbor cache to 2 entries per link.

## SPL

```spl
index=network (sourcetype="sc4snmp:metric" OR sourcetype="snmp:metric") earliest=-7d
  metric_name="ipv6NetToMediaTable.count" OR metric_name="ipv6IfStatsInReceives"
| eval ndp_entries=if(metric_name="ipv6NetToMediaTable.count", metric_value, null())
| stats latest(ndp_entries) as current_entries by host, _time
| bin _time span=1h
| stats avg(current_entries) as avg_entries max(current_entries) as max_entries by host
| lookup ndp_cache_limits.csv host OUTPUT max_entries as cache_limit
| eval utilization_pct=if(isnotnull(cache_limit), round(max_entries/cache_limit*100, 1), null())
| eval status=case(
    utilization_pct > 90, "CRITICAL — NDP cache at " . utilization_pct . "% capacity",
    utilization_pct > 80, "WARNING — NDP cache at " . utilization_pct . "% capacity",
    utilization_pct > 60, "ELEVATED — NDP cache at " . utilization_pct . "% capacity",
    isnotnull(utilization_pct), "OK — NDP cache at " . utilization_pct . "%",
    1=1, "UNKNOWN — cache limit not configured in lookup")
| sort -utilization_pct
```

## Visualization

(1) Gauge: worst NDP cache utilization. (2) Table: routers with cache utilization. (3) Timechart: 30-day NDP cache growth trend. (4) Alert: overflow events.

## Known False Positives

**Privacy extensions generating many addresses.** Hosts using RFC 8981 temporary addresses may have 3-5 IPv6 addresses simultaneously. This is normal and increases NDP cache size. Account for this when sizing cache limits (multiply expected host count by 3-5).

**Network scanning tools.** Authorized vulnerability scanners probing IPv6 addresses can temporarily spike NDP cache entries. Schedule scans and correlate timestamps.

**VM density.** Hypervisors with many VMs per VLAN generate proportionally more NDP entries. This is a capacity planning concern, not an anomaly.

## References

- [RFC 6583 — Operational Neighbor Discovery Problems](https://www.rfc-editor.org/rfc/rfc6583)
- [RFC 4861 — Neighbor Discovery for IPv6](https://www.rfc-editor.org/rfc/rfc4861)
- [RFC 6164 — Using 127-Bit IPv6 Prefixes on Inter-Router Links](https://www.rfc-editor.org/rfc/rfc6164)
