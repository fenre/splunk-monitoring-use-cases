<!-- AUTO-GENERATED from UC-5.8.17.json — DO NOT EDIT -->

---
id: "5.8.17"
title: "Network Health Score Aggregation and Executive Reporting (Meraki)"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-5.8.17 · Network Health Score Aggregation and Executive Reporting (Meraki)

> **Criticality:** Medium &middot; **Difficulty:** Intermediate &middot; **Pillar:** Observability &middot; **Type:** Availability

*We roll Meraki health into a simple view leaders can read, not just a wall of device lists.*

---

## Description

Provides high-level network health metric for executive dashboards and trend reporting.

## Value

Network operations teams generate composite network health scores across all Meraki sites for executive reporting, combining device availability and security posture into a single, actionable metric per site.

## Implementation

1. Enable Devices Availabilities and Assurance Alerts inputs in Splunk_TA_cisco_meraki. 2. Compute availability_pct as online/total per network. 3. Subtract 0.5 per open alert to penalise networks with active issues. 4. Tune the weighting and tier the result into Critical/Warning/OK bands for an executive view.

## Detailed Implementation

### Prerequisites
- Install and configure the required add-on or app: `Cisco Meraki Add-on for Splunk` (Splunkbase 5580).
- Ensure the following data sources are available: Splunk_TA_cisco_meraki (Splunkbase #5580): Devices Availabilities input (sourcetype=meraki:devicesavailabilities) and Assurance Alerts input (sourcetype=meraki:assurancealerts). NOTE: the Meraki Dashboard API does NOT expose a single numeric 'health score' per device or network; this UC composes one from availability % and open-alert count..
- For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

### Step 1 — Configure data collection
1. Enable Devices Availabilities and Assurance Alerts inputs in Splunk_TA_cisco_meraki. 2. Compute availability_pct as online/total per network. 3. Subtract 0.5 per open alert to penalise networks with active issues. 4. Tune the weighting and tier the result into Critical/Warning/OK bands for an executive view.

### Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=meraki sourcetype="meraki:devicesavailabilities" earliest=-1h
| stats count as device_count,
        sum(eval(if(status="online",1,0))) as online_count,
        sum(eval(if(status="alerting",1,0))) as alerting_count,
        sum(eval(if(status="offline",1,0))) as offline_count
         by network.id, network.name
| eval availability_pct = round(online_count*100/device_count, 1)
| join type=left network.id [
    search index=meraki sourcetype="meraki:assurancealerts" earliest=-24h
    | stats count as open_alerts by networkId
    | rename networkId as "network.id"
  ]
| fillnull value=0 open_alerts
| eval network_health = round(availability_pct - (open_alerts*0.5), 1)
| sort network_health
```

#### Understanding this SPL

**Network Health Score Aggregation and Executive Reporting (Meraki)** — Network operations teams generate composite network health scores across all Meraki sites for executive reporting, combining device availability and security posture into a single, actionable metric per site.

Documented **Data sources**: Splunk_TA_cisco_meraki (Splunkbase #5580): Devices Availabilities input (sourcetype=meraki:devicesavailabilities) and Assurance Alerts input (sourcetype=meraki:assurancealerts). NOTE: the Meraki Dashboard API does NOT expose a single numeric 'health score' per device or network; this UC composes one from availability % and open-alert count. **App/TA** (typical add-on context): `Cisco Meraki Add-on for Splunk` (Splunkbase 5580). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: meraki; **sourcetype**: meraki:devicesavailabilities. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

- Scopes the data: index=meraki, sourcetype="meraki:devicesavailabilities", time bounds. Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
- `stats` rolls up events into metrics; results are split **by network.id, network.name** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
- `eval` defines or adjusts **availability_pct** — often to normalize units, derive a ratio, or prepare for thresholds.
- Joins to a subsearch with `join` — set `max=` to match cardinality and avoid silent truncation.
- Fills null values with `fillnull`.
- `eval` defines or adjusts **network_health** — often to normalize units, derive a ratio, or prepare for thresholds.
- Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.


### Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

### Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Network health gauge; health trend sparkline; status KPI dashboard.

## SPL

```spl
index=meraki sourcetype="meraki:devicesavailabilities" earliest=-1h
| stats count as device_count,
        sum(eval(if(status="online",1,0))) as online_count,
        sum(eval(if(status="alerting",1,0))) as alerting_count,
        sum(eval(if(status="offline",1,0))) as offline_count
         by network.id, network.name
| eval availability_pct = round(online_count*100/device_count, 1)
| join type=left network.id [
    search index=meraki sourcetype="meraki:assurancealerts" earliest=-24h
    | stats count as open_alerts by networkId
    | rename networkId as "network.id"
  ]
| fillnull value=0 open_alerts
| eval network_health = round(availability_pct - (open_alerts*0.5), 1)
| sort network_health
```

## Visualization

Network health gauge; health trend sparkline; status KPI dashboard.

## Known False Positives

Aggregates hide a single bad site; always drill to site-level before exec reporting drives the wrong project priority.

## References

- [Splunkbase app 5580](https://splunkbase.splunk.com/app/5580)
