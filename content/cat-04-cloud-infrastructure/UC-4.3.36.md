---
id: "4.3.36"
title: "Memorystore (Redis) Health"
criticality: "high"
splunkPillar: "Observability"
---

# UC-4.3.36 · Memorystore (Redis) Health

## Description

Redis backs sessions and caches; memory pressure and replication lag cause timeouts and stale reads.

## Value

Redis backs sessions and caches; memory pressure and replication lag cause timeouts and stale reads.

## Implementation

Alert on memory usage above 90%, high CPU, or replica lag metrics. Plan tier upgrades or key eviction policies. Monitor persistence (RDB/AOF) failures if enabled.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_google-cloudplatform`.
• Ensure the following data sources are available: `sourcetype=google:gcp:monitoring` (`redis.googleapis.com/stats/memory/usage_ratio`, `replication/role`, `cpu/utilization`).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Alert on memory usage above 90%, high CPU, or replica lag metrics. Plan tier upgrades or key eviction policies. Monitor persistence (RDB/AOF) failures if enabled.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=gcp sourcetype="google:gcp:monitoring" metric.type="redis.googleapis.com/stats/memory/usage_ratio"
| stats latest(value) as mem_ratio by resource.labels.instance_id, bin(_time, 5m)
| where mem_ratio > 0.9
| sort - mem_ratio
```

Understanding this SPL

**Memorystore (Redis) Health** — Redis backs sessions and caches; memory pressure and replication lag cause timeouts and stale reads.

Documented **Data sources**: `sourcetype=google:gcp:monitoring` (`redis.googleapis.com/stats/memory/usage_ratio`, `replication/role`, `cpu/utilization`). **App/TA** (typical add-on context): `Splunk_TA_google-cloudplatform`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: gcp; **sourcetype**: google:gcp:monitoring. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=gcp, sourcetype="google:gcp:monitoring". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `stats` rolls up events into metrics; results are split **by resource.labels.instance_id, bin(_time, 5m)** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• Filters the current rows with `where mem_ratio > 0.9` — typically the threshold or rule expression for this monitoring goal.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Line chart (memory ratio, CPU), Table (instance, tier), Single value (evictions if exported).

## SPL

```spl
index=gcp sourcetype="google:gcp:monitoring" metric.type="redis.googleapis.com/stats/memory/usage_ratio"
| stats latest(value) as mem_ratio by resource.labels.instance_id, bin(_time, 5m)
| where mem_ratio > 0.9
| sort - mem_ratio
```

## Visualization

Line chart (memory ratio, CPU), Table (instance, tier), Single value (evictions if exported).

## References

- [Splunk_TA_google-cloudplatform](https://splunkbase.splunk.com/app/3088)
