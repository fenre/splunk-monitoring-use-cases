<!-- AUTO-GENERATED from UC-5.14.43.json — DO NOT EDIT -->

---
id: "5.14.43"
title: "Traefik Entrypoint Open Connections"
status: "draft"
criticality: "high"
splunkPillar: "Observability"
---

# UC-5.14.43 · Traefik Entrypoint Open Connections

> **Criticality:** High &middot; **Difficulty:** Intermediate &middot; **Pillar:** Observability &middot; **Type:** Capacity, Performance &middot; **Status:** Draft

*We watch traefik entrypoint open connections and catch issues early, before they turn into outages for the people who rely on the network.*

---

## Description

Connection growth predicts fds and memory pressure.

## Value

Operations teams track Traefik entrypoint open connection counts to detect connection exhaustion attacks, capacity limits, and idle connection leaks.

## Implementation

Enable `--metrics.prometheus`; label series by entrypoint. Use OTel if multi-tenant.

## Detailed Implementation

### Prerequisites
* Traefik access logs and/or Prometheus metrics forwarded to Splunk. Data in `index=proxy` with `sourcetype=traefik:access` (JSON or CLF access log) or `sourcetype=traefik:metrics` (Prometheus scrape). Key metrics: `traefik_entrypoint_open_connections` (gauge, labeled by entrypoint and protocol), `traefik_entrypoint_requests_total`.
* Entrypoints: Traefik's network listeners (e.g., `:80/http`, `:443/https`). Open connections is the number of active TCP connections on each entrypoint. High values indicate: (1) legitimate traffic surge, (2) slowloris/connection exhaustion attack, (3) connection leak from clients not closing.

### Step 1 — - Configure data collection
Enable Traefik access log and metrics:
```yaml
# traefik.yml (static config)
accessLog:
  filePath: /var/log/traefik/access.log
  format: json
  fields:
    headers:
      defaultMode: keep

metrics:
  prometheus:
    entryPoint: metrics
    addEntryPointsLabels: true
    addServicesLabels: true

entryPoints:
  web:
    address: ":80"
  websecure:
    address: ":443"
  metrics:
    address: ":8082"
```
Verify:
```spl
index=proxy sourcetype="traefik:metrics" earliest=-4h
| where match(metric_name, "entrypoint_open_connections")
| stats latest(metric_value) as open_conns by entrypoint
```

### Step 2 — - Create the search and alert

**Primary search -- Open connections per entrypoint:**
```spl
index=proxy sourcetype="traefik:metrics" earliest=-4h
| where match(metric_name, "entrypoint_open_connections")
| bin _time span=5m
| stats avg(metric_value) as avg_open max(metric_value) as max_open by _time, entrypoint
| eval severity=case(max_open > 10000, "CRITICAL -- >10K open connections", max_open > 5000, "HIGH -- >5K connections", avg_open > 2000, "WARNING -- sustained high connections", 1==1, "OK")
| where severity != "OK"
| table _time, entrypoint, avg_open, max_open, severity
```

**From access log (connection counting):**
```spl
index=proxy sourcetype="traefik:access" earliest=-1h
| bin _time span=5m
| stats dc(ClientAddr) as unique_clients count as requests by _time, entrypoint
| table _time, entrypoint, unique_clients, requests
```

### Step 3 — - Validate
(a) Traefik API dashboard: `http://<traefik>:8080/api/entrypoints` -- shows entrypoint config.
(b) Compare with `curl http://localhost:8082/metrics | grep entrypoint_open`.
(c) Load test with many concurrent connections and verify gauge increases.

### Step 4 — - Operationalize
Dashboard ("Traefik -- Entrypoint Connections"):
* Row 1 -- Single-value per entrypoint: "Open connections", "Unique clients", "Requests/sec".
* Row 2 -- Connection count timechart.

Alerting:
* Critical (> 10K open connections): potential exhaustion or attack.
* High (> 5K sustained): capacity planning needed.

### Step 5 — - Troubleshooting

* **Connections growing but requests flat** -- Clients are opening connections without sending requests (idle/keepalive). Tune: `transport.respondingTimeouts.idleTimeout` (default 180s) in Traefik config.

* **Sudden connection spike** -- Check for: (1) DDoS/slowloris attack (many connections from few IPs), (2) bot scraping, (3) legitimate traffic event. Examine: per-IP connection counts.

* **Connections not decreasing** -- Connection leak. Check: (1) backend is sending responses, (2) no timeout misconfiguration, (3) client-side keepalive settings.

## SPL

```spl
index=proxy sourcetype="traefik:metrics"
| search metric_name="*entrypoint*open_connections*" OR match(metric_name, "traefik_entrypoint_open_connections")
| eval v=tonumber(metric_value)
| timechart span=1m max(v) by entrypoint
```

## Visualization

Time series for rates and latency, top/dedup for hotspots, single-value alerts on health thresholds.

## Known False Positives

Edge cases: multi-vendor mixes and ad hoc feeds can include lab traffic and partial visibility that mimics issues until scopes are defined. Tuning tip: match this to «Traefik Entrypoint Open Connections» and exclude change windows, scans, and lab VLANs you already expect.

## References

- [Vendor documentation](https://doc.traefik.io/traefik/observability/metrics/prometheus/)
