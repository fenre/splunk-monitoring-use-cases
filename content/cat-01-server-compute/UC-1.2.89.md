<!-- AUTO-GENERATED from UC-1.2.89.json — DO NOT EDIT -->

---
id: "1.2.89"
title: "System Uptime & Unexpected Restarts (Windows)"
criticality: "medium"
splunkPillar: "Security"
---

# UC-1.2.89 · System Uptime & Unexpected Restarts (Windows)

## Description

Unexpected restarts indicate BSOD, power loss, forced reboots, or patch installations. Tracking uptime reveals instability patterns and unauthorized maintenance.

## Value

Frequent or surprise reboots on servers that should stay up point to bad patches, power, or cluster fail-over. A timeline of clean vs dirty shutdowns shortens both ops and forensics work.

## Implementation

EventCode 6008=unexpected shutdown (BSOD, power loss, hard reset) — always investigate. EventCode 1074=planned shutdown with user and reason. Calculate uptime by measuring time between 6005 events. Alert on any EventCode 6008 (unexpected) and on restarts outside maintenance windows. Track monthly uptime percentage per server for SLA reporting.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_windows`.
• Ensure the following data sources are available: `sourcetype=WinEventLog:System` (EventCode 6005, 6006, 6008, 6009, 1074).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
EventCode 6008=unexpected shutdown (BSOD, power loss, hard reset) — always investigate. EventCode 1074=planned shutdown with user and reason. Calculate uptime by measuring time between 6005 events. Alert on any EventCode 6008 (unexpected) and on restarts outside maintenance windows. Track monthly uptime percentage per server for SLA reporting.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=wineventlog sourcetype="WinEventLog:System" EventCode IN (6005, 6006, 6008, 1074)
| eval event=case(EventCode=6005,"Event log started (boot)",EventCode=6006,"Event log stopped (clean shutdown)",EventCode=6008,"Unexpected shutdown",EventCode=1074,"User-initiated shutdown/restart")
| table _time, host, event, User, Reason, Comment
| sort -_time
```

Understanding this SPL

**System Uptime & Unexpected Restarts (Windows)** — Unexpected restarts indicate BSOD, power loss, forced reboots, or patch installations. Tracking uptime reveals instability patterns and unauthorized maintenance.

Documented **Data sources**: `sourcetype=WinEventLog:System` (EventCode 6005, 6006, 6008, 6009, 1074). **App/TA** (typical add-on context): `Splunk_TA_windows`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: wineventlog; **sourcetype**: WinEventLog:System. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=wineventlog, sourcetype="WinEventLog:System". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `eval` defines or adjusts **event** — often to normalize units, derive a ratio, or prepare for thresholds.
• Pipeline stage (see **System Uptime & Unexpected Restarts (Windows)**): table _time, host, event, User, Reason, Comment
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (shutdown events), Line chart (uptime per host), Single value (hosts with unexpected restarts), Calendar view.

## SPL

```spl
index=wineventlog sourcetype="WinEventLog:System" EventCode IN (6005, 6006, 6008, 1074)
| eval event=case(EventCode=6005,"Event log started (boot)",EventCode=6006,"Event log stopped (clean shutdown)",EventCode=6008,"Unexpected shutdown",EventCode=1074,"User-initiated shutdown/restart")
| table _time, host, event, User, Reason, Comment
| sort -_time
```

## CIM SPL

```spl
| tstats `summariesonly` count
  from datamodel=Change.All_Changes
  by All_Changes.dest All_Changes.action span=1h
| where count > 0
```

## Visualization

Table (shutdown events), Line chart (uptime per host), Single value (hosts with unexpected restarts), Calendar view.

## References

- [Splunk_TA_windows](https://splunkbase.splunk.com/app/742)
