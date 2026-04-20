---
id: "9.1.5"
title: "Kerberos Ticket Anomalies"
criticality: "critical"
splunkPillar: "Security"
---

# UC-9.1.5 · Kerberos Ticket Anomalies

## Description

Detects Kerberoasting and Golden Ticket attacks, which are advanced AD compromise techniques. Essential for security monitoring.

## Value

Detects Kerberoasting and Golden Ticket attacks, which are advanced AD compromise techniques. Essential for security monitoring.

## Implementation

Forward 4768/4769 events from DCs. Detect Kerberoasting by filtering for RC4 encryption (0x17) on TGS requests. Detect Golden Ticket by looking for TGT requests with unusual encryption types or from non-DC sources.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_windows`.
• Ensure the following data sources are available: Security Event Log (4768 — TGT request, 4769 — TGS request).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Forward 4768/4769 events from DCs. Detect Kerberoasting by filtering for RC4 encryption (0x17) on TGS requests. Detect Golden Ticket by looking for TGT requests with unusual encryption types or from non-DC sources.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=wineventlog sourcetype="WinEventLog:Security" EventCode=4769 Ticket_Encryption_Type=0x17
| stats count by Account_Name, Service_Name
| where count > 5
| sort -count
```

Understanding this SPL

**Kerberos Ticket Anomalies** — Detects Kerberoasting and Golden Ticket attacks, which are advanced AD compromise techniques. Essential for security monitoring.

Documented **Data sources**: Security Event Log (4768 — TGT request, 4769 — TGS request). **App/TA** (typical add-on context): `Splunk_TA_windows`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: wineventlog; **sourcetype**: WinEventLog:Security. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=wineventlog, sourcetype="WinEventLog:Security". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `stats` rolls up events into metrics; results are split **by Account_Name, Service_Name** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• Filters the current rows with `where count > 5` — typically the threshold or rule expression for this monitoring goal.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.

Optional CIM / accelerated variant (same use case, normalized fields via Common Information Model):

```spl
| tstats `summariesonly` count
  from datamodel=Authentication.Authentication
  where match(Authentication.signature, "4768|4769|4771")
  by Authentication.user Authentication.src Authentication.action span=1h
| sort -count
```

Understanding this CIM / accelerated SPL

**Kerberos Ticket Anomalies** — Detects Kerberoasting and Golden Ticket attacks, which are advanced AD compromise techniques. Essential for security monitoring.

Documented **Data sources**: Security Event Log (4768 — TGT request, 4769 — TGS request). **App/TA** (typical add-on context): `Splunk_TA_windows`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

This **CIM or accelerated** block uses normalized field names and/or `tstats` over data models. Enable **acceleration** on the referenced models (and correct CIM knowledge objects) or the search may return nothing.

**Pipeline walkthrough**

• Uses `tstats` against accelerated summaries for data model `Authentication.Authentication` — enable acceleration for that model.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.

Enable Data Model Acceleration (and metric indexes for `mstats`) for the models or datasets referenced above; otherwise `tstats`/`mstats` may return no results from summaries.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (suspicious Kerberos requests), Bar chart (requests by encryption type), Timeline (anomalous events).

## SPL

```spl
index=wineventlog sourcetype="WinEventLog:Security" EventCode=4769 Ticket_Encryption_Type=0x17
| stats count by Account_Name, Service_Name
| where count > 5
| sort -count
```

## CIM SPL

```spl
| tstats `summariesonly` count
  from datamodel=Authentication.Authentication
  where match(Authentication.signature, "4768|4769|4771")
  by Authentication.user Authentication.src Authentication.action span=1h
| sort -count
```

## Visualization

Table (suspicious Kerberos requests), Bar chart (requests by encryption type), Timeline (anomalous events).

## Known False Positives

Administrative tasks, scheduled jobs or platform updates can match this pattern — correlate with change management, maintenance windows and user role before raising severity.

## References

- [Splunk_TA_windows](https://splunkbase.splunk.com/app/742)
- [CIM: Authentication](https://docs.splunk.com/Documentation/CIM/latest/User/Authentication)
