<!-- AUTO-GENERATED from UC-6.3.5.json — DO NOT EDIT -->

---
id: "6.3.5"
title: "Restore Test Tracking"
criticality: "high"
splunkPillar: "Observability"
---

# UC-6.3.5 · Restore Test Tracking

## Description

Backups are worthless if restores fail. Tracking restore tests ensures confidence in recoverability and satisfies audit requirements.

## Value

Backups are worthless if restores fail. Tracking restore tests ensures confidence in recoverability and satisfies audit requirements.

## Implementation

Log all restore test results (automated or manual) to a dedicated index. Maintain a lookup of systems requiring quarterly restore tests. Alert when any system exceeds 90 days without a successful test.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: Manual/scripted input, backup TA.
• Ensure the following data sources are available: Restore test logs, manual test result entries.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Log all restore test results (automated or manual) to a dedicated index. Maintain a lookup of systems requiring quarterly restore tests. Alert when any system exceeds 90 days without a successful test.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=backup sourcetype="restore_test"
| stats latest(_time) as last_test, latest(result) as result by system_name
| eval days_since_test=round((now()-last_test)/86400)
| where days_since_test > 90 OR result!="Success"
| table system_name, last_test, result, days_since_test
```

Understanding this SPL

**Restore Test Tracking** — Backups are worthless if restores fail. Tracking restore tests ensures confidence in recoverability and satisfies audit requirements.

Documented **Data sources**: Restore test logs, manual test result entries. **App/TA** (typical add-on context): Manual/scripted input, backup TA. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: backup; **sourcetype**: restore_test. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=backup, sourcetype="restore_test". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `stats` rolls up events into metrics; results are split **by system_name** so each row reflects one combination of those dimensions.
• `eval` defines or adjusts **days_since_test** — often to normalize units, derive a ratio, or prepare for thresholds.
• Filters the current rows with `where days_since_test > 90 OR result!="Success"` — typically the threshold or rule expression for this monitoring goal.
• Pipeline stage (see **Restore Test Tracking**): table system_name, last_test, result, days_since_test


Step 3 — Validate
Compare the same metric, object name, and interval in the vendor or cloud console (array, backup, or object store) that is the source of truth for this feed.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. List media server, proxy, and repository names in the runbook, and when to open a ticket with the application team versus the backup team. Consider visualizations: Table (systems with test status), Single value (% tested in last 90d), Status grid (system × quarter).

## SPL

```spl
index=backup sourcetype="restore_test"
| stats latest(_time) as last_test, latest(result) as result by system_name
| eval days_since_test=round((now()-last_test)/86400)
| where days_since_test > 90 OR result!="Success"
| table system_name, last_test, result, days_since_test
```

## Visualization

Table (systems with test status), Single value (% tested in last 90d), Status grid (system × quarter).

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
