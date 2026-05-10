<!-- AUTO-GENERATED from UC-3.2.18.json — DO NOT EDIT -->

---
id: "3.2.18"
title: "Kubernetes Ingress Upstream 502/503/504 — Backend Pod and Endpoint Health Axis"
status: "verified"
criticality: "critical"
splunkPillar: "Observability"
---

# UC-3.2.18 · Kubernetes Ingress Upstream 502/503/504 — Backend Pod and Endpoint Health Axis

> **Criticality:** Critical &middot; **Difficulty:** Intermediate &middot; **Pillar:** Observability &middot; **Type:** Reliability, Availability &middot; **Wave:** Walk &middot; **Status:** Verified

*We watch the doorway between the public internet and the programs running inside our clusters. When that doorway answers with errors because the programs behind it are missing, overloaded, or cannot complete a secure handshake, we raise a clear signal so teams fix the right layer instead of guessing.*

---

## Description

Isolates customer-visible 502 Bad Gateway, 503 Service Unavailable, and 504 Gateway Timeout responses emitted by Kubernetes ingress data planes because upstream pods, endpoints, TLS verification, or backend pools are unhealthy—not because the ingress controller process failed admission, reload, or configuration (UC-3.2.9). The analytic ties normalized edge access logs to kube-state-metrics signals for endpoint address availability and pod readiness so responders see whether the ingress returned 502 after an upstream reset, 503 when no ready endpoint accepted traffic, 504 when upstream latency exceeded proxy timeouts, or 502-class symptoms after TLS verify or mTLS mismatch between proxy and application container. It names controller family (nginx_ingress, traefik, envoy_ingress, haproxy_ingress, contour_envoy, aws_alb, gke_l7, aks_appgw) for routing runbooks while keeping equipmentModels scoped to kubernetes_k8s.

## Value

Mean time to innocence drops when platform teams can prove an edge 503 coincides with kube_endpoint_address_available at zero for the Service namespace while UC-3.2.9 dashboards stay green for controller reload health. Application owners receive actionable rows that pair vhost, namespace, dominant symptom code, ninetieth percentile request latency, minimum endpoint availability, average pod ready ratio, and TLS-hint flags instead of generic five-xx percentiles alone. FinOps gains defensible correlation between upstream saturation, connection-pool exhaustion hints in access logs, and readiness churn without re-ingesting duplicate controller-process metrics already governed elsewhere.

## Implementation

Forward ingress access logs with upstream_status and timing fields into index=web, scrape kube-state-metrics into k8s_metrics, publish ingress_oncall_routing.csv, save uc_3_2_18_ingress_upstream_backend_5xx every fifteen minutes with earliest=-24h@h latest=now, route critical and high severities per platform paging policy, and validate with a lab Deployment that toggles readiness or introduces upstream delay while tailing the closing table.

## Evidence

Saved search uc_3_2_18_ingress_upstream_backend_5xx; ingress_oncall_routing.csv versioned in git; weekly CSV export of alert tables to a restricted evidence index; dashboard drilldowns from vhost to kube Endpoints describe snippets.

## Control test

### Positive scenario

In a lab namespace, scale a Deployment behind an Ingress to zero replicas, generate traffic with curl in a loop, run uc_3_2_18_ingress_upstream_backend_5xx over earliest=-24h@h, and expect rows with dominant_symptom 503, kube_endpoint_min_available at or near zero, and severity critical or high when ERR_FLOOR is met.

### Negative scenario

With all pods ready and healthy upstream responses, send only 200-class traffic for one hour; expect zero rows after the final where clause because is_edge_502_504 never triggers.

## Detailed Implementation

### Step 1 — Prerequisites

Head of Platform owns this control with the service-mesh or ingress platform squad, the observability engineer who certifies label parity between Prometheus scrapes and access-log dimensions, and the application reliability lead who maps namespaces to customer-facing services. UC-3.2.18 is deliberately narrower than UC-3.2.9: the latter proves whether the shared ingress controller process, admission webhooks, and configuration reload planes are healthy across aggregate north-south HTTP. This document instead explains how to detect and triage upstream or backend failures that surface as 502, 503, and 504 at the data plane when clients still reach a listening proxy. Scope includes NGINX Ingress with log-format-upstream JSON, Traefik access logs, Envoy-based ingress classes such as Contour or Istio gateways when fields upstream_cluster and response_flags land in Splunk, HAProxy ingress implementations that expose backend status in logs, cloud L7 controllers including AWS Load Balancer Controller with target group semantics, Google Kubernetes Engine HTTP(S) load balancing telemetry, and Azure Application Gateway ingress add-on diagnostics. Out of scope: certificate notAfter lifecycle depth (UC-3.2.13), pure controller CPU saturation without upstream symptoms (UC-3.2.9), per-URL canary decomposition (UC-3.2.27 when implemented), and bare Service object cardinality without ingress correlation (UC-3.2.41).

Index and permission design: dedicate index=web for edge HTTP with sourcetype discipline, index=k8s_logs when security policy splits administrative ingress stderr from customer access lines, and index=k8s_metrics for kube-state-metrics and optional nginx_ingress_controller_requests counters. Readers need role capabilities that include all three; evidence exports must redact query strings when legal requires. HEC tokens rotate quarterly. kube-state-metrics RBAC must list watches on endpoints, pods, and services so kube_endpoint_address_available and kube_pod_status_ready series exist; validate scrape interval versus pod churn so fifteen-minute rollups do not miss short flaps.

Governance lookup ingress_oncall_routing.csv carries cluster, on_call_team, optional suppress_preview_tier, and optional max_ingress_latency_ms override columns documented beside UC-3.2.9; reuse it here so paging routes stay consistent. Namespace allow lists for sandboxes belong in the same file to keep synthetic chaos from paging production bridges.

Risk framing: a 502 with upstream_status dash or upstream_code 0 in NGINX often means the proxy could not obtain a TCP connection to any ready endpoint, which tracks rolling pod terminations, wrong containerPort wiring, or NetworkPolicy drops. A 503 with upstream text referencing no live upstreams or Traefik messages about missing servers tracks zero ready endpoints, sticky-session affinity pinning all clients to a drained pod, or readiness probes that never flip true after a dependency outage. A 504 with high request_time and healthy upstream_code suggests the backend answered too slowly versus proxy read timeouts, database locks, or dependency chains. TLS verify failures and mTLS client certificate mismatches frequently appear as 502 with ssl_ or verify fragments in error logs even when HTTP status in access lines looks nominal; the SPL flags tls_upstream_hint for those rows.

Licensing: raw access logs dominate; retain high-fidelity upstream fields only on clusters that justify forensic depth. Sample success traffic into separate summary metrics if finance challenges daily volume.

Differentiation recap: when nginx_ingress_controller_config_last_reload_successful collapses, open UC-3.2.9 first. When this search fires with kube_endpoint_min_available at zero, focus on Endpoints and readiness before touching controller configuration.


### Step 2 — Configure data collection

Enable JSON access logs on NGINX Ingress using log-format-upstream so upstream_status, upstream_response_time, request_time, upstream_addr, host, and ingress namespace annotations flow as extracted fields. Traefik static configuration should enable accessLog with fields DownstreamStatus, OriginStatus, Duration, RouterName, ServiceName, and RequestHost. Envoy ingress should emit JSON access logs including response_code, upstream_cluster, response_flags, and x-envoy-upstream-service-time when possible.

Deploy kube-state-metrics with a ServiceMonitor or OTel prometheus_simple scrape at thirty-second intervals. Confirm the following families appear in index=k8s_metrics: kube_endpoint_address_available with endpoint and namespace labels, kube_pod_status_ready for condition true, kube_pod_container_status_ready, kube_pod_status_phase.

Example NGINX Ingress ConfigMap fragment:

```yaml
data:
  log-format-upstream: >-
    {"time":"$time_iso8601","host":"$host","status":$status,
    "upstream_status":"$upstream_status","request_time":$request_time,
    "upstream_response_time":"$upstream_response_time",
    "upstream_addr":"$upstream_addr",
    "ingress_namespace":"$namespace",
    "ingress_class":"$ingress_name"}
```

Example Splunk OpenTelemetry Collector exporter routing edge logs to index=web:

```yaml
exporters:
  splunk_hec/web:
    token: "${SPLUNK_HEC_TOKEN_WEB}"
    endpoint: "https://splunk.example.com:8088/services/collector"
    index: web
service:
  pipelines:
    logs/ingress:
      receivers: [filelog]
      processors: [k8sattributes, batch]
      exporters: [splunk_hec/web]
```

For AWS Load Balancer Controller, ensure target group health transition events or access logs with target_status_code reach Splunk so you can distinguish ALB-generated 502 from pod-generated 502. For GKE, enable HTTP(S) load balancer logging to a sink your forwarder reads. For AKS Application Gateway, export diagnostic settings for ApplicationGatewayAccessLog and PerformanceLog.

Validate with short searches: index=web sourcetype=nginx:access upstream_status=* earliest=-15m, index=k8s_metrics kube_endpoint_address_available earliest=-15m, and index=k8s_metrics kube_pod_status_ready earliest=-15m. Skew between log and metric pipelines should stay under one minute for production alerting.


### Step 3 — Create the search and alert

Save the SPL as uc_3_2_18_ingress_upstream_backend_5xx with schedule */15 * * * * and alert when severity is critical or high. Throttle duplicate pages per cluster, namespace, and vhost for thirty minutes unless severity escalates. Attach the closing table row body to tickets. Document controller_family values in your runbook: nginx_ingress, traefik, envoy_ingress, haproxy_ingress, contour_envoy, aws_alb, gke_l7, aks_appgw.

Pipeline intent: multisearch fans NGINX and Traefik arms so a missing sourcetype does not blank results. Each arm keeps only 502, 503, and 504 client statuses, normalizes cluster and namespace, derives req_latency_ms, flags tls_upstream_hint from raw text, and preserves upstream_code for upstream-emitted five-xx. The fifteen-minute bin rolls up counts and ninetieth percentile latency per vhost. eventstats adds fleet_median_cnt for relative noise. Subsearches join kube_endpoint_address_available and kube_pod_status_ready rollups by cluster and namespace. inputlookup merges on_call_team. case assigns severity with critical weight on zero endpoints with 503 symptoms and large TLS-hinted 502 bursts.

Fenced SPL for runbooks must match the spl JSON field byte-for-byte aside from newline normalization:

```spl
`comment("UC-3.2.18 Ingress upstream 502-504 vs kube-state-metrics. Tunables: indexes web k8s_logs k8s_metrics; sourcetypes nginx:access traefik:access prometheus:scrape:metrics kube:objects:metrics; earliest=-24h@h latest=now; ERR_FLOOR=12; LAT_WARN_MS=6000.")`
| multisearch
    [ search (index=web OR index=k8s_logs) sourcetype="nginx:access" earliest=-24h@h latest=now
      | eval controller_family="nginx_ingress"
      | eval cluster=lower(trim(toString(coalesce(k8s_cluster, cluster_name, cluster, kube_cluster, k8s_cluster_name, source_cluster, ""))))
      | eval ingress_class=lower(trim(toString(coalesce(ingress_class, k8s_ingress_class, ingress_class_name, ""))))
      | eval namespace=lower(trim(toString(coalesce(k8s_namespace, kubernetes_namespace, ingress_namespace, proxy_upstream_name, ""))))
      | eval status_code=tonumber(tostring(coalesce(status, status_code, http_status, http_status_code, sc, "")), 10)
      | eval upstream_code=tonumber(tostring(coalesce(upstream_status, upstream_http_code, "")), 10)
      | eval rt_raw=tonumber(tostring(coalesce(request_time, request_time_sec, upstream_response_time, upstream_rt, "")), 10)
      | eval req_latency_ms=if(isnotnull(rt_raw) AND rt_raw>0 AND rt_raw<300, round(rt_raw*1000, 2), if(isnotnull(rt_raw) AND rt_raw>=300, rt_raw, tonumber(tostring(coalesce(response_time_ms, duration_ms, "")), 10)))
      | eval vhost=lower(trim(toString(coalesce(host, http_host, server_name, ""))))
      | eval upstream_peer=trim(toString(coalesce(upstream_addr, upstream, "")))
      | eval uri=toString(coalesce(uri, request_uri, path, ""))
      | eval lr=lower(_raw)
      | eval tls_upstream_hint=if(match(lr, "ssl|handshake|verify|x509|peer cert|certificate"), 1, 0)
      | eval is_edge_502_504=if(isnotnull(status_code) AND status_code>=502 AND status_code<=504, 1, 0)
      | eval upstream_5xx_echo=if((isnotnull(upstream_code) AND upstream_code>=500 AND upstream_code<600), 1, 0)
      | where is_edge_502_504=1
      | eval symptom_code=case(status_code==502, 502, status_code==503, 503, status_code==504, 504, true(), 0)
      | fields _time cluster controller_family ingress_class namespace vhost uri status_code upstream_code req_latency_ms upstream_peer tls_upstream_hint symptom_code upstream_5xx_echo ]
    [ search (index=web OR index=k8s_logs) sourcetype="traefik:access" earliest=-24h@h latest=now
      | eval controller_family="traefik"
      | eval cluster=lower(trim(toString(coalesce(k8s_cluster, cluster_name, cluster, kube_cluster, k8s_cluster_name, source_cluster, ""))))
      | eval ingress_class=lower(trim(toString(coalesce(ingress_class, entryPointName, router_name, routerName, ""))))
      | eval namespace=lower(trim(toString(coalesce(k8s_namespace, kubernetes_namespace, ServiceName, serviceName, ""))))
      | eval status_code=tonumber(tostring(coalesce(DownstreamStatus, downstream_status, status, status_code, "")), 10)
      | eval upstream_code=tonumber(tostring(coalesce(OriginStatus, origin_status, upstream_status, "")), 10)
      | eval rt_raw=tonumber(tostring(coalesce(Duration, duration, round_trip_time_ms, "")), 10)
      | eval req_latency_ms=if(isnotnull(rt_raw) AND rt_raw>0 AND rt_raw<300, round(rt_raw*1000, 2), if(isnotnull(rt_raw) AND rt_raw>=300, rt_raw, tonumber(tostring(coalesce(response_time_ms, duration_ms, "")), 10)))
      | eval vhost=lower(trim(toString(coalesce(RequestHost, request_host, host, ""))))
      | eval upstream_peer=trim(toString(coalesce(ServiceAddr, service_addr, BackendURL, "")))
      | eval uri=toString(coalesce(RequestPath, request_path, uri, ""))
      | eval lr=lower(_raw)
      | eval tls_upstream_hint=if(match(lr, "tls|handshake|x509|certificate"), 1, 0)
      | eval is_edge_502_504=if(isnotnull(status_code) AND status_code>=502 AND status_code<=504, 1, 0)
      | eval upstream_5xx_echo=if((isnotnull(upstream_code) AND upstream_code>=500 AND upstream_code<600), 1, 0)
      | where is_edge_502_504=1
      | eval symptom_code=case(status_code==502, 502, status_code==503, 503, status_code==504, 504, true(), 0)
      | fields _time cluster controller_family ingress_class namespace vhost uri status_code upstream_code req_latency_ms upstream_peer tls_upstream_hint symptom_code upstream_5xx_echo ]
| eval cluster=if(isnull(cluster) OR len(trim(cluster))<1 OR cluster="null", "unknown_cluster", cluster)
| eval ingress_class=if(isnull(ingress_class) OR len(trim(ingress_class))<1 OR ingress_class="null", "default", ingress_class)
| eval namespace=if(isnull(namespace) OR len(trim(namespace))<1 OR namespace="null", "unknown_ns", namespace)
| bin _time span=15m aligntime=@m
| stats count AS edge_cnt sum(upstream_5xx_echo) AS upstream_5xx_hits max(tls_upstream_hint) AS tls_hint_flag perc90(req_latency_ms) AS p90_latency_ms values(symptom_code) AS symptom_mv BY _time cluster controller_family ingress_class namespace vhost
| eval symptom_join=mvjoin(symptom_mv, ",")
| eval dominant_symptom=if(match(symptom_join, "504"), 504, if(match(symptom_join, "503"), 503, if(match(symptom_join, "502"), 502, 0)))
| eventstats median(edge_cnt) AS fleet_median_cnt BY cluster
| eval ERR_FLOOR=12
| eval LAT_WARN_MS=6000
| where edge_cnt>=ERR_FLOOR OR upstream_5xx_hits>=3 OR p90_latency_ms>=LAT_WARN_MS
| join type=left max=0 cluster namespace
    [ search ((index=k8s_metrics OR index=k8s) (sourcetype="prometheus:scrape:metrics" OR sourcetype="kube:objects:metrics")) earliest=-24h@h latest=now
      | eval lr=lower(_raw)
      | where like(lr, "%kube_endpoint_address_available%")
      | rex field=_raw "namespace=\"(?<mns>[^\"]+)\""
      | rex field=_raw "\\s(?<epval>[0-9.eE+-]+)\\s*$"
      | eval ep_avail=tonumber(epval, 10)
      | eval cluster=lower(trim(toString(coalesce(cluster, cluster_name, k8s_cluster, kube_cluster, ""))))
      | stats min(ep_avail) AS kube_endpoint_min_available BY cluster mns
      | rename mns AS namespace ]
| fillnull value=999999 kube_endpoint_min_available
| join type=left max=0 cluster namespace
    [ search ((index=k8s_metrics OR index=k8s) (sourcetype="prometheus:scrape:metrics" OR sourcetype="kube:objects:metrics")) earliest=-24h@h latest=now
      | eval lr=lower(_raw)
      | where like(lr, "%kube_pod_status_ready%") AND match(lr, "condition=\\\"true\\\"|condition=\"true\"")
      | rex field=_raw "namespace=\"(?<pns>[^\"]+)\""
      | rex field=_raw "pod=\"(?<pdn>[^\"]+)\""
      | rex field=_raw "\\s(?<rdy>[01])\\s*$"
      | eval ready_v=tonumber(rdy, 10)
      | eval cluster=lower(trim(toString(coalesce(cluster, cluster_name, k8s_cluster, kube_cluster, ""))))
      | stats sum(ready_v) AS ready_sum dc(pdn) AS pod_dc BY cluster pns
      | eval kube_pod_ready_ratio=if(pod_dc>0, round(ready_sum/pod_dc, 4), 1.0)
      | rename pns AS namespace
      | fields cluster namespace kube_pod_ready_ratio ]
| fillnull value=1 kube_pod_ready_ratio
| join type=left max=0 cluster
    [| inputlookup ingress_oncall_routing.csv
     | eval cluster=lower(trim(toString(coalesce(cluster, cluster_name, k8s_cluster, ""))))
     | eval on_call_team=toString(coalesce(on_call_team, team, squad, pagerduty_service, ""))
     | fields cluster on_call_team ]
| eval on_call_team=if(isnull(on_call_team) OR len(trim(on_call_team))<1, "platform-edge-upstream", on_call_team)
| eval severity=case(
    kube_endpoint_min_available==0 AND dominant_symptom==503, "critical",
    kube_pod_ready_ratio<0.4 AND dominant_symptom>0, "critical",
    tls_hint_flag==1 AND edge_cnt>=ERR_FLOOR AND dominant_symptom==502, "high",
    dominant_symptom==504 AND p90_latency_ms>=LAT_WARN_MS, "high",
    kube_endpoint_min_available<=0 AND edge_cnt>=20, "high",
    upstream_5xx_hits>=8 AND dominant_symptom==502, "high",
    edge_cnt>=fleet_median_cnt*4 AND dominant_symptom==503, "medium",
    kube_pod_ready_ratio<0.85 AND dominant_symptom>0, "medium",
    true(), "medium")
| where match(severity, "critical|high|medium")
| table _time cluster controller_family ingress_class namespace vhost edge_cnt upstream_5xx_hits dominant_symptom p90_latency_ms kube_endpoint_min_available kube_pod_ready_ratio tls_hint_flag fleet_median_cnt severity on_call_team symptom_join
```

Alert actions should include the symptom_join and kube_endpoint_min_available columns in the message body so responders open Kubernetes describe for Endpoints before kube-apiserver control-plane theories.


### Step 4 — Validate

Positive path A — readiness drain: kubectl scale deployment lab-upstream --replicas=0 in a non-production namespace instrumented in ingress logs; expect dominant_symptom 503 with kube_endpoint_min_available collapsing toward zero within two scrape intervals and a critical severity row when ERR_FLOOR clears.

Positive path B — slow upstream: introduce an intentional sleep in the lab service above proxy read timeout; expect dominant_symptom 504 with p90_latency_ms climbing past LAT_WARN_MS while kube_pod_ready_ratio stays near one.

Positive path C — wrong Service port: point an Ingress backend to a closed containerPort; expect 502 with upstream_code 0 or dash patterns in raw NGINX lines and upstream_5xx_echo low while tls_hint_flag stays zero.

Positive path D — TLS verify mismatch: deploy an upstream that presents a certificate whose SAN does not match the kube Service DNS name used by the mesh or ingress backend protocol; expect tls_hint_flag one with 502 dominant_symptom.

Tear down: restore replicas, fix port, or roll back TLS material; confirm the saved search returns zero qualifying rows after the throttle window.

Spot validation SPL for field presence:

```spl
(index=web OR index=k8s_logs) (sourcetype="nginx:access" OR sourcetype="traefik:access") earliest=-30m status>=502 status<=504
| eval cluster=lower(trim(toString(coalesce(k8s_cluster, cluster_name, cluster, ""))))
| stats count BY sourcetype cluster status
| sort - count
```

Metric path validation:

```spl
(index=k8s_metrics OR index=k8s) (sourcetype="prometheus:scrape:metrics" OR sourcetype="kube:objects:metrics") earliest=-30m (kube_endpoint_address_available OR kube_pod_status_ready)
| head 20
```

Readers without index=k8s_metrics must see the log arm still function but joins will show synthetic endpoint availability; document that gap in onboarding.


### Step 5 — Operationalize & Troubleshoot

Case 1 — NGINX 502 with upstream_status 502 and kube_pod_ready_ratio collapsed
The pod answered five-xx; pivot to application logs and dependency timeouts before blaming the ingress. Compare upstream_response_time to request_time to see whether delay sat upstream or in TLS.

Case 2 — NGINX 502 with upstream_status dash and kube_endpoint_min_available zero
No socket could be established; verify Endpoints subsets, readiness probes, and that Service selectors still match pod labels after a mis-typed rollout.

Case 3 — Traefik 503 with OriginStatus empty and router churn during deploy
Rolling updates can leave a router without backends for seconds; dampen alerts when edge_cnt is below ERR_FLOOR for only one bucket and deployment annotations show a controlled rollout.

Case 4 — Sticky-session storms
When session affinity pins traffic to a single pod that is terminating, edge 503 bursts can appear with healthy aggregate pod counts; inspect sessionAffinity on Service and pod disruption budgets.

Case 5 — Connection-pool exhaustion at the application
Access logs show fast 503 or 502 with upstream flags suggesting reset while CPU is low; thread dumps and database pool metrics belong to the service team, not the ingress squad.

Case 6 — Contour or Envoy upstream_cluster mismatch
response_flags containing UF or URX in Envoy logs signals upstream connection failure or retry exhaustion; map upstream_cluster to the Kubernetes Service name and verify mTLS secrets.

Case 7 — AWS ALB target deregistration
Compare elb_status_code 502 with target_status_code dash during target drain; require sustained buckets before sev-one if health checks are still passing intermittently.

Case 8 — GKE L7 load balancer backend unhealthy
Backend service health can decouple from pod readiness during NEG sync delays; correlate with GCP operations console transitions and require cross-check on kube_endpoint_address_available.

Case 9 — AKS Application Gateway backend pool overlap
Misconfigured backend settings on path-based rules send traffic to empty pools; validate Application Gateway backend health diagnostics and Ingress annotations from the AKS add-on.

Case 10 — Rate limiting inside the app returning 503
Distinguish ingress-emitted 503 from upstream JSON bodies carrying Retry-After by logging upstream headers when policy allows; tune ERR_FLOOR so marketing bursts do not page.

Case 11 — mTLS client certificate rotation skew
New upstream trust bundles without matching client certs yield handshake failures; align rotation jobs with tls_hint_flag spikes and coordinate with UC-3.2.13 calendar only for notAfter, not controller reload.

Case 12 — False correlation on unknown namespace
When namespace stays unknown_ns because JSON logs omit ingress_namespace, joins widen to fleet-level kube ratios; fix log pipeline before trusting kube_pod_ready_ratio for that row.

Governance: quarterly replay one historical upstream incident through the SPL after kube-state-metrics upgrades because label shapes shift. Update multisearch arms when you adopt a new ingress class. Keep differentiation notes with UC-3.2.9 in the incident template so bridges do not duplicate controller-process investigation steps.

Performance note: when Job Inspector shows heavy scan cost on k8s_metrics, materialize hourly rollups for kube_endpoint_min_available and kube_pod_ready_ratio into a summary index keyed by cluster and namespace, then point the join subsearches at that summary for alerting while retaining raw scrapes for ad-hoc tuning.



## SPL

```spl
`comment("UC-3.2.18 Ingress upstream 502-504 vs kube-state-metrics. Tunables: indexes web k8s_logs k8s_metrics; sourcetypes nginx:access traefik:access prometheus:scrape:metrics kube:objects:metrics; earliest=-24h@h latest=now; ERR_FLOOR=12; LAT_WARN_MS=6000.")`
| multisearch
    [ search (index=web OR index=k8s_logs) sourcetype="nginx:access" earliest=-24h@h latest=now
      | eval controller_family="nginx_ingress"
      | eval cluster=lower(trim(toString(coalesce(k8s_cluster, cluster_name, cluster, kube_cluster, k8s_cluster_name, source_cluster, ""))))
      | eval ingress_class=lower(trim(toString(coalesce(ingress_class, k8s_ingress_class, ingress_class_name, ""))))
      | eval namespace=lower(trim(toString(coalesce(k8s_namespace, kubernetes_namespace, ingress_namespace, proxy_upstream_name, ""))))
      | eval status_code=tonumber(tostring(coalesce(status, status_code, http_status, http_status_code, sc, "")), 10)
      | eval upstream_code=tonumber(tostring(coalesce(upstream_status, upstream_http_code, "")), 10)
      | eval rt_raw=tonumber(tostring(coalesce(request_time, request_time_sec, upstream_response_time, upstream_rt, "")), 10)
      | eval req_latency_ms=if(isnotnull(rt_raw) AND rt_raw>0 AND rt_raw<300, round(rt_raw*1000, 2), if(isnotnull(rt_raw) AND rt_raw>=300, rt_raw, tonumber(tostring(coalesce(response_time_ms, duration_ms, "")), 10)))
      | eval vhost=lower(trim(toString(coalesce(host, http_host, server_name, ""))))
      | eval upstream_peer=trim(toString(coalesce(upstream_addr, upstream, "")))
      | eval uri=toString(coalesce(uri, request_uri, path, ""))
      | eval lr=lower(_raw)
      | eval tls_upstream_hint=if(match(lr, "ssl|handshake|verify|x509|peer cert|certificate"), 1, 0)
      | eval is_edge_502_504=if(isnotnull(status_code) AND status_code>=502 AND status_code<=504, 1, 0)
      | eval upstream_5xx_echo=if((isnotnull(upstream_code) AND upstream_code>=500 AND upstream_code<600), 1, 0)
      | where is_edge_502_504=1
      | eval symptom_code=case(status_code==502, 502, status_code==503, 503, status_code==504, 504, true(), 0)
      | fields _time cluster controller_family ingress_class namespace vhost uri status_code upstream_code req_latency_ms upstream_peer tls_upstream_hint symptom_code upstream_5xx_echo ]
    [ search (index=web OR index=k8s_logs) sourcetype="traefik:access" earliest=-24h@h latest=now
      | eval controller_family="traefik"
      | eval cluster=lower(trim(toString(coalesce(k8s_cluster, cluster_name, cluster, kube_cluster, k8s_cluster_name, source_cluster, ""))))
      | eval ingress_class=lower(trim(toString(coalesce(ingress_class, entryPointName, router_name, routerName, ""))))
      | eval namespace=lower(trim(toString(coalesce(k8s_namespace, kubernetes_namespace, ServiceName, serviceName, ""))))
      | eval status_code=tonumber(tostring(coalesce(DownstreamStatus, downstream_status, status, status_code, "")), 10)
      | eval upstream_code=tonumber(tostring(coalesce(OriginStatus, origin_status, upstream_status, "")), 10)
      | eval rt_raw=tonumber(tostring(coalesce(Duration, duration, round_trip_time_ms, "")), 10)
      | eval req_latency_ms=if(isnotnull(rt_raw) AND rt_raw>0 AND rt_raw<300, round(rt_raw*1000, 2), if(isnotnull(rt_raw) AND rt_raw>=300, rt_raw, tonumber(tostring(coalesce(response_time_ms, duration_ms, "")), 10)))
      | eval vhost=lower(trim(toString(coalesce(RequestHost, request_host, host, ""))))
      | eval upstream_peer=trim(toString(coalesce(ServiceAddr, service_addr, BackendURL, "")))
      | eval uri=toString(coalesce(RequestPath, request_path, uri, ""))
      | eval lr=lower(_raw)
      | eval tls_upstream_hint=if(match(lr, "tls|handshake|x509|certificate"), 1, 0)
      | eval is_edge_502_504=if(isnotnull(status_code) AND status_code>=502 AND status_code<=504, 1, 0)
      | eval upstream_5xx_echo=if((isnotnull(upstream_code) AND upstream_code>=500 AND upstream_code<600), 1, 0)
      | where is_edge_502_504=1
      | eval symptom_code=case(status_code==502, 502, status_code==503, 503, status_code==504, 504, true(), 0)
      | fields _time cluster controller_family ingress_class namespace vhost uri status_code upstream_code req_latency_ms upstream_peer tls_upstream_hint symptom_code upstream_5xx_echo ]
| eval cluster=if(isnull(cluster) OR len(trim(cluster))<1 OR cluster="null", "unknown_cluster", cluster)
| eval ingress_class=if(isnull(ingress_class) OR len(trim(ingress_class))<1 OR ingress_class="null", "default", ingress_class)
| eval namespace=if(isnull(namespace) OR len(trim(namespace))<1 OR namespace="null", "unknown_ns", namespace)
| bin _time span=15m aligntime=@m
| stats count AS edge_cnt sum(upstream_5xx_echo) AS upstream_5xx_hits max(tls_upstream_hint) AS tls_hint_flag perc90(req_latency_ms) AS p90_latency_ms values(symptom_code) AS symptom_mv BY _time cluster controller_family ingress_class namespace vhost
| eval symptom_join=mvjoin(symptom_mv, ",")
| eval dominant_symptom=if(match(symptom_join, "504"), 504, if(match(symptom_join, "503"), 503, if(match(symptom_join, "502"), 502, 0)))
| eventstats median(edge_cnt) AS fleet_median_cnt BY cluster
| eval ERR_FLOOR=12
| eval LAT_WARN_MS=6000
| where edge_cnt>=ERR_FLOOR OR upstream_5xx_hits>=3 OR p90_latency_ms>=LAT_WARN_MS
| join type=left max=0 cluster namespace
    [ search ((index=k8s_metrics OR index=k8s) (sourcetype="prometheus:scrape:metrics" OR sourcetype="kube:objects:metrics")) earliest=-24h@h latest=now
      | eval lr=lower(_raw)
      | where like(lr, "%kube_endpoint_address_available%")
      | rex field=_raw "namespace=\"(?<mns>[^\"]+)\""
      | rex field=_raw "\\s(?<epval>[0-9.eE+-]+)\\s*$"
      | eval ep_avail=tonumber(epval, 10)
      | eval cluster=lower(trim(toString(coalesce(cluster, cluster_name, k8s_cluster, kube_cluster, ""))))
      | stats min(ep_avail) AS kube_endpoint_min_available BY cluster mns
      | rename mns AS namespace ]
| fillnull value=999999 kube_endpoint_min_available
| join type=left max=0 cluster namespace
    [ search ((index=k8s_metrics OR index=k8s) (sourcetype="prometheus:scrape:metrics" OR sourcetype="kube:objects:metrics")) earliest=-24h@h latest=now
      | eval lr=lower(_raw)
      | where like(lr, "%kube_pod_status_ready%") AND match(lr, "condition=\\\"true\\\"|condition=\"true\"")
      | rex field=_raw "namespace=\"(?<pns>[^\"]+)\""
      | rex field=_raw "pod=\"(?<pdn>[^\"]+)\""
      | rex field=_raw "\\s(?<rdy>[01])\\s*$"
      | eval ready_v=tonumber(rdy, 10)
      | eval cluster=lower(trim(toString(coalesce(cluster, cluster_name, k8s_cluster, kube_cluster, ""))))
      | stats sum(ready_v) AS ready_sum dc(pdn) AS pod_dc BY cluster pns
      | eval kube_pod_ready_ratio=if(pod_dc>0, round(ready_sum/pod_dc, 4), 1.0)
      | rename pns AS namespace
      | fields cluster namespace kube_pod_ready_ratio ]
| fillnull value=1 kube_pod_ready_ratio
| join type=left max=0 cluster
    [| inputlookup ingress_oncall_routing.csv
     | eval cluster=lower(trim(toString(coalesce(cluster, cluster_name, k8s_cluster, ""))))
     | eval on_call_team=toString(coalesce(on_call_team, team, squad, pagerduty_service, ""))
     | fields cluster on_call_team ]
| eval on_call_team=if(isnull(on_call_team) OR len(trim(on_call_team))<1, "platform-edge-upstream", on_call_team)
| eval severity=case(
    kube_endpoint_min_available==0 AND dominant_symptom==503, "critical",
    kube_pod_ready_ratio<0.4 AND dominant_symptom>0, "critical",
    tls_hint_flag==1 AND edge_cnt>=ERR_FLOOR AND dominant_symptom==502, "high",
    dominant_symptom==504 AND p90_latency_ms>=LAT_WARN_MS, "high",
    kube_endpoint_min_available<=0 AND edge_cnt>=20, "high",
    upstream_5xx_hits>=8 AND dominant_symptom==502, "high",
    edge_cnt>=fleet_median_cnt*4 AND dominant_symptom==503, "medium",
    kube_pod_ready_ratio<0.85 AND dominant_symptom>0, "medium",
    true(), "medium")
| where match(severity, "critical|high|medium")
| table _time cluster controller_family ingress_class namespace vhost edge_cnt upstream_5xx_hits dominant_symptom p90_latency_ms kube_endpoint_min_available kube_pod_ready_ratio tls_hint_flag fleet_median_cnt severity on_call_team symptom_join
```

## CIM SPL

```spl
| tstats summariesonly=f count FROM datamodel=Web WHERE nodename=Web earliest=-24h@h latest=now BY Web.url Web.status span=15m
| rename Web.url AS vhost Web.status AS http_status
| where http_status>=502 AND http_status<=504
| stats sum(count) AS edge_cnt BY vhost http_status span=15m
| join type=left vhost [
| tstats summariesonly=f perc90(Performance.response_time) AS p90_ms FROM datamodel=Performance WHERE nodename=Performance earliest=-24h@h latest=now BY Performance.dest span=15m
| rename Performance.dest AS vhost ]
| where edge_cnt>=3
```

## Visualization

Stacked bar of edge_cnt by dominant_symptom per vhost, line overlay of kube_endpoint_min_available and kube_pod_ready_ratio from joined metrics, heatmap of tls_hint_flag by cluster, single value of critical severity count.

## Known False Positives

Chaos experiments that deliberately drop readiness or inject latency in non-production namespaces will reproduce 503 and 504 rows without customer impact unless ingress_oncall_routing.csv suppress_preview_tier flags those clusters. Blue-green cutovers often show a short 502 window while old pods terminate and new pods warm JVM heaps; require two consecutive fifteen-minute buckets above ERR_FLOOR before paging prod. CDN or edge WAF failures occasionally synthesize 502 responses that never hit the cluster; correlate with upstream_addr emptiness and absence of matching kube-state-metrics movement. Bot traffic that hammers deprecated hostnames can elevate 503 counts while business traffic stays healthy; split vhost allow lists. Database maintenance windows that extend application-level timeouts can trip 504 without ingress defects; confirm dominant_symptom 504 against application change calendars. Certificate hot reloads at the sidecar rather than the ingress can spike tls_hint_flag during rotations that are still compliant with PKI policy; dampen when notAfter is not imminently expiring. Autoscaler scale-down races that remove endpoints before in-flight connections drain resemble sticky-session storms; check Pod disruption budgets before blaming code. Mis-parsed namespace fields from incomplete JSON logging widen joins to unknown_ns and inflate kube_pod_ready_ratio significance; fix extraction before trusting severity. Regional DNS failover drills can send traffic to clusters whose backends were intentionally scaled to zero for the drill; exclude those intervals via lookup columns.

## References

- [Kubernetes — Ingress](https://kubernetes.io/docs/concepts/services-networking/ingress/)
- [NGINX Ingress Controller — Troubleshooting](https://kubernetes.github.io/ingress-nginx/troubleshooting/)
- [Envoy — Access logging](https://www.envoyproxy.io/docs/envoy/latest/configuration/observability/access_log/usage)
- [Contour — Troubleshooting](https://projectcontour.io/docs/v1.30/troubleshooting/)
- [Google Cloud — GKE Ingress troubleshooting](https://cloud.google.com/kubernetes-engine/docs/troubleshooting/ingress)
- [Microsoft — Application Gateway Ingress Controller](https://learn.microsoft.com/en-us/azure/application-gateway/ingress-controller-overview)
- [Kubernetes SIGs — AWS Load Balancer Controller](https://kubernetes-sigs.github.io/aws-load-balancer-controller/v2.7/)
- [Traefik — Access Logs](https://doc.traefik.io/traefik/observability/access-logs/)
