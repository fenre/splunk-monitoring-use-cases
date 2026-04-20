---
id: "9.2.9"
title: "LDAP Signing Enforcement"
criticality: "high"
splunkPillar: "Security"
---

# UC-9.2.9 · LDAP Signing Enforcement

## Description

Unsigned LDAP binds expose credentials to interception. Tracking enforcement and bind failures ensures GPO and domain controller settings are effective.

## Value

Unsigned LDAP binds expose credentials to interception. Tracking enforcement and bind failures ensures GPO and domain controller settings are effective.

## Implementation

Enable LDAP signing requirements via GPO. Alert on sustained unsigned binds from specific apps; work with owners to enable signing/TLS. Do not alert on one-off legacy until remediated.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_windows`.
• Ensure the following data sources are available: Directory Service event log (2886 — unsigned LDAP bind, 2887 — unsigned SASL).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Enable LDAP signing requirements via GPO. Alert on sustained unsigned binds from specific apps; work with owners to enable signing/TLS. Do not alert on one-off legacy until remediated.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=wineventlog sourcetype="WinEventLog:Directory Service" EventCode IN (2886,2887)
| stats count by ComputerName, EventCode, Client_IP
| where count > 10
| sort -count
```

Understanding this SPL

**LDAP Signing Enforcement** — Unsigned LDAP binds expose credentials to interception. Tracking enforcement and bind failures ensures GPO and domain controller settings are effective.

Documented **Data sources**: Directory Service event log (2886 — unsigned LDAP bind, 2887 — unsigned SASL). **App/TA** (typical add-on context): `Splunk_TA_windows`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: wineventlog; **sourcetype**: WinEventLog:Directory Service. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=wineventlog, sourcetype="WinEventLog:Directory Service". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `stats` rolls up events into metrics; results are split **by ComputerName, EventCode, Client_IP** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• Filters the current rows with `where count > 10` — typically the threshold or rule expression for this monitoring goal.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.

Optional CIM / accelerated variant (same use case, normalized fields via Common Information Model):

```spl
| tstats summariesonly=t count from datamodel=Authentication.Authentication by Authentication.src | sort - count
```

Understanding this CIM / accelerated SPL

**LDAP Signing Enforcement** — Unsigned LDAP binds expose credentials to interception. Tracking enforcement and bind failures ensures GPO and domain controller settings are effective.

Documented **Data sources**: Directory Service event log (2886 — unsigned LDAP bind, 2887 — unsigned SASL). **App/TA** (typical add-on context): `Splunk_TA_windows`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

This **CIM or accelerated** block uses normalized field names and/or `tstats` over data models. Enable **acceleration** on the referenced models (and correct CIM knowledge objects) or the search may return nothing.

**Pipeline walkthrough**

• Uses `tstats` against accelerated summaries for data model `Authentication.Authentication` — enable acceleration for that model.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.

Enable Data Model Acceleration (and metric indexes for `mstats`) for the models or datasets referenced above; otherwise `tstats`/`mstats` may return no results from summaries.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (clients with unsigned binds), Bar chart (by subnet), Line chart (trend toward zero).

## SPL

```spl
index=wineventlog sourcetype="WinEventLog:Directory Service" EventCode IN (2886,2887)
| stats count by ComputerName, EventCode, Client_IP
| where count > 10
| sort -count
```

## CIM SPL

```spl
| tstats summariesonly=t count from datamodel=Authentication.Authentication by Authentication.src | sort - count
```

## Visualization

Table (clients with unsigned binds), Bar chart (by subnet), Line chart (trend toward zero).

## Known False Positives

Administrative tasks, scheduled jobs or platform updates can match this pattern — correlate with change management, maintenance windows and user role before raising severity.

## References

- [Splunk_TA_windows](https://splunkbase.splunk.com/app/742)
- [CIM: Authentication](https://docs.splunk.com/Documentation/CIM/latest/User/Authentication)
