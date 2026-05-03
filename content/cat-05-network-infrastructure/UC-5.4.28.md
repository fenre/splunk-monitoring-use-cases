<!-- AUTO-GENERATED from UC-5.4.28.json — DO NOT EDIT -->

---
id: "5.4.28"
title: "AP Uptime and Availability Monitoring (Meraki MR)"
criticality: "critical"
splunkPillar: "Observability"
---

# UC-5.4.28 · AP Uptime and Availability Monitoring (Meraki MR)

> **Criticality:** Critical &middot; **Difficulty:** Beginner &middot; **Pillar:** Observability &middot; **Type:** Availability

*We watch ap uptime and availability monitoring (meraki mr) so we notice problems while they are still small, and we can fix them before Wi-Fi users get dropped calls or dead spots.*

---

## Description

Ensures all access points are online and operational; alerts on unexpected AP outages.

## Value

Network operations teams analyze Meraki wireless application-layer traffic patterns using DPI data, comparing bandwidth consumption across SSIDs and application categories to optimize traffic shaping policies.

## Implementation

Monitor device status API for all MR devices. Alert on status="offline".

## Detailed Implementation

### Prerequisites
- Meraki providing wireless client application usage data. Data in `index=meraki` with `sourcetype=meraki:api:wireless` or `sourcetype=meraki:api:clients`. Key fields: `client_mac`, `application` (L7 application name), `usage` (bytes), `ssid`, `ap_name`.
- Meraki performs deep packet inspection (DPI) to classify traffic by application (e.g., Office 365, Zoom, YouTube, Netflix). This enables: (1) understanding what applications consume wireless bandwidth, (2) validating traffic shaping policies, (3) identifying unauthorized application usage on corporate SSID.

### Step 1 — Configure data collection
Verify application data:
```spl
index=meraki (sourcetype="meraki:api:wireless" OR sourcetype="meraki:api:clients") earliest=-4h
| where isnotnull(application) AND isnotnull(usage)
| stats sum(usage) as bytes by application
| eval MB=round(bytes/1048576, 1)
| sort -MB
| head 20
```

### Step 2 — Create the search and alert

**Primary search — Application bandwidth consumption:**
```spl
index=meraki (sourcetype="meraki:api:wireless" OR sourcetype="meraki:api:clients") earliest=-4h
| where isnotnull(application) AND isnotnull(usage)
| stats sum(usage) as total_bytes dc(client_mac) as users by application, ssid
| eval total_GB=round(total_bytes/1073741824, 2)
| eval avg_per_user_MB=round(total_bytes/(users*1048576), 1)
| eval app_category=case(match(application, "(?i)(teams|zoom|webex|meet)"), "Unified Communications", match(application, "(?i)(office|sharepoint|onedrive|google.doc)"), "Productivity", match(application, "(?i)(youtube|netflix|hulu|twitch|tiktok)"), "Streaming", match(application, "(?i)(dropbox|box|gdrive|icloud)"), "Cloud Storage", match(application, "(?i)(windows.update|apple|software.update)"), "OS Updates", 1==1, "Other")
| sort -total_bytes
```

**Corporate vs guest SSID application comparison:**
```spl
index=meraki (sourcetype="meraki:api:wireless" OR sourcetype="meraki:api:clients") earliest=-4h
| where isnotnull(application) AND isnotnull(usage)
| eval ssid_type=case(match(ssid, "(?i)(corp|enterprise|secure)"), "Corporate", match(ssid, "(?i)(guest|visitor)"), "Guest", 1==1, "Other")
| eval app_category=case(match(application, "(?i)(teams|zoom|webex|meet)"), "UC", match(application, "(?i)(youtube|netflix|twitch|tiktok)"), "Streaming", 1==1, "Other")
| stats sum(usage) as bytes by ssid_type, app_category
| eval GB=round(bytes/1073741824, 2)
| chart sum(GB) by ssid_type app_category
```

### Step 3 — Validate
(a) Join a Zoom call on WiFi and verify the "Zoom" application appears in Splunk with appropriate byte count.
(b) Compare top applications with Meraki Dashboard: Network-wide > Clients > Application usage.
(c) Verify that traffic shaping rules (if configured) are reflected in application throughput.

### Step 4 — Operationalize
Dashboard ("Meraki — Wireless Application Usage"):
- Row 1 — Single-value: "Top application", "Total wireless bandwidth (4h)", "Streaming %", "UC %".
- Row 2 — Application bandwidth table with category, users, and per-user average.
- Row 3 — Corporate vs guest application comparison.

Alerting:
- Warning (streaming > 50% of corporate SSID bandwidth): enforce traffic shaping.
- Info (weekly): wireless application usage report.

### Step 5 — Troubleshooting

- **Application not classified** — Some encrypted applications (especially over QUIC/TLS 1.3) may not be classified by DPI. These appear as "Uncategorized HTTPS" or similar.

- **OS updates consuming excessive bandwidth** — Configure WSUS/SCCM for Windows Update delivery, or enable Apple caching server. This prevents each device from downloading updates over WiFi independently.

- **Application data not available** — Ensure traffic analysis is enabled: Meraki Dashboard > Network-wide > General > Traffic analysis: Detailed.

## SPL

```spl
index=cisco_network sourcetype="meraki:api" device_type=MR
| stats latest(status) as ap_status, latest(last_status_change) as last_change by ap_name, ap_mac
| where ap_status="offline"
```

## Visualization

Status table with last seen time; uptime percentage gauge; event alert dashboard.

## Known False Positives

Access points may go offline during scheduled firmware updates, PoE switch reboots, cabling work, or RF site surveys, which can look like an outage without a real coverage problem.

## References

- [Splunkbase app 5580](https://splunkbase.splunk.com/app/5580)
