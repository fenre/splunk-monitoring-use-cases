---
id: "1.2.55"
title: "Suspicious Token Manipulation"
criticality: "critical"
splunkPillar: "Security"
---

# UC-1.2.55 · Suspicious Token Manipulation

## Description

Token impersonation and privilege escalation via token manipulation (SeImpersonatePrivilege abuse) is a common post-exploitation technique.

## Value

Token impersonation and privilege escalation via token manipulation (SeImpersonatePrivilege abuse) is a common post-exploitation technique.

## Implementation

Enable "Audit Sensitive Privilege Use" in Advanced Audit Policy. EventCode 4673=sensitive privilege used, 4674=operation on privileged object. Focus on SeImpersonatePrivilege (Potato attacks), SeDebugPrivilege (memory injection), SeTcbPrivilege (token creation). Filter known legitimate users (service accounts, SQL Server, IIS). Alert on non-standard processes using these privileges.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_windows`.
• Ensure the following data sources are available: `sourcetype=WinEventLog:Security` (EventCode 4673, 4674).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Enable "Audit Sensitive Privilege Use" in Advanced Audit Policy. EventCode 4673=sensitive privilege used, 4674=operation on privileged object. Focus on SeImpersonatePrivilege (Potato attacks), SeDebugPrivilege (memory injection), SeTcbPrivilege (token creation). Filter known legitimate users (service accounts, SQL Server, IIS). Alert on non-standard processes using these privileges.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=wineventlog sourcetype="WinEventLog:Security" EventCode IN (4673, 4674)
  Privileges IN ("SeImpersonatePrivilege", "SeAssignPrimaryTokenPrivilege", "SeTcbPrivilege", "SeDebugPrivilege")
| where NOT match(ProcessName, "(?i)(lsass|svchost|services|mssql|w3wp)")
| stats count by SubjectUserName, ProcessName, Privileges, host
| sort -count
```

Understanding this SPL

**Suspicious Token Manipulation** — Token impersonation and privilege escalation via token manipulation (SeImpersonatePrivilege abuse) is a common post-exploitation technique.

Documented **Data sources**: `sourcetype=WinEventLog:Security` (EventCode 4673, 4674). **App/TA** (typical add-on context): `Splunk_TA_windows`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: wineventlog; **sourcetype**: WinEventLog:Security. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=wineventlog, sourcetype="WinEventLog:Security". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Filters the current rows with `where NOT match(ProcessName, "(?i)(lsass|svchost|services|mssql|w3wp)")` — typically the threshold or rule expression for this monitoring goal.
• `stats` rolls up events into metrics; results are split **by SubjectUserName, ProcessName, Privileges, host** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.

Optional CIM / accelerated variant (same use case, normalized fields via Common Information Model):

```spl
| tstats `summariesonly` count
  from datamodel=Authentication.Authentication
  where Authentication.action=failure
  by Authentication.user Authentication.src Authentication.dest span=1h
| where count > 5
```

Understanding this CIM / accelerated SPL

**Suspicious Token Manipulation** — Token impersonation and privilege escalation via token manipulation (SeImpersonatePrivilege abuse) is a common post-exploitation technique.

Documented **Data sources**: `sourcetype=WinEventLog:Security` (EventCode 4673, 4674). **App/TA** (typical add-on context): `Splunk_TA_windows`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

This **CIM or accelerated** block uses normalized field names and/or `tstats` over data models. Enable **acceleration** on the referenced models (and correct CIM knowledge objects) or the search may return nothing.

**Pipeline walkthrough**

• Uses `tstats` against accelerated summaries for data model `Authentication.Authentication` — enable acceleration for that model.
• Filters the current rows with `where count > 5` — typically the threshold or rule expression for this monitoring goal.

Enable Data Model Acceleration (and metric indexes for `mstats`) for the models or datasets referenced above; otherwise `tstats`/`mstats` may return no results from summaries.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (privilege usage by process), Bar chart (privilege types), Timeline, Alert on unusual callers.

## SPL

```spl
index=wineventlog sourcetype="WinEventLog:Security" EventCode IN (4673, 4674)
  Privileges IN ("SeImpersonatePrivilege", "SeAssignPrimaryTokenPrivilege", "SeTcbPrivilege", "SeDebugPrivilege")
| where NOT match(ProcessName, "(?i)(lsass|svchost|services|mssql|w3wp)")
| stats count by SubjectUserName, ProcessName, Privileges, host
| sort -count
```

## CIM SPL

```spl
| tstats `summariesonly` count
  from datamodel=Authentication.Authentication
  where Authentication.action=failure
  by Authentication.user Authentication.src Authentication.dest span=1h
| where count > 5
```

## Visualization

Table (privilege usage by process), Bar chart (privilege types), Timeline, Alert on unusual callers.

## References

- [Splunk_TA_windows](https://splunkbase.splunk.com/app/742)
- [CIM: Authentication](https://docs.splunk.com/Documentation/CIM/latest/User/Authentication)
