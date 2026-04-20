---
id: "8.2.1"
title: "JVM Heap Utilization"
criticality: "critical"
splunkPillar: "Observability"
---

# UC-8.2.1 · JVM Heap Utilization

## Description

JVM heap exhaustion causes OutOfMemoryError, crashing the application. Monitoring enables tuning before failures occur.

## Value

JVM heap exhaustion causes OutOfMemoryError, crashing the application. Monitoring enables tuning before failures occur.

## Implementation

Deploy JMX TA on a heavy forwarder. Configure JMX connection to each app server. Poll memory MBeans every minute. Alert at 85% heap usage. Track heap growth pattern to detect memory leaks (sawtooth with increasing floor).

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `TA-jmx`, OpenTelemetry.
• Ensure the following data sources are available: JMX MBeans (`java.lang:type=Memory`), Prometheus JMX exporter.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Deploy JMX TA on a heavy forwarder. Configure JMX connection to each app server. Poll memory MBeans every minute. Alert at 85% heap usage. Track heap growth pattern to detect memory leaks (sawtooth with increasing floor).

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=jmx sourcetype="jmx:memory"
| eval heap_pct=round(HeapMemoryUsage.used/HeapMemoryUsage.max*100,1)
| timechart span=5m avg(heap_pct) as heap_usage by host
| where heap_usage > 85
```

Understanding this SPL

**JVM Heap Utilization** — JVM heap exhaustion causes OutOfMemoryError, crashing the application. Monitoring enables tuning before failures occur.

Documented **Data sources**: JMX MBeans (`java.lang:type=Memory`), Prometheus JMX exporter. **App/TA** (typical add-on context): `TA-jmx`, OpenTelemetry. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: jmx; **sourcetype**: jmx:memory. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=jmx, sourcetype="jmx:memory". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `eval` defines or adjusts **heap_pct** — often to normalize units, derive a ratio, or prepare for thresholds.
• `timechart` plots the metric over time using **span=5m** buckets with a separate series **by host** — ideal for trending and alerting on this use case.
• Filters the current rows with `where heap_usage > 85` — typically the threshold or rule expression for this monitoring goal.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Line chart (heap usage over time), Gauge (current heap %), Area chart (heap used vs max).

## SPL

```spl
index=jmx sourcetype="jmx:memory"
| eval heap_pct=round(HeapMemoryUsage.used/HeapMemoryUsage.max*100,1)
| timechart span=5m avg(heap_pct) as heap_usage by host
| where heap_usage > 85
```

## Visualization

Line chart (heap usage over time), Gauge (current heap %), Area chart (heap used vs max).

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
