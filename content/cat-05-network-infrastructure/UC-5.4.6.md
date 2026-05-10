<!-- AUTO-GENERATED from UC-5.4.6.json — DO NOT EDIT -->

---
id: "5.4.6"
title: "RF Interference Events"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-5.4.6 · RF Interference Events

> **Criticality:** Medium &middot; **Difficulty:** Beginner &middot; **Pillar:** Observability &middot; **Type:** Fault, Performance

*We watch rf interference events so we notice problems while they are still small, and we can fix them before Wi-Fi users get dropped calls or dead spots.*

---

## Description

Radar (DFS), non-WiFi interference, and channel changes degrade wireless quality.

## Value

Network operations teams detect and classify RF interference sources (microwaves, Bluetooth, radar, jammers) impacting wireless performance, track DFS channel changes, and identify security threats from RF jamming devices.

## Implementation

1. Configure SC4S to receive Cisco WLC syslog. 2. The query above counts radar / DFS / interference / channel-change events by AP and channel. 3. If you are running Meraki MR instead: configure a Meraki Dashboard alert profile for 'radar detected (DFS)' and 'high channel utilization' and ingest via the Splunk_TA_cisco_meraki Webhook Logs (HEC) input (sourcetype=meraki:webhook). Polled API does not expose continuous channel-utilization counters.

## Detailed Implementation

### Prerequisites
- Wireless controller or spectrum analysis tool reporting RF interference events. Sources: (1) Cisco CleanAir — spectrum analysis via WLC syslog (`sourcetype=cisco:wlc`), (2) Meraki — RF interference events via API, (3) Aruba ARM — interference detection.
- Key fields: `ap_name`, `radio_band`, `channel`, `interference_type` (microwave, bluetooth, cordless phone, video bridge, radar, jammer), `severity`, `duty_cycle` (% of time the interferer is active), `rssi` (interferer signal strength).

### Step 1 — Configure data collection
Verify RF interference events:
```spl
index=wireless earliest=-24h
| where match(_raw, "(?i)(interference|cleanair|spectrum|radar|dfs|jammer|microwave|bluetooth)")
| stats count by sourcetype, ap_name
```

### Step 2 — Create the search and alert

**Primary search — RF interference events by type and impact:**
```spl
index=wireless earliest=-24h
| where match(_raw, "(?i)(interference|cleanair|spectrum|radar|dfs|jammer|microwave)")
| eval interferer=case(match(_raw, "(?i)microwave"), "Microwave Oven", match(_raw, "(?i)bluetooth"), "Bluetooth", match(_raw, "(?i)radar|dfs"), "Radar/DFS", match(_raw, "(?i)jammer"), "RF Jammer", match(_raw, "(?i)cordless"), "Cordless Phone", match(_raw, "(?i)video.bridge"), "Video Bridge", 1==1, "Unknown")
| eval ap_id=coalesce(ap_name, name)
| eval band=coalesce(radio_band, case(match(channel, "^(1|6|11)$"), "2.4GHz", 1==1, "5GHz"))
| lookup wireless_ap_inventory.csv ap_name as ap_id OUTPUT building floor zone
| stats count as events dc(ap_id) as affected_aps latest(_time) as last_seen by interferer, band, building
| eval impact=case(interferer="RF Jammer", "CRITICAL", interferer="Radar/DFS" AND events > 5, "HIGH", events > 20, "HIGH", events > 5, "MEDIUM", 1==1, "LOW")
| sort impact, -events
```

#### Understanding this SPL: Interference classification drives the response. Microwave ovens (2.4GHz, intermittent) require user education or shielding. Radar/DFS events force the AP off its channel — frequent DFS events indicate the AP is on a channel near an airport or weather radar. An RF jammer is a security incident. Bluetooth is usually benign unless from a medical device interfering with clinical WiFi.

**DFS channel change tracking:**
```spl
index=wireless earliest=-7d
| where match(_raw, "(?i)(dfs|radar|channel.change)")
| eval ap_id=coalesce(ap_name, name)
| stats count as dfs_events by ap_id
| where dfs_events > 3
| lookup wireless_ap_inventory.csv ap_name as ap_id OUTPUT building floor
| sort -dfs_events
```

### Step 3 — Validate
(a) If using Cisco CleanAir: check the WLC's CleanAir dashboard for spectrum analysis results. Compare detected interferers.
(b) For DFS: check if the building is near an airport or weather radar station. Frequent DFS events are expected in these locations.
(c) Verify by generating known interference: turn on a microwave oven near a 2.4GHz AP and confirm the event.

### Step 4 — Operationalize
Dashboard ("Wireless — RF Interference"):
- Row 1 — Single-value tiles: "Interference events (24h)", "DFS channel changes", "Affected APs", "RF jammers detected".
- Row 2 — Interference table: type, band, building, events, affected APs, impact.
- Row 3 — DFS event frequency per AP.

Alerting:
- Critical (RF jammer detected): security incident — locate and remove immediately.
- High (> 5 DFS events on same AP in 24h): persistent radar interference — consider disabling DFS channels for that AP.
- Warning (sustained interference > 20% duty cycle): investigate and mitigate.

### Step 5 — Troubleshooting

- **Constant microwave interference on 2.4GHz** — Common in break rooms and kitchens. Solutions: move APs away from kitchens, switch clients to 5GHz band steering, or use channel 1 or 11 (less overlap with 2.45GHz microwave frequency).

- **Frequent DFS events forcing channel changes** — The AP is detecting radar on 5GHz DFS channels. Solutions: disable DFS channels in the AP configuration (use only UNII-1 channels 36-48 and UNII-3 channels 149-165), or accept the channel changes if coverage isn't impacted.

- **No interference data available** — Spectrum analysis requires: Cisco CleanAir (specific AP models with dedicated spectrum radios), Meraki auto-RF, or Aruba ARM. Not all AP models support interference classification.

## SPL

```spl
index=network sourcetype="cisco:wlc" ("radar" OR "DFS" OR "interference" OR "channel change")
| stats count by ap_name, channel | sort -count
```

## Visualization

Table (AP, event type, count), Timeline, Bar chart.

## Known False Positives

RF noise and channel changes can spike when neighbors deploy new gear, microwaves run, or the controller runs automatic channel updates; weather and outdoor clients can also move the numbers.

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
