---
id: "9.7.6"
title: "Password Reset Volume Trending"
criticality: "medium"
splunkPillar: "Security"
---

# UC-9.7.6 · Password Reset Volume Trending

## Description

Sudden increases in password resets—self-service or helpdesk—often align with phishing waves, credential stuffing after a breach, or attacker-driven resets. A ninety-day trend with a moving average makes campaign-scale activity visible before individual tickets pile up.

## Value

Sudden increases in password resets—self-service or helpdesk—often align with phishing waves, credential stuffing after a breach, or attacker-driven resets. A ninety-day trend with a moving average makes campaign-scale activity visible before individual tickets pile up.

## Implementation

Normalize multiple sources into one panel or use `eval source_system` before `stats`. Exclude routine bulk resets from known automation via a lookup of service accounts or change windows. When the SMA breaches a static or adaptive threshold, open a phishing hunt and check MFA and impossible-travel dashboards. Add helpdesk ticket volume from ITSM if self-service is low but calls spike.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: Splunk Add-on for Microsoft Windows (`Splunk_TA_windows`), Okta Add-on for Splunk, Splunk Add-on for ServiceNow or your ITSM (optional).
• Ensure the following data sources are available: AD Security log `EventCode` 4724 (password reset attempt); `index=okta` `sourcetype=Okta:system` password reset events; ITSM `category=password` incidents.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Normalize multiple sources into one panel or use `eval source_system` before `stats`. Exclude routine bulk resets from known automation via a lookup of service accounts or change windows. When the SMA breaches a static or adaptive threshold, open a phishing hunt and check MFA and impossible-travel dashboards. Add helpdesk ticket volume from ITSM if self-service is low but calls spike.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
(index=wineventlog sourcetype="WinEventLog:Security" EventCode=4724 earliest=-90d@d)
 OR (index=okta sourcetype=Okta:system EVENT_TYPE=user.account.reset_password earliest=-90d@d)
| bin _time span=1d
| stats count as reset_volume by _time
| sort _time
| trendline sma7(reset_volume) as reset_sma7
| predict reset_volume as reset_forecast algorithm=LLP future_timespan=7
```

Understanding this SPL

**Password Reset Volume Trending** — Sudden increases in password resets—self-service or helpdesk—often align with phishing waves, credential stuffing after a breach, or attacker-driven resets. A ninety-day trend with a moving average makes campaign-scale activity visible before individual tickets pile up.

Documented **Data sources**: AD Security log `EventCode` 4724 (password reset attempt); `index=okta` `sourcetype=Okta:system` password reset events; ITSM `category=password` incidents. **App/TA** (typical add-on context): Splunk Add-on for Microsoft Windows (`Splunk_TA_windows`), Okta Add-on for Splunk, Splunk Add-on for ServiceNow or your ITSM (optional). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: wineventlog, okta; **sourcetype**: WinEventLog:Security, Okta:system. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=wineventlog, index=okta, sourcetype="WinEventLog:Security", time bounds. Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Discretizes time or numeric ranges with `bin`/`bucket`.
• `stats` rolls up events into metrics; results are split **by _time** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.
• Pipeline stage (see **Password Reset Volume Trending**): trendline sma7(reset_volume) as reset_sma7
• Pipeline stage (see **Password Reset Volume Trending**): predict reset_volume as reset_forecast algorithm=LLP future_timespan=7


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Column or line chart of daily reset_volume with SMA; optional forecast ribbon.

## SPL

```spl
(index=wineventlog sourcetype="WinEventLog:Security" EventCode=4724 earliest=-90d@d)
 OR (index=okta sourcetype=Okta:system EVENT_TYPE=user.account.reset_password earliest=-90d@d)
| bin _time span=1d
| stats count as reset_volume by _time
| sort _time
| trendline sma7(reset_volume) as reset_sma7
| predict reset_volume as reset_forecast algorithm=LLP future_timespan=7
```

## Visualization

Column or line chart of daily reset_volume with SMA; optional forecast ribbon.

## Known False Positives

Administrative tasks, scheduled jobs or platform updates can match this pattern — correlate with change management, maintenance windows and user role before raising severity.

## References

- [Splunk_TA_windows](https://splunkbase.splunk.com/app/742)
- [Splunk Add-on for ServiceNow](https://splunkbase.splunk.com/app/1928)
