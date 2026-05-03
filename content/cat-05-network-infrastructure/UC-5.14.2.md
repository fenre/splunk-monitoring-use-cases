<!-- AUTO-GENERATED from UC-5.14.2.json — DO NOT EDIT -->

---
id: "5.14.2"
title: "HAProxy Connection Retry and Redispatch Volume"
status: "draft"
criticality: "high"
splunkPillar: "Observability"
---

# UC-5.14.2 · HAProxy Connection Retry and Redispatch Volume

> **Criticality:** High &middot; **Difficulty:** Intermediate &middot; **Pillar:** Observability &middot; **Type:** Resilience, Performance &middot; **Status:** Draft

*We watch haproxy connection retry and redispatch volume and catch issues early, before they turn into outages for the people who rely on the network.*

---

## Description

Retries absorb brief faults but high volume masks systemic overload or brownouts.

## Value

Operations teams track HAProxy connection retry and redispatch volumes per backend to identify intermittently failing servers and prevent cascading failures from retry storms.

## Implementation

Extend `log-format` to include retry/redispatch counters; validate with `show stat`. Baseline per service.

## Detailed Implementation

### Prerequisites
* HAProxy HTTP logs in `index=proxy` with `sourcetype=haproxy:http`. Key fields: `retries` (number of connection retries), `redispatch` (request re-sent to different server), `backend`, `server`, `Tc` (connect time), `termination_state`.
* HAProxy retries: when a connection to a backend server fails, HAProxy retries on the same server (`retries` count). Redispatch: after retries exhausted, HAProxy sends the request to a different server in the same backend. High retries/redispatches indicate unstable backends.

### Step 1 — - Configure data collection
Ensure retry/redispatch logging:
```
# haproxy.cfg
defaults
    retries 3
    option redispatch
    option httplog
```
Verify:
```spl
index=proxy sourcetype="haproxy:http" earliest=-4h
| where retries > 0 OR match(termination_state, "(?i)R")
| stats count sum(retries) as total_retries by backend
```

### Step 2 — - Create the search and alert

**Primary search -- Retry and redispatch analysis:**
```spl
index=proxy sourcetype="haproxy:http" earliest=-4h
| where retries > 0 OR match(_raw, "(?i)redispatch")
| eval had_redispatch=if(match(termination_state, "(?i)R") OR match(_raw, "(?i)redispatch"), 1, 0)
| stats count as events sum(retries) as total_retries sum(had_redispatch) as redispatches by backend, server
| eval retry_rate=round(total_retries/events, 2)
| eval severity=case(redispatches > 50, "HIGH -- frequent redispatches", total_retries > 100, "WARNING -- elevated retries", 1==1, "INFO")
| lookup haproxy_backends.csv backend, server OUTPUT application
| where severity != "INFO"
| sort severity, -total_retries
```

### Step 3 — - Validate
(a) Introduce network latency to a backend and verify retries increase.
(b) Check HAProxy stats for retry/redispatch counters per backend.
(c) Verify `retries` and `option redispatch` are configured in the backend.

### Step 4 — - Operationalize
Dashboard ("HAProxy -- Retries & Redispatches"):
* Row 1 -- Single-value: "Total retries (4h)", "Redispatches", "Affected backends".
* Row 2 -- Per-backend retry analysis.

Alerting:
* High (redispatches > 50 in 15 min): multiple servers failing -- investigate.
* Warning (retries > 100 in 15 min): connection instability.

### Step 5 — - Troubleshooting

* **High retries on specific server** -- That server is intermittently refusing connections. Check: (1) server connection backlog (`somaxconn`), (2) process resource limits, (3) firewall connection tracking.

* **Redispatches but all servers show UP** -- Servers are passing health checks but failing under load. Health checks may be too lenient (e.g., checking / but app fails on /api). Use application-specific health endpoints.

* **Retries causing cascading failures** -- Each retry adds load to the backend. If backends are overloaded, retries make it worse. Consider reducing `retries` or enabling `option abortonclose`.

## SPL

```spl
index=proxy sourcetype="haproxy:http"
| regex field=_raw "(?i)retry=(?<retry>\d+)"
| stats sum(retry) as retries by backend, server
| where retries > 100
```

## Visualization

Time series for rates and latency, top/dedup for hotspots, single-value alerts on health thresholds.

## Known False Positives

Edge cases: multi-vendor mixes and ad hoc feeds can include lab traffic and partial visibility that mimics issues until scopes are defined. Tuning tip: match this to «HAProxy Connection Retry and Redispatch Volume» and exclude change windows, scans, and lab VLANs you already expect.

## References

- [Vendor documentation](https://docs.haproxy.org/2.8/configuration.html#log-format)
