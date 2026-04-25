<!-- AUTO-GENERATED from UC-5.3.30.json — DO NOT EDIT -->

---
id: "5.3.30"
title: "Citrix ADC Integrated Cache Hit Ratio"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-5.3.30 · Citrix ADC Integrated Cache Hit Ratio

## Description

The Citrix ADC integrated content cache can offload origin servers for static and cacheable content. A falling hit ratio increases origin load and latency; high cache memory pressure can evict hot objects. Monitoring hit ratio, miss volume, and cache memory guides TTL tuning, object sizing, and capacity for content-heavy services.

## Value

The Citrix ADC integrated content cache can offload origin servers for static and cacheable content. A falling hit ratio increases origin load and latency; high cache memory pressure can evict hot objects. Monitoring hit ratio, miss volume, and cache memory guides TTL tuning, object sizing, and capacity for content-heavy services.

## Implementation

Poll NITRO for integrated cache object statistics or use the TA’s scripted metrics into `citrix:netscaler:perf`. Align on per-content-group rollups. Alert on sustained hit ratio drop week over week, or memory utilization over 90% for multiple intervals. Log cache flush events in syslog and correlate to deployments.

## Detailed Implementation

Prerequisites
• `index=netscaler` `sourcetype=citrix:netscaler:perf`; integrated cache feature licensed. 7d baseline of hit/miss. Clarify in runbook: counter delta vs rate from NITRO; use `streamstats` if cumulative.

Step 1 — Configure data collection
TA poll 1–5m; in `props` coalesce `ico_hits/ico_misses` into `cache_hits`/`cache_misses`. `eval` defensively with `tonumber()`. Ingest syslog for manual `flush`/`clear` to annotate drops.

Step 2 — Create the search and alert
`hit_ratio<50` and `cache_mem>90` are defaults: override per `lbvserver` in `lookups/adc_cache_slo` (static APIs expect low hit rate). Add WoW drop alert: 20+ points sustained 1h. Suppress on deploy token. Alert miss spike: possible cache bust/attack.

Step 3 — Validate
Compare vservers, services, and load-balancing state in the Citrix ADC management view or command line for the same time window and objects.
Step 4 — Operationalize
Panels: line hit %, area hits+misses, gauge mem, drill to `host`. Owner: app (TTL, cacheability), platform (sizing). Escalation: P2 if origin 5xx/latency rise with ratio drop. Tag releases in dashboard to explain sudden shifts.

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

## References

- [Splunk Documentation: Splunk Add-on for Citrix NetScaler](https://docs.splunk.com/Documentation/AddOns/released/CitrixNetScaler/CitrixNetScaler)
- [Citrix ADC — Integrated caching](https://docs.citrix.com/en-us/citrix-adc/current-release/optimization/integrated-caching.html)
