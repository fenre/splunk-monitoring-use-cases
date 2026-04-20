---
id: "1.2.31"
title: "Kerberos Authentication Failures"
criticality: "high"
splunkPillar: "Observability"
---

# UC-1.2.31 · Kerberos Authentication Failures

## Description

Kerberos failures (EventCode 4771) reveal password spraying, expired accounts, clock skew, and misconfigured SPNs. Distinct from NTLM failures and requires separate monitoring.

## Value

Kerberos failures (EventCode 4771) reveal password spraying, expired accounts, clock skew, and misconfigured SPNs. Distinct from NTLM failures and requires separate monitoring.

## Implementation

Collect Security event logs from all domain controllers. EventCode 4771 is Kerberos pre-auth failure. Status codes: 0x18=wrong password (most common attack indicator), 0x12=disabled/locked, 0x25=clock skew (infrastructure issue). Alert on >10 failures per user in 5 minutes (spray detection). Correlate IpAddress with known endpoints.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_windows`.
• Ensure the following data sources are available: `sourcetype=WinEventLog:Security` (EventCode 4771).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Collect Security event logs from all domain controllers. EventCode 4771 is Kerberos pre-auth failure. Status codes: 0x18=wrong password (most common attack indicator), 0x12=disabled/locked, 0x25=clock skew (infrastructure issue). Alert on >10 failures per user in 5 minutes (spray detection). Correlate IpAddress with known endpoints.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=wineventlog sourcetype="WinEventLog:Security" EventCode=4771
| eval failure=case(Status="0x6","Unknown username",Status="0x12","Account disabled/expired/locked",Status="0x17","Password expired",Status="0x18","Bad password",Status="0x25","Clock skew",1=1,Status)
| stats count by TargetUserName, IpAddress, failure, host
| where count > 5
| sort -count
```

Understanding this SPL

**Kerberos Authentication Failures** — Kerberos failures (EventCode 4771) reveal password spraying, expired accounts, clock skew, and misconfigured SPNs. Distinct from NTLM failures and requires separate monitoring.

Documented **Data sources**: `sourcetype=WinEventLog:Security` (EventCode 4771). **App/TA** (typical add-on context): `Splunk_TA_windows`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: wineventlog; **sourcetype**: WinEventLog:Security. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=wineventlog, sourcetype="WinEventLog:Security". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `eval` defines or adjusts **failure** — often to normalize units, derive a ratio, or prepare for thresholds.
• `stats` rolls up events into metrics; results are split **by TargetUserName, IpAddress, failure, host** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• Filters the current rows with `where count > 5` — typically the threshold or rule expression for this monitoring goal.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.

Optional CIM / accelerated variant (same use case, normalized fields via Common Information Model):

```spl
| tstats `summariesonly` count
  from datamodel=Authentication.Authentication
  where Authentication.action=failure
  by Authentication.user Authentication.src span=1h
| where count > 10
```

Understanding this CIM / accelerated SPL

**Kerberos Authentication Failures** — Kerberos failures (EventCode 4771) reveal password spraying, expired accounts, clock skew, and misconfigured SPNs. Distinct from NTLM failures and requires separate monitoring.

Documented **Data sources**: `sourcetype=WinEventLog:Security` (EventCode 4771). **App/TA** (typical add-on context): `Splunk_TA_windows`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

This **CIM or accelerated** block uses normalized field names and/or `tstats` over data models. Enable **acceleration** on the referenced models (and correct CIM knowledge objects) or the search may return nothing.

**Pipeline walkthrough**

• Uses `tstats` against accelerated summaries for data model `Authentication.Authentication` — enable acceleration for that model.
• Filters the current rows with `where count > 10` — typically the threshold or rule expression for this monitoring goal.

Enable Data Model Acceleration (and metric indexes for `mstats`) for the models or datasets referenced above; otherwise `tstats`/`mstats` may return no results from summaries.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (failures by user and reason), Bar chart (top failing accounts), Timechart (failure rate trending).

## SPL

```spl
index=wineventlog sourcetype="WinEventLog:Security" EventCode=4771
| eval failure=case(Status="0x6","Unknown username",Status="0x12","Account disabled/expired/locked",Status="0x17","Password expired",Status="0x18","Bad password",Status="0x25","Clock skew",1=1,Status)
| stats count by TargetUserName, IpAddress, failure, host
| where count > 5
| sort -count
```

## CIM SPL

```spl
| tstats `summariesonly` count
  from datamodel=Authentication.Authentication
  where Authentication.action=failure
  by Authentication.user Authentication.src span=1h
| where count > 10
```

## Visualization

Table (failures by user and reason), Bar chart (top failing accounts), Timechart (failure rate trending).

## References

- [Splunk_TA_windows](https://splunkbase.splunk.com/app/742)
- [CIM: Authentication](https://docs.splunk.com/Documentation/CIM/latest/User/Authentication)
