---
id: "1.2.76"
title: "AdminSDHolder Modification"
criticality: "critical"
splunkPillar: "Observability"
---

# UC-1.2.76 · AdminSDHolder Modification

## Description

The AdminSDHolder container controls ACLs on all privileged AD groups. Modifying it grants persistent hidden admin access that survives permission resets.

## Value

The AdminSDHolder container controls ACLs on all privileged AD groups. Modifying it grants persistent hidden admin access that survives permission resets.

## Implementation

Enable "Audit Directory Service Changes" on domain controllers. EventCode 5136=directory object modified. Filter for ObjectDN containing "AdminSDHolder". Any modification to this container is highly suspicious — it should only change via approved security hardening. The SDProp process propagates AdminSDHolder ACLs to all protected groups every 60 minutes. Alert immediately with critical priority.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_windows`.
• Ensure the following data sources are available: `sourcetype=WinEventLog:Security` (EventCode 5136).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Enable "Audit Directory Service Changes" on domain controllers. EventCode 5136=directory object modified. Filter for ObjectDN containing "AdminSDHolder". Any modification to this container is highly suspicious — it should only change via approved security hardening. The SDProp process propagates AdminSDHolder ACLs to all protected groups every 60 minutes. Alert immediately with critical priority.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=wineventlog sourcetype="WinEventLog:Security" EventCode=5136
  ObjectDN="*AdminSDHolder*"
| table _time, host, SubjectUserName, AttributeLDAPDisplayName, AttributeValue, OperationType
| sort -_time
```

Understanding this SPL

**AdminSDHolder Modification** — The AdminSDHolder container controls ACLs on all privileged AD groups. Modifying it grants persistent hidden admin access that survives permission resets.

Documented **Data sources**: `sourcetype=WinEventLog:Security` (EventCode 5136). **App/TA** (typical add-on context): `Splunk_TA_windows`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: wineventlog; **sourcetype**: WinEventLog:Security. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=wineventlog, sourcetype="WinEventLog:Security". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Pipeline stage (see **AdminSDHolder Modification**): table _time, host, SubjectUserName, AttributeLDAPDisplayName, AttributeValue, OperationType
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.

Optional CIM / accelerated variant (same use case, normalized fields via Common Information Model):

```spl
| tstats `summariesonly` count
  from datamodel=Authentication.Authentication
  where Authentication.action=success
  by Authentication.user Authentication.src Authentication.dest span=1h
| search Authentication.user=*admin* OR Authentication.user=root
```

Understanding this CIM / accelerated SPL

**AdminSDHolder Modification** — The AdminSDHolder container controls ACLs on all privileged AD groups. Modifying it grants persistent hidden admin access that survives permission resets.

Documented **Data sources**: `sourcetype=WinEventLog:Security` (EventCode 5136). **App/TA** (typical add-on context): `Splunk_TA_windows`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

This **CIM or accelerated** block uses normalized field names and/or `tstats` over data models. Enable **acceleration** on the referenced models (and correct CIM knowledge objects) or the search may return nothing.

**Pipeline walkthrough**

• Uses `tstats` against accelerated summaries for data model `Authentication.Authentication` — enable acceleration for that model.
• Applies an explicit `search` filter to narrow the current result set.

Enable Data Model Acceleration (and metric indexes for `mstats`) for the models or datasets referenced above; otherwise `tstats`/`mstats` may return no results from summaries.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (modifications), Single value (count — target: 0), Alert with SOC escalation.

## SPL

```spl
index=wineventlog sourcetype="WinEventLog:Security" EventCode=5136
  ObjectDN="*AdminSDHolder*"
| table _time, host, SubjectUserName, AttributeLDAPDisplayName, AttributeValue, OperationType
| sort -_time
```

## CIM SPL

```spl
| tstats `summariesonly` count
  from datamodel=Authentication.Authentication
  where Authentication.action=success
  by Authentication.user Authentication.src Authentication.dest span=1h
| search Authentication.user=*admin* OR Authentication.user=root
```

## Visualization

Table (modifications), Single value (count — target: 0), Alert with SOC escalation.

## References

- [Splunk_TA_windows](https://splunkbase.splunk.com/app/742)
- [CIM: Authentication](https://docs.splunk.com/Documentation/CIM/latest/User/Authentication)
