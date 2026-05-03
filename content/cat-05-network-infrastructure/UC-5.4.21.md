<!-- AUTO-GENERATED from UC-5.4.21.json — DO NOT EDIT -->

---
id: "5.4.21"
title: "Wireless Latency Analysis by SSID and Location (Meraki MR)"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-5.4.21 · Wireless Latency Analysis by SSID and Location (Meraki MR)

> **Criticality:** Medium &middot; **Difficulty:** Intermediate &middot; **Pillar:** Observability &middot; **Type:** Performance

*We watch wireless latency analysis by ssid and location (meraki mr) so we notice problems while they are still small, and we can fix them before Wi-Fi users get dropped calls or dead spots.*

---

## Description

Identifies latency patterns across network to optimize AP placement, channel allocation, and client routing.

## Value

Wireless security teams leverage Meraki Air Marshal (WIDS/WIPS) events to detect rogue APs, evil twin attacks (SSID spoofing), and wired rogue devices, classifying threats by severity for rapid response.

## Implementation

Use API clients endpoint with latency metric. Aggregate by SSID and AP location.

## Detailed Implementation

### Prerequisites
- Meraki providing air marshal (wireless intrusion detection) events. Data in `index=meraki` with `sourcetype=meraki:events` or `sourcetype=meraki:api:airmarshal`. Key fields: `type` (air marshal), `bssid` (detected AP BSSID), `ssid` (detected AP SSID), `channels`, `rssi`, `wiredMac`, `classification` (rogue/known/contained).
- Meraki Air Marshal is the built-in wireless intrusion detection and prevention system (WIDS/WIPS) on all MR APs. It detects: rogue APs, ad-hoc networks, spoofed SSIDs, and can contain rogue APs by sending deauthentication frames.

### Step 1 — Configure data collection
Verify Air Marshal data:
```spl
index=meraki (sourcetype="meraki:events" OR sourcetype="meraki:api:airmarshal") earliest=-4h
| where match(type, "(?i)(rogue|air.?marshal|intrusion|wids)")
| stats count by type, ssid
```

### Step 2 — Create the search and alert

**Primary search — Rogue AP detection and classification:**
```spl
index=meraki (sourcetype="meraki:events" OR sourcetype="meraki:api:airmarshal") earliest=-24h
| where match(type, "(?i)(rogue|air.?marshal|intrusion|wids)")
| eval threat_level=case(match(type, "(?i)spoof"), "CRITICAL — SSID Spoofing", match(type, "(?i)contain"), "HIGH — Active Containment", match(type, "(?i)rogue") AND isnotnull(wiredMac), "HIGH — Wired Rogue AP", match(type, "(?i)rogue"), "MEDIUM — Rogue AP", match(type, "(?i)ad.?hoc"), "LOW — Ad-hoc Network", 1==1, "INFO")
| eval risk_context=case(match(threat_level, "CRITICAL"), "An attacker may be spoofing your corporate SSID to harvest credentials (evil twin attack)", match(threat_level, "Wired Rogue"), "A rogue AP is connected to your wired network — immediate security risk", 1==1, "Monitor and investigate")
| stats count as detections dc(bssid) as unique_rogues latest(_time) as last_detected by threat_level, risk_context
| sort threat_level
```

**Wired rogue AP correlation:**
```spl
index=meraki (sourcetype="meraki:events" OR sourcetype="meraki:api:airmarshal") earliest=-24h
| where match(type, "(?i)rogue") AND isnotnull(wiredMac)
| eval detecting_ap=coalesce(ap_name, deviceName)
| stats count as detections values(channels) as channels values(ssid) as ssid values(detecting_ap) as detected_by latest(_time) as last_seen by bssid, wiredMac
| sort -detections
```

### Step 3 — Validate
(a) Enable a personal hotspot near an AP and verify it appears as a rogue in Splunk.
(b) Compare detections with Meraki Dashboard: Wireless > Monitor > Air Marshal.
(c) Verify that known APs (neighboring legitimate APs) are not flagged as rogues.

### Step 4 — Operationalize
Dashboard ("Meraki — Wireless Threat Detection"):
- Row 1 — Single-value: "Active Rogues", "SSID Spoofing Alerts", "Wired Rogues", "Containment Active".
- Row 2 — Threat classification summary.
- Row 3 — Wired rogue AP details with MAC and detecting AP.

Alerting:
- Critical (SSID spoofing detected): immediate security incident — evil twin attack.
- High (wired rogue AP detected): rogue AP connected to corporate network — locate and remove.
- Warning (> 10 new rogue APs in 24h): investigate.

### Step 5 — Troubleshooting

- **False positives — neighboring business APs flagged as rogues** — Use Meraki Air Marshal's "Mark as known" feature. In Splunk, maintain a lookup of known neighbor BSSIDs and filter them from alerts.

- **SSID spoofing alert** — This is a serious threat. The attacker is broadcasting your corporate SSID. Use the RSSI and detecting AP to physically locate the rogue. Meraki can auto-contain the rogue by sending deauth frames.

- **No Air Marshal data** — Air Marshal runs on all MR APs by default. Check that syslog or API collection includes security events. In Meraki Dashboard: Network > General > Reporting > Syslog servers: enable "Security events".

## SPL

```spl
index=cisco_network sourcetype="meraki:api" latency=*
| stats avg(latency) as avg_latency, max(latency) as max_latency, count by ssid, ap_name
| eval latency_sla="OK"
| eval latency_sla=if(avg_latency > 50, "Warning", latency_sla)
| eval latency_sla=if(avg_latency > 100, "Critical", latency_sla)
```

## Visualization

Heatmap of latency by AP; line chart of latency trends; SLA compliance dashboard.

## Known False Positives

Wireless metrics move with user behavior, maintenance, and nearby RF; we tune alerts around change windows and known busy hours so normal days do not page the team.

## References

- [Splunkbase app 5580](https://splunkbase.splunk.com/app/5580)
