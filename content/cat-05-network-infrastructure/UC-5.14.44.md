<!-- AUTO-GENERATED from UC-5.14.44.json — DO NOT EDIT -->

---
id: "5.14.44"
title: "Traefik Service Health Check Failures"
status: "draft"
criticality: "critical"
splunkPillar: "Observability"
---

# UC-5.14.44 · Traefik Service Health Check Failures

> **Criticality:** Critical &middot; **Difficulty:** Beginner &middot; **Pillar:** Observability &middot; **Type:** Availability &middot; **Status:** Draft

*We watch traefik service health check failures and catch issues early, before they turn into outages for the people who rely on the network.*

---

## Description

Router health drives load balancing; silent failures hurt most.

## Value

Operations teams detect Traefik service health check failures and server DOWN transitions, identifying backend capacity reductions across dynamically discovered services.

## Implementation

Ship container stdout via sidecar; set log level INFO in prod.

## Detailed Implementation

### Prerequisites
* Traefik access logs and metrics. Key metrics: `traefik_service_server_up` (gauge, 0/1 per server), `traefik_service_requests_total` (with code label showing 5xx). Access log fields: `ServiceName`, `OriginStatus`, `DownstreamStatus`, `Duration`.
* Traefik health checks: configured per service with `healthCheck.path`, `healthCheck.interval`, `healthCheck.timeout`. When a server fails health checks, Traefik stops routing traffic to it. Unlike HAProxy, Traefik integrates with service discovery (Docker, Kubernetes, Consul) so servers can also disappear from the pool when containers stop.

### Step 1 — - Configure data collection
Dynamic config (file provider or Docker labels):
```yaml
# dynamic config
http:
  services:
    my-service:
      loadBalancer:
        healthCheck:
          path: /health
          interval: 10s
          timeout: 5s
        servers:
        - url: http://10.0.0.1:8080
        - url: http://10.0.0.2:8080
```
Verify:
```spl
index=proxy sourcetype="traefik:metrics" earliest=-4h
| where match(metric_name, "service_server_up")
| stats latest(metric_value) as status by service, url
| where status=0
```

### Step 2 — - Create the search and alert

**Primary search -- Service health check failure detection:**
```spl
index=proxy sourcetype="traefik:metrics" earliest=-4h
| where match(metric_name, "service_server_up")
| eval is_down=if(metric_value=0, 1, 0)
| stats latest(metric_value) as status latest(_time) as last_check sum(is_down) as down_checks count as total_checks by service, url
| eval health=if(status=0, "DOWN", "UP")
| eval severity=case(health="DOWN", "CRITICAL -- server is DOWN", down_checks > 5 AND health="UP", "WARNING -- recent flapping (".down_checks." failures)", 1==1, "OK")
| where severity != "OK"
| table service, url, health, down_checks, total_checks, last_check, severity
```

**From access logs (backend errors):**
```spl
index=proxy sourcetype="traefik:access" earliest=-4h
| where OriginStatus >= 500
| stats count as errors by ServiceName, ServiceAddr
| sort -errors
```

### Step 3 — - Validate
(a) Traefik dashboard: `http://<traefik>:8080/dashboard/` -- shows service health status.
(b) Traefik API: `curl http://localhost:8080/api/http/services` -- lists services with server statuses.
(c) Stop a backend server and verify it is marked DOWN.

### Step 4 — - Operationalize
Dashboard ("Traefik -- Service Health"):
* Row 1 -- Single-value: "DOWN servers", "Total servers", "Services with failures".
* Row 2 -- Server health status table.
* Row 3 -- Backend error rate timechart.

Alerting:
* Critical (server DOWN): traffic no longer being routed to this server.
* Warning (frequent flapping): server intermittently failing health checks.

### Step 5 — - Troubleshooting

* **Server DOWN but application works** -- Health check path may differ from application path. Verify: `healthCheck.path` is correct and returns 2xx.

* **All servers DOWN for a service** -- Traefik will return 503 for all requests to this service. Check: (1) backend network connectivity, (2) common dependency failure, (3) DNS resolution.

* **Health checks passing but backend errors** -- Health check is too basic. Use an endpoint that tests full application stack (DB, cache, dependencies).

## SPL

```spl
index=proxy sourcetype="traefik:log"
| regex _raw="(?i)(Health check failed|Status.*DOWN|Server.*Unhealthy)"
| stats count by service_name
| sort - count
```

## Visualization

Time series for rates and latency, top/dedup for hotspots, single-value alerts on health thresholds.

## Known False Positives

Edge cases: multi-vendor mixes and ad hoc feeds can include lab traffic and partial visibility that mimics issues until scopes are defined. Tuning tip: match this to «Traefik Service Health Check Failures» and exclude change windows, scans, and lab VLANs you already expect.

## References

- [Vendor documentation](https://doc.traefik.io/traefik/routing/services/#health-check)
