<!-- AUTO-GENERATED from UC-5.4.3.json — DO NOT EDIT -->

---
id: "5.4.3"
title: "Channel Utilization"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-5.4.3 · Channel Utilization

> **Criticality:** Medium &middot; **Difficulty:** Intermediate &middot; **Pillar:** Observability &middot; **Type:** Performance, Capacity

*We watch channel utilization so we notice problems while they are still small, and we can fix them before Wi-Fi users get dropped calls or dead spots.*

---

## Description

High channel utilization degrades wireless performance. Identifies congested APs needing channel changes or additional coverage.

## Value

Network operations teams monitor wireless channel utilization and interference levels per AP, band, and location to identify capacity bottlenecks, RF interference sources, and areas requiring additional access points or channel optimization.

## Implementation

Poll Meraki RF statistics API or WLC SNMP. Track per-AP channel utilization. Alert when >60% (2.4GHz) or >50% (5GHz).

## Detailed Implementation

### Prerequisites
- Wireless controller or AP reporting RF channel utilization metrics. Sources: (1) Cisco WLC — Radio Resource Management (RRM) data via SNMP or syslog, (2) Meraki Dashboard API (`sourcetype=meraki:api:devices` or `meraki:api:wireless`) — per-radio channel utilization, (3) Aruba controller — ARM (Adaptive Radio Management) statistics.
- Data in `index=wireless`. Key fields: `ap_name`, `radio_band` (2.4GHz/5GHz/6GHz), `channel`, `channel_utilization` (0-100%), `noise_floor` (dBm), `tx_utilization`, `rx_utilization`, `interference` (non-WiFi RF energy percentage).
- Channel utilization above 60-70% causes noticeable performance degradation. Above 80%, users experience significant latency, packet loss, and retransmissions. The utilization is divided into: (1) Tx — time the AP spends transmitting, (2) Rx — time receiving from clients, (3) Interference — non-WiFi energy (microwave ovens, Bluetooth, etc.), (4) Other — neighboring APs on the same channel.

### Step 1 — Configure data collection
Verify channel utilization data:
```spl
index=wireless earliest=-1h
| where isnotnull(channel_utilization) OR match(_raw, "(?i)channel.util")
| stats avg(channel_utilization) as avg_util by ap_name, radio_band
| sort -avg_util
| head 20
```

### Step 2 — Create the search and alert

**Primary search — Channel utilization hotspots:**
```spl
index=wireless earliest=-1h
| where isnotnull(channel_utilization)
| stats avg(channel_utilization) as avg_util max(channel_utilization) as peak_util avg(interference) as avg_interference by ap_name, radio_band, channel
| lookup wireless_ap_inventory.csv ap_name OUTPUT building floor zone
| eval status=case(avg_util > 80, "CRITICAL", avg_util > 60, "WARNING", avg_util > 40, "ELEVATED", 1==1, "OK")
| eval interference_flag=if(avg_interference > 20, "HIGH_INTERFERENCE", "OK")
| where status!="OK"
| eval location=building." / ".floor." / ".zone
| table ap_name, location, radio_band, channel, avg_util, peak_util, avg_interference, status, interference_flag
| sort status, -avg_util
```

#### Understanding this SPL: Channel utilization is the single most important metric for wireless capacity. High utilization means the airtime is saturated — adding more clients or bandwidth will degrade everyone's experience. The interference component is critical: if 30% of utilization is interference (non-WiFi), changing the channel or adding shielding is more effective than adding APs.

**Utilization by building/floor:**
```spl
index=wireless earliest=-4h
| where isnotnull(channel_utilization)
| lookup wireless_ap_inventory.csv ap_name OUTPUT building floor
| stats avg(channel_utilization) as avg_util dc(ap_name) as ap_count by building, floor, radio_band
| eval status=case(avg_util > 70, "CONGESTED", avg_util > 50, "BUSY", 1==1, "OK")
| where status!="OK"
| sort status, -avg_util
```

**Channel utilization trending:**
```spl
index=wireless earliest=-24h
| where isnotnull(channel_utilization)
| bin _time span=15m
| lookup wireless_ap_inventory.csv ap_name OUTPUT building
| stats avg(channel_utilization) as util by _time, building, radio_band
| timechart span=15m avg(util) by building
```

### Step 3 — Validate
(a) Compare channel utilization in Splunk with the wireless controller's RF dashboard. Values should be within 5% variance.
(b) Generate traffic (large file transfer over WiFi) and verify utilization increases on the corresponding AP/channel.
(c) Verify the interference field: place a known interference source (microwave oven on 2.4GHz) near a test AP and confirm the interference metric increases.

### Step 4 — Operationalize
Dashboard ("Wireless — Channel Utilization"):
- Row 1 — Single-value tiles: "APs > 80% utilization", "APs with high interference", "Average 5GHz utilization", "Average 2.4GHz utilization".
- Row 2 — Utilization hotspot table: AP, location, band, channel, utilization, interference.
- Row 3 — Building/floor utilization summary.
- Row 4 — 24-hour utilization trending per building.

Alerting:
- Critical (AP > 80% utilization sustained 30 minutes): users experiencing degradation — add APs or offload clients.
- Warning (AP > 60% utilization): approaching capacity — monitor.
- Info (high interference detected): investigate RF environment for non-WiFi sources.

### Step 5 — Troubleshooting

- **High utilization on 2.4GHz but not 5GHz** — 2.4GHz has fewer non-overlapping channels (1, 6, 11) and more interference sources. Enable band steering (UC-5.4.11/19) to move capable clients to 5GHz.

- **High utilization from interference, not WiFi traffic** — Non-WiFi sources (microwaves, Bluetooth, baby monitors) create interference. Use a spectrum analyzer to identify the source. Consider moving to 5GHz or 6GHz.

- **Utilization data not available** — SNMP polling for RF metrics may not be configured. For Cisco WLC: enable RRM monitoring. For Meraki: RF data is included in the API. For Aruba: enable ARM statistics export.

## SPL

```spl
index=network sourcetype="meraki:api"
| stats avg(channel_utilization) as util_pct by ap_name, channel, band
| where util_pct > 60 | sort -util_pct
```

## Visualization

Heatmap (APs by utilization), Table, Line chart (trending).

## Known False Positives

RF noise and channel changes can spike when neighbors deploy new gear, microwaves run, or the controller runs automatic channel updates; weather and outdoor clients can also move the numbers.

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
