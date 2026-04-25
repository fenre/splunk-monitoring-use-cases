<!-- AUTO-GENERATED from UC-2.6.12.json — DO NOT EDIT -->

---
id: "2.6.12"
title: "Citrix Application Usage and Popularity Analytics"
criticality: "medium"
splunkPillar: "Security"
---

# UC-2.6.12 · Citrix Application Usage and Popularity Analytics

## Description

Understanding which published applications are most used, by which user groups, and at what times enables informed capacity planning, application retirement decisions, and license optimization. Applications with zero usage can be decommissioned to reduce attack surface and management overhead. High-usage applications may need dedicated delivery groups or additional server capacity.

## Value

Understanding which published applications are most used, by which user groups, and at what times enables informed capacity planning, application retirement decisions, and license optimization. Applications with zero usage can be decommissioned to reduce attack surface and management overhead. High-usage applications may need dedicated delivery groups or additional server capacity.

## Implementation

Collect application launch events from the Broker Service event log or Monitor Service OData API `ApplicationInstances` endpoint. Track application name, launching user, delivery group, and session duration. Generate weekly reports showing: most-used applications (by unique users and total launches), least-used applications (candidates for retirement), peak usage hours per application, and average session duration. Correlate with license costs per application for ROI analysis.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: Template for Citrix XenDesktop 7 (`TA-XD7-Broker`), Citrix Monitor Service OData API.
• Ensure the following data sources are available: `index=xd` `sourcetype="citrix:broker:events"` fields `app_name`, `user`, `delivery_group`, `session_duration_min`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Collect application launch events from the Broker Service event log or Monitor Service OData API `ApplicationInstances` endpoint. Track application name, launching user, delivery group, and session duration. Generate weekly reports showing: most-used applications (by unique users and total launches), least-used applications (candidates for retirement), peak usage hours per application, and average session duration. Correlate with license costs per application for ROI analysis.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=xd sourcetype="citrix:broker:events" event_type="ApplicationLaunch"
| bin _time span=1d
| stats dc(user) as unique_users, count as launches, avg(session_duration_min) as avg_duration by app_name, _time
| sort -unique_users
| table _time, app_name, unique_users, launches, avg_duration
```

Understanding this SPL

**Citrix Application Usage and Popularity Analytics** — Understanding which published applications are most used, by which user groups, and at what times enables informed capacity planning, application retirement decisions, and license optimization. Applications with zero usage can be decommissioned to reduce attack surface and management overhead. High-usage applications may need dedicated delivery groups or additional server capacity.

Documented **Data sources**: `index=xd` `sourcetype="citrix:broker:events"` fields `app_name`, `user`, `delivery_group`, `session_duration_min`. **App/TA** (typical add-on context): Template for Citrix XenDesktop 7 (`TA-XD7-Broker`), Citrix Monitor Service OData API. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: xd; **sourcetype**: citrix:broker:events. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=xd, sourcetype="citrix:broker:events". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Discretizes time or numeric ranges with `bin`/`bucket`.
• `stats` rolls up events into metrics; results are split **by app_name, _time** so each row reflects one combination of those dimensions.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.
• Pipeline stage (see **Citrix Application Usage and Popularity Analytics**): table _time, app_name, unique_users, launches, avg_duration

Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Bar chart (top applications by users), Heatmap (application usage by hour), Table (unused applications).

## SPL

```spl
index=xd sourcetype="citrix:broker:events" event_type="ApplicationLaunch"
| bin _time span=1d
| stats dc(user) as unique_users, count as launches, avg(session_duration_min) as avg_duration by app_name, _time
| sort -unique_users
| table _time, app_name, unique_users, launches, avg_duration
```

## Visualization

Bar chart (top applications by users), Heatmap (application usage by hour), Table (unused applications).

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
