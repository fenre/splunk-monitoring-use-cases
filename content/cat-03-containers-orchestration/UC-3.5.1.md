<!-- AUTO-GENERATED from UC-3.5.1.json — DO NOT EDIT -->

---
id: "3.5.1"
title: "Istio Mesh Traffic Monitoring"
status: "verified"
criticality: "high"
splunkPillar: "Observability"
---

# UC-3.5.1 · Istio Mesh Traffic Monitoring

## Description

Correlates **Istio** sidecar-reported **`istio_requests_total`** and **`istio_request_duration_milliseconds_bucket`** metrics across all service-to-service pairs to compute per-destination error rates, P95/P99 latency, and east-west traffic matrices — surfacing degrading microservices before a single endpoint failure cascades into a customer-visible outage.

## Value

Silent service-mesh degradation compounds: a 2% error rate on one backend amplifies through retry storms, timeouts, and circuit-breaker trips until the entire request path collapses. Catching error-rate drift and latency creep at the Envoy sidecar level gives SRE teams minutes of lead time to isolate a failing deployment, roll back a bad canary, or shed load — time that disappears once users start seeing 503s.

## Implementation

Deploy the Splunk OpenTelemetry Collector with a Prometheus receiver scraping Istio sidecar port 15090 and control plane port 15014. Forward metrics to Splunk via OTLP or HEC into index=containers. Build three search variants: per-destination error rate (istio_requests_total), latency anomaly (istio_request_duration_milliseconds_bucket), and source-to-destination traffic matrix. Schedule alerts for sustained >1% error rate on medium/high-volume services and P99 latency exceeding 500ms.

## Detailed Implementation

Prerequisites
• **Istio** 1.18+ installed in the target Kubernetes cluster with **Envoy** **sidecar injection** enabled (verify with `istioctl version` and `kubectl get namespace -L istio-injection`); earlier **Istio** versions use different metric label names that require field-alias adjustments.
• **Splunk OpenTelemetry Collector** deployed as a **DaemonSet** via the `splunk-otel-collector-chart` **Helm chart** with the **Prometheus receiver** enabled; confirm the receiver is configured to scrape Istio sidecar metrics on port **15090** (`/stats/prometheus`) and **control plane** components on port **15014**.
• **Splunk HEC** token provisioned for **`index=containers`** with default **`sourcetype=otel:metrics`**; secondary token or source override for **access logs** landing as **`sourcetype=istio:accesslog`**; third stream for **`sourcetype=kube:events`** via **Splunk Connect for Kubernetes**.
• **Kubernetes RBAC**: the OTel Collector **ServiceAccount** needs `get`, `list`, `watch` on pods, services, endpoints, and nodes to discover **scrape targets** via **Kubernetes service discovery**; Istio sidecars expose metrics without additional auth.
• Splunk RBAC: users running mesh searches need **`srchIndexesAllowed`** including `containers`; assign via a custom role (**`mesh_observer`**) rather than granting admin.
• License estimate: Istio **metric volume** scales with **service count** × **scrape interval**; a 50-service mesh at 15s scrape intervals generates ~200–400 MB/day of metric events; access logs add ~2 KB per request, so a mesh handling 10k RPS generates ~1.5 GB/day of access logs.

Step 1 — Configure data collection
(1) **Prometheus receiver** in the OTel Collector: edit the Helm values to enable Istio-specific **scrape configs** targeting the `istio-proxy` container port 15090. The default `splunk-otel-collector-chart` includes **pod annotations**-based discovery — Istio sidecars carry `prometheus.io/port: "15090"` and `prometheus.io/path: "/stats/prometheus"` annotations by default. Verify by checking a sidecar-injected pod: `kubectl get pod <pod> -o jsonpath='{.metadata.annotations}'`.

(2) **Control plane scraping**: add scrape targets for **`istiod`** (port 15014) to collect **pilot metrics** (**`pilot_xds_pushes`**, **`pilot_proxy_convergence_time`**, `pilot_k8s_reg_events`) that contextualize data-plane anomalies. Add a Kubernetes service monitor or static scrape config targeting the `istiod` service in the **`istio-system`** namespace.

(3) **Metric label normalization**: Istio metrics arrive with labels **`destination_service_name`**, **`destination_canonical_service`**, `destination_workload`, **`source_workload`**, **`source_canonical_service`**, **`response_code`**, **`reporter`**, **`request_protocol`**, **`connection_security_policy`**, **`grpc_response_status`**. The SPL in Step 2 uses **`coalesce`** chains to handle label presence variations across Istio versions and OTel Collector configurations. Key metrics to validate: **`istio_requests_total`** (request counter), **`istio_request_duration_milliseconds_bucket`** (latency histogram), **`istio_tcp_connections_opened_total`** (TCP connection counter).

(4) **Access log collection** (optional, for per-request forensics): Istio defaults to **JSON access logs** on sidecar stdout. The OTel Collector `filelog` receiver or Splunk Connect for Kubernetes captures these as `sourcetype=istio:accesslog`. Key fields: **`upstream_cluster`**, `response_code`, `duration`, `bytes_sent`, `bytes_received`, `authority`, `path`, `method`, **`request_id`** (trace correlation).

(5) **Kubernetes events**: ensure `sourcetype=kube:events` collection is active via Splunk Connect for Kubernetes or the OTel Collector `k8s_events` receiver — these events correlate deployment rollouts, pod restarts, and HPA scaling with mesh traffic anomalies.

Step 2 — Create the search and alert
The primary SPL computes per-destination **error rate**s from `istio_requests_total` counters. The `coalesce` chains handle label variability: older Istio versions use `destination_service_name` while newer versions prefer `destination_canonical_service`; gRPC services populate `grpc_response_status` instead of `response_code`. The `reporter` label distinguishes source-side from destination-side reporting — prefer `reporter=destination` for accuracy since the destination sidecar sees the final response code after retries.

The **`traffic_class`** field filters out **low-volume services** (< 100 requests in the window) to avoid noisy alerts on internal health-check endpoints that naturally have spiky error rates. Adjust the volume threshold per your mesh size — a mesh with hundreds of services may need a higher floor.

The **latency variant** uses `istio_request_duration_milliseconds_bucket` **histogram buckets** to approximate P95 and P99 latencies per destination. The **`le`** (less-than-or-equal) label defines bucket boundaries; the search finds the smallest bucket where cumulative percentage exceeds the target percentile.

Schedule the error-rate search every **5 minutes** over `-5m@m to @m`; alert when any medium/high-volume service exceeds **1% server error rate** sustained across two consecutive runs. Schedule the latency search every **15 minutes** over `-15m` and alert when P99 exceeds **500ms** for any service that was below 200ms in the prior 24h rolling baseline.

Step 3 — Validate
(a) Verify metric ingestion: `index=containers sourcetype=otel:metrics metric_name=istio_requests_total earliest=-5m | stats dc(destination_service_name) as services, sum(value) as total_requests`. The `services` count should match your mesh service count visible in `istioctl proxy-status`.
(b) Cross-check with Istio's built-in monitoring: if Prometheus + Grafana is deployed alongside Istio, compare the Grafana "Istio Service Dashboard" error rates with the SPL output for the same time window. Values should agree within ±2% (minor differences from scrape timing and counter reset handling).
(c) Test a known-bad service: deploy a test pod that returns 500 errors (`kubectl run fault-test --image=nginx --port=80 -- /bin/sh -c 'echo HTTP/1.1 500 | nc -l -p 80'`), send traffic, and confirm the error-rate search surfaces it within one scrape cycle.
(d) Verify label presence: `index=containers sourcetype=otel:metrics metric_name=istio_requests_total earliest=-5m | head 1 | table destination_service_name source_workload response_code reporter request_protocol`. All five labels should be non-null. If `destination_service_name` is missing, check Istio's `meshConfig.defaultConfig.proxyStatsMatcher` for label filtering.
(e) Confirm latency buckets: `index=containers sourcetype=otel:metrics metric_name=istio_request_duration_milliseconds_bucket earliest=-5m | stats dc(le) as bucket_count`. Expect 15–25 distinct `le` values (Istio default histogram boundaries).

Step 4 — Operationalize dashboards and runbooks
• Row A: **timechart** of **`err_rate`** by `dest_svc` over 4 hours — line chart with automatic color by service; overlay a horizontal reference line at the 1% alert threshold.
• Row B: **single-value tiles** — mesh-wide error rate (red if > 0.5%), total RPS across mesh, P95 latency for the slowest service, count of services currently above error threshold.
• Row C: **heatmap** of the source-to-destination traffic matrix from the third SPL variant — color intensity by `total_requests`, cell annotation with `total_err_rate`; this reveals which service pairs carry the most traffic and where errors concentrate.
• Row D: **sortable table** of services exceeding thresholds — columns: dest_svc, source_svc, total, errors, err_rate, traffic_class, P95_ms, P99_ms. Drilldown opens per-service detail with access log correlation.
• Alerting: sustained error rate > 1% on medium/high-volume services → **PagerDuty** P2 with `dest_svc`, `err_rate`, `total`, and last-5m **timechart** sparkline; P99 latency spike → Slack `#sre-mesh` with service name and comparison to 24h baseline.
• Runbook (owner: SRE mesh on-call): (1) check if a deployment rollout is in progress via `index=containers sourcetype=kube:events reason=ScalingReplicaSet` for the destination namespace, (2) check circuit breaker status via `istioctl proxy-config cluster <pod> --fqdn <dest>`, (3) inspect **Envoy** access logs for upstream connection failures, (4) verify **mTLS certificate** validity between the service pair.

Step 5 — Visualization, alert design, and troubleshooting
• Visualization: use a **topology map** (custom viz or export to Splunk Observability Cloud) showing service nodes sized by RPS and colored by error rate; pair with a **latency distribution** bar chart of P50/P95/P99 per service; add a **timechart overlay** comparing current error rates against 7-day rolling averages to distinguish spikes from trends.
• Alert design: include `dest_svc`, `source_svc`, `err_rate`, `total` requests, `traffic_class`, and `reporter_side` in every alert payload; for latency alerts include **`p95_ms`**, **`p99_ms`**, and the prior-day baseline values; add a deep-link to the Splunk dashboard filtered to the alerting service.
• **No metrics arriving** — verify the OTel Collector DaemonSet is running: `kubectl get ds -n splunk-otel -o wide`; check collector logs for **Prometheus receiver** errors: `kubectl logs -n splunk-otel -l app=splunk-otel-collector -c otel-collector | grep -i istio`; confirm sidecar injection is active on the target namespace.
• **Metrics arrive but** `destination_service_name` is null — the service does not have a **Kubernetes Service** object fronting it, or Istio cannot resolve the service name from the cluster DNS; check `istioctl proxy-config endpoint <pod>` and verify a Service resource exists.
• **Error rate shows 100%** on a service — very low traffic volume (< 10 requests) where a single failed health check dominates the ratio; the `traffic_class` filter should exclude these, but verify the volume threshold matches your mesh scale.
• **Latency search returns no rows** — histogram buckets may not be present if `istio_request_duration_milliseconds_bucket` is disabled in the **mesh telemetry config**; verify with `istioctl dashboard envoy <pod>` and search for `duration` in the stats page.
• **Mismatched error rates** between source and destination reporters — expected when retries occur; the destination reporter sees fewer attempts than the source reporter because retries are handled at the source sidecar. Prefer destination-side metrics for accuracy of final response codes.
• **Stale metrics after pod restart** — OTel Collector may cache stale scrape targets; verify **`staleness_period`** in the **Prometheus receiver** config is set to 5m or less; restart the collector pod if target discovery is stuck.

## SPL

```spl
`comment("--- Istio Service Error Rate by Destination ---")`
index=containers (sourcetype="otel:metrics" OR sourcetype="prometheus:istio")
| where like(metric_name, "istio_requests_total%") OR like(name, "istio_requests_total%")
| eval response_code_num=tonumber(coalesce(response_code, grpc_response_status, "0"))
| eval source_svc=coalesce(source_workload, source_canonical_service, source_app, "unknown")
| eval dest_svc=coalesce(destination_service_name, destination_canonical_service, destination_workload, "unknown")
| eval reporter_side=lower(coalesce(reporter, "destination"))
| eval request_protocol=lower(coalesce(request_protocol, connection_security_policy, "http"))
| eval is_error=case(
    response_code_num >= 500, 1,
    response_code_num = 0 AND isnull(grpc_response_status), 1,
    response_code_num >= 400 AND response_code_num < 500, 0,
    1=1, 0)
| stats sum(value) as total_requests by dest_svc, source_svc, reporter_side, is_error
| stats sum(total_requests) as total,
    sum(eval(if(is_error=1, total_requests, 0))) as errors
    by dest_svc, source_svc, reporter_side
| eval err_rate=round(100 * errors / total, 2)
| eval traffic_class=case(
    total < 100, "low-volume",
    total < 10000, "medium-volume",
    1=1, "high-volume")
| where err_rate > 1 AND traffic_class != "low-volume"
| sort -err_rate
| head 50
| table dest_svc source_svc reporter_side total errors err_rate traffic_class

`comment("--- Istio Service Latency P95/P99 Anomaly Detection ---")`
index=containers (sourcetype="otel:metrics" OR sourcetype="prometheus:istio")
| where like(metric_name, "istio_request_duration_milliseconds_bucket%") OR like(name, "istio_request_duration_milliseconds_bucket%")
| eval dest_svc=coalesce(destination_service_name, destination_canonical_service, "unknown")
| eval le_val=tonumber(le)
| where isnotnull(le_val)
| stats sum(value) as bucket_count by dest_svc, le_val, _time
| eventstats sum(bucket_count) as total_count by dest_svc, _time
| eval bucket_pct=round(100 * bucket_count / total_count, 2)
| where le_val <= 1000
| stats max(eval(if(bucket_pct >= 95, le_val, null()))) as p95_ms,
    max(eval(if(bucket_pct >= 99, le_val, null()))) as p99_ms,
    max(total_count) as total_reqs
    by dest_svc
| where p99_ms > 500 OR p95_ms > 250
| sort -p99_ms
| table dest_svc p95_ms p99_ms total_reqs

`comment("--- Service-to-Service Traffic Matrix (East-West Volume) ---")`
index=containers (sourcetype="otel:metrics" OR sourcetype="prometheus:istio")
| where like(metric_name, "istio_requests_total%") OR like(name, "istio_requests_total%")
| eval source_svc=coalesce(source_workload, source_canonical_service, "unknown")
| eval dest_svc=coalesce(destination_service_name, destination_canonical_service, "unknown")
| eval response_code_num=tonumber(coalesce(response_code, "200"))
| stats sum(value) as total_requests,
    sum(eval(if(response_code_num >= 500, value, 0))) as server_errors,
    sum(eval(if(response_code_num >= 400 AND response_code_num < 500, value, 0))) as client_errors
    by source_svc, dest_svc
| eval total_err_rate=round(100 * (server_errors + client_errors) / total_requests, 2)
| where total_requests > 50
| sort -total_requests
| head 100
| table source_svc dest_svc total_requests server_errors client_errors total_err_rate
```

## Visualization

Timechart of error rate by destination service, heatmap of source-to-destination traffic volume, P95/P99 latency distribution bars, single-value tile for mesh-wide error percentage, sortable service table with drilldown.

## Known False Positives

**canary_release_noise** — During canary or blue-green deployments, the new version may exhibit elevated error rates for the first few minutes as the Envoy sidecar warms up connection pools and the service initializes caches; correlate with `sourcetype=kube:events reason=ScalingReplicaSet` timestamps and suppress alerts for 10 minutes after a deployment event in the same namespace.

**health_check_amplification** — Kubernetes liveness and readiness probes generate HTTP requests that flow through the Istio sidecar and contribute to `istio_requests_total` counters; if a probe endpoint returns intermittent failures, it inflates the error rate for the entire service despite having zero user impact. Exclude probe paths by filtering `path!="/healthz" AND path!="/ready"` in the access-log variant.

**retry_storm_double_count** — Istio automatic retries (configured via DestinationRule `retryPolicy`) cause the source reporter to record multiple attempts for a single logical request; when calculating error rates from `reporter=source` metrics, the denominator is inflated by retry attempts. Always prefer `reporter=destination` for accurate final-response-code percentages.

**circuit_breaker_trip** — When Envoy trips an outlier detection circuit breaker on a destination, subsequent requests to that destination return 503 from the source sidecar without reaching the destination at all; these synthetic 503s appear as destination errors but originate from the mesh, not the application. Check `envoy_cluster_outlier_detection_ejections_active` to distinguish mesh-generated errors from application errors.

**mtls_handshake_spike** — Periodic mTLS certificate rotation by Istio's citadel/istiod causes brief TLS handshake failures across the mesh, producing a coordinated burst of connection errors that resolves within 30–60 seconds. Correlate with `istiod` certificate-rotation logs and suppress alerts shorter than 90 seconds.

**low_volume_service_noise** — Internal services handling < 50 requests per scrape interval (batch jobs, admin endpoints, internal tooling) have inherently noisy error rates where a single failed request creates a 10–50% error rate. The `traffic_class` filter in the SPL excludes these, but adjust the threshold if your mesh has many legitimate low-volume services.

**grpc_status_mismatch** — gRPC services report errors via `grpc_response_status` rather than HTTP `response_code`; a gRPC `UNAVAILABLE` (status 14) maps to HTTP 503 but appears as `response_code=200` with a non-zero `grpc_response_status` in the Istio metrics. The SPL `coalesce` chain handles this, but verify gRPC-heavy services have correct error classification by checking `grpc_response_status` field presence.

## References

- [Istio Standard Metrics — istio_requests_total, istio_request_duration](https://istio.io/latest/docs/reference/config/metrics/)
- [Istio Observability — Metrics Architecture](https://istio.io/latest/docs/concepts/observability/)
- [Splunk OpenTelemetry Collector for Kubernetes — Helm Chart](https://github.com/signalfx/splunk-otel-collector-chart)
- [Envoy Proxy Statistics Reference](https://www.envoyproxy.io/docs/envoy/latest/configuration/upstream/cluster_manager/cluster_stats)
- [Splunk HTTP Event Collector (HEC) Reference](https://docs.splunk.com/Documentation/Splunk/latest/Data/UsetheHTTPEventCollector)
