<!-- AUTO-GENERATED from UC-8.4.45.json — DO NOT EDIT -->

---
id: "8.4.45"
title: "PHP-FPM HTTP Method Distribution from Access Log"
status: "draft"
criticality: "low"
splunkPillar: "Observability"
---

# UC-8.4.45 · PHP-FPM HTTP Method Distribution from Access Log

> **Criticality:** Low &middot; **Difficulty:** Beginner &middot; **Pillar:** Observability &middot; **Type:** Analytics, Security &middot; **Status:** Draft

*We use this to support security and product teams with behavioral context.*

---

## Description

Method mix shifts can signal scraping, API abuse, or misconfigured clients. Baselines by pool make anomalies obvious.

## Value

Supports security and API product teams with behavioral context.

## Implementation

Use W3C-like access format with method field; extract `cs_method`.

## SPL

```spl
index=web sourcetype="phpfpm:access"
| stats count by cs_method, pool
| sort - count
```

## CIM SPL

```spl
| tstats `summariesonly` count as events
  from datamodel=Web.Web
  by Web.http_method Web.dest span=5m
| sort -events
```

## Visualization

Time series (pool utilization, queue, latency percentiles), single value alerts, top charts for scripts and methods.

## Known False Positives

Spikes or gaps can follow approved maintenance, load tests, or short collection outages. We add a second signal and a change window before escalating.

## References

- [CIM: Web](https://docs.splunk.com/Documentation/CIM/latest/User/Web)
- [PHP-FPM configuration](https://www.php.net/manual/en/fpm.configuration.php#access-format)
