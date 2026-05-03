<!-- AUTO-GENERATED from UC-5.14.40.json — DO NOT EDIT -->

---
id: "5.14.40"
title: "Envoy Upstream Connection Pool Overflow"
status: "draft"
criticality: "critical"
splunkPillar: "Observability"
---

# UC-5.14.40 · Envoy Upstream Connection Pool Overflow

> **Criticality:** Critical &middot; **Difficulty:** Advanced &middot; **Pillar:** Observability &middot; **Type:** Availability, Capacity &middot; **Status:** Draft

*We watch envoy upstream connection pool overflow and catch issues early, before they turn into outages for the people who rely on the network.*

---

## Description

Pool overflow produces 503s without obvious CPU load.

## Value

Operations teams detect Envoy upstream connection pool overflows where the per-cluster max_connections limit is exhausted, causing request failures from connection-level saturation.

## Implementation

Increase `max_connections` and `max_pending_requests` carefully; verify upstream capacity.

## Detailed Implementation

### Prerequisites
* Envoy access logs and metrics. Key response flags: `UO` (upstream overflow -- connection pool exhausted). Key metrics: `envoy_cluster_upstream_cx_overflow`, `envoy_cluster_upstream_cx_pool_overflow`, `envoy_cluster_upstream_cx_active`, `envoy_cluster_upstream_cx_max_active`.
* Connection pool overflow: Envoy maintains connection pools per upstream cluster. When `max_connections` (circuit breaker) is reached for a cluster, new requests overflow and get 503. Different from circuit breaker `max_requests` -- this specifically tracks connection-level exhaustion.

### Step 1 — - Configure data collection
```yaml
clusters:
- name: my_service
  circuit_breakers:
    thresholds:
    - max_connections: 1024
      max_pending_requests: 1024
      max_requests: 1024
  connect_timeout: 5s
```
Verify:
```spl
index=proxy (sourcetype="envoy:access" OR sourcetype="envoy:metrics") earliest=-4h
| where match(response_flags, "UO") OR match(metric_name, "upstream_cx_overflow|cx_pool_overflow")
| stats count
```

### Step 2 — - Create the search and alert

**Primary search -- Connection pool overflow analysis:**
```spl
index=proxy sourcetype="envoy:access" earliest=-4h
| where match(response_flags, "UO")
| bin _time span=5m
| stats count as overflows dc(upstream_cluster) as affected_clusters values(upstream_cluster) as clusters by _time
| eval severity=case(overflows > 200, "CRITICAL -- heavy pool overflow", overflows > 50, "HIGH -- connection pools saturated", 1==1, "WARNING")
| table _time, overflows, affected_clusters, clusters, severity
```

**Connection pool utilization from metrics:**
```spl
index=proxy sourcetype="envoy:metrics" earliest=-4h
| where match(metric_name, "upstream_cx_active|upstream_cx_max")
| stats latest(metric_value) as value by upstream_cluster, metric_name
| xyseries upstream_cluster metric_name value
| rename upstream_cx_active as active, upstream_cx_max as max_ever
| eval utilization=round(100*active/max_ever, 1)
| where utilization > 70
| sort -utilization
```

### Step 3 — - Validate
(a) `curl http://localhost:15000/clusters | grep cx_active` -- shows active connections per cluster.
(b) Reduce `max_connections` to a very low value and send traffic -- verify UO events.
(c) Check for connection reuse: `curl http://localhost:15000/stats | grep upstream_cx_reuse`.

### Step 4 — - Operationalize
Dashboard ("Envoy -- Connection Pool"):
* Row 1 -- Single-value: "Pool overflows (4h)", "Affected clusters", "Max active connections".
* Row 2 -- Overflow events timechart.
* Row 3 -- Per-cluster connection utilization.

Alerting:
* Critical (overflows > 200/5m): upstream connections exhausted.
* High (overflows > 50/5m): approaching capacity.

### Step 5 — - Troubleshooting

* **Overflow on specific cluster** -- Check: (1) `max_connections` may be too low for traffic, (2) upstream hosts may be slow (holding connections longer), (3) number of upstream hosts in the cluster.

* **Connection pool not reusing connections** -- Check: (1) HTTP keepalive is enabled, (2) upstream `Connection: close` header, (3) `max_requests_per_connection` setting (0 = unlimited reuse).

* **Overflow across all clusters** -- Envoy may be hitting system-level file descriptor limits. Check: `ulimit -n` for the Envoy process.

## SPL

```spl
index=proxy sourcetype="envoy:stats"
| search metric_name="*overflow*" OR metric_name="*pending_requests*"
| eval v=tonumber(metric_value)
| where v > 0
| timechart span=1m sum(v) by cluster_name
```

## Visualization

Time series for rates and latency, top/dedup for hotspots, single-value alerts on health thresholds.

## Known False Positives

Edge cases: multi-vendor mixes and ad hoc feeds can include lab traffic and partial visibility that mimics issues until scopes are defined. Tuning tip: match this to «Envoy Upstream Connection Pool Overflow» and exclude change windows, scans, and lab VLANs you already expect.

## References

- [Vendor documentation](https://www.envoyproxy.io/docs/envoy/latest/intro/arch_overview/upstream/connection_pooling)
