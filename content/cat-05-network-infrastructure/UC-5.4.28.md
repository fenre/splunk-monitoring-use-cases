<!-- AUTO-GENERATED from UC-5.4.28.json — DO NOT EDIT -->

---
id: "5.4.28"
title: "AP Uptime and Availability Monitoring (Meraki MR)"
criticality: "critical"
splunkPillar: "Observability"
---

# UC-5.4.28 · AP Uptime and Availability Monitoring (Meraki MR)

> **Criticality:** Critical &middot; **Difficulty:** Beginner &middot; **Pillar:** Observability &middot; **Type:** Availability

*We watch ap uptime and availability monitoring (meraki mr) so we notice problems while they are still small, and we can fix them before Wi-Fi users get dropped calls or dead spots.*

---

## Description

Ensures all access points are online and operational; alerts on unexpected AP outages.

## Value

Network operations teams analyze Meraki wireless application-layer traffic patterns using DPI data, comparing bandwidth consumption across SSIDs and application categories to optimize traffic shaping policies.

## Implementation

1. Enable both Devices Availabilities and Devices Availabilities Change History inputs in Splunk_TA_cisco_meraki. 2. The Availabilities input returns one event per device with status (online/offline/dormant/alerting), productType, serial, mac, network.{id,name}. 3. Filter productType=wireless for MR APs. 4. For transition history (when each AP last went offline) join against meraki:devicesavailabilitieschangehistory which carries previousStatus, status, and details on each event.

## Detailed Implementation

### Prerequisites
- Install and configure the required add-on or app: `Cisco Meraki Add-on for Splunk` (Splunkbase 5580).
- Ensure the following data sources are available: Splunk_TA_cisco_meraki (Splunkbase #5580): Devices Availabilities input (sourcetype=meraki:devicesavailabilities, daily, TA v3.3+) and Devices Availabilities Change History input (sourcetype=meraki:devicesavailabilitieschangehistory, hourly) for AP transition events..
- For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

### Step 1 — Configure data collection
1. Enable both Devices Availabilities and Devices Availabilities Change History inputs in Splunk_TA_cisco_meraki. 2. The Availabilities input returns one event per device with status (online/offline/dormant/alerting), productType, serial, mac, network.{id,name}. 3. Filter productType=wireless for MR APs. 4. For transition history (when each AP last went offline) join against meraki:devicesavailabilitieschangehistory which carries previousStatus, status, and details on each event.

### Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=meraki sourcetype="meraki:devicesavailabilities" productType="wireless" earliest=-1h
| stats latest(status) as ap_status,
        latest(_time) as last_seen
         by serial, name, network.name, network.id, mac
| where ap_status != "online"
| eval offline_minutes = round((now() - last_seen)/60, 0)
| sort - offline_minutes
```

#### Understanding this SPL

**AP Uptime and Availability Monitoring (Meraki MR)** — Network operations teams analyze Meraki wireless application-layer traffic patterns using DPI data, comparing bandwidth consumption across SSIDs and application categories to optimize traffic shaping policies.

Documented **Data sources**: Splunk_TA_cisco_meraki (Splunkbase #5580): Devices Availabilities input (sourcetype=meraki:devicesavailabilities, daily, TA v3.3+) and Devices Availabilities Change History input (sourcetype=meraki:devicesavailabilitieschangehistory, hourly) for AP transition events. **App/TA** (typical add-on context): `Cisco Meraki Add-on for Splunk` (Splunkbase 5580). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: meraki; **sourcetype**: meraki:devicesavailabilities. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

- Scopes the data: index=meraki, sourcetype="meraki:devicesavailabilities", time bounds. Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
- `stats` rolls up events into metrics; results are split **by serial, name, network.name, network.id, mac** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
- Filters the current rows with `where ap_status != "online"` — typically the threshold or rule expression for this monitoring goal.
- `eval` defines or adjusts **offline_minutes** — often to normalize units, derive a ratio, or prepare for thresholds.
- Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.


### Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

### Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Status table with last seen time; uptime percentage gauge; event alert dashboard.

## SPL

```spl
index=meraki sourcetype="meraki:devicesavailabilities" productType="wireless" earliest=-1h
| stats latest(status) as ap_status,
        latest(_time) as last_seen
         by serial, name, network.name, network.id, mac
| where ap_status != "online"
| eval offline_minutes = round((now() - last_seen)/60, 0)
| sort - offline_minutes
```

## Visualization

Status table with last seen time; uptime percentage gauge; event alert dashboard.

## Known False Positives

Access points may go offline during scheduled firmware updates, PoE switch reboots, cabling work, or RF site surveys, which can look like an outage without a real coverage problem.

## References

- [Splunkbase app 5580](https://splunkbase.splunk.com/app/5580)
