<!-- AUTO-GENERATED from UC-5.4.27.json — DO NOT EDIT -->

---
id: "5.4.27"
title: "Connection Duration and Session Quality (Meraki MR)"
criticality: "low"
splunkPillar: "Observability"
---

# UC-5.4.27 · Connection Duration and Session Quality (Meraki MR)

> **Criticality:** Low &middot; **Difficulty:** Intermediate &middot; **Pillar:** Observability &middot; **Type:** Performance

*We watch connection duration and session quality (meraki mr) so we notice problems while they are still small, and we can fix them before Wi-Fi users get dropped calls or dead spots.*

---

## Description

Analyzes typical session lengths and stability to identify problematic SSIDs or time-based issues.

## Value

Wireless security teams audit Meraki SSID configurations across all sites against corporate security policies, detecting unauthorized SSIDs, authentication downgrades, and encryption misconfigurations.

## Implementation

1. Enable the Webhook Logs (HEC) input and the Meraki Dashboard alert profile 'client connection changed'. 2. Use the SPL transaction command to pair connect and disconnect events on the same client MAC; the duration field is the session length in seconds. 3. Tune maxspan to your typical session length (24h is generous; reduce to 4h for retail/guest WLAN). 4. Persistent disconnects under 60 seconds suggest band-steering loops or sticky-client problems — investigate the involved AP.

## Detailed Implementation

### Prerequisites
- Install and configure the required add-on or app: `Cisco Meraki Add-on for Splunk` (Splunkbase 5580).
- Ensure the following data sources are available: Splunk_TA_cisco_meraki (Splunkbase #5580): Webhook receiver (sourcetype=meraki:webhook) with 'client connection changed' alerts. The TA's polled inputs do not return per-client connect/disconnect timestamps..
- For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

### Step 1 — Configure data collection
1. Enable the Webhook Logs (HEC) input and the Meraki Dashboard alert profile 'client connection changed'. 2. Use the SPL transaction command to pair connect and disconnect events on the same client MAC; the duration field is the session length in seconds. 3. Tune maxspan to your typical session length (24h is generous; reduce to 4h for retail/guest WLAN). 4. Persistent disconnects under 60 seconds suggest band-steering loops or sticky-client problems — investigate the involved AP.

### Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=meraki sourcetype IN ("meraki:webhook","meraki:webhooklogs:api")
    (alertType="client_connectivity" OR alertTypeId="client_connection_changed")
    earliest=-24h
| spath
| eval client_mac = coalesce('alertData.clientMac', 'alertData.client.mac')
| eval connect_state = 'alertData.status'
| where isnotnull(client_mac)
| transaction client_mac startswith=eval(connect_state="connected") endswith=eval(connect_state="disconnected") maxspan=24h
| eval session_minutes = round(duration/60, 1)
| stats avg(session_minutes) as avg_session_min,
        median(session_minutes) as median_session_min,
        max(session_minutes) as max_session_min,
        count as session_count
         by deviceName, networkName
```

#### Understanding this SPL

**Connection Duration and Session Quality (Meraki MR)** — Wireless security teams audit Meraki SSID configurations across all sites against corporate security policies, detecting unauthorized SSIDs, authentication downgrades, and encryption misconfigurations.

Documented **Data sources**: Splunk_TA_cisco_meraki (Splunkbase #5580): Webhook receiver (sourcetype=meraki:webhook) with 'client connection changed' alerts. The TA's polled inputs do not return per-client connect/disconnect timestamps. **App/TA** (typical add-on context): `Cisco Meraki Add-on for Splunk` (Splunkbase 5580). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: meraki.

**Pipeline walkthrough**

- Scopes the data: index=meraki, time bounds. Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
- Extracts structured paths (JSON/XML) with `spath`.
- `eval` defines or adjusts **client_mac** — often to normalize units, derive a ratio, or prepare for thresholds.
- `eval` defines or adjusts **connect_state** — often to normalize units, derive a ratio, or prepare for thresholds.
- Filters the current rows with `where isnotnull(client_mac)` — typically the threshold or rule expression for this monitoring goal.
- Groups related events into transactions — prefer `maxspan`/`maxpause`/`maxevents` for bounded memory.
- `eval` defines or adjusts **session_minutes** — often to normalize units, derive a ratio, or prepare for thresholds.
- `stats` rolls up events into metrics; results are split **by deviceName, networkName** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).


### Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

### Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Histogram of session durations; time-of-day heatmap; SSID comparison chart.

## SPL

```spl
index=meraki sourcetype IN ("meraki:webhook","meraki:webhooklogs:api")
    (alertType="client_connectivity" OR alertTypeId="client_connection_changed")
    earliest=-24h
| spath
| eval client_mac = coalesce('alertData.clientMac', 'alertData.client.mac')
| eval connect_state = 'alertData.status'
| where isnotnull(client_mac)
| transaction client_mac startswith=eval(connect_state="connected") endswith=eval(connect_state="disconnected") maxspan=24h
| eval session_minutes = round(duration/60, 1)
| stats avg(session_minutes) as avg_session_min,
        median(session_minutes) as median_session_min,
        max(session_minutes) as max_session_min,
        count as session_count
         by deviceName, networkName
```

## Visualization

Histogram of session durations; time-of-day heatmap; SSID comparison chart.

## Known False Positives

Wireless metrics move with user behavior, maintenance, and nearby RF; we tune alerts around change windows and known busy hours so normal days do not page the team.

## References

- [Splunkbase app 5580](https://splunkbase.splunk.com/app/5580)
