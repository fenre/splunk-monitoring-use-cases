<!-- AUTO-GENERATED from UC-5.4.10.json — DO NOT EDIT -->

---
id: "5.4.10"
title: "Wireless IDS/IPS Events"
criticality: "critical"
splunkPillar: "Security"
---

# UC-5.4.10 · Wireless IDS/IPS Events

> **Criticality:** Critical &middot; **Difficulty:** Intermediate &middot; **Pillar:** Security &middot; **Type:** Security

*We watch wireless ids/ips events so we notice problems while they are still small, and we can fix them before Wi-Fi users get dropped calls or dead spots.*

---

## Description

Wireless attacks (deauth floods, evil twin, KRACK) compromise network security. Early detection prevents credential theft and MitM attacks.

## Value

Security operations teams detect active wireless attacks (deauth floods, evil twins, MitM, EAPOL attacks) with threat-level classification and physical location context, enabling rapid response and attacker localization.

## Implementation

1. Configure SC4S to receive Cisco WLC syslog. 2. The query uses rex to extract Snort-style signature id, signature name, and attacker MAC from wIPS messages. 3. If you are running Meraki MR instead: enable the Air Marshal input (sourcetype=meraki:airmarshal) and filter on threat-related event types — Meraki MR does not have Snort-style wIPS signatures but Air Marshal covers rogue / spoof / containment events.

## Detailed Implementation

### Prerequisites
- Wireless IDS/IPS events from controllers or dedicated sensors. Sources: (1) Cisco Adaptive wIPS via WLC syslog (`sourcetype=cisco:wlc`), (2) Meraki Air Marshal events (`sourcetype=meraki`), (3) Aruba WIDS/WIPS (`sourcetype=aruba:controller`).
- Key fields: `alert_type` (deauth_flood, beacon_flood, evil_twin, rogue_ap, mitm, eapol_flood), `severity`, `src_mac` (attacker MAC), `target_mac`, `ap_name` (detecting AP), `channel`, `action` (alert/contain/block).
- Wireless attacks include: (1) Deauthentication flood — forces all clients to disconnect and reconnect, (2) Beacon flood — overwhelms clients with fake SSIDs, (3) Evil twin — rogue AP mimicking corporate SSID, (4) EAPOL flood — targets the authentication process, (5) Man-in-the-middle — interception of client traffic.

### Step 1 — Configure data collection
Verify WIDS/WIPS events:
```spl
index=wireless earliest=-24h
| where match(_raw, "(?i)(wips|wids|ids.*wireless|intrusion|deauth.*flood|beacon.*flood|evil.twin|eapol|containment)")
| stats count by sourcetype
```

### Step 2 — Create the search and alert

**Primary search — Wireless IDS/IPS events by severity:**
```spl
index=wireless earliest=-24h
| where match(_raw, "(?i)(wips|wids|intrusion|deauth.*flood|beacon.*flood|evil.twin|eapol|containment|mitm|spoofing)")
| eval attack_type=case(match(_raw, "(?i)deauth.*flood"), "Deauth Flood", match(_raw, "(?i)beacon.*flood"), "Beacon Flood", match(_raw, "(?i)evil.twin"), "Evil Twin", match(_raw, "(?i)eapol.*flood"), "EAPOL Flood", match(_raw, "(?i)mitm|man.in.the.middle"), "Man-in-the-Middle", match(_raw, "(?i)spoof|impersonat"), "MAC Spoofing", match(_raw, "(?i)containment"), "AP Containment", 1==1, "Other IDS Event")
| eval attacker=coalesce(src_mac, attacker_mac)
| eval detector=coalesce(ap_name, detecting_ap)
| lookup wireless_ap_inventory.csv ap_name as detector OUTPUT building floor zone
| eval threat_level=case(attack_type IN ("Evil Twin", "Man-in-the-Middle"), "CRITICAL", attack_type IN ("Deauth Flood", "EAPOL Flood"), "HIGH", attack_type="Beacon Flood", "MEDIUM", 1==1, "LOW")
| stats count as events dc(detector) as detecting_aps values(building) as locations latest(_time) as last_seen by attack_type, attacker, threat_level
| sort threat_level, -events
```

#### Understanding this SPL: Wireless attacks are categorized by intent. Evil Twin and MitM are credential theft attacks — critical because they compromise user data. Deauth and EAPOL floods are denial-of-service attacks — disruptive but don't steal data. Beacon floods are nuisance attacks. The location context (which building/floor the detecting APs are in) helps physical security teams locate the attacker.

**Active containment status:**
```spl
index=wireless earliest=-24h
| where match(_raw, "(?i)containment|contain|block")
| eval contained_device=coalesce(rogue_mac, src_mac, target_mac)
| eval action=case(match(_raw, "(?i)start.*contain"), "CONTAIN_START", match(_raw, "(?i)stop.*contain"), "CONTAIN_STOP", 1==1, "CONTAINMENT_EVENT")
| stats count by contained_device, action, ap_name
```

### Step 3 — Validate
(a) Generate a test deauthentication attack (using authorized penetration testing tools) and verify the WIDS alert appears.
(b) Compare WIDS events with the wireless controller's security dashboard.
(c) Verify containment is working: if a rogue AP is being contained, clients shouldn't be able to connect to it.

### Step 4 — Operationalize
Dashboard ("Wireless — IDS/IPS"):
- Row 1 — Single-value tiles: "Active attacks (24h)", "Critical threats", "APs under containment", "Attack sources detected".
- Row 2 — Attack events table: type, attacker MAC, threat level, events, detecting APs, locations.
- Row 3 — Active containment status.
- Row 4 — Attack trending (7 days).

Alerting:
- Critical (Evil Twin or MitM detected): credential theft risk — locate and remove.
- High (Deauth flood detected): denial of service — identify source location.
- Warning (any WIDS event): security awareness — investigate.

### Step 5 — Troubleshooting

- **Deauth flood alerts from legitimate roaming** — Some devices send deauth frames during normal roaming. Tune the deauth flood threshold to require > 10 frames in 1 second before alerting.

- **No WIDS events detected** — Wireless IDS may not be enabled. For Cisco: enable wIPS on the WLC. For Meraki: Air Marshal is enabled by default. For Aruba: enable WIDS in the AP group configuration.

- **Containment not effective** — Wireless containment works by sending deauth frames to clients connecting to the rogue AP. If the rogue AP uses 802.11w (Protected Management Frames), containment is ineffective. Physical removal is required.

## SPL

```spl
index=network sourcetype="cisco:wlc" "IDS Signature" OR "wIPS"
| rex "Signature (?<sig_id>\d+).*?(?<sig_name>[^,]+).*?MAC (?<attacker_mac>[0-9a-f:]+)"
| stats count by sig_name, attacker_mac | sort -count
```

## Visualization

Table (signature, attacker MAC, count), Timeline, Single value (alerts today).

## Known False Positives

Neighbor networks, personal hotspots, or test labs can look like rogues; confirm against known nearby SSIDs and change windows before escalation.

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
