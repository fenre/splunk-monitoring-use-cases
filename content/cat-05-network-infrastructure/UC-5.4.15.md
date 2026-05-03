<!-- AUTO-GENERATED from UC-5.4.15.json — DO NOT EDIT -->

---
id: "5.4.15"
title: "SSID Performance Ranking and Trend Analysis (Meraki MR)"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-5.4.15 · SSID Performance Ranking and Trend Analysis (Meraki MR)

> **Criticality:** Medium &middot; **Difficulty:** Intermediate &middot; **Pillar:** Observability &middot; **Type:** Performance

*We watch ssid performance ranking and trend analysis (meraki mr) so we notice problems while they are still small, and we can fix them before Wi-Fi users get dropped calls or dead spots.*

---

## Description

Compares performance across multiple SSIDs to identify underperforming networks and optimize deployment strategy.

## Value

Network operations teams rank Meraki SSID performance across all sites using a composite score (success rate, signal quality, latency), enabling cross-site comparison and targeted wireless optimization.

## Implementation

Aggregate client connection metrics by SSID. Compare average connection duration, client count, and signal strength.

## Detailed Implementation

### Prerequisites
- Meraki API providing per-SSID performance metrics. Data in `index=meraki` with `sourcetype=meraki:api:wireless` or `sourcetype=meraki:events`. Key fields: `ssid`, `client_count`, `throughput` (avg client throughput), `latency`, `rssi`, `success_rate` (connection success rate).

### Step 1 — Configure data collection
Verify per-SSID data:
```spl
index=meraki (sourcetype="meraki:api:wireless" OR sourcetype="meraki:events") earliest=-4h
| where isnotnull(ssid)
| stats count dc(client_mac) as clients by ssid
```

### Step 2 — Create the search and alert

**Primary search — SSID performance ranking:**
```spl
index=meraki (sourcetype="meraki:api:wireless" OR sourcetype="meraki:events") earliest=-4h
| where isnotnull(ssid)
| stats dc(client_mac) as client_count avg(rssi) as avg_rssi avg(latency) as avg_latency count(eval(match(type, "(?i)fail"))) as failures count as total_events by ssid, network
| eval success_rate=round(100*(total_events - failures)/total_events, 1)
| eval performance_score=round((success_rate * 0.4) + (min(100, max(0, (avg_rssi + 90) * 3)) * 0.3) + (min(100, max(0, 100 - avg_latency)) * 0.3), 1)
| lookup meraki_networks.csv network OUTPUT site_name
| eval ranking=case(performance_score > 85, "A", performance_score > 70, "B", performance_score > 55, "C", 1==1, "D")
| sort -performance_score
```

#### Understanding this SPL: The composite performance score combines success rate (40%), signal quality (30%), and latency (30%) into a single ranking per SSID. This enables management reporting: "Corporate WiFi scores A at HQ but C at the Chicago branch." The ranking highlights which SSIDs at which sites need attention.

**SSID trending (weekly):**
```spl
index=meraki (sourcetype="meraki:api:wireless" OR sourcetype="meraki:events") earliest=-7d
| where isnotnull(ssid)
| bin _time span=1d
| stats dc(client_mac) as clients count(eval(match(type, "(?i)fail"))) as failures count as events by _time, ssid
| eval daily_success=round(100*(events - failures)/events, 1)
| timechart span=1d avg(daily_success) by ssid
```

### Step 3 — Validate
(a) Compare SSID client counts with Meraki Dashboard: Wireless > Monitor > SSIDs.
(b) Verify the performance score reflects the actual user experience at different sites.
(c) Test by degrading one SSID (reduce power on its APs) and verify the score drops.

### Step 4 — Operationalize
Dashboard ("Meraki — SSID Performance"):
- Row 1 — Single-value: "Best SSID score", "Worst SSID score", "Total SSIDs", "SSIDs rated D".
- Row 2 — SSID ranking table: SSID, network/site, clients, success rate, avg RSSI, latency, score, rating.
- Row 3 — Weekly SSID success rate trending.

Alerting:
- Warning (SSID score drops below C at a Tier1 site): investigate.
- Info (weekly): SSID performance report for all sites.

### Step 5 — Troubleshooting

- **Corporate SSID scores well at HQ but poorly at branches** — Branches may have fewer APs, different RF environments, or RADIUS connectivity issues. Compare per-site metrics.

- **Guest SSID always scores low** — Guest SSIDs often have bandwidth limits, captive portals (add latency), and lower priority QoS. This may be by design.

- **Score fluctuates daily** — Likely corresponds to occupancy patterns. Score drops during peak hours when more clients compete for airtime.

## SPL

```spl
index=cisco_network sourcetype="meraki:api"
| stats avg(connection_duration) as avg_duration, count as client_count, avg(rssi) as avg_rssi by ssid
| eval performance_score=round((avg_rssi+100)*client_count/100, 2)
| sort - performance_score
```

## Visualization

Bar chart comparing SSID performance; sparklines for trend; scorecard showing top/bottom performers.

## Known False Positives

RF noise and channel changes can spike when neighbors deploy new gear, microwaves run, or the controller runs automatic channel updates; weather and outdoor clients can also move the numbers.

## References

- [Splunkbase app 5580](https://splunkbase.splunk.com/app/5580)
