---
id: "2.6.23"
title: "Application Crash and Error Reporting"
criticality: "high"
splunkPillar: "Security"
---

# UC-2.6.23 · Application Crash and Error Reporting

## Description

Application crashes in Citrix sessions cause data loss, user frustration, and helpdesk calls. uberAgent captures Windows Error Reporting (WER) crash data including the faulting module, exception code, and application version, enabling crash trending and root-cause identification across the fleet. Crash rate spikes after application or image updates indicate problematic deployments.

## Value

Application crashes in Citrix sessions cause data loss, user frustration, and helpdesk calls. uberAgent captures Windows Error Reporting (WER) crash data including the faulting module, exception code, and application version, enabling crash trending and root-cause identification across the fleet. Crash rate spikes after application or image updates indicate problematic deployments.

## Implementation

uberAgent captures crash data automatically from WER. Trend crash rates per application version to detect regressions. Alert on crash rate spikes (>200% increase over 7-day baseline). Correlate exception codes with known bugs and vendor advisories. Track crash resolution over time after patching.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: uberAgent UXM (Splunkbase 1448).
• Ensure the following data sources are available: `sourcetype="uberAgent:Application:Errors"`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
uberAgent captures crash data automatically from WER. Trend crash rates per application version to detect regressions. Alert on crash rate spikes (>200% increase over 7-day baseline). Correlate exception codes with known bugs and vendor advisories. Track crash resolution over time after patching.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=uberagent sourcetype="uberAgent:Application:Errors" earliest=-7d
| stats count as crashes dc(User) as affected_users values(ExceptionCode) as exception_codes by AppName, AppVersion
| sort -crashes
| table AppName, AppVersion, crashes, affected_users, exception_codes
```

Understanding this SPL

**Application Crash and Error Reporting** — Application crashes in Citrix sessions cause data loss, user frustration, and helpdesk calls. uberAgent captures Windows Error Reporting (WER) crash data including the faulting module, exception code, and application version, enabling crash trending and root-cause identification across the fleet. Crash rate spikes after application or image updates indicate problematic deployments.

Documented **Data sources**: `sourcetype="uberAgent:Application:Errors"`. **App/TA** (typical add-on context): uberAgent UXM (Splunkbase 1448). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: uberagent; **sourcetype**: uberAgent:Application:Errors. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=uberagent, sourcetype="uberAgent:Application:Errors", time bounds. Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `stats` rolls up events into metrics; results are split **by AppName, AppVersion** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.
• Pipeline stage (see **Application Crash and Error Reporting**): table AppName, AppVersion, crashes, affected_users, exception_codes


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Bar chart (crashes by application), Line chart (crash rate trending), Table (faulting modules).

## SPL

```spl
index=uberagent sourcetype="uberAgent:Application:Errors" earliest=-7d
| stats count as crashes dc(User) as affected_users values(ExceptionCode) as exception_codes by AppName, AppVersion
| sort -crashes
| table AppName, AppVersion, crashes, affected_users, exception_codes
```

## Visualization

Bar chart (crashes by application), Line chart (crash rate trending), Table (faulting modules).

## References

- [uberAgent UXM](https://splunkbase.splunk.com/app/1448)
