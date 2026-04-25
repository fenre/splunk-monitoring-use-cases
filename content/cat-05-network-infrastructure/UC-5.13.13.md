<!-- AUTO-GENERATED from UC-5.13.13.json — DO NOT EDIT -->

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
• **UC-5.13.9** and client health data flowing to `cisco:dnac:clienthealth`.
• `siteId` on events (Catalyst site hierarchy in Design and inventory sync). Add a **lookup** from `siteId` to building or campus name for humans.
• Cisco Catalyst Add-on (7538); `clienthealth` input. Nested `scoreDetail` field paths can differ by build—`scoreDetail{}.scoreCategory.value` is convenient when multivalue paths work; if not, use the same `spath` flattening as UC-5.13.9 and aggregate after.
• See `docs/implementation-guide.md`.

Step 1 — Configure data collection
• Intent client-health API via TA `clienthealth` modular input; default 900s poll.
• Confirm `siteId` is non-null for production sites; unassigned clients skew “unknown” site buckets.

Step 2 — Create the search and alert
```spl
index=catalyst sourcetype="cisco:dnac:clienthealth" | stats avg(scoreDetail{}.scoreCategory.value) as avg_health sum(scoreDetail{}.clientCount) as total_clients by siteId | eval health_status=case(avg_health>=75,"Healthy",avg_health>=50,"Fair",1==1,"Poor") | sort avg_health
```

Understanding this SPL
• Multivalue `scoreDetail{}` paths roll up all nested categories in one `stats`—if your data shape does not support parallel arrays, switch to a flattened subsearch (UC-5.13.9 pattern) and then `stats by siteId`.
• `health_status` uses 75/50 cutoffs; align to your SLOs or to device-health bands used in UC-5.13.1 for executive consistency.
• `sort avg_health` ascending shows worst user experience at the top; pair with `total_clients` to avoid overreacting to a small branch.

**Pipeline walkthrough**
• `stats by siteId` → average of reported health values and sum of client counts; `eval` labels bands; `sort` for triage order.

Step 3 — Validate
• Compare a single site’s row to Catalyst Center Client health for that site in the same window.
• `| fieldsummary siteId` to ensure coverage; if many nulls, fix hierarchy in Catalyst before trusting rankings.

Step 4 — Operationalize
• Regional dashboard: table of site (name from lookup), avg_health, total_clients, health_status. Drill to UC-5.13.5 for device-level health and UC-5.13.1 where needed.
• Optional: trellis or separate panels for “large campus” vs “branch” using a site-tier lookup to avoid false prioritization.

Step 5 — Troubleshooting
• Wildly wrong averages: often multivalue `scoreDetail` is not parallel—flatten first, then re-aggregate.
• Good Splunk, bad UI: time zone, site filter in TA, or different Assurance scope in the console versus global Splunk index.


## SPL

```spl
index=catalyst sourcetype="cisco:dnac:clienthealth" | stats avg(scoreDetail{}.scoreCategory.value) as avg_health sum(scoreDetail{}.clientCount) as total_clients by siteId | eval health_status=case(avg_health>=75,"Healthy",avg_health>=50,"Fair",1==1,"Poor") | sort avg_health
```

## Visualization

Table (siteId, avg_health, total_clients, health_status), bar chart, map if joined with geo for campus locations.

## References

- [Splunkbase app 7538](https://splunkbase.splunk.com/app/7538)
- [Catalyst Center API docs](https://developer.cisco.com/docs/catalyst-center/)
- [Catalyst Center Integration Guide](docs/guides/catalyst-center.md)
