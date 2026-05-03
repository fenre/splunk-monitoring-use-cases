<!-- AUTO-GENERATED from UC-5.14.52.json — DO NOT EDIT -->

---
id: "5.14.52"
title: "Traefik Weighted Round-Robin Backend Imbalance"
status: "draft"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-5.14.52 · Traefik Weighted Round-Robin Backend Imbalance

> **Criticality:** Medium &middot; **Difficulty:** Advanced &middot; **Pillar:** Observability &middot; **Type:** Performance, Operations &middot; **Status:** Draft

*We watch traefik weighted round-robin backend imbalance and catch issues early, before they turn into outages for the people who rely on the network.*

---

## Description

Skewed weights waste capacity or overload canaries.

## Value

Operations teams detect Traefik weighted round-robin backend distribution imbalances, identifying skewed traffic allocation that overloads specific backends while others are underutilized.

## Implementation

Validate dynamic weights from Consul/Kubernetes; investigate cold endpoints.

## Detailed Implementation

### Prerequisites
* Traefik access logs with backend server information and metrics. Key access log fields: `ServiceAddr` (backend server address), `ServiceName`, `Duration`, `OriginStatus`. Key metrics: `traefik_service_requests_total` (labeled by service and server).
* Weighted round-robin: Traefik supports weighted load balancing where backends receive traffic proportional to their weight. Imbalance occurs when: (1) weights are misconfigured, (2) health checks remove servers, (3) sticky sessions cause skew, (4) uneven backend capacity. Imbalance leads to some backends being overloaded while others are underutilized.

### Step 1 — - Configure data collection
```yaml
# Dynamic config -- weighted WRR
http:
  services:
    my-weighted-service:
      weighted:
        services:
        - name: server1
          weight: 3
        - name: server2
          weight: 1
```
Or with load balancer:
```yaml
http:
  services:
    my-service:
      loadBalancer:
        servers:
        - url: http://10.0.0.1:8080
          weight: 3
        - url: http://10.0.0.2:8080
          weight: 1
```
Verify:
```spl
index=proxy sourcetype="traefik:access" earliest=-4h
| stats count as requests by ServiceName, ServiceAddr
| sort ServiceName, -requests
```

### Step 2 — - Create the search and alert

**Primary search -- Backend distribution imbalance detection:**
```spl
index=proxy sourcetype="traefik:access" earliest=-4h
| stats count as requests avg(tonumber(Duration)/1000000) as avg_latency_ms count(eval(OriginStatus >= 500)) as errors by ServiceName, ServiceAddr
| eventstats sum(requests) as service_total dc(ServiceAddr) as server_count by ServiceName
| eval expected_pct=round(100/server_count, 1)
| eval actual_pct=round(100*requests/service_total, 1)
| eval deviation=abs(actual_pct - expected_pct)
| eval error_rate=round(100*errors/requests, 2)
| eval severity=case(deviation > 20, "WARNING -- >20% deviation from expected distribution", error_rate > 5 AND deviation > 10, "HIGH -- imbalanced AND errors on skewed server", 1==1, "OK")
| where severity != "OK"
| table ServiceName, ServiceAddr, requests, actual_pct, expected_pct, deviation, avg_latency_ms, error_rate, severity
| sort ServiceName, -deviation
```

### Step 3 — - Validate
(a) Send 100 requests and verify distribution matches configured weights.
(b) Traefik API: `curl http://localhost:8080/api/http/services/<service>@provider` -- shows server weights.
(c) Remove one server and verify traffic redistributes.

### Step 4 — - Operationalize
Dashboard ("Traefik -- Load Balance Distribution"):
* Row 1 -- Single-value: "Imbalanced services", "Max deviation (%)".
* Row 2 -- Per-service backend distribution bar chart.
* Row 3 -- Backend latency and error rate comparison.

Alerting:
* Warning (deviation > 20%): traffic distribution skewed.
* High (imbalance + high error rate): overloaded backend from skew.

### Step 5 — - Troubleshooting

* **Imbalance with equal weights** -- Check: (1) sticky sessions are sending all traffic from specific clients to one server, (2) a server was recently readmitted after health check failure (gets burst of new connections), (3) long-lived connections (WebSocket) skew distribution.

* **Intentional imbalance (weighted)** -- If weights are 3:1, expected distribution is 75%:25%. Verify actual matches configured weight ratio, not equal distribution.

* **One server getting all traffic** -- Other servers may be DOWN. Check health check status. Or sticky session cookie is pinning all clients to one server -- verify cookie settings.

## SPL

```spl
index=proxy sourcetype="traefik:access"
| stats count by ServiceName, ServiceAddr
| eventstats sum(count) as tot by ServiceName
| eval share_pct=round(100*count/tot,2)
| where share_pct < 5 OR share_pct > 80
| table ServiceName, ServiceAddr, count, share_pct
```

## Visualization

Time series for rates and latency, top/dedup for hotspots, single-value alerts on health thresholds.

## Known False Positives

Edge cases: multi-vendor mixes and ad hoc feeds can include lab traffic and partial visibility that mimics issues until scopes are defined. Tuning tip: match this to «Traefik Weighted Round-Robin Backend Imbalance» and exclude change windows, scans, and lab VLANs you already expect.

## References

- [Vendor documentation](https://doc.traefik.io/traefik/routing/services/#weighted-round-robin)
