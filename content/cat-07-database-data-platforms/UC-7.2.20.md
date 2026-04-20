---
id: "7.2.20"
title: "Redis Eviction Rate"
criticality: "high"
splunkPillar: "Observability"
---

# UC-7.2.20 · Redis Eviction Rate

## Description

Rising `evicted_keys` per second indicates memory pressure and cache miss storms. Distinct from fragmentation and hit ratio for ops response.

## Value

Rising `evicted_keys` per second indicates memory pressure and cache miss storms. Distinct from fragmentation and hit ratio for ops response.

## Implementation

Derive per-second evictions from counter deltas. Alert when sustained above baseline. Correlate with `maxmemory` policy and traffic.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: redis-cli `INFO stats`.
• Ensure the following data sources are available: `evicted_keys`, `maxmemory`, `used_memory`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Derive per-second evictions from counter deltas. Alert when sustained above baseline. Correlate with `maxmemory` policy and traffic.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=database sourcetype="redis:info"
| timechart span=1m per_second(evicted_keys) as evict_per_sec by host
| where evict_per_sec > 10
```

Understanding this SPL

**Redis Eviction Rate** — Rising `evicted_keys` per second indicates memory pressure and cache miss storms. Distinct from fragmentation and hit ratio for ops response.

Documented **Data sources**: `evicted_keys`, `maxmemory`, `used_memory`. **App/TA** (typical add-on context): redis-cli `INFO stats`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: database; **sourcetype**: redis:info. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=database, sourcetype="redis:info". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `timechart` plots the metric over time using **span=1m** buckets with a separate series **by host** — ideal for trending and alerting on this use case.
• Filters the current rows with `where evict_per_sec > 10` — typically the threshold or rule expression for this monitoring goal.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Line chart (evictions/sec), Table (hosts spiking), Dual-axis (evictions + memory).

## SPL

```spl
index=database sourcetype="redis:info"
| timechart span=1m per_second(evicted_keys) as evict_per_sec by host
| where evict_per_sec > 10
```

## Visualization

Line chart (evictions/sec), Table (hosts spiking), Dual-axis (evictions + memory).

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
