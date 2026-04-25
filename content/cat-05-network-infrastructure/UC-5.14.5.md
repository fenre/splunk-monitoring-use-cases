<!-- AUTO-GENERATED from UC-5.14.5.json — DO NOT EDIT -->

---
id: "5.14.5"
title: "HAProxy Stick-Table and Rate-Limit Table Pressure"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-5.14.5 · HAProxy Stick-Table and Rate-Limit Table Pressure

## Description

Full stick-tables silently change traffic steering and security posture.

## Value

Keeps bot defenses and ACL stickiness predictable under attack.

## Implementation

Size `stick-table` with `size` and `expire` appropriate to QPS; alert on `table_full` class messages.

## SPL

```spl
index=proxy sourcetype="haproxy:syslog"
| regex _raw="(?i)(stick-table|gpc0|rate-limit|table_full)"
| stats count by host
| where count >= 1
```

## Visualization

Time series for rates and latency, top/dedup for hotspots, single-value alerts on health thresholds.

## References

- [Vendor documentation](https://docs.haproxy.org/2.8/configuration.html#stick-table)
