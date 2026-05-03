<!-- AUTO-GENERATED from UC-5.14.45.json — DO NOT EDIT -->

---
id: "5.14.45"
title: "Traefik Middleware Time Share of Request Duration"
status: "draft"
criticality: "high"
splunkPillar: "Observability"
---

# UC-5.14.45 · Traefik Middleware Time Share of Request Duration

> **Criticality:** High &middot; **Difficulty:** Advanced &middot; **Pillar:** Observability &middot; **Type:** Performance &middot; **Status:** Draft

*We watch traefik middleware time share of request duration and catch issues early, before they turn into outages for the people who rely on the network.*

---

## Description

Auth and compression should not dominate latency budgets.

## Value

Operations teams decompose Traefik request latency into middleware processing time vs backend origin time, identifying middleware chains that add disproportionate latency.

## Implementation

If fields absent, export OpenTelemetry traces with span attributes for middleware.

## Detailed Implementation

### Prerequisites
* Traefik access logs with timing details. Key access log fields: `Duration` (total request duration), `OriginDuration` (time from Traefik to backend and back), `OriginStatus`. Middleware timing can be derived as: middleware_time = Duration - OriginDuration. Data in `index=proxy` with `sourcetype=traefik:access`.
* Traefik middleware chain: requests pass through middleware (rate limiting, authentication, headers, compression, circuit breaker, retry) before reaching the backend. If middleware_time is a large fraction of Duration, middleware is the bottleneck, not the backend.

### Step 1 — - Configure data collection
JSON access log with timing:
```yaml
accessLog:
  format: json
  fields:
    headers:
      defaultMode: keep
    names:
      Duration: keep
      OriginDuration: keep
      OriginStatus: keep
```
Verify:
```spl
index=proxy sourcetype="traefik:access" earliest=-4h
| where isnotnull(Duration) AND isnotnull(OriginDuration)
| eval middleware_ms=(tonumber(Duration)-tonumber(OriginDuration))/1000000
| stats avg(middleware_ms) as avg_mw_ms avg(tonumber(OriginDuration)/1000000) as avg_origin_ms
```

### Step 2 — - Create the search and alert

**Primary search -- Middleware vs origin time share:**
```spl
index=proxy sourcetype="traefik:access" earliest=-4h
| eval total_ms=tonumber(Duration)/1000000
| eval origin_ms=tonumber(OriginDuration)/1000000
| eval middleware_ms=total_ms - origin_ms
| where isnotnull(middleware_ms) AND total_ms > 0
| eval mw_pct=round(100*middleware_ms/total_ms, 1)
| bin _time span=5m
| stats avg(mw_pct) as avg_mw_pct avg(middleware_ms) as avg_mw_ms avg(origin_ms) as avg_origin_ms p95(total_ms) as p95_total count as requests by _time, RouterName
| eval bottleneck=case(avg_mw_pct > 50, "MIDDLEWARE (".round(avg_mw_pct, 0)."% of latency)", avg_origin_ms > 2000, "BACKEND (avg ".round(avg_origin_ms, 0)."ms)", 1==1, "OK")
| where bottleneck != "OK"
| table _time, RouterName, requests, avg_mw_ms, avg_origin_ms, avg_mw_pct, p95_total, bottleneck
```

### Step 3 — - Validate
(a) Add a slow middleware (e.g., rate limiter with low burst) and verify middleware_ms increases.
(b) Compare Duration and OriginDuration for a specific route.
(c) Use Traefik built-in metrics: `traefik_service_request_duration_seconds_bucket` for backend latency.

### Step 4 — - Operationalize
Dashboard ("Traefik -- Middleware Timing"):
* Row 1 -- Single-value: "Avg middleware time (ms)", "Avg origin time (ms)", "Middleware % of total".
* Row 2 -- Middleware vs origin time share timechart.
* Row 3 -- Routes where middleware dominates.

### Step 5 — - Troubleshooting

* **High middleware time** -- Identify which middleware is slow. Common culprits: (1) authentication middleware calling external IdP, (2) rate limiter with Redis backend, (3) request body buffering. Disable middlewares one at a time to isolate.

* **Middleware time is zero** -- No middleware configured for this route. This is normal if the route does not need middleware.

* **OriginDuration is null** -- Traefik did not reach the backend (error before forwarding). Check: route configuration and middleware chain for early termination.

## SPL

```spl
index=proxy sourcetype="traefik:access"
| eval mw=tonumber(MiddlewareDuration), total=tonumber(Duration)
| eval mw_pct=if(total>0, round(100*mw/total,1), null())
| where mw_pct > 25
| timechart span=5m perc95(mw_pct) by RouterName
```

## Visualization

Time series for rates and latency, top/dedup for hotspots, single-value alerts on health thresholds.

## Known False Positives

Edge cases: multi-vendor mixes and ad hoc feeds can include lab traffic and partial visibility that mimics issues until scopes are defined. Tuning tip: match this to «Traefik Middleware Time Share of Request Duration» and exclude change windows, scans, and lab VLANs you already expect.

## References

- [Vendor documentation](https://doc.traefik.io/traefik/observability/access-logs/)
