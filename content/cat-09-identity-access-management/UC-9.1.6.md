<!-- AUTO-GENERATED from UC-9.1.6.json — DO NOT EDIT -->

---
id: "9.1.6"
title: "Password Policy Violations"
criticality: "medium"
splunkPillar: "Security"
---

# UC-9.1.6 · Password Policy Violations

## Description

Failed password changes indicate users struggling with policy or potential social engineering. Monitoring supports security awareness.

## Value

Failed password changes indicate users struggling with policy or potential social engineering. Monitoring supports security awareness.

## Implementation

Forward DC Security logs. Track password change success/failure rates. Alert on excessive failures per user. Monitor 4724 (admin resets) separately as these bypass self-service and may indicate social engineering.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_windows`.
• Ensure the following data sources are available: Security Event Log (4723 — password change attempt, 4724 — password reset attempt).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Forward DC Security logs. Track password change success/failure rates. Alert on excessive failures per user. Monitor 4724 (admin resets) separately as these bypass self-service and may indicate social engineering.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=wineventlog sourcetype="WinEventLog:Security" EventCode IN (4723, 4724)
| stats count(eval(Keywords="Audit Failure")) as failures, count(eval(Keywords="Audit Success")) as successes by Account_Name
| where failures > 3
```

Understanding this SPL

**Password Policy Violations** — Failed password changes indicate users struggling with policy or potential social engineering. Monitoring supports security awareness.

Documented **Data sources**: Security Event Log (4723 — password change attempt, 4724 — password reset attempt). **App/TA** (typical add-on context): `Splunk_TA_windows`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: wineventlog; **sourcetype**: WinEventLog:Security. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=wineventlog, sourcetype="WinEventLog:Security". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `stats` rolls up events into metrics; results are split **by Account_Name** so each row reflects one combination of those dimensions.
• Filters the current rows with `where failures > 3` — typically the threshold or rule expression for this monitoring goal.

Optional CIM / accelerated variant (same use case, normalized fields via Common Information Model):

```spl
| tstats `summariesonly` count
  from datamodel=Authentication.Authentication
  where match(Authentication.signature, "4723|4724|4725") OR match(Authentication.vendor_action, "(?i)password")
  by Authentication.user Authentication.action span=1h
| sort -count
```

Understanding this CIM / accelerated SPL

**Password Policy Violations** — Failed password changes indicate users struggling with policy or potential social engineering. Monitoring supports security awareness.

Documented **Data sources**: Security Event Log (4723 — password change attempt, 4724 — password reset attempt). **App/TA** (typical add-on context): `Splunk_TA_windows`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

This **CIM or accelerated** block uses normalized field names and/or `tstats` over data models. Enable **acceleration** on the referenced models (and correct CIM knowledge objects) or the search may return nothing.

**Pipeline walkthrough**

• Uses `tstats` against accelerated summaries for data model `Authentication.Authentication` — enable acceleration for that model.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.

Enable Data Model Acceleration (and metric indexes for `mstats`) for the models or datasets referenced above; otherwise `tstats`/`mstats` may return no results from summaries.


Step 3 — Validate
Compare with Event Viewer on domain controllers (or exported Security logs) and with Active Directory Users and Computers for the same objects and time window.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (users with failures), Bar chart (failure rate by user), Pie chart (change vs reset).

## SPL

```spl
index=wineventlog sourcetype="WinEventLog:Security" EventCode IN (4723, 4724)
| stats count(eval(Keywords="Audit Failure")) as failures, count(eval(Keywords="Audit Success")) as successes by Account_Name
| where failures > 3
```

## CIM SPL

```spl
| tstats `summariesonly` count
  from datamodel=Authentication.Authentication
  where match(Authentication.signature, "4723|4724|4725") OR match(Authentication.vendor_action, "(?i)password")
  by Authentication.user Authentication.action span=1h
| sort -count
```

## Visualization

Table (users with failures), Bar chart (failure rate by user), Pie chart (change vs reset).

## References

- [Splunk_TA_windows](https://splunkbase.splunk.com/app/742)
- [CIM: Authentication](https://docs.splunk.com/Documentation/CIM/latest/User/Authentication)
