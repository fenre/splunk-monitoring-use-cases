---
id: "8.2.23"
title: "Jira Data Center Performance"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-8.2.23 · Jira Data Center Performance

## Description

JMX metrics, request duration, and attachment storage indicate Jira health. Slow requests frustrate users; disk usage growth risks outages. Enables capacity planning and performance tuning.

## Value

JMX metrics, request duration, and attachment storage indicate Jira health. Slow requests frustrate users; disk usage growth risks outages. Enables capacity planning and performance tuning.

## Implementation

Deploy Jolokia agent on Jira application nodes and configure Splunk to poll JMX MBeans (java.lang:type=Memory, java.lang:type=Threading, com.atlassian.jira:type=RequestMetrics). Poll every 60 seconds. Ingest Jira access logs for request duration percentiles. Optionally poll /rest/api/2/serverInfo for version and build. Alert on heap >85%, thread count >500, or P95 request duration >3 seconds. Track attachment storage via JMX or filesystem metrics. Correlate with database and disk I/O.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: Custom JMX input (Jolokia), Jira REST API.
• Ensure the following data sources are available: Jira JMX MBeans (heap, threads, request duration), /rest/api/2/serverInfo, Jira access logs.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Deploy Jolokia agent on Jira application nodes and configure Splunk to poll JMX MBeans (java.lang:type=Memory, java.lang:type=Threading, com.atlassian.jira:type=RequestMetrics). Poll every 60 seconds. Ingest Jira access logs for request duration percentiles. Optionally poll /rest/api/2/serverInfo for version and build. Alert on heap >85%, thread count >500, or P95 request duration >3 seconds. Track attachment storage via JMX or filesystem metrics. Correlate with database and disk I/O.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=jira sourcetype="jira:jmx"
| eval heap_used_pct=if(HeapMemoryMax>0, round(HeapMemoryUsed/HeapMemoryMax*100, 1), null())
| where heap_used_pct > 85 OR ThreadCount > 500 OR RequestDurationP95 > 3000
| bin _time span=5m
| stats latest(HeapMemoryUsed) as heap_used, latest(HeapMemoryMax) as heap_max, latest(heap_used_pct) as heap_pct, latest(ThreadCount) as threads, latest(RequestDurationP95) as p95_ms by _time, host
| where heap_pct > 85 OR threads > 500 OR p95_ms > 3000
| table _time, host, heap_used, heap_max, heap_pct, threads, p95_ms
```

Understanding this SPL

**Jira Data Center Performance** — JMX metrics, request duration, and attachment storage indicate Jira health. Slow requests frustrate users; disk usage growth risks outages. Enables capacity planning and performance tuning.

Documented **Data sources**: Jira JMX MBeans (heap, threads, request duration), /rest/api/2/serverInfo, Jira access logs. **App/TA** (typical add-on context): Custom JMX input (Jolokia), Jira REST API. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: jira; **sourcetype**: jira:jmx. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=jira, sourcetype="jira:jmx". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `eval` defines or adjusts **heap_used_pct** — often to normalize units, derive a ratio, or prepare for thresholds.
• Filters the current rows with `where heap_used_pct > 85 OR ThreadCount > 500 OR RequestDurationP95 > 3000` — typically the threshold or rule expression for this monitoring goal.
• Discretizes time or numeric ranges with `bin`/`bucket`.
• `stats` rolls up events into metrics; results are split **by _time, host** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• Filters the current rows with `where heap_pct > 85 OR threads > 500 OR p95_ms > 3000` — typically the threshold or rule expression for this monitoring goal.
• Pipeline stage (see **Jira Data Center Performance**): table _time, host, heap_used, heap_max, heap_pct, threads, p95_ms


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Line chart (heap usage, thread count, P95 latency), Gauge (heap %), Table (performance metrics by node), Bar chart (request duration by endpoint).

## SPL

```spl
index=jira sourcetype="jira:jmx"
| eval heap_used_pct=if(HeapMemoryMax>0, round(HeapMemoryUsed/HeapMemoryMax*100, 1), null())
| where heap_used_pct > 85 OR ThreadCount > 500 OR RequestDurationP95 > 3000
| bin _time span=5m
| stats latest(HeapMemoryUsed) as heap_used, latest(HeapMemoryMax) as heap_max, latest(heap_used_pct) as heap_pct, latest(ThreadCount) as threads, latest(RequestDurationP95) as p95_ms by _time, host
| where heap_pct > 85 OR threads > 500 OR p95_ms > 3000
| table _time, host, heap_used, heap_max, heap_pct, threads, p95_ms
```

## Visualization

Line chart (heap usage, thread count, P95 latency), Gauge (heap %), Table (performance metrics by node), Bar chart (request duration by endpoint).

## References

- [Splunk Connect for Kafka](https://splunkbase.splunk.com/app/3862)
