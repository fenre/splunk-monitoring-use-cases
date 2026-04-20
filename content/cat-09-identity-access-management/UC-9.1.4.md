---
id: "9.1.4"
title: "Service Account Anomalies"
criticality: "critical"
splunkPillar: "Security"
---

# UC-9.1.4 · Service Account Anomalies

## Description

Service accounts used interactively or from unexpected hosts indicate compromise. Detection prevents lateral movement.

## Value

Service accounts used interactively or from unexpected hosts indicate compromise. Detection prevents lateral movement.

## Implementation

Maintain lookup of service accounts with expected Logon Types and source hosts. Alert on interactive logon (Type 2, 10) or unexpected source. Regularly audit service account inventory with AD queries.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_windows`.
• Ensure the following data sources are available: Security Event Log (4624 — successful logon, Logon Type field).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Maintain lookup of service accounts with expected Logon Types and source hosts. Alert on interactive logon (Type 2, 10) or unexpected source. Regularly audit service account inventory with AD queries.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=wineventlog sourcetype="WinEventLog:Security" EventCode=4624
| lookup service_accounts.csv Account_Name OUTPUT expected_hosts, account_type
| where account_type="service" AND (Logon_Type=2 OR Logon_Type=10 OR NOT match(src_host, expected_hosts))
| table _time, Account_Name, Logon_Type, src_host
```

Understanding this SPL

**Service Account Anomalies** — Service accounts used interactively or from unexpected hosts indicate compromise. Detection prevents lateral movement.

Documented **Data sources**: Security Event Log (4624 — successful logon, Logon Type field). **App/TA** (typical add-on context): `Splunk_TA_windows`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: wineventlog; **sourcetype**: WinEventLog:Security. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=wineventlog, sourcetype="WinEventLog:Security". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Enriches events using `lookup` (lookup definition + optional OUTPUT fields).
• Filters the current rows with `where account_type="service" AND (Logon_Type=2 OR Logon_Type=10 OR NOT match(src_host, expected_hosts))` — typically the threshold or rule expression for this monitoring goal.
• Pipeline stage (see **Service Account Anomalies**): table _time, Account_Name, Logon_Type, src_host

Optional CIM / accelerated variant (same use case, normalized fields via Common Information Model):

```spl
| tstats `summariesonly` count
  from datamodel=Authentication.Authentication
  where Authentication.action="success" AND match(Authentication.user, "(?i)svc|service|_sa$")
  by Authentication.user Authentication.src Authentication.app span=1h
| sort -count
```

Understanding this CIM / accelerated SPL

**Service Account Anomalies** — Service accounts used interactively or from unexpected hosts indicate compromise. Detection prevents lateral movement.

Documented **Data sources**: Security Event Log (4624 — successful logon, Logon Type field). **App/TA** (typical add-on context): `Splunk_TA_windows`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

This **CIM or accelerated** block uses normalized field names and/or `tstats` over data models. Enable **acceleration** on the referenced models (and correct CIM knowledge objects) or the search may return nothing.

**Pipeline walkthrough**

• Uses `tstats` against accelerated summaries for data model `Authentication.Authentication` — enable acceleration for that model.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.

Enable Data Model Acceleration (and metric indexes for `mstats`) for the models or datasets referenced above; otherwise `tstats`/`mstats` may return no results from summaries.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (anomalous service account usage), Timeline (events), Bar chart (anomalies by account).

## SPL

```spl
index=wineventlog sourcetype="WinEventLog:Security" EventCode=4624
| lookup service_accounts.csv Account_Name OUTPUT expected_hosts, account_type
| where account_type="service" AND (Logon_Type=2 OR Logon_Type=10 OR NOT match(src_host, expected_hosts))
| table _time, Account_Name, Logon_Type, src_host
```

## CIM SPL

```spl
| tstats `summariesonly` count
  from datamodel=Authentication.Authentication
  where Authentication.action="success" AND match(Authentication.user, "(?i)svc|service|_sa$")
  by Authentication.user Authentication.src Authentication.app span=1h
| sort -count
```

## Visualization

Table (anomalous service account usage), Timeline (events), Bar chart (anomalies by account).

## Known False Positives

Administrative tasks, scheduled jobs or platform updates can match this pattern — correlate with change management, maintenance windows and user role before raising severity.

## References

- [Splunk_TA_windows](https://splunkbase.splunk.com/app/742)
- [CIM: Authentication](https://docs.splunk.com/Documentation/CIM/latest/User/Authentication)
