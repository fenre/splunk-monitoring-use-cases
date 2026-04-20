---
id: "1.2.7"
title: "Account Lockout Tracking"
criticality: "high"
splunkPillar: "Security"
---

# UC-1.2.7 · Account Lockout Tracking

## Description

Lockouts frustrate users and can indicate active attacks. Identifying the source computer of the lockout dramatically speeds resolution.

## Value

Lockouts frustrate users and can indicate active attacks. Identifying the source computer of the lockout dramatically speeds resolution.

## Implementation

Collect Security logs from domain controllers (critical). The CallerComputerName field identifies which machine caused the lockout. Create alert per lockout and an aggregate alert for mass lockouts.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_windows`.
• Ensure the following data sources are available: `sourcetype=WinEventLog:Security`, EventCode=4740.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Collect Security logs from domain controllers (critical). The CallerComputerName field identifies which machine caused the lockout. Create alert per lockout and an aggregate alert for mass lockouts.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=wineventlog sourcetype="WinEventLog:Security" EventCode=4740
| table _time TargetUserName TargetDomainName CallerComputerName
| sort -_time
```

Understanding this SPL

**Account Lockout Tracking** — Lockouts frustrate users and can indicate active attacks. Identifying the source computer of the lockout dramatically speeds resolution.

Documented **Data sources**: `sourcetype=WinEventLog:Security`, EventCode=4740. **App/TA** (typical add-on context): `Splunk_TA_windows`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: wineventlog; **sourcetype**: WinEventLog:Security. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=wineventlog, sourcetype="WinEventLog:Security". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Pipeline stage (see **Account Lockout Tracking**): table _time TargetUserName TargetDomainName CallerComputerName
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

**Account Lockout Tracking** — Lockouts frustrate users and can indicate active attacks. Identifying the source computer of the lockout dramatically speeds resolution.

Documented **Data sources**: `sourcetype=WinEventLog:Security`, EventCode=4740. **App/TA** (typical add-on context): `Splunk_TA_windows`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

This **CIM or accelerated** block uses normalized field names and/or `tstats` over data models. Enable **acceleration** on the referenced models (and correct CIM knowledge objects) or the search may return nothing.

**Pipeline walkthrough**

• Uses `tstats` against accelerated summaries for data model `Authentication.Authentication` — enable acceleration for that model.
• Filters the current rows with `where count > 10` — typically the threshold or rule expression for this monitoring goal.

Enable Data Model Acceleration (and metric indexes for `mstats`) for the models or datasets referenced above; otherwise `tstats`/`mstats` may return no results from summaries.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (user, source computer, time), Single value (lockouts last 24h), Bar chart by user.

## SPL

```spl
index=wineventlog sourcetype="WinEventLog:Security" EventCode=4740
| table _time TargetUserName TargetDomainName CallerComputerName
| sort -_time
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

Table (user, source computer, time), Single value (lockouts last 24h), Bar chart by user.

## References

- [Splunk_TA_windows](https://splunkbase.splunk.com/app/742)
- [CIM: Authentication](https://docs.splunk.com/Documentation/CIM/latest/User/Authentication)
