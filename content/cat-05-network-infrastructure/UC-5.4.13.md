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

1. Enable the Webhook Logs (HEC) input in Splunk_TA_cisco_meraki (TA v3.2+) and let it provision the Meraki webhook receiver. 2. In Meraki Dashboard enable the 'client connection changed' alert profile. 3. The webhook payload includes alertData.rssi (dBm). 4. For end-to-end client experience graphs, also enable the Wireless Packet Loss by Device input (meraki:wirelessdevicespacketlossbydevice) which exposes upstream/downstream packet loss percentages per AP.

## Detailed Implementation

### Prerequisites
- Install and configure the required add-on or app: `Cisco Meraki Add-on for Splunk` (Splunkbase 5580).
- Ensure the following data sources are available: Splunk_TA_cisco_meraki (Splunkbase #5580): Webhook receiver (sourcetype=meraki:webhook) with the Meraki Dashboard alert profile 'client connection changed' enabled. The polled Dashboard API does NOT expose per-client RSSI; webhook is the only path..
- For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

### Step 1 — Configure data collection
1. Enable the Webhook Logs (HEC) input in Splunk_TA_cisco_meraki (TA v3.2+) and let it provision the Meraki webhook receiver. 2. In Meraki Dashboard enable the 'client connection changed' alert profile. 3. The webhook payload includes alertData.rssi (dBm). 4. For end-to-end client experience graphs, also enable the Wireless Packet Loss by Device input (meraki:wirelessdevicespacketlossbydevice) which exposes upstream/downstream packet loss percentages per AP.

### Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=meraki sourcetype IN ("meraki:webhook","meraki:webhooklogs:api")
    alertType="client_connectivity"
    earliest=-24h
| spath
| eval rssi_dbm = coalesce('alertData.rssi', 'alertData.signal.rssi')
| where isnotnull(rssi_dbm) AND isnum(rssi_dbm)
| eval rssi_level = case(
    rssi_dbm>=-60, "Excellent",
    rssi_dbm>=-70, "Good",
    rssi_dbm>=-80, "Fair",
    1=1, "Poor")
| stats avg(rssi_dbm) as avg_rssi, min(rssi_dbm) as min_rssi, count
         by deviceSerial, deviceName, rssi_level
| sort avg_rssi
```

#### Understanding this SPL

**RSSI/Signal Strength Degradation Detection (Meraki MR)** — Network operations teams monitor Meraki MR client RSSI values per AP and location to detect wireless coverage gaps, identify areas with weak signal causing poor client performance, and prioritize RF optimization.

Documented **Data sources**: Splunk_TA_cisco_meraki (Splunkbase #5580): Webhook receiver (sourcetype=meraki:webhook) with the Meraki Dashboard alert profile 'client connection changed' enabled. The polled Dashboard API does NOT expose per-client RSSI; webhook is the only path. **App/TA** (typical add-on context): `Cisco Meraki Add-on for Splunk` (Splunkbase 5580). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: meraki.

**Pipeline walkthrough**

- Scopes the data: index=meraki, time bounds. Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
- Extracts structured paths (JSON/XML) with `spath`.
- `eval` defines or adjusts **rssi_dbm** — often to normalize units, derive a ratio, or prepare for thresholds.
- Filters the current rows with `where isnotnull(rssi_dbm) AND isnum(rssi_dbm)` — typically the threshold or rule expression for this monitoring goal.
- `eval` defines or adjusts **rssi_level** — often to normalize units, derive a ratio, or prepare for thresholds.
- `stats` rolls up events into metrics; results are split **by deviceSerial, deviceName, rssi_level** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
- Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.


### Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

### Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Heatmap of RSSI by AP location; histogram of signal strength distribution; gauge charts for coverage quality by SSID.

## SPL

```spl
index=meraki sourcetype IN ("meraki:webhook","meraki:webhooklogs:api")
    alertType="client_connectivity"
    earliest=-24h
| spath
| eval rssi_dbm = coalesce('alertData.rssi', 'alertData.signal.rssi')
| where isnotnull(rssi_dbm) AND isnum(rssi_dbm)
| eval rssi_level = case(
    rssi_dbm>=-60, "Excellent",
    rssi_dbm>=-70, "Good",
    rssi_dbm>=-80, "Fair",
    1=1, "Poor")
| stats avg(rssi_dbm) as avg_rssi, min(rssi_dbm) as min_rssi, count
         by deviceSerial, deviceName, rssi_level
| sort avg_rssi
```

## Visualization

Heatmap of RSSI by AP location; histogram of signal strength distribution; gauge charts for coverage quality by SSID.

## Known False Positives

RF noise and channel changes can spike when neighbors deploy new gear, microwaves run, or the controller runs automatic channel updates; weather and outdoor clients can also move the numbers.

## References

- [Splunkbase app 5580](https://splunkbase.splunk.com/app/5580)
