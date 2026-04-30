<!-- AUTO-GENERATED from UC-8.4.44.json — DO NOT EDIT -->

---
id: "8.4.44"
title: "PHP-FPM Error Log Pattern Detection (segfault, SIGSEGV)"
status: "draft"
criticality: "critical"
splunkPillar: "Observability"
---

# UC-8.4.44 · PHP-FPM Error Log Pattern Detection (segfault, SIGSEGV)

> **Criticality:** Critical &middot; **Difficulty:** Intermediate &middot; **Pillar:** Observability &middot; **Type:** Fault, Security &middot; **Status:** Draft

*We use this to reduce prolonged partial outages from recycling crash loops.*

---

## Description

Segfault and heap corruption messages in FPM logs indicate unstable extensions or malicious input. These events warrant immediate isolation.

## Value

Reduces prolonged partial outages from recycling crash loops.

## Implementation

Forward php-fpm error log; set `LINE_BREAKER` for `[pool` blocks. Page on first match; attach core dump policy.

## SPL

```spl
index=web sourcetype="phpfpm:log" OR index=main sourcetype="phpfpm:log"
| regex _raw="(?i)(SIGSEGV|segmentation fault|zend_mm_heap corrupted|child exited on signal)"
| stats count by host, pool
| where count >= 1
```

## Visualization

Time series (pool utilization, queue, latency percentiles), single value alerts, top charts for scripts and methods.

## Known False Positives

Spikes or gaps can follow approved maintenance, load tests, or short collection outages. We add a second signal and a change window before escalating.

## References

- [PHP-FPM configuration](https://www.php.net/manual/en/install.fpm.php)
