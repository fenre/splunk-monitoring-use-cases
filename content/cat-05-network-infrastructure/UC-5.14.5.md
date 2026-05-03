<!-- AUTO-GENERATED from UC-5.14.5.json — DO NOT EDIT -->

---
id: "5.14.5"
title: "HAProxy Stick-Table and Rate-Limit Table Pressure"
status: "draft"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-5.14.5 · HAProxy Stick-Table and Rate-Limit Table Pressure

> **Criticality:** Medium &middot; **Difficulty:** Advanced &middot; **Pillar:** Observability &middot; **Type:** Security, Performance &middot; **Status:** Draft

*We watch haproxy stick-table and rate-limit table pressure and catch issues early, before they turn into outages for the people who rely on the network.*

---

## Description

Full stick-tables silently change traffic steering and security posture.

## Value

Operations teams correlate HAProxy 5xx error rates per backend with specific HTTP status codes (502/503/504), distinguishing backend application failures from HAProxy-layer connection issues.

## Implementation

Size `stick-table` with `size` and `expire` appropriate to QPS; alert on `table_full` class messages.

## Detailed Implementation

### Prerequisites
* HAProxy HTTP logs with status code fields. Key fields: `status_code` (HTTP response status), `backend`, `server`, `http_request` (method + URI). Data in `index=proxy` with `sourcetype=haproxy:http`.
* HAProxy-generated vs backend-generated errors: HAProxy itself can return 408 (request timeout), 502 (bad gateway), 503 (service unavailable), 504 (gateway timeout). Backend errors are simply proxied through.

### Step 1 — - Configure data collection
Verify HTTP status code logging:
```spl
index=proxy sourcetype="haproxy:http" earliest=-4h
| eval status_class=substr(status_code, 1, 1)."xx"
| stats count by status_class
```

### Step 2 — - Create the search and alert

**Primary search -- Error rate per backend with 5xx breakdown:**
```spl
index=proxy sourcetype="haproxy:http" earliest=-4h
| eval status_class=substr(status_code, 1, 1)."xx"
| bin _time span=5m
| stats count as total count(eval(status_class="4xx")) as client_errors count(eval(status_class="5xx")) as server_errors count(eval(status_code=502)) as bad_gateway count(eval(status_code=503)) as svc_unavail count(eval(status_code=504)) as gw_timeout by _time, backend
| eval error_rate_pct=round(100*server_errors/total, 2)
| eval severity=case(error_rate_pct > 10, "CRITICAL -- >10% server errors", error_rate_pct > 5, "HIGH -- >5% server errors", error_rate_pct > 1, "WARNING -- >1% server errors", 1==1, "OK")
| where severity != "OK"
| table _time, backend, total, server_errors, error_rate_pct, bad_gateway, svc_unavail, gw_timeout, severity
```

**Top error URLs:**
```spl
index=proxy sourcetype="haproxy:http" status_code>=500 earliest=-4h
| rex field=http_request "\S+ (?<uri>\S+)"
| stats count as errors by backend, uri, status_code
| sort -errors | head 20
```

### Step 3 — - Validate
(a) Intentionally return 503 from a backend and verify it appears in the search.
(b) Compare error rates with HAProxy stats page `err_resp` column.
(c) Validate 502 vs 503 vs 504 distinction: 502 = backend sent invalid response, 503 = no server available, 504 = backend took too long.

### Step 4 — - Operationalize
Dashboard ("HAProxy -- Error Rates"):
* Row 1 -- Single-value: "5xx rate (%)", "502 count", "503 count", "504 count".
* Row 2 -- Error rate timechart per backend.
* Row 3 -- Top error URLs table.

Alerting:
* Critical (5xx rate > 10% for > 5 min): major outage.
* High (5xx rate > 5%): significant degradation.

### Step 5 — - Troubleshooting

* **502 Bad Gateway** -- HAProxy connected to backend but received invalid response. Check: (1) backend is sending partial responses, (2) backend process crashed mid-request, (3) backend HTTP version mismatch.

* **503 Service Unavailable** -- No backend server available. Check: (1) all servers in backend DOWN, (2) maxconn reached on all servers, (3) maintenance mode enabled.

* **504 Gateway Timeout** -- Backend didn't respond within timeout. Check: `timeout server` in haproxy.cfg. Default is 50s. Increase if backend genuinely needs more time, but investigate slow queries first.

## SPL

```spl
index=proxy sourcetype="haproxy:syslog"
| regex _raw="(?i)(stick-table|gpc0|rate-limit|table_full)"
| stats count by host
| where count >= 1
```

## Visualization

Time series for rates and latency, top/dedup for hotspots, single-value alerts on health thresholds.

## Known False Positives

Edge cases: multi-vendor mixes and ad hoc feeds can include lab traffic and partial visibility that mimics issues until scopes are defined. Tuning tip: match this to «HAProxy Stick-Table and Rate-Limit Table Pressure» and exclude change windows, scans, and lab VLANs you already expect.

## References

- [Vendor documentation](https://docs.haproxy.org/2.8/configuration.html#stick-table)
