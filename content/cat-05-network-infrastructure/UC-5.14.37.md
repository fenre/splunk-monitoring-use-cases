<!-- AUTO-GENERATED from UC-5.14.37.json — DO NOT EDIT -->

---
id: "5.14.37"
title: "Envoy Outlier Detection Ejection Events"
status: "draft"
criticality: "high"
splunkPillar: "Observability"
---

# UC-5.14.37 · Envoy Outlier Detection Ejection Events

> **Criticality:** High &middot; **Difficulty:** Intermediate &middot; **Pillar:** Observability &middot; **Type:** Resilience, Performance &middot; **Status:** Draft

*We watch envoy outlier detection ejection events and catch issues early, before they turn into outages for the people who rely on the network.*

---

## Description

Ejections explain uneven load and surprise latency.

## Value

Operations teams monitor Envoy outlier detection ejections, tracking which upstream hosts are being removed from load balancing due to consecutive errors and identifying clusters with no healthy hosts.

## Implementation

Tune outlier `consecutive_5xx`; confirm with periodic `/clusters` admin dumps (low volume).

## Detailed Implementation

### Prerequisites
* Envoy access logs and/or metrics. Key access log response flags: `UH` (no healthy upstream), `UF` (upstream connection failure), `UR` (upstream connection reset). Key metrics: `envoy_cluster_outlier_detection_ejections_active`, `envoy_cluster_outlier_detection_ejections_total`, `envoy_cluster_outlier_detection_ejections_enforced_total`.
* Outlier detection: Envoy monitors upstream host error rates. When a host exceeds the threshold (e.g., > 5% 5xx rate), it's ejected from the load balancing pool for a duration. This prevents sending traffic to unhealthy hosts. Parameters: `consecutive_5xx`, `interval`, `base_ejection_time`, `max_ejection_percent`.

### Step 1 — - Configure data collection
Envoy outlier detection config:
```yaml
clusters:
- name: my_service
  outlier_detection:
    consecutive_5xx: 5
    interval: 10s
    base_ejection_time: 30s
    max_ejection_percent: 50
    enforcing_consecutive_5xx: 100
```
Verify:
```spl
index=proxy (sourcetype="envoy:access" OR sourcetype="envoy:metrics") earliest=-4h
| where match(_raw, "(?i)outlier|eject|UH|no healthy")
| stats count
```

### Step 2 — - Create the search and alert

**Primary search -- Outlier ejection events:**
```spl
index=proxy sourcetype="envoy:access" earliest=-4h
| where match(response_flags, "UH|UF|UR")
| eval ejection_type=case(match(response_flags, "UH"), "NO_HEALTHY_UPSTREAM", match(response_flags, "UF"), "UPSTREAM_CONNECT_FAIL", match(response_flags, "UR"), "UPSTREAM_RESET", 1==1, "OTHER")
| bin _time span=5m
| stats count as events dc(upstream_cluster) as affected_clusters values(upstream_cluster) as clusters by _time, ejection_type
| eval severity=case(ejection_type="NO_HEALTHY_UPSTREAM", "CRITICAL -- no healthy hosts", events > 50, "HIGH -- frequent upstream failures", 1==1, "WARNING")
| sort severity, -events
```

**From metrics:**
```spl
index=proxy sourcetype="envoy:metrics" earliest=-4h
| where match(metric_name, "outlier_detection_ejections_active")
| where metric_value > 0
| stats latest(metric_value) as ejected_hosts by upstream_cluster
| eval severity=if(ejected_hosts > 0, "WARNING -- ".ejected_hosts." hosts ejected", "OK")
| where severity != "OK"
```

### Step 3 — - Validate
(a) `curl http://localhost:15000/clusters` -- shows outlier detection status and ejected hosts.
(b) Make a backend return 5xx errors consecutively and verify ejection.
(c) Wait for `base_ejection_time` and verify host is re-admitted.

### Step 4 — - Operationalize
Dashboard ("Envoy -- Outlier Detection"):
* Row 1 -- Single-value: "Ejected hosts", "No-healthy-upstream events", "Upstream failures".
* Row 2 -- Ejection events timechart by cluster.

Alerting:
* Critical (UH -- no healthy upstream): complete service failure.
* High (> 50% hosts ejected in a cluster): severe capacity reduction.

### Step 5 — - Troubleshooting

* **All hosts ejected** -- `max_ejection_percent` prevents ejecting all hosts (default 10%). If all hosts are unhealthy, Envoy keeps some in pool. Check: backend health across all hosts.

* **Host keeps getting ejected and re-admitted** -- Host is intermittently unhealthy. Check: (1) backend logs for errors, (2) resource exhaustion (CPU, memory, connections), (3) consider increasing `base_ejection_time` to give more recovery time.

* **Outlier detection too aggressive** -- Increase `consecutive_5xx` threshold or `interval`. Consider `success_rate_stdev_factor` for statistical outlier detection instead of consecutive errors.

## SPL

```spl
index=proxy sourcetype="envoy:access"
| where match(response_flags, "UH") OR match(response_flags, "UF") OR match(_raw, "(?i)eject")
| stats count by upstream_host, cluster_name
| where count > 5
```

## Visualization

Time series for rates and latency, top/dedup for hotspots, single-value alerts on health thresholds.

## Known False Positives

Edge cases: multi-vendor mixes and ad hoc feeds can include lab traffic and partial visibility that mimics issues until scopes are defined. Tuning tip: match this to «Envoy Outlier Detection Ejection Events» and exclude change windows, scans, and lab VLANs you already expect.

## References

- [Vendor documentation](https://www.envoyproxy.io/docs/envoy/latest/intro/arch_overview/upstream/outlier)
