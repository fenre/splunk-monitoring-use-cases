<!-- AUTO-GENERATED from UC-8.4.40.json — DO NOT EDIT -->

---
id: "8.4.40"
title: "PHP-FPM OPcache Hit Ratio from Status JSON"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-8.4.40 · PHP-FPM OPcache Hit Ratio from Status JSON

## Description

OPcache hit ratio reflects how often PHP executes from shared memory versus compiling. Drops after deploys or multi-version pools signal cold caches.

## Value

Protects CPU and latency by catching mis-tuned `opcache.validate_timestamps` or undersized shared memory.

## Implementation

Requires extended status including OPcache (PHP 7+); flatten keys in HEC payload. Alert hit_ratio < 95% sustained.

## SPL

```spl
index=web sourcetype="phpfpm:status"
| eval hits=tonumber(opcache_statistics_hits), miss=tonumber(opcache_statistics_misses)
| eval hit_ratio=if((hits+miss)>0, round(100*hits/(hits+miss),2), null())
| where isnotnull(hit_ratio)
| timechart span=1h min(hit_ratio) as min_hit_ratio by host
```

## Visualization

Time series (pool utilization, queue, latency percentiles), single value alerts, top charts for scripts and methods.

## References

- [CIM: Web](https://docs.splunk.com/Documentation/CIM/latest/User/Web)
- [PHP-FPM configuration](https://www.php.net/manual/en/book.opcache.php)
