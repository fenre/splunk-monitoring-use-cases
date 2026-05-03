<!-- AUTO-GENERATED from UC-5.11.8.json — DO NOT EDIT -->

---
id: "5.11.8"
title: "BGP Prefix Count and Route Churn Monitoring"
criticality: "high"
splunkPillar: "Security"
---

# UC-5.11.8 · BGP Prefix Count and Route Churn Monitoring

> **Criticality:** High &middot; **Difficulty:** Intermediate &middot; **Pillar:** Security &middot; **Type:** Performance, Security

*We help you see when route tables are shaking more than usual, which can be the first sign of a bad peering, filter mistake, or unstable link upstream.*

---

## Description

A sudden jump in received BGP prefixes could indicate a route leak, hijack, or misconfigured peer advertising a full table into a leaf switch. Conversely, a prefix count drop means routes are being withdrawn — potentially black-holing traffic. Streaming prefix counts via gNMI at 30-second intervals detects these events far faster than waiting for syslog or SNMP traps.

## Value

Network operations teams detect BGP route anomalies (sudden prefix drops/increases, route churn, RIB capacity exhaustion) in near real time, enabling rapid response to routing instability, network partitions, and route leaks.

## Implementation

Subscribe to BGP AFI-SAFI state at 30s intervals. Baseline normal prefix counts per peer. Alert on >10% change in a 5-minute window or absolute change >1000 prefixes. A full BGP table leak (800k+ IPv4 prefixes) into a leaf with 64k TCAM will crash forwarding — detect it before the FIB overflows. Correlate with CPU spikes (UC-5.11.4) during convergence events.

## Detailed Implementation

### Prerequisites
- Telegraf gNMI collector with SAMPLE subscription to BGP RIB (Routing Information Base) counters. OpenConfig path: `/network-instances/network-instance/protocols/protocol/bgp/global/state` for total prefix counts, or `/network-instances/network-instance/protocols/protocol/bgp/neighbors/neighbor/afi-safis/afi-safi/state/prefixes` for per-neighbor prefix counts. Key metrics: `received`, `installed`, `sent`.
- Understanding BGP prefix counts: in a VXLAN EVPN fabric, each host/VM creates an EVPN Type-2 (MAC/IP) route and potentially Type-5 (IP prefix) route. A fabric with 10,000 VMs generates ~10,000-20,000 EVPN routes. Sudden prefix count changes indicate: (a) mass VM migration (planned — capacity event), (b) network partition (unplanned — routes withdrawn), (c) route leak or hijack (security event), (d) BGP optimizer or policy change.
- Route churn: BGP advertises routes when they appear and withdraws them when they disappear. High churn (many advertisements + withdrawals per minute) stresses the control plane CPU and can delay convergence. Monitor churn independently from absolute prefix count.
- For WAN BGP: internet full table is ~950K+ IPv4 prefixes (2024). A sudden drop of >10% could indicate a provider depeering event. A sudden increase could indicate a route leak.

### Step 1 — Configure data collection
Telegraf subscription:
```toml
[[inputs.gnmi.subscription]]
  name = "openconfig_bgp_prefixes"
  origin = "openconfig"
  path = "/network-instances/network-instance/protocols/protocol/bgp/neighbors/neighbor/afi-safis/afi-safi/state/prefixes"
  subscription_mode = "sample"
  sample_interval = "30s"
```

Verify prefix data:
```spl
| mstats latest("openconfig_bgp_prefixes.received") AS received WHERE index=gnmi_metrics BY host, neighbor_address, afi_safi_name span=5m
| stats sum(received) as total_received by host, afi_safi_name
```

### Step 2 — Create the search and alert

**Primary search — Prefix count anomaly detection:**
```spl
| mstats latest("openconfig_bgp_prefixes.received") AS received latest("openconfig_bgp_prefixes.installed") AS installed WHERE index=gnmi_metrics BY host, neighbor_address, afi_safi_name span=5m earliest=-24h
| eventstats avg(received) AS avg_received stdev(received) AS std_received by host, neighbor_address, afi_safi_name
| eval upper=avg_received + (3 * std_received)
| eval lower=avg_received - (3 * std_received)
| where received > upper OR received < lower
| eval change_type=if(received > upper, "INCREASE", "DECREASE")
| eval deviation_pct=round(100*(received-avg_received)/avg_received, 1)
| lookup bgp_peers.csv host neighbor_address OUTPUT peer_asn peer_description
| sort -abs(deviation_pct)
```

#### Understanding this SPL: Detects sudden changes in prefix counts using 3-sigma statistical thresholds. A decrease suggests route withdrawal (peer down, policy change, or network partition). An increase suggests new routes (route leak, new peering, or configuration change). The `deviation_pct` quantifies the magnitude of change.

**Route churn detection (high advertisement/withdrawal rate):**
```spl
| mstats rate_avg("openconfig_bgp_prefixes.received") AS received_rate rate_avg("openconfig_bgp_prefixes.installed") AS installed_rate WHERE index=gnmi_metrics BY host, neighbor_address span=1m
| eval churn_rate=abs(received_rate) + abs(installed_rate)
| where churn_rate > 10
| eventstats avg(churn_rate) AS avg_churn stdev(churn_rate) AS std_churn by host, neighbor_address
| where churn_rate > avg_churn + (3 * std_churn)
| eval churn_factor=round(churn_rate/if(avg_churn>0, avg_churn, 1), 1)
| lookup bgp_peers.csv host neighbor_address OUTPUT peer_asn peer_description
| sort -churn_factor
```

#### Understanding this SPL: Route churn = rate of change in prefix counts. Normal churn is low (a few routes per minute). High churn (many changes per minute) indicates instability: flapping links, oscillating routing policies, or a router with intermittent forwarding. `rate_avg()` on the prefix counter captures the velocity of change.

**RIB capacity monitoring:**
```spl
| mstats latest("openconfig_bgp_prefixes.received") AS received WHERE index=gnmi_metrics BY host, neighbor_address, afi_safi_name
| stats sum(received) AS total_prefixes by host, afi_safi_name
| lookup device_capacity.csv host OUTPUT max_routes platform
| eval utilization_pct=if(isnotnull(max_routes), round(100*total_prefixes/max_routes, 1), null())
| where utilization_pct > 70 OR total_prefixes > 500000
| sort -utilization_pct
```

### Step 3 — Validate
(a) On the device, check: `show bgp summary` for prefix counts per neighbor. Compare with the `mstats` received count.
(b) Test: advertise a batch of test routes from a route generator and verify the prefix count increase appears in the anomaly detection.
(c) For internet full table routers: verify the total prefix count is approximately current (check cidr-report.org for reference).

### Step 4 — Operationalize
Dashboard ("Network — BGP Route Health"):
- Row 1 — Single-value tiles: "Total BGP prefixes (fabric)", "Prefix anomalies (24h)", "Active churn events", "RIB utilization (max)".
- Row 2 — Timechart: total received prefixes per neighbor over 24h.
- Row 3 — Anomaly table: host, neighbor, afi_safi, received, deviation_pct, change_type.
- Row 4 — Route churn timeline: churn_rate over 24h with anomaly markers.

Alerting:
- Critical (prefix count drops > 30% on any peer): possible network partition or major outage — page NOC.
- Critical (RIB utilization > 90%): router at risk of route table overflow — add memory or reduce prefix count.
- High (route churn > 5x baseline for 5+ minutes): unstable routing — investigate flapping.
- Warning (prefix count increases > 20% on internet peer): possible route leak — verify with upstream provider.

Runbook:
1. **Sudden prefix drop**: Check if the BGP peer itself is down (UC-5.11.3). If the peer is up but prefix count dropped, check for filtering changes or upstream depeering.
2. **Route churn**: Identify the specific prefixes being advertised/withdrawn using device CLI or BGP route monitoring. Common causes: flapping link on a remote site, route oscillation due to MED/local-preference loops.
3. **RIB approaching capacity**: Implement more aggressive route filtering, deploy route aggregation, or upgrade to a platform with more RIB capacity.

### Step 5 — Troubleshooting

- **Prefix count metrics not available** — Not all platforms expose per-AFI/SAFI prefix counts via gNMI. Some report only total prefixes. Check `| mcatalog values(metric_name) WHERE index=gnmi_metrics` for available BGP metrics.

- **Churn detection shows constant low-level changes** — In large fabrics, some churn is normal (VM mobility, container scaling). Increase the churn threshold or filter to specific address families (e.g., focus on IPv4 unicast, exclude EVPN Type-2 if VM mobility is expected).

- **RIB capacity unknown for your platform** — Consult the vendor's data sheet for TCAM and RIB limits. Store in `device_capacity.csv` for automated monitoring.

**IPv6 Coverage:** The IPv6 global routing table is ~200k prefixes (vs ~900k+ for IPv4). Add explicit IPv6 unicast SAFI monitoring alongside IPv4. Use OpenConfig path: `afi-safi[afi-safi-name=IPV6_UNICAST]/state/prefixes/received`

## SPL

```spl
| mstats latest("openconfig_bgp.prefixes_received") AS prefixes WHERE index=gnmi_metrics BY host, neighbor_address, afi_safi_name span=5m
| streamstats current=f last(prefixes) AS prev_prefixes by host, neighbor_address, afi_safi_name
| eval delta=prefixes - prev_prefixes, pct_change=if(prev_prefixes>0, round(delta*100/prev_prefixes, 1), 0)
| where abs(pct_change) > 10 OR abs(delta) > 1000
| table _time, host, neighbor_address, afi_safi_name, prev_prefixes, prefixes, delta, pct_change
| sort -abs(delta)
```

## Visualization

Line chart (prefix count per peer over time), Table (peers with recent churn), Single value (total fabric prefix count), Alert list (abnormal changes).

## Known False Positives

Telemetry pauses during device reboots, cert renewals, or transport changes; subscription restarts and path renames can look like drops without a live fault.

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
