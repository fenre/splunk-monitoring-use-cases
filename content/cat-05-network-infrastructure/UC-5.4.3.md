<!-- AUTO-GENERATED from UC-5.4.3.json — DO NOT EDIT -->

---
id: "5.4.3"
title: "Channel Utilization"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-5.4.3 · Channel Utilization

> **Criticality:** Medium &middot; **Difficulty:** Intermediate &middot; **Pillar:** Observability &middot; **Type:** Performance, Capacity

*We watch channel utilization so we notice problems while they are still small, and we can fix them before Wi-Fi users get dropped calls or dead spots.*

---

## Description

High channel utilization degrades wireless performance. Identifies congested APs needing channel changes or additional coverage.

## Value

Network operations teams monitor wireless channel utilization and interference levels per AP, band, and location to identify capacity bottlenecks, RF interference sources, and areas requiring additional access points or channel optimization.

## Implementation

1. In Splunk_TA_cisco_meraki configure the HEC token and the Webhook Logs (HEC) input. The TA will provision the receiver in Meraki Dashboard automatically (TA v3.2+). 2. In Meraki Dashboard go to Network-wide -> Alerts and enable the 'high channel utilization' and 'rogue access point detected' alert types pointing at the TA's webhook receiver. 3. The webhook payload arrives as JSON with alertType, alertData.*, deviceSerial, deviceName, networkName. 4. For continuous channel-utilization graphs you must scrape the Dashboard UI (RF Spectrum) or use a 3rd-party WiFi analyzer.

## Detailed Implementation

### Prerequisites
- Install and configure the required add-on or app: Meraki API, WLC SNMP.
- Ensure the following data sources are available: Splunk_TA_cisco_meraki (Splunkbase #5580): Webhook receiver (sourcetype=meraki:webhook) configured via TA v3.2+ with Meraki alert profile entries for 'high channel utilization', 'radar detected (DFS)', and 'rogue AP detected'. Per-AP per-channel utilization is NOT exposed by the polled Dashboard API..
- For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

### Step 1 — Configure data collection
1. In Splunk_TA_cisco_meraki configure the HEC token and the Webhook Logs (HEC) input. The TA will provision the receiver in Meraki Dashboard automatically (TA v3.2+). 2. In Meraki Dashboard go to Network-wide -> Alerts and enable the 'high channel utilization' and 'rogue access point detected' alert types pointing at the TA's webhook receiver. 3. The webhook payload arrives as JSON with alertType, alertData.*, deviceSerial, deviceName, networkName. 4. For continuous channel-utilization graphs y…

### Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=meraki sourcetype IN ("meraki:webhook","meraki:webhooklogs:api")
    (alertType="utilization" OR alertType="rf_spectrum" OR alertTypeId="ap_radar_detected")
    earliest=-24h
| spath
| stats count as event_count,
        values(alertData.channel) as channels,
        values(alertData.band) as bands
         by deviceSerial, deviceName, networkName
| where event_count > 0
| sort - event_count
```

#### Understanding this SPL

**Channel Utilization** — Network operations teams monitor wireless channel utilization and interference levels per AP, band, and location to identify capacity bottlenecks, RF interference sources, and areas requiring additional access points or channel optimization.

Documented **Data sources**: Splunk_TA_cisco_meraki (Splunkbase #5580): Webhook receiver (sourcetype=meraki:webhook) configured via TA v3.2+ with Meraki alert profile entries for 'high channel utilization', 'radar detected (DFS)', and 'rogue AP detected'. Per-AP per-channel utilization is NOT exposed by the polled Dashboard API. **App/TA** (typical add-on context): Meraki API, WLC SNMP. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: meraki.

**Pipeline walkthrough**

- Scopes the data: index=meraki, time bounds. Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
- Extracts structured paths (JSON/XML) with `spath`.
- `stats` rolls up events into metrics; results are split **by deviceSerial, deviceName, networkName** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
- Filters the current rows with `where event_count > 0` — typically the threshold or rule expression for this monitoring goal.
- Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.


### Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

### Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Heatmap (APs by utilization), Table, Line chart (trending).

## SPL

```spl
index=meraki sourcetype IN ("meraki:webhook","meraki:webhooklogs:api")
    (alertType="utilization" OR alertType="rf_spectrum" OR alertTypeId="ap_radar_detected")
    earliest=-24h
| spath
| stats count as event_count,
        values(alertData.channel) as channels,
        values(alertData.band) as bands
         by deviceSerial, deviceName, networkName
| where event_count > 0
| sort - event_count
```

## Visualization

Heatmap (APs by utilization), Table, Line chart (trending).

## Known False Positives

RF noise and channel changes can spike when neighbors deploy new gear, microwaves run, or the controller runs automatic channel updates; weather and outdoor clients can also move the numbers.

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
