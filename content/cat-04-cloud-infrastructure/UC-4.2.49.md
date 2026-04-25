<!-- AUTO-GENERATED from UC-4.2.49.json — DO NOT EDIT -->

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
| tstats `summariesonly` avg(Performance.mem_used_percent) as agg_value
  from datamodel=Performance where nodename=Performance.Memory
  by Performance.host span=5m
| sort - agg_value
```

Understanding this CIM / accelerated SPL

**Azure Redis Cache Performance** — Redis Cache is a common caching and session store layer in Azure architectures.

If you map cloud vendor fields into the CIM, this variant uses normalized names and `tstats` on accelerated models. The raw vendor search in Step 2 is still the first stop for troubleshooting.

**Pipeline walkthrough**

• Uses `tstats` on the `Performance` data model (Memory node)—enable that model in Data Models and the CIM add-on, or the search may return no rows.

• Uses `sort` to rank results; add `head` to limit the table.

Enable Data Model Acceleration (and the right field aliases) for the models or datasets above; otherwise `tstats` may not find summaries.


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
| tstats `summariesonly` avg(Performance.mem_used_percent) as agg_value
  from datamodel=Performance where nodename=Performance.Memory
  by Performance.host span=5m
| sort - agg_value
```

## Visualization

Gauge (server load), Line chart (memory % and hit ratio), Single value (evicted keys).

## References

- [Splunk_TA_microsoft-cloudservices](https://splunkbase.splunk.com/app/3110)
- [CIM: Performance](https://docs.splunk.com/Documentation/CIM/latest/User/Performance)
