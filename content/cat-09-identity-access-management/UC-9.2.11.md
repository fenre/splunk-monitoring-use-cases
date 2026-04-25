<!-- AUTO-GENERATED from UC-9.2.11.json — DO NOT EDIT -->

---
id: "9.2.11"
title: "LDAP Channel Binding Status"
criticality: "high"
splunkPillar: "Security"
---

# UC-9.2.11 · LDAP Channel Binding Status

## Description

Channel binding tokens for LDAP/SASL mitigate relay attacks; monitoring confirms clients meet `ldapEnforceChannelBinding` policy.

## Value

Channel binding tokens for LDAP/SASL mitigate relay attacks; monitoring confirms clients meet `ldapEnforceChannelBinding` policy.

## Implementation

Phase enforcement with reporting mode first. Identify legacy apps from Client_IP. Alert when moving to enforced mode and failures persist.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_windows`.
• Ensure the following data sources are available: Directory Service (3039 — rejected bind missing channel binding tokens when required).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Phase enforcement with reporting mode first. Identify legacy apps from Client_IP. Alert when moving to enforced mode and failures persist.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=wineventlog sourcetype="WinEventLog:Directory Service" EventCode=3039
| stats count by ComputerName, Client_IP
| where count > 5
| sort -count
```

Understanding this SPL

**LDAP Channel Binding Status** — Channel binding tokens for LDAP/SASL mitigate relay attacks; monitoring confirms clients meet `ldapEnforceChannelBinding` policy.

Documented **Data sources**: Directory Service (3039 — rejected bind missing channel binding tokens when required). **App/TA** (typical add-on context): `Splunk_TA_windows`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: wineventlog; **sourcetype**: WinEventLog:Directory Service. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=wineventlog, sourcetype="WinEventLog:Directory Service". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `stats` rolls up events into metrics; results are split **by ComputerName, Client_IP** so each row reflects one combination of those dimensions.
• Filters the current rows with `where count > 5` — typically the threshold or rule expression for this monitoring goal.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.

Optional CIM / accelerated variant (same use case, normalized fields via Common Information Model):

```spl
| tstats summariesonly=t count from datamodel=Authentication.Authentication by Authentication.src | sort - count
```

Understanding this CIM / accelerated SPL

**LDAP Channel Binding Status** — Channel binding tokens for LDAP/SASL mitigate relay attacks; monitoring confirms clients meet `ldapEnforceChannelBinding` policy.

Documented **Data sources**: Directory Service (3039 — rejected bind missing channel binding tokens when required). **App/TA** (typical add-on context): `Splunk_TA_windows`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

This **CIM or accelerated** block uses normalized field names and/or `tstats` over data models. Enable **acceleration** on the referenced models (and correct CIM knowledge objects) or the search may return nothing.

**Pipeline walkthrough**

• Uses `tstats` against accelerated summaries for data model `Authentication.Authentication` — enable acceleration for that model.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.

Enable Data Model Acceleration (and metric indexes for `mstats`) for the models or datasets referenced above; otherwise `tstats`/`mstats` may return no results from summaries.


Step 3 — Validate
Compare with Event Viewer on domain controllers (or exported Security logs) and with Active Directory Users and Computers for the same objects and time window.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (clients failing channel binding), Bar chart (by application owner), Line chart (remediation trend).

## SPL

```spl
index=wineventlog sourcetype="WinEventLog:Directory Service" EventCode=3039
| stats count by ComputerName, Client_IP
| where count > 5
| sort -count
```

## CIM SPL

```spl
| tstats summariesonly=t count from datamodel=Authentication.Authentication by Authentication.src | sort - count
```

## Visualization

Table (clients failing channel binding), Bar chart (by application owner), Line chart (remediation trend).

## References

- [Splunk_TA_windows](https://splunkbase.splunk.com/app/742)
- [CIM: Authentication](https://docs.splunk.com/Documentation/CIM/latest/User/Authentication)
