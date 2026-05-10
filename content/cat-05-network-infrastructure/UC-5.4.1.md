<!-- AUTO-GENERATED from UC-5.4.1.json — DO NOT EDIT -->

---
id: "5.4.1"
title: "AP Offline Detection"
criticality: "critical"
splunkPillar: "Observability"
---

# UC-5.4.1 · AP Offline Detection

> **Criticality:** Critical &middot; **Difficulty:** Intermediate &middot; **Pillar:** Observability &middot; **Type:** Availability

*We watch ap offline detection so we notice problems while they are still small, and we can fix them before Wi-Fi users get dropped calls or dead spots.*

---

## Description

Offline APs create coverage dead zones. Users lose connectivity in affected areas.

## Value

Network operations teams detect offline wireless access points with physical location context, correlate multi-AP outages to identify upstream infrastructure failures (PoE switch, power), and assess wireless coverage impact per building and floor.

## Implementation

1. In Splunk_TA_cisco_meraki enable both Devices Availabilities and Devices Availabilities Change History inputs (TA v3.3+). 2. Filter to productType=wireless for MR APs. The Availabilities input gives current state; the Change History input lists every transition (online -> offline, etc.). 3. For paging-grade alerting, configure a Meraki Dashboard alert profile on 'device went offline for X minutes' and ingest via the Webhook Logs (HEC) input — webhook latency is near-real-time vs the daily Availabilities polling cadence.

## Detailed Implementation

### Prerequisites
- Install and configure the required add-on or app: `Cisco Meraki Add-on for Splunk` (Splunkbase 5580).
- Ensure the following data sources are available: Splunk_TA_cisco_meraki (Splunkbase #5580): Devices Availabilities input (sourcetype=meraki:devicesavailabilities, daily, TA v3.3+) and Devices Availabilities Change History input (sourcetype=meraki:devicesavailabilitieschangehistory, hourly). NOTE: Meraki MR access points do NOT emit 'device offline' syslog events. AP offline detection is performed by the Meraki Dashboard cloud (controller) and exposed through the polled Devices Availabilities API endpoint..
- For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

### Step 1 — Configure data collection
1. In Splunk_TA_cisco_meraki enable both Devices Availabilities and Devices Availabilities Change History inputs (TA v3.3+). 2. Filter to productType=wireless for MR APs. The Availabilities input gives current state; the Change History input lists every transition (online -> offline, etc.). 3. For paging-grade alerting, configure a Meraki Dashboard alert profile on 'device went offline for X minutes' and ingest via the Webhook Logs (HEC) input — webhook latency is near-real-time vs the daily Ava…

### Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=meraki sourcetype="meraki:devicesavailabilities" productType="wireless" earliest=-1h
| stats latest(status) as ap_status,
        latest(_time) as last_status_time,
        latest(name) as ap_name,
        latest(network.name) as network_name
         by serial, mac
| where ap_status != "online"
| eval offline_minutes = round((now() - last_status_time)/60, 0)
| sort - offline_minutes
| append [
    search index=meraki sourcetype="meraki:devicesavailabilitieschangehistory"
        productType="wireless" status="offline" earliest=-24h
    | stats earliest(_time) as offline_since,
            values(previousStatus) as previous_status
             by serial, networkName
  ]
```

#### Understanding this SPL

**AP Offline Detection** — Network operations teams detect offline wireless access points with physical location context, correlate multi-AP outages to identify upstream infrastructure failures (PoE switch, power), and assess wireless coverage impact per building and floor.

Documented **Data sources**: Splunk_TA_cisco_meraki (Splunkbase #5580): Devices Availabilities input (sourcetype=meraki:devicesavailabilities, daily, TA v3.3+) and Devices Availabilities Change History input (sourcetype=meraki:devicesavailabilitieschangehistory, hourly). NOTE: Meraki MR access points do NOT emit 'device offline' syslog events. AP offline detection is performed by the Meraki Dashboard cloud (controller) and exposed through the polled Devices Availabilities API endpoint. **App/TA** (typical add-on context): `Cisco Meraki Add-on for Splunk` (Splunkbase 5580). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: meraki; **sourcetype**: meraki:devicesavailabilities. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

- Scopes the data: index=meraki, sourcetype="meraki:devicesavailabilities", time bounds. Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
- `stats` rolls up events into metrics; results are split **by serial, mac** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
- Filters the current rows with `where ap_status != "online"` — typically the threshold or rule expression for this monitoring goal.
- `eval` defines or adjusts **offline_minutes** — often to normalize units, derive a ratio, or prepare for thresholds.
- Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.
- Appends rows from a subsearch with `append`.


### Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

### Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Map (AP locations with status), Table, Status grid, Single value (APs offline).

## SPL

```spl
index=meraki sourcetype="meraki:devicesavailabilities" productType="wireless" earliest=-1h
| stats latest(status) as ap_status,
        latest(_time) as last_status_time,
        latest(name) as ap_name,
        latest(network.name) as network_name
         by serial, mac
| where ap_status != "online"
| eval offline_minutes = round((now() - last_status_time)/60, 0)
| sort - offline_minutes
| append [
    search index=meraki sourcetype="meraki:devicesavailabilitieschangehistory"
        productType="wireless" status="offline" earliest=-24h
    | stats earliest(_time) as offline_since,
            values(previousStatus) as previous_status
             by serial, networkName
  ]
```

## Visualization

Map (AP locations with status), Table, Status grid, Single value (APs offline).

## Known False Positives

Access points may go offline during scheduled firmware updates, PoE switch reboots, cabling work, or RF site surveys, which can look like an outage without a real coverage problem.

## References

- [Splunkbase app 5580](https://splunkbase.splunk.com/app/5580)
