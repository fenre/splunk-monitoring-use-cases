<!-- AUTO-GENERATED from UC-3.5.9.json — DO NOT EDIT -->

---
id: "3.5.9"
title: "Service Mesh Control Plane Health"
status: "verified"
criticality: "critical"
splunkPillar: "Observability"
---

# UC-3.5.9 · Service Mesh Control Plane Health

> **Criticality:** Critical &middot; **Difficulty:** Advanced &middot; **Pillar:** Observability &middot; **Type:** Availability, Fault, Performance &middot; **Wave:** Crawl &middot; **Status:** Verified

*The service mesh has a central brain that tells all the little network helpers how to route traffic — we watch that brain's vital signs to catch problems before the helpers stop receiving instructions.*

---

## Description

Monitors the Istio service mesh control plane (istiod) by tracking **XDS push success rates**, **configuration validation failures**, **listener conflicts**, **sidecar injection counts**, and **gRPC push error patterns** — classifying overall control plane health as CRITICAL, DEGRADED, or HEALTHY so platform teams detect istiod degradation before it silently blocks Envoy proxy configuration updates across the mesh.

## Value

The Istio control plane is the brain of the service mesh — when istiod fails, no new routing rules propagate, no sidecars get injected, and certificate rotation stalls. Unlike data plane failures that produce immediate user-visible errors, control plane degradation is insidious: existing proxies continue serving stale configuration while new deployments silently fail to join the mesh. Monitoring XDS push error rates and validation failures gives platform teams the 5–10 minute warning needed to intervene before a configuration drift cascade affects production traffic.

## Implementation

Scrape istiod Prometheus metrics via OTel Collector Prometheus receiver into index=containers. Build two search variants: 5-minute istiod metric aggregation with push error rate and health classification, and 15-minute log error categorization from istiod container logs. Alert when cp_health enters CRITICAL or DEGRADED state sustained for 2+ intervals.

## Detailed Implementation

### Prerequisites
- **Istio** 1.14+ service mesh with **istiod** deployed as a **Deployment** in the `istio-system` namespace. Istiod serves as the unified control plane handling **XDS** (Envoy configuration distribution), **certificate authority** (mTLS certificate issuance), **configuration validation** (Galley), and **sidecar injection** (mutating webhook).
- **Splunk OpenTelemetry Collector** deployed as a **DaemonSet** with the **Prometheus receiver** configured to scrape the istiod `/metrics` endpoint. The istiod metrics port is typically **15014** (HTTP) with the path `/metrics`. Configure the Prometheus receiver's `scrape_configs` to target the istiod **Service** (`istiod.istio-system.svc:15014`) at **30-second intervals**.
- **Splunk Connect for Kubernetes** or the OTel Collector's **filelog receiver** for collecting **`sourcetype=kube:container:logs`** from the istiod pods. Istiod logs are structured JSON by default in recent versions; configure the log pipeline to preserve the JSON structure.
- **Splunk HEC** token for **`index=containers`** with appropriate sourcetype routing rules. Secondary tokens for **`sourcetype=kube:events`** and **`sourcetype=kube:apiserver:audit`** if collecting API server audit logs.
- **Kubernetes RBAC**: the OTel Collector's **ServiceAccount** needs `get` on **Services** and **Endpoints** in `istio-system` for Prometheus service discovery. For API server audit logs, the collector needs `get` on **audit** events.
- Splunk RBAC: users running control plane health searches need **`srchIndexesAllowed`** including `containers`; assign via a **`mesh_operator`** role.
- **License estimate**: istiod metrics at 30-second scrape intervals generate approximately 2–5 MB/day per istiod replica. Istiod logs vary from 500 KB/day (healthy) to 50 MB/day (degraded with high error rates).

### Step 1 — Configure data collection
(1) **Prometheus metrics scraping**: configure the OTel Collector Prometheus receiver to scrape the istiod metrics endpoint:
— **Target**: `istiod.istio-system.svc:15014/metrics`
— **Interval**: 30 seconds
— **Key metrics** to validate:
- `pilot_xds_pushes` (counter) — total **XDS configuration pushes** to Envoy proxies, labeled by `type` (cds, eds, lds, rds). This is the primary indicator of control plane activity.
- `pilot_xds_push_errors` (counter) — failed XDS pushes. A rising rate indicates configuration distribution failures.
- `pilot_proxy_convergence_time` (histogram) — time from configuration change to **proxy update acknowledgment**. The p99 should remain under 10 seconds for a healthy mesh.
- `pilot_conflict_outbound_listener` (gauge) — **listener conflicts** caused by overlapping port/protocol definitions across services. Any value > 0 indicates misconfiguration.
- `galley_validation_passed` / `galley_validation_failed` (counters) — configuration validation results. Rising failures indicate invalid **VirtualService**, **DestinationRule**, or **Gateway** resources being applied.
- `sidecar_injection_requests_total` (counter) — sidecar injection requests received by the **mutating webhook**. A sudden drop to zero may indicate webhook failure.
- `citadel_server_csr_count` (counter) — certificate signing requests processed. A drop indicates certificate authority issues.

(2) **Istiod container log collection**: collect logs from the `discovery` container in istiod pods. Key log patterns:
- **XDS push errors**: `"xds: push error"` or `"pilot: push failed"` — indicates gRPC stream failures between istiod and Envoy proxies
- **Webhook timeouts**: `"webhook timeout"` or `"admission webhook timed out"` — indicates the API server cannot reach istiod for sidecar injection or config validation
- **Leader election**: `"leader election"` or `"leader lost"` — indicates istiod HA failover events (expected during upgrades, concerning during normal operation)
- **Certificate errors**: `"certificate error"` or `"CSR failed"` — indicates mTLS certificate rotation failures
- **Configuration rejection**: `"config rejected"` or `"validation failed"` — indicates the **Galley validator** rejecting malformed Istio resources
- **Resource exhaustion**: `"OOM"` or `"panic"` — indicates istiod running out of memory or crashing (often in large meshes)

(3) **Kubernetes events**: collect **Warning** events from the `istio-system` namespace. Key reasons to watch: **OOMKilled** (istiod memory exhaustion), **CrashLoopBackOff** (repeated crashes), **FailedScheduling** (cannot place istiod pod), and **Unhealthy** (readiness probe failures).

(4) **API server audit logs** (optional but recommended for production): collect audit events for `ValidatingWebhookConfiguration` and `MutatingWebhookConfiguration` resources. These show when the API server **fails to reach** the istiod webhook, which means new pods will not get sidecar injection and invalid configurations will not be caught.

### Step 2 — Create the search and alert
The primary SPL aggregates **istiod Prometheus metrics** into 5-minute windows. The **`cp_health`** classification:
— **CRITICAL**: push error rate exceeds **20%** OR listener conflicts exceed **10** — the control plane is actively failing to distribute configuration and the mesh is at risk
— **DEGRADED**: push error rate exceeds **5%** OR validation failure rate exceeds **10%** — the control plane is experiencing issues that may escalate
— **HEALTHY**: all metrics within normal bounds

The log analysis variant categorizes istiod container log entries into **error categories**:
— **XDS_PUSH_ERROR**: the most impactful — means Envoy proxies are not receiving updated configuration
— **WEBHOOK_TIMEOUT**: means new pod deployments may fail to get **sidecar injection**
— **LEADER_ELECTION**: expected during upgrades; unexpected during normal operation indicates instability
— **CERT_ERROR**: means **mTLS certificate rotation** is failing, which will eventually cause service-to-service communication failures
— **CONFIG_VALIDATION**: means someone is applying invalid Istio resources
— **RESOURCE_EXHAUSTION**: means istiod needs more CPU/memory resources

Schedule the metrics health search every **5 minutes** over **`-15m`** (3 intervals for smoothing). Alert when `cp_health=CRITICAL` for 2+ consecutive intervals (10 minutes). Schedule the log categorization every **15 minutes**. Alert when `XDS_PUSH_ERROR` count exceeds **50** in a 15-minute window or when **WEBHOOK_TIMEOUT** appears in logs.

### Step 3 — Validate
(a) Verify metrics collection: `index=containers sourcetype="otel:metrics" metric_name="pilot_xds_pushes" earliest=-1h | stats sum(metric_value) by type`. Should show non-zero values for cds, eds, lds, rds.
(b) Simulate a push error: apply an invalid **DestinationRule** that creates a listener conflict: `kubectl apply -f - <<< '{apiVersion: networking.istio.io/v1beta1, kind: DestinationRule, metadata: {name: test-conflict}, spec: {host: "*.local", trafficPolicy: {portLevelSettings: [{port: {number: 80}}]}}}'`. Verify: `index=containers sourcetype="otel:metrics" metric_name="pilot_conflict_outbound_listener" metric_value>0 earliest=-5m`.
(c) Simulate a **webhook timeout**: temporarily scale istiod to 0 replicas and attempt a pod deployment in a labeled namespace. The API server should log a webhook timeout. Then scale istiod back.
(d) Verify log collection: `index=containers sourcetype="kube:container:logs" container_name="discovery" earliest=-1h | head 5`. Should show istiod structured log entries.
(e) Check **sidecar injection**: deploy a test pod in an injection-enabled namespace and verify: `index=containers sourcetype="otel:metrics" metric_name="sidecar_injection_requests_total" earliest=-5m | stats sum(metric_value) as injections`.

### Step 4 — Operationalize dashboards and runbooks
- Row A: **single-value tiles** — cp_health (CRITICAL=red, DEGRADED=amber, HEALTHY=green), push_error_rate %, validation_fail_rate %, total injections last 1h, listener conflicts (any > 0 = red).
- Row B: **line chart** of total_pushes and push_errors over 24h at 5-minute granularity — the gap between the lines shows push success. Overlay the push_error_rate as a secondary Y-axis.
- Row C: **stacked bar chart** of error categories from istiod logs over 24h at 15-minute intervals — shows whether errors are concentrated in one category or distributed.
- Row D: **table** of istiod pod status — pod name, ready status, restart count, last restart time, age. Red rows for pods not ready or with restarts > 0.
- **Alerting**: CRITICAL cp_health for 10+ min → PagerDuty **P1** (service mesh is degrading); DEGRADED for 30+ min → PagerDuty **P3**; WEBHOOK_TIMEOUT in logs → Slack `#mesh-ops` (injection may be failing); leader election events during non-maintenance → Slack notification.
- **Runbook** (owner: service mesh platform team): (1) check istiod pod health: `kubectl get pods -n istio-system -l app=istiod`, (2) check istiod logs for errors: `kubectl logs -n istio-system deploy/istiod --tail=50`, (3) check webhook configuration: `kubectl get validatingwebhookconfigurations istio-validator-istio-system`, (4) check proxy sync status: `istioctl proxy-status`, (5) if push errors: check Envoy proxy logs for **NACK** responses: `istioctl proxy-config log <pod> --level xds:debug`.

### Step 5 — Visualization, alert design, and troubleshooting
- **Visualization**: use a **mesh topology diagram** overlaid with control plane health status — show istiod at the center with connections to each namespace's proxy fleet, colored by push success rate. Pair with a **convergence time histogram** showing the distribution of proxy update latency.
- **Alert design**: include `cp_health`, `push_error_rate`, `validation_fail_rate`, `listener_conflicts`, `total_pushes`, `injections`, and the top 3 error categories from logs in the alert payload.
- **Push error rate is always 0 but mesh is misbehaving** — istiod may be healthy but Envoy proxies may not be connected. Check `pilot_proxy_queue_time` and `pilot_proxy_convergence_time` for stale connections. Also check if proxies are running an incompatible Istio version.
- **Validation failures spike after upgrade** — Istio version upgrades may introduce stricter validation rules. Review `galley_validation_failed` alongside `kubectl get istiooperator` for version skew between the control plane and custom resources.
- **Sidecar injection count drops to zero** — the istiod webhook may have been accidentally deleted or the webhook TLS certificate may have expired. Verify: `kubectl get mutatingwebhookconfigurations istio-sidecar-injector` and check the caBundle field.
- **Leader election churning** — frequent leader elections indicate istiod pods are unhealthy or network partitions are occurring between replicas. Check pod resource usage (CPU/memory) and network connectivity between istiod replicas.

## SPL

```spl
`comment("--- Istio Control Plane Health — istiod Metrics and Error Detection ---")`
index=containers sourcetype="otel:metrics" metric_name IN ("pilot_xds_pushes", "pilot_proxy_convergence_time_bucket", "pilot_conflict_outbound_listener", "galley_validation_passed", "galley_validation_failed", "sidecar_injection_requests_total", "pilot_xds_push_errors")
| eval metric=coalesce(metric_name, _metric_name)
| eval push_type=coalesce(type, push_type, "unknown")
| bin _time span=5m
| stats sum(eval(if(metric="pilot_xds_pushes", metric_value, 0))) as total_pushes,
    sum(eval(if(metric="pilot_xds_push_errors", metric_value, 0))) as push_errors,
    sum(eval(if(metric="pilot_conflict_outbound_listener", metric_value, 0))) as listener_conflicts,
    sum(eval(if(metric="galley_validation_failed", metric_value, 0))) as validation_failures,
    sum(eval(if(metric="galley_validation_passed", metric_value, 0))) as validation_passed,
    sum(eval(if(metric="sidecar_injection_requests_total", metric_value, 0))) as injections
    by _time
| eval push_error_rate=if(total_pushes > 0, round(100 * push_errors / total_pushes, 2), 0)
| eval validation_fail_rate=if((validation_passed + validation_failures) > 0, round(100 * validation_failures / (validation_passed + validation_failures), 2), 0)
| eval cp_health=case(
    push_error_rate > 20 OR listener_conflicts > 10, "CRITICAL",
    push_error_rate > 5 OR validation_fail_rate > 10, "DEGRADED",
    1=1, "HEALTHY")
| table _time total_pushes push_errors push_error_rate listener_conflicts validation_failures validation_fail_rate injections cp_health

`comment("--- istiod Log Error Categorization and gRPC Push Failure Analysis ---")`
index=containers sourcetype="kube:container:logs" (container_name="discovery" OR container_name="istiod")
| eval error_cat=case(
    match(_raw, "(?i)xds.*push.*error|push.*fail"), "XDS_PUSH_ERROR",
    match(_raw, "(?i)webhook.*timeout|admission.*timeout"), "WEBHOOK_TIMEOUT",
    match(_raw, "(?i)leader.*election|leader.*lost"), "LEADER_ELECTION",
    match(_raw, "(?i)certificate.*error|CSR.*fail"), "CERT_ERROR",
    match(_raw, "(?i)config.*reject|validation.*fail"), "CONFIG_VALIDATION",
    match(_raw, "(?i)OOM|out.of.memory|panic"), "RESOURCE_EXHAUSTION",
    match(_raw, "(?i)error|warn"), "OTHER_ERROR",
    1=1, "INFO")
| where error_cat != "INFO"
| bin _time span=15m
| stats count as error_count,
    dc(pod) as affected_pods,
    latest(_raw) as example_msg
    by error_cat, _time
| sort -error_count
```

## Visualization

Single-value tiles (cp_health, push_error_rate, validation_fail_rate), line chart of pushes/errors over time, stacked bar of error categories from logs, replica health table, single-value (injection count last 1h).

## Known False Positives

**upgrade_window_churn** — During Istio control plane upgrades, istiod pods restart, leader elections occur, and XDS push error rates temporarily spike as the new version takes over. These are expected transient events during the upgrade window. Correlate with known maintenance schedules and suppress alerts during planned upgrade windows.

**proxy_version_skew** — When Envoy sidecar proxies run a different Istio version than the control plane (common during canary upgrades), istiod may report increased push errors for specific proxy versions. These errors resolve as proxies are gradually updated. Check the `proxy_version` label on push metrics to identify version-related errors.

**config_validation_learning** — Platform teams authoring new Istio resources (VirtualService, DestinationRule, AuthorizationPolicy) during development produce validation failures that appear as control plane issues. These are expected in development namespaces. Use namespace-aware alerting that excludes development namespaces from validation failure alerts.

**resource_quota_scaling** — In autoscaled clusters, istiod memory consumption grows proportionally with the number of services and endpoints. During scale-up events, istiod may briefly approach its memory limit, causing garbage collection pauses that appear as degraded push performance. This resolves after istiod's HPA scales the deployment.

**api_server_latency** — High API server latency (from cluster-wide load, etcd compaction, or node pressure) slows istiod's ability to watch configuration changes and distribute updates. The resulting push delays appear as control plane degradation but are actually infrastructure-level issues. Correlate with API server latency metrics.

**certificate_rotation_burst** — Periodic mTLS certificate rotation across the mesh causes a burst of CSR requests to istiod's certificate authority component. This temporarily increases CPU usage and may cause push delays. The burst pattern is predictable and correlates with the certificate TTL setting.

## References

- [Istio — istiod Metrics Reference](https://istio.io/latest/docs/reference/commands/pilot-discovery/#metrics)
- [Istio — Troubleshooting the Control Plane](https://istio.io/latest/docs/ops/diagnostic-tools/controlz/)
- [Istio — Debugging Envoy and Istiod](https://istio.io/latest/docs/ops/diagnostic-tools/proxy-cmd/)
- [Splunk OpenTelemetry Collector — Prometheus Receiver](https://docs.splunk.com/observability/en/gdi/opentelemetry/components/prometheus-receiver.html)
- [Splunk Connect for Kubernetes](https://github.com/splunk/splunk-connect-for-kubernetes)
