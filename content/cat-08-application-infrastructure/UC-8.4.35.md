<!-- AUTO-GENERATED from UC-8.4.35.json — DO NOT EDIT -->

---
id: "8.4.35"
title: "PHP-FPM Idle Process Count Trending for Pool Right-Sizing"
status: "draft"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-8.4.35 · PHP-FPM Idle Process Count Trending for Pool Right-Sizing

> **Criticality:** Medium &middot; **Difficulty:** Intermediate &middot; **Pillar:** Observability &middot; **Type:** Capacity &middot; **Status:** Draft

*We watch for signs that optimizes memory versus headroom for predictable workloads.*

---

## Description

Idle workers represent reserved memory; zero idle with a growing listen queue signals undersizing. Chronic excess idle suggests oversized pools.

## Value

Optimizes memory versus headroom for predictable workloads.

## Implementation

Poll status JSON; baseline idle % per pool. Alert when idle_ratio < 5% AND listen_queue_len > 0, or idle_ratio > 70% for 24h.

## SPL

```spl
index=web sourcetype="phpfpm:status"
| eval idle=tonumber(idle_processes), total=tonumber(total_processes)
| eval idle_ratio=if(total>0, round(100*idle/total,1), null())
| timechart span=15m avg(idle_ratio) as idle_pct by pool
```

## Visualization

Time series (pool utilization, queue, latency percentiles), single value alerts, top charts for scripts and methods.

## Known False Positives

Spikes or gaps can follow approved maintenance, load tests, or short collection outages. We add a second signal and a change window before escalating.

## References

- [CIM: Web](https://docs.splunk.com/Documentation/CIM/latest/User/Web)
- [PHP-FPM configuration](https://www.php.net/manual/en/fpm.status.php)
