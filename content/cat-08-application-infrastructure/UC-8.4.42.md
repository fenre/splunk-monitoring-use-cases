<!-- AUTO-GENERATED from UC-8.4.42.json — DO NOT EDIT -->

---
id: "8.4.42"
title: "PHP-FPM Child Process Spawn vs Exit Rate"
criticality: "high"
splunkPillar: "Observability"
---

# UC-8.4.42 · PHP-FPM Child Process Spawn vs Exit Rate

## Description

Rapid changes in `total_processes` indicate recycling, crashes, or aggressive scaling. Comparing churn to `pm.max_requests` distinguishes healthy recycling from faults.

## Value

Shortens MTTR for extension crashes misread as traffic issues.

## Implementation

Poll status frequently enough to see step changes; compare with `pm.max_requests` setting from config lookup.

## SPL

```spl
index=web sourcetype="phpfpm:status"
| eval tc=tonumber(total_processes)
| sort 0 host, pool, _time
| streamstats window=2 global=f current=f last(tc) as prev_tc by host, pool
| eval delta_tp=tc-prev_tc
| timechart span=5m sum(abs(delta_tp)) as process_churn by pool
```

## Visualization

Time series (pool utilization, queue, latency percentiles), single value alerts, top charts for scripts and methods.

## References

- [CIM: Web](https://docs.splunk.com/Documentation/CIM/latest/User/Web)
- [PHP-FPM configuration](https://www.php.net/manual/en/fpm.configuration.php#pm.max-requests)
