<!-- AUTO-GENERATED from UC-5.14.36.json — DO NOT EDIT -->

---
id: "5.14.36"
title: "Envoy Circuit Breaker Open Events by Cluster"
status: "draft"
criticality: "critical"
splunkPillar: "Observability"
---

# UC-5.14.36 · Envoy Circuit Breaker Open Events by Cluster

> **Criticality:** Critical &middot; **Difficulty:** Intermediate &middot; **Pillar:** Observability &middot; **Type:** Resilience, Availability &middot; **Status:** Draft

*We watch envoy circuit breaker open events by cluster and catch issues early, before they turn into outages for the people who rely on the network.*

---

## Description

Open breakers shed load but indicate real upstream pain.

## Value

Operations teams detect Envoy circuit breaker activations per upstream cluster, identifying saturated backends where Envoy is short-circuiting requests to prevent cascade failures.

## Implementation

Scrape via OpenTelemetry Collector or Telegraf; normalize `cluster_name` label.

## Detailed Implementation

### Prerequisites
* Envoy Proxy access logs and/or Prometheus metrics forwarded to Splunk. Data in `index=proxy` with `sourcetype=envoy:access` (JSON access log) or `sourcetype=envoy:metrics` (Prometheus scrape). Key metrics: `envoy_cluster_circuit_breakers_default_cx_open`, `envoy_cluster_circuit_breakers_default_rq_pending_open`, `envoy_cluster_circuit_breakers_default_rq_open`. Key access log fields: `response_flags` containing `UO` (upstream overflow = circuit breaker triggered).
* Circuit breakers: Envoy limits outstanding requests/connections per upstream cluster. When thresholds are exceeded, Envoy short-circuits with 503 and response flag `UO`. Thresholds: `max_connections`, `max_pending_requests`, `max_requests`, `max_retries`. These prevent cascade failures but must be tuned -- too low causes false triggers.

### Step 1 — - Configure data collection
Envoy JSON access log:
```yaml
# envoy.yaml
static_resources:
  listeners:
  - address:
      socket_address: { address: 0.0.0.0, port_value: 8080 }
    filter_chains:
    - filters:
      - name: envoy.filters.network.http_connection_manager
        typed_config:
          "@type": type.googleapis.com/envoy.extensions.filters.network.http_connection_manager.v3.HttpConnectionManager
          access_log:
          - name: envoy.access_loggers.file
            typed_config:
              "@type": type.googleapis.com/envoy.extensions.access_loggers.file.v3.FileAccessLog
              path: /var/log/envoy/access.log
              log_format:
                json_format:
                  response_flags: "%RESPONSE_FLAGS%"
                  upstream_cluster: "%UPSTREAM_CLUSTER%"
                  response_code: "%RESPONSE_CODE%"
                  duration: "%DURATION%"
```
Verify:
```spl
index=proxy sourcetype="envoy:access" earliest=-4h
| where match(response_flags, "UO")
| stats count by upstream_cluster
```

### Step 2 — - Create the search and alert

**Primary search -- Circuit breaker open events per cluster:**
```spl
index=proxy sourcetype="envoy:access" earliest=-4h
| where match(response_flags, "UO")
| eval cb_reason=case(match(response_flags, "UO"), "UPSTREAM_OVERFLOW", 1==1, "UNKNOWN")
| bin _time span=5m
| stats count as cb_triggers dc(upstream_cluster) as affected_clusters values(upstream_cluster) as clusters by _time
| eval severity=case(cb_triggers > 100, "CRITICAL -- heavy circuit breaker activation", cb_triggers > 20, "HIGH -- frequent circuit breaking", 1==1, "WARNING")
| table _time, cb_triggers, affected_clusters, clusters, severity
```

**From metrics (if available):**
```spl
index=proxy sourcetype="envoy:metrics" earliest=-4h
| where match(metric_name, "circuit_breakers.*open")
| eval is_open=if(metric_value > 0, 1, 0)
| stats sum(is_open) as open_breakers values(metric_name) as breaker_types by upstream_cluster
| where open_breakers > 0
```

### Step 3 — - Validate
(a) Check Envoy admin: `curl http://localhost:15000/clusters | grep circuit_breakers`.
(b) Overload a test cluster and verify `UO` response flag appears.
(c) Review configured thresholds: `curl http://localhost:15000/config_dump | grep circuit_breakers`.

### Step 4 — - Operationalize
Dashboard ("Envoy -- Circuit Breakers"):
* Row 1 -- Single-value: "CB triggers (4h)", "Affected clusters", "Currently open".
* Row 2 -- Circuit breaker triggers timechart by cluster.

Alerting:
* Critical (> 100 UO events/5m): upstream cluster is saturated.
* High (> 20 UO events/5m): circuit breaker engaging frequently.

### Step 5 — - Troubleshooting

* **Frequent UO on healthy cluster** -- Circuit breaker thresholds too low for the traffic volume. Increase: `max_connections`, `max_pending_requests`, `max_requests` in cluster config. Calculate based on peak QPS.

* **UO across all clusters simultaneously** -- Envoy itself may be overloaded (CPU, memory, connection limit). Check Envoy process resources.

* **UO on specific cluster after deploy** -- New deployment may have reduced backend capacity. Check: (1) number of healthy upstream hosts, (2) per-host connection limit vs number of hosts.

## SPL

```spl
index=proxy sourcetype="envoy:stats"
| search metric_name="*circuit_breakers*open*" OR metric_name="*cx_open*"
| eval v=tonumber(metric_value)
| where v > 0
| timechart span=1m max(v) by cluster_name
```

## Visualization

Time series for rates and latency, top/dedup for hotspots, single-value alerts on health thresholds.

## Known False Positives

Edge cases: multi-vendor mixes and ad hoc feeds can include lab traffic and partial visibility that mimics issues until scopes are defined. Tuning tip: match this to «Envoy Circuit Breaker Open Events by Cluster» and exclude change windows, scans, and lab VLANs you already expect.

## References

- [Vendor documentation](https://www.envoyproxy.io/docs/envoy/latest/configuration/upstream/cluster_manager/cluster_circuit_breakers)
