<!-- AUTO-GENERATED from UC-5.1.45.json — DO NOT EDIT -->

---
id: "5.1.45"
title: "Switch CPU and Memory Utilization (Meraki MS)"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-5.1.45 · Switch CPU and Memory Utilization (Meraki MS)

> **Criticality:** Medium &middot; **Difficulty:** Beginner &middot; **Pillar:** Observability &middot; **Type:** Fault

*We help you know early when something looks wrong with switch cpu and memory utilization so the team can act before it grows into a bigger outage.*

---

## Description

Monitors switch hardware resources to prevent performance degradation or device failure.

## Value

Operations teams monitor Meraki MS switch CPU and memory utilization, detecting resource exhaustion that affects management plane responsiveness and control plane processing.

## Implementation

1. Enable the Assurance Alerts input in Splunk_TA_cisco_meraki. The TA polls GET /organizations/{orgId}/assurance/alerts hourly and emits one event per alert. The relevant fields are: `deviceType` (model code: MR/MS/MX/MV/MT/MG), `scope.devices{}.serial`, `scope.devices{}.name`, `network.name`, `network.id`, `categoryType`, `title`, `severity`, `dismissedAt`. 2. Filter to `deviceType="MS"` for switch-specific issues — the API uses uppercase model codes, NOT the lowercase product type. Performance issues (high CPU, memory pressure, queue drops) surface as device alerts with categoryType=device or =connectivity. 3. `dismissedAt` carries the literal string `"null"` while the alert is open, so use `search dismissed_at="null"` instead of `where isnull(dismissed_at)`. 4. For continuous CPU/memory graphs, supplement with SNMP polling against the switch's management IP using OIDs from CISCO-PROCESS-MIB (cpmCPUTotal5minRev) and CISCO-MEMORY-POOL-MIB — the Meraki TA does NOT carry these counters.

## Detailed Implementation

### Prerequisites
- Install and configure the required add-on or app: `Cisco Meraki Add-on for Splunk` (Splunkbase 5580).
- Ensure the following data sources are available: Splunk_TA_cisco_meraki (Splunkbase #5580): Assurance Alerts input (sourcetype=meraki:assurancealerts, hourly, OAuth scope dashboard:general:telemetry:read). The TA preserves Meraki's nested JSON paths: `deviceType` is the model-family code (`MS` for switches, NOT `switch`), device identity is `scope.devices{}.serial` / `scope.devices{}.name`, network identity is `network.name` / `network.id`, and `dismissedAt` carries the literal string `"null"` (not a Splunk NULL) when an alert is still open. Note: the Meraki Dashboard API does NOT expose per-switch CPU or memory counters via this TA. If you need raw CPU/memory telemetry, deploy SNMP polling (Splunk SNMP modular input) against the switch directly using IF-MIB / CISCO-PROCESS-MIB OIDs..
- For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

### Step 1 — Configure data collection
1. Enable the Assurance Alerts input in Splunk_TA_cisco_meraki. The TA polls GET /organizations/{orgId}/assurance/alerts hourly and emits one event per alert. The relevant fields are: `deviceType` (model code: MR/MS/MX/MV/MT/MG), `scope.devices{}.serial`, `scope.devices{}.name`, `network.name`, `network.id`, `categoryType`, `title`, `severity`, `dismissedAt`. 2. Filter to `deviceType="MS"` for switch-specific issues — the API uses uppercase model codes, NOT the lowercase product type. Performanc…

### Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=meraki sourcetype="meraki:assurancealerts"
    deviceType="MS"
    (categoryType="device" OR categoryType="connectivity")
    earliest=-24h
| rename scope.devices{}.serial as device_serial,
         scope.devices{}.name as device_name,
         network.name as network_name
| stats count as alert_count,
        values(title) as alert_titles,
        latest(severity) as severity,
        latest(dismissedAt) as dismissed_at
         by device_serial, device_name, network_name
| search dismissed_at="null"
| where alert_count > 0
| sort - alert_count
```

#### Understanding this SPL

**Switch CPU and Memory Utilization (Meraki MS)** — Operations teams monitor Meraki MS switch CPU and memory utilization, detecting resource exhaustion that affects management plane responsiveness and control plane processing.

Documented **Data sources**: Splunk_TA_cisco_meraki (Splunkbase #5580): Assurance Alerts input (sourcetype=meraki:assurancealerts, hourly, OAuth scope dashboard:general:telemetry:read). The TA preserves Meraki's nested JSON paths: `deviceType` is the model-family code (`MS` for switches, NOT `switch`), device identity is `scope.devices{}.serial` / `scope.devices{}.name`, network identity is `network.name` / `network.id`, and `dismissedAt` carries the literal string `"null"` (not a Splunk NULL) when an alert is still open. Note: the Meraki Dashboard API does NOT expose per-switch CPU or memory counters via this TA. If you need raw CPU/memory telemetry, deploy SNMP polling (Splunk SNMP modular input) against the switch directly using IF-MIB / CISCO-PROCESS-MIB OIDs. **App/TA** (typical add-on context): `Cisco Meraki Add-on for Splunk` (Splunkbase 5580). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: meraki; **sourcetype**: meraki:assurancealerts. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

- Scopes the data: index=meraki, sourcetype="meraki:assurancealerts", time bounds. Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
- Renames fields with `rename` for clarity or joins.
- `stats` rolls up events into metrics; results are split **by device_serial, device_name, network_name** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
- Applies an explicit `search` filter to narrow the current result set.
- Filters the current rows with `where alert_count > 0` — typically the threshold or rule expression for this monitoring goal.
- Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.


### Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

### Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Gauge charts for CPU/memory; time-series trends; capacity planning dashboard.

## SPL

```spl
index=meraki sourcetype="meraki:assurancealerts"
    deviceType="MS"
    (categoryType="device" OR categoryType="connectivity")
    earliest=-24h
| rename scope.devices{}.serial as device_serial,
         scope.devices{}.name as device_name,
         network.name as network_name
| stats count as alert_count,
        values(title) as alert_titles,
        latest(severity) as severity,
        latest(dismissedAt) as dismissed_at
         by device_serial, device_name, network_name
| search dismissed_at="null"
| where alert_count > 0
| sort - alert_count
```

## Visualization

Gauge charts for CPU/memory; time-series trends; capacity planning dashboard.

## Known False Positives

Short CPU or memory spikes during routing convergence, code upgrade, or SNMP walks are common. Baseline by platform role and compare to a maintenance calendar.

## References

- [Splunkbase app 5580](https://splunkbase.splunk.com/app/5580)
