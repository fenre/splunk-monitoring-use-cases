---
id: "8.2.14"
title: "JVM Garbage Collection Pause Time (STW)"
criticality: "critical"
splunkPillar: "Security"
---

# UC-8.2.14 · JVM Garbage Collection Pause Time (STW)

## Description

Stop-the-world pause duration percentiles from unified GC logs (G1, ZGC) drive SLA breaches before heap % alerts fire.

## Value

Stop-the-world pause duration percentiles from unified GC logs (G1, ZGC) drive SLA breaches before heap % alerts fire.

## Implementation

Parse pause events only (not concurrent phases). Alert on p95 >200ms or any pause >2s. Split by pool (G1 Old Gen vs Young).

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: GC log parsing, `jvm:gc` sourcetype.
• Ensure the following data sources are available: `-Xlog:gc*` (Java 11+), `gc_pause_ms`, `gc_type`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Parse pause events only (not concurrent phases). Alert on p95 >200ms or any pause >2s. Split by pool (G1 Old Gen vs Young).

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=jvm sourcetype="jvm:gc"
| where gc_pause_ms > 500
| timechart span=5m perc95(gc_pause_ms) as p95_pause, max(gc_pause_ms) as max_pause by host
| where p95_pause > 200
```

Understanding this SPL

**JVM Garbage Collection Pause Time (STW)** — Stop-the-world pause duration percentiles from unified GC logs (G1, ZGC) drive SLA breaches before heap % alerts fire.

Documented **Data sources**: `-Xlog:gc*` (Java 11+), `gc_pause_ms`, `gc_type`. **App/TA** (typical add-on context): GC log parsing, `jvm:gc` sourcetype. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: jvm; **sourcetype**: jvm:gc. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=jvm, sourcetype="jvm:gc". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Filters the current rows with `where gc_pause_ms > 500` — typically the threshold or rule expression for this monitoring goal.
• `timechart` plots the metric over time using **span=5m** buckets with a separate series **by host** — ideal for trending and alerting on this use case.
• Filters the current rows with `where p95_pause > 200` — typically the threshold or rule expression for this monitoring goal.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Line chart (p95/max pause), Histogram (pause distribution), Table (worst hosts).

## SPL

```spl
index=jvm sourcetype="jvm:gc"
| where gc_pause_ms > 500
| timechart span=5m perc95(gc_pause_ms) as p95_pause, max(gc_pause_ms) as max_pause by host
| where p95_pause > 200
```

## Visualization

Line chart (p95/max pause), Histogram (pause distribution), Table (worst hosts).

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
