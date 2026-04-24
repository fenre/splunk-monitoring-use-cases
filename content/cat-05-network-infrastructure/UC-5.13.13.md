---
id: "5.13.13"
title: "Client Health by Site"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-5.13.13 · Client Health by Site

## Description

Aggregates client health metrics by Catalyst Center site, enabling location-based comparison of user experience quality.

## Value

Comparing client health across sites reveals whether problems are localized (single building) or systemic (infrastructure-wide), guiding remediation priority.

## Implementation

Requires UC-5.13.9 and site-level `siteId` in each event. If only UUIDs are present, add a `lookup` to friendly site names. Run during business hours to compare user populations fairly; for 24/7 sites, add a time-of-day trellis or a separate night-shift view.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Cisco Catalyst Add-on for Splunk` (Splunkbase 7538).
• Ensure the following data sources are available: index=catalyst, sourcetype cisco:dnac:clienthealth (Catalyst Center client health feed).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Requires UC-5.13.9 and site-level `siteId` in each event. If only UUIDs are present, add a `lookup` to friendly site names. Run during business hours to compare user populations fairly; for 24/7 sites, add a time-of-day trellis or a separate night-shift view.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=catalyst sourcetype="cisco:dnac:clienthealth" | stats avg(scoreDetail{}.scoreCategory.value) as avg_health sum(scoreDetail{}.clientCount) as total_clients by siteId | eval health_status=case(avg_health>=75,"Healthy",avg_health>=50,"Fair",1==1,"Poor") | sort avg_health
```

Understanding this SPL

**Client Health by Site** — Comparing client health across sites reveals whether problems are localized (single building) or systemic (infrastructure-wide), guiding remediation priority.

Documented **Data sources**: index=catalyst, sourcetype cisco:dnac:clienthealth (Catalyst Center client health feed). **App/TA** (typical add-on context): `Cisco Catalyst Add-on for Splunk` (Splunkbase 7538). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: catalyst; **sourcetype**: cisco:dnac:clienthealth. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• `stats` groups all events to each `siteId`, averaging the nested per-category `value` and summing the nested `clientCount` in one pass. Field semantics follow how Catalyst Center parallelizes the arrays in your data.
• `case` in `health_status` maps `avg_health` to Healthy, Fair, or Poor to mirror common executive bands; adjust the numeric cutoffs to match your SLOs.
• `sort avg_health` lists the most troubled sites at the top so a regional NOC can open UC-5.13.5 for devices as a follow-on where relevant.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (siteId, avg_health, total_clients, health_status), bar chart, map if joined with geo for campus locations.

## SPL

```spl
index=catalyst sourcetype="cisco:dnac:clienthealth" | stats avg(scoreDetail{}.scoreCategory.value) as avg_health sum(scoreDetail{}.clientCount) as total_clients by siteId | eval health_status=case(avg_health>=75,"Healthy",avg_health>=50,"Fair",1==1,"Poor") | sort avg_health
```

## Visualization

Table (siteId, avg_health, total_clients, health_status), bar chart, map if joined with geo for campus locations.

## References

- [Splunkbase app 7538](https://splunkbase.splunk.com/app/7538)
- [Catalyst Center API docs](https://developer.cisco.com/docs/catalyst-center/)
