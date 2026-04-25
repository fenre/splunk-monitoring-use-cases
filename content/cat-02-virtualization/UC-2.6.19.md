<!-- AUTO-GENERATED from UC-2.6.19.json — DO NOT EDIT -->

---
id: "2.6.19"
title: "Application Startup Duration Tracking"
criticality: "high"
splunkPillar: "Security"
---

# UC-2.6.19 · Application Startup Duration Tracking

## Description

How long applications take to become usable after launch directly impacts perceived performance. A user launching Outlook, SAP, or a browser expects it within seconds. uberAgent measures the time from process start to the application window being interactive, capturing real user-perceived startup times rather than just process creation. Slow startups indicate disk I/O contention, antivirus interference, or application configuration issues.

## Value

How long applications take to become usable after launch directly impacts perceived performance. A user launching Outlook, SAP, or a browser expects it within seconds. uberAgent measures the time from process start to the application window being interactive, capturing real user-perceived startup times rather than just process creation. Slow startups indicate disk I/O contention, antivirus interference, or application configuration issues.

## Implementation

uberAgent measures startup duration automatically for all applications. Baseline normal startup times per application. Alert when p95 startup exceeds thresholds (e.g., >10s for Outlook, >15s for SAP). Trend over time to detect regression after updates or image changes.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: uberAgent UXM (Splunkbase 1448).
• Ensure the following data sources are available: `sourcetype="uberAgent:Process:ProcessStartup"`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
uberAgent measures startup duration automatically for all applications. Baseline normal startup times per application. Alert when p95 startup exceeds thresholds (e.g., >10s for Outlook, >15s for SAP). Trend over time to detect regression after updates or image changes.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=uberagent sourcetype="uberAgent:Process:ProcessStartup" earliest=-24h
| stats avg(StartupTimeMs) as avg_startup_ms perc95(StartupTimeMs) as p95_startup_ms count as launches dc(User) as users by AppName
| eval avg_startup_sec=round(avg_startup_ms/1000,1), p95_startup_sec=round(p95_startup_ms/1000,1)
| where p95_startup_sec > 10
| sort -p95_startup_sec
| table AppName, launches, users, avg_startup_sec, p95_startup_sec
```

Understanding this SPL

**Application Startup Duration Tracking** — How long applications take to become usable after launch directly impacts perceived performance. A user launching Outlook, SAP, or a browser expects it within seconds. uberAgent measures the time from process start to the application window being interactive, capturing real user-perceived startup times rather than just process creation. Slow startups indicate disk I/O contention, antivirus interference, or application configuration issues.

Documented **Data sources**: `sourcetype="uberAgent:Process:ProcessStartup"`. **App/TA** (typical add-on context): uberAgent UXM (Splunkbase 1448). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: uberagent; **sourcetype**: uberAgent:Process:ProcessStartup. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=uberagent, sourcetype="uberAgent:Process:ProcessStartup", time bounds. Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `stats` rolls up events into metrics; results are split **by AppName** so each row reflects one combination of those dimensions.
• `eval` defines or adjusts **avg_startup_sec** — often to normalize units, derive a ratio, or prepare for thresholds.
• Filters the current rows with `where p95_startup_sec > 10` — typically the threshold or rule expression for this monitoring goal.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.
• Pipeline stage (see **Application Startup Duration Tracking**): table AppName, launches, users, avg_startup_sec, p95_startup_sec

Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Bar chart (p95 startup by app), Line chart (startup trending), Table (slowest applications).

## SPL

```spl
index=uberagent sourcetype="uberAgent:Process:ProcessStartup" earliest=-24h
| stats avg(StartupTimeMs) as avg_startup_ms perc95(StartupTimeMs) as p95_startup_ms count as launches dc(User) as users by AppName
| eval avg_startup_sec=round(avg_startup_ms/1000,1), p95_startup_sec=round(p95_startup_ms/1000,1)
| where p95_startup_sec > 10
| sort -p95_startup_sec
| table AppName, launches, users, avg_startup_sec, p95_startup_sec
```

## Visualization

Bar chart (p95 startup by app), Line chart (startup trending), Table (slowest applications).

## References

- [uberAgent UXM](https://splunkbase.splunk.com/app/1448)
