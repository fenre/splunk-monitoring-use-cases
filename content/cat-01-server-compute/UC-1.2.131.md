<!-- AUTO-GENERATED from UC-1.2.131.json — DO NOT EDIT -->

---
id: "1.2.131"
title: "Windows Print Spooler Health"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-1.2.131 · Windows Print Spooler Health

## Description

Spooler service state, queue depth, and stalled print jobs affect printing availability. Print Spooler failures block all printing on the host.

## Value

Spooler service state, queue depth, and stalled print jobs affect printing availability. Print Spooler failures block all printing on the host.

## Implementation

Enable `WinEventLog:System` input for EventCode 7036 (service state change). Filter for ServiceName=Spooler. Configure Perfmon input for Print Queue object: counter=Jobs (queue depth). Run every 60 seconds. Alert when Spooler stops; alert when queue depth exceeds 50 for sustained period (stalled jobs).

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_windows`.
• Ensure the following data sources are available: `WinEventLog:System` (Event ID 7036 for spooler), Perfmon (Print Queue counters).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Enable `WinEventLog:System` input for EventCode 7036 (service state change). Filter for ServiceName=Spooler. Configure Perfmon input for Print Queue object: counter=Jobs (queue depth). Run every 60 seconds. Alert when Spooler stops; alert when queue depth exceeds 50 for sustained period (stalled jobs).

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=perfmon sourcetype=Perfmon:PrintQueue host=* counter="Jobs"
| stats latest(Value) as queue_depth by host, instance
| where queue_depth > 50
| sort -queue_depth
```

Understanding this SPL

**Windows Print Spooler Health** — Spooler service state, queue depth, and stalled print jobs affect printing availability. Print Spooler failures block all printing on the host.

Documented **Data sources**: `WinEventLog:System` (Event ID 7036 for spooler), Perfmon (Print Queue counters). **App/TA** (typical add-on context): `Splunk_TA_windows`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: perfmon; **sourcetype**: Perfmon:PrintQueue. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=perfmon, sourcetype=Perfmon:PrintQueue. Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `stats` rolls up events into metrics; results are split **by host, instance** so each row reflects one combination of those dimensions.
• Filters the current rows with `where queue_depth > 50` — typically the threshold or rule expression for this monitoring goal.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (host, spooler state, queue depth), Single value (failed spooler count), Line chart (queue depth over time).

## SPL

```spl
index=perfmon sourcetype=Perfmon:PrintQueue host=* counter="Jobs"
| stats latest(Value) as queue_depth by host, instance
| where queue_depth > 50
| sort -queue_depth
```

## Visualization

Table (host, spooler state, queue depth), Single value (failed spooler count), Line chart (queue depth over time).

## References

- [Splunk_TA_windows](https://splunkbase.splunk.com/app/742)
