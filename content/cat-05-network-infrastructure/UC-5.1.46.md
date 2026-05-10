<!-- AUTO-GENERATED from UC-5.1.46.json — DO NOT EDIT -->

---
id: "5.1.46"
title: "Stack Unit and Redundancy Health (Meraki MS)"
criticality: "high"
splunkPillar: "Security"
---

# UC-5.1.46 · Stack Unit and Redundancy Health (Meraki MS)

> **Criticality:** High &middot; **Difficulty:** Beginner &middot; **Pillar:** Security &middot; **Type:** Availability

*We help you know early when something looks wrong with stack unit and redundancy health so the team can act before it grows into a bigger outage.*

---

## Description

Ensures switch stacking configuration remains healthy and redundancy is not compromised.

## Value

NOC teams monitor Meraki MS switch stack health including member presence, ring topology status, and role changes, detecting stack member loss and ring breaks that reduce redundancy.

## Implementation

1. Enable Devices Availabilities and Devices Availabilities Change History inputs. Meraki MS stacks are modeled as multiple switches in the same network sharing a switchProfileId; status field is online/offline/dormant/alerting. 2. The query above groups switches by network and counts offline members. For more accurate per-stack grouping use 'index=meraki sourcetype=meraki:devices productType=switch' joined on switchProfileId. 3. Pair with an alert profile that triggers when offline_members exceeds 0 within a stack-bearing network.

## Detailed Implementation

### Prerequisites
- Install and configure the required add-on or app: `Cisco Meraki Add-on for Splunk` (Splunkbase 5580).
- Ensure the following data sources are available: Splunk_TA_cisco_meraki (Splunkbase #5580): Devices Availabilities input (sourcetype=meraki:devicesavailabilities, daily, TA v3.3+) and Device Availabilities Change History input (sourcetype=meraki:devicesavailabilitieschangehistory, hourly) for stack member status. Stack inventory comes from meraki:devices (productType=switch, switchProfileId field identifies stacked members)..
- For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

### Step 1 — Configure data collection
1. Enable Devices Availabilities and Devices Availabilities Change History inputs. Meraki MS stacks are modeled as multiple switches in the same network sharing a switchProfileId; status field is online/offline/dormant/alerting. 2. The query above groups switches by network and counts offline members. For more accurate per-stack grouping use 'index=meraki sourcetype=meraki:devices productType=switch' joined on switchProfileId. 3. Pair with an alert profile that triggers when offline_members exce…

### Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=meraki sourcetype="meraki:devicesavailabilities" productType="switch" earliest=-1h
| stats values(serial) as members,
        count as stack_size,
        sum(eval(if(status="online",0,1))) as offline_members,
        latest(status) as latest_status
         by network.id, network.name
| where stack_size > 1 AND offline_members > 0
| sort - offline_members
```

#### Understanding this SPL

**Stack Unit and Redundancy Health (Meraki MS)** — NOC teams monitor Meraki MS switch stack health including member presence, ring topology status, and role changes, detecting stack member loss and ring breaks that reduce redundancy.

Documented **Data sources**: Splunk_TA_cisco_meraki (Splunkbase #5580): Devices Availabilities input (sourcetype=meraki:devicesavailabilities, daily, TA v3.3+) and Device Availabilities Change History input (sourcetype=meraki:devicesavailabilitieschangehistory, hourly) for stack member status. Stack inventory comes from meraki:devices (productType=switch, switchProfileId field identifies stacked members). **App/TA** (typical add-on context): `Cisco Meraki Add-on for Splunk` (Splunkbase 5580). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: meraki; **sourcetype**: meraki:devicesavailabilities. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

- Scopes the data: index=meraki, sourcetype="meraki:devicesavailabilities", time bounds. Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
- `stats` rolls up events into metrics; results are split **by network.id, network.name** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
- Filters the current rows with `where stack_size > 1 AND offline_members > 0` — typically the threshold or rule expression for this monitoring goal.
- Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.


### Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

### Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table of stack members and status; redundancy gauge; alert dashboard.

## SPL

```spl
index=meraki sourcetype="meraki:devicesavailabilities" productType="switch" earliest=-1h
| stats values(serial) as members,
        count as stack_size,
        sum(eval(if(status="online",0,1))) as offline_members,
        latest(status) as latest_status
         by network.id, network.name
| where stack_size > 1 AND offline_members > 0
| sort - offline_members
```

## Visualization

Table of stack members and status; redundancy gauge; alert dashboard.

## Known False Positives

Meraki cloud delays, dashboard API limits, and large site templates can look like a gap. Confirm in dashboard before opening a P1 on Splunk only.

## References

- [Splunkbase app 5580](https://splunkbase.splunk.com/app/5580)
