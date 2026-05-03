<!-- AUTO-GENERATED from UC-5.14.48.json — DO NOT EDIT -->

---
id: "5.14.48"
title: "Traefik Retry Middleware Activations"
status: "draft"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-5.14.48 · Traefik Retry Middleware Activations

> **Criticality:** Medium &middot; **Difficulty:** Intermediate &middot; **Pillar:** Observability &middot; **Type:** Resilience, Fault &middot; **Status:** Draft

*We watch traefik retry middleware activations and catch issues early, before they turn into outages for the people who rely on the network.*

---

## Description

Retries mask flaky upstreams but add load when misconfigured.

## Value

Operations teams track Traefik retry middleware activations per service, detecting backend instability and evaluating retry storm risk on degraded services.

## Implementation

Enable retries only on idempotent routes; watch for retry amplification.

## Detailed Implementation

### Prerequisites
* Traefik access logs with retry middleware information. Key access log fields: `RetryAttempts`, `RouterName`, `ServiceName`, `OriginStatus`. Data in `index=proxy` with `sourcetype=traefik:access`. Key metrics: `traefik_service_retries_total`.
* Retry middleware: Traefik can retry failed requests to different backend servers. Configured with `retry.attempts` (max retries) and `retry.initialInterval`. Retries are triggered on network errors and 5xx responses. High retry rates indicate backend instability and can amplify load on already-struggling backends.

### Step 1 — - Configure data collection
```yaml
# Dynamic config
http:
  middlewares:
    retry-middleware:
      retry:
        attempts: 3
        initialInterval: 100ms
  routers:
    my-router:
      rule: "Host(`app.example.com`)"
      middlewares:
      - retry-middleware
      service: my-service
```
Verify:
```spl
index=proxy sourcetype="traefik:access" earliest=-4h
| where tonumber(RetryAttempts) > 0
| stats count sum(RetryAttempts) as total_retries by ServiceName
```

### Step 2 — - Create the search and alert

**Primary search -- Retry middleware activation analysis:**
```spl
index=proxy sourcetype="traefik:access" earliest=-4h
| eval retries=tonumber(coalesce(RetryAttempts, 0))
| where retries > 0
| bin _time span=5m
| stats count as retried_requests sum(retries) as total_retries avg(retries) as avg_retries max(retries) as max_retries by _time, ServiceName
| eval severity=case(total_retries > 200, "HIGH -- heavy retry activity", retried_requests > 50, "WARNING -- significant retried requests", avg_retries > 2, "WARNING -- requests averaging >2 retries", 1==1, "OK")
| where severity != "OK"
| table _time, ServiceName, retried_requests, total_retries, avg_retries, max_retries, severity
```

**From metrics:**
```spl
index=proxy sourcetype="traefik:metrics" earliest=-4h
| where match(metric_name, "service_retries_total")
| bin _time span=5m
| stats latest(metric_value) as retries by _time, service
| streamstats current=f last(retries) as prev by service
| eval retry_rate=retries - prev
| where isnotnull(retry_rate) AND retry_rate > 0
| table _time, service, retry_rate
```

### Step 3 — - Validate
(a) Intentionally return 503 from a backend and verify retries happen.
(b) Traefik API: `curl http://localhost:8080/api/http/middlewares` -- shows retry config.
(c) Check that successful retries result in 200 in the access log (OriginStatus may differ from DownstreamStatus).

### Step 4 — - Operationalize
Dashboard ("Traefik -- Retries"):
* Row 1 -- Single-value: "Retried requests (4h)", "Total retries", "Avg retries/request".
* Row 2 -- Retry rate timechart by service.

Alerting:
* High (> 200 retries/5m): backend instability.
* Warning (avg retries > 2): most retried requests exhausting attempts.

### Step 5 — - Troubleshooting

* **High retry rate on specific service** -- Backend servers in that service are intermittently failing. Check: (1) health check is catching unhealthy servers, (2) backend resource utilization (CPU, memory, connections).

* **Retries causing cascade** -- Each retry adds load. If backends are already overloaded, retries make it worse. Consider: (1) reducing `attempts`, (2) increasing `initialInterval` for backoff, (3) circuit breaker middleware.

* **All retry attempts exhausted** -- Request failed after max retries. Client receives the last error. Check: number of healthy backend servers -- if only 1-2 remain, retries to the same failing server are pointless.

## SPL

```spl
index=proxy sourcetype="traefik:access"
| where RetryAttempts > 0
| stats sum(RetryAttempts) as retries by ServiceName
| sort - retries
```

## Visualization

Time series for rates and latency, top/dedup for hotspots, single-value alerts on health thresholds.

## Known False Positives

Edge cases: multi-vendor mixes and ad hoc feeds can include lab traffic and partial visibility that mimics issues until scopes are defined. Tuning tip: match this to «Traefik Retry Middleware Activations» and exclude change windows, scans, and lab VLANs you already expect.

## References

- [Vendor documentation](https://doc.traefik.io/traefik/middlewares/http/retry/)
