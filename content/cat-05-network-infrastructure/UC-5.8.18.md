<!-- AUTO-GENERATED from UC-5.8.18.json — DO NOT EDIT -->

---
id: "5.8.18"
title: "Device Online/Offline Status Monitoring (Meraki)"
criticality: "critical"
splunkPillar: "Observability"
---

# UC-5.8.18 · Device Online/Offline Status Monitoring (Meraki)

> **Criticality:** Critical &middot; **Difficulty:** Intermediate &middot; **Pillar:** Observability &middot; **Type:** Availability

*We help you know quickly when a Meraki box drops offline, before users open tickets about dead Wi‑Fi or VPN.*

---

## Description

Tracks device connectivity status to quickly identify and respond to device failures.

## Value

Network operations teams monitor Meraki device online/offline status with impact-aware urgency classification, distinguishing gateway outages (site down) from AP outages (coverage gaps) and tracking offline duration for dispatch decisions.

## Implementation

Poll devices API for status. Alert on offline devices.

## Detailed Implementation

### Prerequisites
- Cisco Meraki Add-on for Splunk polling device status via Dashboard API. Data in `index=meraki` with `sourcetype=meraki:api:devices`. Key fields: `serial`, `name`, `model`, `network`, `status` (online/offline/alerting/dormant), `lastReportedAt` (ISO 8601 timestamp).
- For real-time offline detection, also configure Meraki webhooks to Splunk HEC. Webhooks fire immediately when a device goes offline, providing near-real-time notification vs. the API polling interval.

### Step 1 — Configure data collection
Verify device status data:
```spl
index=meraki sourcetype="meraki:api:devices" earliest=-15m
| dedup serial sortby -_time
| stats count by status
```

### Step 2 — Create the search and alert

**Primary search — Offline device monitoring with duration:**
```spl
index=meraki sourcetype="meraki:api:devices" earliest=-15m
| dedup serial sortby -_time
| where status="offline"
| eval last_seen_epoch=strptime(lastReportedAt, "%Y-%m-%dT%H:%M:%SZ")
| eval offline_hours=round((now() - last_seen_epoch)/3600, 1)
| eval device_type=case(match(model, "^MX"), "Gateway", match(model, "^MR"), "AP", match(model, "^MS"), "Switch", match(model, "^MV"), "Camera", match(model, "^MT"), "Sensor", 1==1, "Other")
| lookup meraki_networks.csv network OUTPUT site_name tier
| eval impact=case(device_type="Gateway", "SITE_DOWN", device_type="Switch" AND offline_hours > 0.5, "CONNECTIVITY_LOSS", device_type="AP", "COVERAGE_GAP", 1==1, "MONITORING_LOSS")
| eval urgency=case(impact="SITE_DOWN", "CRITICAL", offline_hours > 24, "HIGH", offline_hours > 4, "MEDIUM", 1==1, "LOW")
| table name, serial, model, device_type, network, site_name, tier, offline_hours, impact, urgency
| sort urgency, -offline_hours
```

#### Understanding this SPL: Device impact varies by type: an offline MX gateway means the entire site loses connectivity; an offline AP creates a wireless coverage gap; an offline switch affects connected wired devices. The `lastReportedAt` field shows when the device last communicated with the Meraki cloud, enabling offline duration calculation. Longer offline durations suggest hardware failure or power loss rather than transient connectivity issues.

**Online/offline status change timeline:**
```spl
index=meraki sourcetype="meraki:api:devices" earliest=-24h
| eval is_offline=if(status="offline", 1, 0)
| bin _time span=15m
| stats sum(is_offline) as offline_count dc(serial) as total_devices by _time
| eval offline_pct=round(100*offline_count/total_devices, 1)
| timechart span=15m avg(offline_pct) as "Offline %"
```

**Devices offline for extended periods:**
```spl
index=meraki sourcetype="meraki:api:devices" status="offline" earliest=-15m
| dedup serial sortby -_time
| eval last_seen_epoch=strptime(lastReportedAt, "%Y-%m-%dT%H:%M:%SZ")
| eval offline_days=round((now() - last_seen_epoch)/86400, 1)
| where offline_days > 7
| table name, serial, model, network, offline_days
| sort -offline_days
```

### Step 3 — Validate
(a) Power off a test device and verify it shows as offline in Splunk within the polling interval.
(b) Compare offline device list with Meraki Dashboard: Organization > Monitor > Overview (filter by offline).
(c) Verify `lastReportedAt` timestamps are accurate and parsing correctly.

### Step 4 — Operationalize
Dashboard ("Meraki Device Status"):
- Row 1 — Single-value tiles: "Online", "Offline", "Alerting", "Offline gateways (critical)".
- Row 2 — Offline device table with impact and urgency.
- Row 3 — Offline % trending (24h).
- Row 4 — Long-term offline devices (> 7 days) — candidates for decommission or RMA.

Alerting:
- Critical (any MX gateway offline): site is down — page NOC.
- High (device offline > 24 hours): hardware failure likely — dispatch field support.
- Warning (any device offline > 4 hours): investigation needed.

### Step 5 — Troubleshooting

- **Device shows offline in Splunk but works** — API polling lag. The device recovered between polls. Reduce polling interval or use webhooks for real-time status.

- **Many devices show "dormant"** — Dormant means the device is claimed to the organization but has never connected to the Meraki cloud. These are usually spare/staging devices. Filter them from active monitoring.

- **lastReportedAt is very old but device is not flagged** — Some device types may not report `lastReportedAt` consistently. Use `status` field as the primary indicator.

## SPL

```spl
index=cisco_network sourcetype="meraki:api"
| stats latest(status) as device_status, latest(last_status_change) as status_change_time, count(eval(status="offline")) as offline_count by network_id
| eval offline_pct=round(offline_count*100/count, 2)
| where offline_count > 0
```

## Visualization

Device status table; offline count gauge; status change timeline.

## Known False Positives

Brief cellular or power blips to appliances can flip offline/online; use duration filters and local ping where possible before heavy paging.

## References

- [Splunkbase app 5580](https://splunkbase.splunk.com/app/5580)
