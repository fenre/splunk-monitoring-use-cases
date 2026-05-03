<!-- AUTO-GENERATED from UC-5.4.13.json — DO NOT EDIT -->

---
id: "5.4.13"
title: "RSSI/Signal Strength Degradation Detection (Meraki MR)"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-5.4.13 · RSSI/Signal Strength Degradation Detection (Meraki MR)

> **Criticality:** Medium &middot; **Difficulty:** Intermediate &middot; **Pillar:** Observability &middot; **Type:** Performance

*We watch rssi/signal strength degradation detection (meraki mr) so we notice problems while they are still small, and we can fix them before Wi-Fi users get dropped calls or dead spots.*

---

## Description

Proactively identifies weak WiFi coverage areas and client placement issues before users experience connectivity problems.

## Value

Network operations teams monitor Meraki MR client RSSI values per AP and location to detect wireless coverage gaps, identify areas with weak signal causing poor client performance, and prioritize RF optimization.

## Implementation

Ingest Meraki API client data periodically; analyze RSSI distribution by AP and SSID. Set thresholds for "poor" signal (< -70 dBm).

## Detailed Implementation

### Prerequisites
- Meraki API or syslog providing client RSSI (Received Signal Strength Indicator) data. Data in `index=meraki` with `sourcetype=meraki:events` or `sourcetype=meraki:api:wireless`. Key fields: `client_mac`, `rssi` (dBm), `ap_name`, `ssid`, `network`.
- RSSI ranges: Excellent (> -55 dBm), Good (-55 to -67 dBm), Fair (-67 to -70 dBm), Weak (-70 to -80 dBm), Unusable (< -80 dBm). Below -70 dBm, clients experience packet retransmissions, low data rates, and connectivity issues.

### Step 1 — Configure data collection
Verify RSSI data:
```spl
index=meraki (sourcetype="meraki:events" OR sourcetype="meraki:api:wireless") earliest=-4h
| where isnotnull(rssi)
| stats avg(rssi) as avg_rssi by ap_name
| sort avg_rssi
```

### Step 2 — Create the search and alert

**Primary search — Signal strength degradation by AP:**
```spl
index=meraki (sourcetype="meraki:events" OR sourcetype="meraki:api:wireless") earliest=-4h
| where isnotnull(rssi)
| stats avg(rssi) as avg_rssi min(rssi) as min_rssi count(eval(rssi < -75)) as weak_connections count as total_connections by ap_name, ssid
| eval weak_pct=round(100*weak_connections/total_connections, 1)
| eval signal_quality=case(avg_rssi > -55, "Excellent", avg_rssi > -67, "Good", avg_rssi > -70, "Fair", avg_rssi > -80, "Weak", 1==1, "Unusable")
| lookup wireless_ap_inventory.csv ap_name OUTPUT building floor zone
| where signal_quality IN ("Weak", "Unusable") OR weak_pct > 30
| table ap_name, building, floor, zone, ssid, avg_rssi, min_rssi, weak_pct, signal_quality
| sort avg_rssi
```

**RSSI distribution heatmap:**
```spl
index=meraki (sourcetype="meraki:events" OR sourcetype="meraki:api:wireless") earliest=-4h
| where isnotnull(rssi)
| eval rssi_bucket=case(rssi > -55, "Excellent", rssi > -67, "Good", rssi > -70, "Fair", rssi > -80, "Weak", 1==1, "Unusable")
| lookup wireless_ap_inventory.csv ap_name OUTPUT building floor
| stats count by building, floor, rssi_bucket
| chart sum(count) by building rssi_bucket
```

### Step 3 — Validate
(a) Walk away from an AP and verify RSSI decreases in Splunk.
(b) Compare RSSI values with Meraki Dashboard: Wireless > Monitor > Clients > Signal Strength.
(c) Verify location data: check that APs with weak signals are in expected edge-of-coverage areas.

### Step 4 — Operationalize
Dashboard ("Meraki — Signal Strength"):
- Row 1 — Single-value tiles: "APs with weak signal", "Clients with RSSI < -75", "Average RSSI", "Worst AP".
- Row 2 — AP signal quality table with building/floor context.
- Row 3 — RSSI distribution by building.

Alerting:
- Warning (AP avg RSSI < -75 with > 20 clients): coverage issue — clients experiencing poor performance.
- Info (monthly): signal quality report for RF planning.

### Step 5 — Troubleshooting

- **All clients show weak signal on one AP** — AP power output may have been reduced (auto-power), or there's a physical obstruction. Check Meraki Dashboard for the AP's transmit power setting.

- **RSSI data not available** — RSSI is typically included in association and roaming events, not in all event types. Ensure syslog includes wireless event logs.

- **RSSI seems higher than expected** — Meraki may report RSSI in different formats depending on the event type. Verify the dBm interpretation.

## SPL

```spl
index=cisco_network sourcetype="meraki:api"
| eval rssi_level=case(rssi>=-50, "Excellent", rssi>=-60, "Good", rssi>=-70, "Fair", rssi<-70, "Poor")
| stats avg(rssi) as avg_rssi, min(rssi) as min_rssi, count by ap_name, ssid, rssi_level
| where min_rssi < -70 or avg_rssi < -65
```

## Visualization

Heatmap of RSSI by AP location; histogram of signal strength distribution; gauge charts for coverage quality by SSID.

## Known False Positives

RF noise and channel changes can spike when neighbors deploy new gear, microwaves run, or the controller runs automatic channel updates; weather and outdoor clients can also move the numbers.

## References

- [Splunkbase app 5580](https://splunkbase.splunk.com/app/5580)
