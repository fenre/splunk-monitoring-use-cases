<!-- AUTO-GENERATED from UC-5.8.2.json — DO NOT EDIT -->

---
id: "5.8.2"
title: "Meraki Organization Monitoring"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-5.8.2 · Meraki Organization Monitoring

> **Criticality:** Medium &middot; **Difficulty:** Intermediate &middot; **Pillar:** Observability &middot; **Type:** Availability

*We help you see when Meraki gear goes offline or unhealthy across sites so the team can fix it before everyone loses the network in that building.*

---

## Description

Tracks Meraki device status across all networks and organizations from a single pane.

## Value

Network operations teams maintain a unified view of Meraki device health across all organizations and networks, detecting site outages (offline MX), degraded coverage (offline APs), and alerting conditions with offline duration tracking.

## Implementation

1. Enable Devices Availabilities and Organization Networks inputs in Splunk_TA_cisco_meraki. The Availabilities input returns one event per device with status (online/offline/dormant/alerting), productType, network.{id,name}. 2. Aggregate per network for a per-site availability dashboard. 3. For multi-org consolidation, configure one Organization input per Meraki tenancy and tag events with the org name; the TA's input wizard prompts for org name when adding.

## Detailed Implementation

### Prerequisites
- Install and configure the required add-on or app: `Cisco Meraki Add-on for Splunk` (Splunkbase 5580).
- Ensure the following data sources are available: Splunk_TA_cisco_meraki (Splunkbase #5580): Devices Availabilities input (sourcetype=meraki:devicesavailabilities, daily, TA v3.3+) and Organization Networks input (sourcetype=meraki:organizationsnetworks, daily) for network metadata..
- For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

### Step 1 — Configure data collection
1. Enable Devices Availabilities and Organization Networks inputs in Splunk_TA_cisco_meraki. The Availabilities input returns one event per device with status (online/offline/dormant/alerting), productType, network.{id,name}. 2. Aggregate per network for a per-site availability dashboard. 3. For multi-org consolidation, configure one Organization input per Meraki tenancy and tag events with the org name; the TA's input wizard prompts for org name when adding.

### Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=meraki sourcetype="meraki:devicesavailabilities" earliest=-1h
| stats count as device_count,
        sum(eval(if(status="online",1,0))) as online_count,
        sum(eval(if(status="offline",1,0))) as offline_count,
        sum(eval(if(status="alerting",1,0))) as alerting_count
         by network.id, network.name
| eval pct_online = round(online_count*100/device_count, 1)
| where offline_count > 0 OR alerting_count > 0
| sort pct_online
```

#### Understanding this SPL

**Meraki Organization Monitoring** — Network operations teams maintain a unified view of Meraki device health across all organizations and networks, detecting site outages (offline MX), degraded coverage (offline APs), and alerting conditions with offline duration tracking.

Documented **Data sources**: Splunk_TA_cisco_meraki (Splunkbase #5580): Devices Availabilities input (sourcetype=meraki:devicesavailabilities, daily, TA v3.3+) and Organization Networks input (sourcetype=meraki:organizationsnetworks, daily) for network metadata. **App/TA** (typical add-on context): `Cisco Meraki Add-on for Splunk` (Splunkbase 5580). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: meraki; **sourcetype**: meraki:devicesavailabilities. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

- Scopes the data: index=meraki, sourcetype="meraki:devicesavailabilities", time bounds. Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
- `stats` rolls up events into metrics; results are split **by network.id, network.name** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
- `eval` defines or adjusts **pct_online** — often to normalize units, derive a ratio, or prepare for thresholds.
- Filters the current rows with `where offline_count > 0 OR alerting_count > 0` — typically the threshold or rule expression for this monitoring goal.
- Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.


### Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

### Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Map (device locations), Table, Status grid, Single value (offline count).

## SPL

```spl
index=meraki sourcetype="meraki:devicesavailabilities" earliest=-1h
| stats count as device_count,
        sum(eval(if(status="online",1,0))) as online_count,
        sum(eval(if(status="offline",1,0))) as offline_count,
        sum(eval(if(status="alerting",1,0))) as alerting_count
         by network.id, network.name
| eval pct_online = round(online_count*100/device_count, 1)
| where offline_count > 0 OR alerting_count > 0
| sort pct_online
```

## Visualization

Map (device locations), Table, Status grid, Single value (offline count).

## Known False Positives

Meraki maintenance windows, cellular backup failovers, and brief cloud API hiccups can look like outages; match counts to the dashboard map before paging.

## References

- [Splunkbase app 5580](https://splunkbase.splunk.com/app/5580)
