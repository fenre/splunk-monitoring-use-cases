<!-- AUTO-GENERATED from UC-5.4.23.json — DO NOT EDIT -->

---
id: "5.4.23"
title: "Multicast and Broadcast Storm Detection (Meraki MR)"
criticality: "high"
splunkPillar: "Observability"
---

# UC-5.4.23 · Multicast and Broadcast Storm Detection (Meraki MR)

> **Criticality:** High &middot; **Difficulty:** Intermediate &middot; **Pillar:** Observability &middot; **Type:** Anomaly

*We watch multicast and broadcast storm detection (meraki mr) so we notice problems while they are still small, and we can fix them before Wi-Fi users get dropped calls or dead spots.*

---

## Description

Identifies multicast/broadcast flooding that degrades wireless performance across multiple client devices.

## Value

Facilities and wireless teams estimate location-based occupancy from Meraki MR client counts per zone, detecting near-capacity areas for facilities planning and proactive wireless capacity management.

## Implementation

Monitor broadcast/multicast flows in syslog. Set thresholds for abnormal packet rates.

## Detailed Implementation

### Prerequisites
- Meraki providing location analytics or scanning API data. Data in `index=meraki` with `sourcetype=meraki:api:wireless` or `sourcetype=meraki:scanning`. Key fields: `client_mac`, `ap_name`, `ssid`, `rssi`, `location` or `x/y` coordinates, `network`.
- Meraki location analytics uses RSSI triangulation from multiple APs to estimate client positions. This enables: visitor flow analysis, dwell time measurement, occupancy estimation, and location-aware troubleshooting.

### Step 1 — Configure data collection
Verify location data:
```spl
index=meraki (sourcetype="meraki:api:wireless" OR sourcetype="meraki:scanning") earliest=-4h
| where isnotnull(client_mac)
| stats dc(ap_name) as seen_by_aps count as observations by client_mac
| where seen_by_aps > 1
| head 20
```

### Step 2 — Create the search and alert

**Primary search — Location-based occupancy estimation:**
```spl
index=meraki (sourcetype="meraki:api:wireless" OR sourcetype="meraki:events") earliest=-4h
| where isnotnull(client_mac) AND isnotnull(ssid)
| bin _time span=15m
| eval ap_id=coalesce(ap_name, deviceName)
| stats dc(client_mac) as client_count by _time, ap_id, ssid
| lookup wireless_ap_inventory.csv ap_name as ap_id OUTPUT building floor zone capacity
| eval occupancy_pct=if(isnotnull(capacity), round(100*client_count/capacity, 1), null())
| where occupancy_pct > 80 OR client_count > 50
| eval status=case(occupancy_pct > 100, "OVER_CAPACITY", occupancy_pct > 80, "NEAR_CAPACITY", client_count > 50, "HIGH_DENSITY", 1==1, "OK")
| sort -occupancy_pct
```

**Occupancy trending:**
```spl
index=meraki (sourcetype="meraki:api:wireless" OR sourcetype="meraki:events") earliest=-7d
| where isnotnull(client_mac) AND isnotnull(ssid)
| bin _time span=1h
| eval ap_id=coalesce(ap_name, deviceName)
| lookup wireless_ap_inventory.csv ap_name as ap_id OUTPUT building floor
| stats dc(client_mac) as clients by _time, building, floor
| timechart span=1h avg(clients) by building
```

### Step 3 — Validate
(a) Count devices in a room and compare with the Splunk client count for the covering AP.
(b) Verify occupancy patterns match expected schedules (higher during business hours, lower evenings).
(c) Compare with Meraki Dashboard: Wireless > Location analytics.

### Step 4 — Operationalize
Dashboard ("Meraki — Location & Occupancy"):
- Row 1 — Single-value: "Total connected clients", "Zones near capacity", "Highest occupancy zone", "Average occupancy".
- Row 2 — Per-zone occupancy table with capacity thresholds.
- Row 3 — Hourly occupancy trending by building.

Alerting:
- Warning (zone occupancy > 90%): capacity issue — may impact WiFi performance.
- Info (weekly): occupancy report for facilities planning.

### Step 5 — Troubleshooting

- **Client count seems too high** — Some users carry multiple devices (phone, laptop, tablet). Apply a multiplier (typically 1.5-2x devices per person) for occupancy estimation.

- **Location data not available** — Meraki scanning API must be enabled: Network > General > Location and scanning. The CMX/scanning API requires a separate configuration.

- **Inaccurate location** — RSSI-based triangulation requires 3+ APs with line of sight. Accuracy is typically 5-10 meters. For higher accuracy, consider BLE beacons.

## SPL

```spl
index=cisco_network sourcetype="meraki" type=flow dest="255.255.255.255" OR dest_mac="ff:ff:ff:ff:ff:ff"
| stats sum(sent_bytes) as total_bytes, count as pkt_count by ap_name, src_mac
| where pkt_count > 1000
| sort - pkt_count
```

## CIM SPL

```spl
| tstats `summariesonly` sum(All_Traffic.bytes) as bytes
  from datamodel=Network_Traffic.All_Traffic
  by All_Traffic.src All_Traffic.dest All_Traffic.dvc span=1h
| where bytes>0
| sort -bytes
```

## Visualization

Table of broadcast sources; time-series of broadcast packets; alert threshold dashboard.

## Known False Positives

Backup jobs, imaging, and video can create heavy wireless flows; confirm with the app owner before assuming abuse or a misbehaving client.

## References

- [Splunkbase app 5580](https://splunkbase.splunk.com/app/5580)
