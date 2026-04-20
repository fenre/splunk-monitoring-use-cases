---
id: "8.2.2"
title: "Garbage Collection Impact"
criticality: "high"
splunkPillar: "Observability"
---

# UC-8.2.2 · Garbage Collection Impact

## Description

Frequent or long GC pauses cause application latency spikes and request timeouts. Monitoring guides JVM tuning.

## Value

Frequent or long GC pauses cause application latency spikes and request timeouts. Monitoring guides JVM tuning.

## Implementation

Enable GC logging on all JVM-based app servers (`-Xlog:gc*` for Java 11+). Forward logs via UF. Parse pause duration, type, and cause. Alert on pauses >200ms or total pause time >5% of wall clock time.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: GC log parsing, `TA-jmx`.
• Ensure the following data sources are available: JVM GC logs, JMX GarbageCollector MBeans.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Enable GC logging on all JVM-based app servers (`-Xlog:gc*` for Java 11+). Forward logs via UF. Parse pause duration, type, and cause. Alert on pauses >200ms or total pause time >5% of wall clock time.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=jvm sourcetype="jvm:gc"
| where gc_pause_ms > 200
| timechart span=15m count as gc_events, sum(gc_pause_ms) as total_pause_ms by host
| eval pause_pct=round(total_pause_ms/900000*100,2)
```

Understanding this SPL

**Garbage Collection Impact** — Frequent or long GC pauses cause application latency spikes and request timeouts. Monitoring guides JVM tuning.

Documented **Data sources**: JVM GC logs, JMX GarbageCollector MBeans. **App/TA** (typical add-on context): GC log parsing, `TA-jmx`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: jvm; **sourcetype**: jvm:gc. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=jvm, sourcetype="jvm:gc". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Filters the current rows with `where gc_pause_ms > 200` — typically the threshold or rule expression for this monitoring goal.
• `timechart` plots the metric over time using **span=15m** buckets with a separate series **by host** — ideal for trending and alerting on this use case.
• `eval` defines or adjusts **pause_pct** — often to normalize units, derive a ratio, or prepare for thresholds.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Line chart (GC pause duration), Histogram (pause distribution), Single value (total pause time per hour).

## SPL

```spl
index=jvm sourcetype="jvm:gc"
| where gc_pause_ms > 200
| timechart span=15m count as gc_events, sum(gc_pause_ms) as total_pause_ms by host
| eval pause_pct=round(total_pause_ms/900000*100,2)
```

## Visualization

Line chart (GC pause duration), Histogram (pause distribution), Single value (total pause time per hour).

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
