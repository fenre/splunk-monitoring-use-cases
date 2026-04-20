---
id: "9.7.1"
title: "Authentication Volume Trending"
criticality: "medium"
splunkPillar: "Security"
---

# UC-9.7.1 · Authentication Volume Trending

## Description

Daily authentication success and failure volumes show whether login load, credential attacks, or misconfiguration are drifting over a quarter. A seven-day moving average smooths weekly noise so you can spot sustained shifts before they overwhelm help desks or mask intrusions.

## Value

Daily authentication success and failure volumes show whether login load, credential attacks, or misconfiguration are drifting over a quarter. A seven-day moving average smooths weekly noise so you can spot sustained shifts before they overwhelm help desks or mask intrusions.

## Implementation

Accelerate the Authentication data model and confirm identity sources are tagged to CIM. Schedule the search over `-90d` with daily `span` for executive and SOC review dashboards. Treat a rising failure trend with flat success as password-spray or IdP issues; rising both may indicate bulk user or application changes. Tune out known maintenance windows with a time-bound macro if needed.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: Splunk Common Information Model (CIM), Splunk Add-on for Microsoft Windows (`Splunk_TA_windows`), Splunk Add-on for Microsoft Cloud Services (`Splunk_TA_microsoft-cloudservices`), Okta Add-on for Splunk.
• Ensure the following data sources are available: `Authentication` data model (accelerated); underlying `sourcetype` values such as `WinEventLog:Security`, `azure:aad:signin`, `Okta:im` / `OktaIM2`, `duo` (normalized to CIM Authentication).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Accelerate the Authentication data model and confirm identity sources are tagged to CIM. Schedule the search over `-90d` with daily `span` for executive and SOC review dashboards. Treat a rising failure trend with flat success as password-spray or IdP issues; rising both may indicate bulk user or application changes. Tune out known maintenance windows with a time-bound macro if needed.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
| tstats `summariesonly` count
  from datamodel=Authentication.Authentication
  where earliest=-90d@d latest=@d
  by _time span=1d Authentication.action
| rename "Authentication.action" as action
| timechart span=1d sum(count) by action
| trendline sma7(success) as success_sma7 sma7(failure) as failure_sma7
| predict failure as failure_forecast algorithm=LLP future_timespan=7
```

Understanding this SPL

**Authentication Volume Trending** — Daily authentication success and failure volumes show whether login load, credential attacks, or misconfiguration are drifting over a quarter. A seven-day moving average smooths weekly noise so you can spot sustained shifts before they overwhelm help desks or mask intrusions.

Documented **Data sources**: `Authentication` data model (accelerated); underlying `sourcetype` values such as `WinEventLog:Security`, `azure:aad:signin`, `Okta:im` / `OktaIM2`, `duo` (normalized to CIM Authentication). **App/TA** (typical add-on context): Splunk Common Information Model (CIM), Splunk Add-on for Microsoft Windows (`Splunk_TA_windows`), Splunk Add-on for Microsoft Cloud Services (`Splunk_TA_microsoft-cloudservices`), Okta Add-on for Splunk. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

**Pipeline walkthrough**

• Uses `tstats` against accelerated summaries for data model `Authentication.Authentication` — enable acceleration for that model.
• Renames fields with `rename` for clarity or joins.
• `timechart` plots the metric over time using **span=1d** buckets with a separate series **by action** — ideal for trending and alerting on this use case.
• Pipeline stage (see **Authentication Volume Trending**): trendline sma7(success) as success_sma7 sma7(failure) as failure_sma7
• Pipeline stage (see **Authentication Volume Trending**): predict failure as failure_forecast algorithm=LLP future_timespan=7

Optional CIM / accelerated variant (same use case, normalized fields via Common Information Model):

```spl
| tstats summariesonly=t count from datamodel=Authentication.Authentication by Authentication.action span=1d | sort - count
```

Understanding this CIM / accelerated SPL

**Authentication Volume Trending** — Daily authentication success and failure volumes show whether login load, credential attacks, or misconfiguration are drifting over a quarter. A seven-day moving average smooths weekly noise so you can spot sustained shifts before they overwhelm help desks or mask intrusions.

Documented **Data sources**: `Authentication` data model (accelerated); underlying `sourcetype` values such as `WinEventLog:Security`, `azure:aad:signin`, `Okta:im` / `OktaIM2`, `duo` (normalized to CIM Authentication). **App/TA** (typical add-on context): Splunk Common Information Model (CIM), Splunk Add-on for Microsoft Windows (`Splunk_TA_windows`), Splunk Add-on for Microsoft Cloud Services (`Splunk_TA_microsoft-cloudservices`), Okta Add-on for Splunk. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

This **CIM or accelerated** block uses normalized field names and/or `tstats` over data models. Enable **acceleration** on the referenced models (and correct CIM knowledge objects) or the search may return nothing.

**Pipeline walkthrough**

• Uses `tstats` against accelerated summaries for data model `Authentication.Authentication` — enable acceleration for that model.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.

Enable Data Model Acceleration (and metric indexes for `mstats`) for the models or datasets referenced above; otherwise `tstats`/`mstats` may return no results from summaries.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Multi-series line or area chart (success vs failure vs SMA); optional overlay for short-term forecast.

## SPL

```spl
| tstats `summariesonly` count
  from datamodel=Authentication.Authentication
  where earliest=-90d@d latest=@d
  by _time span=1d Authentication.action
| rename "Authentication.action" as action
| timechart span=1d sum(count) by action
| trendline sma7(success) as success_sma7 sma7(failure) as failure_sma7
| predict failure as failure_forecast algorithm=LLP future_timespan=7
```

## CIM SPL

```spl
| tstats summariesonly=t count from datamodel=Authentication.Authentication by Authentication.action span=1d | sort - count
```

## Visualization

Multi-series line or area chart (success vs failure vs SMA); optional overlay for short-term forecast.

## Known False Positives

Administrative tasks, scheduled jobs or platform updates can match this pattern — correlate with change management, maintenance windows and user role before raising severity.

## References

- [Splunk_TA_windows](https://splunkbase.splunk.com/app/742)
- [Splunk_TA_microsoft-cloudservices](https://splunkbase.splunk.com/app/3110)
- [CIM: Authentication](https://docs.splunk.com/Documentation/CIM/latest/User/Authentication)
