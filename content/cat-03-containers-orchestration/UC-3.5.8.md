<!-- AUTO-GENERATED from UC-3.5.8.json — DO NOT EDIT -->

---
id: "3.5.8"
title: "Circuit Breaker Trips"
status: "verified"
criticality: "high"
splunkPillar: "Observability"
---

# UC-3.5.8 · Circuit Breaker Trips

## Description

Monitors **Envoy** circuit breaker and **outlier detection** activity across the **Istio** mesh by tracking `envoy_cluster_outlier_detection_ejections_active`, pending request overflows, and connection overflows per upstream cluster — then correlates with `UO` (upstream overflow) response flags in access logs to quantify how many requests are being rejected by tripped circuit breakers and which calling services are impacted.

## Value

Circuit breakers protect the mesh from cascading failures by shedding load to unhealthy upstreams, but every tripped breaker is also a rejected request that a real user experienced. Monitoring circuit breaker trips reveals the tension between protection and availability: frequent trips signal that the upstream needs more capacity, better health checks, or code fixes, while no trips during a known degradation may indicate misconfigured thresholds that let failures cascade.

## Implementation

Deploy the Splunk OTel Collector with Prometheus receiver scraping Envoy sidecar stats to collect outlier detection ejection and circuit breaker overflow counters. Build two search variants: circuit breaker status by upstream cluster with severity classification, and UO response flag analysis from access logs quantifying rejected requests per destination. Alert on any cluster with active ejections plus pending overflow >100 or when rejected requests exceed 1000 in a 15-minute window.

## Detailed Implementation

Prerequisites
• **Istio** 1.18+ with **DestinationRule** resources configured for upstream clusters that include **circuit breaking** settings (`connectionPool.tcp.maxConnections`, `connectionPool.http.h2UpgradePolicy`, `connectionPool.http.maxRequestsPerConnection`) and **outlier detection** settings (`outlierDetection.consecutiveErrors`, `outlierDetection.interval`, `outlierDetection.baseEjectionTime`, `outlierDetection.maxEjectionPercent`).
• **Envoy** **sidecar**s expose circuit breaker and **outlier detection** metrics on port **15090** (`/stats/prometheus`). Verify: `kubectl exec <pod> -c istio-proxy -- curl -s localhost:15000/stats | grep outlier`.
• **Splunk OpenTelemetry Collector** deployed as a **DaemonSet** with the **Prometheus receiver** scraping sidecar stats. Key metrics:
— **`envoy_cluster_outlier_detection_ejections_active`** (gauge: currently ejected **endpoint**s)
— **`envoy_cluster_outlier_detection_ejections_total`** (counter: cumulative ejection events)
— **`envoy_cluster_upstream_rq_pending_overflow`** (counter: requests rejected because pending request queue was full)
— **`envoy_cluster_upstream_cx_overflow`** (counter: connections rejected because **connection pool** was full)
— **`envoy_cluster_circuit_breakers_default_remaining_pending`** (gauge: remaining pending request **capacity** before overflow)
• **Splunk HEC** token for **`index=containers`** with **`sourcetype=otel:metrics`**; secondary stream for **`sourcetype=istio:accesslog`** (Envoy **access log**s where `response_flags=UO` marks **circuit-breaker rejections**).
• Splunk RBAC: users need **`srchIndexesAllowed`** including `containers` via role **`mesh_observer`**.
• **License estimate**: outlier detection metrics add ~200 bytes per upstream cluster per scrape; a 50-service mesh generates ~1–2 MB/day of circuit breaker metrics.

Step 1 — Configure data collection
(1) **Outlier detection metrics**: Envoy's **outlier detection** tracks per-endpoint health within each upstream cluster. When an endpoint exceeds the configured error threshold (`consecutiveErrors`), Envoy ejects it for a configurable **base ejection time**. The `ejections_active` gauge shows how many endpoints are currently ejected — a non-zero value means the circuit breaker has identified **unhealthy backends**.

(2) **Connection pool overflow metrics**: Envoy's **circuit breaker** limits the number of concurrent connections, pending requests, and active retries to each upstream cluster. When these limits are exceeded, Envoy rejects the request immediately with a **503 status** and sets the `response_flags=UO` (upstream overflow) in the access log. The `pending_overflow` and `cx_overflow` counters track how many requests hit these limits.

(3) **Access log correlation**: the **`response_flags=UO`** field in Envoy **access logs** is the definitive signal that a request was rejected by a circuit breaker. Unlike the metric counters which report **aggregate** totals, the access log provides per-request context: which **calling service** was affected, what **path** was requested, and the request **duration** (which will be near-zero for circuit-breaker rejections since no upstream processing occurred).

(4) **DestinationRule inventory**: create a lookup **`destination_rules.csv`** with columns `cluster_name`, `max_connections`, `max_pending`, `max_retries`, `outlier_consecutive_errors`, `outlier_base_ejection_time` extracted from `kubectl get destinationrule -o yaml --all-namespaces`. This provides context for whether circuit breaker thresholds are appropriate.

(5) **Event correlation**: collect **`sourcetype=kube:events`** to correlate circuit breaker trips with **deployment rollout**s and pod restarts — a newly deployed unhealthy version will trigger **outlier ejections** across the mesh as Envoy detects errors on the new pods.

Step 2 — Create the search and alert
The primary SPL aggregates circuit breaker metrics per upstream cluster across all sidecars. The **`severity`** classification uses a combination of active ejections and pending overflow:
— **CRITICAL**: endpoints are ejected AND pending overflow > 100 (circuit breaker is tripping AND requests are being rejected — the upstream is both unhealthy and overloaded)
— **WARNING**: endpoints are ejected but pending overflow is low (outlier detection working, but capacity may be shrinking)
— **ELEVATED**: no ejections but pending overflow > 50 (connection pool limits may be too low for current traffic)

The access log variant quantifies the **user-visible impact** by counting requests with `response_flags=UO`. The **`impact`** classification (HIGH/MEDIUM/LOW) helps prioritize which clusters need immediate attention.

Schedule the circuit breaker status search every **5 minutes** over **`-5m@m`** and alert on **CRITICAL severity**. Schedule the UO rejection search every **15 minutes** and alert when rejected_requests > 1000 for any destination.

Step 3 — Validate
(a) Check **outlier detection configuration**: `kubectl get destinationrule -A -o yaml | grep -A10 outlierDetection` — verify at least one DestinationRule has outlier detection configured.
(b) Verify **metric presence**: `index=containers sourcetype=otel:metrics metric_name=envoy_cluster_outlier_detection_ejections_active earliest=-5m | stats dc(envoy_cluster_name) as clusters`. Should be non-zero.
(c) Simulate a circuit breaker trip: deploy a service returning 500 errors behind a DestinationRule with `consecutiveErrors: 3` and `interval: 10s`. After 3 **consecutive error**s, verify `ejections_active > 0` in the search output.
(d) Verify **UO flag correlation**: during the simulation, send additional requests and confirm they appear in the access log search with `response_flags=UO`.
(e) Cross-check with **Envoy admin**: `kubectl exec <pod> -c istio-proxy -- curl -s localhost:15000/clusters | grep outlier` shows per-endpoint **ejection state**.

Step 4 — Operationalize dashboards and runbooks
• Row A: **single-value tiles** — clusters with active ejections, total rejected requests (UO), worst cluster rejection count, percentage of mesh clusters in HEALTHY state.
• Row B: **circuit breaker table** — cluster_name, ns, active_ejections, total_ejections, **pending_overflow**, **connection_overflow**, severity. Red rows for CRITICAL. Drilldown opens **cluster endpoint** detail.
• Row C: **timechart** of UO rejection count by destination over 4 hours — spikes correlate with upstream degradation events.
• Row D: **caller impact matrix** — source_svc × dest_svc showing rejected_requests count as a **heatmap**.
• **Alerting**: CRITICAL (active ejections + overflow > 100) → **PagerDuty** P2 with cluster name and ejection count; UO rejections > 1000/15m → P2 with affected callers; sustained ejections > 30m → P1 escalation.
• **Runbook** (owner: SRE mesh on-call): (1) identify the cluster from the alert, (2) check endpoint health: `istioctl **proxy-config** endpoint <pod> --cluster <cluster>`, (3) check if a deployment is in progress, (4) for capacity issues: increase `connectionPool` limits in the DestinationRule, (5) for application errors: check application logs of ejected endpoints.

Step 5 — Visualization, alert design, and troubleshooting
• **Visualization**: use a **circuit breaker state diagram** (custom HTML panel) showing each upstream cluster as a box with green/yellow/red state based on `active_ejections` and `pending_overflow`; pair with a **rejection flow diagram** showing source → breaker → destination with rejection counts; add a **threshold comparison table** showing current traffic vs. configured circuit breaker limits from the `destination_rules.csv` lookup.
• **Alert design**: include `cluster_name`, `ns`, `active_ejections`, `pending_overflow`, `connection_overflow`, `severity` in breaker alerts; for UO alerts include `dest_svc`, `rejected_requests`, `affected_callers`, `impact`; add a **deep-link** to the DestinationRule configuration.
• **No outlier detection metrics** — the cluster may not have a DestinationRule with outlier detection configured; Envoy defaults do not include outlier detection. Check: `istioctl proxy-config cluster <pod> --fqdn <service> -o json | grep outlierDetection`.
• **Active ejections but no UO rejections** — outlier detection ejected some endpoints but enough healthy endpoints remain to serve traffic. This is the intended behavior — the circuit breaker is protecting the service.
• **UO rejections without ejections** — the connection pool circuit breaker (max connections/pending) is tripping, not the **outlier detector**. Increase `connectionPool.tcp.maxConnections` or `connectionPool.http.maxPendingRequests` in the DestinationRule.
• **Passive vs active health checking** — Envoy's outlier detection uses **passive health checking** (observing real traffic errors) by default. For proactive detection, configure **active health checking** in the DestinationRule's `connectionPool` section so Envoy probes endpoints independently of user traffic — active checks catch failures before user requests are affected.
• **Ejections resolve and recur rapidly** — the `baseEjectionTime` is too short, causing endpoints to be re-admitted before they recover. Increase the ejection time or add exponential backoff via `consecutiveErrors` tuning.

## SPL

```spl
`comment("--- Circuit Breaker Trips — Outlier Detection Ejections and Overflow ---")`
index=containers (sourcetype="otel:metrics" OR sourcetype="prometheus:istio")
| where match(metric_name, "envoy_cluster_outlier_detection_ejections|envoy_cluster_upstream_rq_pending_overflow|envoy_cluster_upstream_cx_overflow")
| eval cluster_name=coalesce(envoy_cluster_name, cluster_name, label_envoy_cluster_name, "unknown")
| eval pod_name=coalesce(pod, exported_pod, label_pod, "unknown")
| eval ns=coalesce(namespace, exported_namespace, label_namespace, "unknown")
| eval metric=coalesce(metric_name, name)
| eval metric_class=case(
    match(metric, "ejections_active"), "active_ejections",
    match(metric, "ejections_total"), "total_ejections",
    match(metric, "ejections_enforced_total"), "enforced_ejections",
    match(metric, "rq_pending_overflow"), "pending_overflow",
    match(metric, "cx_overflow"), "connection_overflow",
    1=1, metric)
| eval val=tonumber(value)
| stats latest(eval(if(metric_class="active_ejections", val, null()))) as active_ejections,
    max(eval(if(metric_class="total_ejections", val, null()))) as total_ejections,
    sum(eval(if(metric_class="pending_overflow", val, null()))) as pending_overflow,
    sum(eval(if(metric_class="connection_overflow", val, null()))) as connection_overflow,
    latest(_time) as last_seen
    by cluster_name, ns
| eval cb_activity=active_ejections + pending_overflow + connection_overflow
| eval severity=case(
    active_ejections > 0 AND pending_overflow > 100, "CRITICAL",
    active_ejections > 0, "WARNING",
    pending_overflow > 50, "ELEVATED",
    1=1, "HEALTHY")
| where severity != "HEALTHY"
| sort -cb_activity
| table cluster_name ns active_ejections total_ejections pending_overflow connection_overflow cb_activity severity last_seen

`comment("--- Circuit Breaker Impact — Requests Rejected by UO Response Flag ---")`
index=containers sourcetype="istio:accesslog" response_flags="UO"
| eval dest_svc=coalesce(upstream_cluster, authority, "unknown")
| eval source_svc=coalesce(downstream_remote_address, source_workload, "unknown")
| eval response_code=tonumber(coalesce(response_code, status_code, "503"))
| eval duration_ms=tonumber(coalesce(duration, request_duration, "0"))
| stats count as rejected_requests,
    dc(source_svc) as affected_callers,
    avg(duration_ms) as avg_duration_ms,
    latest(_time) as last_rejection
    by dest_svc
| eval impact=case(
    rejected_requests > 1000, "HIGH",
    rejected_requests > 100, "MEDIUM",
    1=1, "LOW")
| sort -rejected_requests
| table dest_svc rejected_requests affected_callers avg_duration_ms impact last_rejection
```

## Visualization

Circuit breaker activity table by cluster, UO rejection timechart, affected caller matrix, single-value tiles (clusters with active ejections, total rejected requests, worst cluster rejection count).

## Known False Positives

**canary_endpoint_ejection** — During canary deployments, the canary endpoint may exhibit elevated error rates that trigger outlier detection ejection. This is the expected behavior of outlier detection protecting the service during progressive rollout. Correlate ejection timestamps with deployment events and suppress ejection alerts for 15 minutes after a canary deployment starts.

**health_check_driven_ejection** — Outlier detection uses passive health checking (counting errors on actual requests). If the upstream has aggressive liveness probes that fail during brief GC pauses, those failures count toward the consecutive error threshold and trigger ejection even though application traffic is healthy. Adjust `consecutiveErrors` to be higher than the expected probe failure bursts.

**connection_pool_sizing** — Default Envoy circuit breaker limits (1024 max connections, 1024 max pending requests) may be insufficient for high-traffic services. Hitting these limits generates `pending_overflow` events that indicate undersized pool configuration rather than application failure. Compare current traffic with DestinationRule limits to determine if scaling is needed.

**panic_threshold_activation** — When Envoy ejects more than `maxEjectionPercent` of endpoints, it enters panic mode and routes to all endpoints (including ejected ones) to avoid complete service unavailability. The `ejections_active` counter stays high but traffic continues to flow — the circuit breaker metrics look alarming but the system is self-protecting.

**split_brain_ejection** — In multi-zone deployments, each zone's Envoy may independently eject the same endpoint based on its local view. Cross-zone traffic patterns can cause the same healthy endpoint to be ejected by sidecars in a different zone while remaining healthy from the local zone's perspective. Check ejection counts per zone.

**warm_up_connection_burst** — When a new pod starts, the first few requests may timeout while connection pools warm up, triggering the consecutive error threshold. Set `outlierDetection.interval` longer than the pod's startup time to avoid ejecting endpoints that are still initializing.

## References

- [Envoy — Circuit Breaker Configuration](https://www.envoyproxy.io/docs/envoy/latest/intro/arch_overview/upstream/circuit_breaking)
- [Envoy — Outlier Detection](https://www.envoyproxy.io/docs/envoy/latest/intro/arch_overview/upstream/outlier)
- [Istio — DestinationRule Circuit Breaking](https://istio.io/latest/docs/reference/config/networking/destination-rule/#ConnectionPoolSettings)
- [Envoy Cluster Statistics — Circuit Breaker Stats](https://www.envoyproxy.io/docs/envoy/latest/configuration/upstream/cluster_manager/cluster_stats)
- [Envoy Access Log Response Flags — UO](https://www.envoyproxy.io/docs/envoy/latest/configuration/observability/access_log/usage)
