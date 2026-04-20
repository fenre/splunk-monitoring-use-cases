---
id: "9.7.4"
title: "Service Account Usage Trending"
criticality: "medium"
splunkPillar: "Security"
---

# UC-9.7.4 · Service Account Usage Trending

## Description

Service accounts should authenticate in predictable volumes from known automation. A dormant account suddenly trending upward may indicate compromise, scope creep, or shadow IT scripts. Ninety-day views expose slow burns and seasonal batch jobs alike.

## Value

Service accounts should authenticate in predictable volumes from known automation. A dormant account suddenly trending upward may indicate compromise, scope creep, or shadow IT scripts. Ninety-day views expose slow burns and seasonal batch jobs alike.

## Implementation

Populate the lookup from AD and cloud app registrations; treat unknown machine accounts carefully. Baseline expected daily volume per account in a separate panel if volumes differ widely. Alert when a low-volume account crosses its historical band or when the aggregate trend jumps after no change tickets. Cross-check with password last set and owner field.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: Splunk Common Information Model (CIM), Splunk Add-on for Microsoft Windows (`Splunk_TA_windows`).
• Ensure the following data sources are available: `Authentication` data model; `service_accounts.csv` lookup (`Account_Name`, `account_type`) or naming convention `svc_*` / `service_*`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Populate the lookup from AD and cloud app registrations; treat unknown machine accounts carefully. Baseline expected daily volume per account in a separate panel if volumes differ widely. Alert when a low-volume account crosses its historical band or when the aggregate trend jumps after no change tickets. Cross-check with password last set and owner field.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
| tstats `summariesonly` count
  from datamodel=Authentication.Authentication
  where earliest=-90d@d latest=@d
  by _time span=1d Authentication.user
| lookup service_accounts.csv Account_Name AS "Authentication.user" OUTPUT account_type
| eval is_service=if(account_type="service" OR match(lower('Authentication.user'),"^(svc|service)[-_].*"),1,0)
| where is_service=1
| timechart span=1d sum(count) as service_auth_volume
| trendline sma7(service_auth_volume) as svc_sma7
| predict service_auth_volume as svc_forecast algorithm=LLP future_timespan=14
```

Understanding this SPL

**Service Account Usage Trending** — Service accounts should authenticate in predictable volumes from known automation. A dormant account suddenly trending upward may indicate compromise, scope creep, or shadow IT scripts. Ninety-day views expose slow burns and seasonal batch jobs alike.

Documented **Data sources**: `Authentication` data model; `service_accounts.csv` lookup (`Account_Name`, `account_type`) or naming convention `svc_*` / `service_*`. **App/TA** (typical add-on context): Splunk Common Information Model (CIM), Splunk Add-on for Microsoft Windows (`Splunk_TA_windows`). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

**Pipeline walkthrough**

• Uses `tstats` against accelerated summaries for data model `Authentication.Authentication` — enable acceleration for that model.
• Enriches events using `lookup` (lookup definition + optional OUTPUT fields).
• `eval` defines or adjusts **is_service** — often to normalize units, derive a ratio, or prepare for thresholds.
• Filters the current rows with `where is_service=1` — typically the threshold or rule expression for this monitoring goal.
• `timechart` plots the metric over time using **span=1d** buckets — ideal for trending and alerting on this use case.
• Pipeline stage (see **Service Account Usage Trending**): trendline sma7(service_auth_volume) as svc_sma7
• Pipeline stage (see **Service Account Usage Trending**): predict service_auth_volume as svc_forecast algorithm=LLP future_timespan=14

Optional CIM / accelerated variant (same use case, normalized fields via Common Information Model):

```spl
| tstats summariesonly=t count from datamodel=Authentication.Authentication by Authentication.user span=1d | sort - count
```

Understanding this CIM / accelerated SPL

**Service Account Usage Trending** — Service accounts should authenticate in predictable volumes from known automation. A dormant account suddenly trending upward may indicate compromise, scope creep, or shadow IT scripts. Ninety-day views expose slow burns and seasonal batch jobs alike.

Documented **Data sources**: `Authentication` data model; `service_accounts.csv` lookup (`Account_Name`, `account_type`) or naming convention `svc_*` / `service_*`. **App/TA** (typical add-on context): Splunk Common Information Model (CIM), Splunk Add-on for Microsoft Windows (`Splunk_TA_windows`). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

This **CIM or accelerated** block uses normalized field names and/or `tstats` over data models. Enable **acceleration** on the referenced models (and correct CIM knowledge objects) or the search may return nothing.

**Pipeline walkthrough**

• Uses `tstats` against accelerated summaries for data model `Authentication.Authentication` — enable acceleration for that model.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.

Enable Data Model Acceleration (and metric indexes for `mstats`) for the models or datasets referenced above; otherwise `tstats`/`mstats` may return no results from summaries.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Line chart with SMA and forecast; small multiples per high-risk service account if volume allows.

## SPL

```spl
| tstats `summariesonly` count
  from datamodel=Authentication.Authentication
  where earliest=-90d@d latest=@d
  by _time span=1d Authentication.user
| lookup service_accounts.csv Account_Name AS "Authentication.user" OUTPUT account_type
| eval is_service=if(account_type="service" OR match(lower('Authentication.user'),"^(svc|service)[-_].*"),1,0)
| where is_service=1
| timechart span=1d sum(count) as service_auth_volume
| trendline sma7(service_auth_volume) as svc_sma7
| predict service_auth_volume as svc_forecast algorithm=LLP future_timespan=14
```

## CIM SPL

```spl
| tstats summariesonly=t count from datamodel=Authentication.Authentication by Authentication.user span=1d | sort - count
```

## Visualization

Line chart with SMA and forecast; small multiples per high-risk service account if volume allows.

## Known False Positives

Administrative tasks, scheduled jobs or platform updates can match this pattern — correlate with change management, maintenance windows and user role before raising severity.

## References

- [Splunk_TA_windows](https://splunkbase.splunk.com/app/742)
- [CIM: Authentication](https://docs.splunk.com/Documentation/CIM/latest/User/Authentication)
