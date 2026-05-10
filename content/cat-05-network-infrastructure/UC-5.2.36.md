<!-- AUTO-GENERATED from UC-5.2.36.json — DO NOT EDIT -->

---
id: "5.2.36"
title: "Warm Spare Failover and Appliance Redundancy (Meraki MX)"
criticality: "critical"
splunkPillar: "Observability"
---

# UC-5.2.36 · Warm Spare Failover and Appliance Redundancy (Meraki MX)

> **Criticality:** Critical &middot; **Difficulty:** Beginner &middot; **Pillar:** Observability &middot; **Type:** Availability

*We catch warm-spare handovers so a spare box taking over is something you know about, not a mystery outage after the fact.*

---

## Description

Ensures warm spare failover mechanism is operational and redundancy is maintained.

## Value

NOC teams monitor Meraki MX warm spare failover events and redundancy status to ensure appliance-level high availability and detect loss of backup protection.

## Implementation

1. Configure SC4S for MX syslog. 2. Warm-spare role transitions are emitted as type=events with role keywords. 3. Enable the Assurance Alerts input for Dashboard-side HA alerts (warm-spare unreachable, primary failed, etc.). 4. Trigger paging-grade alerts on every HA role change — these are real failover incidents.

## Detailed Implementation

### Prerequisites
- Install and configure the required add-on or app: `Cisco Meraki Add-on for Splunk` (Splunkbase 5580).
- Ensure the following data sources are available: SC4S Meraki vendor pack (sourcetype=meraki) receiving MX warm-spare HA events as type=events, plus Splunk_TA_cisco_meraki Assurance Alerts input for HA-related Dashboard alerts..
- For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

### Step 1 — Configure data collection
1. Configure SC4S for MX syslog. 2. Warm-spare role transitions are emitted as type=events with role keywords. 3. Enable the Assurance Alerts input for Dashboard-side HA alerts (warm-spare unreachable, primary failed, etc.). 4. Trigger paging-grade alerts on every HA role change — these are real failover incidents.

### Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=meraki sourcetype="meraki" type=events
    ("warm spare" OR "warm-spare" OR "HA" OR "redundancy"
     OR "primary" OR "spare" OR "vrrp")
    earliest=-7d
| rex "(?<role>primary|spare|active|standby)"
| stats count as ha_event_count,
        values(role) as roles_seen
         by host
| where ha_event_count > 0
| append [
    search index=meraki sourcetype="meraki:assurancealerts" deviceType="appliance"
        (title="*HA*" OR title="*spare*" OR title="*primary*") earliest=-7d
    | stats values(title) as ha_alerts, count by deviceSerial, networkName
  ]
```

#### Understanding this SPL

**Warm Spare Failover and Appliance Redundancy (Meraki MX)** — NOC teams monitor Meraki MX warm spare failover events and redundancy status to ensure appliance-level high availability and detect loss of backup protection.

Documented **Data sources**: SC4S Meraki vendor pack (sourcetype=meraki) receiving MX warm-spare HA events as type=events, plus Splunk_TA_cisco_meraki Assurance Alerts input for HA-related Dashboard alerts. **App/TA** (typical add-on context): `Cisco Meraki Add-on for Splunk` (Splunkbase 5580). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: meraki; **sourcetype**: meraki. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

- Scopes the data: index=meraki, sourcetype="meraki", time bounds. Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
- Extracts fields with `rex` (regular expression).
- `stats` rolls up events into metrics; results are split **by host** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
- Filters the current rows with `where ha_event_count > 0` — typically the threshold or rule expression for this monitoring goal.
- Appends rows from a subsearch with `append`.


### Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

### Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: HA status dashboard; failover timeline; redundancy health gauge.

## SPL

```spl
index=meraki sourcetype="meraki" type=events
    ("warm spare" OR "warm-spare" OR "HA" OR "redundancy"
     OR "primary" OR "spare" OR "vrrp")
    earliest=-7d
| rex "(?<role>primary|spare|active|standby)"
| stats count as ha_event_count,
        values(role) as roles_seen
         by host
| where ha_event_count > 0
| append [
    search index=meraki sourcetype="meraki:assurancealerts" deviceType="appliance"
        (title="*HA*" OR title="*spare*" OR title="*primary*") earliest=-7d
    | stats values(title) as ha_alerts, count by deviceSerial, networkName
  ]
```

## Visualization

HA status dashboard; failover timeline; redundancy health gauge.

## Known False Positives

Rehearsed failovers, firmware rollouts, and power tests create warm-standby messages you already expect.

## References

- [Splunkbase app 5580](https://splunkbase.splunk.com/app/5580)
