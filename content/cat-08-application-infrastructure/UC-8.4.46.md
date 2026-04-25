<!-- AUTO-GENERATED from UC-8.4.46.json — DO NOT EDIT -->

---
id: "8.4.46"
title: "PHP-FPM PHP Fatal Error Rate from php error_log"
criticality: "high"
splunkPillar: "Observability"
---

# UC-8.4.46 · PHP-FPM PHP Fatal Error Rate from php error_log

## Description

PHP fatal errors stop request handling for that worker and often return 500 to users. Spikes correlate with bad deploys or missing dependencies.

## Value

Speeds rollback decisions with objective error rates.

## Implementation

Forward FPM pool logs with `catch_workers_output=yes` or aggregate `php-fpm.d/*.log` via UF. Tune threshold per environment; suppress known vendor stack traces with lookup.

## SPL

```spl
index=web sourcetype="phpfpm:log"
| regex _raw="(?i)PHP Fatal error"
| bin _time span=5m
| stats count by host, pool, _time
| where count > 10
```

## Visualization

Time series (pool utilization, queue, latency percentiles), single value alerts, top charts for scripts and methods.

## References

- [PHP-FPM configuration](https://www.php.net/manual/en/errorfunc.constants.php)
