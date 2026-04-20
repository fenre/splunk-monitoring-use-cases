---
id: "1.2.65"
title: "Pass-the-Hash / NTLM Relay Detection"
criticality: "critical"
splunkPillar: "Security"
---

# UC-1.2.65 · Pass-the-Hash / NTLM Relay Detection

## Description

Pass-the-hash attacks use stolen NTLM hashes to authenticate without knowing the password. Detecting NTLM logons from unusual sources catches this common lateral movement technique.

## Value

Pass-the-hash attacks use stolen NTLM hashes to authenticate without knowing the password. Detecting NTLM logons from unusual sources catches this common lateral movement technique.

## Implementation

NTLM type 3 (network) logons from non-standard sources indicate pass-the-hash. In environments enforcing Kerberos, any NTLM logon to a server is suspicious. Focus on admin accounts using NTLM to access multiple hosts. EventCode 4776 on the DC shows the NTLM validation. Remediation: enable "Restrict NTLM" GPO settings, enforce Kerberos, deploy Credential Guard. MITRE ATT&CK T1550.002.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_windows`.
• Ensure the following data sources are available: `sourcetype=WinEventLog:Security` (EventCode 4624, LogonType 3, AuthenticationPackageName=NTLM).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
NTLM type 3 (network) logons from non-standard sources indicate pass-the-hash. In environments enforcing Kerberos, any NTLM logon to a server is suspicious. Focus on admin accounts using NTLM to access multiple hosts. EventCode 4776 on the DC shows the NTLM validation. Remediation: enable "Restrict NTLM" GPO settings, enforce Kerberos, deploy Credential Guard. MITRE ATT&CK T1550.002.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=wineventlog sourcetype="WinEventLog:Security" EventCode=4624 LogonType=3
  AuthenticationPackageName="NTLM" TargetUserName!="ANONYMOUS LOGON"
| stats count dc(host) as target_hosts values(host) as targets by TargetUserName, IpAddress
| where target_hosts > 3
| sort -target_hosts
```

Understanding this SPL

**Pass-the-Hash / NTLM Relay Detection** — Pass-the-hash attacks use stolen NTLM hashes to authenticate without knowing the password. Detecting NTLM logons from unusual sources catches this common lateral movement technique.

Documented **Data sources**: `sourcetype=WinEventLog:Security` (EventCode 4624, LogonType 3, AuthenticationPackageName=NTLM). **App/TA** (typical add-on context): `Splunk_TA_windows`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: wineventlog; **sourcetype**: WinEventLog:Security. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=wineventlog, sourcetype="WinEventLog:Security". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `stats` rolls up events into metrics; results are split **by TargetUserName, IpAddress** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• Filters the current rows with `where target_hosts > 3` — typically the threshold or rule expression for this monitoring goal.
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

**Pass-the-Hash / NTLM Relay Detection** — Pass-the-hash attacks use stolen NTLM hashes to authenticate without knowing the password. Detecting NTLM logons from unusual sources catches this common lateral movement technique.

Documented **Data sources**: `sourcetype=WinEventLog:Security` (EventCode 4624, LogonType 3, AuthenticationPackageName=NTLM). **App/TA** (typical add-on context): `Splunk_TA_windows`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

This **CIM or accelerated** block uses normalized field names and/or `tstats` over data models. Enable **acceleration** on the referenced models (and correct CIM knowledge objects) or the search may return nothing.

**Pipeline walkthrough**

• Uses `tstats` against accelerated summaries for data model `Authentication.Authentication` — enable acceleration for that model.
• Filters the current rows with `where count > 5` — typically the threshold or rule expression for this monitoring goal.

Enable Data Model Acceleration (and metric indexes for `mstats`) for the models or datasets referenced above; otherwise `tstats`/`mstats` may return no results from summaries.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (NTLM logons from suspicious sources), Network graph (source→targets), Timeline, Single value (NTLM vs Kerberos ratio).

## SPL

```spl
index=wineventlog sourcetype="WinEventLog:Security" EventCode=4624 LogonType=3
  AuthenticationPackageName="NTLM" TargetUserName!="ANONYMOUS LOGON"
| stats count dc(host) as target_hosts values(host) as targets by TargetUserName, IpAddress
| where target_hosts > 3
| sort -target_hosts
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

Table (NTLM logons from suspicious sources), Network graph (source→targets), Timeline, Single value (NTLM vs Kerberos ratio).

## References

- [Splunk_TA_windows](https://splunkbase.splunk.com/app/742)
- [CIM: Authentication](https://docs.splunk.com/Documentation/CIM/latest/User/Authentication)
