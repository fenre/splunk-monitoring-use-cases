<!-- AUTO-GENERATED from UC-5.4.24.json — DO NOT EDIT -->

---
id: "5.4.24"
title: "Wireless Health Score Trending (Meraki MR)"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-5.4.24 · Wireless Health Score Trending (Meraki MR)

> **Criticality:** Medium &middot; **Difficulty:** Intermediate &middot; **Pillar:** Observability &middot; **Type:** Availability

*We watch wireless health score trending (meraki mr) so we notice problems while they are still small, and we can fix them before Wi-Fi users get dropped calls or dead spots.*

---

## Description

Provides a composite health metric across all APs to facilitate executive reporting and trend analysis.

## Value

Network operations teams track Meraki wireless bandwidth consumption by SSID and client, correlating usage with WAN capacity to detect bandwidth abuse and validate traffic shaping policy effectiveness.

## Implementation

Pull health_score metric from MR devices API. Aggregate across network.

## Detailed Implementation

### Prerequisites
- Meraki API providing per-SSID traffic shaping and group policy data. Data in `index=meraki` with `sourcetype=meraki:events` or `sourcetype=meraki:api:wireless`. Key fields: `ssid`, `client_mac`, `bandwidth_limit`, `usage` (bytes), `group_policy`.
- Meraki traffic shaping controls bandwidth per SSID, per client, and per application. It uses L7 firewall rules and traffic shaping rules to prioritize or throttle applications (e.g., prioritize VoIP, throttle video streaming on guest SSID).

### Step 1 — Configure data collection
Verify traffic data:
```spl
index=meraki (sourcetype="meraki:events" OR sourcetype="meraki:api:wireless") earliest=-4h
| where isnotnull(ssid) AND isnotnull(usage)
| stats sum(usage) as total_bytes dc(client_mac) as clients by ssid
| eval total_GB=round(total_bytes/1073741824, 2)
```

### Step 2 — Create the search and alert

**Primary search — Bandwidth consumption by SSID:**
```spl
index=meraki (sourcetype="meraki:events" OR sourcetype="meraki:api:wireless") earliest=-4h
| where isnotnull(ssid) AND (isnotnull(usage) OR isnotnull(sent) OR isnotnull(recv))
| eval bytes_total=coalesce(usage, sent + recv, 0)
| stats sum(bytes_total) as total_bytes dc(client_mac) as client_count by ssid, network
| eval total_GB=round(total_bytes/1073741824, 2)
| eval avg_per_client_MB=round(total_bytes/(client_count*1048576), 1)
| lookup meraki_networks.csv network OUTPUT site_name wan_bandwidth_mbps
| eval wan_pct=if(isnotnull(wan_bandwidth_mbps), round(100*(total_bytes*8/1000000)/(wan_bandwidth_mbps*3600*4), 1), null())
| sort -total_GB
```

**Top bandwidth consumers (per client):**
```spl
index=meraki (sourcetype="meraki:events" OR sourcetype="meraki:api:wireless") earliest=-4h
| where isnotnull(client_mac) AND (isnotnull(usage) OR isnotnull(sent))
| eval bytes_total=coalesce(usage, sent + recv, 0)
| stats sum(bytes_total) as total_bytes latest(ssid) as ssid latest(ap_name) as last_ap by client_mac
| eval total_MB=round(total_bytes/1048576, 1)
| where total_MB > 500
| sort -total_bytes
| head 20
```

### Step 3 — Validate
(a) Download a large file on the guest SSID and verify the bandwidth consumption appears.
(b) Verify per-client bandwidth limits are being enforced by checking actual throughput vs configured limit.
(c) Compare with Meraki Dashboard: Wireless > Clients > sort by Usage.

### Step 4 — Operationalize
Dashboard ("Meraki — Bandwidth & Traffic Shaping"):
- Row 1 — Single-value: "Total bandwidth (4h)", "Top SSID by usage", "Top client", "WAN utilization (estimated)".
- Row 2 — Per-SSID bandwidth table with client count and WAN impact.
- Row 3 — Top 20 bandwidth consumers (clients).

Alerting:
- Warning (single client > 2 GB in 4 hours on guest SSID): potential abuse — apply stricter group policy.
- Info (WAN utilization estimate > 80%): wireless traffic consuming significant WAN bandwidth.

### Step 5 — Troubleshooting

- **Guest SSID consuming more bandwidth than corporate** — Guest users may be streaming video without traffic shaping restrictions. Apply per-client bandwidth limits in Meraki Dashboard: Wireless > Firewall & traffic shaping.

- **Traffic shaping not effective** — Ensure L7 firewall rules are configured (Meraki: Wireless > Firewall & traffic shaping > L7 firewall rules). Common rules: throttle peer-to-peer, limit video streaming.

- **WAN utilization high** — Consider enabling content caching or deploying a Meraki MX with SD-WAN traffic shaping at the WAN edge.

## SPL

```spl
index=cisco_network sourcetype="meraki:api" device_type=MR
| stats avg(health_score) as network_health, min(health_score) as worst_ap, count(eval(health_score<80)) as unhealthy_aps by network_id
| eval health_status=if(network_health >= 85, "Healthy", if(network_health >= 70, "Degraded", "Critical"))
```

## Visualization

Gauge of overall health; bar chart of individual AP health; trend sparkline; KPI dashboard.

## Known False Positives

Wireless metrics move with user behavior, maintenance, and nearby RF; we tune alerts around change windows and known busy hours so normal days do not page the team.

## References

- [Splunkbase app 5580](https://splunkbase.splunk.com/app/5580)
