<!-- AUTO-GENERATED from UC-8.4.36.json — DO NOT EDIT -->

---
id: "8.4.36"
title: "PHP-FPM Request Duration P95/P99 from Access Log"
criticality: "high"
splunkPillar: "Observability"
---

# UC-8.4.36 · PHP-FPM Request Duration P95/P99 from Access Log

## Description

Percentiles from the FPM access log quantify user-visible latency better than averages alone. P95/P99 spikes often precede saturation on status metrics.

## Value

Supports SLO dashboards and error-budget discussions tied to real request timing.

## Implementation

Configure `access.log` with `%d` duration; ingest as `phpfpm:access`. Map `request_time` in `props.conf`.

## SPL

```spl
index=web sourcetype="phpfpm:access"
| eval dur_ms=tonumber(coalesce(request_time, request_duration, duration_ms))
| where isnotnull(dur_ms)
| timechart span=5m perc95(dur_ms) as p95_ms perc99(dur_ms) as p99_ms by pool
```

## CIM SPL

```spl
| tstats `summariesonly` perc95(Web.duration) as p95_ms avg(Web.duration) as avg_ms
  from datamodel=Web.Web
  by Web.dest Web.uri_path span=5m
| where p95_ms > 2000
```

## Visualization

Time series (pool utilization, queue, latency percentiles), single value alerts, top charts for scripts and methods.

## References

- [CIM: Web](https://docs.splunk.com/Documentation/CIM/latest/User/Web)
- [PHP-FPM configuration](https://www.php.net/manual/en/fpm.configuration.php#access-log)
