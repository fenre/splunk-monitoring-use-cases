<!-- AUTO-GENERATED from UC-5.14.41.json — DO NOT EDIT -->

---
id: "5.14.41"
title: "Envoy Active Health Check Failure Spike"
status: "draft"
criticality: "high"
splunkPillar: "Observability"
---

# UC-5.14.41 · Envoy Active Health Check Failure Spike

> **Criticality:** High &middot; **Difficulty:** Advanced &middot; **Pillar:** Observability &middot; **Type:** Availability &middot; **Status:** Draft

*We watch envoy active health check failure spike and catch issues early, before they turn into outages for the people who rely on the network.*

---

## Description

Failing checks drain endpoints before user monitors react.

## Value

Operations teams monitor Envoy active health check failure spikes and healthy host percentages per cluster, detecting capacity degradation before it causes complete service failures.

## Implementation

Correlate with Kubernetes pod restart metrics and upstream deploys.

## Detailed Implementation

### Prerequisites
* Envoy access logs and metrics for health check events. Key response flags: `UH` (no healthy upstream). Key metrics: `envoy_cluster_health_check_failure`, `envoy_cluster_health_check_success`, `envoy_cluster_health_check_attempt`, `envoy_cluster_membership_healthy`, `envoy_cluster_membership_total`.
* Active health checks: Envoy periodically probes upstream hosts (HTTP, gRPC, TCP). When a host fails `unhealthy_threshold` consecutive checks, it's marked unhealthy and removed from load balancing. After `healthy_threshold` successes, it's readmitted.

### Step 1 — - Configure data collection
```yaml
clusters:
- name: my_service
  health_checks:
  - timeout: 5s
    interval: 10s
    unhealthy_threshold: 3
    healthy_threshold: 2
    http_health_check:
      path: /health
      expected_statuses:
      - start: 200
        end: 299
```
Verify:
```spl
index=proxy sourcetype="envoy:metrics" earliest=-4h
| where match(metric_name, "health_check_failure|membership_healthy")
| stats latest(metric_value) as value by upstream_cluster, metric_name
```

### Step 2 — - Create the search and alert

**Primary search -- Health check failure spike detection:**
```spl
index=proxy sourcetype="envoy:metrics" earliest=-4h
| where match(metric_name, "health_check_(failure|success|attempt)|membership_(healthy|total)")
| stats latest(metric_value) as value by upstream_cluster, metric_name
| xyseries upstream_cluster metric_name value
| eval healthy_pct=if(isnotnull(membership_total) AND membership_total > 0, round(100*membership_healthy/membership_total, 1), 100)
| eval failure_rate=if(isnotnull(health_check_attempt) AND health_check_attempt > 0, round(100*health_check_failure/health_check_attempt, 1), 0)
| eval severity=case(healthy_pct < 50, "CRITICAL -- <50% healthy hosts", healthy_pct < 80, "HIGH -- reduced healthy hosts", failure_rate > 20, "WARNING -- >20% health check failure rate", 1==1, "OK")
| where severity != "OK"
| table upstream_cluster, membership_healthy, membership_total, healthy_pct, failure_rate, severity
```

**From access logs (UH = no healthy upstream):**
```spl
index=proxy sourcetype="envoy:access" response_flags="UH" earliest=-4h
| bin _time span=5m
| stats count as no_healthy_events by _time, upstream_cluster
| where no_healthy_events > 0
```

### Step 3 — - Validate
(a) `curl http://localhost:15000/clusters` -- shows per-host health status.
(b) Stop a backend and verify health check failures appear and host is removed.
(c) Check health check config: `curl http://localhost:15000/config_dump | grep health_check`.

### Step 4 — - Operationalize
Dashboard ("Envoy -- Health Checks"):
* Row 1 -- Single-value: "Healthy hosts", "Unhealthy hosts", "Health check failures", "No-healthy events".
* Row 2 -- Healthy host percentage timechart per cluster.

Alerting:
* Critical (healthy_pct < 50%): severe capacity loss.
* Critical (UH events > 0): complete cluster failure.
* Warning (failure_rate > 20%): investigate failing hosts.

### Step 5 — - Troubleshooting

* **All hosts failing health checks** -- Common cause: health check endpoint changed after deploy. Verify: (1) `path: /health` exists on backend, (2) returns 2xx status, (3) responds within `timeout`.

* **Host flapping healthy/unhealthy** -- `unhealthy_threshold` too low (default 3). Increase to tolerate transient failures. Also check if health check `interval` is shorter than the backend's response time.

* **Health check succeeds but traffic fails** -- Health check endpoint may not test the full application stack. Use a health check that verifies database connectivity, dependency health, etc.

## SPL

```spl
index=proxy sourcetype="envoy:stats"
| search metric_name="*health_check*failure*" OR metric_name="*health_check*network_failure*"
| eval v=tonumber(metric_value)
| where v > 0
| timechart span=1m sum(v) by cluster_name
```

## Visualization

Time series for rates and latency, top/dedup for hotspots, single-value alerts on health thresholds.

## Known False Positives

Edge cases: multi-vendor mixes and ad hoc feeds can include lab traffic and partial visibility that mimics issues until scopes are defined. Tuning tip: match this to «Envoy Active Health Check Failure Spike» and exclude change windows, scans, and lab VLANs you already expect.

## References

- [Vendor documentation](https://www.envoyproxy.io/docs/envoy/latest/intro/arch_overview/upstream/health_checking)
