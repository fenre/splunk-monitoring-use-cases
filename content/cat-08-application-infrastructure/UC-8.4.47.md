<!-- AUTO-GENERATED from UC-8.4.47.json — DO NOT EDIT -->

---
id: "8.4.47"
title: "PHP-FPM Status Endpoint Self-Monitoring Response Time"
status: "draft"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-8.4.47 · PHP-FPM Status Endpoint Self-Monitoring Response Time

> **Criticality:** Medium &middot; **Difficulty:** Intermediate &middot; **Pillar:** Observability &middot; **Type:** Performance, Operational &middot; **Status:** Draft

*We watch for signs that catches observer bias where synthetic checks fail before user traffic alarms.*

---

## Description

The status endpoint should answer quickly on a healthy node. Slow polls imply CPU starvation, syscall issues, or overloaded loopback.

## Value

Catches observer bias where synthetic checks fail before user traffic alarms.

## Implementation

Add `poll_duration_ms` in your collector script (time curl). Alert when poller_p95_ms > 500ms.

## SPL

```spl
index=web sourcetype="phpfpm:status"
| eval poll_duration_ms=tonumber(poll_duration_ms)
| where isnotnull(poll_duration_ms)
| timechart span=5m perc95(poll_duration_ms) as poller_p95_ms by host
```

## Visualization

Time series (pool utilization, queue, latency percentiles), single value alerts, top charts for scripts and methods.

## Known False Positives

Response time spikes during JVM garbage collection, connection pool exhaustion, or backend dependency degradation. Load tests, campaigns, and cold caches also move percentiles.

## References

- [CIM: Web](https://docs.splunk.com/Documentation/CIM/latest/User/Web)
- [PHP-FPM configuration](https://www.php.net/manual/en/fpm.status.php)
