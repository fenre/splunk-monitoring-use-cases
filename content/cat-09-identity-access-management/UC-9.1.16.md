---
id: "9.1.16"
title: "Golden Ticket Indicators"
criticality: "critical"
splunkPillar: "Security"
---

# UC-9.1.16 · Golden Ticket Indicators

## Description

Forged TGTs often produce anomalous ticket lifetimes, encryption types, or DC sourcing. Heuristic alerts support hunt teams when krbtgt may be compromised.

## Value

Forged TGTs often produce anomalous ticket lifetimes, encryption types, or DC sourcing. Heuristic alerts support hunt teams when krbtgt may be compromised.

## Implementation

Baseline normal TGT lifetimes and encryption types per domain. Alert on unusual lifetimes, unknown ETYPE, or TGT requests not originating from expected workstations. Correlate with 4624 type 10 and lateral movement analytics.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_windows`.
• Ensure the following data sources are available: Security Event Log (4768 — Kerberos authentication ticket requested), 4624 (logon type 10 with Kerberos).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Baseline normal TGT lifetimes and encryption types per domain. Alert on unusual lifetimes, unknown ETYPE, or TGT requests not originating from expected workstations. Correlate with 4624 type 10 and lateral movement analytics.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=wineventlog sourcetype="WinEventLog:Security" EventCode=4768
| eval ticket_life_h=(Ticket_Lifetime/3600)
| where ticket_life_h > 10 OR Ticket_Encryption_Type IN ("0xffffffff","0x12")
| table _time, Account_Name, Ticket_Encryption_Type, ticket_life_h, IpAddress
```

Understanding this SPL

**Golden Ticket Indicators** — Forged TGTs often produce anomalous ticket lifetimes, encryption types, or DC sourcing. Heuristic alerts support hunt teams when krbtgt may be compromised.

Documented **Data sources**: Security Event Log (4768 — Kerberos authentication ticket requested), 4624 (logon type 10 with Kerberos). **App/TA** (typical add-on context): `Splunk_TA_windows`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: wineventlog; **sourcetype**: WinEventLog:Security. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=wineventlog, sourcetype="WinEventLog:Security". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `eval` defines or adjusts **ticket_life_h** — often to normalize units, derive a ratio, or prepare for thresholds.
• Filters the current rows with `where ticket_life_h > 10 OR Ticket_Encryption_Type IN ("0xffffffff","0x12")` — typically the threshold or rule expression for this monitoring goal.
• Pipeline stage (see **Golden Ticket Indicators**): table _time, Account_Name, Ticket_Encryption_Type, ticket_life_h, IpAddress

Optional CIM / accelerated variant (same use case, normalized fields via Common Information Model):

```spl
| tstats summariesonly=t count from datamodel=Authentication.Authentication by Authentication.action, Authentication.user, Authentication.src | sort - count
```

Understanding this CIM / accelerated SPL

**Golden Ticket Indicators** — Forged TGTs often produce anomalous ticket lifetimes, encryption types, or DC sourcing. Heuristic alerts support hunt teams when krbtgt may be compromised.

Documented **Data sources**: Security Event Log (4768 — Kerberos authentication ticket requested), 4624 (logon type 10 with Kerberos). **App/TA** (typical add-on context): `Splunk_TA_windows`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

This **CIM or accelerated** block uses normalized field names and/or `tstats` over data models. Enable **acceleration** on the referenced models (and correct CIM knowledge objects) or the search may return nothing.

**Pipeline walkthrough**

• Uses `tstats` against accelerated summaries for data model `Authentication.Authentication` — enable acceleration for that model.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.

Enable Data Model Acceleration (and metric indexes for `mstats`) for the models or datasets referenced above; otherwise `tstats`/`mstats` may return no results from summaries.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (suspicious TGT events), Timeline, Single value (anomalies per day).

## SPL

```spl
index=wineventlog sourcetype="WinEventLog:Security" EventCode=4768
| eval ticket_life_h=(Ticket_Lifetime/3600)
| where ticket_life_h > 10 OR Ticket_Encryption_Type IN ("0xffffffff","0x12")
| table _time, Account_Name, Ticket_Encryption_Type, ticket_life_h, IpAddress
```

## CIM SPL

```spl
| tstats summariesonly=t count from datamodel=Authentication.Authentication by Authentication.action, Authentication.user, Authentication.src | sort - count
```

## Visualization

Table (suspicious TGT events), Timeline, Single value (anomalies per day).

## Known False Positives

Administrative tasks, scheduled jobs or platform updates can match this pattern — correlate with change management, maintenance windows and user role before raising severity.

## References

- [Splunk_TA_windows](https://splunkbase.splunk.com/app/742)
- [CIM: Authentication](https://docs.splunk.com/Documentation/CIM/latest/User/Authentication)
