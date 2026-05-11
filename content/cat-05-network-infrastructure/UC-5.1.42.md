<!-- AUTO-GENERATED from UC-5.1.42.json — DO NOT EDIT -->

---
id: "5.1.42"
title: "MAC Flooding and Bridge Table Exhaustion (Meraki MS)"
criticality: "high"
splunkPillar: "Security"
---

# UC-5.1.42 · MAC Flooding and Bridge Table Exhaustion (Meraki MS)

> **Criticality:** High &middot; **Difficulty:** Beginner &middot; **Pillar:** Security &middot; **Type:** Capacity

*We help you know early when something looks wrong with mac flooding and bridge table exhaustion so the team can act before it grows into a bigger outage.*

---

## Description

Detects MAC address table exhaustion and flooding attacks that could overwhelm switch resources.

## Value

Security teams detect MAC flooding attacks and bridge table exhaustion on Meraki MS switches, identifying ports generating excessive MAC addresses that compromise network segmentation.

## Implementation

1. Enable the Assurance Alerts input in Splunk_TA_cisco_meraki (TA v3+, hourly polling of GET /organizations/{orgId}/assurance/alerts). 2. Filter to deviceType=switch with MAC/flood/storm keywords. 3. For deeper inspection use Meraki Dashboard -> Switch -> Switches -> [select switch] -> Tools -> MAC table to see live entries; the MAC table size is not exposed via API.

## Detailed Implementation

### Prerequisites
- Install and configure the required add-on or app: `Cisco Meraki Add-on for Splunk` (Splunkbase 5580).
- Ensure the following data sources are available: Splunk_TA_cisco_meraki (Splunkbase #5580): Assurance Alerts input (sourcetype=meraki:assurancealerts). NOTE: Meraki MS switches do NOT emit per-port MAC flooding or bridge-table-exhaustion events to syslog. The closest signal is the Assurance Alerts feed which fires on switch performance issues..
- For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

### Step 1 — Configure data collection
1. Enable the Assurance Alerts input in Splunk_TA_cisco_meraki (TA v3+, hourly polling of GET /organizations/{orgId}/assurance/alerts). 2. Filter to deviceType=switch with MAC/flood/storm keywords. 3. For deeper inspection use Meraki Dashboard -> Switch -> Switches -> [select switch] -> Tools -> MAC table to see live entries; the MAC table size is not exposed via API.

### Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=meraki sourcetype="meraki:assurancealerts"
    deviceType="MS"
    (title="*MAC*" OR title="*flood*" OR title="*storm*"
     OR categoryType="performance")
    earliest=-24h
| stats count as alert_count,
        values(title) as alert_titles,
        latest(severity) as severity
         by scope.devices{}.serial, scope.devices{}.name, network.name
| sort - alert_count
```

#### Understanding this SPL

**MAC Flooding and Bridge Table Exhaustion (Meraki MS)** — Security teams detect MAC flooding attacks and bridge table exhaustion on Meraki MS switches, identifying ports generating excessive MAC addresses that compromise network segmentation.

Documented **Data sources**: Splunk_TA_cisco_meraki (Splunkbase #5580): Assurance Alerts input (sourcetype=meraki:assurancealerts). NOTE: Meraki MS switches do NOT emit per-port MAC flooding or bridge-table-exhaustion events to syslog. The closest signal is the Assurance Alerts feed which fires on switch performance issues. **App/TA** (typical add-on context): `Cisco Meraki Add-on for Splunk` (Splunkbase 5580). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: meraki; **sourcetype**: meraki:assurancealerts. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

- Scopes the data: index=meraki, sourcetype="meraki:assurancealerts", time bounds. Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
- `stats` rolls up events into metrics; results are split **by scope.devices{}.serial, scope.devices{}.name, network.name** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
- Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.


### Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

### Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table of affected switches/ports; time-series of flood events; alert dashboard.

## SPL

```spl
index=meraki sourcetype="meraki:assurancealerts"
    deviceType="MS"
    (title="*MAC*" OR title="*flood*" OR title="*storm*"
     OR categoryType="performance")
    earliest=-24h
| stats count as alert_count,
        values(title) as alert_titles,
        latest(severity) as severity
         by scope.devices{}.serial, scope.devices{}.name, network.name
| sort - alert_count
```

## Visualization

Table of affected switches/ports; time-series of flood events; alert dashboard.

## Known False Positives

VMware vMotion, imaging carts, and conference room churn move MACs often. Baseline by VLAN before calling an attack.

## References

- [Splunkbase app 5580](https://splunkbase.splunk.com/app/5580)
