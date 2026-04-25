<!-- AUTO-GENERATED from UC-8.5.2.json — DO NOT EDIT -->

---
id: "8.5.2"
title: "Memory Utilization"
criticality: "high"
splunkPillar: "Observability"
---

# UC-8.5.2 · Memory Utilization

## Description

Cache memory exhaustion triggers evictions, degrading performance. Monitoring enables timely scaling.

## Value

Cache memory exhaustion triggers evictions, degrading performance. Monitoring enables timely scaling.

## Implementation

Poll memory metrics every minute. Track used vs max memory and RSS vs used ratio (fragmentation). Alert at 85% memory usage. Monitor memory fragmentation ratio — values >1.5 indicate excessive fragmentation.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: Custom scripted input.
• Ensure the following data sources are available: Redis INFO memory, Memcached stats.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Poll memory metrics every minute. Track used vs max memory and RSS vs used ratio (fragmentation). Alert at 85% memory usage. Monitor memory fragmentation ratio — values >1.5 indicate excessive fragmentation.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=cache sourcetype="redis:info"
| eval mem_pct=round(used_memory/maxmemory*100,1)
| timechart span=5m max(mem_pct) as memory_pct by host
| where memory_pct > 85
```

Understanding this SPL

**Memory Utilization** — Cache memory exhaustion triggers evictions, degrading performance. Monitoring enables timely scaling.

Documented **Data sources**: Redis INFO memory, Memcached stats. **App/TA** (typical add-on context): Custom scripted input. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: cache; **sourcetype**: redis:info. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=cache, sourcetype="redis:info". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `eval` defines or adjusts **mem_pct** — often to normalize units, derive a ratio, or prepare for thresholds.
• `timechart` plots the metric over time using **span=5m** buckets with a separate series **by host** — ideal for trending and alerting on this use case.
• Filters the current rows with `where memory_pct > 85` — typically the threshold or rule expression for this monitoring goal.


Step 3 — Validate
Compare with `redis-cli INFO` (and slowlog if relevant) on the same instance and time window.


Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Gauge (% memory used), Line chart (memory usage over time), Table (instances approaching limit).

## SPL

```spl
index=cache sourcetype="redis:info"
| eval mem_pct=round(used_memory/maxmemory*100,1)
| timechart span=5m max(mem_pct) as memory_pct by host
| where memory_pct > 85
```

## Visualization

Gauge (% memory used), Line chart (memory usage over time), Table (instances approaching limit).

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
