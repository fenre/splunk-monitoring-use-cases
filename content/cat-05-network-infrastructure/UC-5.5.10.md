<!-- AUTO-GENERATED from UC-5.5.10.json — DO NOT EDIT -->

---
id: "5.5.10"
title: "WAN Link Utilization per Transport"
criticality: "high"
splunkPillar: "Observability"
---

# UC-5.5.10 · WAN Link Utilization per Transport

> **Criticality:** High &middot; **Difficulty:** Intermediate &middot; **Pillar:** Observability &middot; **Type:** Performance, Capacity

*We keep an eye on how our wide-area links and SD-WAN paths are behaving so we spot a bad circuit or policy issue before branch users lose voice, video, or critical apps.*

---

## Description

Unbalanced link utilization wastes expensive MPLS bandwidth while underusing broadband circuits. Enables cost-effective traffic engineering.

## Value

Network operations teams monitor per-transport WAN link utilization with cost-awareness, identifying saturated circuits, validating transport balance across MPLS/Internet/LTE, and projecting metered transport costs.

## Implementation

Collect interface stats per WAN transport type (MPLS, Internet, LTE). Compare utilization across links. Alert on >70% sustained utilization. Use for capacity planning.

## Detailed Implementation

### Prerequisites
- Cisco Catalyst Add-on for Splunk polling vManage API for interface statistics per WAN transport. Data in `index=sdwan` with `sourcetype=cisco:sdwan:interface`. Key fields: `site_id`, `system_ip`, `interface`, `vpn_id`, `af_type`, `tx_octets`, `rx_octets`, `tx_kbps`, `rx_kbps`, `speed_mbps`, `color` (mpls, biz-internet, lte, private1).
- SD-WAN sites typically have multiple WAN transports: MPLS (reliable, expensive), Internet (cheaper, best-effort), LTE (metered, backup). Each transport has different cost and performance characteristics. Monitoring utilization per transport helps optimize cost — if expensive MPLS is saturated while cheap Internet is idle, AAR policy may need tuning.
- Build `sdwan_transport_costs.csv` lookup: `site_id,color,provider,speed_mbps,monthly_cost_usd,cost_per_gb` (e.g., `200,mpls,AT&T,50,3000,0`, `200,biz-internet,Comcast,100,200,0`, `200,lte,Verizon,50,50,0.05`).

### Step 1 — Configure data collection
Verify per-transport data:
```spl
index=sdwan sourcetype="cisco:sdwan:interface" earliest=-15m
| where isnotnull(color)
| stats sum(tx_kbps) as tx sum(rx_kbps) as rx by site_id, color
| eval total_mbps=round((tx+rx)/1000, 1)
| sort site_id, color
```

### Step 2 — Create the search and alert

**Primary search — Per-transport utilization with cost analysis:**
```spl
index=sdwan sourcetype="cisco:sdwan:interface" earliest=-1h
| where isnotnull(color)
| stats sum(tx_kbps) as tx_kbps sum(rx_kbps) as rx_kbps by site_id, color
| eval total_mbps=round((tx_kbps + rx_kbps)/1000, 1)
| eval total_gb_hour=round(total_mbps * 3600 / 8000, 2)
| lookup sdwan_transport_costs.csv site_id, color OUTPUT provider speed_mbps monthly_cost_usd cost_per_gb
| eval util_pct=if(isnotnull(speed_mbps), round(100 * total_mbps / speed_mbps, 1), null())
| eval hourly_cost=if(cost_per_gb > 0, round(total_gb_hour * cost_per_gb, 2), 0)
| lookup sdwan_sites.csv site_id OUTPUT site_name tier
| eval transport_label=upper(color)." (".provider.")"
| eval status=case(util_pct > 90, "SATURATED", util_pct > 75, "HIGH", color="lte" AND total_mbps > 5, "COST_ALERT", 1==1, "OK")
| where status!="OK"
| sort status, -util_pct
```

#### Understanding this SPL: Goes beyond simple utilization by adding cost awareness. LTE transports are typically metered ($0.01-$0.10 per GB), so even low utilization can generate unexpected costs if sustained. Conversely, MPLS saturation at $3000/month fixed cost suggests upgrading bandwidth or offloading traffic to cheaper Internet.

**Transport utilization balance across site:**
```spl
index=sdwan sourcetype="cisco:sdwan:interface" earliest=-4h
| where isnotnull(color)
| stats sum(tx_kbps) as tx_kbps sum(rx_kbps) as rx_kbps by site_id, color
| eval total_mbps=round((tx_kbps + rx_kbps)/1000, 1)
| lookup sdwan_transport_costs.csv site_id, color OUTPUT speed_mbps
| eval util_pct=round(100 * total_mbps / speed_mbps, 1)
| chart avg(util_pct) by site_id color
```

**LTE usage cost projection:**
```spl
index=sdwan sourcetype="cisco:sdwan:interface" color="lte" earliest=-24h
| bin _time span=1h
| stats sum(tx_kbps) as tx sum(rx_kbps) as rx by _time, site_id
| eval gb_hour=round((tx+rx)*3600/8000000, 2)
| stats sum(gb_hour) as total_gb by site_id
| lookup sdwan_transport_costs.csv site_id color as "lte" OUTPUT cost_per_gb provider
| eval daily_cost=round(total_gb * cost_per_gb, 2)
| eval monthly_projection=round(daily_cost * 30, 2)
| lookup sdwan_sites.csv site_id OUTPUT site_name
| where monthly_projection > 100
| sort -monthly_projection
```

### Step 3 — Validate
(a) In vManage: Monitor > Network > select device > Interface. Compare per-interface throughput by color with Splunk results.
(b) Cross-check LTE data usage with carrier billing for the same period.
(c) Verify transport cost lookup against actual contracts.

### Step 4 — Operationalize
Dashboard ("SD-WAN — Transport Utilization"):
- Row 1 — Single-value tiles: "Saturated transports", "LTE cost (24h)", "Busiest MPLS site", "Average Internet utilization".
- Row 2 — Transport utilization table: site, transport, provider, speed, utilization %, hourly cost (if metered).
- Row 3 — LTE cost projection table: site, daily GB, daily cost, monthly projection.
- Row 4 — Transport balance chart: stacked bar per site showing utilization of each transport.

Alerting:
- Critical (any transport > 90% sustained 15 min): link saturated.
- High (LTE monthly projection > $500): unexpected metered costs — may indicate primary transport failure.
- Warning (MPLS > 75% while Internet < 30%): AAR policy may need tuning to offload traffic.

### Step 5 — Troubleshooting

- **LTE shows high utilization but no failover occurred** — Some SD-WAN policies route specific applications to LTE by default (e.g., IoT devices). Check AAR policy to verify LTE usage is intentional.

- **MPLS utilization doesn't match carrier reports** — The TA reports layer-3 throughput; carrier reports may include layer-2 overhead. A 5-10% difference is normal.

- **No color field on interface data** — The interface may not be mapped to a transport color in the device template. Check vManage: Configuration > Templates > device template > Transport VPN.

## SPL

```spl
index=network sourcetype="cisco:sdwan:interface"
| eval util_pct=round(tx_octets*8/speed*100,1)
| stats avg(util_pct) as avg_util, max(util_pct) as peak_util by system_ip, color, interface_name
| where avg_util > 70 | sort -avg_util
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

Line chart (utilization per transport), Stacked bar (site comparison), Table.

## Known False Positives

Utilization and top-application charts jump during backups, patch windows, video calls, or large file transfers; compare to baselines and scheduled jobs before treating a spike as fault.

## References

- [Splunkbase app 7538](https://splunkbase.splunk.com/app/7538)
