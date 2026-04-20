---
id: "2.6.18"
title: "Application Unresponsiveness (UI Hangs) Detection"
criticality: "high"
splunkPillar: "Security"
---

# UC-2.6.18 · Application Unresponsiveness (UI Hangs) Detection

## Description

Application hangs — where the UI becomes unresponsive and shows "Not Responding" — are a major source of user frustration in CVAD sessions. Unlike crashes, hangs don't generate Windows Error Reporting events and are invisible to most monitoring tools. uberAgent detects them in real-time by monitoring message pump responsiveness, capturing which application hung, for how long, and what the user was doing.

## Value

Application hangs — where the UI becomes unresponsive and shows "Not Responding" — are a major source of user frustration in CVAD sessions. Unlike crashes, hangs don't generate Windows Error Reporting events and are invisible to most monitoring tools. uberAgent detects them in real-time by monitoring message pump responsiveness, capturing which application hung, for how long, and what the user was doing.

## Implementation

uberAgent detects UI unresponsiveness automatically. No special configuration required. Use the data to identify problematic applications, correlate hangs with VDA resource contention (CPU, memory), and prioritise application remediation. Alert when a single application generates more than 20 hangs per hour across the fleet.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: uberAgent UXM (Splunkbase 1448).
• Ensure the following data sources are available: `sourcetype="uberAgent:Application:UIDelay"`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
uberAgent detects UI unresponsiveness automatically. No special configuration required. Use the data to identify problematic applications, correlate hangs with VDA resource contention (CPU, memory), and prioritise application remediation. Alert when a single application generates more than 20 hangs per hour across the fleet.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=uberagent sourcetype="uberAgent:Application:UIDelay" earliest=-24h
| stats count as hang_count avg(UIDelayDurationMs) as avg_hang_ms max(UIDelayDurationMs) as max_hang_ms dc(User) as affected_users by AppName, AppVersion
| where hang_count > 5
| eval avg_hang_sec=round(avg_hang_ms/1000,1)
| sort -hang_count
| table AppName, AppVersion, hang_count, avg_hang_sec, affected_users
```

Understanding this SPL

**Application Unresponsiveness (UI Hangs) Detection** — Application hangs — where the UI becomes unresponsive and shows "Not Responding" — are a major source of user frustration in CVAD sessions. Unlike crashes, hangs don't generate Windows Error Reporting events and are invisible to most monitoring tools. uberAgent detects them in real-time by monitoring message pump responsiveness, capturing which application hung, for how long, and what the user was doing.

Documented **Data sources**: `sourcetype="uberAgent:Application:UIDelay"`. **App/TA** (typical add-on context): uberAgent UXM (Splunkbase 1448). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: uberagent; **sourcetype**: uberAgent:Application:UIDelay. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=uberagent, sourcetype="uberAgent:Application:UIDelay", time bounds. Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `stats` rolls up events into metrics; results are split **by AppName, AppVersion** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• Filters the current rows with `where hang_count > 5` — typically the threshold or rule expression for this monitoring goal.
• `eval` defines or adjusts **avg_hang_sec** — often to normalize units, derive a ratio, or prepare for thresholds.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.
• Pipeline stage (see **Application Unresponsiveness (UI Hangs) Detection**): table AppName, AppVersion, hang_count, avg_hang_sec, affected_users


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Bar chart (hangs by application), Line chart (hang frequency over time), Table (worst applications with user impact).

## SPL

```spl
index=uberagent sourcetype="uberAgent:Application:UIDelay" earliest=-24h
| stats count as hang_count avg(UIDelayDurationMs) as avg_hang_ms max(UIDelayDurationMs) as max_hang_ms dc(User) as affected_users by AppName, AppVersion
| where hang_count > 5
| eval avg_hang_sec=round(avg_hang_ms/1000,1)
| sort -hang_count
| table AppName, AppVersion, hang_count, avg_hang_sec, affected_users
```

## Visualization

Bar chart (hangs by application), Line chart (hang frequency over time), Table (worst applications with user impact).

## References

- [uberAgent UXM](https://splunkbase.splunk.com/app/1448)
