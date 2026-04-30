<!-- AUTO-GENERATED from UC-8.4.39.json — DO NOT EDIT -->

---
id: "8.4.39"
title: "PHP-FPM Pool Restart and Crash Detection"
status: "draft"
criticality: "high"
splunkPillar: "Observability"
---

# UC-8.4.39 · PHP-FPM Pool Restart and Crash Detection

> **Criticality:** High &middot; **Difficulty:** Intermediate &middot; **Pillar:** Observability &middot; **Type:** Change, Fault &middot; **Status:** Draft

*We use this to reduce user-facing latency and 5xx rates by exposing pool saturation, slow scripts, and worker stability before front proxies fail.*

---

## Description

Graceful reloads and worker crashes leave distinct signatures in the FPM master log. Tracking signals and reload phrases helps separate planned deploys from instability and extension segfaults before pools stop accepting traffic.

## Value

Reduces user-facing latency and 5xx rates by exposing pool saturation, slow scripts, and worker stability before front proxies fail.

## Implementation

Monitor FPM master stderr and `journalctl` via syslog; tag `phpfpm:log`. Correlate with deploy windows for graceful reload.

## SPL

```spl
index=web sourcetype="phpfpm:log"
| regex _raw="(?i)(SIGSEGV|SIGABRT|segmentation fault|zend_mm_heap corrupted|exiting|master process.*reload)"
| rex field=_raw "\[pool\s+(?<pool>[^\]]+)\]"
| stats count by host, pool, _raw
| where count >= 1
```

## Visualization

Time series (pool utilization, queue, latency percentiles), single value alerts, top charts for scripts and methods.

## Known False Positives

Spikes or gaps can follow approved maintenance, load tests, or short collection outages. We add a second signal and a change window before escalating.

## References

- [PHP-FPM configuration](https://www.php.net/manual/en/install.fpm.php)
