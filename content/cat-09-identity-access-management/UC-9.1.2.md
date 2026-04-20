---
id: "9.1.2"
title: "Account Lockout Monitoring"
criticality: "high"
splunkPillar: "Security"
---

# UC-9.1.2 · Account Lockout Monitoring

## Description

Lockouts cause user productivity loss and help desk load. Source identification enables rapid resolution.

## Value

Lockouts cause user productivity loss and help desk load. Source identification enables rapid resolution.

## Implementation

Forward DC Security logs. Alert on each lockout with source workstation included. Create report of recurring lockouts for proactive investigation. Correlate with 4625 events to find the failing source.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_windows`.
• Ensure the following data sources are available: Security Event Log (Event ID 4740 — account locked out).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Forward DC Security logs. Alert on each lockout with source workstation included. Create report of recurring lockouts for proactive investigation. Correlate with 4625 events to find the failing source.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=wineventlog sourcetype="WinEventLog:Security" EventCode=4740
| table _time, Account_Name, CallerComputerName
| sort -_time
```

Understanding this SPL

**Account Lockout Monitoring** — Lockouts cause user productivity loss and help desk load. Source identification enables rapid resolution.

Documented **Data sources**: Security Event Log (Event ID 4740 — account locked out). **App/TA** (typical add-on context): `Splunk_TA_windows`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: wineventlog; **sourcetype**: WinEventLog:Security. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=wineventlog, sourcetype="WinEventLog:Security". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Pipeline stage (see **Account Lockout Monitoring**): table _time, Account_Name, CallerComputerName
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.

Optional CIM / accelerated variant (same use case, normalized fields via Common Information Model):

```spl
| tstats `summariesonly` count
  from datamodel=Authentication.Authentication
  where match(Authentication.signature, "4740") OR match(Authentication.vendor_action, "(?i)lockout")
  by Authentication.user Authentication.src span=1h
| sort -count
```

Understanding this CIM / accelerated SPL

**Account Lockout Monitoring** — Lockouts cause user productivity loss and help desk load. Source identification enables rapid resolution.

Documented **Data sources**: Security Event Log (Event ID 4740 — account locked out). **App/TA** (typical add-on context): `Splunk_TA_windows`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

This **CIM or accelerated** block uses normalized field names and/or `tstats` over data models. Enable **acceleration** on the referenced models (and correct CIM knowledge objects) or the search may return nothing.

**Pipeline walkthrough**

• Uses `tstats` against accelerated summaries for data model `Authentication.Authentication` — enable acceleration for that model.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.

Enable Data Model Acceleration (and metric indexes for `mstats`) for the models or datasets referenced above; otherwise `tstats`/`mstats` may return no results from summaries.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (lockouts with source), Bar chart (top locked accounts), Line chart (lockout trend).

## SPL

```spl
index=wineventlog sourcetype="WinEventLog:Security" EventCode=4740
| table _time, Account_Name, CallerComputerName
| sort -_time
```

## CIM SPL

```spl
| tstats `summariesonly` count
  from datamodel=Authentication.Authentication
  where match(Authentication.signature, "4740") OR match(Authentication.vendor_action, "(?i)lockout")
  by Authentication.user Authentication.src span=1h
| sort -count
```

## Visualization

Table (lockouts with source), Bar chart (top locked accounts), Line chart (lockout trend).

## Known False Positives

Administrative tasks, scheduled jobs or platform updates can match this pattern — correlate with change management, maintenance windows and user role before raising severity.

## References

- [Splunk_TA_windows](https://splunkbase.splunk.com/app/742)
- [CIM: Authentication](https://docs.splunk.com/Documentation/CIM/latest/User/Authentication)
