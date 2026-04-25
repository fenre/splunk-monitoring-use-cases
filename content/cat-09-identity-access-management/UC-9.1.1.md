<!-- AUTO-GENERATED from UC-9.1.1.json — DO NOT EDIT -->

---
id: "9.1.1"
title: "Brute-Force Login Detection"
criticality: "critical"
splunkPillar: "Security"
---

# UC-9.1.1 · Brute-Force Login Detection

## Description

Brute-force attacks are a primary credential compromise vector. Early detection prevents account takeover.

## Value

Brute-force attacks are a primary credential compromise vector. Early detection prevents account takeover.

## Implementation

Deploy the Universal Forwarder on all Domain Controllers with `[WinEventLog://Security]` enabled. Ensure the GPO enables Audit Logon Success and Failure. Alert with `stats count by Account_Name, src span=15m` when count exceeds 10. Suppress break-glass and service accounts via a `privileged_accounts` lookup to reduce false positives.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_windows`.
• Ensure the following data sources are available: Windows Security Event Log (Event ID 4625 — failed logon).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Deploy the Universal Forwarder on all Domain Controllers with `[WinEventLog://Security]` enabled. Ensure the GPO enables Audit Logon Success and Failure. Alert with `stats count by Account_Name, src span=15m` when count exceeds 10. Suppress break-glass and service accounts via a `privileged_accounts` lookup to reduce false positives.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=wineventlog sourcetype="WinEventLog:Security" EventCode=4625
| stats count by Account_Name, Source_Network_Address
| where count > 10
| sort -count
```

Understanding this SPL

**Brute-Force Login Detection** — Brute-force attacks are a primary credential compromise vector. Early detection prevents account takeover.

Documented **Data sources**: Windows Security Event Log (Event ID 4625 — failed logon). **App/TA** (typical add-on context): `Splunk_TA_windows`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: wineventlog; **sourcetype**: WinEventLog:Security. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=wineventlog, sourcetype="WinEventLog:Security". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `stats` rolls up events into metrics; results are split **by Account_Name, Source_Network_Address** so each row reflects one combination of those dimensions.
• Filters the current rows with `where count > 10` — typically the threshold or rule expression for this monitoring goal.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.

Optional CIM / accelerated variant (same use case, normalized fields via Common Information Model):

```spl
| tstats `summariesonly` count
  from datamodel=Authentication.Authentication
  where Authentication.action="failure"
  by Authentication.user Authentication.src span=1h
| where count > 10
```

Understanding this CIM / accelerated SPL

**Brute-Force Login Detection** — Brute-force attacks are a primary credential compromise vector. Early detection prevents account takeover.

Documented **Data sources**: Windows Security Event Log (Event ID 4625 — failed logon). **App/TA** (typical add-on context): `Splunk_TA_windows`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

This **CIM or accelerated** block uses normalized field names and/or `tstats` over data models. Enable **acceleration** on the referenced models (and correct CIM knowledge objects) or the search may return nothing.

**Pipeline walkthrough**

• Uses `tstats` against accelerated summaries for data model `Authentication.Authentication` — enable acceleration for that model.
• Filters the current rows with `where count > 10` — typically the threshold or rule expression for this monitoring goal.

Enable Data Model Acceleration (and metric indexes for `mstats`) for the models or datasets referenced above; otherwise `tstats`/`mstats` may return no results from summaries.


Step 3 — Validate
Compare with Event Viewer on domain controllers (or exported Security logs) and with Active Directory Users and Computers for the same objects and time window.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (accounts with failure counts), Line chart (failure rate over time), Geo map (source IPs).

## SPL

```spl
index=wineventlog sourcetype="WinEventLog:Security" EventCode=4625
| stats count by Account_Name, Source_Network_Address
| where count > 10
| sort -count
```

## CIM SPL

```spl
| tstats `summariesonly` count
  from datamodel=Authentication.Authentication
  where Authentication.action="failure"
  by Authentication.user,Authentication.src span=1h
| where count > 10
```

## Visualization

Table (accounts with failure counts), Line chart (failure rate over time), Geo map (source IPs).

## References

- [Splunk_TA_windows](https://splunkbase.splunk.com/app/742)
- [CIM: Authentication](https://docs.splunk.com/Documentation/CIM/latest/User/Authentication)
