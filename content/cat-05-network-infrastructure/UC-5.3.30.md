<!-- AUTO-GENERATED from UC-5.3.30.json — DO NOT EDIT -->

---
id: "5.3.30"
title: "Citrix ADC Integrated Cache Hit Ratio"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-5.3.30 · Citrix ADC Integrated Cache Hit Ratio

> **Criticality:** Medium &middot; **Difficulty:** Intermediate &middot; **Pillar:** Observability &middot; **Type:** Performance

*We look at content cache hit ratio on the same platform so a cold start after a release does not get mistaken for a broken cache for weeks.*

---

## Description

The Citrix ADC integrated content cache can offload origin servers for static and cacheable content. A falling hit ratio increases origin load and latency; high cache memory pressure can evict hot objects. Monitoring hit ratio, miss volume, and cache memory guides TTL tuning, object sizing, and capacity for content-heavy services.

## Value

Infrastructure teams monitor Citrix ADC integrated cache hit ratios to ensure HTTP response caching is effectively reducing backend load and improving response times.

## Implementation

Poll NITRO for integrated cache object statistics or use the TA’s scripted metrics into `citrix:netscaler:perf`. Align on per-content-group rollups. Alert on sustained hit ratio drop week over week, or memory utilization over 90% for multiple intervals. Log cache flush events in syslog and correlate to deployments.

## Detailed Implementation

### Prerequisites
* Splunk Add-on for Citrix NetScaler (`Splunk_TA_citrix-netscaler`, Splunkbase 2770). NITRO stats for integrated caching. Key metrics: `cache_hits`, `cache_misses`, `cache_hit_ratio`, `cache_memory_usage`, `cache_objects`.
* Citrix ADC Integrated Caching stores HTTP responses in ADC memory. Cache hits serve responses without contacting the backend, reducing: backend load, response time, and bandwidth. A low cache hit ratio means most requests still go to the backend.

### Step 1 — - Configure data collection
Poll NITRO API: `GET /nitro/v1/stat/cachecontentgroup` for cache statistics. Verify:
```spl
index=netscaler sourcetype="citrix:netscaler:perf" earliest=-4h
| where isnotnull(cache_hits) OR isnotnull(cache_hit_ratio) OR isnotnull(cachehitpct)
| stats latest(cache_hit_ratio) as hit_ratio by host
```

### Step 2 — - Create the search and alert

**Primary search -- Cache hit ratio monitoring:**
```spl
index=netscaler sourcetype="citrix:netscaler:perf" earliest=-4h
| eval hits=coalesce(cache_hits, cachehits)
| eval misses=coalesce(cache_misses, cachemisses)
| eval hit_ratio=coalesce(cache_hit_ratio, cachehitpct, if((hits+misses) > 0, round(100*hits/(hits+misses), 1), null()))
| eval mem_used=coalesce(cache_memory_usage, cachememusage)
| eval objects=coalesce(cache_objects, cacheobjects)
| bin _time span=15m
| stats avg(hit_ratio) as avg_hit_ratio latest(mem_used) as cache_mem latest(objects) as cached_objects sum(hits) as total_hits sum(misses) as total_misses by _time, host
| eval status=case(avg_hit_ratio < 30, "LOW -- most requests going to backend", avg_hit_ratio < 60, "MODERATE -- room for improvement", 1==1, "GOOD")
| where status != "GOOD"
| sort status, avg_hit_ratio
```

### Step 3 — - Validate
(a) On ADC CLI: `stat cache contentgroup` -- compare hit ratio.
(b) Access a cacheable URL twice and verify cache hit on second request.
(c) Check cache memory: `show cache parameter` for allocated memory.

### Step 4 — - Operationalize
Dashboard ("Citrix ADC -- Cache Performance"):
* Row 1 -- Single-value: "Hit ratio %", "Cached objects", "Cache memory (MB)", "Backend saves".
* Row 2 -- Cache hit ratio trending timechart.

Alerting:
* Warning (cache hit ratio < 30% sustained): caching not effective.

### Step 5 — - Troubleshooting

* **Low hit ratio** -- Check: (1) Content group policies: `show cache contentgroup` -- are the right URLs being cached? (2) Cache-Control headers from backends -- `no-cache`/`no-store` prevents caching. (3) Vary headers -- too many variants reduce cache effectiveness.

* **Cache memory full** -- Increase cache memory: `set cache parameter -memLimit <MB>`. Also check max object size and TTL settings.

* **Cache not enabled** -- Verify caching is enabled and policies bound: `show cache policy`.

## SPL

```spl
index=netscaler sourcetype="citrix:netscaler:perf" ("ic_cache" OR "ico_" OR cache_hits OR cache_misses)
| eval hits=coalesce(cache_hits, ico_hits, 0), misses=coalesce(cache_misses, ico_misses, 0)
| eval mem_use_pct=coalesce(cache_mem_use_pct, cache_mem_util, 0)
| bin _time span=5m
| stats sum(hits) as sum_hits, sum(misses) as sum_miss, avg(mem_use_pct) as cache_mem, latest(host) as adc by _time, host
| eval hit_ratio=if((sum_hits+sum_misses)>0, round(sum_hits/(sum_hits+sum_misses)*100,2), 0)
| where hit_ratio < 50 OR cache_mem > 90
| table _time, adc, sum_hits, sum_miss, hit_ratio, cache_mem
```

## Visualization

Line chart: hit ratio; area chart: hits vs misses; gauge: cache memory usage.

## Known False Positives

Cold caches and one-off content can tank hit ratio for an hour; compare to a longer baseline.

## References

- [Splunk Documentation: Splunk Add-on for Citrix NetScaler](https://docs.splunk.com/Documentation/AddOns/released/CitrixNetScaler/CitrixNetScaler)
- [Citrix ADC — Integrated caching](https://docs.citrix.com/en-us/citrix-adc/current-release/optimization/integrated-caching.html)
