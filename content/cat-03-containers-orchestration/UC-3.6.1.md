<!-- AUTO-GENERATED from UC-3.6.1.json — DO NOT EDIT -->

---
id: "3.6.1"
title: "Pod Restart Rate Trending"
status: "verified"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-3.6.1 · Pod Restart Rate Trending

## Description

Tracks the **`kube_pod_container_status_restarts_total`** counter across every namespace and pod, computing daily restart deltas, 7-day simple moving averages, and 30-day baselines to surface rising instability trends — then correlates spikes with **`kube_pod_container_status_last_terminated_reason`** and Kubernetes events to classify root causes as OOMKilled, CrashLoopBackOff, eviction, or bad-rollout patterns.

## Value

Pod restarts are the earliest signal that workloads are silently failing: each restart burns CPU on container init, drops in-flight requests, and resets connection pools. A steadily rising restart trend that goes unnoticed compounds into SLO violations, wasted compute, and on-call fatigue. Surfacing the trend and its cause at the cluster level gives platform teams evidence to prioritize fixes — whether that means raising memory limits, fixing a liveness probe, or rolling back a deployment.

## Implementation

Deploy the Splunk OpenTelemetry Collector with a Prometheus receiver scraping kube-state-metrics to collect kube_pod_container_status_restarts_total counters into index=containers. Build three search variants: cluster-wide 30-day trending with 7-day SMA and spike detection, namespace-level restart anomaly breakdown, and pod-level restart burst correlation with termination reasons from kube:events. Alert when cluster-wide daily restarts exceed the 7-day moving average by 50% or when any namespace sees > 5 restarts affecting > 3 pods.

## Detailed Implementation

Prerequisites
• **kube-state-metrics** 2.8+ deployed as a Deployment in the **kube-system** or dedicated monitoring namespace, exposing the **`kube_pod_container_status_restarts_total`** counter, **`kube_pod_container_status_last_terminated_reason`** gauge, and **`kube_pod_status_phase`** gauge on its **metrics service port** (default 8080).
• **Splunk OpenTelemetry Collector** deployed as a **DaemonSet** via the `splunk-otel-collector-chart` **Helm chart** with the **Prometheus receiver** configured to discover and scrape the **kube-state-metrics** endpoint via **Kubernetes service discovery**; **scrape interval** of **15–30 seconds** balances resolution against volume.
• **Splunk HEC** token provisioned for **`index=containers`** with default **`sourcetype=otel:metrics`**; secondary stream for **`sourcetype=kube:events`** via Splunk Connect for Kubernetes or the OTel **`k8s_events`** receiver; optional third stream for **`sourcetype=kube:pod:logs`** crash logs.
• **Metrics index**: `index=containers` must be configured as a **metrics index** (not an **events index**) if you use the **`mstats`**-based primary search; the namespace/pod-level variants work against either events or **metrics index**es. Verify with `| mcatalog values(metric_name) WHERE index=containers metric_name=kube_pod*`.
• **Kubernetes RBAC**: the **OTel Collector** **ServiceAccount** needs `get`, `list`, `watch` on pods, events, and nodes for both metric discovery and event collection.
• Splunk RBAC: users running restart searches need **`srchIndexesAllowed`** including `containers`; assign via a custom role (`k8s_platform_observer`).
• **License estimate**: kube-state-metrics produces ~0.5–2 KB per pod per scrape; a 500-pod cluster at 15s intervals generates ~50–100 MB/day of metric events; kube:events adds ~1–5 MB/day depending on cluster activity.

Step 1 — Configure data collection
(1) **kube-state-metrics scraping**: verify the OTel Collector Prometheus receiver includes a scrape config targeting the kube-state-metrics service. The default `splunk-otel-collector-chart` discovers kube-state-metrics via pod annotations or a static service-name match. Verify: `kubectl get svc -n kube-system | grep kube-state-metrics` then check the collector config for a matching **`job_name`** entry. The key metrics to validate are present in the scrape:
— **`kube_pod_container_status_restarts_total`** (**monotonic counter**; increments on each container restart)
— **`kube_pod_container_status_last_terminated_reason`** (gauge labeled by `reason`: OOMKilled, Error, Completed, Evicted)
— **`kube_pod_status_phase`** (gauge labeled by `phase`: Pending, Running, Succeeded, Failed, Unknown)
— **`kube_pod_container_status_waiting_reason`** (gauge labeled by `reason`: CrashLoopBackOff, ImagePullBackOff, CreateContainerError)
Each metric carries labels: `namespace`, `pod`, `container`, `uid` — the SPL uses `coalesce` chains to handle label-name variations between OTel Collector versions and direct Prometheus paths.

(2) **Kubernetes event collection**: ensure `sourcetype=kube:events` captures events with reasons **BackOff**, **OOMKilling**, **Killing**, **Evicted**, **Preempted**, **FailedScheduling**. These events carry `involved_object_name` (pod name), `namespace`, `reason`, and a free-text `message` that provides human-readable context. Events are ephemeral in the Kubernetes API (default 1h TTL) — the collector must poll frequently or use a watch stream.

(3) **Crash log collection** (optional): configure the OTel `filelog` receiver or Splunk Connect for Kubernetes to capture container stdout/stderr as `sourcetype=kube:pod:logs`. When a container crashes, its last log lines before termination reveal the root cause (stack traces, OOM messages, segfaults). Pair crash logs with restart events using `pod` and `container` as join keys.

(4) **Namespace exclusion lookup**: create `excluded_namespaces.csv` with column `namespace` listing system namespaces you want to exclude from alerting (e.g., `kube-system`, `istio-system`, `monitoring`, `cert-manager`). Define the lookup in **`transforms.conf`** and reference it in the namespace-level search with `| lookup excluded_namespaces namespace OUTPUT excluded | where isnull(excluded)`.

Step 2 — Create the search and alert
The primary search uses `mstats` to query the **`kube_pod_container_status_restarts_total`** **monotonic counter** directly from the metrics index. Because this counter only increments, the daily delta represents new restarts in each 24-hour window. The **`trendline sma7`** command computes a 7-day simple moving average to smooth daily variance, and the **`deviation_pct`** field measures how far today's count is from the rolling average.

The **`alert_flag`** fires when daily restarts exceed 1.5× the 7-day SMA AND the absolute count exceeds 10 — the absolute floor prevents alerts on clusters with near-zero normal restarts where a single pod restart would be a 150% spike.

The namespace-level variant uses `stats` to compute restart deltas per namespace and pod, surfacing which namespaces are contributing most restarts and how many distinct pods are affected. The `affected_pods > 3` filter distinguishes systemic namespace issues from a single crashlooping pod.

The pod-level variant joins termination-reason metrics with Kubernetes events to classify each restart: **OOMKilled** points to **memory limits**, **Error** suggests application bugs, **BackOff** indicates repeated **crash-restart cycles**, **Evicted** signals **node resource pressure**.

Schedule the cluster-wide search daily at **06:00** over **`-30d@d`** for trending and once every **4 hours** over **`-4h`** for spike detection. Schedule the namespace search every **1 hour** over **`-1h`** and alert when any non-excluded namespace shows **> 5 restarts affecting > 3 pods**. Schedule the pod-level search every **15 minutes** over **`-1h`** and alert on any pod with **> 3 restarts** in the window.

Step 3 — Validate
(a) Verify metric presence: `| mcatalog values(metric_name) WHERE index=containers metric_name=kube_pod_container_status_restarts_total` should return at least one metric name. If empty, confirm the metrics index type and that kube-state-metrics is being scraped.
(b) Cross-check with kubectl: `kubectl get pods --all-namespaces --field-selector=status.phase!=Running -o wide` and `kubectl get events --all-namespaces --field-selector reason=BackOff` — the restart counts and events in Splunk should match within one scrape interval of lag.
(c) Create a test restart: `kubectl run restart-test --image=busybox --restart=Always -- /bin/sh -c 'exit 1'` — the pod will crash-loop and restarts should appear in both the mstats and events searches within 2–3 minutes. Clean up: `kubectl delete pod restart-test`.
(d) Validate **namespace exclusion**: add `kube-system` to `excluded_namespaces.csv` and verify the namespace-level search no longer returns kube-system pods.
(e) Confirm trend calculation: the 30-day search should produce a line chart with the `sma_7d` line smoothing daily fluctuations. If the trend line is flat at zero, verify the time range covers enough data and that `mstats` is returning non-zero values.

Step 4 — Operationalize dashboards and runbooks
• Row A: **line chart** of `cluster_total` (daily restarts) with **`sma_7d`** overlay over 30 days — the SMA line reveals the trend direction while daily bars show spikes.
• Row B: **single-value tiles** — today's restart count (red if > 1.5× SMA), 7-day SMA, deviation %, count of namespaces with active spikes, most-restarting namespace name.
• Row C: **stacked area chart** of restarts by namespace over 7 days — immediately shows which namespace contributes most to a cluster-wide spike.
• Row D: **sortable table** of pod-level restarts — columns: namespace, pod_name, reason, reason_count, event_count, last_message, last_seen. Drilldown opens pod crash logs.
• **Alerting**: cluster-wide spike (> 1.5× SMA) → Slack `#platform-ops`; namespace burst (> 5 restarts, > 3 pods) → PagerDuty P3 tagged with namespace; individual pod > 3 restarts in 1h → PagerDuty P2 with pod name and **termination reason**.
• **Runbook** (owner: platform engineering on-call): (1) identify the namespace and pod from the alert, (2) check termination reason — OOMKilled → increase memory limits or investigate leak; Error → check pod logs; CrashLoopBackOff → check **liveness probe** config and application startup time, (3) check if a **deployment rollout** is in progress: `kubectl rollout status deploy/<name> -n <ns>`, (4) check node resource pressure: `kubectl top nodes`.

Step 5 — Visualization, alert design, and troubleshooting
• **Visualization**: use a **dual-axis chart** with daily restart count as bars (left axis) and 7-day SMA as an overlaid line (right axis) to separate daily variance from the trend; add a **treemap** sized by **`ns_restarts`** and colored by **`affected_pods`** to show namespace-level impact at a glance; include a **timeline** panel correlating restart spikes with deployment events from `sourcetype=kube:events reason=ScalingReplicaSet`.
• **Alert design**: include `cluster_name`, `namespace`, `pod_name`, `reason`, **`deviation_pct`**, `cluster_total`, and `sma_7d` in the alert payload; for pod-level alerts include the last termination `message` truncated to 200 chars; add a deep-link to the dashboard filtered to the alerting namespace and time window.
• **mstats returns no results** — verify `index=containers` is a metrics index: `| eventcount summarize=false index=containers` versus `| mcatalog values(metric_name) WHERE index=containers`; if events exist but mstats returns nothing, the data was indexed as events rather than metrics — check the HEC token's `index` and `sourcetype` configuration.
• **Restart counts never increase** — kube-state-metrics may not be running or may not be scraped; verify: `kubectl get pods -n kube-system -l app.kubernetes.io/name=kube-state-metrics`; check the OTel Collector logs for scrape errors on the kube-state-metrics target.
• **All restarts show in kube-system** — some OTel Collector configurations scrape the kubelet summary API which reports system containers; exclude system namespaces via the lookup or filter `ns!=kube-system` in the SPL.
• **Termination reason is always "unknown"** — the **`kube_pod_container_status_last_terminated_reason`** metric may not be enabled in your kube-state-metrics config; verify with `curl <ksm-endpoint>/metrics | grep terminated_reason`.
• **Event join returns empty** — Kubernetes events have a short TTL (default 1h); if the event collector polls less frequently or if events aged out before collection, the join finds no matches. Increase the **event TTL** or reduce the collector poll interval.
• **Spike alert fires on every deployment** — rolling deployments naturally restart pods; add a deployment-event correlation window that suppresses alerts for 15 minutes after a `ScalingReplicaSet` event in the same namespace using a **`maintenance_windows`** lookup or a **correlation search**.

## SPL

```spl
`comment("--- Pod Restart Rate Trending — Cluster-Wide 30-Day Baseline ---")`
| mstats latest(kube_pod_container_status_restarts_total) as restarts WHERE index=containers by namespace, pod, container span=1d
| eval daily_restart_delta=restarts
| stats sum(daily_restart_delta) as daily_restarts by _time, namespace
| timechart span=1d sum(daily_restarts) as total_restarts by namespace limit=20
| addtotals fieldname=cluster_total
| trendline sma7(cluster_total) as sma_7d
| eval baseline_30d=avg(cluster_total)
| eval deviation_pct=round(100 * (cluster_total - sma_7d) / max(sma_7d, 1), 1)
| eval alert_flag=if(cluster_total > sma_7d * 1.5 AND cluster_total > 10, "SPIKE", "normal")
| fields _time cluster_total sma_7d deviation_pct alert_flag *

`comment("--- Namespace-Level Restart Rate Anomaly Detection ---")`
index=containers (sourcetype="otel:metrics" OR sourcetype="prometheus:kube")
| where match(metric_name, "kube_pod_container_status_restarts_total")
| eval ns=coalesce(namespace, exported_namespace, label_namespace, "unknown")
| eval pod_name=coalesce(pod, exported_pod, label_pod, "unknown")
| eval container_name=coalesce(container, label_container, "unknown")
| eval cluster_name=coalesce(cluster, cluster_name, "default")
| eval restart_count=tonumber(value)
| stats max(restart_count) as max_restarts, min(restart_count) as min_restarts by ns, pod_name, container_name, cluster_name
| eval delta_restarts=max_restarts - min_restarts
| where delta_restarts > 0
| stats sum(delta_restarts) as ns_restarts,
    dc(pod_name) as affected_pods,
    dc(container_name) as affected_containers,
    values(pod_name) as restarting_pods
    by ns, cluster_name
| sort -ns_restarts
| where ns_restarts > 5 OR affected_pods > 3
| table ns cluster_name ns_restarts affected_pods affected_containers restarting_pods

`comment("--- Pod-Level Restart Burst with Termination Reason ---")`
index=containers (sourcetype="otel:metrics" OR sourcetype="prometheus:kube")
| where match(metric_name, "kube_pod_container_status_last_terminated_reason")
| eval ns=coalesce(namespace, exported_namespace, "unknown")
| eval pod_name=coalesce(pod, exported_pod, "unknown")
| eval reason=coalesce(reason, label_reason, "unknown")
| where tonumber(value) > 0
| stats count as reason_count, latest(_time) as last_seen by ns, pod_name, reason
| join type=left pod_name ns [search index=containers sourcetype="kube:events" reason IN ("BackOff", "OOMKilling", "Killing", "Evicted", "Preempted") earliest=-24h
    | eval ns=coalesce(namespace, object_namespace)
    | eval pod_name=coalesce(involved_object_name, object_name)
    | stats count as event_count, latest(message) as last_message by ns, pod_name, reason]
| table ns pod_name reason reason_count event_count last_message last_seen
| sort -reason_count
```

## Visualization

Line chart (daily restarts + 7-day SMA trend over 30 days), stacked area by namespace, single-value tiles (cluster total, deviation %, spike count), sortable pod-restart table with termination reason and event message.

## Known False Positives

**rolling_deployment_restart** — Every Kubernetes rolling deployment replaces pods by terminating old replicas and starting new ones, which increments the restart counter for the old containers. During a busy deployment window affecting 10+ services, the cluster-wide restart count spikes without indicating instability. Correlate with `sourcetype=kube:events reason=ScalingReplicaSet` and suppress alerts for 15 minutes after deployment events in the same namespace.

**liveness_probe_tuning** — Overly aggressive liveness probes (short `initialDelaySeconds`, tight `timeoutSeconds`) cause healthy but slow-starting containers to be killed and restarted repeatedly. The restart counter climbs but the application is functioning correctly once warm. Check liveness probe configuration: `kubectl describe pod <pod> | grep Liveness` and adjust thresholds before treating the restarts as failures.

**node_drain_churn** — When nodes are cordoned and drained for maintenance or autoscaler scale-down, all pods on those nodes are evicted and rescheduled, producing a burst of restarts concentrated in the drain window. Compare restart spikes with node lifecycle events: `sourcetype=kube:events reason=Evicted` or `reason=NodeNotReady` and suppress during planned maintenance.

**oom_kill_resource_sizing** — Containers running near their memory limits may be OOMKilled by the kernel during transient load spikes. The restart counter increments but the application recovers immediately after restart. Distinguish genuine memory leaks (steadily rising restarts over days) from transient OOMs (isolated spikes) by checking whether the same pod appears in consecutive alert windows.

**hpa_scale_down_restart** — When a HorizontalPodAutoscaler scales down a deployment, surplus pods are terminated, incrementing the restart counter for those containers. This is normal autoscaler behavior, not instability. Filter by checking whether `kube_pod_status_phase` transitions to `Succeeded` (graceful termination) rather than `Failed` (crash).

**preemption_spot_instance** — Pods running on preemptible or spot instance nodes are terminated when the cloud provider reclaims the node. Restarts from preemption are expected cost-optimization behavior, not application instability. Identify preemption restarts by correlating with node labels (`node.kubernetes.io/instance-type` containing `spot` or `preemptible`) or event reason `Preempted`.

## References

- [kube-state-metrics — Pod Metrics Reference](https://github.com/kubernetes/kube-state-metrics/blob/main/docs/pod-metrics.md)
- [Kubernetes — Container Restart Policy](https://kubernetes.io/docs/concepts/workloads/pods/pod-lifecycle/#restart-policy)
- [Splunk OpenTelemetry Collector for Kubernetes — Helm Chart](https://github.com/signalfx/splunk-otel-collector-chart)
- [Kubernetes — Pod Lifecycle and Termination](https://kubernetes.io/docs/concepts/workloads/pods/pod-lifecycle/)
- [Splunk Metrics — mstats Command Reference](https://docs.splunk.com/Documentation/Splunk/latest/SearchReference/Mstats)
