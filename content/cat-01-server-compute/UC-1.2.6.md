<!-- AUTO-GENERATED from UC-1.2.6.json — DO NOT EDIT -->

---
id: "1.2.6"
title: "Failed Login Monitoring"
criticality: "high"
splunkPillar: "Security"
---

# UC-1.2.6 · Failed Login Monitoring

## Description

Detects credential stuffing, brute-force attacks, and compromised account usage. Key for security monitoring and compliance.

## Value

You get an early sign of brute force or broken automation before a valid login succeeds or the account locks out everywhere.

## Implementation

Enable Security Event Log collection (already default in most deployments). Create alert for >10 failures from single source in 5 minutes. Correlate with successful logins (4624) from same source.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_windows`.
• Ensure the following data sources are available: `sourcetype=WinEventLog:Security`, EventCode=4625.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Enable Security Event Log collection (already default in most deployments). Create alert for >10 failures from single source in 5 minutes. Correlate with successful logins (4624) from same source.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=wineventlog sourcetype="WinEventLog:Security" EventCode=4625
| eval src=coalesce(src, IpAddress)
| stats count as failures, dc(TargetUserName) as accounts_targeted, values(TargetUserName) as usernames by src, host
| where failures > 10
| sort -failures
| iplocation src
```

Understanding this SPL

**Failed Login Monitoring** — Detects credential stuffing, brute-force attacks, and compromised account usage. Key for security monitoring and compliance.

Documented **Data sources**: `sourcetype=WinEventLog:Security`, EventCode=4625. **App/TA** (typical add-on context): `Splunk_TA_windows`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: wineventlog; **sourcetype**: WinEventLog:Security. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=wineventlog, sourcetype="WinEventLog:Security". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `eval` defines or adjusts **src** — often to normalize units, derive a ratio, or prepare for thresholds.
• `stats` rolls up events into metrics; results are split **by src, host** so each row reflects one combination of those dimensions.
• Filters the current rows with `where failures > 10` — typically the threshold or rule expression for this monitoring goal.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.
• Pipeline stage (see **Failed Login Monitoring**): iplocation src

Optional CIM / accelerated variant (same use case, normalized fields via Common Information Model):

```spl
| tstats `summariesonly` count
  from datamodel=Authentication where nodename=Authentication
  where Authentication.action=failure
  by Authentication.user Authentication.src Authentication.dest
| where count > 10
```

Understanding this CIM / accelerated SPL

**Failed Login Monitoring** — Detects credential stuffing, brute-force attacks, and compromised account usage. Key for security monitoring and compliance.

Documented **Data sources**: `sourcetype=WinEventLog:Security`, EventCode=4625. **App/TA** (typical add-on context): `Splunk_TA_windows`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

This **CIM or accelerated** block uses normalized field names and/or `tstats` over data models. Enable **acceleration** on the referenced models (and correct CIM knowledge objects) or the search may return nothing.

**Pipeline walkthrough**

• Uses `tstats` against accelerated summaries for data model `Authentication.Authentication` — enable acceleration for that model.
• Filters the current rows with `where count > 10` — typically the threshold or rule expression for this monitoring goal.

Enable Data Model Acceleration (and metric indexes for `mstats`) for the models or datasets referenced above; otherwise `tstats`/`mstats` may return no results from summaries.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (source, failures, targets), Map (GeoIP), Timechart of failure trends.

## SPL

```spl
index=wineventlog sourcetype="WinEventLog:Security" EventCode=4625
| eval src=coalesce(src, IpAddress)
| stats count as failures, dc(TargetUserName) as accounts_targeted, values(TargetUserName) as usernames by src, host
| where failures > 10
| sort -failures
| iplocation src
```

## CIM SPL

```spl
| tstats `summariesonly` count
  from datamodel=Authentication where nodename=Authentication
  where Authentication.action=failure
  by Authentication.user Authentication.src Authentication.dest
| where count > 10
```

## Visualization

Table (source, failures, targets), Map (GeoIP), Timechart of failure trends.

## References

- [Splunk_TA_windows](https://splunkbase.splunk.com/app/742)
- [CIM: Authentication](https://docs.splunk.com/Documentation/CIM/latest/User/Authentication)
