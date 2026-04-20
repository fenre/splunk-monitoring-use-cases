---
id: "1.2.78"
title: "DSRM Account Usage"
criticality: "critical"
splunkPillar: "Security"
---

# UC-1.2.78 · DSRM Account Usage

## Description

The Directory Services Restore Mode (DSRM) account is a local admin on every DC with a rarely-changed password. Its use outside restores indicates compromise.

## Value

The Directory Services Restore Mode (DSRM) account is a local admin on every DC with a rarely-changed password. Its use outside restores indicates compromise.

## Implementation

EventCode 4794=DSRM password change (should only happen during planned maintenance). DSRM logons appear as local "Administrator" logons on the DC. Since Windows Server 2008 R2, registry key DsrmAdminLogonBehavior allows DSRM logon while AD is running (value=2). Alert on any DSRM password change and any local admin logon to a DC. Set DsrmAdminLogonBehavior=0 (default, deny DSRM logon while AD running).

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_windows`.
• Ensure the following data sources are available: `sourcetype=WinEventLog:Security` (EventCode 4794, 4624 with DSRM).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
EventCode 4794=DSRM password change (should only happen during planned maintenance). DSRM logons appear as local "Administrator" logons on the DC. Since Windows Server 2008 R2, registry key DsrmAdminLogonBehavior allows DSRM logon while AD is running (value=2). Alert on any DSRM password change and any local admin logon to a DC. Set DsrmAdminLogonBehavior=0 (default, deny DSRM logon while AD running).

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=wineventlog sourcetype="WinEventLog:Security"
  (EventCode=4794 OR (EventCode=4624 TargetUserName="Administrator" LogonType=10 AuthenticationPackageName="Negotiate"))
| eval alert_type=case(EventCode=4794,"DSRM password changed",EventCode=4624,"Possible DSRM logon")
| table _time, host, alert_type, SubjectUserName, IpAddress
| sort -_time
```

Understanding this SPL

**DSRM Account Usage** — The Directory Services Restore Mode (DSRM) account is a local admin on every DC with a rarely-changed password. Its use outside restores indicates compromise.

Documented **Data sources**: `sourcetype=WinEventLog:Security` (EventCode 4794, 4624 with DSRM). **App/TA** (typical add-on context): `Splunk_TA_windows`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: wineventlog; **sourcetype**: WinEventLog:Security. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=wineventlog, sourcetype="WinEventLog:Security". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `eval` defines or adjusts **alert_type** — often to normalize units, derive a ratio, or prepare for thresholds.
• Pipeline stage (see **DSRM Account Usage**): table _time, host, alert_type, SubjectUserName, IpAddress
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (DSRM events), Single value (count — target: 0 outside restore operations), Alert.

## SPL

```spl
index=wineventlog sourcetype="WinEventLog:Security"
  (EventCode=4794 OR (EventCode=4624 TargetUserName="Administrator" LogonType=10 AuthenticationPackageName="Negotiate"))
| eval alert_type=case(EventCode=4794,"DSRM password changed",EventCode=4624,"Possible DSRM logon")
| table _time, host, alert_type, SubjectUserName, IpAddress
| sort -_time
```

## Visualization

Table (DSRM events), Single value (count — target: 0 outside restore operations), Alert.

## References

- [Splunk_TA_windows](https://splunkbase.splunk.com/app/742)
