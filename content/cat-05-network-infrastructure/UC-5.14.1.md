<!-- AUTO-GENERATED from UC-5.14.1.json — DO NOT EDIT -->

---
id: "5.14.1"
title: "HAProxy Backend Server Health Check Failures"
status: "draft"
criticality: "critical"
splunkPillar: "Observability"
---

# UC-5.14.1 · HAProxy Backend Server Health Check Failures

> **Criticality:** Critical &middot; **Difficulty:** Beginner &middot; **Pillar:** Observability &middot; **Type:** Availability, Performance &middot; **Status:** Draft

*We watch haproxy backend server health check failures and catch issues early, before they turn into outages for the people who rely on the network.*

---

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

## Known False Positives

Edge cases: multi-vendor mixes and ad hoc feeds can include lab traffic and partial visibility that mimics issues until scopes are defined. Tuning tip: match this to «HAProxy Backend Server Health Check Failures» and exclude change windows, scans, and lab VLANs you already expect.

## References

- [Vendor documentation](https://docs.haproxy.org/2.8/configuration.html#8.2.1)
