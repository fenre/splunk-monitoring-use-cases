<!-- AUTO-GENERATED from UC-5.4.25.json — DO NOT EDIT -->

---
id: "5.4.25"
title: "Connected Client Count Trending and Capacity Planning (Meraki MR)"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-5.4.25 · Connected Client Count Trending and Capacity Planning (Meraki MR)

> **Criticality:** Medium &middot; **Difficulty:** Intermediate &middot; **Pillar:** Observability &middot; **Type:** Capacity

*We watch connected client count trending and capacity planning (meraki mr) so we notice problems while they are still small, and we can fix them before Wi-Fi users get dropped calls or dead spots.*

---

## Description

Tracks client density by AP and SSID for capacity planning and performance optimization.

## Value

Facilities and security teams leverage Meraki MR built-in BLE scanning to track tagged assets, detect BLE device movement between zones, and support indoor location-based services.

## Implementation

Query clients API to count connected devices. Track over time.

## Detailed Implementation

### Prerequisites
- Meraki providing Bluetooth Low Energy (BLE) beacon data. Data in `index=meraki` with `sourcetype=meraki:api:bluetooth` or `sourcetype=meraki:scanning`. Key fields: `mac` (BLE device MAC), `rssi`, `ap_name` (detecting AP), `uuid`/`major`/`minor` (iBeacon identifiers), `type` (BLE).
- Meraki MR APs have built-in BLE radios that can: (1) broadcast as BLE beacons (for indoor wayfinding apps), (2) scan for nearby BLE devices (for asset tracking), (3) provide BLE-based location analytics. This UC focuses on BLE scanning for asset tracking and rogue device detection.

### Step 1 — Configure data collection
Verify BLE data:
```spl
index=meraki (sourcetype="meraki:api:bluetooth" OR sourcetype="meraki:scanning") earliest=-4h
| where match(type, "(?i)ble") OR isnotnull(uuid)
| stats count dc(mac) as unique_devices by ap_name
| sort -unique_devices
```

### Step 2 — Create the search and alert

**Primary search — BLE device inventory and tracking:**
```spl
index=meraki (sourcetype="meraki:api:bluetooth" OR sourcetype="meraki:scanning") earliest=-4h
| where match(type, "(?i)ble") OR isnotnull(uuid)
| stats latest(rssi) as latest_rssi latest(ap_name) as nearest_ap count as observations dc(ap_name) as seen_by_aps by mac
| lookup ble_asset_inventory.csv mac OUTPUT asset_name asset_type owner
| eval device_class=case(isnotnull(asset_name), "TRACKED_ASSET", latest_rssi > -50, "NEARBY_DEVICE", 1==1, "BACKGROUND")
| eval nearest_location=nearest_ap
| where device_class IN ("TRACKED_ASSET", "NEARBY_DEVICE")
| sort device_class, -observations
```

**Asset movement tracking:**
```spl
index=meraki (sourcetype="meraki:api:bluetooth" OR sourcetype="meraki:scanning") earliest=-24h
| where match(type, "(?i)ble") OR isnotnull(uuid)
| lookup ble_asset_inventory.csv mac OUTPUT asset_name asset_type
| where isnotnull(asset_name)
| stats earliest(ap_name) as first_location latest(ap_name) as last_location dc(ap_name) as locations_visited by mac, asset_name
| where first_location != last_location
| table asset_name, mac, first_location, last_location, locations_visited
```

### Step 3 — Validate
(a) Place a known BLE beacon near an AP and verify it appears in the Splunk inventory.
(b) Move the beacon to a different AP's coverage area and verify the movement is tracked.
(c) Compare with Meraki Dashboard: Wireless > Bluetooth.

### Step 4 — Operationalize
Dashboard ("Meraki — BLE & Asset Tracking"):
- Row 1 — Single-value: "Tracked assets", "Assets in motion", "BLE devices detected", "Coverage APs".
- Row 2 — Tracked asset location table.
- Row 3 — Asset movement history.

Alerting:
- Warning (tracked asset leaves designated area): asset geofence violation.
- Info (daily): asset location summary report.

### Step 5 — Troubleshooting

- **BLE data not appearing** — BLE scanning must be enabled: Meraki Dashboard > Wireless > Bluetooth. Ensure "Scanning" is enabled (not just "Advertising").

- **Low accuracy for asset location** — BLE RSSI is affected by obstacles, reflections, and body absorption. Accuracy is typically 3-8 meters. For better accuracy, increase AP density or use dedicated BLE gateways.

- **Too many background BLE devices** — Filter by RSSI threshold (e.g., only devices with RSSI > -70) and use the asset lookup to focus on tracked devices.

## SPL

```spl
index=cisco_network sourcetype="meraki:api"
| stats count as client_count by ap_name, ssid
| eval capacity_pct=round(client_count*100/30, 2)
| where capacity_pct > 70
| sort - client_count
```

## Visualization

Bubble chart of capacity by AP; stacked bar of clients by SSID; capacity gauge.

## Known False Positives

Wireless client counts spike during shift changes, big events, or back-to-school style rushes; compare against the calendar before calling it an incident.

## References

- [Splunkbase app 5580](https://splunkbase.splunk.com/app/5580)
