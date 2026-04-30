<!-- AUTO-GENERATED from UC-3.5.15.json — DO NOT EDIT -->

---
id: "3.5.15"
title: "eBPF Auto-Instrumented Service Metrics (Beyla)"
status: "verified"
criticality: "high"
splunkPillar: "Observability"
---

# UC-3.5.15 · eBPF Auto-Instrumented Service Metrics (Beyla)

> **Criticality:** High &middot; **Difficulty:** Advanced &middot; **Pillar:** Observability &middot; **Type:** Performance, Availability &middot; **Wave:** Crawl &middot; **Status:** Verified

*We attach an invisible speed camera to every service in our software city that automatically measures how fast each one responds and how often it makes mistakes, without the service ever knowing the camera is there.*

---

## Description

Ingests **Grafana Beyla** eBPF auto-instrumented RED metrics (Request rate, Error rate, Duration) to monitor **HTTP service latency and error rates** without application code changes, detects **latency anomalies** via z-score deviation from rolling baselines, and identifies **uninstrumented services** missing eBPF metric coverage — enabling platform teams to achieve comprehensive service observability across polyglot microservice environments with zero-touch instrumentation.

## Value

Traditional application performance monitoring requires instrumenting each service with language-specific SDKs — a significant engineering investment that leaves gaps in polyglot environments where teams use different languages, frameworks, and versions. Beyla attaches eBPF programs to the Linux kernel's networking and system call interface to extract RED metrics and distributed traces from any HTTP/gRPC service without modifying a single line of application code. Ingesting these metrics into Splunk gives the platform team a universal observability baseline that covers every service from day one, including legacy applications, third-party components, and services whose teams have not yet adopted OpenTelemetry SDKs.

## Implementation

Deploy Beyla as a DaemonSet or sidecar with OTLP export to the Splunk OTel Collector. Build three search variants: RED metric dashboard with severity classification, endpoint-level latency anomaly detection using z-score, and instrumentation coverage gap analysis comparing running services to Beyla metric inventory. Alert on CRITICAL latency/error status and uninstrumented production services.

## Detailed Implementation

### Prerequisites
- **Grafana Beyla** 1.5+ — an open-source eBPF-based **auto-instrumentation agent** that extracts RED metrics (Request rate, Error rate, Duration) and distributed traces from HTTP and gRPC services by attaching eBPF programs to the Linux kernel's **socket operations** and **Go runtime** (for Go services). Unlike traditional APM agents, Beyla requires **no application code changes**, no SDK integration, and no language-specific instrumentation — it works with **any language** or **framework** that communicates over HTTP/gRPC.
- **Deployment model**: Beyla can run as:
  — **DaemonSet** (recommended): one Beyla pod per node, instrumenting all eligible services on that node. Configure via `BEYLA_OPEN_PORT` or `BEYLA_EXECUTABLE_NAME` to target specific processes.
  — **Sidecar**: one Beyla container per application pod, providing per-service isolation. Use when DaemonSet-level access is restricted or when different services need different Beyla configurations.
- **Splunk Distribution of OpenTelemetry Collector** deployed as a **DaemonSet** with the **OTLP receiver** enabled (gRPC port 4317, HTTP port 4318). Beyla exports metrics and traces via **OTLP** to the local node's OTel Collector, which processes, batches, and forwards to **Splunk HEC**.
- **Splunk HEC** token for **`index=containers`** configured to receive **metric events** (for Beyla RED metrics) and **event data** (for traces and logs). The OTel Collector's **Splunk HEC exporter** maps OTLP metrics to Splunk metric events with dimensions preserved as fields.
- **Kubernetes node requirements**: Beyla needs Linux kernel **5.8+** (for BPF ring buffers) and **BTF** (BPF Type Format) support enabled. Most modern Kubernetes distributions (EKS, GKE, AKS with Ubuntu/Debian nodes) include these by default. Verify: `ls /sys/kernel/btf/vmlinux` — if this file exists, BTF is available.
- **Service discovery**: Beyla automatically discovers services by scanning for processes listening on **network ports**. Configure `BEYLA_OPEN_PORT` to specify which ports to instrument (e.g., `80,443,8080,8443,3000`) or use `BEYLA_EXECUTABLE_NAME` to target specific binaries.
- **Performance impact**: Beyla's eBPF programs add approximately **1–3 microseconds** per request, which is negligible for most services. Memory usage is typically **50–100 MB** per Beyla DaemonSet pod.
- **License estimate**: each instrumented service generates approximately **1–5 KB/minute** of metric data (depending on endpoint cardinality). A cluster with 50 services generates approximately **100–400 MB/day** of Beyla metrics.
- Splunk RBAC: assign a **`sre_analyst`** role with **`srchIndexesAllowed`** including `containers`.

### Step 1 — Configure data collection
(1) **Beyla DaemonSet deployment**: deploy Beyla with OTLP export to the local OTel Collector:
```yaml
apiVersion: apps/v1
kind: DaemonSet
metadata:
  name: beyla
  namespace: monitoring
spec:
  selector:
    matchLabels:
      app: beyla
  template:
    spec:
      hostPID: true
      containers:
      - name: beyla
        image: grafana/beyla:latest
        env:
        - name: BEYLA_OPEN_PORT
          value: "80,443,8080,8443,3000"
        - name: OTEL_EXPORTER_OTLP_ENDPOINT
          value: "http://localhost:4318"
        securityContext:
          privileged: true
```

Beyla requires **hostPID** access to discover processes on the node and **privileged** mode to load eBPF programs. The `BEYLA_OPEN_PORT` setting tells Beyla to instrument any process listening on these ports.

(2) **Metric naming conventions**: Beyla generates metrics following **OpenTelemetry semantic conventions**:
  — **`http.server.request.duration`**: histogram of HTTP request latency (server-side)
  — **`http.client.request.duration`**: histogram of HTTP request latency (client-side / outgoing calls)
  — **`http.server.request.body.size`**: request body size
  — **`rpc.server.duration`**: gRPC server-side request duration
  Dimensions include: `service.name`, `http.request.method`, `http.response.status_code`, `http.route`, `url.path`

(3) **OTel Collector pipeline configuration**: configure the Splunk OTel Collector to receive OTLP metrics and export to Splunk HEC:
  — **Receiver**: `otlp` with gRPC (4317) and HTTP (4318) endpoints
  — **Processor**: `batch` (200ms timeout, 8192 send batch size) + `resource/beyla` (add `sourcetype=beyla:metrics`)
  — **Exporter**: `splunk_hec` with metric event support enabled

(4) **Service name resolution**: by default, Beyla uses the **executable name** as the service name (e.g., `nginx`, `python3`, `java`). For meaningful service names:
  — Set the `OTEL_SERVICE_NAME` environment variable in each application pod
  — Configure Beyla's **service name discovery** to read from Kubernetes labels (`app.kubernetes.io/name`)
  — Use the OTel Collector's **k8sattributes processor** to enrich metrics with Kubernetes labels

(5) **Trace collection**: Beyla generates distributed traces alongside metrics. Configure the OTel Collector to export traces to **Splunk Observability Cloud** (via the `sapm` exporter) or to **`index=containers`** with **`sourcetype=beyla:traces`** for SPL-based trace analysis. Traces provide per-request detail that complements the aggregate RED metrics.

(6) **Pipeline health monitoring**: collect the OTel Collector's **internal metrics** (**`sourcetype=otel:metrics`**) to monitor the Beyla-to-Splunk pipeline. Key metrics: `otelcol_receiver_accepted_metric_points` (are metrics arriving from Beyla?), `otelcol_exporter_send_failed_metric_points` (are exports to Splunk failing?), `otelcol_processor_batch_batch_send_size` (is batching efficient?).

### Step 2 — Create the search and alert
The primary SPL uses **`mstats`** to query Beyla's HTTP server duration metrics, computing RED aggregations per service in 5-minute windows. The **severity classification**:
  — **CRITICAL** (latency): p99 > 5000ms — the service is severely degraded
  — **HIGH** (latency): p95 > 2000ms — significant latency affecting user experience
  — **MEDIUM** (latency): p95 > 500ms — elevated latency worth investigating
  — **CRITICAL** (error): error_rate > 10% — major reliability problem
  — **HIGH** (error): error_rate > 5% — elevated error rate
  — **MEDIUM** (error): error_rate > 1% — worth investigating

The anomaly detection variant computes a **z-score** for each endpoint's average latency relative to its rolling baseline. A z-score > 3 indicates an **ANOMALY** (>3 standard deviations from mean), > 2 indicates a **WARNING**. This catches gradual degradation and sudden spikes that absolute thresholds miss.

The coverage gap analysis variant compares **running services** (from `kube:pod:status`) with **services generating Beyla metrics** to identify uninstrumented services. This ensures the auto-instrumentation layer covers all production workloads.

Schedule the RED metric search every **5 minutes** and alert on CRITICAL status (PagerDuty P2). Schedule the anomaly detection every **15 minutes** and alert on ANOMALY deviations. Schedule the coverage analysis **daily** and report uninstrumented services.

### Step 3 — Validate
(a) Verify Beyla metrics: `| mstats count(http.server.request.duration) WHERE index=containers AND sourcetype="beyla:metrics" BY service.name span=5m | head 20`. Should show metric counts per service.
(b) Generate test traffic: `kubectl exec <test-pod> -- curl http://<target-service>:8080/health` and verify the request appears in Beyla metrics within 5 minutes.
(c) Verify service names: `| mstats count(http.server.request.duration) WHERE index=containers BY service.name | sort -count`. Service names should be meaningful (not merely executable names).
(d) Test anomaly detection: introduce artificial latency to a test service (e.g., add a sleep) and verify the z-score increases above the ANOMALY threshold.
(e) Verify coverage: compare the list of services in `kube:pod:status` with services generating Beyla metrics. Any production service missing Beyla metrics indicates an instrumentation gap.

### Step 4 — Operationalize dashboards and runbooks
- Row A: **single-value tiles** — services monitored, total request rate (all services), average p95 latency, average error rate, instrumentation coverage percentage.
- Row B: **RED metric panels** per service — three columns: request rate (line chart), error rate (area chart, red fill), latency percentiles (p50, p95, p99 band chart).
- Row C: **anomaly table** — svc, endpoint, method, avg_latency, baseline_avg, z_score, deviation. Red rows for ANOMALY.
- Row D: **coverage matrix** — namespace, uninstrumented_services, service_list. Highlights services missing eBPF metrics.
- **Alerting**: CRITICAL latency/error → PagerDuty P2 + Slack `#sre-alerts`; ANOMALY z-score > 3 → Slack `#sre-alerts`; coverage below 90% → weekly report to platform team; pipeline health degradation (otel:metrics export failures) → Slack `#monitoring-ops`.
- **Runbook** (owner: SRE/platform team): (1) check service health via RED metrics, (2) drill into affected endpoints via the anomaly table, (3) correlate with Tetragon events (UC-3.5.14) and network flows (UC-3.5.13) for root-cause analysis, (4) verify Beyla instrumentation is active on the target node.

### Step 5 — Visualization, alert design, and troubleshooting
- **Visualization**: use a **service topology map** where node size represents request volume, node color represents health (green/amber/red based on error rate), and edge thickness represents inter-service call volume. Beyla's client-side metrics (`http.client.request.duration`) enable mapping service-to-service dependencies automatically.
- **Alert design**: include `service.name`, `requests`, `error_rate`, `p95_latency`, `p99_latency`, `latency_status`, `error_status`, and for anomalies include `endpoint`, `z_score`, `deviation`, `baseline_avg`.
- **No metrics for a known service** — Beyla may not be discovering the service's listening port. Check Beyla logs: `kubectl logs -n monitoring <beyla-pod> | grep -i discover`. Verify the service's port is listed in `BEYLA_OPEN_PORT` or switch to `BEYLA_EXECUTABLE_NAME` targeting.
- **Service names show as executable names** — the `OTEL_SERVICE_NAME` environment variable is not set in the application pod. Configure the **k8sattributes processor** in the OTel Collector to inject Kubernetes labels as resource attributes.
- **High cardinality in url.path** — REST APIs with path parameters (e.g., `/api/users/12345`) create unique paths per request, leading to metric cardinality explosion. Configure Beyla's **route decoration** or the OTel Collector's **attributes processor** to normalize paths (e.g., `/api/users/{id}`).
- **Metrics missing after node reboot** — Beyla's eBPF programs are loaded into the kernel and persist only while the Beyla process runs. After a node reboot, the DaemonSet restarts and reattaches eBPF programs, but there is a brief gap in metrics during restart. This gap is expected and typically lasts under 60 seconds.
- **Pipeline backpressure** — if the OTel Collector's export queue fills up, Beyla metrics are dropped. Monitor `otelcol_exporter_queue_size` and increase the collector's memory limit or batch size if needed.

## SPL

```spl
`comment("--- Beyla Auto-Instrumented RED Metrics — Service Latency and Error Rates ---")`
| mstats avg(http.server.request.duration) as avg_latency_ms,
    perc95(http.server.request.duration) as p95_latency_ms,
    perc99(http.server.request.duration) as p99_latency_ms,
    count(http.server.request.duration) as total_requests
    WHERE index=containers AND sourcetype="beyla:metrics"
    BY service.name, http.request.method, http.response.status_code
    span=5m
| eval is_error=if(http.response.status_code >= 400 AND http.response.status_code < 600, 1, 0)
| stats sum(total_requests) as requests,
    sum(eval(if(is_error=1, total_requests, 0))) as errors,
    avg(avg_latency_ms) as avg_latency,
    max(p95_latency_ms) as p95_latency,
    max(p99_latency_ms) as p99_latency
    by _time, service.name
| eval error_rate=round(errors / requests * 100, 2)
| eval latency_status=case(
    p99_latency > 5000, "CRITICAL",
    p95_latency > 2000, "HIGH",
    p95_latency > 500, "MEDIUM",
    1=1, "OK")
| eval error_status=case(
    error_rate > 10, "CRITICAL",
    error_rate > 5, "HIGH",
    error_rate > 1, "MEDIUM",
    1=1, "OK")
| table _time service.name requests errors error_rate avg_latency p95_latency p99_latency latency_status error_status

`comment("--- Beyla Endpoint Anomaly Detection — Latency Deviation from Baseline ---")`
index=containers sourcetype="beyla:metrics" metric_name="http.server.request.duration"
| eval svc=coalesce(service_name, "service.name")
| eval endpoint=coalesce(http_target, url_path, http_route)
| eval method=coalesce(http_method, http_request_method)
| bin _time span=15m
| stats avg(metric_value) as avg_latency, perc95(metric_value) as p95, count as req_count by _time, svc, endpoint, method
| eventstats avg(avg_latency) as baseline_avg, stdev(avg_latency) as baseline_stdev by svc, endpoint, method
| eval z_score=round((avg_latency - baseline_avg) / if(baseline_stdev > 0, baseline_stdev, 1), 2)
| eval deviation=case(
    z_score > 3, "ANOMALY",
    z_score > 2, "WARNING",
    1=1, "NORMAL")
| where deviation != "NORMAL" AND req_count > 10
| sort -z_score
| table _time svc endpoint method avg_latency baseline_avg z_score deviation req_count

`comment("--- Beyla Instrumentation Coverage — Services Without eBPF Metrics ---")`
index=containers sourcetype="kube:pod:status"
| eval ns=coalesce(namespace, metadata.namespace)
| eval svc_label=coalesce(label_app, label_app_kubernetes_io_name)
| where ns NOT IN ("kube-system", "monitoring", "cert-manager")
| dedup ns, svc_label sortby -_time
| join type=left svc_label [
    search index=containers sourcetype="beyla:metrics" earliest=-1h
    | eval svc_label=coalesce(service_name, "service.name")
    | stats count as metric_count by svc_label
]
| eval instrumented=if(isnotnull(metric_count) AND metric_count > 0, "YES", "NO")
| where instrumented="NO"
| stats dc(svc_label) as uninstrumented_services, values(svc_label) as service_list by ns
| sort -uninstrumented_services
| table ns uninstrumented_services service_list
```

## Visualization

RED metric dashboard (request rate line, error rate area, latency percentile bands), endpoint anomaly scatter plot, instrumentation coverage matrix, service health status table, single-value tiles (services monitored, anomalies detected, coverage %).

## Known False Positives

**cold_start_latency_spike** — When a service pod starts or scales up, the first few requests experience higher latency due to JIT compilation, connection pool initialization, and cache warming. Beyla captures these requests, inflating the initial p95/p99 values. Exclude the first 60 seconds after pod start from latency alerting or use a minimum request count threshold.

**health_check_skew** — Kubernetes health check endpoints (/health, /readyz, /livez) respond in sub-millisecond times, pulling down average latency numbers and inflating request counts. These endpoints should be filtered from RED metric calculations or tracked separately.

**batch_job_endpoints** — Some services have endpoints that process batch operations with legitimately long response times (e.g., report generation, data export). These endpoints consistently trigger latency alerts even when functioning correctly. Create endpoint-specific thresholds in a lookup and exclude known long-running endpoints from standard latency alerting.

**metric_cardinality_artifacts** — When url.path is not normalized, each unique path creates a separate metric series. The z-score calculation may flag low-traffic paths as anomalies simply because they have insufficient data points for a stable baseline. Require a minimum request count (e.g., 10 requests per 15-minute window) before computing z-scores.

**beyla_binary_mismatch** — Beyla uses heuristics to identify service processes. If multiple processes listen on the same port (e.g., a sidecar proxy and the main application), Beyla may attribute all traffic to one process. This creates phantom services or missing services in the metrics. Use BEYLA_EXECUTABLE_NAME to disambiguate.

**grpc_status_codes** — gRPC uses numeric status codes where some non-zero codes (like CANCELLED or DEADLINE_EXCEEDED) are expected in normal operation. Beyla maps these to error counts, inflating the error rate. Configure gRPC-aware error classification to treat expected status codes as non-errors.

## References

- [Grafana Beyla — Introduction](https://grafana.com/docs/beyla/latest/)
- [Grafana Beyla — Kubernetes Deployment](https://grafana.com/docs/beyla/latest/setup/kubernetes/)
- [OpenTelemetry — Semantic Conventions for HTTP](https://opentelemetry.io/docs/specs/semconv/http/)
- [Splunk — mstats Command Reference](https://docs.splunk.com/Documentation/Splunk/latest/SearchReference/Mstats)
- [Splunk — eventstats Command Reference](https://docs.splunk.com/Documentation/Splunk/latest/SearchReference/Eventstats)
