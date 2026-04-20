---
id: "8.7.4"
title: "Cache Hit Ratio Trending"
criticality: "medium"
splunkPillar: "Security"
---

# UC-8.7.4 · Cache Hit Ratio Trending

## Description

Cache hit ratio over 30 days reveals memory sizing issues, key churn, and upstream slowdowns that force more origin fetches. Declining trends often precede latency SLO breaches.

## Value

Cache hit ratio over 30 days reveals memory sizing issues, key churn, and upstream slowdowns that force more origin fetches. Declining trends often precede latency SLO breaches.

## Implementation

Poll INFO/stats on a fixed interval; compute ratio in SPL or at ingest for accuracy. Split by `instance` or `cluster` for sharded caches. Correlate drops with deployments and TTL changes. For HTTP caches, derive hits from `X-Cache` or CDN logs instead.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: Splunk Add-on for Redis, Memcached, Varnish or CDN logs.
• Ensure the following data sources are available: `index=middleware` `sourcetype=redis:info`, `memcached:stats`, or application-emitted cache metrics.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Poll INFO/stats on a fixed interval; compute ratio in SPL or at ingest for accuracy. Split by `instance` or `cluster` for sharded caches. Correlate drops with deployments and TTL changes. For HTTP caches, derive hits from `X-Cache` or CDN logs instead.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=middleware (sourcetype="redis:info" OR sourcetype="memcached:stats" OR sourcetype="app:cache:metrics")
| eval hits=coalesce(keyspace_hits, cache_hits, 0)
| eval misses=coalesce(keyspace_misses, cache_misses, 0)
| eval hit_ratio=if((hits+misses)>0, round(100*hits/(hits+misses),2), null())
| timechart span=1d avg(hit_ratio) as cache_hit_ratio_pct
```

Understanding this SPL

**Cache Hit Ratio Trending** — Cache hit ratio over 30 days reveals memory sizing issues, key churn, and upstream slowdowns that force more origin fetches. Declining trends often precede latency SLO breaches.

Documented **Data sources**: `index=middleware` `sourcetype=redis:info`, `memcached:stats`, or application-emitted cache metrics. **App/TA** (typical add-on context): Splunk Add-on for Redis, Memcached, Varnish or CDN logs. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: middleware; **sourcetype**: redis:info, memcached:stats, app:cache:metrics. Those sourcetypes align with what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=middleware, sourcetype="redis:info". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `eval` defines or adjusts **hits** — often to normalize units, derive a ratio, or prepare for thresholds.
• `eval` defines or adjusts **misses** — often to normalize units, derive a ratio, or prepare for thresholds.
• `eval` defines or adjusts **hit_ratio** — often to normalize units, derive a ratio, or prepare for thresholds.
• `timechart` plots the metric over time using **span=1d** buckets — ideal for trending and alerting on this use case.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Line chart (hit ratio %), dual axis (hits and misses counts), single value (30-day min hit ratio).

## SPL

```spl
index=middleware (sourcetype="redis:info" OR sourcetype="memcached:stats" OR sourcetype="app:cache:metrics")
| eval hits=coalesce(keyspace_hits, cache_hits, 0)
| eval misses=coalesce(keyspace_misses, cache_misses, 0)
| eval hit_ratio=if((hits+misses)>0, round(100*hits/(hits+misses),2), null())
| timechart span=1d avg(hit_ratio) as cache_hit_ratio_pct
```

## Visualization

Line chart (hit ratio %), dual axis (hits and misses counts), single value (30-day min hit ratio).

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
