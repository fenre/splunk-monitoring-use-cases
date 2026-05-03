<!-- AUTO-GENERATED from UC-5.2.33.json — DO NOT EDIT -->

---
id: "5.2.33"
title: "WAN Link Quality Monitoring — Jitter, Latency, Packet Loss (Meraki MX)"
criticality: "high"
splunkPillar: "Observability"
---

# UC-5.2.33 · WAN Link Quality Monitoring — Jitter, Latency, Packet Loss (Meraki MX)

> **Criticality:** High &middot; **Difficulty:** Intermediate &middot; **Pillar:** Observability &middot; **Type:** Fault

*We look at loss, delay, and jitter on internet links from the same boxes so a flaky provider is visible on a dashboard, not in angry tickets.*

---

## Description

Continuously monitors WAN quality metrics to detect link degradation before impacting users.

## Value

NOC teams monitor Meraki MX WAN uplink latency, loss, and jitter in real time to detect link degradation and trigger failover or ISP escalation before users are impacted.

## Implementation

Query appliance API for uplink WAN metrics. Monitor quality KPIs.

## Detailed Implementation

### Prerequisites
* Meraki MX WAN uplink performance data. Data in `index=meraki` with `sourcetype=meraki:api:uplinks` or `sourcetype=meraki:api:uplinkstats`. Key fields: `latencyMs`, `lossPct`, `jitterMs`, `interface` (wan1/wan2), `serial`, `network_name`.
* Meraki Dashboard API endpoint: `GET /organizations/{orgId}/devices/uplinksLossAndLatency` returns per-uplink latency, loss, and jitter sampled every ~5 minutes.

### Step 1 — - Configure data collection
```
# inputs.conf -- poll uplink loss and latency
[meraki_uplink_quality]
interval = 300
sourcetype = meraki:api:uplinkstats
index = meraki
# API: GET /organizations/{orgId}/devices/uplinksLossAndLatency?timespan=300
```
Verify:
```spl
index=meraki sourcetype="meraki:api:uplinkstats" earliest=-1h
| stats avg(latencyMs) avg(lossPct) avg(jitterMs) by serial, interface
```

### Step 2 — - Create the search and alert

**Primary search -- WAN quality degradation detection:**
```spl
index=meraki sourcetype="meraki:api:uplinkstats" earliest=-4h
| eval latency=tonumber(latencyMs)
| eval loss=tonumber(lossPct)
| eval jitter=tonumber(jitterMs)
| lookup meraki_networks.csv serial OUTPUT network_name, site_name
| bin _time span=5m
| stats avg(latency) as avg_latency avg(loss) as avg_loss avg(jitter) as avg_jitter by _time, serial, network_name, interface
| eval avg_latency=round(avg_latency, 1)
| eval avg_loss=round(avg_loss, 2)
| eval avg_jitter=round(avg_jitter, 1)
| eval severity=case(
    avg_loss > 5 OR avg_latency > 200, "CRITICAL -- severe WAN degradation",
    avg_loss > 2 OR avg_latency > 100 OR avg_jitter > 30, "WARNING -- WAN quality degraded",
    avg_loss > 0.5 OR avg_latency > 50, "INFO -- minor WAN quality fluctuation",
    1==1, "OK")
| where severity != "OK"
| table _time, network_name, serial, interface, avg_latency, avg_loss, avg_jitter, severity
| sort severity, -avg_loss
```

### Step 3 — - Validate
(a) Dashboard: Security & SD-WAN > Uplink status -- compare latency/loss graphs.
(b) Ping from MX: Tools > Ping to verify reported latency.
(c) Correlate with ISP-reported circuit quality.

### Step 4 — - Operationalize
Dashboard ("Meraki MX -- WAN Link Quality"):
* Row 1 -- Single-value: "Avg latency (ms)", "Avg loss (%)", "Avg jitter (ms)".
* Row 2 -- WAN quality timechart (latency, loss, jitter by uplink).
* Row 3 -- Sites with degraded WAN quality table.

Alert: Critical (loss >5% or latency >200ms sustained for 15+ minutes): page NOC.

### Step 5 — - Troubleshooting

* **Sustained high latency** -- Check ISP circuit health. Verify no saturation (check bandwidth utilization). Consider QoS adjustments or traffic shaping.

* **Intermittent packet loss** -- Check physical cabling, ISP peering, and last-mile connectivity. Compare both WAN uplinks to isolate.

* **Jitter spikes** -- Often caused by congestion or bufferbloat. Verify MX traffic shaping is enabled. Consider SD-WAN path preference changes.

## SPL

```spl
index=cisco_network sourcetype="meraki:api" uplink=*
| stats avg(latency) as avg_latency, avg(jitter) as avg_jitter, avg(packet_loss) as avg_loss by uplink_id
| eval link_quality=case(avg_loss > 5, "Critical", avg_latency > 100, "Poor", avg_jitter > 50, "Fair", 1=1, "Good")
```

## Visualization

Uplink quality scorecard; latency/jitter/loss timeline; quality gauge per uplink.

## Known False Positives

Carrier work, DDNS, and weather-related outages can trigger jitter and loss alerts on a clean policy.

## References

- [Splunkbase app 5580](https://splunkbase.splunk.com/app/5580)
