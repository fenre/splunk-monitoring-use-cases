<!-- AUTO-GENERATED from UC-5.14.1.json — DO NOT EDIT -->

---
id: "5.14.1"
title: "HAProxy Backend Server Health Check Failures"
criticality: "critical"
splunkPillar: "Observability"
---

# UC-5.14.1 · HAProxy Backend Server Health Check Failures

## Description

Backend health checks prevent traffic to failed nodes; log evidence shows which farm member and protocol failed first.

## Value

Cuts time to restore origin pools by pinpointing DOWN transitions and related 5xx.

## Implementation

Forward HAProxy logs via syslog or UF file tail. Map `backend`/`server` fields per HAProxy 2.8 `log-format`. Correlate with `haproxy:stats` CSV from `show stat`.

## SPL

```spl
index=proxy sourcetype="haproxy:http"
| where status >= 500 OR match(_raw, "(?i)NOLB|no server") OR match(_raw, "(?i)layer7 invalid")
| stats count by backend, server
| sort - count
```

## Visualization

Time series for rates and latency, top/dedup for hotspots, single-value alerts on health thresholds.

## References

- [Vendor documentation](https://docs.haproxy.org/2.8/configuration.html#8.2.1)
