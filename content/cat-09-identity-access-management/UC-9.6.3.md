<!-- AUTO-GENERATED from UC-9.6.3.json — DO NOT EDIT -->

---
id: "9.6.3"
title: "Geofencing Alerts and Location-Based Policy Triggers"
criticality: "medium"
splunkPillar: "Security"
---

# UC-9.6.3 · Geofencing Alerts and Location-Based Policy Triggers

> **Criticality:** Medium &middot; **Difficulty:** Beginner &middot; **Pillar:** Security &middot; **Type:** Security, Performance

*We use identity and sign-in data in Splunk so we can notice unusual logins, access changes, and privileged use while it still matters — Geofencing Alerts and Location-Based Policy Triggers*

---

## Description

Uses geofencing to detect when devices leave secure zones and trigger location-based policies.

## Value

Uses geofencing to detect when devices leave secure zones and trigger location-based policies.

## Implementation

Meraki SM detects jailbroken iOS and rooted Android devices and posts alerts via webhook. Configure either `cisco_meraki_webhook` (HEC) or `cisco_meraki_webhook_logs` (polled) input and subscribe to SM security alerts in the Dashboard. Treat any detection as a high-severity finding — the device should be quarantined and re-imaged before being allowed back on corporate Wi-Fi.

## Detailed Implementation

### Prerequisites
- Install and configure the required add-on or app: `Cisco Meraki Add-on for Splunk` (Splunkbase 5580).
- Ensure the following data sources are available: `index=meraki sourcetype=meraki:webhook` (HEC) or `meraki:webhooklogs:api` (polled) in `Splunk_TA_cisco_meraki` (Splunkbase 5580). Subscribe to SM jailbreak / root / security-state alerts..
- For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

### Step 1 — Configure data collection
Meraki SM detects jailbroken iOS and rooted Android devices and posts alerts via webhook. Configure either `cisco_meraki_webhook` (HEC) or `cisco_meraki_webhook_logs` (polled) input and subscribe to SM security alerts in the Dashboard. Treat any detection as a high-severity finding — the device should be quarantined and re-imaged before being allowed back on corporate Wi-Fi.

### Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=meraki sourcetype IN ("meraki:webhook","meraki:webhooklogs:api") (alertTypeId="sm_jailbreak" OR alertTypeId="sm_rooted" OR like(alertType, "%jailbreak%") OR like(alertType, "%rooted%") OR like(alertType, "%security%"))
| spath
| eval device_name=coalesce('alertData.deviceName', 'data.deviceName', deviceName)
| eval os_type=coalesce('alertData.osName', 'data.osName', osName)
| eval issue=case(like(alertType, "%jailbreak%"), "jailbroken", like(alertType, "%root%"), "rooted", true(), alertType)
| stats count as detections, latest(_time) as last_detection by device_name, os_type, issue, networkName
| eval last_detection_human=strftime(last_detection, "%Y-%m-%d %H:%M:%S")
| sort - last_detection
```

#### Understanding this SPL

**Geofencing Alerts and Location-Based Policy Triggers** — Uses geofencing to detect when devices leave secure zones and trigger location-based policies.

Documented **Data sources**: `index=meraki sourcetype=meraki:webhook` (HEC) or `meraki:webhooklogs:api` (polled) in `Splunk_TA_cisco_meraki` (Splunkbase 5580). Subscribe to SM jailbreak / root / security-state alerts. **App/TA** (typical add-on context): `Cisco Meraki Add-on for Splunk` (Splunkbase 5580). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: meraki.

**Pipeline walkthrough**

- Scopes the data: index=meraki. Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
- Extracts structured paths (JSON/XML) with `spath`.
- `eval` defines or adjusts **device_name** — often to normalize units, derive a ratio, or prepare for thresholds.
- `eval` defines or adjusts **os_type** — often to normalize units, derive a ratio, or prepare for thresholds.
- `eval` defines or adjusts **issue** — often to normalize units, derive a ratio, or prepare for thresholds.
- `stats` rolls up events into metrics; results are split **by device_name, os_type, issue, networkName** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
- `eval` defines or adjusts **last_detection_human** — often to normalize units, derive a ratio, or prepare for thresholds.
- Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.


### Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

### Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Geofence event timeline; zone heat map; affected device list.

## SPL

```spl
index=meraki sourcetype IN ("meraki:webhook","meraki:webhooklogs:api") (alertTypeId="sm_jailbreak" OR alertTypeId="sm_rooted" OR like(alertType, "%jailbreak%") OR like(alertType, "%rooted%") OR like(alertType, "%security%"))
| spath
| eval device_name=coalesce('alertData.deviceName', 'data.deviceName', deviceName)
| eval os_type=coalesce('alertData.osName', 'data.osName', osName)
| eval issue=case(like(alertType, "%jailbreak%"), "jailbroken", like(alertType, "%root%"), "rooted", true(), alertType)
| stats count as detections, latest(_time) as last_detection by device_name, os_type, issue, networkName
| eval last_detection_human=strftime(last_detection, "%Y-%m-%d %H:%M:%S")
| sort - last_detection
```

## Visualization

Geofence event timeline; zone heat map; affected device list.

## Known False Positives

Planned policy rollouts, pilot tenants, and emergency relaxations for incidents; require change tickets for production changes.

## References

- [Splunkbase app 5580](https://splunkbase.splunk.com/app/5580)
