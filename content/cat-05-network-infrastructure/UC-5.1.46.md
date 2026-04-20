---
id: "5.1.46"
title: "Stack Unit and Redundancy Health (Meraki MS)"
criticality: "high"
splunkPillar: "Security"
---

# UC-5.1.46 · Stack Unit and Redundancy Health (Meraki MS)

## Description

Ensures switch stacking configuration remains healthy and redundancy is not compromised.

## Value

Ensures switch stacking configuration remains healthy and redundancy is not compromised.

## Implementation

Monitor stack member status via device API. Alert on member removal or failure.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Cisco Meraki Add-on for Splunk` (Splunkbase 5580).
• Ensure the following data sources are available: `sourcetype=meraki:api device_type=MS stack_id=*`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Monitor stack member status via device API. Alert on member removal or failure.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=cisco_network sourcetype="meraki:api" device_type=MS stack_id=*
| stats count as stack_members, count(eval(status="offline")) as offline_members by stack_id
| where offline_members > 0
```

Understanding this SPL

**Stack Unit and Redundancy Health (Meraki MS)** — Ensures switch stacking configuration remains healthy and redundancy is not compromised.

Documented **Data sources**: `sourcetype=meraki:api device_type=MS stack_id=*`. **App/TA** (typical add-on context): `Cisco Meraki Add-on for Splunk` (Splunkbase 5580). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: cisco_network; **sourcetype**: meraki:api. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=cisco_network, sourcetype="meraki:api". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `stats` rolls up events into metrics; results are split **by stack_id** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• Filters the current rows with `where offline_members > 0` — typically the threshold or rule expression for this monitoring goal.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table of stack members and status; redundancy gauge; alert dashboard.

## SPL

```spl
index=cisco_network sourcetype="meraki:api" device_type=MS stack_id=*
| stats count as stack_members, count(eval(status="offline")) as offline_members by stack_id
| where offline_members > 0
```

## Visualization

Table of stack members and status; redundancy gauge; alert dashboard.

## References

- [Splunkbase app 5580](https://splunkbase.splunk.com/app/5580)
