<!-- AUTO-GENERATED from UC-1.2.123.json — DO NOT EDIT -->

---
id: "1.2.123"
title: "Token Manipulation / Privilege Escalation"
criticality: "critical"
splunkPillar: "Security"
---

# UC-1.2.123 · Token Manipulation / Privilege Escalation

## Description

Token manipulation (impersonation, token duplication) allows attackers to escalate privileges. Detecting abuse of SeImpersonatePrivilege catches potato-style attacks.

## Value

Token privilege abuse is a direct path to admin on the box. Correlating 4672/4703 style activity with process data shortens time to stop elevation chains.

## Implementation

Enable Audit Sensitive Privilege Use. Monitor 4673 (sensitive privilege used) and 4674 (privilege operation on privileged object). Focus on SeImpersonatePrivilege (potato attacks), SeDebugPrivilege (process injection), SeTcbPrivilege (token creation), and SeAssignPrimaryTokenPrivilege. Filter OS processes. Alert on privilege use by service accounts running web apps or databases (common potato attack targets). MITRE ATT&CK T1134.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_windows`.
• Ensure the following data sources are available: `sourcetype=WinEventLog:Security` (EventCode 4673, 4674).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Enable Audit Sensitive Privilege Use. Monitor 4673 (sensitive privilege used) and 4674 (privilege operation on privileged object). Focus on SeImpersonatePrivilege (potato attacks), SeDebugPrivilege (process injection), SeTcbPrivilege (token creation), and SeAssignPrimaryTokenPrivilege. Filter OS processes. Alert on privilege use by service accounts running web apps or databases (common potato attack targets). MITRE ATT&CK T1134.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=wineventlog EventCode IN (4673, 4674) PrivilegeList IN ("SeImpersonatePrivilege", "SeAssignPrimaryTokenPrivilege", "SeTcbPrivilege", "SeDebugPrivilege")
| where NOT match(ProcessName, "(?i)(lsass|services|svchost|csrss|wininit|smss)")
| stats count by host, SubjectUserName, ProcessName, PrivilegeList
| sort -count
```

Understanding this SPL

**Token Manipulation / Privilege Escalation** — Token manipulation (impersonation, token duplication) allows attackers to escalate privileges. Detecting abuse of SeImpersonatePrivilege catches potato-style attacks.

Documented **Data sources**: `sourcetype=WinEventLog:Security` (EventCode 4673, 4674). **App/TA** (typical add-on context): `Splunk_TA_windows`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: wineventlog.

**Pipeline walkthrough**

• Scopes the data: index=wineventlog. Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Filters the current rows with `where NOT match(ProcessName, "(?i)(lsass|services|svchost|csrss|wininit|smss)")` — typically the threshold or rule expression for this monitoring goal.
• `stats` rolls up events into metrics; results are split **by host, SubjectUserName, ProcessName, PrivilegeList** so each row reflects one combination of those dimensions.
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

**Token Manipulation / Privilege Escalation** — Token manipulation (impersonation, token duplication) allows attackers to escalate privileges. Detecting abuse of SeImpersonatePrivilege catches potato-style attacks.

Documented **Data sources**: `sourcetype=WinEventLog:Security` (EventCode 4673, 4674). **App/TA** (typical add-on context): `Splunk_TA_windows`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

This **CIM or accelerated** block uses normalized field names and/or `tstats` over data models. Enable **acceleration** on the referenced models (and correct CIM knowledge objects) or the search may return nothing.

**Pipeline walkthrough**

• Uses `tstats` against accelerated summaries for data model `Authentication.Authentication` — enable acceleration for that model.
• Applies an explicit `search` filter to narrow the current result set.

Enable Data Model Acceleration (and metric indexes for `mstats`) for the models or datasets referenced above; otherwise `tstats`/`mstats` may return no results from summaries.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (privilege use events), Alert on suspicious processes, Bar chart.

## SPL

```spl
index=wineventlog EventCode IN (4673, 4674) PrivilegeList IN ("SeImpersonatePrivilege", "SeAssignPrimaryTokenPrivilege", "SeTcbPrivilege", "SeDebugPrivilege")
| where NOT match(ProcessName, "(?i)(lsass|services|svchost|csrss|wininit|smss)")
| stats count by host, SubjectUserName, ProcessName, PrivilegeList
| sort -count
```

## CIM SPL

```spl
| tstats `summariesonly` count
  from datamodel=Authentication.Authentication
  by Authentication.user Authentication.src Authentication.dest span=1h
| where count > 0
```

## Visualization

Table (privilege use events), Alert on suspicious processes, Bar chart.

## References

- [Splunk_TA_windows](https://splunkbase.splunk.com/app/742)
- [CIM: Authentication](https://docs.splunk.com/Documentation/CIM/latest/User/Authentication)
