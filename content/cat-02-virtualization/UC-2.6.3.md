---
id: "2.6.3"
title: "Citrix Connection Failure Analysis"
criticality: "critical"
splunkPillar: "Observability"
---

# UC-2.6.3 · Citrix Connection Failure Analysis

## Description

Connection failures prevent users from launching virtual desktops or published applications. Failures can occur at multiple stages: brokering (no available machines), power management (VM failed to start), registration (VDA not registered with controller), or HDX connection (protocol failure). Categorizing failures by type and correlating with infrastructure state enables rapid root-cause identification.

## Value

Connection failures prevent users from launching virtual desktops or published applications. Failures can occur at multiple stages: brokering (no available machines), power management (VM failed to start), registration (VDA not registered with controller), or HDX connection (protocol failure). Categorizing failures by type and correlating with infrastructure state enables rapid root-cause identification.

## Implementation

Collect Broker Service events (Event IDs 1100–1199 for connection lifecycle) from Delivery Controllers. The Monitor Service OData API `ConnectionFailureLogs` endpoint provides structured failure data with `FailureType` (ClientConnectionFailure, MachineFailure, etc.) and `FailureReason`. Alert on: more than 3 failures in 15 minutes for any delivery group, any `MachineFailure` type (indicates infrastructure problem), or rising failure rates across the site. Correlate with machine power state and VDA registration status for root cause.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: Template for Citrix XenDesktop 7 (`TA-XD7-Broker`), Citrix Monitor Service OData API.
• Ensure the following data sources are available: `index=xd` `sourcetype="citrix:broker:events"` fields `connection_state`, `failure_reason`, `failure_type`, `delivery_group`, `machine_name`, `user`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Collect Broker Service events (Event IDs 1100–1199 for connection lifecycle) from Delivery Controllers. The Monitor Service OData API `ConnectionFailureLogs` endpoint provides structured failure data with `FailureType` (ClientConnectionFailure, MachineFailure, etc.) and `FailureReason`. Alert on: more than 3 failures in 15 minutes for any delivery group, any `MachineFailure` type (indicates infrastructure problem), or rising failure rates across the site. Correlate with machine power state and V…

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=xd sourcetype="citrix:broker:events" event_type="ConnectionFailure"
| bin _time span=15m
| stats count as failures, dc(user) as affected_users, values(failure_reason) as reasons by failure_type, delivery_group, _time
| where failures > 3
| sort -failures
| table _time, delivery_group, failure_type, failures, affected_users, reasons
```

Understanding this SPL

**Citrix Connection Failure Analysis** — Connection failures prevent users from launching virtual desktops or published applications. Failures can occur at multiple stages: brokering (no available machines), power management (VM failed to start), registration (VDA not registered with controller), or HDX connection (protocol failure). Categorizing failures by type and correlating with infrastructure state enables rapid root-cause identification.

Documented **Data sources**: `index=xd` `sourcetype="citrix:broker:events"` fields `connection_state`, `failure_reason`, `failure_type`, `delivery_group`, `machine_name`, `user`. **App/TA** (typical add-on context): Template for Citrix XenDesktop 7 (`TA-XD7-Broker`), Citrix Monitor Service OData API. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: xd; **sourcetype**: citrix:broker:events. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=xd, sourcetype="citrix:broker:events". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Discretizes time or numeric ranges with `bin`/`bucket`.
• `stats` rolls up events into metrics; results are split **by failure_type, delivery_group, _time** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• Filters the current rows with `where failures > 3` — typically the threshold or rule expression for this monitoring goal.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.
• Pipeline stage (see **Citrix Connection Failure Analysis**): table _time, delivery_group, failure_type, failures, affected_users, reasons


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Bar chart (failures by type), Timeline (failure events), Table (recent failures with user and machine details).

## SPL

```spl
index=xd sourcetype="citrix:broker:events" event_type="ConnectionFailure"
| bin _time span=15m
| stats count as failures, dc(user) as affected_users, values(failure_reason) as reasons by failure_type, delivery_group, _time
| where failures > 3
| sort -failures
| table _time, delivery_group, failure_type, failures, affected_users, reasons
```

## Visualization

Bar chart (failures by type), Timeline (failure events), Table (recent failures with user and machine details).

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
