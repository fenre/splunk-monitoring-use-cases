<!-- AUTO-GENERATED from UC-5.4.4.json — DO NOT EDIT -->

---
id: "5.4.4"
title: "Rogue AP Detection"
criticality: "high"
splunkPillar: "Security"
---

# UC-5.4.4 · Rogue AP Detection

> **Criticality:** High &middot; **Difficulty:** Beginner &middot; **Pillar:** Security &middot; **Type:** Security

*We watch rogue ap detection so we notice problems while they are still small, and we can fix them before Wi-Fi users get dropped calls or dead spots.*

---

## Description

Rogue APs are unauthorized and can be used for man-in-the-middle attacks or network bridging.

## Value

Security operations teams detect unauthorized rogue access points with risk-based classification (on-wire, evil twin, impersonation), enabling rapid physical isolation of the highest-risk rogues before credential theft or network bridging occurs.

## Implementation

1. Configure SC4S to receive Cisco WLC syslog. 2. The query above surfaces rogue AP detections with detecting_ap, channel, and rogue_mac. 3. If you are running Meraki MR instead: enable the Air Marshal input (sourcetype=meraki:airmarshal) in Splunk_TA_cisco_meraki and filter on type=rogue_ssid_detected / type=ssid_spoofing_detected — both come with ssid, bssid, src, dst, channel, rssi fields.

## Detailed Implementation

### Prerequisites
- Wireless IDS/IPS or management platform reporting rogue AP detections. Sources: (1) Cisco WLC — CleanAir and rogue AP detection events (`sourcetype=cisco:wlc`), (2) Meraki Air Marshal via API/events (`sourcetype=meraki`), (3) Aruba WIDS/WIPS events (`sourcetype=aruba:controller`).
- Key fields: `rogue_mac` (MAC of detected rogue AP), `rogue_ssid` (SSID broadcast by rogue), `detecting_ap` (AP that detected it), `rssi` (signal strength — proximity indicator), `channel`, `classification` (rogue/friendly/contained), `is_on_wire` (detected on wired network — highest risk).
- Build `authorized_aps.csv` lookup: `mac,ap_name,owner,status` for all known authorized APs. Any AP not in this lookup is potentially rogue.

### Step 1 — Configure data collection
Verify rogue AP detection events:
```spl
index=wireless earliest=-24h
| where match(_raw, "(?i)(rogue|unauthorized.*ap|air.marshal|unknown.*ap|containment)")
| stats count by sourcetype
```

### Step 2 — Create the search and alert

**Primary search — Rogue AP detection with risk assessment:**
```spl
index=wireless earliest=-24h
| where match(_raw, "(?i)(rogue|unauthorized.*ap|air.marshal|unknown.*ap)")
| eval rogue_id=coalesce(rogue_mac, src_mac)
| eval rogue_network=coalesce(rogue_ssid, ssid)
| eval detector=coalesce(detecting_ap, ap_name)
| lookup authorized_aps.csv mac as rogue_id OUTPUT ap_name as known_name status as known_status
| where isnull(known_name)
| eval risk=case(match(_raw, "(?i)on.wire|wired|lan"), "CRITICAL_ON_WIRE", rogue_network=ssid AND isnotnull(ssid), "HIGH_EVIL_TWIN", isnotnull(rogue_network) AND match(rogue_network, "(?i)(corp|internal|employee)"), "HIGH_IMPERSONATION", rssi > -50, "MEDIUM_NEARBY", 1==1, "LOW")
| stats count as detections dc(detector) as detecting_aps latest(_time) as last_seen values(rogue_network) as ssids by rogue_id, risk
| eval last_seen_str=strftime(last_seen, "%Y-%m-%d %H:%M")
| sort risk, -detections
```

#### Understanding this SPL: The risk assessment is crucial. A rogue AP on the wired network (`CRITICAL_ON_WIRE`) is the highest risk — it provides a bridge between your wired LAN and an unauthorized wireless network, bypassing all network access controls. An "evil twin" (same SSID as your corporate network) can trick users into connecting and capturing their credentials. A nearby rogue (high RSSI) is more concerning than a distant one (could be a neighbor's AP).

**Evil twin detection (SSIDs matching corporate networks):**
```spl
index=wireless earliest=-24h
| where match(_raw, "(?i)(rogue|unauthorized.*ap|air.marshal)")
| eval rogue_network=coalesce(rogue_ssid, ssid)
| eval rogue_id=coalesce(rogue_mac, src_mac)
| lookup authorized_aps.csv mac as rogue_id OUTPUT ap_name as known_name
| where isnull(known_name) AND isnotnull(rogue_network)
| lookup corporate_ssids.csv ssid as rogue_network OUTPUT is_corporate
| where is_corporate="yes"
| stats count by rogue_id, rogue_network, detecting_ap
```

### Step 3 — Validate
(a) Set up a test rogue AP (personal hotspot with a unique SSID) near a managed AP and verify detection in Splunk.
(b) Compare rogue AP lists with the wireless controller's rogue AP dashboard.
(c) Verify the authorized AP lookup is complete — no legitimate APs should be classified as rogue.

### Step 4 — Operationalize
Dashboard ("Wireless — Rogue AP Detection"):
- Row 1 — Single-value tiles: "Active rogues", "On-wire rogues (CRITICAL)", "Evil twins", "New rogues (24h)".
- Row 2 — Rogue AP table: MAC, SSID, risk level, detections, detecting APs, last seen.
- Row 3 — Evil twin alerts.
- Row 4 — Rogue AP location estimation (based on detecting APs and RSSI).

Alerting:
- Critical (rogue AP on wired network): immediate security incident — physical isolation required.
- Critical (evil twin detected): credential theft risk — locate and remove.
- High (new rogue with strong signal): nearby unauthorized AP — investigate.

### Step 5 — Troubleshooting

- **Excessive rogue AP alerts** — In dense environments (office buildings, malls), neighboring APs are detected as rogues. Classify persistent neighboring APs as "friendly" in the controller. Raise the RSSI threshold to filter distant APs.

- **Rogue AP detected but can't find it physically** — Use the detecting APs' locations and RSSI values to triangulate. The rogue is closest to the AP with the strongest RSSI. Walk the area with a WiFi scanner.

- **"On wire" detection false positive** — The rogue AP may be using a MAC address that coincidentally matches a wired device OUI. Verify by checking the wired MAC address table on switches.

## SPL

```spl
index=network sourcetype="cisco:wlc" "rogue" ("detected" OR "alert" OR "contained")
| stats count by rogue_mac, detecting_ap, channel | sort -count
```

## Visualization

Table (rogue MAC, detecting AP, channel), Map, Single value.

## Known False Positives

Neighbor networks, personal hotspots, or test labs can look like rogues; confirm against known nearby SSIDs and change windows before escalation.

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
