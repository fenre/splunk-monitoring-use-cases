<!-- AUTO-GENERATED from UC-8.4.43.json — DO NOT EDIT -->

---
id: "8.4.43"
title: "PHP-FPM Unix Socket vs TCP Listen Mode Latency Comparison"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-8.4.43 · PHP-FPM Unix Socket vs TCP Listen Mode Latency Comparison

## Description

Unix domain sockets usually outperform TCP loopback for same-host nginx-to-FPM links. Comparing access-log latency by listen mode validates architecture decisions.

## Value

Quantifies migration benefits when consolidating listeners.

## Implementation

Add custom field from pool config lookup (`listen = /run/php.sock` vs `127.0.0.1:9000`). Compare p95 request_time.

## SPL

```spl
index=web sourcetype="phpfpm:access"
| eval listen_mode=coalesce(listen_transport, server_protocol)
| bin _time span=15m
| stats perc95(request_time) as p95_ms by listen_mode, pool
```

## Visualization

Time series (pool utilization, queue, latency percentiles), single value alerts, top charts for scripts and methods.

## References

- [CIM: Web](https://docs.splunk.com/Documentation/CIM/latest/User/Web)
- [PHP-FPM configuration](https://www.php.net/manual/en/fpm.configuration.php#listen)
