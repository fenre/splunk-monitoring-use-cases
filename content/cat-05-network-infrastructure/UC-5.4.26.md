<!-- AUTO-GENERATED from UC-5.4.26.json — DO NOT EDIT -->

---
id: "5.4.26"
title: "Top Talker Analysis and Bandwidth Hogs (Meraki MR)"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-5.4.26 · Top Talker Analysis and Bandwidth Hogs (Meraki MR)

> **Criticality:** Medium &middot; **Difficulty:** Intermediate &middot; **Pillar:** Observability &middot; **Type:** Performance

*We watch top talker analysis and bandwidth hogs (meraki mr) so we notice problems while they are still small, and we can fix them before Wi-Fi users get dropped calls or dead spots.*

---

## Description

Identifies bandwidth-intensive clients and applications to enforce QoS policies and prevent network congestion.

## Value

Network operations teams monitor Meraki wireless health scores across all sites, grading each network on connection success, throughput, and latency to prioritize sites needing wireless optimization.

## Implementation

Analyze flow records from syslog; track data usage by client and application.

## Detailed Implementation

### Prerequisites
- Meraki providing wireless network health scores and alerts. Data in `index=meraki` with `sourcetype=meraki:api:wireless` or `sourcetype=meraki:api:networkHealth`. Key fields: `network`, `healthScore` (overall wireless health 0-100), `latency`, `connectionScore`, `throughputScore`.
- Meraki wireless health is a composite metric that considers: connection success rate, latency, throughput, and DNS resolution time. Low health scores indicate systemic wireless issues affecting user experience.

### Step 1 — Configure data collection
Verify health data:
```spl
index=meraki (sourcetype="meraki:api:wireless" OR sourcetype="meraki:api:networkHealth") earliest=-4h
| where isnotnull(healthScore) OR isnotnull(connectionScore)
| stats latest(healthScore) as health by network
| sort health
```

### Step 2 — Create the search and alert

**Primary search — Network wireless health ranking:**
```spl
index=meraki (sourcetype="meraki:api:wireless" OR sourcetype="meraki:api:networkHealth") earliest=-4h
| where isnotnull(healthScore) OR isnotnull(connectionScore)
| stats latest(healthScore) as overall_health latest(connectionScore) as connection latest(throughputScore) as throughput latest(latency) as latency dc(client_mac) as clients by network
| lookup meraki_networks.csv network OUTPUT site_name tier
| eval health_grade=case(overall_health > 85, "A", overall_health > 70, "B", overall_health > 55, "C", overall_health > 40, "D", 1==1, "F")
| eval concern=case(connection < 70, "Connection failures", throughput < 70, "Low throughput", latency > 100, "High latency", overall_health < 55, "Multiple issues", 1==1, "None")
| sort overall_health
```

**Health score trending:**
```spl
index=meraki (sourcetype="meraki:api:wireless" OR sourcetype="meraki:api:networkHealth") earliest=-7d
| where isnotnull(healthScore)
| bin _time span=1h
| lookup meraki_networks.csv network OUTPUT site_name
| stats avg(healthScore) as health by _time, site_name
| timechart span=1h avg(health) by site_name
```

### Step 3 — Validate
(a) Compare health scores with Meraki Dashboard: Wireless > Monitor > Health.
(b) Verify that sites with known wireless issues show lower health scores.
(c) Correlate health score drops with specific events (firmware upgrades, AP outages).

### Step 4 — Operationalize
Dashboard ("Meraki — Wireless Health"):
- Row 1 — Single-value: "Average health score", "Sites rated D/F", "Lowest health site", "Total clients".
- Row 2 — Per-site health ranking table with grade, sub-scores, and primary concern.
- Row 3 — 7-day health score trending by site.

Alerting:
- Warning (Tier-1 site health score < 60 for > 30 min): investigate.
- Info (weekly): wireless health report card for all sites.

### Step 5 — Troubleshooting

- **Health score dropped suddenly** — Correlate with timeline: firmware upgrade? AP outage? Configuration change? Check Meraki Dashboard: Organization > Change log.

- **Connection score low, throughput OK** — Clients are failing to connect but those who do get good throughput. Likely an authentication issue (RADIUS, PSK).

- **Latency high across all sites** — Check upstream: DNS resolution time, DHCP response time, or WAN latency. Meraki health includes end-to-end latency.

## SPL

```spl
index=cisco_network sourcetype="meraki" type=flow
| stats sum(sent_bytes) as upload_bytes, sum(received_bytes) as download_bytes by client_mac, application
| eval total_bytes=upload_bytes+download_bytes
| sort -total_bytes
| head 20
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

Table of top talkers; horizontal bar chart of data usage; Sankey diagram of flows.

## Known False Positives

Backup jobs, imaging, and video can create heavy wireless flows; confirm with the app owner before assuming abuse or a misbehaving client.

## References

- [Splunkbase app 5580](https://splunkbase.splunk.com/app/5580)
