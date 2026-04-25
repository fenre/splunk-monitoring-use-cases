<!-- AUTO-GENERATED from UC-1.2.5.json — DO NOT EDIT -->

---
id: "1.2.5"
title: "Event Log Flood Detection"
criticality: "medium"
splunkPillar: "Security"
---

# UC-1.2.5 · Event Log Flood Detection

## Description

Abnormal event log volumes often indicate error loops, misconfiguration, or an active attack. Also protects Splunk license from unexpected spikes.

## Value

Spikes can be attack noise, a broken script, or a log storm that hides a real error—trending shows which host is the outlier.

## Implementation

Use `timechart` + standard deviation to baseline normal volumes. Alert when volume exceeds 3 standard deviations. Investigate the top EventCode contributing to the spike.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_windows`.
• Ensure the following data sources are available: `sourcetype=WinEventLog:*`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Use `timechart` + standard deviation to baseline normal volumes. Alert when volume exceeds 3 standard deviations. Investigate the top EventCode contributing to the spike.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=wineventlog sourcetype="WinEventLog:*"
| timechart span=1h count by host
| eventstats avg(count) as avg_count, stdev(count) as stdev_count by host
| eval threshold = avg_count + (3 * stdev_count)
| where count > threshold
```

Understanding this SPL

**Event Log Flood Detection** — Abnormal event log volumes often indicate error loops, misconfiguration, or an active attack. Also protects Splunk license from unexpected spikes.

Documented **Data sources**: `sourcetype=WinEventLog:*`. **App/TA** (typical add-on context): `Splunk_TA_windows`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: wineventlog; **sourcetype**: WinEventLog:*. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=wineventlog, sourcetype="WinEventLog:*". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `timechart` plots the metric over time using **span=1h** buckets with a separate series **by host** — ideal for trending and alerting on this use case.
• `eventstats` rolls up events into metrics; results are split **by host** so each row reflects one combination of those dimensions.
• `eval` defines or adjusts **threshold** — often to normalize units, derive a ratio, or prepare for thresholds.
• Filters the current rows with `where count > threshold` — typically the threshold or rule expression for this monitoring goal.

Enable Data Model Acceleration (and metric indexes for `mstats`) for the models or datasets referenced above; otherwise `tstats`/`mstats` may return no results from summaries.

Optional CIM / accelerated variant (same use case, normalized fields via Common Information Model):

```spl
| tstats `summariesonly` count
  from datamodel=Change where nodename=Change.All_Changes
  by All_Changes.dest span=1h
| eventstats avg(count) as avg_count, stdev(count) as stdev_count by All_Changes.dest
| eval threshold=avg_count+(3*stdev_count)
| where count > threshold
```

Understanding this CIM / accelerated SPL

CIM tstats is an approximate mirror when Windows TA field extractions and CIM tags are complete. Enable the matching data model acceleration or tstats may return no rows.



Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Line chart with dynamic threshold overlay, Table of spike events.

## SPL

```spl
index=wineventlog sourcetype="WinEventLog:*"
| timechart span=1h count by host
| eventstats avg(count) as avg_count, stdev(count) as stdev_count by host
| eval threshold = avg_count + (3 * stdev_count)
| where count > threshold
```

## CIM SPL

```spl
| tstats `summariesonly` count
  from datamodel=Change where nodename=Change.All_Changes
  by All_Changes.dest span=1h
| eventstats avg(count) as avg_count, stdev(count) as stdev_count by All_Changes.dest
| eval threshold=avg_count+(3*stdev_count)
| where count > threshold
```

## Visualization

Line chart with dynamic threshold overlay, Table of spike events.

## References

- [Splunk_TA_windows](https://splunkbase.splunk.com/app/742)
