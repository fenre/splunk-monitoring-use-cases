<!-- AUTO-GENERATED from UC-3.6.6.json — DO NOT EDIT -->

---
id: "3.6.6"
title: "Ingress Traffic Volume Trending"
status: "verified"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-3.6.6 · Ingress Traffic Volume Trending

## Description

Tracks daily ingress request volume across NGINX Ingress Controller and Istio Gateway access logs, computing 7-day moving average RPS and deviation percentages to surface organic traffic growth, campaign-driven surges, and unexpected drops — then breaks down by **host header** and **status class** to identify which services drive volume changes and whether growth brings proportional error increases.

## Value

Ingress controllers are the front door to the cluster — they absorb every external request before routing to backend services. A steadily rising daily RPS that goes unnoticed leads to controller CPU saturation, connection pool exhaustion, and latency spikes that affect all hosted services simultaneously. Conversely, a sudden traffic drop may indicate DNS failures, CDN misrouting, or upstream provider outages. Trending ingress volume daily with a 7-day SMA gives capacity planners the data to scale horizontally before saturation, marketing teams the visibility into campaign traffic, and SREs the anomaly detection baseline to distinguish organic growth from attacks.

## Implementation

Collect NGINX Ingress Controller and/or Istio Gateway access logs into index=containers. Build two search variants: daily RPS trend with 7-day SMA and SURGE/DROP classification, and per-host/status-class breakdown with latency and byte volume. Alert when daily RPS exceeds 2× the 7-day SMA or drops below 30% of the SMA.

## Detailed Implementation

Prerequisites
• **NGINX Ingress Controller** 1.5+ deployed in the cluster (or **Istio Ingress Gateway** 1.14+ for service mesh environments). NGINX Ingress is the most common Kubernetes ingress controller, handling external HTTP/HTTPS traffic and routing to backend **Services** based on **Ingress** resource rules.
• **Access log format**: configure the **NGINX Ingress Controller** to emit **JSON-format** **access logs** by setting the `log-format-upstream` **ConfigMap** key. JSON logs provide structured fields (method, uri, status, request_length, **bytes_sent**, **request_time**, upstream_response_time) without regex-based field extraction. For Istio, enable the **Envoy access log** via the **Telemetry API** with JSON format.
• **Splunk Connect for Kubernetes** or the **OTel filelog receiver** configured to collect access logs from ingress controller pods and index them as **`sourcetype=nginx:ingress:access`** or **`sourcetype=istio:accesslog`**.
• **Splunk HEC** token for **`index=containers`** with appropriate sourcetype routing.
• At least **14 days** of historical access log data for meaningful 7-day SMA trending; **30 days** is ideal. Set **index retention** to at least 90 days for capacity planning analysis.
• **License estimate**: access log volume is directly proportional to request volume. At 500 bytes per log line, 1 million requests/day generates approximately **500 MB/day** of log data. For high-traffic clusters, consider using **metrics** (from the **Prometheus receiver**) instead of raw access logs to reduce license consumption — the metrics variant provides RPS and error rates without per-request log storage.
• Splunk RBAC: users running ingress trend searches need **`srchIndexesAllowed`** including `containers`; assign via a **`platform_analyst`** role.

Step 1 — Configure data collection
(1) **NGINX Ingress Controller JSON access log**: configure the ingress controller's **ConfigMap** to emit structured JSON logs:
```
apiVersion: v1
kind: ConfigMap
metadata:
  name: ingress-nginx-controller
  namespace: ingress-nginx
data:
  log-format-escape-json: "true"
  log-format-upstream: '{"time":"$time_iso8601","remote_addr":"$remote_addr","host":"$host","request_method":"$request_method","request_uri":"$request_uri","status":$status,"body_bytes_sent":$body_bytes_sent,"request_time":$request_time,"upstream_response_time":"$upstream_response_time","ingress_name":"$ingress_name","service_name":"$service_name","service_port":"$service_port"}'
```

This format ensures every field is immediately available as a JSON key in Splunk without additional field extraction rules. The key fields for trending:
— **`host`** (the **Host header** — identifies which virtual host/service receives the request)
— **`status`** (HTTP status code — for error rate calculation)
— **`request_time`** (total request duration in seconds — for latency trending)
— **`body_bytes_sent`** (response size — for bandwidth trending)
— **`ingress_name`** and **`service_name`** (Kubernetes resource names — for per-service drill-down)

(2) **Istio Ingress Gateway** access log: enable via the Telemetry API or MeshConfig:
— Set `meshConfig.accessLogFile` to `/dev/stdout` and `meshConfig.accessLogEncoding` to `JSON`
— Key **Envoy access log** fields: `authority` (equivalent to Host header), `response_code`, `duration`, `bytes_sent`, `upstream_cluster`, `response_flags`

(3) **Prometheus metrics** (alternative for high-volume clusters): scrape the NGINX Ingress Controller's `/metrics` endpoint with the OTel Collector **Prometheus receiver**. Key metrics:
— `nginx_ingress_controller_requests` (counter, labeled by ingress, host, status, method) — provides request counts without per-request log storage
— `nginx_ingress_controller_request_duration_seconds_bucket` (histogram) — for **latency percentiles**
— `nginx_ingress_controller_response_size` (histogram) — for bandwidth trending
For Istio, use `istio_requests_total` and `istio_request_duration_milliseconds_bucket` from the gateway pods.

(4) **Ingress controller pod status**: collect **`sourcetype=kube:pod:status`** for the ingress controller pods. This provides replica count, resource utilization, and readiness state, which are essential for correlating traffic volume with controller capacity. A traffic surge that coincides with a controller pod restart indicates the controller is being overwhelmed.

(5) **Geographic and **CDN** context** (optional): if ingress traffic passes through a **CDN** or **load balancer** before reaching the Kubernetes ingress controller, the `X-Forwarded-For` and `X-Real-IP` headers provide the original client IP. Configure the NGINX Ingress Controller to trust the upstream proxy via the `use-forwarded-headers` ConfigMap setting.

Step 2 — Create the search and alert
The primary SPL computes daily **request volume** and **RPS** from access logs, then applies a **7-day SMA** to smooth daily variance. The **`trend_flag`** classification:
— **SURGE**: daily RPS exceeds **2× the 7-day SMA** AND exceeds **10 RPS** (absolute floor for small clusters). May indicate a traffic spike from a marketing campaign, viral event, or DDoS attack.
— **DROP**: daily RPS drops below **30% of the SMA** when the SMA is above **5 RPS**. May indicate DNS failures, CDN misrouting, or upstream provider outages.
— **NORMAL**: within expected bounds.

The breakdown variant groups traffic by **host header** (virtual host) and **status class** (2xx, 3xx, 4xx, 5xx) to identify which services drive volume changes. Key computed fields:
— **avg_latency** and **p95_latency** — latency correlation with volume (rising latency during traffic growth indicates capacity saturation)
— **total_gb** — bandwidth consumption per host (useful for cost allocation and CDN planning)
— **sparkline** — inline trend visualization per host+status combination

Schedule the daily RPS trend over **`-30d`** daily at **07:00**. Alert on SURGE (immediate Slack notification) or DROP (immediate investigation trigger). Schedule the breakdown search daily for the **capacity planning dashboard**.

Step 3 — Validate
(a) Verify access log collection: `index=containers sourcetype="nginx:ingress:access" earliest=-1h | stats count`. Should return a count proportional to your ingress traffic volume.
(b) Verify field extraction: `index=containers sourcetype="nginx:ingress:access" earliest=-5m | table host status request_time bytes_sent ingress_name service_name`. All fields should populate (not null).
(c) Generate test traffic: `for i in $(seq 1 100); do curl -s -o /dev/null https://<ingress-host>/healthz; done`. Verify the 100 requests appear in the access log within 1 minute.
(d) Verify **RPS calculation**: manually compute expected RPS from known traffic. For example, 86,400 requests/day = 1.0 RPS. Compare with the search output.
(e) Verify **host breakdown**: `index=containers sourcetype="nginx:ingress:access" earliest=-1h | stats count by host | sort -count`. The top hosts should match your known high-traffic services.
(f) Confirm **status class distribution**: the majority of requests should be **2xx** for a healthy cluster. A high proportion of 4xx may indicate client errors or misconfigured routes; 5xx indicates upstream service failures.

Step 4 — Operationalize dashboards and runbooks
• Row A: **single-value tiles** — today's total requests, current daily RPS, 7-day SMA RPS, deviation %, trend flag (SURGE=red, DROP=amber, NORMAL=green), error rate %.
• Row B: **line chart** of daily RPS with **7-day SMA** overlay over 30 days — the primary capacity planning signal. Add a secondary Y-axis for daily 5xx error rate.
• Row C: **stacked area chart** of daily requests by host header over 14 days — shows which services contribute most to total volume and whether growth is concentrated or distributed.
• Row D: **host+status breakdown table** — host_header, status_class, total_requests, avg_daily, peak_daily, overall_avg_latency, overall_p95_latency, total_gb, sparkline. Sorted by total requests.
• **Alerting**: SURGE flag → Slack `#platform-ops` (immediate investigation); DROP flag → Slack `#platform-ops` + email to on-call (potential outage); daily RPS exceeds **capacity threshold** (e.g., 80% of tested controller max RPS) → PagerDuty P3 (scale ingress controllers); 5xx error rate > 5% → PagerDuty P2.
• **Runbook** (owner: platform engineering): (1) for SURGE: check if traffic is legitimate (marketing campaign) or an attack (DDoS) by examining client IP distribution and request patterns, (2) for DROP: check DNS resolution, CDN health, and upstream provider status, (3) for latency increase: check ingress controller CPU/memory and backend pod health, (4) for error rate increase: check upstream service health and ingress annotation configuration.

Step 5 — Visualization, alert design, and troubleshooting
• **Visualization**: use a **heatmap** showing hourly request volume over 30 days (X=hour, Y=day) to reveal traffic patterns — daily cycles, weekend dips, campaign spikes. Pair with a **top-N bar chart** showing the top 10 hosts by request volume.
• **Alert design**: include `daily_rps`, `sma_7d_rps`, `deviation_pct`, `trend_flag`, `daily_5xx`, `error_rate`, `active_hosts`, and `unique_clients` in the alert payload. For breakdown alerts include `host_header`, `peak_daily`, and `overall_p95_latency`.
• **Access log volume too high for license** — switch to the metrics-based approach using `nginx_ingress_controller_requests` counters instead of per-request access logs. Metrics provide the same RPS and error rate data at a fraction of the license cost.
• **Host header is always "unknown"** — the ingress controller is not extracting the Host header. Verify the log format includes `$host` and that the ingress resource has the correct `host` field in its rules.
• **RPS appears low despite high request count** — the `daily_rps` calculation divides by 86,400 (seconds in a day). If your traffic is concentrated in business hours (e.g., 8 hours/day), the effective RPS during peak hours is 3× the daily average. Add a **peak-hour RPS** calculation.
• **Trend SMA is flat but traffic is growing** — the 7-day SMA smooths gradual growth to near zero deviation. Add a **30-day linear regression** (`predict` command) to detect slow growth trends that the SMA does not surface.

## SPL

```spl
`comment("--- Ingress Traffic Volume — Daily RPS Trend with 7-Day SMA ---")`
index=containers sourcetype IN ("nginx:ingress:access", "istio:accesslog")
| eval ingress_class=coalesce(ingress_class, ingress, upstream_cluster, "default")
| eval host_header=coalesce(host, server_name, authority, "unknown")
| eval status_class=case(
    status >= 200 AND status < 300, "2xx",
    status >= 300 AND status < 400, "3xx",
    status >= 400 AND status < 500, "4xx",
    status >= 500, "5xx",
    1=1, "other")
| bin _time span=1d
| stats count as daily_requests,
    sum(eval(if(status_class="5xx",1,0))) as daily_5xx,
    dc(host_header) as active_hosts,
    dc(client_ip) as unique_clients,
    avg(request_time) as avg_latency_sec
    by _time
| eval daily_rps=round(daily_requests / 86400, 2)
| eval error_rate=round(100 * daily_5xx / max(daily_requests, 1), 2)
| trendline sma7(daily_rps) as sma_7d_rps
| eval deviation_pct=round(100 * (daily_rps - sma_7d_rps) / max(sma_7d_rps, 0.01), 1)
| eval trend_flag=case(
    daily_rps > sma_7d_rps * 2 AND daily_rps > 10, "SURGE",
    daily_rps < sma_7d_rps * 0.3 AND sma_7d_rps > 5, "DROP",
    1=1, "NORMAL")
| table _time daily_requests daily_rps sma_7d_rps deviation_pct daily_5xx error_rate active_hosts unique_clients avg_latency_sec trend_flag

`comment("--- Ingress Traffic Breakdown by Host and Status Class ---")`
index=containers sourcetype IN ("nginx:ingress:access", "istio:accesslog")
| eval host_header=coalesce(host, server_name, authority, "unknown")
| eval status_class=case(
    status >= 200 AND status < 300, "2xx",
    status >= 300 AND status < 400, "3xx",
    status >= 400 AND status < 500, "4xx",
    status >= 500, "5xx",
    1=1, "other")
| bin _time span=1d
| stats count as daily_count,
    avg(request_time) as avg_latency,
    perc95(request_time) as p95_latency,
    sum(bytes_sent) as daily_bytes
    by host_header, status_class, _time
| stats sum(daily_count) as total_requests,
    avg(daily_count) as avg_daily,
    max(daily_count) as peak_daily,
    avg(avg_latency) as overall_avg_latency,
    avg(p95_latency) as overall_p95_latency,
    sum(daily_bytes) as total_bytes,
    sparkline(sum(daily_count)) as trend
    by host_header, status_class
| eval total_gb=round(total_bytes / 1073741824, 2)
| sort -total_requests
| head 50
| table host_header status_class total_requests avg_daily peak_daily overall_avg_latency overall_p95_latency total_gb trend

`comment("--- Hourly Peak RPS Calculation — Capacity Planning ---")`
index=containers sourcetype IN ("nginx:ingress:access", "istio:accesslog")
| eval host_header=coalesce(host, server_name, authority, "unknown")
| bin _time span=1h
| stats count as hourly_requests by _time, host_header
| eval hourly_rps=round(hourly_requests / 3600, 2)
| stats max(hourly_rps) as peak_rps,
    avg(hourly_rps) as avg_rps,
    perc95(hourly_rps) as p95_rps
    by host_header
| eval capacity_ratio=round(peak_rps / max(avg_rps, 0.01), 1)
| sort -peak_rps
| head 20
| table host_header peak_rps avg_rps p95_rps capacity_ratio
```

## Visualization

Line chart of daily RPS with 7-day SMA overlay, stacked area by host header, status class heatmap, single-value tiles (trend direction, deviation %, peak RPS, error rate), per-host sparkline table.

## Known False Positives

**health_check_inflation** — Kubernetes liveness and readiness probes, plus external health check systems (load balancers, CDNs, uptime monitors), generate a steady stream of requests that inflate the daily request count without representing real user traffic. These typically hit a fixed path like /healthz. Filter by URI or user-agent to separate synthetic health checks from user traffic.

**bot_and_crawler_traffic** — Search engine crawlers, vulnerability scanners, and automated bots can represent 10–40% of total ingress traffic depending on the application. A spike in bot traffic appears as a legitimate traffic surge. Use user-agent classification and rate-per-client-IP analysis to separate bot traffic from human traffic.

**cdn_cache_bypass** — When a CDN cache is invalidated or bypassed (e.g., cache-busting query parameters, Vary header changes), all requests that were previously served from cache suddenly hit the origin ingress controller. This appears as a traffic surge but represents the same user volume with changed caching behavior. Correlate with CDN cache hit ratio metrics.

**timezone_aggregation_artifact** — Daily aggregation bins are aligned to UTC by default. For applications with traffic concentrated in a specific timezone, a UTC day boundary splits the peak traffic period across two daily buckets, making both days appear to have moderate traffic rather than one day with a clear peak. Use `| eval _time=relative_time(_time, "@d")` with timezone adjustment if needed.

**ingress_controller_restart** — When an ingress controller pod restarts, in-flight connections are dropped and clients retry, creating a brief spike in request count immediately after the restart. This appears as a traffic surge but is actually connection recovery. Correlate with ingress controller pod restart events from UC-3.6.1.

## References

- [NGINX Ingress Controller — Monitoring](https://kubernetes.github.io/ingress-nginx/user-guide/monitoring/)
- [NGINX Ingress Controller — Log Format](https://kubernetes.github.io/ingress-nginx/user-guide/nginx-configuration/log-format/)
- [Istio — Envoy Access Logging](https://istio.io/latest/docs/tasks/observability/logs/access-log/)
- [Splunk Connect for Kubernetes](https://github.com/splunk/splunk-connect-for-kubernetes)
- [Splunk trendline Command Reference](https://docs.splunk.com/Documentation/Splunk/latest/SearchReference/Trendline)
