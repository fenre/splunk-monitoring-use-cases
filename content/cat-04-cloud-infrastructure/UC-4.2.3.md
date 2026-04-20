---
id: "4.2.3"
title: "Entra ID Privilege Escalation"
criticality: "critical"
splunkPillar: "Security"
---

# UC-4.2.3 · Entra ID Privilege Escalation

## Description

Privileged role assignments (Global Admin, Privileged Role Admin) grant extreme power. Unauthorized assignments mean full tenant compromise.

## Value

Privileged role assignments (Global Admin, Privileged Role Admin) grant extreme power. Unauthorized assignments mean full tenant compromise.

## Implementation

Forward Entra ID audit logs. Create critical alerts on role assignments for Global Administrator, Privileged Role Administrator, and Exchange Administrator. Correlate with PIM activation events.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_microsoft-cloudservices`.
• Ensure the following data sources are available: `sourcetype=mscs:azure:auditlog`, Entra ID audit logs.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Forward Entra ID audit logs. Create critical alerts on role assignments for Global Administrator, Privileged Role Administrator, and Exchange Administrator. Correlate with PIM activation events.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=azure sourcetype="mscs:azure:auditlog" activityDisplayName="Add member to role"
| spath output=role path=targetResources{}.modifiedProperties{}.newValue
| table _time initiatedBy.user.userPrincipalName targetResources{}.userPrincipalName role
| sort -_time
```

Understanding this SPL

**Entra ID Privilege Escalation** — Privileged role assignments (Global Admin, Privileged Role Admin) grant extreme power. Unauthorized assignments mean full tenant compromise.

Documented **Data sources**: `sourcetype=mscs:azure:auditlog`, Entra ID audit logs. **App/TA** (typical add-on context): `Splunk_TA_microsoft-cloudservices`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: azure; **sourcetype**: mscs:azure:auditlog. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=azure, sourcetype="mscs:azure:auditlog". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Extracts structured paths (JSON/XML) with `spath`.
• Pipeline stage (see **Entra ID Privilege Escalation**): table _time initiatedBy.user.userPrincipalName targetResources{}.userPrincipalName role
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.

Optional CIM / accelerated variant (same use case, normalized fields via Common Information Model):

```spl
| tstats `summariesonly` count
  from datamodel=Change.All_Changes
  by All_Changes.user All_Changes.object_category All_Changes.action span=1h
| sort -count
```

Understanding this CIM / accelerated SPL

**Entra ID Privilege Escalation** — Privileged role assignments (Global Admin, Privileged Role Admin) grant extreme power. Unauthorized assignments mean full tenant compromise.

Documented **Data sources**: `sourcetype=mscs:azure:auditlog`, Entra ID audit logs. **App/TA** (typical add-on context): `Splunk_TA_microsoft-cloudservices`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

This **CIM or accelerated** block uses normalized field names and/or `tstats` over data models. Enable **acceleration** on the referenced models (and correct CIM knowledge objects) or the search may return nothing.

**Pipeline walkthrough**

• Uses `tstats` against accelerated summaries for data model `Change.All_Changes` — enable acceleration for that model.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.

Enable Data Model Acceleration (and metric indexes for `mstats`) for the models or datasets referenced above; otherwise `tstats`/`mstats` may return no results from summaries.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Events list (critical), Table (who assigned what to whom), Timeline.

## SPL

```spl
index=azure sourcetype="mscs:azure:auditlog" activityDisplayName="Add member to role"
| spath output=role path=targetResources{}.modifiedProperties{}.newValue
| table _time initiatedBy.user.userPrincipalName targetResources{}.userPrincipalName role
| sort -_time
```

## CIM SPL

```spl
| tstats `summariesonly` count
  from datamodel=Change.All_Changes
  by All_Changes.user All_Changes.object_category All_Changes.action span=1h
| sort -count
```

## Visualization

Events list (critical), Table (who assigned what to whom), Timeline.

## References

- [Splunk_TA_microsoft-cloudservices](https://splunkbase.splunk.com/app/3110)
- [CIM: Change](https://docs.splunk.com/Documentation/CIM/latest/User/Change)
