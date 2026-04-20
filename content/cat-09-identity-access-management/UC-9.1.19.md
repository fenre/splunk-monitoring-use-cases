---
id: "9.1.19"
title: "LAPS Password Rotation Failures"
criticality: "high"
splunkPillar: "Security"
---

# UC-9.1.19 · LAPS Password Rotation Failures

## Description

Failed LAPS rotations leave predictable local admin passwords; attackers target stale LAPS attributes.

## Value

Failed LAPS rotations leave predictable local admin passwords; attackers target stale LAPS attributes.

## Implementation

Forward LAPS Operational log from all domain-joined clients that use LAPS. Map Event IDs to rotation success/failure. Alert on repeated failures per OU or GPO scope. Correlate with GPO and network issues.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_windows`.
• Ensure the following data sources are available: Operational log `Microsoft-Windows-LAPS/Operational` (Event IDs 10023, 10024, 10025, 10026), or legacy CSE events.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Forward LAPS Operational log from all domain-joined clients that use LAPS. Map Event IDs to rotation success/failure. Alert on repeated failures per OU or GPO scope. Correlate with GPO and network issues.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=wineventlog sourcetype="WinEventLog:Microsoft-Windows-LAPS/Operational" EventCode IN (10023,10024,10025,10026)
| stats count by ComputerName, EventCode, Message
| where count > 0
| sort -count
```

Understanding this SPL

**LAPS Password Rotation Failures** — Failed LAPS rotations leave predictable local admin passwords; attackers target stale LAPS attributes.

Documented **Data sources**: Operational log `Microsoft-Windows-LAPS/Operational` (Event IDs 10023, 10024, 10025, 10026), or legacy CSE events. **App/TA** (typical add-on context): `Splunk_TA_windows`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: wineventlog; **sourcetype**: WinEventLog:Microsoft-Windows-LAPS/Operational. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=wineventlog, sourcetype="WinEventLog:Microsoft-Windows-LAPS/Operational". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `stats` rolls up events into metrics; results are split **by ComputerName, EventCode, Message** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• Filters the current rows with `where count > 0` — typically the threshold or rule expression for this monitoring goal.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (hosts with failures), Bar chart (failures by OU), Single value (failed rotations 24h).

## SPL

```spl
index=wineventlog sourcetype="WinEventLog:Microsoft-Windows-LAPS/Operational" EventCode IN (10023,10024,10025,10026)
| stats count by ComputerName, EventCode, Message
| where count > 0
| sort -count
```

## Visualization

Table (hosts with failures), Bar chart (failures by OU), Single value (failed rotations 24h).

## Known False Positives

Administrative tasks, scheduled jobs or platform updates can match this pattern — correlate with change management, maintenance windows and user role before raising severity.

## References

- [Splunk_TA_windows](https://splunkbase.splunk.com/app/742)
