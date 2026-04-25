<!-- AUTO-GENERATED from UC-8.4.32.json — DO NOT EDIT -->

---
id: "8.4.32"
title: "PHP-FPM Listen Queue Length Spike Detection"
criticality: "high"
splunkPillar: "Observability"
---

# UC-8.4.32 · PHP-FPM Listen Queue Length Spike Detection

## Description

The listen queue grows when workers cannot accept connections fast enough. A non-zero queue is normal in bursts; sustained growth predicts timeouts upstream.

## Value

Surfaces backlog pressure before nginx or HAProxy logs fill with upstream timed out.

## Implementation

Expose `pm.status_path` on loopback; poll every 30s via UF script. Set alert `listen_queue_len` > 10 sustained 5m. Tune for high-traffic pools.

## SPL

```spl
index=web sourcetype="phpfpm:status"
| eval lql=tonumber(coalesce(listen_queue_len, listen_queue))
| where lql > 0
| timechart span=1m max(lql) as listen_queue by pool, host
```

## Visualization

Time series (pool utilization, queue, latency percentiles), single value alerts, top charts for scripts and methods.

## References

- [CIM: Web](https://docs.splunk.com/Documentation/CIM/latest/User/Web)
- [PHP-FPM configuration](https://www.php.net/manual/en/fpm.configuration.php#pm.status-path)
