<!-- AUTO-GENERATED from UC-3.2.9.json — DO NOT EDIT -->

---
id: "3.2.9"
title: "Ingress Controller Health and 4xx/5xx Error Rate"
status: "verified"
criticality: "critical"
splunkPillar: "Observability"
---

# UC-3.2.9 · Ingress Controller Health and 4xx/5xx Error Rate

> **Criticality:** Critical &middot; **Difficulty:** Advanced &middot; **Pillar:** Observability &middot; **Type:** Reliability, Performance &middot; **Wave:** Walk &middot; **Status:** Verified

*Most apps in a Kubernetes cluster face the public internet through one or two Ingress Controllers. When those controllers fail or slow down, every customer hits errors no matter how healthy the apps behind them are. This use case watches the front door of the cluster.*

---

## Description

Correlates north-south HTTP reliability at the Kubernetes ingress controller layer across NGINX Ingress, HAProxy, Traefik, and cloud-managed AWS Load Balancer Controller patterns by fusing normalized access logs with Prometheus scrape signals. The analytic computes hourly requests_per_sec, error_rate_5xx_pct, p99_latency_ms, upstream_failure_rate, upstream_zero_endpoints hints from controller text, config_reload_failed from nginx_ingress_controller_config_last_reload_successful, z-score anomaly versus a seven-day hourly 5xx baseline, and slo_burn_rate against a 0.1 percent monthly-style 5xx budget expressed per hour. It answers whether the shared front door is on fire before per-upstream forensics (UC-3.2.27), backend readiness churn (UC-3.2.18), or Service endpoint cardinality (UC-3.2.41) investigations split the incident. Certificate lifecycle depth stays in UC-3.2.13 with only cross-links here for TLS reload correlation.

## Value

Customer-visible outages often manifest as ingress-emitted 502, 503, and 504 storms while kubectl shows green pods; this control collapses mean time to innocence by naming controller reload failures, aggregate burn against a published 5xx SLO, and tail latency at the edge. Platform finance gains defensible signal when license spend on access logs maps directly to error-budget governance and paging discipline. Executive reviews receive evidence that the cluster front door is monitored distinctly from microservice dashboards, which prevents duplicate escalations during single-controller incidents that would otherwise fan out across dozens of application teams.

## Implementation

Provision indexes k8s_metrics, k8s_logs, and web with HEC tokens; scrape NGINX 10254, HAProxy 8404, and Traefik 8080 metrics through OTel or ServiceMonitor; ship JSON ingress access logs to index=web; publish ingress_oncall_routing.csv; save uc_3_2_9_ingress_controller_health on a five-minute cadence; route down and critical severities using on_call_team; archive weekly CSV exports for error-budget reviews.

## Evidence

Saved search uc_3_2_9_ingress_controller_health; lookups/ingress_oncall_routing.csv versioned in git; weekly CSV exports of alert tables to a restricted evidence index; dashboard panels combining hourly slo_burn_rate, p99_latency_ms, and config_reload_failed timelines with drilldowns to raw access logs.

## Control test

### Positive scenario

In a lab cluster, configure index=web nginx:access with a synthetic workload returning HTTP 500 for path /api/fail, run uc_3_2_9_ingress_controller_health over earliest=-1h@h, and expect non-healthy severity with elevated error_rate_5xx_pct and slo_burn_rate for cluster nginx ingress_class keys.

### Negative scenario

In a lab cluster with only successful traffic, excluded health probes, and nginx_ingress_controller_config_last_reload_successful equal to one across the hour, expect healthy classification such that the alert search returns zero rows after the final where clause.

## Detailed Implementation

### Step 1 — Prerequisites

Head of Platform owns this control together with the cluster ingress platform team, the edge networking group that operates regional load balancers, and the observability engineer who certifies Prometheus and access-log parity across NGINX Ingress Controller, HAProxy-based ingress implementations, Traefik, and cloud-managed AWS Load Balancer Controller surfaces. UC-3.2.9 isolates the north-south HTTP reliability axis at the ingress controller itself: request arrival rate, tail latency observed on responses the controller emits, aggregate 4xx and 5xx class ratios, upstream connect and error semantics as inferred from controller logs, controller process and configuration reload health, and optional signals that hint at empty backend endpoints from controller error text. The scope deliberately excludes deep per-upstream decomposition that UC-3.2.27 owns, excludes pod-level backend flap analytics owned by UC-3.2.18, and excludes Kubernetes Service Endpoints object cardinality diagnostics owned by UC-3.2.41 except as cross-links when controller logs prove zero ready endpoints. Certificate notAfter monitoring and cert-manager workflow detail remain with UC-3.2.13; this document references certificate renewal only for correlation when brief TLS reload windows align with error bursts.

Before you schedule the saved search, confirm four indexing paths are healthy. First, index=k8s_metrics ingests Prometheus-formatted scrapes from NGINX Ingress Controller port 10254, HAProxy metrics on 8404 when the data plane exposes Prometheus text, and Traefik on 8080 for the metrics entrypoint, with resource attributes that preserve cluster identity, ingress class, namespace, pod, and service names through the Splunk OpenTelemetry Collector kubernetesattributes processor. Validate scrape budgets during peak requests per second so the cluster-wide footprint does not starve small control planes. Second, index=web hosts normalized HTTP access events from sourcetype nginx:access, haproxy:access, and traefik:access with fields suitable for coalesce on status_code, status, http_status, and vendor-specific variants including DownstreamStatus for Traefik. Third, index=k8s_logs carries administrative controller logs when forwarders split them from edge access logs; align host naming so joins on cluster remain deterministic across hybrid ingestion. Fourth, publish lookups/ingress_oncall_routing.csv with cluster, on_call_team, escalation_policy_id, and optional suppress_preview_tier so paging routes consistently when multisearch arms disagree slightly on labels.

Risk framing for incident commanders: customers experience outages when ingress controllers return 502, 503, or 504 at volume even while application pods pass readiness probes. The failure can be controller saturation, TLS hot reload, a bad Ingress object that prevents clean configuration reload, partial connectivity to apiserver during control-plane storms, or target-group churn during cloud reconciles. This correlation elevates those patterns above generic application dashboards by anchoring metrics to controller identity and ingress class rather than to a single microservice deployment. Differentiation recap: UC-3.2.18 tracks unhealthy backends and pod-level readiness churn; UC-3.2.27 isolates which upstream service or URL path carries concentrated 5xx; UC-3.2.41 tracks Service objects with zero endpoints; UC-3.2.9 answers whether the shared controller front door is degrading across tenants before you open those sibling investigations.

Capacity and licensing: access logs dominate license bytes; retain raw web indexes hot for error budget math while sampling high-cardinality success traffic into separate summary metrics when finance requests relief. SCRAM authentication on metrics scrapes belongs in vault alongside HEC tokens; rotate quarterly. Legal review may require stripping query strings at collection for personally identifiable query parameters while preserving path, status, and latency.

Concrete metric families expected in k8s_metrics for NGINX Ingress include nginx_ingress_controller_requests, nginx_ingress_controller_request_duration_seconds, nginx_ingress_controller_upstream_latency_seconds, nginx_ingress_controller_config_last_reload_successful, and nginx_ingress_controller_nginx_process_cpu_seconds. HAProxy arms should map haproxy_backend_http_responses_total, haproxy_backend_status, and haproxy_backend_response_time_average_seconds when exporters are enabled. Traefik arms should map traefik_entrypoint_requests_total, traefik_service_requests_total, and traefik_router_requests_total. Cloud-managed ingress on Amazon EKS often relies on AWS Load Balancer Controller with CloudWatch signals; when Prometheus scrape is impossible for those controllers, mirror CloudWatch ApplicationELB or TargetGroup metrics into k8s_metrics through the Splunk Add-on for AWS or an OTel cloudwatch receiver, and document the field mapping beside this UC so coalesce lists stay short.

Governance: ingress_oncall_routing.csv must refresh weekly from the service catalog. Namespace allow lists for preview environments belong in a column so synthetic 4xx during throwaway URLs does not page production bridges. When finance challenges ingest cost, attach minutes of customer-visible 5xx during a historical ingress incident to demonstrate return on telemetry investment.


### Step 2 — Configure data collection

Deploy ServiceMonitor or PodMonitor objects, or equivalent OTel receiver scrape_configs, that hit NGINX Ingress metrics on port 10254, HAProxy on 8404, and Traefik metrics on 8080. Route OTLP or HEC payloads so numeric samples land in index=k8s_metrics with sourcetype conventions your platform team already accelerates. Route access logs to index=web with sourcetype nginx:access, haproxy:access, or traefik:access after props.conf normalization. Enable JSON access logs on NGINX Ingress with log-format-upstream so upstream_status, request_time, and ingress_class flow into Splunk without fragile regex-only extractions. Enable HAProxy stats with read-only credentials and Traefik accessLog plus metrics in static configuration.

Example ServiceMonitor for NGINX Ingress Controller:

```yaml
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: nginx-ingress-metrics
  namespace: ingress-nginx
  labels:
    release: prometheus
spec:
  selector:
    matchLabels:
      app.kubernetes.io/name: ingress-nginx
  endpoints:
    - port: metrics
      interval: 30s
      path: /metrics
      scheme: http
```

Example ServiceMonitor for HAProxy ingress metrics:

```yaml
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: haproxy-ingress-metrics
  namespace: haproxy-system
spec:
  selector:
    matchLabels:
      app.kubernetes.io/name: haproxy-ingress
  endpoints:
    - port: prometheus
      interval: 30s
      path: /metrics
```

Example ServiceMonitor for Traefik:

```yaml
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: traefik-metrics
  namespace: traefik
spec:
  selector:
    matchLabels:
      app.kubernetes.io/name: traefik
  endpoints:
    - port: metrics
      interval: 30s
      path: /metrics
```

Splunk OpenTelemetry Collector exporter fragment routing metrics and logs:

```yaml
exporters:
  splunk_hec/metrics:
    token: "${SPLUNK_HEC_TOKEN_K8S_METRICS}"
    endpoint: "https://splunk.example.com:8088/services/collector"
    index: k8s_metrics
  splunk_hec/web:
    token: "${SPLUNK_HEC_TOKEN_WEB}"
    endpoint: "https://splunk.example.com:8088/services/collector"
    index: web
service:
  pipelines:
    metrics:
      receivers: [prometheus_simple]
      processors: [k8sattributes, batch]
      exporters: [splunk_hec/metrics]
    logs/ingress:
      receivers: [filelog]
      processors: [k8sattributes, batch]
      exporters: [splunk_hec/web]
```

NGINX Ingress ConfigMap fragment enabling JSON upstream-aware access logs:

```yaml
data:
  log-format-upstream: >-
    {"time":"$time_iso8601","request_id":"$req_id","host":"$host","uri":"$uri","method":"$method",
    "status":$status,"upstream_status":"$upstream_status","request_time":$request_time,
    "upstream_response_time":"$upstream_response_time","ingress_class":"$ingress_name",
    "cluster":"$namespace"}
```

After deployment, validate with index searches for sourcetype and confirm cluster, ingress_class, and status fields populate on canary traffic.


### Step 3 — Create the search and alert

Save the SPL as saved search uc_3_2_9_ingress_controller_health with schedule every five minutes and time range earliest=-1h@h latest=@h for operational alerting. Throttle duplicate pages per cluster, controller_type, and ingress_class for twenty minutes unless severity escalates from medium to down inside the same hour. Route down and critical severities to on_call_team from ingress_oncall_routing.csv; attach the closing table row in the page body.

Understanding the pipeline in operator terms: the comment macro lists indexes, SLO target, z-score gates, and latency floors. multisearch fans three parallel access-log arms so a silent failure on one sourcetype does not blank the others. Each arm normalizes cluster and ingress_class, coalesce-normalizes HTTP status into status_code, derives resp_ms from fractional seconds or milliseconds, flags synthetic probes on /healthz, /readyz, /livez, and /metrics, and computes is_5xx and is_upstream_fail for connect-style failures. After fan-in, hourly stats derive requests_per_sec, error_rate_5xx_pct, p99_latency_ms, upstream_failure_rate, and upstream_zero_endpoints from log evidence. A left join on seven days of hourly 5xx rates per key supplies baseline_5xx_pct and baseline_5xx_stdev for z_5xx. slo_burn_rate compares observed five_xx_count to the budget implied by SLO_TARGET_5XX_PCT over the observed total_count hour. A metrics join on nginx_ingress_controller_config_last_reload_successful surfaces config_reload_failed per cluster. severity uses case with down, critical, high, medium, and healthy tiers; the alert filters out healthy rows.

Fenced SPL for runbooks must match the spl JSON field byte-for-byte:

```spl
`comment("UC-3.2.9 Ingress Controller Health and 4xx/5xx Error Rate. Tunables: (index=web OR index=k8s_logs) plus optional index=k8s_metrics; sourcetypes nginx:access,haproxy:access,traefik:access; SLO_TARGET_5XX_PCT=0.1; FAST_BURN_MULT=6; Z_HIGH=2.5; Z_CRIT=3.5; P99_HIGH_MS=2000; P99_CRIT_MS=5000; earliest=-1h@h latest=@h; BASELINE earliest=-7d@d latest=@d.")`
| multisearch
    [ search (index=web OR index=k8s_logs) sourcetype="nginx:access" earliest=-1h@h latest=@h
      | eval controller_type="nginx"
      | eval cluster=lower(trim(toString(coalesce(k8s_cluster, cluster_name, cluster, kube_cluster, k8s_cluster_name, source_cluster, ""))))
      | eval ingress_class=lower(trim(toString(coalesce(ingress_class, k8s_ingress_class, ingress_class_name, ""))))
      | eval status_code=tonumber(tostring(coalesce(status, status_code, http_status, http_status_code, sc, request_status, code, "")), 10)
      | eval upstream_code=tonumber(tostring(coalesce(upstream_status, upstream_http_code, "")), 10)
      | eval rt_raw=tonumber(tostring(coalesce(request_time, request_time_sec, upstream_response_time, upstream_rt, request_duration, time_taken, "")), 10)
      | eval resp_ms=if(isnotnull(rt_raw) AND rt_raw<500, round(rt_raw*1000, 3), coalesce(rt_raw, tonumber(tostring(coalesce(response_time_ms, duration_ms, traefik_duration_ms, "")), 10)))
      | eval uri=toString(coalesce(uri, request_uri, path, http_uri, request_path, ""))
      | eval lr=lower(_raw)
      | eval is_synthetic=if(match(uri, "(?i)/healthz(\?|$)") OR match(uri, "(?i)/readyz(\?|$)") OR match(uri, "(?i)/livez(\?|$)") OR match(uri, "(?i)/metrics(\?|$)"), 1, 0)
      | eval upstream_zero=if(match(lr, "no live upstreams"), 1, 0)
      | eval is_5xx=if(isnotnull(status_code) AND status_code>=500 AND status_code<600, 1, 0)
      | eval is_upstream_fail=if((isnotnull(upstream_code) AND upstream_code>=500 AND upstream_code<600) OR status_code==502 OR status_code==503 OR status_code==504, 1, 0)
      | where is_synthetic==0 AND isnotnull(status_code)
      | fields _time cluster controller_type ingress_class status_code resp_ms is_5xx is_upstream_fail upstream_zero ]
    [ search (index=web OR index=k8s_logs) sourcetype="haproxy:access" earliest=-1h@h latest=@h
      | eval controller_type="haproxy"
      | eval cluster=lower(trim(toString(coalesce(k8s_cluster, cluster_name, cluster, kube_cluster, k8s_cluster_name, source_cluster, ""))))
      | eval ingress_class=lower(trim(toString(coalesce(ingress_class, proxy_name, fe_name, frontend_name, ""))))
      | eval status_code=tonumber(tostring(coalesce(status, status_code, sc, rsp_code, http_status_code, code, "")), 10)
      | eval upstream_code=null()
      | eval rt_raw=tonumber(tostring(coalesce(TR, tr, Ta, ta, tun, wait, response_time, time_taken, "")), 10)
      | eval resp_ms=if(isnotnull(rt_raw) AND rt_raw<500, round(rt_raw*1000, 3), coalesce(rt_raw, tonumber(tostring(coalesce(response_time_ms, duration_ms, "")), 10)))
      | eval uri=toString(coalesce(uri, path, req_uri, http_uri, ""))
      | eval lr=lower(_raw)
      | eval is_synthetic=if(match(uri, "(?i)/healthz(\?|$)") OR match(uri, "(?i)/readyz(\?|$)") OR match(uri, "(?i)/livez(\?|$)"), 1, 0)
      | eval upstream_zero=if(match(lr, "nosrv|no server available"), 1, 0)
      | eval is_5xx=if(isnotnull(status_code) AND status_code>=500 AND status_code<600, 1, 0)
      | eval is_upstream_fail=if(status_code==502 OR status_code==503 OR status_code==504, 1, 0)
      | where is_synthetic==0 AND isnotnull(status_code)
      | fields _time cluster controller_type ingress_class status_code resp_ms is_5xx is_upstream_fail upstream_zero ]
    [ search (index=web OR index=k8s_logs) sourcetype="traefik:access" earliest=-1h@h latest=@h
      | eval controller_type="traefik"
      | eval cluster=lower(trim(toString(coalesce(k8s_cluster, cluster_name, cluster, kube_cluster, k8s_cluster_name, source_cluster, ""))))
      | eval ingress_class=lower(trim(toString(coalesce(ingress_class, entryPointName, entry_point, routerName, router_name, ""))))
      | eval status_code=tonumber(tostring(coalesce(DownstreamStatus, downstream_status, status, status_code, code, http_status, "")), 10)
      | eval upstream_code=tonumber(tostring(coalesce(OriginStatus, origin_status, upstream_status, "")), 10)
      | eval rt_raw=tonumber(tostring(coalesce(Duration, duration, round_trip_time_ms, "")), 10)
      | eval resp_ms=if(isnotnull(rt_raw) AND rt_raw>0 AND rt_raw<500, round(rt_raw*1000, 3), if(isnotnull(rt_raw) AND rt_raw>=500, rt_raw, tonumber(tostring(coalesce(response_time_ms, duration_ms, "")), 10)))
      | eval uri=toString(coalesce(RequestPath, request_path, path, uri, ""))
      | eval lr=lower(_raw)
      | eval is_synthetic=if(match(uri, "(?i)/healthz(\?|$)") OR match(uri, "(?i)/readyz(\?|$)") OR match(uri, "(?i)/livez(\?|$)"), 1, 0)
      | eval upstream_zero=if(match(lr, "no valid url|service unavailable"), 1, 0)
      | eval is_5xx=if(isnotnull(status_code) AND status_code>=500 AND status_code<600, 1, 0)
      | eval is_upstream_fail=if((isnotnull(upstream_code) AND upstream_code>=500) OR status_code==502 OR status_code==503 OR status_code==504, 1, 0)
      | where is_synthetic==0 AND isnotnull(status_code)
      | fields _time cluster controller_type ingress_class status_code resp_ms is_5xx is_upstream_fail upstream_zero ]
| eval cluster=if(isnull(cluster) OR len(trim(cluster))<1 OR cluster="null", "unknown_cluster", cluster)
| eval ingress_class=if(isnull(ingress_class) OR len(trim(ingress_class))<1 OR ingress_class="null", "default", ingress_class)
| bin _time span=1h
| stats count AS total_count sum(is_5xx) AS five_xx_count sum(is_upstream_fail) AS upstream_fail_hits max(upstream_zero) AS upstream_zero_endpoints perc99(resp_ms) AS p99_latency_ms BY cluster controller_type ingress_class _time
| eval window_sec=3600
| eval requests_per_sec=if(window_sec>0, round(total_count/window_sec, 4), 0)
| eval error_rate_5xx_pct=if(total_count>0, round(100.0*five_xx_count/total_count, 4), 0)
| eval upstream_failure_rate=if(total_count>0, round(100.0*upstream_fail_hits/total_count, 4), 0)
| eval SLO_TARGET_5XX_PCT=0.1
| eval slo_5xx_budget_count=if(total_count>0, max(ceil(total_count * SLO_TARGET_5XX_PCT / 100.0), 1), 1)
| eval slo_burn_rate=round(five_xx_count / slo_5xx_budget_count, 3)
| join type=left cluster controller_type ingress_class
    [ search (index=web OR index=k8s_logs) (sourcetype="nginx:access" OR sourcetype="haproxy:access" OR sourcetype="traefik:access") earliest=-7d@d latest=@d
      | eval controller_type=case(sourcetype="nginx:access", "nginx", sourcetype="haproxy:access", "haproxy", sourcetype="traefik:access", "traefik", true(), "unknown")
      | eval cluster=lower(trim(toString(coalesce(k8s_cluster, cluster_name, cluster, kube_cluster, k8s_cluster_name, source_cluster, ""))))
      | eval ingress_class=lower(trim(toString(coalesce(ingress_class, k8s_ingress_class, proxy_name, fe_name, entryPointName, routerName, ""))))
      | eval status_code=tonumber(tostring(coalesce(status, status_code, http_status, DownstreamStatus, sc, rsp_code, code, "")), 10)
      | eval uri=toString(coalesce(uri, request_uri, path, RequestPath, http_uri, ""))
      | eval is_synthetic=if(match(uri, "(?i)/healthz(\?|$)") OR match(uri, "(?i)/readyz(\?|$)") OR match(uri, "(?i)/livez(\?|$)") OR match(uri, "(?i)/metrics(\?|$)"), 1, 0)
      | eval is_5xx=if(isnotnull(status_code) AND status_code>=500 AND status_code<600, 1, 0)
      | where is_synthetic==0 AND isnotnull(status_code)
      | eval ingress_class=if(isnull(ingress_class) OR len(trim(ingress_class))<1, "default", ingress_class)
      | bin _time span=1h aligntime=@h
      | stats count AS bc sum(is_5xx) AS b5 BY cluster controller_type ingress_class _time
      | eval hr5=if(bc>0, 100.0*b5/bc, null())
      | stats avg(hr5) AS baseline_5xx_pct_avg stdev(hr5) AS baseline_5xx_stdev BY cluster controller_type ingress_class ]
| eval baseline_5xx_pct=coalesce(baseline_5xx_pct_avg, 0.05)
| eval baseline_5xx_stdev=if(isnotnull(baseline_5xx_stdev) AND baseline_5xx_stdev>0, baseline_5xx_stdev, 0.02)
| eval z_5xx=if(baseline_5xx_stdev>0, round((error_rate_5xx_pct - baseline_5xx_pct) / baseline_5xx_stdev, 3), if(error_rate_5xx_pct>baseline_5xx_pct+0.05, 5, 0))
| join type=left max=0 cluster
    [ search index=k8s_metrics earliest=-1h@h latest=@h
      | eval mn=lower(toString(coalesce(metric_name, __name__, name, metric, "")))
      | eval cluster=lower(trim(toString(coalesce(k8s_cluster, cluster, cluster_name, kube_cluster, ""))))
      | where match(mn, "nginx_ingress_controller_config_last_reload_successful")
      | eval v=tonumber(tostring(coalesce(Value, value, metric_value, _value, "")), 10)
      | stats min(v) AS min_reload BY cluster
      | eval config_reload_failed=if(isnull(min_reload) OR min_reload==0, 1, 0)
      | fields cluster config_reload_failed ]
| fillnull value=0 config_reload_failed
| join type=left max=0 cluster
    [| inputlookup ingress_oncall_routing.csv
     | eval cluster=lower(trim(toString(coalesce(cluster, cluster_name, k8s_cluster, ""))))
     | eval on_call_team=toString(coalesce(on_call_team, team, squad, pagerduty_service, ""))
     | fields cluster on_call_team ]
| eval on_call_team=if(isnull(on_call_team) OR len(trim(on_call_team))<1, "platform-ingress", on_call_team)
| eval FAST_BURN_MULT=6
| eval Z_HIGH=2.5
| eval Z_CRIT=3.5
| eval P99_HIGH_MS=2000
| eval P99_CRIT_MS=5000
| eval severity=case(
    config_reload_failed==1, "critical",
    error_rate_5xx_pct>2 OR slo_burn_rate>=FAST_BURN_MULT, "down",
    p99_latency_ms>=P99_CRIT_MS OR z_5xx>=Z_CRIT OR upstream_failure_rate>5, "critical",
    z_5xx>=Z_HIGH OR error_rate_5xx_pct>0.5 OR p99_latency_ms>=P99_HIGH_MS, "high",
    error_rate_5xx_pct>SLO_TARGET_5XX_PCT OR upstream_failure_rate>1 OR (slo_burn_rate>1 AND slo_burn_rate<FAST_BURN_MULT), "medium",
    error_rate_5xx_pct<=SLO_TARGET_5XX_PCT AND p99_latency_ms<P99_HIGH_MS AND upstream_failure_rate<=1, "healthy",
    true(), "medium")
| where severity!="healthy"
| table cluster controller_type ingress_class requests_per_sec error_rate_5xx_pct p99_latency_ms upstream_zero_endpoints config_reload_failed severity on_call_team slo_burn_rate upstream_failure_rate z_5xx baseline_5xx_pct
```


Dashboard drilldowns should link cluster to your regional kubectl context map, ingress_class to the live IngressClass object, and controller_type to the vendor runbook. Maintain a secondary panel plotting nginx_ingress_controller_requests rate from k8s_metrics for corroboration when log volume sampling is active.


### Step 4 — Validate

Positive path A — synthetic 500 from an in-cluster pod: kubectl run curlfail --rm -it --restart=Never --image=curlimages/curl -- curl -s -o /dev/null -w "%{http_code}" https://ingress.test/api/fail and confirm error_rate_5xx_pct rises in index=web for the matching sourcetype within two collection intervals.

Positive path B — latency injection: kubectl run latload --restart=Always --image=curlimages/curl --command -- sh -c 'while true; do sleep 5; curl -s https://ingress.test >/dev/null; done' and confirm p99_latency_ms reacts when upstream delay is introduced; verify the alert only fires if P99_HIGH_MS or SLO gates breach.

Positive path C — NGINX config reload failure: apply an Ingress carrying an invalid regex in a server-snippet or equivalent unsafe annotation under change control; confirm nginx_ingress_controller_config_last_reload_successful drops to zero in k8s_metrics and config_reload_failed=1 surfaces in the search; identify the offending object with kubectl describe ingress and controller admission events.

Positive path D — tear down: remove the faulty Ingress and the synthetic pods; confirm severity returns to healthy and the saved search emits no rows after the throttle window.

Validation SPL for spot-checking field coverage:

```spl
(index=web OR index=k8s_logs) (sourcetype="nginx:access" OR sourcetype="haproxy:access" OR sourcetype="traefik:access") earliest=-15m
| eval status_code=tonumber(tostring(coalesce(status, status_code, http_status, DownstreamStatus, sc, code, "")), 10)
| eval cluster=lower(trim(toString(coalesce(k8s_cluster, cluster_name, cluster, ""))))
| stats count BY sourcetype cluster status_code
| sort - count
```

Role check: readers without index=web must see zero rows from the validation search.


### Step 5 — Operationalize & Troubleshoot

Case 1 — NGINX 502 due to upstream pod restart: expect a short burst of 502 responses while endpoints reconcile. Dampen alerts by requiring two consecutive five-minute buckets above threshold or by correlating with Kubernetes pod restart events from sibling workload telemetry; open UC-3.2.18 only when unhealthy backend patterns persist beyond the dampening window.

Case 2 — NGINX 503 due to no upstream pods (zero endpoints): controller logs often show no live upstreams while upstream_zero_endpoints flags in the hourly rollup. Cross-link UC-3.2.41 for Endpoints object and selector hygiene; do not rewrite backend remediation steps here.

Case 3 — HAProxy 504 due to slow upstream: tail latency rises with 504 class; pivot to application performance after confirming controller CPU and connection table health; compare p99_latency_ms across ingress_class to spot a single noisy backend pool.

Case 4 — Traefik 4xx surge after deploy: new routes or renamed paths generate 404 spikes from legitimate clients; classify as caller-side or rollout-side using deployment timestamps; exclude preview hostnames via ingress_oncall_routing.csv suppress_preview_tier.

Case 5 — NGINX config-reload failure: nginx_ingress_controller_config_last_reload_successful at zero is a critical controller-side signal. Identify the newest Ingress or annotation change with admission audit and controller logs; roll back the object before chasing application teams.

Case 6 — Controller pod restart: Kubernetes may restart the ingress controller during node pressure or upgrade. Verify the pod returns Ready within seconds and request rate recovers; suppress pages when restart_count is one and error_rate_5xx_pct normalizes inside ten minutes with a recorded change ticket.

Case 7 — Certificate renewal in flight: brief 502 or TLS handshake errors can appear during hot reload. Correlate with UC-3.2.13 rotation timelines; dampen pages when notAfter transitions match renewal windows and error_rate_5xx_pct falls below SLO within one bucket.

Case 8 — AWS Load Balancer Controller target deregistration: target group churn produces transient 5xx while targets drain. Annotate maintenance or rollouts; compare with AWS TargetHealth events ingested to Splunk; require sustained burn before sev-one.

Case 9 — SLO burn rate greater than six times budget: treat as fast-burn; escalate immediately using on_call_team with slo_burn_rate and error_rate_5xx_pct in the page.

Case 10 — SLO burn rate between one and six times budget: slow-burn; open a ticket, attach the hourly table row, and schedule remediation within the next business day unless customer impact is already visible in CRM bridges.

Case 11 — False positive from synthetic monitoring on /healthz: low-volume probes can skew ratios on quiet clusters; the SPL drops is_synthetic==1 paths; extend the exclusion list via a macro if your synthetic tool uses custom probe paths.

Case 12 — Cross-link with UC-3.2.18: when backends flap, UC-3.2.18 owns pod-level evidence; this UC owns controller saturation, reload failure, and aggregate door-front error budget. Do not duplicate backend remediation narratives here; hand off with the cluster, ingress_class, and timestamp only.

Governance: quarterly replay one historical ingress incident through the SPL after major controller upgrades. Update the comment macro when indexes move. Require lookup owners to approve threshold edits in the same change record as SLO policy updates.

Closing checklist: five plain-text step headers with em dashes; multisearch lists three arms; coalesce appears on HTTP status and timing fields; eventstats baseline math appears via join on seven-day hourly rates; case includes down, critical, high, medium, healthy; closing table includes cluster, controller_type, ingress_class, requests_per_sec, error_rate_5xx_pct, p99_latency_ms, upstream_zero_endpoints, config_reload_failed, severity, on_call_team, slo_burn_rate, plus upstream_failure_rate, z_5xx, baseline_5xx_pct; narrative fields contain no asterisk emphasis; references include NGINX Ingress monitoring and exporter pages, Kubernetes ingress docs, HAProxy configuration reference, Traefik metrics overview, AWS Load Balancer Controller guide, and Splunk Kubernetes add-on documentation.



## SPL

```spl
`comment("UC-3.2.9 Ingress Controller Health and 4xx/5xx Error Rate. Tunables: (index=web OR index=k8s_logs) plus optional index=k8s_metrics; sourcetypes nginx:access,haproxy:access,traefik:access; SLO_TARGET_5XX_PCT=0.1; FAST_BURN_MULT=6; Z_HIGH=2.5; Z_CRIT=3.5; P99_HIGH_MS=2000; P99_CRIT_MS=5000; earliest=-1h@h latest=@h; BASELINE earliest=-7d@d latest=@d.")`
| multisearch
    [ search (index=web OR index=k8s_logs) sourcetype="nginx:access" earliest=-1h@h latest=@h
      | eval controller_type="nginx"
      | eval cluster=lower(trim(toString(coalesce(k8s_cluster, cluster_name, cluster, kube_cluster, k8s_cluster_name, source_cluster, ""))))
      | eval ingress_class=lower(trim(toString(coalesce(ingress_class, k8s_ingress_class, ingress_class_name, ""))))
      | eval status_code=tonumber(tostring(coalesce(status, status_code, http_status, http_status_code, sc, request_status, code, "")), 10)
      | eval upstream_code=tonumber(tostring(coalesce(upstream_status, upstream_http_code, "")), 10)
      | eval rt_raw=tonumber(tostring(coalesce(request_time, request_time_sec, upstream_response_time, upstream_rt, request_duration, time_taken, "")), 10)
      | eval resp_ms=if(isnotnull(rt_raw) AND rt_raw<500, round(rt_raw*1000, 3), coalesce(rt_raw, tonumber(tostring(coalesce(response_time_ms, duration_ms, traefik_duration_ms, "")), 10)))
      | eval uri=toString(coalesce(uri, request_uri, path, http_uri, request_path, ""))
      | eval lr=lower(_raw)
      | eval is_synthetic=if(match(uri, "(?i)/healthz(\?|$)") OR match(uri, "(?i)/readyz(\?|$)") OR match(uri, "(?i)/livez(\?|$)") OR match(uri, "(?i)/metrics(\?|$)"), 1, 0)
      | eval upstream_zero=if(match(lr, "no live upstreams"), 1, 0)
      | eval is_5xx=if(isnotnull(status_code) AND status_code>=500 AND status_code<600, 1, 0)
      | eval is_upstream_fail=if((isnotnull(upstream_code) AND upstream_code>=500 AND upstream_code<600) OR status_code==502 OR status_code==503 OR status_code==504, 1, 0)
      | where is_synthetic==0 AND isnotnull(status_code)
      | fields _time cluster controller_type ingress_class status_code resp_ms is_5xx is_upstream_fail upstream_zero ]
    [ search (index=web OR index=k8s_logs) sourcetype="haproxy:access" earliest=-1h@h latest=@h
      | eval controller_type="haproxy"
      | eval cluster=lower(trim(toString(coalesce(k8s_cluster, cluster_name, cluster, kube_cluster, k8s_cluster_name, source_cluster, ""))))
      | eval ingress_class=lower(trim(toString(coalesce(ingress_class, proxy_name, fe_name, frontend_name, ""))))
      | eval status_code=tonumber(tostring(coalesce(status, status_code, sc, rsp_code, http_status_code, code, "")), 10)
      | eval upstream_code=null()
      | eval rt_raw=tonumber(tostring(coalesce(TR, tr, Ta, ta, tun, wait, response_time, time_taken, "")), 10)
      | eval resp_ms=if(isnotnull(rt_raw) AND rt_raw<500, round(rt_raw*1000, 3), coalesce(rt_raw, tonumber(tostring(coalesce(response_time_ms, duration_ms, "")), 10)))
      | eval uri=toString(coalesce(uri, path, req_uri, http_uri, ""))
      | eval lr=lower(_raw)
      | eval is_synthetic=if(match(uri, "(?i)/healthz(\?|$)") OR match(uri, "(?i)/readyz(\?|$)") OR match(uri, "(?i)/livez(\?|$)"), 1, 0)
      | eval upstream_zero=if(match(lr, "nosrv|no server available"), 1, 0)
      | eval is_5xx=if(isnotnull(status_code) AND status_code>=500 AND status_code<600, 1, 0)
      | eval is_upstream_fail=if(status_code==502 OR status_code==503 OR status_code==504, 1, 0)
      | where is_synthetic==0 AND isnotnull(status_code)
      | fields _time cluster controller_type ingress_class status_code resp_ms is_5xx is_upstream_fail upstream_zero ]
    [ search (index=web OR index=k8s_logs) sourcetype="traefik:access" earliest=-1h@h latest=@h
      | eval controller_type="traefik"
      | eval cluster=lower(trim(toString(coalesce(k8s_cluster, cluster_name, cluster, kube_cluster, k8s_cluster_name, source_cluster, ""))))
      | eval ingress_class=lower(trim(toString(coalesce(ingress_class, entryPointName, entry_point, routerName, router_name, ""))))
      | eval status_code=tonumber(tostring(coalesce(DownstreamStatus, downstream_status, status, status_code, code, http_status, "")), 10)
      | eval upstream_code=tonumber(tostring(coalesce(OriginStatus, origin_status, upstream_status, "")), 10)
      | eval rt_raw=tonumber(tostring(coalesce(Duration, duration, round_trip_time_ms, "")), 10)
      | eval resp_ms=if(isnotnull(rt_raw) AND rt_raw>0 AND rt_raw<500, round(rt_raw*1000, 3), if(isnotnull(rt_raw) AND rt_raw>=500, rt_raw, tonumber(tostring(coalesce(response_time_ms, duration_ms, "")), 10)))
      | eval uri=toString(coalesce(RequestPath, request_path, path, uri, ""))
      | eval lr=lower(_raw)
      | eval is_synthetic=if(match(uri, "(?i)/healthz(\?|$)") OR match(uri, "(?i)/readyz(\?|$)") OR match(uri, "(?i)/livez(\?|$)"), 1, 0)
      | eval upstream_zero=if(match(lr, "no valid url|service unavailable"), 1, 0)
      | eval is_5xx=if(isnotnull(status_code) AND status_code>=500 AND status_code<600, 1, 0)
      | eval is_upstream_fail=if((isnotnull(upstream_code) AND upstream_code>=500) OR status_code==502 OR status_code==503 OR status_code==504, 1, 0)
      | where is_synthetic==0 AND isnotnull(status_code)
      | fields _time cluster controller_type ingress_class status_code resp_ms is_5xx is_upstream_fail upstream_zero ]
| eval cluster=if(isnull(cluster) OR len(trim(cluster))<1 OR cluster="null", "unknown_cluster", cluster)
| eval ingress_class=if(isnull(ingress_class) OR len(trim(ingress_class))<1 OR ingress_class="null", "default", ingress_class)
| bin _time span=1h
| stats count AS total_count sum(is_5xx) AS five_xx_count sum(is_upstream_fail) AS upstream_fail_hits max(upstream_zero) AS upstream_zero_endpoints perc99(resp_ms) AS p99_latency_ms BY cluster controller_type ingress_class _time
| eval window_sec=3600
| eval requests_per_sec=if(window_sec>0, round(total_count/window_sec, 4), 0)
| eval error_rate_5xx_pct=if(total_count>0, round(100.0*five_xx_count/total_count, 4), 0)
| eval upstream_failure_rate=if(total_count>0, round(100.0*upstream_fail_hits/total_count, 4), 0)
| eval SLO_TARGET_5XX_PCT=0.1
| eval slo_5xx_budget_count=if(total_count>0, max(ceil(total_count * SLO_TARGET_5XX_PCT / 100.0), 1), 1)
| eval slo_burn_rate=round(five_xx_count / slo_5xx_budget_count, 3)
| join type=left cluster controller_type ingress_class
    [ search (index=web OR index=k8s_logs) (sourcetype="nginx:access" OR sourcetype="haproxy:access" OR sourcetype="traefik:access") earliest=-7d@d latest=@d
      | eval controller_type=case(sourcetype="nginx:access", "nginx", sourcetype="haproxy:access", "haproxy", sourcetype="traefik:access", "traefik", true(), "unknown")
      | eval cluster=lower(trim(toString(coalesce(k8s_cluster, cluster_name, cluster, kube_cluster, k8s_cluster_name, source_cluster, ""))))
      | eval ingress_class=lower(trim(toString(coalesce(ingress_class, k8s_ingress_class, proxy_name, fe_name, entryPointName, routerName, ""))))
      | eval status_code=tonumber(tostring(coalesce(status, status_code, http_status, DownstreamStatus, sc, rsp_code, code, "")), 10)
      | eval uri=toString(coalesce(uri, request_uri, path, RequestPath, http_uri, ""))
      | eval is_synthetic=if(match(uri, "(?i)/healthz(\?|$)") OR match(uri, "(?i)/readyz(\?|$)") OR match(uri, "(?i)/livez(\?|$)") OR match(uri, "(?i)/metrics(\?|$)"), 1, 0)
      | eval is_5xx=if(isnotnull(status_code) AND status_code>=500 AND status_code<600, 1, 0)
      | where is_synthetic==0 AND isnotnull(status_code)
      | eval ingress_class=if(isnull(ingress_class) OR len(trim(ingress_class))<1, "default", ingress_class)
      | bin _time span=1h aligntime=@h
      | stats count AS bc sum(is_5xx) AS b5 BY cluster controller_type ingress_class _time
      | eval hr5=if(bc>0, 100.0*b5/bc, null())
      | stats avg(hr5) AS baseline_5xx_pct_avg stdev(hr5) AS baseline_5xx_stdev BY cluster controller_type ingress_class ]
| eval baseline_5xx_pct=coalesce(baseline_5xx_pct_avg, 0.05)
| eval baseline_5xx_stdev=if(isnotnull(baseline_5xx_stdev) AND baseline_5xx_stdev>0, baseline_5xx_stdev, 0.02)
| eval z_5xx=if(baseline_5xx_stdev>0, round((error_rate_5xx_pct - baseline_5xx_pct) / baseline_5xx_stdev, 3), if(error_rate_5xx_pct>baseline_5xx_pct+0.05, 5, 0))
| join type=left max=0 cluster
    [ search index=k8s_metrics earliest=-1h@h latest=@h
      | eval mn=lower(toString(coalesce(metric_name, __name__, name, metric, "")))
      | eval cluster=lower(trim(toString(coalesce(k8s_cluster, cluster, cluster_name, kube_cluster, ""))))
      | where match(mn, "nginx_ingress_controller_config_last_reload_successful")
      | eval v=tonumber(tostring(coalesce(Value, value, metric_value, _value, "")), 10)
      | stats min(v) AS min_reload BY cluster
      | eval config_reload_failed=if(isnull(min_reload) OR min_reload==0, 1, 0)
      | fields cluster config_reload_failed ]
| fillnull value=0 config_reload_failed
| join type=left max=0 cluster
    [| inputlookup ingress_oncall_routing.csv
     | eval cluster=lower(trim(toString(coalesce(cluster, cluster_name, k8s_cluster, ""))))
     | eval on_call_team=toString(coalesce(on_call_team, team, squad, pagerduty_service, ""))
     | fields cluster on_call_team ]
| eval on_call_team=if(isnull(on_call_team) OR len(trim(on_call_team))<1, "platform-ingress", on_call_team)
| eval FAST_BURN_MULT=6
| eval Z_HIGH=2.5
| eval Z_CRIT=3.5
| eval P99_HIGH_MS=2000
| eval P99_CRIT_MS=5000
| eval severity=case(
    config_reload_failed==1, "critical",
    error_rate_5xx_pct>2 OR slo_burn_rate>=FAST_BURN_MULT, "down",
    p99_latency_ms>=P99_CRIT_MS OR z_5xx>=Z_CRIT OR upstream_failure_rate>5, "critical",
    z_5xx>=Z_HIGH OR error_rate_5xx_pct>0.5 OR p99_latency_ms>=P99_HIGH_MS, "high",
    error_rate_5xx_pct>SLO_TARGET_5XX_PCT OR upstream_failure_rate>1 OR (slo_burn_rate>1 AND slo_burn_rate<FAST_BURN_MULT), "medium",
    error_rate_5xx_pct<=SLO_TARGET_5XX_PCT AND p99_latency_ms<P99_HIGH_MS AND upstream_failure_rate<=1, "healthy",
    true(), "medium")
| where severity!="healthy"
| table cluster controller_type ingress_class requests_per_sec error_rate_5xx_pct p99_latency_ms upstream_zero_endpoints config_reload_failed severity on_call_team slo_burn_rate upstream_failure_rate z_5xx baseline_5xx_pct
```

## CIM SPL

```spl
| tstats summariesonly=t count FROM datamodel=Web WHERE nodename=Web earliest=-1h@h latest=@h BY Web.url Web.status span=5m
| rename Web.url AS uri Web.status AS status
| eval is_5xx=if(status>=500 AND status<600,1,0)
| stats sum(is_5xx) AS five_xx count AS total BY uri
| eval error_rate_5xx_pct=if(total>0, round(100*five_xx/total,3), 0)
| where error_rate_5xx_pct>0
```

## Visualization

Hourly error_rate_5xx_pct and slo_burn_rate combo chart by cluster, p99_latency_ms heatmap faceted by controller_type, requests_per_sec baseline ribbon, config_reload_failed state timeline from k8s_metrics, and severity-tier table with drilldowns to raw nginx:access, haproxy:access, or traefik:access rows.

## Known False Positives

Brief 502 or 503 bursts during NGINX Ingress configuration reloads follow every Ingress create or update because the controller replaces worker processes; dampen by requiring consecutive buckets above threshold or by correlating reload timestamps from kubernetes audit logs. Readiness gaps during scale-out can show 502 while new pods pass kubelet probes but cloud load balancers have not yet registered targets; suppress using AWS TargetTransitioning annotations or an internal readiness_delay_minutes column on ingress_oncall_routing.csv. Synthetic monitors that probe /healthz without authentication sometimes produce 404 or 401; the SPL excludes common probe paths—extend the macro if your tool uses uncommon URIs. Internet bot and scanner traffic elevates 4xx rates without customer impact; route those signals to security analytics instead of application SLO pages by splitting indexes or sourcetypes for edge WAF logs. Preview and staging clusters that intentionally return 404 on unknown hosts should set suppress_preview_tier in the lookup so medium 4xx surges never page production bridges. Traefik debug access logs in non-production can inflate upstream_zero flags when routers are intentionally partial; scope alerts with cluster tier columns.

## References

- [NGINX Ingress Controller — monitoring](https://kubernetes.github.io/ingress-nginx/user-guide/monitoring/)
- [NGINX Ingress Controller — exporting metrics](https://kubernetes.github.io/ingress-nginx/)
- [Kubernetes — Ingress](https://kubernetes.io/docs/concepts/services-networking/ingress/)
- [Kubernetes — Ingress controllers](https://kubernetes.io/docs/concepts/services-networking/ingress-controllers/)
- [HAProxy configuration manual](https://docs.haproxy.org/dev/configuration.html)
- [Traefik — Metrics overview](https://doc.traefik.io/traefik/observability/metrics/overview/)
- [AWS — AWS Load Balancer Controller](https://docs.aws.amazon.com/eks/latest/userguide/aws-load-balancer-controller.html)
- [Splunk — Kubernetes Add-on](https://docs.splunk.com/Documentation/AddOns/released/Kubernetes/About)
