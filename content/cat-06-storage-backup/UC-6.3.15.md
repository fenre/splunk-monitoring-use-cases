---
id: "6.3.15"
title: "DR Rehearsal Tracking"
criticality: "high"
splunkPillar: "Observability"
---

# UC-6.3.15 · DR Rehearsal Tracking

## Description

Tabletop and technical DR tests must occur on schedule. Tracking rehearsal outcomes and dates supports audit and readiness scoring.

## Value

Tabletop and technical DR tests must occur on schedule. Tracking rehearsal outcomes and dates supports audit and readiness scoring.

## Implementation

Log each rehearsal with scenario, duration, pass/fail. Alert when annual test is overdue or result is not Pass. Correlate with actual restore tests from backup tools.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: Custom (ITSM, spreadsheet ingest, HEC).
• Ensure the following data sources are available: DR test results, DR runbook completion events.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Log each rehearsal with scenario, duration, pass/fail. Alert when annual test is overdue or result is not Pass. Correlate with actual restore tests from backup tools.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=backup sourcetype="dr_rehearsal"
| stats latest(test_date) as last_test, latest(result) as result by system_name, scenario
| eval days_since=round((now()-strptime(last_test,"%Y-%m-%d"))/86400)
| where days_since > 365 OR result!="Pass"
| table system_name scenario last_test result days_since
```

Understanding this SPL

**DR Rehearsal Tracking** — Tabletop and technical DR tests must occur on schedule. Tracking rehearsal outcomes and dates supports audit and readiness scoring.

Documented **Data sources**: DR test results, DR runbook completion events. **App/TA** (typical add-on context): Custom (ITSM, spreadsheet ingest, HEC). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: backup; **sourcetype**: dr_rehearsal. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=backup, sourcetype="dr_rehearsal". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `stats` rolls up events into metrics; results are split **by system_name, scenario** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• `eval` defines or adjusts **days_since** — often to normalize units, derive a ratio, or prepare for thresholds.
• Filters the current rows with `where days_since > 365 OR result!="Pass"` — typically the threshold or rule expression for this monitoring goal.
• Pipeline stage (see **DR Rehearsal Tracking**): table system_name scenario last_test result days_since


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (overdue systems), Calendar (scheduled tests), Single value (% scenarios current).

## SPL

```spl
index=backup sourcetype="dr_rehearsal"
| stats latest(test_date) as last_test, latest(result) as result by system_name, scenario
| eval days_since=round((now()-strptime(last_test,"%Y-%m-%d"))/86400)
| where days_since > 365 OR result!="Pass"
| table system_name scenario last_test result days_since
```

## Visualization

Table (overdue systems), Calendar (scheduled tests), Single value (% scenarios current).

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
