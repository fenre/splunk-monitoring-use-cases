<!-- AUTO-GENERATED from UC-8.4.37.json — DO NOT EDIT -->

---
id: "8.4.37"
title: "PHP-FPM max_children Reached and 503 Correlation"
criticality: "critical"
splunkPillar: "Observability"
---

# UC-8.4.37 · PHP-FPM max_children Reached and 503 Correlation

## Description

The `max children reached` counter increments when FPM cannot spawn workers to accept new connections. It aligns with application errors and proxy connection failures.

## Value

Triggers immediate scaling or config changes instead of waiting for global outage metrics.

## Implementation

Alert on any `max_children_reached` increase. Correlate with `phpfpm:access` 5xx and front-end nginx/haproxy errors.

## SPL

```spl
index=web sourcetype="phpfpm:status"
| eval mcr=tonumber(max_children_reached)
| where mcr > 0
| timechart span=5m sum(mcr) as max_children_reached_events by pool, host
```

## Visualization

Time series (pool utilization, queue, latency percentiles), single value alerts, top charts for scripts and methods.

## References

- [CIM: Web](https://docs.splunk.com/Documentation/CIM/latest/User/Web)
- [PHP-FPM configuration](https://bugs.php.net/bug.php?id=bug_report)
