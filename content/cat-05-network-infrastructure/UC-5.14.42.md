<!-- AUTO-GENERATED from UC-5.14.42.json — DO NOT EDIT -->

---
id: "5.14.42"
title: "Envoy ext_authz Latency and Denials"
status: "draft"
criticality: "high"
splunkPillar: "Observability"
---

# UC-5.14.42 · Envoy ext_authz Latency and Denials

> **Criticality:** High &middot; **Difficulty:** Intermediate &middot; **Pillar:** Observability &middot; **Type:** Security, Performance &middot; **Status:** Draft

*We watch envoy ext_authz latency and denials and catch issues early, before they turn into outages for the people who rely on the network.*

---

## Description

Authz latency becomes user latency on every request.

## Value

Operations teams monitor Envoy external authorization (ext_authz) denial rates and latency, detecting misconfigured policies blocking legitimate traffic and slow authz services degrading request performance.

## Implementation

Avoid logging tokens; use separate debug index for authz bodies.

## Detailed Implementation

### Prerequisites
* Envoy access logs with ext_authz filter results. Key response flags: `UAEX` (unauthorized external authorization), duration fields. Key metrics: `envoy_ext_authz_ok`, `envoy_ext_authz_denied`, `envoy_ext_authz_error`, `envoy_ext_authz_failure_mode_allowed`.
* ext_authz: Envoy delegates authorization decisions to an external gRPC or HTTP service. Every request is checked before forwarding to upstream. Latency in the authz service adds to total request latency. Denials should be monitored for legitimate traffic being blocked. `failure_mode_allow` controls behavior when the authz service is unreachable.

### Step 1 — - Configure data collection
```yaml
http_filters:
- name: envoy.filters.http.ext_authz
  typed_config:
    "@type": type.googleapis.com/envoy.extensions.filters.http.ext_authz.v3.ExtAuthz
    grpc_service:
      envoy_grpc:
        cluster_name: ext_authz_cluster
      timeout: 0.5s
    failure_mode_allow: false
    stat_prefix: ext_authz
```
Verify:
```spl
index=proxy (sourcetype="envoy:access" OR sourcetype="envoy:metrics") earliest=-4h
| where match(response_flags, "UAEX") OR match(metric_name, "ext_authz")
| stats count
```

### Step 2 — - Create the search and alert

**Primary search -- ext_authz latency and denial analysis:**
```spl
index=proxy sourcetype="envoy:access" earliest=-4h
| where match(response_flags, "UAEX") OR response_code=401 OR response_code=403
| eval authz_denied=if(match(response_flags, "UAEX") OR response_code=403, 1, 0)
| eval total_duration_ms=tonumber(duration)
| rex field=downstream_remote_address "(?<client_ip>[0-9.]+)"
| bin _time span=5m
| stats sum(authz_denied) as denials count as total avg(total_duration_ms) as avg_latency_ms p99(total_duration_ms) as p99_latency_ms by _time, upstream_cluster
| eval denial_rate=round(100*denials/total, 2)
| eval severity=case(denial_rate > 20, "HIGH -- >20% auth denials", avg_latency_ms > 500, "WARNING -- authz adding >500ms latency", p99_latency_ms > 2000, "WARNING -- P99 authz latency >2s", 1==1, "OK")
| where severity != "OK"
| table _time, upstream_cluster, total, denials, denial_rate, avg_latency_ms, p99_latency_ms, severity
```

**From metrics:**
```spl
index=proxy sourcetype="envoy:metrics" earliest=-4h
| where match(metric_name, "ext_authz_(ok|denied|error|failure_mode)")
| stats latest(metric_value) as value by metric_name
```

### Step 3 — - Validate
(a) `curl http://localhost:15000/stats | grep ext_authz` -- shows authz counters.
(b) Send a request without credentials and verify denial/403.
(c) Introduce latency on the authz service and verify `avg_latency_ms` increases.

### Step 4 — - Operationalize
Dashboard ("Envoy -- External Authorization"):
* Row 1 -- Single-value: "Auth denials (4h)", "Denial rate (%)", "Avg authz latency (ms)", "P99 latency".
* Row 2 -- Denial rate and latency timechart.
* Row 3 -- Top denied clients.

Alerting:
* High (denial rate > 20%): legitimate traffic may be blocked.
* Warning (authz latency P99 > 2s): authz service degradation.
* Critical (ext_authz_error or failure_mode_allowed > 0): authz service down, traffic bypassing auth.

### Step 5 — - Troubleshooting

* **High denial rate after deploy** -- New authorization policy may be too restrictive. Check: (1) authz service logs, (2) policy changes, (3) compare denied requests with expected access patterns.

* **High authz latency** -- Authz service is slow. Check: (1) authz service resource usage, (2) external dependencies (database, LDAP), (3) consider caching authz decisions if policy allows.

* **failure_mode_allowed events** -- Authz service is unreachable and `failure_mode_allow: true` is letting traffic through without authorization. This is a security gap. Fix the authz service immediately or switch to `failure_mode_allow: false` (denies all traffic when authz is down).

## SPL

```spl
index=proxy sourcetype="envoy:access"
| eval dur=tonumber(duration_ms)
| where response_code IN (401,403) OR match(response_flags, "UAEX")
| timechart span=5m perc95(dur) as p95_ms count by cluster_name
```

## Visualization

Time series for rates and latency, top/dedup for hotspots, single-value alerts on health thresholds.

## Known False Positives

Edge cases: multi-vendor mixes and ad hoc feeds can include lab traffic and partial visibility that mimics issues until scopes are defined. Tuning tip: match this to «Envoy ext_authz Latency and Denials» and exclude change windows, scans, and lab VLANs you already expect.

## References

- [Vendor documentation](https://www.envoyproxy.io/docs/envoy/latest/configuration/http/http_filters/ext_authz_filter)
