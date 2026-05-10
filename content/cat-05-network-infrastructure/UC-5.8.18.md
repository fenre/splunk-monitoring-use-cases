<!-- AUTO-GENERATED from UC-5.8.18.json — DO NOT EDIT -->

---
id: "5.8.18"
title: "Device Online/Offline Status Monitoring (Meraki)"
criticality: "critical"
splunkPillar: "Observability"
---

# UC-5.8.18 · Device Online/Offline Status Monitoring (Meraki)

> **Criticality:** Critical &middot; **Difficulty:** Intermediate &middot; **Pillar:** Observability &middot; **Type:** Availability

*We help you know quickly when a Meraki box drops offline, before users open tickets about dead Wi‑Fi or VPN.*

---

## Description

Tracks device connectivity status to quickly identify and respond to device failures.

## Value

Network operations teams monitor Meraki device online/offline status with impact-aware urgency classification, distinguishing gateway outages (site down) from AP outages (coverage gaps) and tracking offline duration for dispatch decisions.

## Implementation

1. Enable Devices Availabilities and Devices Availabilities Change History inputs (both in TA v3.3+). 2. The Availabilities input gives current state; the Change History input lists every status transition (online -> offline -> online ...) with previousStatus, status, and ts. 3. Joining the two lets you report on each currently-down device along with how long it has been down. 4. For paging-grade alerting, configure a Meraki Dashboard alert profile on 'device offline for X minutes' and ingest via the Webhook Logs (HEC) input.

## Detailed Implementation

### Prerequisites
- Install and configure the required add-on or app: `Cisco Meraki Add-on for Splunk` (Splunkbase 5580).
- Ensure the following data sources are available: Splunk_TA_cisco_meraki (Splunkbase #5580): Devices Availabilities input (sourcetype=meraki:devicesavailabilities, daily, TA v3.3+) and Devices Availabilities Change History input (sourcetype=meraki:devicesavailabilitieschangehistory, hourly) for transition timestamps..
- For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

### Step 1 — Configure data collection
1. Enable Devices Availabilities and Devices Availabilities Change History inputs (both in TA v3.3+). 2. The Availabilities input gives current state; the Change History input lists every status transition (online -> offline -> online ...) with previousStatus, status, and ts. 3. Joining the two lets you report on each currently-down device along with how long it has been down. 4. For paging-grade alerting, configure a Meraki Dashboard alert profile on 'device offline for X minutes' and ingest vi…

### Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=meraki sourcetype="meraki:devicesavailabilities" earliest=-1h
| stats latest(status) as device_status,
        latest(_time) as last_status_check,
        latest(productType) as product_type
         by serial, name, network.id, network.name
| where device_status != "online"
| join type=left serial [
    search index=meraki sourcetype="meraki:devicesavailabilitieschangehistory" earliest=-24h
    | stats latest(_time) as last_change_time,
            latest(status) as new_status,
            latest(previousStatus) as prev_status
             by serial
  ]
| eval offline_minutes = round((now() - coalesce(last_change_time, last_status_check))/60, 0)
| sort - offline_minutes
```

#### Understanding this SPL

**Device Online/Offline Status Monitoring (Meraki)** — Network operations teams monitor Meraki device online/offline status with impact-aware urgency classification, distinguishing gateway outages (site down) from AP outages (coverage gaps) and tracking offline duration for dispatch decisions.

Documented **Data sources**: Splunk_TA_cisco_meraki (Splunkbase #5580): Devices Availabilities input (sourcetype=meraki:devicesavailabilities, daily, TA v3.3+) and Devices Availabilities Change History input (sourcetype=meraki:devicesavailabilitieschangehistory, hourly) for transition timestamps. **App/TA** (typical add-on context): `Cisco Meraki Add-on for Splunk` (Splunkbase 5580). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: meraki; **sourcetype**: meraki:devicesavailabilities. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

- Scopes the data: index=meraki, sourcetype="meraki:devicesavailabilities", time bounds. Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
- `stats` rolls up events into metrics; results are split **by serial, name, network.id, network.name** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
- Filters the current rows with `where device_status != "online"` — typically the threshold or rule expression for this monitoring goal.
- Joins to a subsearch with `join` — set `max=` to match cardinality and avoid silent truncation.
- `eval` defines or adjusts **offline_minutes** — often to normalize units, derive a ratio, or prepare for thresholds.
- Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.


### Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

### Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Device status table; offline count gauge; status change timeline.

## SPL

```spl
index=meraki sourcetype="meraki:devicesavailabilities" earliest=-1h
| stats latest(status) as device_status,
        latest(_time) as last_status_check,
        latest(productType) as product_type
         by serial, name, network.id, network.name
| where device_status != "online"
| join type=left serial [
    search index=meraki sourcetype="meraki:devicesavailabilitieschangehistory" earliest=-24h
    | stats latest(_time) as last_change_time,
            latest(status) as new_status,
            latest(previousStatus) as prev_status
             by serial
  ]
| eval offline_minutes = round((now() - coalesce(last_change_time, last_status_check))/60, 0)
| sort - offline_minutes
```

## Visualization

Device status table; offline count gauge; status change timeline.

## Known False Positives

Brief cellular or power blips to appliances can flip offline/online; use duration filters and local ping where possible before heavy paging.

## References

- [Splunkbase app 5580](https://splunkbase.splunk.com/app/5580)
