<!-- AUTO-GENERATED from UC-3.5.17.json — DO NOT EDIT -->

---
id: "3.5.17"
title: "Kubernetes Resource Quota and LimitRange Compliance"
status: "verified"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-3.5.17 · Kubernetes Resource Quota and LimitRange Compliance

## Description

Monitors **Kubernetes ResourceQuota** utilization percentages (CPU, memory, pods) per namespace against tiered thresholds (CRITICAL at 95%, HIGH at 85%, WARNING at 70%), detects **quota exhaustion events** where pod creation was rejected because the namespace exceeded its resource limits, and forecasts quota utilization growth via a **30-day trend** with 7-day SMA — enabling platform teams to proactively adjust quotas before deployment failures cascade.

## Value

Resource quotas are the guardrails that prevent any single team from consuming the entire cluster, but they become invisible walls when approached. A deployment that worked yesterday fails today because the namespace quietly consumed 96% of its CPU quota overnight as a batch job scaled up. The deployment controller silently retries, no alarm fires, and the team discovers the failure minutes later when users report the rollout stalled. Monitoring quota utilization with tiered thresholds gives the platform team advance warning, while tracking quota exhaustion events provides the forensic evidence to understand which workloads consumed the remaining capacity.

## Implementation

Collect ResourceQuota objects via the OTel Collector k8sobjects receiver and kube-state-metrics via the Prometheus receiver into index=containers. Build three search variants: quota utilization risk assessment with bottleneck identification, quota exhaustion event detection from FailedCreate/Forbidden warnings, and 30-day utilization growth trend with SMA forecasting. Alert when any namespace reaches CRITICAL or HIGH risk.

## Detailed Implementation

Prerequisites
• **Kubernetes cluster** with **ResourceQuota** objects configured per namespace. ResourceQuotas define **hard limits** on aggregate resource consumption within a namespace — **CPU requests**, **memory requests**, **CPU limits**, **memory limits**, **pod count**, **service count**, **PersistentVolumeClaim count**, **ConfigMap count**, and **Secret count**. The **Kubernetes API server** enforces these limits at **admission time** — any pod creation that would cause the namespace to exceed its quota is rejected.
• **LimitRange** objects optionally configured per namespace. LimitRanges define **per-container** and **per-pod** defaults, minimums, and maximums for CPU and memory requests/limits. When a pod does not specify resource requests or limits, the **LimitRange admission controller** injects the **default values**. Pods that specify values outside the min/max range are rejected.
• **Splunk Distribution of OpenTelemetry Collector** deployed with:
  — **k8sobjects receiver**: configured to collect **ResourceQuota** and **LimitRange** objects from the Kubernetes API. Polling interval: 60 seconds.
  — **Prometheus receiver**: scraping **kube-state-metrics** for real-time **`kube_resourcequota`** gauge metrics with `resource`, `type` (hard/used), and `namespace` labels.
• **Splunk HEC** token for **`index=containers`** with sourcetype routing for **`kube:objects:resourcequotas`**, **`kube:objects:limitranges`**, **`kube:events`**, **`kube:pod:status`**, and **`otel:metrics`**.
• **kube-state-metrics** v2.0+ deployed in the cluster. This component exposes **Prometheus metrics** for Kubernetes objects including ResourceQuotas, LimitRanges, and pod resource specifications. The OTel Collector scrapes these metrics and forwards them to Splunk.
• **Namespace inventory**: maintain a **lookup** (`namespace_metadata.csv`) mapping each namespace to its **owning team**, **environment** (production, staging, development), **tier** (critical, standard, best-effort), and **contact channel** (Slack, email). This enables risk-appropriate alerting — a CRITICAL quota breach in a production namespace requires immediate response, while the same breach in a development namespace is informational.
• **License estimate**: ResourceQuota objects are small (~1 KB each). A cluster with 50 namespaces generates approximately 50 events per poll cycle × 1440 cycles/day = ~72,000 events/day (~70 MB). kube-state-metrics quota gauges add approximately 10–50 MB/day.
• Splunk RBAC: assign a **`platform_analyst`** role with **`srchIndexesAllowed`** including `containers`.

Step 1 — Configure data collection
(1) **k8sobjects receiver configuration**: configure the OTel Collector to collect **ResourceQuota** objects:
```yaml
receivers:
  k8sobjects:
    objects:
    - name: resourcequotas
      mode: pull
      interval: 60s
    - name: limitranges
      mode: pull
      interval: 300s
```

The receiver emits each ResourceQuota as a structured JSON event containing:
  — **`metadata.namespace`**: the namespace
  — **`metadata.name`**: the quota name
  — **`spec.hard`**: the configured hard limits (e.g., `{"cpu": "4", "memory": "8Gi", "pods": "20"}`)
  — **`status.hard`**: the enforced hard limits (same as spec.hard unless modified by admission webhooks)
  — **`status.used`**: the current aggregate usage across all pods in the namespace

(2) **kube-state-metrics scraping**: configure the **Prometheus receiver** to scrape kube-state-metrics:
  — **`kube_resourcequota`**: gauge with labels `namespace`, `resourcequota`, `resource` (cpu, memory, pods, etc.), and `type` (hard, used)
  — **`kube_limitrange`**: gauge with labels for default, min, max, and type per resource
  This provides **high-resolution** (15-second) quota utilization data compared to the 60-second object polling.

(3) **Quota exhaustion events**: the **k8s_events receiver** already collects Warning events (configured in UC-3.5.16). Quota exhaustion events have specific patterns:
  — **Reason**: `FailedCreate` — a **ReplicaSet** or **Job** could not create a pod because the namespace **exceeded its quota**
  — **Reason**: `Forbidden` — the **API server admission webhook** rejected the request
  — **Message pattern**: `"exceeded quota: <quota-name>, requested: cpu=500m, used: cpu=3500m, limited: cpu=4"`

(4) **Pod resource specification collection**: collect **`sourcetype=kube:pod:status`** with container-level resource requests and limits. This enables **LimitRange compliance** checking — comparing each pod's resource specifications against the namespace's LimitRange constraints to identify pods that were admitted with default values versus pods that explicitly specified resources.

(5) **Resource unit normalization**: Kubernetes expresses CPU in **millicores** (e.g., `500m` = 0.5 cores) and memory in **binary units** (e.g., `256Mi`, `1Gi`). The SPL must handle these unit conversions. The k8sobjects receiver preserves the original string values — use `eval` with `tonumber()` and unit conversion logic to produce comparable percentages.

Step 2 — Create the search and alert
The primary SPL processes **ResourceQuota** objects to compute utilization percentages for CPU, memory, and pod count. The **risk** classification:
  — **CRITICAL** (≥95%): the namespace is nearly exhausted — the next deployment will likely fail
  — **HIGH** (≥85%): approaching exhaustion — proactive intervention required
  — **WARNING** (≥70%): elevated utilization — monitor closely
  — **NOTICE** (≥50%): moderate usage — informational

The **bottleneck** field identifies which resource dimension is closest to exhaustion — this tells the platform team whether to increase the **CPU quota**, **memory quota**, or **pod count quota**.

The quota exhaustion event SPL detects actual **rejection events** using regex extraction to parse the quota name, requested amount, current usage, and limit from the event message. This provides the forensic evidence that deployments are failing due to quota exhaustion.

The 30-day trend SPL computes **daily average utilization** for CPU and memory, then applies a **7-day SMA** to smooth daily fluctuations and reveal the underlying growth trajectory. This enables **forecasting** — if the SMA shows steady growth of 2% per week, the platform team can predict when the namespace will hit the quota limit.

Schedule the utilization risk search every **15 minutes** and alert on CRITICAL (PagerDuty P2) or HIGH (Slack). Schedule the exhaustion event search every **5 minutes** and alert on any rejection. Schedule the trend search **daily** and send a weekly capacity report.

Step 3 — Validate
(a) Verify quota data: `index=containers sourcetype="kube:objects:resourcequotas" earliest=-1h | spath | stats dc(metadata.namespace) as namespaces, dc(metadata.name) as quotas`. Should match the number of namespaces with quotas in the cluster.
(b) Verify utilization calculation: for a known namespace, compare the SPL-computed cpu_pct with `kubectl describe quota -n <ns>`. The percentages should match.
(c) Test quota exhaustion: in a test namespace with a tight quota, attempt to scale a deployment beyond the quota limit. Verify: `index=containers sourcetype="kube:events" "exceeded quota" earliest=-10m`.
(d) Verify kube-state-metrics: `| mstats count(kube_resourcequota) WHERE index=containers BY namespace, resource span=5m | head 20`. Should show metrics for all quota-enabled namespaces.
(e) Validate trend data: `index=containers sourcetype="kube:objects:resourcequotas" earliest=-30d | bin _time span=1d | stats count by _time | sort _time`. Should show consistent daily data points.

Step 4 — Operationalize dashboards and runbooks
• Row A: **single-value tiles** — namespaces at CRITICAL risk, namespaces at HIGH risk, total quota rejections (last 24h), soonest forecasted exhaustion (days), namespaces without quotas.
• Row B: **heatmap** — namespace × resource type (CPU, Memory, Pods) with utilization percentage as color intensity. Red cells immediately highlight the most constrained namespaces.
• Row C: **quota utilization bar chart** — horizontal bars showing CPU and memory utilization per namespace with threshold lines at 70%, 85%, and 95%.
• Row D: **exhaustion event table** — ns, rejection_count, affected_workloads, exceeded_quotas, latest_msg. Red rows for recent rejections.
• Row E: **growth trend line chart** — daily CPU and memory utilization per namespace with SMA overlay and threshold lines.
• **Alerting**: CRITICAL → PagerDuty P2 + Slack `#platform-capacity` (include ns, bottleneck, max_util); HIGH sustained > 2 hours → Slack; quota rejection event → Slack `#platform-ops` (include ns, workload, quota_name); growth trend crossing 85% threshold → weekly capacity planning report.
• **Runbook** (owner: platform/capacity team): (1) for CRITICAL quota: check which workloads are consuming the most resources: `kubectl top pods -n <ns> --sort-by=cpu`, (2) determine if usage is legitimate (growth) or anomalous (runaway pod), (3) if legitimate: increase the quota via `kubectl edit quota -n <ns>` or through GitOps, (4) if anomalous: identify and remediate the runaway workload, (5) for quota rejections: communicate with the affected team about their quota limits and assist with resource optimization.

Step 5 — Visualization, alert design, and troubleshooting
• **Visualization**: use a **quota budget gauge** per namespace showing remaining capacity (like a fuel gauge) — green when plenty of room, amber when approaching limits, red when nearly exhausted. Pair with a **resource allocation treemap** showing each namespace as a rectangle sized by quota allocation and colored by utilization percentage.
• **Alert design**: include `ns`, `quota_name`, `cpu_pct`, `mem_pct`, `pods_pct`, `max_util`, `bottleneck`, and `risk` in the alert payload. For exhaustion events include `rejection_count`, `affected_workloads`, `exceeded_quotas`, and `latest_msg`.
• **Utilization shows 0% for all resources** — the `spath` extraction may not be finding the correct fields. ResourceQuota field paths vary by Kubernetes version and collector configuration. Verify the raw event structure: `index=containers sourcetype="kube:objects:resourcequotas" earliest=-5m | head 1 | spath | fields status.*`.
• **CPU/memory values are strings, not numbers** — Kubernetes API returns resource values as strings (e.g., `"4"` for CPU, `"8Gi"` for memory). Use `tonumber()` in eval and handle unit suffixes (m for millicores, Ki/Mi/Gi for memory) before computing percentages.
• **Quota rejection events not appearing** — the FailedCreate event is generated by the **ReplicaSet controller**, not the pod itself. Check the event's involvedObject.kind — it should be ReplicaSet or Job, not Pod.
• **LimitRange defaults not visible in pod specs** — when a LimitRange injects default resource requests/limits, the injected values appear in the pod spec but are not distinguishable from explicitly set values. Compare pod specs with the LimitRange defaults to identify pods relying on injected defaults versus explicit specifications.
• **Multi-cluster quota aggregation** — if the same team operates across multiple clusters, aggregate quota utilization across clusters by team using the namespace metadata lookup. This provides a holistic view of team resource consumption.

## SPL

```spl
`comment("--- Resource Quota Utilization — Namespace Capacity Risk Assessment ---")`
index=containers sourcetype="kube:objects:resourcequotas"
| spath
| eval ns=coalesce("metadata.namespace", namespace)
| eval quota_name=coalesce("metadata.name", quota_name)
| eval cpu_hard=coalesce("status.hard.requests.cpu", "status.hard.cpu", 0)
| eval cpu_used=coalesce("status.used.requests.cpu", "status.used.cpu", 0)
| eval mem_hard=coalesce("status.hard.requests.memory", "status.hard.memory", 0)
| eval mem_used=coalesce("status.used.requests.memory", "status.used.memory", 0)
| eval pods_hard=coalesce("status.hard.pods", 0)
| eval pods_used=coalesce("status.used.pods", 0)
| eval cpu_pct=if(cpu_hard > 0, round(cpu_used / cpu_hard * 100, 1), 0)
| eval mem_pct=if(mem_hard > 0, round(mem_used / mem_hard * 100, 1), 0)
| eval pods_pct=if(pods_hard > 0, round(pods_used / pods_hard * 100, 1), 0)
| eval max_util=max(cpu_pct, mem_pct, pods_pct)
| eval bottleneck=case(
    cpu_pct=max_util, "CPU",
    mem_pct=max_util, "Memory",
    pods_pct=max_util, "Pods",
    1=1, "Unknown")
| eval risk=case(
    max_util >= 95, "CRITICAL",
    max_util >= 85, "HIGH",
    max_util >= 70, "WARNING",
    max_util >= 50, "NOTICE",
    1=1, "OK")
| where risk != "OK"
| stats latest(cpu_pct) as cpu_pct,
    latest(mem_pct) as mem_pct,
    latest(pods_pct) as pods_pct,
    latest(max_util) as max_util,
    latest(bottleneck) as bottleneck,
    latest(risk) as risk
    by ns, quota_name
| sort -max_util
| table ns quota_name cpu_pct mem_pct pods_pct max_util bottleneck risk

`comment("--- Quota Exhaustion Events — Failed Pod Creation Due to Quota ---")`
index=containers sourcetype="kube:events" type="Warning"
    (reason="FailedCreate" OR reason="Forbidden")
    ("exceeded quota" OR "forbidden: exceeded quota" OR "resource quota")
| eval ns=coalesce(involvedObject.namespace, namespace, object_namespace)
| eval workload=coalesce(involvedObject.name, object_name)
| eval obj_kind=coalesce(involvedObject.kind, object_kind)
| rex field=message "exceeded quota: (?<quota_name>[^,]+)"
| rex field=message "requested: (?<requested>[^,]+)"
| rex field=message "used: (?<current_used>[^,]+)"
| rex field=message "limited: (?<limit>[^,]+)"
| bin _time span=1h
| stats count as rejection_count,
    dc(workload) as affected_workloads,
    values(obj_kind) as workload_types,
    values(quota_name) as exceeded_quotas,
    latest(message) as latest_msg
    by _time, ns
| sort -rejection_count
| table _time ns rejection_count affected_workloads workload_types exceeded_quotas latest_msg

`comment("--- Quota Utilization Growth Trend — 30-Day Forecast ---")`
index=containers sourcetype="kube:objects:resourcequotas"
| spath
| eval ns=coalesce("metadata.namespace", namespace)
| eval cpu_pct=round(tonumber(coalesce("status.used.requests.cpu",0)) / tonumber(coalesce("status.hard.requests.cpu",1)) * 100, 1)
| eval mem_pct=round(tonumber(coalesce("status.used.requests.memory",0)) / tonumber(coalesce("status.hard.requests.memory",1)) * 100, 1)
| bin _time span=1d
| stats avg(cpu_pct) as daily_cpu, avg(mem_pct) as daily_mem by _time, ns
| trendline sma7(daily_cpu) as cpu_trend, sma7(daily_mem) as mem_trend
| where isnotnull(cpu_trend)
| table _time ns daily_cpu cpu_trend daily_mem mem_trend
```

## Visualization

Heatmap (namespace x resource type utilization), quota utilization bar chart by namespace, exhaustion event timeline, growth trend line with SMA overlay, single-value tiles (namespaces at risk, rejection count, soonest forecasted exhaustion).

## Known False Positives

**transient_ci_cd_spikes** — CI/CD pipelines running in dedicated namespaces temporarily consume large amounts of CPU and memory quota during build and test phases. These spikes push quota utilization to CRITICAL levels but self-resolve within minutes as pipeline jobs complete. Correlate with pipeline execution schedules and use time-averaged utilization rather than peak for alerting.

**horizontal_autoscaler_bursts** — The Horizontal Pod Autoscaler may scale a deployment to its maximum replica count during traffic peaks, temporarily consuming most of the namespace quota. This is expected behavior that the quota is designed to cap. Alert on sustained high utilization rather than momentary peaks.

**job_completion_lag** — Completed Kubernetes Jobs and their pods continue to count against the quota until garbage collected (controlled by ttlSecondsAfterFinished). A namespace may appear near quota exhaustion even though the actual running workload is small. Check for completed-but-uncleaned jobs contributing to quota usage.

**resource_unit_mismatch** — ResourceQuotas can track both requests and limits separately. A namespace at 90% of its CPU requests quota may have only 50% of its CPU limits quota consumed. The risk assessment should evaluate each dimension independently rather than combining them.

**namespace_lifecycle_events** — When namespaces are created or deleted, quota objects appear or disappear, causing utilization jumps or drops. New namespaces start at 0% utilization (benign) while deleted namespaces cause sudden data gaps. Filter quota changes within the first hour of namespace creation.

**quota_scope_confusion** — ResourceQuotas can have scopes (BestEffort, NotBestEffort, Terminating, NotTerminating) that limit which pods count against the quota. A quota with BestEffort scope only tracks pods without resource requests, making the utilization percentage misleading if interpreted as total namespace consumption.

## References

- [Kubernetes — Resource Quotas](https://kubernetes.io/docs/concepts/policy/resource-quotas/)
- [Kubernetes — Limit Ranges](https://kubernetes.io/docs/concepts/policy/limit-range/)
- [kube-state-metrics — ResourceQuota Metrics](https://github.com/kubernetes/kube-state-metrics/blob/main/docs/resourcequota-metrics.md)
- [Splunk — trendline Command Reference](https://docs.splunk.com/Documentation/Splunk/latest/SearchReference/Trendline)
- [Splunk OTel Collector — k8sobjects Receiver](https://docs.splunk.com/observability/en/gdi/opentelemetry/components/k8sobjects-receiver.html)
