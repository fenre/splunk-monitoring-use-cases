<!-- AUTO-GENERATED from UC-8.5.3.json — DO NOT EDIT -->

---
id: "8.5.3"
title: "Eviction Rate Trending"
criticality: "high"
splunkPillar: "Observability"
---

# UC-8.5.3 · Eviction Rate Trending

## Description

High eviction rates mean the cache is too small, causing frequent backend roundtrips. Tracking guides capacity decisions.

## Value

High eviction rates mean the cache is too small, causing frequent backend roundtrips. Tracking guides capacity decisions.

## Implementation

Track evicted_keys counter over time. Calculate eviction rate per second. Alert when eviction rate exceeds threshold. Correlate with memory usage — evictions with memory below max indicates maxmemory-policy is active.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: Custom scripted input.
• Ensure the following data sources are available: Redis INFO stats (evicted_keys), Memcached stats (evictions).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Track evicted_keys counter over time. Calculate eviction rate per second. Alert when eviction rate exceeds threshold. Correlate with memory usage — evictions with memory below max indicates maxmemory-policy is active.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=cache sourcetype="redis:info"
| timechart span=5m per_second(evicted_keys) as eviction_rate by host
| where eviction_rate > 10
```

Understanding this SPL

**Eviction Rate Trending** — High eviction rates mean the cache is too small, causing frequent backend roundtrips. Tracking guides capacity decisions.

Documented **Data sources**: Redis INFO stats (evicted_keys), Memcached stats (evictions). **App/TA** (typical add-on context): Custom scripted input. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: cache; **sourcetype**: redis:info. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=cache, sourcetype="redis:info". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `timechart` plots the metric over time using **span=5m** buckets with a separate series **by host** — ideal for trending and alerting on this use case.
• Filters the current rows with `where eviction_rate > 10` — typically the threshold or rule expression for this monitoring goal.


Step 3 — Validate
Compare with `redis-cli INFO` (and slowlog if relevant) on the same instance and time window.


Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Line chart (eviction rate over time), Single value (current eviction rate), Dual-axis (evictions + memory usage).

## SPL

```spl
index=cache sourcetype="redis:info"
| timechart span=5m per_second(evicted_keys) as eviction_rate by host
| where eviction_rate > 10
```

## Visualization

Line chart (eviction rate over time), Single value (current eviction rate), Dual-axis (evictions + memory usage).

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
