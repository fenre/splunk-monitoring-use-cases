---
id: "6.4.17"
title: "CIFS Connection Monitoring"
criticality: "medium"
splunkPillar: "Security"
---

# UC-6.4.17 · CIFS Connection Monitoring

## Description

Tracks concurrent SMB sessions and failed session setups per file server. Spikes may indicate brute force, misconfigured apps, or server resource limits.

## Value

Tracks concurrent SMB sessions and failed session setups per file server. Spikes may indicate brute force, misconfigured apps, or server resource limits.

## Implementation

Baseline sessions per 5m window per server. Alert on 3× baseline or on SMB error events (551, 552) if enabled. Correlate with auth failures.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_windows`, SMB server audit.
• Ensure the following data sources are available: Event ID 5140/5145, Perfmons `Server Sessions`, `Server Rejects`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Baseline sessions per 5m window per server. Alert on 3× baseline or on SMB error events (551, 552) if enabled. Correlate with auth failures.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=wineventlog sourcetype="WinEventLog:Security" EventCode=5140 OR EventCode=5145
| bucket _time span=5m
| stats count as sessions by ComputerName, _time
| eventstats avg(sessions) as avg_s by ComputerName
| where sessions > avg_s * 3
```

Understanding this SPL

**CIFS Connection Monitoring** — Tracks concurrent SMB sessions and failed session setups per file server. Spikes may indicate brute force, misconfigured apps, or server resource limits.

Documented **Data sources**: Event ID 5140/5145, Perfmons `Server Sessions`, `Server Rejects`. **App/TA** (typical add-on context): `Splunk_TA_windows`, SMB server audit. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: wineventlog; **sourcetype**: WinEventLog:Security. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=wineventlog, sourcetype="WinEventLog:Security". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Discretizes time or numeric ranges with `bin`/`bucket`.
• `stats` rolls up events into metrics; results are split **by ComputerName, _time** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• `eventstats` rolls up events into metrics; results are split **by ComputerName** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• Filters the current rows with `where sessions > avg_s * 3` — typically the threshold or rule expression for this monitoring goal.

Enable Data Model Acceleration (and metric indexes for `mstats`) for the models or datasets referenced above; otherwise `tstats`/`mstats` may return no results from summaries.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Line chart (session rate per server), Table (spike windows), Single value (current sessions).

## SPL

```spl
index=wineventlog sourcetype="WinEventLog:Security" EventCode=5140 OR EventCode=5145
| bucket _time span=5m
| stats count as sessions by ComputerName, _time
| eventstats avg(sessions) as avg_s by ComputerName
| where sessions > avg_s * 3
```

## Visualization

Line chart (session rate per server), Table (spike windows), Single value (current sessions).

## References

- [Splunk_TA_windows](https://splunkbase.splunk.com/app/742)
