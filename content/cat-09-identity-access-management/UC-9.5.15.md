---
id: "9.5.15"
title: "Okta User Lifecycle Events (Provisioning / Deprovisioning)"
status: "verified"
criticality: "high"
splunkPillar: "Security"
---

# UC-9.5.15 · Okta User Lifecycle Events (Provisioning / Deprovisioning)

## Description

Orphaned accounts, failed deprovisions, and unexpected creates drive audit findings and residual access after employee exit.

## Value

Orphaned accounts, failed deprovisions, and unexpected creates drive audit findings and residual access after employee exit.

## Implementation

Align event types with HRIS-driven lifecycle (create, activate, deactivate). Alert on deactivations that fail or retry, and on manual creates outside HR correlation. Feed summaries to access reviews.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_okta`.
• Ensure the following data sources are available: `sourcetype=OktaIM2:log` (`user.lifecycle.*`, `user.account.*`).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Align event types with HRIS-driven lifecycle (create, activate, deactivate). Alert on deactivations that fail or retry, and on manual creates outside HR correlation. Feed summaries to access reviews.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=okta sourcetype="OktaIM2:log"
| where like(eventType,"user.lifecycle%")
| stats count by actor.alternateId, eventType, target{}.displayName
| sort -_time
```

Understanding this SPL

**Okta User Lifecycle Events (Provisioning / Deprovisioning)** — Orphaned accounts, failed deprovisions, and unexpected creates drive audit findings and residual access after employee exit.

Documented **Data sources**: `sourcetype=OktaIM2:log` (`user.lifecycle.*`, `user.account.*`). **App/TA** (typical add-on context): `Splunk_TA_okta`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: okta; **sourcetype**: OktaIM2:log. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=okta, sourcetype="OktaIM2:log". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Filters the current rows with `where like(eventType,"user.lifecycle%")` — typically the threshold or rule expression for this monitoring goal.
• `stats` rolls up events into metrics; results are split **by actor.alternateId, eventType, target{}.displayName** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.

Optional CIM / accelerated variant (same use case, normalized fields via Common Information Model):

```spl
| tstats summariesonly=t count from datamodel=Change.All_Changes by All_Changes.action, All_Changes.object_category, All_Changes.user | sort - count
```

Understanding this CIM / accelerated SPL

**Okta User Lifecycle Events (Provisioning / Deprovisioning)** — Orphaned accounts, failed deprovisions, and unexpected creates drive audit findings and residual access after employee exit.

Documented **Data sources**: `sourcetype=OktaIM2:log` (`user.lifecycle.*`, `user.account.*`). **App/TA** (typical add-on context): `Splunk_TA_okta`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

This **CIM or accelerated** block uses normalized field names and/or `tstats` over data models. Enable **acceleration** on the referenced models (and correct CIM knowledge objects) or the search may return nothing.

**Pipeline walkthrough**

• Uses `tstats` against accelerated summaries for data model `Change.All_Changes` — enable acceleration for that model.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.

Enable Data Model Acceleration (and metric indexes for `mstats`) for the models or datasets referenced above; otherwise `tstats`/`mstats` may return no results from summaries.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (event, target user, actor), Line chart (lifecycle events per day), Bar chart (events by type).

## SPL

```spl
index=okta sourcetype="OktaIM2:log"
| where like(eventType,"user.lifecycle%")
| stats count by actor.alternateId, eventType, target{}.displayName
| sort -_time
```

## CIM SPL

```spl
| tstats summariesonly=t count from datamodel=Change.All_Changes by All_Changes.action, All_Changes.object_category, All_Changes.user | sort - count
```

## Visualization

Table (event, target user, actor), Line chart (lifecycle events per day), Bar chart (events by type).

## Known False Positives

Administrative tasks, scheduled jobs or platform updates can match this pattern — correlate with change management, maintenance windows and user role before raising severity.

## References

- [Splunk_TA_okta](https://splunkbase.splunk.com/app/6553)
- [CIM: Change](https://docs.splunk.com/Documentation/CIM/latest/User/Change)
