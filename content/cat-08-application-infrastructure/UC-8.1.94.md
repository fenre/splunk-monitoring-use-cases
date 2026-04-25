<!-- AUTO-GENERATED from UC-8.1.94.json — DO NOT EDIT -->

---
id: "8.1.94"
title: "WildFly / JBoss Infinispan Cache Eviction and Miss Rate"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-8.1.94 · WildFly / JBoss Infinispan Cache Eviction and Miss Rate

## Description

WildFly embeds Infinispan as its distributed cache for HTTP sessions, EJB stateful beans, Hibernate second-level cache, and JPA entity cache. High eviction rates or low hit ratios indicate that cache regions are undersized, causing repeated database round-trips, increased latency, and wasted CPU on re-computation. Monitoring these metrics prevents silent performance degradation that only surfaces under production load.

## Value

Detecting cache pressure early prevents cascading latency increases. A poorly tuned Infinispan cache can multiply database load by 5-10x during peak traffic, turning a cache-friendly application into one that overwhelms backend datastores.

## Implementation

Deploy Splunk Add-on for JMX on a Universal Forwarder co-located with the WildFly instance. Configure a JMX input targeting org.infinispan:type=Cache,name=*,component=Statistics MBeans. Alternatively, poll the WildFly management API endpoint /subsystem=infinispan/cache-container=*/local-cache=*/component=statistics via a scripted input. Set alert threshold for hit_ratio below 80% sustained over 15 minutes and evictions above 1000 per collection interval. Review cache max-entries and lifespan settings in standalone.xml or domain.xml when alerts fire.

## SPL

```spl
index=appserver sourcetype="jboss:server" OR sourcetype="jmx:jboss"
| search cache AND (eviction OR miss OR hit)
| rex field=_raw "cache=(?<cache_name>[^,\s]+)"
| eval hits=tonumber(coalesce(cache_hits, hits)), misses=tonumber(coalesce(cache_misses, misses)), evictions=tonumber(coalesce(cache_evictions, evictions))
| stats latest(hits) as hits, latest(misses) as misses, latest(evictions) as evictions by host, cache_name
| eval hit_ratio=if((hits+misses)>0, round(100*hits/(hits+misses),1), 0)
| where hit_ratio < 80 OR evictions > 1000
| sort -evictions
```

## Visualization

Table (cache regions with low hit ratio), Line chart (eviction rate over time per cache region), Single value (overall cache hit ratio).

## References

- [WildFly Admin Guide — Infinispan Subsystem](https://docs.wildfly.org/31/Admin_Guide.html#Infinispan_Subsystem)
