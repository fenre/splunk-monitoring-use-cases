<!-- AUTO-GENERATED from UC-8.4.41.json — DO NOT EDIT -->

---
id: "8.4.41"
title: "PHP-FPM Per-Pool Request Throughput Comparison"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-8.4.41 · PHP-FPM Per-Pool Request Throughput Comparison

## Description

Request volume per pool shows which tenants or apps dominate capacity. Imbalance may indicate routing bugs or noisy neighbors.

## Value

Informs fair sharing, rate limits, and horizontal scale plans.

## Implementation

Ensure access log includes pool name or map via `SCRIPT_FILENAME` lookup. Use `sistats` for large volumes.

## SPL

```spl
index=web sourcetype="phpfpm:access"
| bin _time span=5m
| stats count as rps by pool, _time
| eventstats sum(rps) as total_rps by _time
| eval share_pct=round(100*rps/total_rps,1)
```

## Visualization

Time series (pool utilization, queue, latency percentiles), single value alerts, top charts for scripts and methods.

## References

- [CIM: Web](https://docs.splunk.com/Documentation/CIM/latest/User/Web)
- [PHP-FPM configuration](https://www.php.net/manual/en/fpm.configuration.php#access-format)
