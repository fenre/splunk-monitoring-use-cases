<!-- AUTO-GENERATED from UC-5.1.52.json — DO NOT EDIT -->

---
id: "5.1.52"
title: "Cellular Gateway Signal Strength Trending (Meraki MG)"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-5.1.52 · Cellular Gateway Signal Strength Trending (Meraki MG)

> **Criticality:** Medium &middot; **Difficulty:** Intermediate &middot; **Pillar:** Observability &middot; **Type:** Performance

*We help you know early when something looks wrong with cellular gateway signal strength trending so the team can act before it grows into a bigger outage.*

---

## Description

Monitors cellular signal strength to ensure reliable backup connectivity.

## Value

Operations teams trend Meraki MG cellular gateway signal strength (RSRP, RSRQ, SINR) to detect degradation and optimize antenna placement for reliable cellular WAN connectivity.

## Implementation

Query MG device API for signal metrics. Alert on degraded signal.

## Detailed Implementation

### Prerequisites
* Meraki MG cellular signal data from Dashboard API. Data in `index=meraki` with `sourcetype=meraki:api:cellular:signal` or `sourcetype=meraki:api:device:status`. Key fields: `rsrp` (Reference Signal Received Power), `rsrq` (Reference Signal Received Quality), `sinr` (Signal-to-Interference-plus-Noise Ratio), `rssi`.
* Meraki MG: dedicated cellular gateway providing primary or backup WAN connectivity over 4G LTE / 5G. Signal strength directly impacts throughput and reliability. API: `GET /devices/{serial}/cellular/sims`.

### Step 1 — - Configure data collection
```
[meraki_mg_signal]
interval = 300
sourcetype = meraki:api:cellular:signal
index = meraki
# API: GET /devices/{serial}/cellular/sims
# Returns signal metrics per SIM
```
Verify:
```spl
index=meraki sourcetype="meraki:api:cellular:signal" earliest=-4h
| stats latest(rsrp) latest(rsrq) latest(sinr) by host
```

### Step 2 — - Create the search and alert

**Primary search -- Cellular signal strength trending:**
```spl
index=meraki sourcetype="meraki:api:cellular:signal" earliest=-24h
| eval device=coalesce(serial, host)
| eval rsrp=tonumber(rsrp)
| eval rsrq=tonumber(rsrq)
| eval sinr=tonumber(sinr)
| lookup meraki_networks.csv serial AS device OUTPUT network_name, site_name
| bin _time span=15m
| stats avg(rsrp) as avg_rsrp avg(rsrq) as avg_rsrq avg(sinr) as avg_sinr by _time, network_name, device
| eval avg_rsrp=round(avg_rsrp, 1)
| eval avg_rsrq=round(avg_rsrq, 1)
| eval avg_sinr=round(avg_sinr, 1)
| eval signal_quality=case(
    avg_rsrp > -80, "Excellent",
    avg_rsrp > -90, "Good",
    avg_rsrp > -100, "Fair",
    avg_rsrp > -110, "Poor",
    1==1, "Very Poor")
| eval severity=case(
    avg_rsrp < -110 OR avg_sinr < 0, "CRITICAL -- very poor signal, unreliable connectivity",
    avg_rsrp < -100 OR avg_sinr < 5, "WARNING -- poor signal quality",
    avg_rsrp < -90, "INFO -- fair signal",
    1==1, "OK")
| where severity != "OK"
| table _time, network_name, device, avg_rsrp, avg_rsrq, avg_sinr, signal_quality, severity
| sort severity, avg_rsrp
```

### Step 3 — - Validate
(a) Dashboard: Cellular gateway > Overview -- check signal metrics.
(b) Compare with carrier coverage maps for the site location.
(c) Monitor signal variation by time of day (congestion patterns).

### Step 4 — - Operationalize
Dashboard ("Meraki MG -- Signal Strength"):
* Row 1 -- Single-value: "Signal quality", "RSRP (dBm)", "SINR (dB)".
* Row 2 -- Signal strength timechart (RSRP, RSRQ, SINR).

Alert: Warning (RSRP < -100 sustained): poor signal, investigate antenna/placement.

### Step 5 — - Troubleshooting

* **Poor signal** -- Options: (1) reposition antenna, (2) install external high-gain antenna, (3) adjust MG mounting location for better line-of-sight, (4) consider signal booster/repeater.

* **Signal degradation at specific times** -- Cell tower congestion during peak hours. Consider: carrier change, multi-SIM with different carriers, or fixed wireless alternative.

* **Sudden signal drop** -- Check: (1) antenna cable connection, (2) nearby construction blocking signal, (3) carrier network issue.

## SPL

```spl
index=cisco_network sourcetype="meraki:api" device_type=MG
| stats avg(signal_strength) as avg_signal, min(signal_strength) as min_signal by cellular_gateway_id
| eval signal_quality=case(avg_signal > -90, "Excellent", avg_signal > -110, "Good", 1=1, "Poor")
```

## Visualization

Signal strength gauge; trend timeline; cellular quality status.

## Known False Positives

Carrier testing, local SIM swaps, and planned tower work can look like a connectivity fault. Compare the Meraki event log to the same window in Splunk.

## References

- [Splunkbase app 5580](https://splunkbase.splunk.com/app/5580)
