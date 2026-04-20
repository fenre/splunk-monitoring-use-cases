---
id: "7.2.9"
title: "Memory Utilization"
criticality: "high"
splunkPillar: "Observability"
---

# UC-7.2.9 · Memory Utilization

## Description

NoSQL databases are memory-intensive. Evictions indicate undersized cache, causing disk reads and performance degradation.

## Value

NoSQL databases are memory-intensive. Evictions indicate undersized cache, causing disk reads and performance degradation.

## Implementation

Poll memory metrics every 5 minutes. Track used vs max memory, eviction rate, and cache hit ratio. Alert when memory exceeds 85% or eviction rate spikes. Recommend sizing adjustments based on trends.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: Custom scripted input, JMX.
• Ensure the following data sources are available: Redis `INFO memory`, MongoDB WiredTiger cache stats, Cassandra JMX heap metrics.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Poll memory metrics every 5 minutes. Track used vs max memory, eviction rate, and cache hit ratio. Alert when memory exceeds 85% or eviction rate spikes. Recommend sizing adjustments based on trends.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=database sourcetype="redis:info"
| eval mem_pct=round(used_memory/maxmemory*100,1)
| timechart span=5m max(mem_pct) as memory_pct, sum(evicted_keys) as evictions by host
| where memory_pct > 85
```

Understanding this SPL

**Memory Utilization** — NoSQL databases are memory-intensive. Evictions indicate undersized cache, causing disk reads and performance degradation.

Documented **Data sources**: Redis `INFO memory`, MongoDB WiredTiger cache stats, Cassandra JMX heap metrics. **App/TA** (typical add-on context): Custom scripted input, JMX. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: database; **sourcetype**: redis:info. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=database, sourcetype="redis:info". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `eval` defines or adjusts **mem_pct** — often to normalize units, derive a ratio, or prepare for thresholds.
• `timechart` plots the metric over time using **span=5m** buckets with a separate series **by host** — ideal for trending and alerting on this use case.
• Filters the current rows with `where memory_pct > 85` — typically the threshold or rule expression for this monitoring goal.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Gauge (memory % per node), Line chart (memory + evictions), Table (nodes with high utilization).

## SPL

```spl
index=database sourcetype="redis:info"
| eval mem_pct=round(used_memory/maxmemory*100,1)
| timechart span=5m max(mem_pct) as memory_pct, sum(evicted_keys) as evictions by host
| where memory_pct > 85
```

## Visualization

Gauge (memory % per node), Line chart (memory + evictions), Table (nodes with high utilization).

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
