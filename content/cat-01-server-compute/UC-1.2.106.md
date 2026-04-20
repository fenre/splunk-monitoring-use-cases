---
id: "1.2.106"
title: "Local Administrator Group Membership Changes"
criticality: "critical"
splunkPillar: "Security"
---

# UC-1.2.106 · Local Administrator Group Membership Changes

## Description

Local admin privileges enable credential theft, persistence, and lateral movement. Monitoring local admin group changes detects privilege escalation attacks.

## Value

Local admin privileges enable credential theft, persistence, and lateral movement. Monitoring local admin group changes detects privilege escalation attacks.

## Implementation

Enable Audit Security Group Management. Track additions (4732) and removals (4733) from the local Administrators group. Alert on any additions, especially by non-domain-admin accounts. Monitor for patterns: add user → perform action → remove user (cleanup). Correlate with LAPS password rotations and PAM solutions. On servers, local admin changes should be extremely rare.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_windows`.
• Ensure the following data sources are available: `sourcetype=WinEventLog:Security` (EventCode 4732, 4733).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Enable Audit Security Group Management. Track additions (4732) and removals (4733) from the local Administrators group. Alert on any additions, especially by non-domain-admin accounts. Monitor for patterns: add user → perform action → remove user (cleanup). Correlate with LAPS password rotations and PAM solutions. On servers, local admin changes should be extremely rare.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=wineventlog EventCode IN (4732, 4733) TargetUserName="Administrators"
| eval Action=case(EventCode=4732,"Member_Added", EventCode=4733,"Member_Removed", 1=1,"Other")
| table _time, host, Action, MemberName, MemberSid, SubjectUserName, SubjectDomainName
| sort -_time
```

Understanding this SPL

**Local Administrator Group Membership Changes** — Local admin privileges enable credential theft, persistence, and lateral movement. Monitoring local admin group changes detects privilege escalation attacks.

Documented **Data sources**: `sourcetype=WinEventLog:Security` (EventCode 4732, 4733). **App/TA** (typical add-on context): `Splunk_TA_windows`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: wineventlog.

**Pipeline walkthrough**

• Scopes the data: index=wineventlog. Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `eval` defines or adjusts **Action** — often to normalize units, derive a ratio, or prepare for thresholds.
• Pipeline stage (see **Local Administrator Group Membership Changes**): table _time, host, Action, MemberName, MemberSid, SubjectUserName, SubjectDomainName
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

**Local Administrator Group Membership Changes** — Local admin privileges enable credential theft, persistence, and lateral movement. Monitoring local admin group changes detects privilege escalation attacks.

Documented **Data sources**: `sourcetype=WinEventLog:Security` (EventCode 4732, 4733). **App/TA** (typical add-on context): `Splunk_TA_windows`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

This **CIM or accelerated** block uses normalized field names and/or `tstats` over data models. Enable **acceleration** on the referenced models (and correct CIM knowledge objects) or the search may return nothing.

**Pipeline walkthrough**

• Uses `tstats` against accelerated summaries for data model `Authentication.Authentication` — enable acceleration for that model.
• Applies an explicit `search` filter to narrow the current result set.

Enable Data Model Acceleration (and metric indexes for `mstats`) for the models or datasets referenced above; otherwise `tstats`/`mstats` may return no results from summaries.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (membership changes), Alert on all additions, Trend chart.

## SPL

```spl
index=wineventlog EventCode IN (4732, 4733) TargetUserName="Administrators"
| eval Action=case(EventCode=4732,"Member_Added", EventCode=4733,"Member_Removed", 1=1,"Other")
| table _time, host, Action, MemberName, MemberSid, SubjectUserName, SubjectDomainName
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

Table (membership changes), Alert on all additions, Trend chart.

## References

- [Enable Audit Security Group Management. Track additions](https://splunkbase.splunk.com/app/4732)
- [Splunk_TA_windows](https://splunkbase.splunk.com/app/742)
- [CIM: Authentication](https://docs.splunk.com/Documentation/CIM/latest/User/Authentication)
