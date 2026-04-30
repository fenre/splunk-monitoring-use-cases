<!-- AUTO-GENERATED from UC-3.5.10.json — DO NOT EDIT -->

---
id: "3.5.10"
title: "Ingress Gateway Latency"
status: "verified"
criticality: "high"
splunkPillar: "Observability"
---

# UC-3.5.10 · Ingress Gateway Latency

## Description

Tracks Istio Ingress Gateway request latency at **p50, p95, and p99** percentiles per route using Envoy access logs, comparing real-time 5-minute windows against SLO thresholds (p95 < 500ms, error rate < 1%) and computing daily p95 trends with 7-day moving averages to detect latency regressions before they breach external SLAs — covering TLS termination, authentication, routing, and upstream response time in a single measurement.

## Value

The ingress gateway is the first component every external request touches — its latency is a direct component of every user's experience. A 200ms increase at the gateway adds 200ms to every API call, page load, and mobile app request. Unlike internal mesh latency that affects individual service pairs, gateway latency is multiplicative across all external traffic. Trending p95 daily with a 7-day SMA reveals slow regressions that 5-minute monitoring misses: a 10ms/day p95 creep accumulates to 300ms over a month, silently eroding user experience. SLO tracking at the gateway provides the contractual basis for infrastructure investment decisions.

## Implementation

Collect Istio Ingress Gateway Envoy access logs via Splunk Connect for Kubernetes or OTel filelog receiver into index=containers. Build two search variants: 5-minute p50/p95/p99 latency by route with SLO breach detection, and daily p95 trend with 7-day SMA and regression flags. Alert when p95 exceeds 500ms or when the daily trend shows REGRESSION for 2+ consecutive days.

## Detailed Implementation

Prerequisites
• **Istio** 1.14+ service mesh with the **Istio Ingress Gateway** deployed as a **LoadBalancer** or **NodePort** Service in the `istio-system` namespace. The gateway handles **TLS termination**, **authentication** (via RequestAuthentication), **authorization** (via AuthorizationPolicy), and **routing** (via VirtualService/Gateway resources) for all north-south traffic.
• **Envoy access logging** enabled on the ingress gateway. Configure via the Istio **Telemetry API**:
  — Set `meshConfig.accessLogFile` to `/dev/stdout`
  — Set `meshConfig.accessLogEncoding` to `JSON`
  — Alternatively, use a namespace-scoped **Telemetry** resource targeting only the `istio-system` namespace to avoid enabling access logs mesh-wide.
• **Splunk Connect for Kubernetes** or the OTel Collector's **filelog receiver** configured to collect access logs from istio-ingressgateway pods and index them as **`sourcetype=envoy:accesslog`** in **`index=containers`**.
• **Prometheus metrics** scraping: configure the OTel Collector **Prometheus receiver** to scrape the ingress gateway pods' `/stats/prometheus` endpoint on port **15020**. Key metrics:
  — `istio_request_duration_milliseconds_bucket` (histogram — provides percentile computation without per-request log storage)
  — `istio_requests_total` (counter — request rate by response code)
  — `envoy_server_live` (gauge — gateway liveness)
• **Splunk HEC** token for **`index=containers`** with sourcetype routing for access logs, metrics, and events.
• **SLO definition**: establish explicit SLO thresholds per route or globally:
  — Default: **p95 < 500ms**, **error rate < 1%**
  — Create a **lookup** (`gateway_slo_thresholds.csv`) mapping `route` to `p95_threshold_ms` and `error_rate_threshold_pct` for per-route SLO customization.
• At least **7 days** of historical access log data for meaningful SMA trending; **30 days** is ideal.
• **License estimate**: access log volume is proportional to request volume. At ~400 bytes per JSON log line, 1 million requests/day generates ~400 MB/day. For high-traffic gateways, consider using **metrics-only** mode (Prometheus histogram) which provides percentiles at a fraction of the license cost.
• Splunk RBAC: assign a **`gateway_analyst`** role with **`srchIndexesAllowed`** including `containers`.

Step 1 — Configure data collection
(1) **Envoy access log format**: the Istio Ingress Gateway emits Envoy **JSON access logs** with the following key fields:
— **`duration`** (request duration in milliseconds — the primary latency measurement, includes downstream processing, upstream response time, and Envoy internal processing)
— **`response_code`** (HTTP status code — for error rate calculation)
— **`response_flags`** (Envoy response flags: `DC` = downstream connection termination, `UO` = upstream overflow, `UF` = upstream connection failure, `UT` = upstream request timeout, `NR` = no route configured, `URX` = upstream retry limit exceeded — these flags provide root-cause context for latency spikes)
— **`authority`** (the Host header — maps to the virtual host/route)
— **`upstream_cluster`** (the Envoy cluster that served the request — maps to the destination service)
— **`bytes_sent`** and **`bytes_received`** (for bandwidth correlation)
— **`downstream_remote_address`** (client IP for geographic analysis)

(2) **Response flag interpretation**: the `response_flags` field is critical for diagnosing latency root causes:
— **`UT`** (Upstream Timeout): the backend service did not respond within the configured timeout — this is the most common cause of high p99 latency
— **`UO`** (Upstream Overflow): the circuit breaker tripped because the connection pool was full — indicates backend capacity saturation (correlate with UC-3.5.8)
— **`DC`** (Downstream Connection Termination): the client disconnected before receiving a response — may inflate error counts without a real backend issue
— **`NR`** (No Route Configured): the request did not match any VirtualService — indicates configuration errors
— **`UF`** (Upstream Connection Failure): the gateway could not connect to the backend — indicates service unavailability

(3) **Gateway pod metrics**: collect **`sourcetype=kube:pod:status`** for the istio-ingressgateway pods to correlate latency with **replica count** and **resource utilization**. A latency regression that coincides with gateway pod restarts or HPA scaling events indicates infrastructure-level causes rather than application-level causes.

(4) **Multi-gateway deployments**: if the cluster has multiple ingress gateways (e.g., public, private, internal), tag access logs with the gateway **Deployment name** or use the `pod_name` prefix to distinguish them in queries. Create separate dashboard rows for each gateway class.

Step 2 — Create the search and alert
The primary SPL computes **p50/p95/p99 latency** per route in 5-minute windows from access logs. The **`slo_breach`** flag triggers when:
— p95 exceeds **500ms** (the default SLO threshold for gateway latency)
— OR error rate exceeds **1%** (the default SLO threshold for availability)

The **`latency_flag`** classification:
— **CRITICAL**: p99 exceeds **2000ms** — some requests are experiencing unacceptable latency
— **DEGRADED**: p95 exceeds **500ms** — the tail latency is affecting a significant portion of users
— **HEALTHY**: all percentiles within acceptable bounds

The daily trend variant computes **daily p95** per route with a **7-day SMA** and flags **REGRESSION** when the daily p95 exceeds **1.5× the SMA** AND exceeds **200ms** absolute. This catches slow creep that 5-minute monitoring does not surface.

Schedule the 5-minute latency search as a **real-time alert** with a 5-minute window. Alert on CRITICAL latency_flag or sustained SLO breaches (3+ consecutive 5-minute intervals). Schedule the daily trend over **`-30d`** daily at **07:00** and alert on REGRESSION.

Step 3 — Validate
(a) Verify access log collection: `index=containers sourcetype="envoy:accesslog" earliest=-1h | where like(pod_name, "istio-ingressgateway%") | stats count`. Should be proportional to your ingress traffic.
(b) Verify latency field extraction: `index=containers sourcetype="envoy:accesslog" earliest=-5m | table authority duration response_code response_flags upstream_cluster`. All fields should populate.
(c) Generate latency test: `for i in $(seq 1 50); do curl -s -o /dev/null -w "%{time_total}\n" https://<gateway-host>/api/health; done`. Compare reported latency with the p50 computed by the search.
(d) Simulate a latency spike: deploy a backend service with an artificial delay (`sleep 2s`) and route through the gateway. Verify the p99 spike appears: `index=containers sourcetype="envoy:accesslog" route="<test-route>" earliest=-5m | stats p99(duration) as p99_ms`.
(e) Verify SLO breach detection: artificially lower the SLO threshold in the search (e.g., `p95_ms > 10`) and confirm `slo_breach=1` appears for normal traffic.

Step 4 — Operationalize dashboards and runbooks
• Row A: **single-value tiles** — current p50/p95/p99 (last 5 min), error rate %, SLO breach count (last 1h), latency_flag (CRITICAL=red, DEGRADED=amber, HEALTHY=green).
• Row B: **line chart** of p50/p95/p99 over 24h at 5-minute granularity per route — the p95-to-p99 gap reveals tail latency issues.
• Row C: **daily p95 trend** with **7-day SMA** overlay over 30 days — the primary capacity planning and regression detection signal.
• Row D: **route breakdown table** — route, p50_ms, p95_ms, p99_ms, request_count, error_rate, slo_breach, latency_flag. Sorted by p99 descending.
• **Alerting**: CRITICAL latency_flag → PagerDuty **P2** (user-facing degradation); sustained SLO breach for 15+ min → PagerDuty **P3**; REGRESSION in daily trend for 2+ days → Slack `#platform-ops`; error rate > 5% → PagerDuty **P1**.
• **Runbook** (owner: platform engineering): (1) check response flags for root cause: `UT` = backend slow (check backend service), `UO` = circuit breaker (check connection pool limits), `UF` = backend down (check backend pods), (2) check gateway pod CPU/memory utilization, (3) check if latency correlates with traffic volume increase (capacity issue) or specific route (application issue), (4) compare with upstream service latency to isolate gateway overhead vs backend latency.

Step 5 — Visualization, alert design, and troubleshooting
• **Visualization**: use a **latency distribution histogram** (bucket chart) showing the request duration distribution over 1h — reveals bimodal distributions where most requests are fast but a subset is very slow. Pair with a **response flags pie chart** to show the proportion of error types.
• **Alert design**: include `route`, `p50_ms`, `p95_ms`, `p99_ms`, `request_count`, `error_rate`, `slo_breach`, `latency_flag`, and the most common `response_flags` in the alert payload.
• **Latency appears constant at exactly the timeout value** — many requests timing out at the exact upstream timeout limit. Check the Envoy route timeout configuration: `istioctl proxy-config route <gateway-pod> -o json | grep timeout`.
• **p95 is fine but p99 is very high** — a small number of outlier requests are extremely slow. Check for specific routes or client IPs causing the tail. Often caused by TLS renegotiation, DNS resolution delays, or backend garbage collection pauses.
• **Access logs show zero requests** — the Telemetry API access log configuration may not be applied to the ingress gateway namespace. Verify: `kubectl get telemetry -n istio-system` and check that the access log provider is configured.
• **Multi-gateway latency comparison** — if the cluster has separate **public** and **internal** gateways, compare their latency profiles side-by-side. Internal gateways typically show lower latency because they skip TLS termination. A **convergence** of internal and external latency suggests the bottleneck is in the backend services, not the gateway itself.
• **SLO breach but no user complaints** — the SLO threshold may be too aggressive for the application. Review historical p95 baseline and adjust the lookup thresholds accordingly. Also check if the breaches are concentrated on low-traffic routes where a single slow request dominates the percentile.

## SPL

```spl
`comment("--- Ingress Gateway Latency — p50/p95/p99 by Route with SLO Tracking ---")`
index=containers sourcetype="envoy:accesslog"
| where like(upstream_cluster, "inbound%") OR like(pod_name, "istio-ingressgateway%")
| eval dur_ms=coalesce(tonumber(duration), tonumber(request_duration), 0)
| eval route=coalesce(route_name, authority, host, "unknown")
| eval status_class=case(
    response_code >= 200 AND response_code < 300, "2xx",
    response_code >= 300 AND response_code < 400, "3xx",
    response_code >= 400 AND response_code < 500, "4xx",
    response_code >= 500, "5xx",
    1=1, "other")
| eval resp_flag=coalesce(response_flags, "-")
| bin _time span=5m
| stats p50(dur_ms) as p50_ms,
    p95(dur_ms) as p95_ms,
    p99(dur_ms) as p99_ms,
    count as request_count,
    sum(eval(if(status_class="5xx",1,0))) as errors_5xx,
    dc(resp_flag) as unique_flags
    by _time, route
| eval error_rate=round(100 * errors_5xx / max(request_count, 1), 2)
| eval slo_breach=if(p95_ms > 500 OR error_rate > 1, 1, 0)
| eval latency_flag=case(
    p99_ms > 2000, "CRITICAL",
    p95_ms > 500, "DEGRADED",
    1=1, "HEALTHY")
| table _time route p50_ms p95_ms p99_ms request_count errors_5xx error_rate slo_breach latency_flag

`comment("--- Gateway Latency Trend — Daily Percentiles with SMA ---")`
index=containers sourcetype="envoy:accesslog"
| where like(upstream_cluster, "inbound%") OR like(pod_name, "istio-ingressgateway%")
| eval dur_ms=coalesce(tonumber(duration), tonumber(request_duration), 0)
| eval route=coalesce(route_name, authority, host, "unknown")
| bin _time span=1d
| stats p95(dur_ms) as daily_p95,
    p99(dur_ms) as daily_p99,
    count as daily_requests,
    avg(dur_ms) as daily_avg
    by _time, route
| trendline sma7(daily_p95) as sma_p95
| eval deviation_pct=round(100 * (daily_p95 - sma_p95) / max(sma_p95, 1), 1)
| eval trend_flag=case(daily_p95 > sma_p95 * 1.5 AND daily_p95 > 200, "REGRESSION", 1=1, "STABLE")
| table _time route daily_p95 daily_p99 sma_p95 deviation_pct daily_requests daily_avg trend_flag

`comment("--- Response Flag Analysis — Root-Cause Breakdown for Latency Issues ---")`
index=containers sourcetype="envoy:accesslog"
| where like(upstream_cluster, "inbound%") OR like(pod_name, "istio-ingressgateway%")
| eval dur_ms=coalesce(tonumber(duration), tonumber(request_duration), 0)
| eval route=coalesce(route_name, authority, host, "unknown")
| eval resp_flag=coalesce(response_flags, "-")
| where resp_flag != "-"
| stats count as flag_count,
    avg(dur_ms) as avg_latency_ms,
    p95(dur_ms) as p95_latency_ms,
    dc(route) as affected_routes,
    latest(route) as example_route
    by resp_flag
| eval flag_meaning=case(
    resp_flag="UT", "Upstream Timeout",
    resp_flag="UO", "Upstream Overflow (Circuit Breaker)",
    resp_flag="UF", "Upstream Connection Failure",
    resp_flag="DC", "Downstream Disconnected",
    resp_flag="NR", "No Route Configured",
    resp_flag="URX", "Upstream Retry Limit",
    resp_flag="DPE", "Downstream Protocol Error",
    1=1, resp_flag)
| sort -flag_count
| table resp_flag flag_meaning flag_count avg_latency_ms p95_latency_ms affected_routes example_route
```

## Visualization

Line chart of p50/p95/p99 over time per route, SLO burn-down gauge, stacked bar of request volume by status class, latency heatmap by route and hour, regression trend with SMA overlay.

## Known False Positives

**tls_handshake_cold_start** — The first request to a new TLS session incurs a full TLS handshake that adds 50–150ms of latency compared to subsequent requests using session resumption. If the ingress gateway has many short-lived connections (mobile clients, IoT devices), the p99 is dominated by handshake overhead rather than application latency. Separate first-request latency from steady-state latency using the Envoy connection reuse metrics.

**health_check_latency_skew** — External health check systems (load balancers, CDNs, uptime monitors) typically hit lightweight endpoints (/healthz) that respond in single-digit milliseconds, pulling the p50 and average latency artificially low. Filter health check requests by path or user-agent for an accurate application latency measurement.

**backend_retry_inflation** — Istio retry policies cause the gateway to retry failed upstream requests, which inflates the observed request duration (the duration includes all retry attempts). A single request with 3 retries at 500ms each shows 1500ms duration. Check the response flags for UF or 5xx to identify retry-inflated durations.

**gateway_scaling_event** — When the HPA scales the ingress gateway deployment, new pods go through a warm-up period where the Envoy configuration is loaded and connections are established. Requests hitting newly added pods may show higher latency for the first 30–60 seconds. Correlate latency spikes with HPA scaling events from kube:events.

**geographic_client_variance** — Latency measured at the gateway includes network round-trip time from the client to the cluster ingress. Clients in geographically distant regions contribute higher latency that is not caused by the gateway or backend services. Use client IP geolocation to segment latency by region.

## References

- [Istio — Envoy Access Logging](https://istio.io/latest/docs/tasks/observability/logs/access-log/)
- [Istio — Ingress Gateways](https://istio.io/latest/docs/tasks/traffic-management/ingress/ingress-control/)
- [Envoy — Access Log Configuration](https://www.envoyproxy.io/docs/envoy/latest/configuration/observability/access_log/usage)
- [Splunk OpenTelemetry Collector — Prometheus Receiver](https://docs.splunk.com/observability/en/gdi/opentelemetry/components/prometheus-receiver.html)
- [Splunk perc Command Reference](https://docs.splunk.com/Documentation/Splunk/latest/SearchReference/Eventstats)
