<!-- AUTO-GENERATED from UC-1.2.49.json — DO NOT EDIT -->

---
id: "1.2.49"
title: "Lateral Movement via Explicit Credentials"
criticality: "critical"
splunkPillar: "Security"
---

# UC-1.2.49 · Lateral Movement via Explicit Credentials

## Description

Logon type 9 (NewCredentials / RunAs /netonly) and type 10 (RDP) from unexpected sources reveal credential abuse and lateral movement between systems.

## Value

This pattern is a Tier-0 hunting bread crumb—triage with your identity and admin-exposure program, not a raw count only.

## Implementation

Collect Security logs from all servers. Logon type 9=NewCredentials (runas /netonly — commonly used with stolen hashes), type 10=RemoteInteractive (RDP). Focus on admin accounts authenticating to servers they don't normally access. Build a baseline of normal admin→server mappings. Alert when an admin authenticates to >3 new hosts in an hour. Correlate with process creation (4688) on the destination.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_windows`.
• Ensure the following data sources are available: `sourcetype=WinEventLog:Security` (EventCode 4624, Logon Type 3, 9, 10).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Collect Security logs from all servers. Logon type 9=NewCredentials (runas /netonly — commonly used with stolen hashes), type 10=RemoteInteractive (RDP). Focus on admin accounts authenticating to servers they don't normally access. Build a baseline of normal admin→server mappings. Alert when an admin authenticates to >3 new hosts in an hour. Correlate with process creation (4688) on the destination.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=wineventlog sourcetype="WinEventLog:Security" EventCode=4624 LogonType IN (9, 10)
| stats count values(LogonType) as types by TargetUserName, IpAddress, host
| where count > 5
| lookup admin_accounts.csv user as TargetUserName OUTPUT is_admin
| where is_admin="true"
| sort -count
```

Understanding this SPL

**Lateral Movement via Explicit Credentials** — Logon type 9 (NewCredentials / RunAs /netonly) and type 10 (RDP) from unexpected sources reveal credential abuse and lateral movement between systems.

Documented **Data sources**: `sourcetype=WinEventLog:Security` (EventCode 4624, Logon Type 3, 9, 10). **App/TA** (typical add-on context): `Splunk_TA_windows`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: wineventlog; **sourcetype**: WinEventLog:Security. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=wineventlog, sourcetype="WinEventLog:Security". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `stats` rolls up events into metrics; results are split **by TargetUserName, IpAddress, host** so each row reflects one combination of those dimensions.
• Filters the current rows with `where count > 5` — typically the threshold or rule expression for this monitoring goal.
• Enriches events using `lookup` (lookup definition + optional OUTPUT fields).
• Filters the current rows with `where is_admin="true"` — typically the threshold or rule expression for this monitoring goal.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.

Optional CIM / accelerated variant (same use case, normalized fields via Common Information Model):

```spl
| tstats `summariesonly` count
  from datamodel=Authentication where nodename=Authentication
  by Authentication.user Authentication.src Authentication.dest span=1h
| where count>0
```

Understanding this CIM / accelerated SPL

**Lateral Movement via Explicit Credentials** — Logon type 9 (NewCredentials / RunAs /netonly) and type 10 (RDP) from unexpected sources reveal credential abuse and lateral movement between systems.

Documented **Data sources**: `sourcetype=WinEventLog:Security` (EventCode 4624, Logon Type 3, 9, 10). **App/TA** (typical add-on context): `Splunk_TA_windows`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

This **CIM or accelerated** block uses normalized field names and/or `tstats` over data models. Enable **acceleration** on the referenced models (and correct CIM knowledge objects) or the search may return nothing.

**Pipeline walkthrough**

• Uses `tstats` against accelerated summaries for data model `Authentication.Authentication` — enable acceleration for that model.
• Filters the current rows with `where count > 5` — typically the threshold or rule expression for this monitoring goal.

Enable Data Model Acceleration (and metric indexes for `mstats`) for the models or datasets referenced above; otherwise `tstats`/`mstats` may return no results from summaries.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Network graph (source→destination), Table (unusual logons), Timechart (logon rate by type).

## SPL

```spl
index=wineventlog sourcetype="WinEventLog:Security" EventCode=4624 LogonType IN (9, 10)
| stats count values(LogonType) as types by TargetUserName, IpAddress, host
| where count > 5
| lookup admin_accounts.csv user as TargetUserName OUTPUT is_admin
| where is_admin="true"
| sort -count
```

## CIM SPL

```spl
| tstats `summariesonly` count
  from datamodel=Authentication where nodename=Authentication
  by Authentication.user Authentication.src Authentication.dest span=1h
| where count>0
```

## Visualization

Network graph (source→destination), Table (unusual logons), Timechart (logon rate by type).

## References

- [new hosts in an hour. Correlate with process creation](https://splunkbase.splunk.com/app/4688)
- [Splunk_TA_windows](https://splunkbase.splunk.com/app/742)
- [CIM: Authentication](https://docs.splunk.com/Documentation/CIM/latest/User/Authentication)
