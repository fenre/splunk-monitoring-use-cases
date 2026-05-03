<!-- AUTO-GENERATED from UC-5.14.18.json — DO NOT EDIT -->

---
id: "5.14.18"
title: "Varnish Backend Connection Reuse Signals"
status: "draft"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-5.14.18 · Varnish Backend Connection Reuse Signals

> **Criticality:** Medium &middot; **Difficulty:** Intermediate &middot; **Pillar:** Observability &middot; **Type:** Performance &middot; **Status:** Draft

*We watch varnish backend connection reuse signals and catch issues early, before they turn into outages for the people who rely on the network.*

---

## Description

Poor reuse increases latency and CPU on both sides.

## Value

Operations teams monitor Varnish backend connection recycling and reuse ratios, detecting inefficient connection handling that increases TCP handshake overhead and backend load.

## Implementation

Low reuse may indicate TLS handshake storms toward origin.

## Detailed Implementation

### Prerequisites
* Varnish statistics for backend connection management. Key counters: `MAIN.backend_conn` (backend connections made), `MAIN.backend_recycle` (connections recycled/reused), `MAIN.backend_reuse` (connections reused from pool), `MAIN.backend_retry` (retried connections), `MAIN.backend_busy` (backend connections dropped due to max). Data in `index=proxy` with `sourcetype=varnish:stats`.
* Connection reuse: Varnish can keep backend connections open (keepalive) and reuse them for subsequent requests. High reuse ratio = fewer TCP handshakes = lower latency and backend load.

### Step 1 — - Configure data collection
Same as UC-5.14.11. Verify backend connection reuse:
```spl
index=proxy sourcetype="varnish:stats" earliest=-4h
| spath input=_raw path="MAIN.backend_reuse.value" output=reuse
| spath input=_raw path="MAIN.backend_conn.value" output=new_conn
| stats latest(reuse) as reused latest(new_conn) as new_conns
| eval reuse_ratio=round(100*reused/(reused+new_conns), 1)
```

### Step 2 — - Create the search and alert

**Primary search -- Backend connection reuse trending:**
```spl
index=proxy sourcetype="varnish:stats" earliest=-4h
| spath input=_raw path="MAIN.backend_conn.value" output=new_conn
| spath input=_raw path="MAIN.backend_reuse.value" output=reuse
| spath input=_raw path="MAIN.backend_recycle.value" output=recycle
| spath input=_raw path="MAIN.backend_busy.value" output=busy
| spath input=_raw path="MAIN.backend_retry.value" output=retry
| eval new_conn=tonumber(new_conn), reuse=tonumber(reuse), recycle=tonumber(recycle), busy=tonumber(busy), retry=tonumber(retry)
| bin _time span=5m
| stats latest(new_conn) as conn latest(reuse) as reuse latest(recycle) as recycle latest(busy) as busy latest(retry) as retry by _time
| streamstats current=f last(conn) as prev_conn last(reuse) as prev_reuse last(busy) as prev_busy last(retry) as prev_retry
| eval new_rate=conn - prev_conn
| eval reuse_rate=reuse - prev_reuse
| eval busy_rate=busy - prev_busy
| eval retry_rate=retry - prev_retry
| where isnotnull(new_rate) AND (new_rate + reuse_rate) > 0
| eval reuse_pct=round(100*reuse_rate/(new_rate + reuse_rate), 1)
| eval severity=case(busy_rate > 10, "CRITICAL -- backend connections dropped", reuse_pct < 50 AND new_rate > 100, "WARNING -- low connection reuse", retry_rate > 10, "WARNING -- connection retries", 1==1, "OK")
| where severity != "OK"
| table _time, new_rate, reuse_rate, reuse_pct, busy_rate, retry_rate, severity
```

### Step 3 — - Validate
(a) `varnishstat -1 | grep backend_`.
(b) Check if keepalive is enabled: `varnishadm param.show backend_idle_timeout` (default 60s).
(c) Verify with backend access logs that connections are being reused (same source port for multiple requests).

### Step 4 — - Operationalize
Dashboard ("Varnish -- Backend Connections"):
* Row 1 -- Single-value: "Connection reuse %", "New connections", "Busy (dropped)", "Retries".
* Row 2 -- Reuse ratio timechart.

Alerting:
* Critical (busy > 10/5m): connections being dropped.
* Warning (reuse < 50%): backend keepalive may be misconfigured.

### Step 5 — - Troubleshooting

* **Low reuse ratio** -- Backend may be closing connections after each request. Check: (1) backend `Connection: close` header, (2) backend keepalive timeout < Varnish's `backend_idle_timeout`, (3) backend maxconn.

* **backend_busy events** -- All connections to a backend are in use. Increase backend `.max_connections` in VCL. Also check if a slow backend is holding connections open.

* **High retry rate** -- Varnish is retrying failed connections. Check backend availability and network stability.

## SPL

```spl
index=proxy sourcetype="varnish:stats"
| eval conn=tonumber(backend_conn), reuse=tonumber(backend_recycle)
| eval reuse_ratio=if(conn>0, round(100*reuse/conn,1), null())
| timechart span=15m avg(reuse_ratio) by host
```

## Visualization

Time series for rates and latency, top/dedup for hotspots, single-value alerts on health thresholds.

## Known False Positives

Edge cases: multi-vendor mixes and ad hoc feeds can include lab traffic and partial visibility that mimics issues until scopes are defined. Tuning tip: match this to «Varnish Backend Connection Reuse Signals» and exclude change windows, scans, and lab VLANs you already expect.

## References

- [Vendor documentation](https://varnish-cache.org/docs/trunk/reference/varnishstat.html)
