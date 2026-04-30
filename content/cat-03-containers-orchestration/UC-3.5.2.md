<!-- AUTO-GENERATED from UC-3.5.2.json — DO NOT EDIT -->

---
id: "3.5.2"
title: "Sidecar Proxy Health"
status: "verified"
criticality: "high"
splunkPillar: "Observability"
---

# UC-3.5.2 · Sidecar Proxy Health

## Description

Monitors **Envoy** sidecar proxy health across every pod in the **Istio** mesh by tracking `envoy_server_live`, `envoy_server_state`, and `envoy_server_uptime` metrics, correlating unhealthy or draining proxies with Kubernetes restart events, and analyzing Envoy response flags (UF, UH, UC, LR) from access logs to pinpoint proxy-level failures before they cascade into service-wide outages.

## Value

An unhealthy Envoy sidecar silently drops or misroutes traffic for the pod it protects — unlike application crashes that generate obvious errors, a draining or not-ready proxy degrades the mesh invisibly until retry budgets are exhausted and circuit breakers trip across dependent services. Detecting sidecar health degradation at the proxy level gives SRE teams the earliest possible signal to drain, restart, or reschedule the affected pod.

## Implementation

Deploy the Splunk OTel Collector with Prometheus receiver scraping Envoy sidecar stats on port 15090 to collect envoy_server_live, envoy_server_state, and envoy_server_uptime. Build three search variants: sidecar health status (live/draining/initializing/stale), sidecar restart correlation with kube:events, and Envoy response flag analysis from istio:accesslog. Alert on any sidecar in UNHEALTHY or STALE state and on response flag spikes indicating proxy-level failures.

## Detailed Implementation

Prerequisites
• **Istio** 1.18+ with **Envoy** **sidecar** injection enabled across target namespaces; verify injection: `kubectl get namespace -L istio-injection` — namespaces should show `enabled`.
• **Splunk OpenTelemetry Collector** deployed as a **DaemonSet** via the `splunk-otel-collector-chart` **Helm chart** with the **Prometheus receiver** scraping **Envoy** sidecar stats on port **15090** (`/stats/prometheus`); the default chart discovers sidecars via **pod annotations** `prometheus.io/port: "15090"`.
• **Splunk HEC** token for **`index=containers`** with default **`sourcetype=otel:metrics`**; secondary stream for **`sourcetype=kube:events`** via Splunk Connect for **Kubernetes**; third stream for **`sourcetype=istio:accesslog`** from Envoy stdout.
• **kube-state-metrics** deployed to expose **`kube_pod_container_status_ready`** and **`kube_pod_container_status_restarts_total`** for the `istio-proxy` container specifically — the sidecar restart search in Step 2 depends on these counters.
• **Kubernetes RBAC**: **OTel Collector** **ServiceAccount** needs `get`, `list`, `watch` on pods, events, and nodes.
• Splunk RBAC: users running sidecar health searches need **`srchIndexesAllowed`** including `containers`; assign via a custom role (`mesh_observer`).
• **License estimate**: Envoy sidecar stats produce ~1–3 KB per pod per scrape; a 200-pod mesh at 15s intervals generates ~30–80 MB/day of sidecar metrics; **access logs** add ~2 KB per request.

Step 1 — Configure data collection
(1) **Envoy sidecar scraping**: the key metrics to validate in the scrape are:
— **`envoy_server_live`** (gauge: 1 = live, 0 = not live — the most fundamental health indicator)
— **`envoy_server_state`** (gauge: 0 = LIVE, 1 = DRAINING, 2 = PRE_INITIALIZING, 3 = INITIALIZING — maps to Envoy's **server lifecycle states**)
— **`envoy_server_uptime`** (counter: seconds since Envoy process started — low values indicate recent restarts)
— **`envoy_server_concurrency`** (gauge: number of worker threads — should match the pod's CPU limit or **Istio**'s `proxy.concurrency` setting)
Verify by querying a sidecar directly: `kubectl exec <pod> -c istio-proxy -- curl -s localhost:15000/stats | grep server.live`.

(2) **Container status collection**: ensure **`sourcetype=kube:container:status`** includes the `istio-proxy` container's ready state and restart count. The OTel Collector's **`k8sobjects`** receiver or **Splunk Connect for Kubernetes** captures this from the Kubernetes API.

(3) **Envoy access logs**: Istio configures Envoy to emit **JSON access logs** to stdout by default. The **`response_flags`** field in these logs indicates proxy-level errors that are invisible in application metrics:
— **UF** (upstream connection failure), **UH** (no healthy upstream), **UC** (upstream connection termination) indicate the proxy cannot reach the destination
— **LR** (local reset), **UR** (upstream reset) indicate connection resets
— **UO** (upstream overflow) indicates **circuit breaker** trips
— **NR** (no route configured) indicates mesh **routing misconfiguration**
Collect as **`sourcetype=istio:accesslog`** via the OTel **`filelog`** receiver or Splunk Connect for Kubernetes.

(4) **Kubernetes events**: ensure **`sourcetype=kube:events`** captures events with reasons `BackOff`, `Killing`, `Unhealthy`, `FailedMount`, and `Created` for the `istio-proxy` container — these correlate sidecar restarts with Kubernetes-level lifecycle actions.

Step 2 — Create the search and alert
The primary SPL tracks four **Envoy server metrics** to classify each sidecar's health. The `server_state` gauge maps numerically to Envoy's lifecycle: 0 = LIVE (healthy, serving traffic), 1 = DRAINING (graceful shutdown, rejecting new connections), 2–3 = initializing (starting up). Combined with `server_live` and uptime, this produces a precise health classification.

The **`staleness_min`** field detects sidecars that have stopped reporting metrics entirely — a common failure mode when the sidecar crashes or the scrape target becomes unreachable. Any sidecar with > 10 minutes of staleness gets flagged as `STALE`.

The event-correlation variant joins sidecar health issues with **Kubernetes events** to provide context: was the sidecar killed by an OOM event? Did injection fail? Is it stuck in **CrashLoopBackOff**?

The **response-flag variant** analyzes Envoy access logs to quantify proxy-level failures by destination service — a spike in UF/UH flags for a specific service means the proxy cannot reach that destination, even if the destination is technically healthy.

Schedule the sidecar health search every **5 minutes** over **`-5m@m`**; alert on any sidecar in UNHEALTHY or STALE state for more than **2 consecutive runs**. Schedule the **response-flag** search every **15 minutes** over **`-15m`** and alert when any flag exceeds **50 occurrences**.

Step 3 — Validate
(a) Verify metrics: `index=containers sourcetype=otel:metrics metric_name=envoy_**server_live** earliest=-5m | stats dc(pod) as sidecars`. Should match the count of sidecar-injected pods: `kubectl get pods --all-namespaces -l security.istio.io/tlsMode=istio -o name | wc -l`.
(b) Test an unhealthy sidecar: scale a deployment to zero and back to trigger a sidecar restart; verify the search surfaces the pod with `RECENTLY_RESTARTED` status.
(c) Verify response flags: `index=containers sourcetype="istio:accesslog" response_flags!="-" earliest=-1h | stats count by response_flags`. Should return rows if any proxy-level errors occurred.
(d) Cross-check with Istio: `istioctl proxy-status` shows sidecar sync state; compare the count of **SYNCED** proxies with the count of HEALTHY sidecars in the Splunk search.
(e) Confirm event correlation: `index=containers sourcetype="kube:events" earliest=-1h | search "istio-proxy" | stats count by reason`. Should capture sidecar-specific events.

Step 4 — Operationalize dashboards and runbooks
• Row A: **single-value tiles** — healthy sidecar % (green > 99%, yellow > 95%, red ≤ 95%), unhealthy count, stale count, recently restarted count.
• Row B: **sortable table** of unhealthy sidecars — columns: pod_name, ns, cluster_name, status_flag, state_label, uptime_hours, **staleness_min**. Drilldown opens pod detail.
• Row C: **timechart** of sidecar restarts by namespace over 4 hours to spot namespace-level patterns.
• Row D: **bar chart** of response flags by destination service from the access-log variant — immediately shows which services have proxy-level reachability problems.
• **Alerting**: sidecar UNHEALTHY/STALE > 2 consecutive checks → **PagerDuty** P2 with pod name and namespace; response flag spike (UF/UH > 50 in 15m) → Slack `#sre-mesh`; sidecar healthy% < 95% cluster-wide → PagerDuty P1.
• **Runbook** (owner: SRE mesh on-call): (1) check if the pod's application container is also unhealthy: `kubectl describe pod <pod> -n <ns>`, (2) check Envoy admin: `kubectl exec <pod> -c istio-proxy -- curl -s localhost:15000/server_info`, (3) check for injection issues: `istioctl analyze -n <ns>`, (4) for UF/UH flags: verify the destination service exists and has healthy endpoints.

Step 5 — Visualization, alert design, and troubleshooting
• **Visualization**: use a **status grid** (**Dashboard Studio** colored tiles) showing each pod's sidecar health as green/yellow/red squares organized by namespace — gives an instant mesh-health overview; pair with a **response-flag heatmap** showing flag type × destination service × time to reveal temporal patterns.
• **Alert design**: include `pod_name`, `ns`, `cluster_name`, `status_flag`, `state_label`, `uptime_hours`, `staleness_min`, and for response-flag alerts include `flag_meaning`, `dest_svc`, and `flag_count`; add a deep-link to the pod-detail dashboard.
• **All sidecars show STALE** — the OTel Collector may have lost connectivity to the metrics backend or the **Prometheus receiver** **scrape config** is misconfigured; check collector logs: `kubectl logs -n splunk-otel -l app=splunk-otel-collector -c otel-collector | grep -i error`.
• **Sidecar shows DRAINING but pod is Running** — normal during **rolling deployments** or when Istio is being upgraded; the old sidecar drains before the new one takes over. Suppress DRAINING alerts for 5 minutes after deployment events.
• **Response flags show UH for a service that is healthy** — the Envoy sidecar may have stale endpoints; check `istioctl proxy-config endpoint <pod> --cluster <service>` for the endpoint list. An empty list means the sidecar has not received the endpoint update from **istiod**.
• **`envoy_server_concurrency` is 0** — the sidecar is in the process of shutting down or has not finished initializing; correlate with `envoy_server_state` to confirm.
• **Sidecar version mismatch** — after an **Istio control-plane upgrade**, sidecars running the old proxy version may exhibit degraded health until the workload is restarted with the new sidecar image; check `istioctl proxy-status` for version column discrepancies.
• **High restart count but no Kubernetes events** — events may have aged out of the Kubernetes API (default 1h TTL); increase the event collector's poll frequency or check the **kubelet** logs on the node directly.

## SPL

```spl
`comment("--- Envoy Sidecar Health — Not-Ready, Crash-Looping, and Draining Proxies ---")`
index=containers (sourcetype="otel:metrics" OR sourcetype="prometheus:istio")
| where match(metric_name, "envoy_server_(live|state|uptime|concurrency)")
| eval pod_name=coalesce(pod, exported_pod, label_pod, "unknown")
| eval ns=coalesce(namespace, exported_namespace, label_namespace, "unknown")
| eval cluster_name=coalesce(cluster, cluster_name, "default")
| eval metric=coalesce(metric_name, name)
| eval val=tonumber(value)
| stats latest(eval(if(metric="envoy_server_live", val, null()))) as server_live,
    latest(eval(if(metric="envoy_server_state", val, null()))) as server_state,
    latest(eval(if(match(metric, "envoy_server_uptime"), val, null()))) as uptime_sec,
    latest(eval(if(match(metric, "envoy_server_concurrency"), val, null()))) as worker_threads,
    latest(_time) as last_seen
    by pod_name, ns, cluster_name
| eval state_label=case(
    server_state=0, "LIVE",
    server_state=1, "DRAINING",
    server_state=2, "PRE_INITIALIZING",
    server_state=3, "INITIALIZING",
    1=1, "UNKNOWN")
| eval is_healthy=if(server_live=1 AND state_label="LIVE" AND uptime_sec > 60, 1, 0)
| eval uptime_hours=round(uptime_sec / 3600, 2)
| eval staleness_min=round((now() - last_seen) / 60, 1)
| eval status_flag=case(
    staleness_min > 10, "STALE — no recent metrics",
    is_healthy=0 AND state_label="DRAINING", "DRAINING — sidecar shutting down",
    is_healthy=0, "UNHEALTHY — ".state_label,
    uptime_hours < 0.5, "RECENTLY_RESTARTED",
    1=1, "HEALTHY")
| where status_flag != "HEALTHY"
| sort -staleness_min
| table pod_name ns cluster_name status_flag state_label server_live uptime_hours worker_threads staleness_min last_seen

`comment("--- Sidecar Restart Correlation with Kubernetes Events ---")`
index=containers sourcetype="kube:events" (reason="BackOff" OR reason="Killing" OR reason="Unhealthy" OR reason="FailedMount" OR reason="Created")
| eval ns=coalesce(namespace, object_namespace, involvedObject.namespace)
| eval pod_name=coalesce(involvedObject.name, object_name, involved_object_name)
| eval container=coalesce(involvedObject.fieldPath, "")
| where match(container, "istio-proxy") OR match(container, "envoy") OR match(pod_name, "istio")
| stats count as event_count,
    values(reason) as reasons,
    latest(message) as last_message,
    latest(_time) as last_event
    by ns, pod_name
| sort -event_count
| head 50
| table ns pod_name event_count reasons last_message last_event

`comment("--- Envoy Response Flag Analysis — Proxy-Level Error Breakdown ---")`
index=containers sourcetype="istio:accesslog"
| eval response_flag=coalesce(response_flags, "-")
| where response_flag != "-"
| eval flag_meaning=case(
    response_flag="UF", "upstream_connection_failure",
    response_flag="UH", "no_healthy_upstream",
    response_flag="UC", "upstream_connection_termination",
    response_flag="LR", "local_reset",
    response_flag="UR", "upstream_reset",
    response_flag="UO", "upstream_overflow_circuit_breaker",
    response_flag="NR", "no_route_configured",
    response_flag="DT", "downstream_timeout",
    response_flag="DC", "downstream_connection_termination",
    response_flag="RL", "rate_limited",
    1=1, response_flag)
| eval dest_svc=coalesce(upstream_cluster, authority, "unknown")
| stats count as flag_count by flag_meaning, dest_svc
| sort -flag_count
| head 50
| table flag_meaning dest_svc flag_count
```

## Visualization

Sortable pod-health table with status flags, event-correlation timeline, response-flag bar chart by destination service, single-value tiles (healthy %, unhealthy count, recently restarted count).

## Known False Positives

**rolling_upgrade_drain** — During Istio or application rolling upgrades, sidecars transition through DRAINING and PRE_INITIALIZING states as old pods terminate and new pods start. This is expected lifecycle behavior, not a failure. Suppress DRAINING/INITIALIZING alerts for 10 minutes after detecting a corresponding deployment ScalingReplicaSet event in the same namespace.

**node_scale_down_eviction** — When a Kubernetes node is drained for maintenance or autoscaler scale-down, all sidecars on that node briefly show as STALE before pods are rescheduled. Correlate staleness with `sourcetype=kube:events reason=Evicted` or `reason=NodeNotReady` and suppress during planned maintenance windows.

**scrape_target_lag** — The Prometheus receiver discovers new sidecar scrape targets via Kubernetes service discovery, which has a propagation delay of 5–30 seconds. Newly created pods may appear as STALE until the first successful scrape. Ignore staleness alerts for pods less than 2 minutes old based on `kube_pod_created` timestamp.

**response_flag_health_check** — Kubernetes liveness and readiness probes routed through the Envoy sidecar can generate UF or DC response flags when the application takes longer than the probe timeout to respond. These probe-induced flags inflate the error count without representing real traffic failures. Filter by excluding requests to known probe paths.

**concurrency_mismatch_noise** — The `envoy_server_concurrency` metric may differ from the pod's CPU limit when Istio's `proxy.concurrency` is explicitly set in the mesh config or pod annotation. A value of 0 during initialization is expected and resolves within seconds. Only alert on sustained concurrency=0 lasting more than 60 seconds.

**istio_cni_injection_delay** — When using Istio CNI instead of init containers for sidecar injection, there is a brief window during pod startup where the sidecar is not yet configured. Metrics show PRE_INITIALIZING state during this window. Allow 30 seconds of PRE_INITIALIZING before alerting.

## References

- [Envoy Server Statistics — Live, State, Uptime](https://www.envoyproxy.io/docs/envoy/latest/configuration/observability/statistics)
- [Istio — Envoy Access Log Response Flags](https://www.envoyproxy.io/docs/envoy/latest/configuration/observability/access_log/usage)
- [Istio Sidecar Injection — Troubleshooting](https://istio.io/latest/docs/ops/common-problems/injection/)
- [Splunk OpenTelemetry Collector for Kubernetes](https://github.com/signalfx/splunk-otel-collector-chart)
- [Kubernetes Pod Lifecycle — Container States](https://kubernetes.io/docs/concepts/workloads/pods/pod-lifecycle/)
