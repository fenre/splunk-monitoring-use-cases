<!-- AUTO-GENERATED from UC-5.4.16.json — DO NOT EDIT -->

---
id: "5.4.16"
title: "WiFi Channel Utilization and Interference Detection (Meraki MR)"
criticality: "high"
splunkPillar: "Observability"
---

# UC-5.4.16 · WiFi Channel Utilization and Interference Detection (Meraki MR)

> **Criticality:** High &middot; **Difficulty:** Advanced &middot; **Pillar:** Observability &middot; **Type:** Performance

*We watch wifi channel utilization and interference detection (meraki mr) so we notice problems while they are still small, and we can fix them before Wi-Fi users get dropped calls or dead spots.*

---

## Description

Identifies channel congestion and interference sources to optimize channel assignments and reduce co-channel interference.

## Value

Wireless operations teams track Meraki MR DHCP transaction completion rates per AP and SSID to detect IP addressing failures that leave clients connected but without network access.

## Implementation

1. Configure the HEC token and Webhook Logs (HEC) input in Splunk_TA_cisco_meraki. 2. In Meraki Dashboard enable the relevant wireless alert profiles. 3. Each event carries alertData.channel, alertData.band, and deviceSerial. 4. For continuous real-time RF spectrum analysis, supplement with a dedicated WiFi analyzer (Ekahau, NetSpot, AirMagnet) and forward its output to Splunk.

## Detailed Implementation

### Prerequisites
- Install and configure the required add-on or app: `Cisco Meraki Add-on for Splunk` (Splunkbase 5580).
- Ensure the following data sources are available: Splunk_TA_cisco_meraki (Splunkbase #5580): Webhook receiver (sourcetype=meraki:webhook) with alert profiles for 'high channel utilization', 'rogue AP detected', and 'radar detected (DFS)'. The polled Dashboard API does NOT return real-time per-channel utilization counters..
- For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

### Step 1 — Configure data collection
1. Configure the HEC token and Webhook Logs (HEC) input in Splunk_TA_cisco_meraki. 2. In Meraki Dashboard enable the relevant wireless alert profiles. 3. Each event carries alertData.channel, alertData.band, and deviceSerial. 4. For continuous real-time RF spectrum analysis, supplement with a dedicated WiFi analyzer (Ekahau, NetSpot, AirMagnet) and forward its output to Splunk.

### Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=meraki sourcetype IN ("meraki:webhook","meraki:webhooklogs:api")
    (alertType="utilization" OR alertTypeId="ap_radar_detected"
     OR alertType="rogue_ap_detected" OR alertType="rf_spectrum")
    earliest=-24h
| spath
| eval channel = coalesce('alertData.channel', 'alertData.rf.channel')
| eval band = coalesce('alertData.band', 'alertData.rf.band')
| stats count as event_count, values(channel) as channels
         by deviceSerial, deviceName, band, networkName
| sort - event_count
```

#### Understanding this SPL

**WiFi Channel Utilization and Interference Detection (Meraki MR)** — Wireless operations teams track Meraki MR DHCP transaction completion rates per AP and SSID to detect IP addressing failures that leave clients connected but without network access.

Documented **Data sources**: Splunk_TA_cisco_meraki (Splunkbase #5580): Webhook receiver (sourcetype=meraki:webhook) with alert profiles for 'high channel utilization', 'rogue AP detected', and 'radar detected (DFS)'. The polled Dashboard API does NOT return real-time per-channel utilization counters. **App/TA** (typical add-on context): `Cisco Meraki Add-on for Splunk` (Splunkbase 5580). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: meraki.

**Pipeline walkthrough**

- Scopes the data: index=meraki, time bounds. Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
- Extracts structured paths (JSON/XML) with `spath`.
- `eval` defines or adjusts **channel** — often to normalize units, derive a ratio, or prepare for thresholds.
- `eval` defines or adjusts **band** — often to normalize units, derive a ratio, or prepare for thresholds.
- `stats` rolls up events into metrics; results are split **by deviceSerial, deviceName, band, networkName** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
- Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.


### Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

### Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Stacked bar chart of channel utilization by band; channel heatmap over time; interference event timeline.

## SPL

```spl
index=meraki sourcetype IN ("meraki:webhook","meraki:webhooklogs:api")
    (alertType="utilization" OR alertTypeId="ap_radar_detected"
     OR alertType="rogue_ap_detected" OR alertType="rf_spectrum")
    earliest=-24h
| spath
| eval channel = coalesce('alertData.channel', 'alertData.rf.channel')
| eval band = coalesce('alertData.band', 'alertData.rf.band')
| stats count as event_count, values(channel) as channels
         by deviceSerial, deviceName, band, networkName
| sort - event_count
```

## Visualization

Stacked bar chart of channel utilization by band; channel heatmap over time; interference event timeline.

## Known False Positives

RF noise and channel changes can spike when neighbors deploy new gear, microwaves run, or the controller runs automatic channel updates; weather and outdoor clients can also move the numbers.

## References

- [Splunkbase app 5580](https://splunkbase.splunk.com/app/5580)
