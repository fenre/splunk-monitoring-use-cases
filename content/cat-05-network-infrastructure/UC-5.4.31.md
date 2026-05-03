<!-- AUTO-GENERATED from UC-5.4.31.json — DO NOT EDIT -->

---
id: "5.4.31"
title: "WiFi Geolocation and Location Analytics (Meraki MR)"
criticality: "low"
splunkPillar: "Observability"
---

# UC-5.4.31 · WiFi Geolocation and Location Analytics (Meraki MR)

> **Criticality:** Low &middot; **Difficulty:** Beginner &middot; **Pillar:** Observability &middot; **Type:** Performance

*We watch wifi geolocation and location analytics (meraki mr) so we notice problems while they are still small, and we can fix them before Wi-Fi users get dropped calls or dead spots.*

---

## Description

Uses Cisco Meraki location services to track foot traffic patterns and heat maps in physical spaces.

## Value

Network operations teams inventory wireless client device types across Meraki networks, identifying OS distribution, IoT device presence on corporate SSIDs, and BYOD policy violations for security segmentation.

## Implementation

Use Meraki location API to get AP-based location estimates. Map to floor/zone.

## Detailed Implementation

### Prerequisites
- Meraki providing wireless client operating system and device type data. Data in `index=meraki` with `sourcetype=meraki:api:clients` or `sourcetype=meraki:events`. Key fields: `client_mac`, `os` (operating system), `manufacturer`, `deviceTypePrediction`, `ssid`, `ap_name`.
- Understanding the wireless client population is essential for: (1) capacity planning (how many devices per AP), (2) RF optimization (IoT devices on 2.4 GHz, laptops on 5 GHz), (3) security (identifying rogue device types), (4) BYOD policy enforcement.

### Step 1 — Configure data collection
Verify client device data:
```spl
index=meraki (sourcetype="meraki:api:clients" OR sourcetype="meraki:events") earliest=-4h
| where isnotnull(client_mac) AND (isnotnull(os) OR isnotnull(manufacturer))
| stats dc(client_mac) as devices by os, manufacturer
| sort -devices
```

### Step 2 — Create the search and alert

**Primary search — Client device type inventory:**
```spl
index=meraki (sourcetype="meraki:api:clients" OR sourcetype="meraki:events") earliest=-4h
| where isnotnull(client_mac)
| stats latest(os) as os latest(manufacturer) as manufacturer latest(ssid) as ssid latest(ap_name) as ap latest(rssi) as rssi by client_mac
| eval device_category=case(match(os, "(?i)(windows|macos|mac.os|chromeos)"), "Computer", match(os, "(?i)(ios|iphone|ipad|android)"), "Mobile", match(os, "(?i)(printer|zebra|hp.jet)"), "Printer", match(manufacturer, "(?i)(nest|ring|ecobee|sonos|alexa|roku)"), "IoT/Smart Home", match(manufacturer, "(?i)(axis|hikvision|dahua|arlo)"), "Camera", 1==1, "Unknown/Other")
| stats count as device_count by device_category, os, ssid
| sort device_category, -device_count
```

**Device type per SSID (security check):**
```spl
index=meraki (sourcetype="meraki:api:clients" OR sourcetype="meraki:events") earliest=-4h
| where isnotnull(client_mac)
| stats latest(os) as os latest(manufacturer) as manufacturer latest(ssid) as ssid by client_mac
| eval is_iot=if(match(manufacturer, "(?i)(nest|ring|ecobee|sonos|axis|hikvision|dahua|shelly|tuya|espressif)"), "IoT", "Non-IoT")
| stats count(eval(is_iot="IoT")) as iot_devices count(eval(is_iot="Non-IoT")) as non_iot count as total by ssid
| eval iot_pct=round(100*iot_devices/total, 1)
| where iot_devices > 0 AND NOT match(ssid, "(?i)(iot|sensor|device)")
| eval concern="IoT devices on non-IoT SSID — check VLAN segmentation"
| sort -iot_pct
```

### Step 3 — Validate
(a) Connect a known device and verify its OS/manufacturer appears correctly in Splunk.
(b) Compare device counts by OS with Meraki Dashboard: Network-wide > Clients > OS.
(c) Identify IoT devices on the corporate SSID that should be on a dedicated IoT SSID.

### Step 4 — Operationalize
Dashboard ("Meraki — Client Device Inventory"):
- Row 1 — Single-value: "Total devices", "Computers", "Mobile", "IoT devices", "Unknown".
- Row 2 — Device type breakdown by SSID.
- Row 3 — IoT devices on non-IoT SSIDs (security concern).

Alerting:
- Warning (IoT devices > 5 on corporate SSID): VLAN segmentation issue.
- Info (monthly): device type inventory report for capacity planning.

### Step 5 — Troubleshooting

- **Many "Unknown" devices** — Devices with MAC address randomization (iOS 14+, Android 10+) appear as unknown. This is increasingly common. Consider using Meraki's RADIUS-based fingerprinting or 802.1X certificates for accurate identification.

- **IoT devices on corporate SSID** — These devices should be on a dedicated IoT SSID with restricted network access. Create a separate SSID with appropriate VLAN and firewall rules.

- **Device count higher than employee count** — Normal: most users have 2-3 devices (laptop, phone, tablet). Factor this into capacity planning.

## SPL

```spl
index=cisco_network sourcetype="meraki:api" ap_name=*
| stats count as foot_traffic by ap_name, floor
| geom geo_from_metric lat, lon
```

## Visualization

Heat map by physical location; AP heat map overlay; zone traffic comparison.

## Known False Positives

Wireless metrics move with user behavior, maintenance, and nearby RF; we tune alerts around change windows and known busy hours so normal days do not page the team.

## References

- [Splunkbase app 5580](https://splunkbase.splunk.com/app/5580)
