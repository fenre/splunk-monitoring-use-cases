---
id: "9.5.6"
title: "Okta New Admin Creation"
criticality: "critical"
splunkPillar: "Security"
---

# UC-9.5.6 · Okta New Admin Creation

## Description

New super-admin or role assignments are high-value targets for attackers; immediate notification enables rapid validation.

## Value

New super-admin or role assignments are high-value targets for attackers; immediate notification enables rapid validation.

## Implementation

Parse `target` for admin roles and groups. Use lookups for approved role-assignment paths. Alert on any new admin grant or role elevation. Include `actor` and `client.ipAddress` for triage.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_okta`.
• Ensure the following data sources are available: `sourcetype=OktaIM2:log` (`user.privilege.grant`, `group.privilege*`).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Parse `target` for admin roles and groups. Use lookups for approved role-assignment paths. Alert on any new admin grant or role elevation. Include `actor` and `client.ipAddress` for triage.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=okta sourcetype="OktaIM2:log"
| where eventType="user.privilege.grant" OR like(eventType,"group.privilege%")
| eval tgt=lower(mvjoin('target{}.displayName'," "))
| where like(tgt,"%admin%") OR like(tgt,"%super%")
| table _time, actor.alternateId, target{}.displayName, target{}.type
```

Understanding this SPL

**Okta New Admin Creation** — New super-admin or role assignments are high-value targets for attackers; immediate notification enables rapid validation.

Documented **Data sources**: `sourcetype=OktaIM2:log` (`user.privilege.grant`, `group.privilege*`). **App/TA** (typical add-on context): `Splunk_TA_okta`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: okta; **sourcetype**: OktaIM2:log. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=okta, sourcetype="OktaIM2:log". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Filters the current rows with `where eventType="user.privilege.grant" OR like(eventType,"group.privilege%")` — typically the threshold or rule expression for this monitoring goal.
• `eval` defines or adjusts **tgt** — often to normalize units, derive a ratio, or prepare for thresholds.
• Filters the current rows with `where like(tgt,"%admin%") OR like(tgt,"%super%")` — typically the threshold or rule expression for this monitoring goal.
• Pipeline stage (see **Okta New Admin Creation**): table _time, actor.alternateId, target{}.displayName, target{}.type

Optional CIM / accelerated variant (same use case, normalized fields via Common Information Model):

```spl
| tstats summariesonly=t count from datamodel=Change.All_Changes by All_Changes.action, All_Changes.object_category, All_Changes.user | sort - count
```

Understanding this CIM / accelerated SPL

**Okta New Admin Creation** — New super-admin or role assignments are high-value targets for attackers; immediate notification enables rapid validation.

Documented **Data sources**: `sourcetype=OktaIM2:log` (`user.privilege.grant`, `group.privilege*`). **App/TA** (typical add-on context): `Splunk_TA_okta`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

This **CIM or accelerated** block uses normalized field names and/or `tstats` over data models. Enable **acceleration** on the referenced models (and correct CIM knowledge objects) or the search may return nothing.

**Pipeline walkthrough**

• Uses `tstats` against accelerated summaries for data model `Change.All_Changes` — enable acceleration for that model.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.

Enable Data Model Acceleration (and metric indexes for `mstats`) for the models or datasets referenced above; otherwise `tstats`/`mstats` may return no results from summaries.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (who, what role, when), Timeline, Single value (admin grants today).

## SPL

```spl
index=okta sourcetype="OktaIM2:log"
| where eventType="user.privilege.grant" OR like(eventType,"group.privilege%")
| eval tgt=lower(mvjoin('target{}.displayName'," "))
| where like(tgt,"%admin%") OR like(tgt,"%super%")
| table _time, actor.alternateId, target{}.displayName, target{}.type
```

## CIM SPL

```spl
| tstats summariesonly=t count from datamodel=Change.All_Changes by All_Changes.action, All_Changes.object_category, All_Changes.user | sort - count
```

## Visualization

Table (who, what role, when), Timeline, Single value (admin grants today).

## Known False Positives

Administrative tasks, scheduled jobs or platform updates can match this pattern — correlate with change management, maintenance windows and user role before raising severity.

## References

- [Splunk_TA_okta](https://splunkbase.splunk.com/app/6553)
- [CIM: Change](https://docs.splunk.com/Documentation/CIM/latest/User/Change)
