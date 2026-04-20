---
id: "1.2.86"
title: "NTLM Audit and Restriction Monitoring"
criticality: "medium"
splunkPillar: "Security"
---

# UC-1.2.86 · NTLM Audit and Restriction Monitoring

## Description

NTLM is a legacy authentication protocol vulnerable to relay attacks. Auditing NTLM usage identifies applications and systems that need migration to Kerberos.

## Value

NTLM is a legacy authentication protocol vulnerable to relay attacks. Auditing NTLM usage identifies applications and systems that need migration to Kerberos.

## Implementation

Enable NTLM auditing via GPO: Network Security → Restrict NTLM → Audit incoming/outgoing NTLM traffic. EventCode 8001=outgoing NTLM, 8003=incoming NTLM to server, 8004=NTLM blocked. Start in audit mode to identify all NTLM-dependent applications before enabling blocking. Goal: reduce NTLM usage to zero where possible, using Kerberos for all domain authentication.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_windows`.
• Ensure the following data sources are available: `sourcetype=WinEventLog:Security` (EventCode 4776), `sourcetype=WinEventLog:Microsoft-Windows-NTLM/Operational` (EventCode 8001, 8003, 8004).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Enable NTLM auditing via GPO: Network Security → Restrict NTLM → Audit incoming/outgoing NTLM traffic. EventCode 8001=outgoing NTLM, 8003=incoming NTLM to server, 8004=NTLM blocked. Start in audit mode to identify all NTLM-dependent applications before enabling blocking. Goal: reduce NTLM usage to zero where possible, using Kerberos for all domain authentication.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=wineventlog source="WinEventLog:Microsoft-Windows-NTLM/Operational"
  EventCode IN (8001, 8003, 8004)
| stats count by TargetName, DomainName, WorkstationName
| sort -count
```

Understanding this SPL

**NTLM Audit and Restriction Monitoring** — NTLM is a legacy authentication protocol vulnerable to relay attacks. Auditing NTLM usage identifies applications and systems that need migration to Kerberos.

Documented **Data sources**: `sourcetype=WinEventLog:Security` (EventCode 4776), `sourcetype=WinEventLog:Microsoft-Windows-NTLM/Operational` (EventCode 8001, 8003, 8004). **App/TA** (typical add-on context): `Splunk_TA_windows`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: wineventlog.

**Pipeline walkthrough**

• Scopes the data: index=wineventlog. Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `stats` rolls up events into metrics; results are split **by TargetName, DomainName, WorkstationName** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
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

**NTLM Audit and Restriction Monitoring** — NTLM is a legacy authentication protocol vulnerable to relay attacks. Auditing NTLM usage identifies applications and systems that need migration to Kerberos.

Documented **Data sources**: `sourcetype=WinEventLog:Security` (EventCode 4776), `sourcetype=WinEventLog:Microsoft-Windows-NTLM/Operational` (EventCode 8001, 8003, 8004). **App/TA** (typical add-on context): `Splunk_TA_windows`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

This **CIM or accelerated** block uses normalized field names and/or `tstats` over data models. Enable **acceleration** on the referenced models (and correct CIM knowledge objects) or the search may return nothing.

**Pipeline walkthrough**

• Uses `tstats` against accelerated summaries for data model `Authentication.Authentication` — enable acceleration for that model.
• Filters the current rows with `where count > 5` — typically the threshold or rule expression for this monitoring goal.

Enable Data Model Acceleration (and metric indexes for `mstats`) for the models or datasets referenced above; otherwise `tstats`/`mstats` may return no results from summaries.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Bar chart (top NTLM sources/destinations), Timechart (NTLM vs Kerberos ratio), Table (NTLM-dependent applications).

## SPL

```spl
index=wineventlog source="WinEventLog:Microsoft-Windows-NTLM/Operational"
  EventCode IN (8001, 8003, 8004)
| stats count by TargetName, DomainName, WorkstationName
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

Bar chart (top NTLM sources/destinations), Timechart (NTLM vs Kerberos ratio), Table (NTLM-dependent applications).

## References

- [Splunk_TA_windows](https://splunkbase.splunk.com/app/742)
- [CIM: Authentication](https://docs.splunk.com/Documentation/CIM/latest/User/Authentication)
