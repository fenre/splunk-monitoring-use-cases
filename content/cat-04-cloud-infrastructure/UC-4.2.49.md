---
id: "4.2.49"
title: "Azure Redis Cache Performance"
criticality: "high"
splunkPillar: "Observability"
---

# UC-4.2.49 · Azure Redis Cache Performance

## Description

Redis Cache is a common caching and session store layer in Azure architectures. High server load, memory pressure, or cache misses directly impact application response times.

## Value

Redis Cache is a common caching and session store layer in Azure architectures. High server load, memory pressure, or cache misses directly impact application response times.

## Implementation

Collect Azure Monitor metrics for Redis Cache resources. Key metrics: `serverLoad` (alert >80%), `usedmemorypercentage` (alert >90%), `evictedkeys` (any eviction signals memory pressure), and cache hit ratio (`cacheHits/(cacheHits+cacheMisses)`). Track `connectedclients` against tier limits. For Premium tier, monitor replication lag between primary and replica.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_microsoft-cloudservices` (Azure Monitor metrics).
• Ensure the following data sources are available: `sourcetype=azure:monitor:metric` (Microsoft.Cache/Redis).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Collect Azure Monitor metrics for Redis Cache resources. Key metrics: `serverLoad` (alert >80%), `usedmemorypercentage` (alert >90%), `evictedkeys` (any eviction signals memory pressure), and cache hit ratio (`cacheHits/(cacheHits+cacheMisses)`). Track `connectedclients` against tier limits. For Premium tier, monitor replication lag between primary and replica.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=cloud sourcetype="azure:monitor:metric" resource_type="microsoft.cache/redis"
| where metric_name IN ("serverLoad","usedmemorypercentage","cacheHits","cacheMisses","connectedclients","evictedkeys")
| timechart span=5m avg(average) as value by metric_name, resource_name
```

Understanding this SPL

**Azure Redis Cache Performance** — Redis Cache is a common caching and session store layer in Azure architectures. High server load, memory pressure, or cache misses directly impact application response times.

Documented **Data sources**: `sourcetype=azure:monitor:metric` (Microsoft.Cache/Redis). **App/TA** (typical add-on context): `Splunk_TA_microsoft-cloudservices` (Azure Monitor metrics). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: cloud; **sourcetype**: azure:monitor:metric. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=cloud, sourcetype="azure:monitor:metric". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Filters the current rows with `where metric_name IN ("serverLoad","usedmemorypercentage","cacheHits","cacheMisses","connectedclients","evictedkeys")` — typically the threshold or rule expression for this monitoring goal.
• `timechart` plots the metric over time using **span=5m** buckets with a separate series **by metric_name, resource_name** — ideal for trending and alerting on this use case.

Optional CIM / accelerated variant (same use case, normalized fields via Common Information Model):

```spl
| tstats summariesonly=t avg(Performance.cpu_load_percent) as agg_value from datamodel=Performance.Memory by Performance.host span=5m | sort - agg_value
```

Understanding this CIM / accelerated SPL

**Azure Redis Cache Performance** — Redis Cache is a common caching and session store layer in Azure architectures. High server load, memory pressure, or cache misses directly impact application response times.

Documented **Data sources**: `sourcetype=azure:monitor:metric` (Microsoft.Cache/Redis). **App/TA** (typical add-on context): `Splunk_TA_microsoft-cloudservices` (Azure Monitor metrics). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

This **CIM or accelerated** block uses normalized field names and/or `tstats` over data models. Enable **acceleration** on the referenced models (and correct CIM knowledge objects) or the search may return nothing.

**Pipeline walkthrough**

• Uses `tstats` against accelerated summaries for data model `Performance.Memory` — enable acceleration for that model.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.

Enable Data Model Acceleration (and metric indexes for `mstats`) for the models or datasets referenced above; otherwise `tstats`/`mstats` may return no results from summaries.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Gauge (server load), Line chart (memory % and hit ratio), Single value (evicted keys).

## SPL

```spl
index=cloud sourcetype="azure:monitor:metric" resource_type="microsoft.cache/redis"
| where metric_name IN ("serverLoad","usedmemorypercentage","cacheHits","cacheMisses","connectedclients","evictedkeys")
| timechart span=5m avg(average) as value by metric_name, resource_name
```

## CIM SPL

```spl
| tstats summariesonly=t avg(Performance.cpu_load_percent) as agg_value from datamodel=Performance.Memory by Performance.host span=5m | sort - agg_value
```

## Visualization

Gauge (server load), Line chart (memory % and hit ratio), Single value (evicted keys).

## References

- [Splunk_TA_microsoft-cloudservices](https://splunkbase.splunk.com/app/3110)
- [CIM: Performance](https://docs.splunk.com/Documentation/CIM/latest/User/Performance)
