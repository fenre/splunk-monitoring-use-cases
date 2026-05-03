<!-- AUTO-GENERATED from UC-5.4.35.json — DO NOT EDIT -->

---
id: "5.4.35"
title: "Aruba Air Monitor — WIDS/WIPS Events (HPE Aruba)"
criticality: "high"
splunkPillar: "Security"
---

# UC-5.4.35 · Aruba Air Monitor — WIDS/WIPS Events (HPE Aruba)

> **Criticality:** High &middot; **Difficulty:** Intermediate &middot; **Pillar:** Security &middot; **Type:** Security

*We watch aruba air monitor — wids/wips events (hpe aruba) so we notice problems while they are still small, and we can fix them before Wi-Fi users get dropped calls or dead spots.*

---

## Description

Aruba's Wireless Intrusion Detection and Prevention System (WIDS/WIPS) detects rogue APs, evil twin attacks, ad-hoc networks, unauthorized bridges, and DoS attacks (deauthentication floods, association floods). Air Monitor (AM) mode APs or hybrid APs provide dedicated RF security scanning.

## Value

Wireless security teams detect and classify Aruba WIDS/WIPS threats (rogue APs, evil twins, deauth floods) from Air Monitor events, correlating detections with physical site locations for containment.

## Implementation

Enable WIDS/WIPS and AM-capable APs per Aruba design guide; ensure security-class syslog messages are forwarded with TA parsing for threat category and severity. Tune alerts for critical classes (rogue AP, evil twin, deauth flood). Correlate with physical site/AP layout for containment workflows.

## Detailed Implementation

### Prerequisites
- Aruba Networks Add-on for Splunk (Splunkbase 4668) installed, receiving syslog from Aruba Mobility Controllers with WIDS/WIPS security messages. Data in `index=network` with `sourcetype=aruba:syslog`. Key fields: `category` (SECURITY), `subsystem` (wids/WIDS), `wids_classification`, `threat_name`, `intrusion_type`, `severity`, `ap_name`, `detecting_ap`, `channel`, `bssid`, `ssid`.
- Aruba WIDS/WIPS operates in two modes: (1) **Air Monitor (AM)** — dedicated scanning APs that do not serve clients but continuously scan all channels, (2) **Hybrid AP** — serves clients and performs background scanning between channels. AM mode provides better detection but reduces AP capacity.
- WIDS threat classifications: Rogue AP (unauthorized AP on wired network), Interfering AP (nearby but not on your network), Evil Twin (spoofing your SSID), Ad-hoc Network (peer-to-peer), DoS (deauth flood, association flood), Wireless Bridge.

### Step 1 — Configure data collection
Enable WIDS/WIPS on the Aruba Mobility Controller:
```
(Aruba-MC) # wlan wids-profile default
(Aruba-MC)(WIDS profile "default") # rogue-ap-detection
(Aruba-MC)(WIDS profile "default") # suspected-rogue-ap-detection
(Aruba-MC)(WIDS profile "default") # intrusion-detection
```
Ensure syslog severity includes security events (informational or higher).

Verify WIDS data:
```spl
index=network sourcetype="aruba:syslog" (category="SECURITY" OR subsystem="wids" OR subsystem="WIDS") earliest=-24h
| stats count by wids_classification, severity
```

### Step 2 — Create the search and alert

**Primary search — WIDS threat detection with classification:**
```spl
index=network sourcetype="aruba:syslog" (category="SECURITY" OR subsystem="wids" OR subsystem="WIDS" OR match(_raw, "(?i)(rogue|evil.twin|ad-hoc|deauth|disassoc).*(flood|detected|attack|alert)")) earliest=-24h
| eval threat=coalesce(wids_classification, threat_name, intrusion_type, ids_signature, alert_type)
| eval sev=coalesce(severity, threat_severity, priority)
| eval threat_class=case(match(threat, "(?i)evil.twin"), "EVIL_TWIN", match(threat, "(?i)rogue") AND match(_raw, "(?i)wired|on.wire"), "WIRED_ROGUE", match(threat, "(?i)rogue"), "ROGUE_AP", match(threat, "(?i)deauth.*flood"), "DEAUTH_FLOOD", match(threat, "(?i)assoc.*flood"), "ASSOC_FLOOD", match(threat, "(?i)ad.?hoc"), "ADHOC_NETWORK", match(threat, "(?i)bridge"), "WIRELESS_BRIDGE", 1==1, "OTHER")
| eval risk=case(threat_class="EVIL_TWIN", "CRITICAL — attacker spoofing corporate SSID", threat_class="WIRED_ROGUE", "CRITICAL — unauthorized AP on wired network", threat_class="DEAUTH_FLOOD", "HIGH — active DoS attack", threat_class="ASSOC_FLOOD", "HIGH — active DoS attack", threat_class="ROGUE_AP", "MEDIUM — unauthorized AP detected", 1==1, "LOW")
| lookup aruba_ap_inventory.csv ap_name as detecting_ap OUTPUT site, building, floor
| stats count as detections dc(bssid) as unique_threats values(ssid) as ssids latest(_time) as last_detected by threat_class, risk, site, detecting_ap, channel
| sort risk, -detections
```

**Containment status tracking:**
```spl
index=network sourcetype="aruba:syslog" (category="SECURITY" OR subsystem="wids") earliest=-24h
| where match(_raw, "(?i)(contain|tarpit|block|prevent)")
| eval action=case(match(_raw, "(?i)contain"), "CONTAINED", match(_raw, "(?i)tarpit"), "TARPITTED", match(_raw, "(?i)block"), "BLOCKED", 1==1, "PREVENTED")
| stats count as actions values(bssid) as target_bssids values(detecting_ap) as by_ap by action
```

### Step 3 — Validate
(a) Enable a personal hotspot near an Aruba AP and verify it's detected as "Interfering AP" in Splunk.
(b) Cross-check with the Aruba controller: `show wids rogue-ap-table` — verify the same BSSIDs appear.
(c) For AM-mode APs, confirm they're scanning all channels: `show ap arm status ap-name <AP>`.

### Step 4 — Operationalize
Dashboard ("Aruba — Wireless Threat Detection"):
- Row 1 — Single-value tiles: "Active threats", "Evil twins", "Wired rogues", "DoS attacks", "Containments".
- Row 2 — Threat classification table with risk level, site/building context, and detecting AP.
- Row 3 — Containment action log.

Alerting:
- Critical (evil twin detected): immediate SOC escalation — attacker may be harvesting credentials.
- Critical (wired rogue AP): physical investigation required — unauthorized device on corporate network.
- High (deauth/assoc flood > 100 events in 5 min): active DoS attack targeting wireless clients.
- Warning (new rogue AP detected): investigate and classify.

### Step 5 — Troubleshooting

- **Too many "Interfering AP" alerts** — Neighboring business APs will always be detected. These are not rogues. Use the Aruba controller's "Known AP" list to suppress: `wlan wids-profile <name>` > `known-ap-list <filename>`. In Splunk, filter by `threat_class != "ROGUE_AP"` or maintain a neighbor BSSID lookup.

- **Evil twin detected but can't find the device** — Use RSSI from multiple detecting APs to triangulate the location. The Aruba controller shows: `show wids rogue-ap-list bssid <BSSID>` with detecting AP and signal strength. Physically sweep the area.

- **WIDS events only from some APs** — Only APs configured for AM mode or hybrid scanning detect threats. Check AP mode: `show ap database`. APs in "Access" mode only scan their own channel.

## SPL

```spl
index=network sourcetype="aruba:syslog" (category="SECURITY" OR subsystem="wids" OR subsystem="WIDS" OR match(_raw, "(?i)(rogue|evil.twin|ad-hoc|deauth|disassoc).*(flood|detected|attack|alert)"))
| eval threat_type=coalesce(wids_classification, threat_name, intrusion_type, ids_signature, alert_type)
| eval sev=coalesce(severity, threat_severity, priority)
| stats count by threat_type, sev, ap_name, channel, detecting_ap, bssid
| sort -count
```

## Visualization

Table (threat type, severity, channel, detecting AP), Bar chart (threats by type), Timeline (WIDS event rate), Map or floor plan overlay when location fields exist.

## Known False Positives

Neighbor networks, personal hotspots, or test labs can look like rogues; confirm against known nearby SSIDs and change windows before escalation.

## References

- [Splunkbase app 4668](https://splunkbase.splunk.com/app/4668)
- [CIM: Intrusion_Detection](https://docs.splunk.com/Documentation/CIM/latest/User/Intrusion_Detection)
