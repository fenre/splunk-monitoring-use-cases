<!-- AUTO-GENERATED from UC-5.5.7.json — DO NOT EDIT -->

---
id: "5.5.7"
title: "Bandwidth Utilization per Site"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-5.5.7 · Bandwidth Utilization per Site

> **Criticality:** Medium &middot; **Difficulty:** Beginner &middot; **Pillar:** Observability &middot; **Type:** Performance, Capacity

*We keep an eye on how our wide-area links and SD-WAN paths are behaving so we spot a bad circuit or policy issue before branch users lose voice, video, or critical apps.*

---

## Description

WAN bandwidth consumption per site enables capacity planning and cost optimization.

## Value

Network operations teams monitor aggregate WAN bandwidth utilization per site against provisioned capacity, enabling capacity planning, congestion detection, and per-user bandwidth analysis.

## Implementation

Collect interface statistics from vManage. Track per-site, per-transport utilization. Use for upgrade decisions.

## Detailed Implementation

### Prerequisites
- Cisco Catalyst Add-on for Splunk polling vManage API for interface statistics. Data in `index=sdwan` with `sourcetype=cisco:sdwan:interface` or `sourcetype=cisco:sdwan:statistics`. Key fields: `site_id`, `system_ip`, `interface`, `tx_octets`, `rx_octets`, `tx_kbps`, `rx_kbps`, `speed_mbps`.
- Build `sdwan_site_bandwidth.csv` lookup: `site_id,site_name,total_bandwidth_mbps,primary_transport,backup_transport,user_count` (e.g., `200,Branch-Chicago,100,mpls,biz-internet,150`). This enables utilization percentage calculations and capacity planning.
- Bandwidth utilization at a site is the aggregate of all WAN interfaces. A site with 100 Mbps MPLS + 50 Mbps Internet has 150 Mbps total capacity, but MPLS is typically reserved for business-critical traffic.

### Step 1 — Configure data collection
Verify interface statistics:
```spl
index=sdwan sourcetype="cisco:sdwan:interface" earliest=-15m
| stats count dc(interface) as interfaces by site_id, system_ip
```

### Step 2 — Create the search and alert

**Primary search — Per-site bandwidth utilization:**
```spl
index=sdwan sourcetype="cisco:sdwan:interface" earliest=-15m
| where match(interface, "^(ge|eth|GigabitEthernet|TenGig)")
| stats sum(tx_kbps) as total_tx_kbps sum(rx_kbps) as total_rx_kbps by site_id
| eval total_tx_mbps=round(total_tx_kbps/1000, 1)
| eval total_rx_mbps=round(total_rx_kbps/1000, 1)
| eval peak_mbps=max(total_tx_mbps, total_rx_mbps)
| lookup sdwan_site_bandwidth.csv site_id OUTPUT site_name total_bandwidth_mbps user_count
| eval util_pct=if(isnotnull(total_bandwidth_mbps), round(100*peak_mbps/total_bandwidth_mbps, 1), null())
| eval per_user_kbps=if(isnotnull(user_count) AND user_count > 0, round(peak_mbps*1000/user_count, 0), null())
| eval status=case(util_pct > 90, "CRITICAL", util_pct > 75, "WARNING", util_pct > 50, "ELEVATED", 1==1, "OK")
| where status!="OK"
| sort -util_pct
```

#### Understanding this SPL: Aggregates all WAN interface throughput per site and compares against provisioned bandwidth. The `per_user_kbps` metric helps identify whether congestion is caused by increased headcount or bandwidth-intensive applications. Critical at > 90% because SD-WAN QoS policies start dropping lower-priority traffic, impacting user experience.

**Bandwidth trending per site:**
```spl
index=sdwan sourcetype="cisco:sdwan:interface" earliest=-7d
| where match(interface, "^(ge|eth|GigabitEthernet|TenGig)")
| bin _time span=1h
| stats sum(tx_kbps) as tx sum(rx_kbps) as rx by _time, site_id
| eval total_mbps=round((tx+rx)/1000, 1)
| lookup sdwan_site_bandwidth.csv site_id OUTPUT site_name total_bandwidth_mbps
| eval util_pct=round(100*total_mbps/total_bandwidth_mbps, 1)
| timechart span=1h avg(util_pct) by site_name
```

**Top bandwidth consumers by transport:**
```spl
index=sdwan sourcetype="cisco:sdwan:interface" earliest=-1h
| stats sum(tx_kbps) as tx_kbps sum(rx_kbps) as rx_kbps by site_id, interface
| eval total_mbps=round((tx_kbps + rx_kbps)/1000, 1)
| lookup sdwan_sites.csv site_id OUTPUT site_name
| sort -total_mbps
| head 20
```

### Step 3 — Validate
(a) In vManage: Monitor > Network > select device > Interface. Compare TX/RX rates with Splunk values for the same interface and time range.
(b) Run a known bandwidth test (iperf) from a site and verify the spike appears in the trending dashboard.
(c) Validate site bandwidth lookup: check that `total_bandwidth_mbps` matches the actual circuit provisioned speeds.

### Step 4 — Operationalize
Dashboard ("SD-WAN — Site Bandwidth"):
- Row 1 — Single-value tiles: "Sites > 90% utilization", "Sites > 75%", "Total WAN throughput (Gbps)", "Average site utilization".
- Row 2 — Site utilization table: site, bandwidth provisioned, current usage, utilization %, per-user kbps, status.
- Row 3 — 7-day trending per selected site (dropdown).
- Row 4 — Top 20 bandwidth consumers (by interface).

Alerting:
- Critical (site > 90% for 15+ minutes): congestion — QoS is actively dropping traffic.
- Warning (site > 75% sustained): capacity planning needed — order bandwidth upgrade.
- Info (weekly report): sites approaching 70% for trend analysis.

### Step 5 — Troubleshooting

- **Utilization shows > 100%** — The `total_bandwidth_mbps` in the lookup may be wrong, or the site has been upgraded without updating the lookup. Also check if you're summing both directions (TX+RX) against a single-direction capacity.

- **Sudden bandwidth spike at one site** — Check DPI data (UC-5.5.15) to identify the application. Common causes: backup jobs running during business hours, large file transfers, video streaming.

- **Interface stats show 0 for some sites** — The TA may not be polling interface statistics for those devices. Check the TA data input configuration for the statistics API endpoint.

## SPL

```spl
index=sdwan sourcetype="cisco:sdwan:interface"
| timechart span=1h sum(tx_octets) as bytes_out, sum(rx_octets) as bytes_in by site
| eval out_mbps=round(bytes_out*8/3600/1000000,1)
```

## CIM SPL

```spl
| tstats `summariesonly` sum(All_Traffic.bytes) as bytes
  from datamodel=Network_Traffic.All_Traffic
  by All_Traffic.src All_Traffic.dest All_Traffic.app span=1h
| where bytes>0
| sort -bytes
```

## Visualization

Line chart per site, Table, Stacked area.

## Known False Positives

Utilization and top-application charts jump during backups, patch windows, video calls, or large file transfers; compare to baselines and scheduled jobs before treating a spike as fault.

## References

- [Splunkbase app 7538](https://splunkbase.splunk.com/app/7538)
- [CIM: Network_Traffic](https://docs.splunk.com/Documentation/CIM/latest/User/Network_Traffic)
