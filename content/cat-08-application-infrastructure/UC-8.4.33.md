<!-- AUTO-GENERATED from UC-8.4.33.json — DO NOT EDIT -->

---
id: "8.4.33"
title: "PHP-FPM Slow Request Log — Slowlog Timeout Analysis"
criticality: "high"
splunkPillar: "Observability"
---

# UC-8.4.33 · PHP-FPM Slow Request Log — Slowlog Timeout Analysis

## Description

The slow log captures stack traces for requests exceeding `request_slowlog_timeout`. Mining top scripts guides profiling, database fixes, and opcode cache tuning.

## Value

Turns anecdotal slowness into ranked evidence for engineering backlog.

## Implementation

Enable `slowlog` and `request_slowlog_timeout` in pool config; monitor the slow log file with UF `monitor://`. Create LINE_BREAKER on pool headers `[pool www]`.

## SPL

```spl
index=web sourcetype="phpfpm:slow"
| rex field=_raw "script_filename\s*=\s*(?<script_filename>\S+)"
| stats count by pool, script_filename
| sort - count
| head 20
```

## Visualization

Time series (pool utilization, queue, latency percentiles), single value alerts, top charts for scripts and methods.

## References

- [PHP-FPM configuration](https://www.php.net/manual/en/fpm.configuration.php#slowlog)
