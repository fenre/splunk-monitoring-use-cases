<!-- AUTO-GENERATED from UC-3.6.4.json — DO NOT EDIT -->

---
id: "3.6.4"
title: "Resource Request vs Limit Utilization Trending"
status: "verified"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-3.6.4 · Resource Request vs Limit Utilization Trending

> **Criticality:** Medium &middot; **Difficulty:** Intermediate &middot; **Pillar:** Observability &middot; **Type:** Capacity, Performance, Cost &middot; **Wave:** Crawl &middot; **Status:** Verified

*We compare how much computer power each program was promised versus how much it actually uses, spotting those that waste resources by hoarding too much or risk crashing by using more than their share.*

---

## Description

Compares actual **CPU** and **memory** utilization against Kubernetes **resource requests** and **limits** for every container, computing request utilization percentages, waste scores, and OOM-risk tiers — revealing over-provisioned workloads burning budget and under-provisioned workloads approaching throttling or OOMKill.

## Value

Over-provisioned resource requests waste cluster capacity and cloud spend — a namespace averaging 15% CPU request utilization is holding 85% of its allocated capacity idle. Under-provisioned limits create the opposite risk: containers running near their memory limit are one traffic spike away from OOMKill. Trending both dimensions gives platform and finance teams the data to right-size workloads, reclaim wasted capacity, and prevent outages.

## Implementation

Deploy the Splunk OTel Collector to scrape kubelet cAdvisor (container_cpu_usage_seconds_total, container_memory_working_set_bytes) and kube-state-metrics (kube_pod_container_resource_requests, kube_pod_container_resource_limits). Build two search variants: CPU request utilization by namespace with waste scoring and sizing classification, and memory limit utilization with OOM risk detection. Alert on namespaces with >50% waste score or containers at CRITICAL OOM risk.

## Detailed Implementation

### Prerequisites
- **kube-state-metrics** 2.8+ exposing **`kube_pod_container_resource_requests`** and **`kube_pod_container_resource_limits`** gauges labeled by `namespace`, `pod`, `container`, and `resource` (cpu/memory). These metrics report the **declared** request and limit values from each container's **pod spec**.
- **kubelet cAdvisor** metrics enabled (default on all **Kubernetes** distributions) exposing **`container_cpu_usage_seconds_total`** (CPU usage counter) and **`container_memory_working_set_bytes`** (memory usage gauge, preferred over `container_memory_usage_bytes` because it excludes filesystem cache that the kernel can reclaim).
- **Splunk OpenTelemetry Collector** deployed as a **DaemonSet** with the **Prometheus receiver** scraping both **kube-state-metrics** (service port, typically 8080) and **kubelet cAdvisor** (HTTPS port 10250 with **bearer token** auth). The chart's default configuration enables both.
- **Splunk HEC** token for **`index=containers`** with **`sourcetype=otel:metrics`**; secondary stream for **`sourcetype=kube:events`** (**OOMKill**ed, Evicted, CPUThrottling events).
- **Kubernetes RBAC**: **OTel Collector** **ServiceAccount** needs `get`, `list`, `watch` on pods and nodes, plus **kubelet** API access via the `system:node-proxy` **ClusterRole** binding.
- Splunk RBAC: users running resource searches need **`srchIndexesAllowed`** including `containers`; assign via a custom role (**`platform_capacity_analyst`**).
- **License estimate**: resource metrics produce ~500 bytes per container per scrape; a 500-container cluster at 30s intervals generates ~20–40 MB/day.

### Step 1 — Configure data collection
(1) **kube-state-metrics scraping**: verify the **Prometheus receiver** includes the **kube-state-metrics** scrape target. Key metrics:
— **`kube_pod_container_resource_requests{resource="cpu"}`** (gauge: CPU request in cores)
— **`kube_pod_container_resource_requests{resource="memory"}`** (gauge: memory request in bytes)
— **`kube_pod_container_resource_limits{resource="cpu"}`** (gauge: CPU limit in cores)
— **`kube_pod_container_resource_limits{resource="memory"}`** (gauge: memory limit in bytes)
These represent the **static configuration** declared in the pod spec.

(2) **kubelet **cAdvisor** scraping**: the OTel Collector's **kubelet stats receiver** or Prometheus receiver scrapes actual usage from each node's kubelet:
— **`container_cpu_usage_seconds_total`** (counter: cumulative CPU time consumed — rate this over the scrape interval to get CPU cores used)
— **`container_memory_working_set_bytes`** (gauge: current memory **working set** — the best proxy for actual memory consumption that will trigger OOMKill when it exceeds the limit)
Important: use `container_memory_working_set_bytes` not `container_memory_usage_bytes` — the latter includes kernel **page cache** that can be reclaimed and overstates actual memory pressure.

(3) **Node allocatable resources**: collect **`kube_node_status_allocatable{resource="cpu"}`** and **`kube_node_status_allocatable{resource="memory"}`** for cluster-wide capacity context — this enables calculating total cluster utilization versus total allocatable resources.

(4) **OOMKill correlation**: collect **`sourcetype=kube:events`** with reason `OOMKilling` and `Evicted` to correlate containers at CRITICAL memory risk with actual OOMKill events — this validates the risk model.

(5) **Namespace ownership lookup**: reference the **`namespace_owners.csv`** lookup (from UC-3.6.3) to route **waste report**s and OOM alerts to the owning team.

### Step 2 — Create the search and alert
The CPU variant computes **`request_util_pct`** — the ratio of actual CPU usage to the declared CPU request. This measures how efficiently the container uses its guaranteed resources. The **`sizing`** classification:
— **OVER_PROVISIONED**: using less than 20% of its request — the container is holding 80%+ of its guaranteed resources idle
— **RIGHT_SIZED**: using 20–90% of its request — normal operating range
— **RIGHT_SIZED_HOT**: using > 90% of request — close to exhausting guaranteed resources
— **AT_RISK**: using > 90% of request AND > 80% of limit — approaching **CPU throttling**

The **`waste_score`** per namespace is `100 - avg_req_util` — a waste score of 80 means the namespace is using only 20% of its requested CPU capacity on average.

The memory variant focuses on **limit utilization** because memory limits are the OOMKill trigger. A container at 95%+ of its memory limit is one allocation spike away from being killed by the kernel. The **`oom_risk`** classification escalates through LOW → MODERATE (70%) → HIGH (85%) → CRITICAL (95%).

Schedule the CPU waste search **daily at 08:00** over **`-24h`** and generate a weekly report for platform and finance teams. Schedule the memory **OOM-risk search** every **15 minutes** over **`-15m`** and alert on any container at CRITICAL risk.

### Step 3 — Validate
(a) Cross-check with `kubectl top`: `kubectl top pods -n <ns> --sort-by=cpu` and compare CPU usage values with the SPL output. Values should agree within 10% (differences from scrape timing and aggregation).
(b) Test **over-provisioning detection**: deploy a container with 2 CPU cores requested but `stress --cpu 1` running (using ~50% of request). The search should classify it as RIGHT_SIZED. Reduce the workload to idle and verify it shifts to OVER_PROVISIONED.
(c) Test **OOM risk detection**: deploy a container with 128Mi memory limit and `stress --vm 1 --vm-bytes 120M` — using ~94% of limit. The search should show `oom_risk=CRITICAL`.
(d) Verify **waste score calculation**: pick a namespace and manually compute `avg(actual_cpu / request_cpu)` from `kubectl top pods` versus pod spec requests. Compare with the SPL `waste_score`.
(e) Correlate with **OOMKill events**: `index=containers sourcetype="kube:events" reason="OOMKilling" earliest=-24h | stats count by namespace, pod`. Pods in this list should also appear in the CRITICAL OOM risk tier.

### Step 4 — Operationalize dashboards and runbooks
- Row A: **bar chart** of `waste_score` by namespace — sorted descending, color-coded (red > 80%, orange 50–80%, green < 50%) — immediately shows which namespaces waste the most capacity.
- Row B: **single-value tiles** — cluster-wide average waste %, containers at CRITICAL OOM risk, OOMKill events today, total CPU cores requested vs. used, estimated monthly cost savings from **right-sizing** (if cloud cost data is available).
- Row C: **scatter plot** of CPU request utilization (X-axis) vs. memory limit utilization (Y-axis) per container — containers in the top-right are efficiently sized, top-left are CPU-over/memory-right, bottom-right are CPU-right/memory-over.
- Row D: **OOM risk table** — ns, pod_name, container_name, mem_usage_mb, mem_limit_mb, limit_util_pct, oom_risk. Red rows for CRITICAL/HIGH.
- **Alerting**: CRITICAL OOM risk → **PagerDuty** P2 with pod name and memory usage; namespace waste > 80% → weekly email digest to team leads with specific right-sizing recommendations; OOMKill event → Slack `#platform-ops` with pod details.
- **Runbook** (owner: platform engineering): (1) for OVER_PROVISIONED: reduce request to 1.5× average peak usage, (2) for AT_RISK: increase request to cover peak + 20% headroom, (3) for CRITICAL OOM: increase memory limit immediately, then investigate whether the workload has a memory leak, (4) for cluster-wide waste: identify the top 5 namespaces and schedule right-sizing reviews.

### Step 5 — Visualization, alert design, and troubleshooting
- **Visualization**: use a **right-sizing recommendation table** that computes `suggested_request = round(avg_usage * 1.3, 2)` and `suggested_limit = round(peak_usage * 1.5, 2)` for each container — gives engineers specific values to apply; pair with a **30-day trend chart** of namespace-level waste scores to show whether right-sizing efforts are reducing waste over time; add a **cost impact column** if **cloud billing** data is available.
- **Alert design**: include `ns`, `pod_name`, `container_name`, `cpu_usage_cores`, `cpu_request_cores`, `request_util_pct`, `sizing`, `waste_score` for CPU alerts; for OOM alerts include `mem_usage_mb`, `mem_limit_mb`, `limit_util_pct`, `oom_risk`; include right-sizing recommendations in the alert body.
- **CPU usage always shows 0** — `container_cpu_usage_seconds_total` is a counter that must be rated; if the SPL uses `latest(value)` instead of rate calculation, it shows cumulative seconds, not cores. For point-in-time snapshots, use `container_cpu_usage_seconds_total` delta over the scrape interval or use the pre-computed `container_cpu_cfs_periods_total` ratio.
- **Memory shows higher than limit** — `container_memory_usage_bytes` includes kernel page cache; switch to **`container_memory_working_set_bytes`** which excludes reclaimable cache and accurately represents OOMKill-triggering memory.
- **Request/limit metrics show null** — containers without explicit resource requests or limits in their pod spec do not report `kube_pod_container_resource_requests/limits` metrics. The `where isnotnull(cpu_request_cores)` filter excludes these. Add a separate panel listing containers without requests for governance.
- **Waste score is misleading for batch workloads** — batch jobs have bursty CPU patterns with long idle periods between runs. Average utilization understates their peak needs. Use `max` or `p95` utilization instead of `avg` for **batch workloads**.

## SPL

```spl
`comment("--- CPU Request vs Actual Utilization by Namespace and Workload ---")`
index=containers (sourcetype="otel:metrics" OR sourcetype="prometheus:kube")
| where match(metric_name, "container_cpu_usage_seconds_total|kube_pod_container_resource_requests|kube_pod_container_resource_limits")
| eval ns=coalesce(namespace, exported_namespace, label_namespace, "unknown")
| eval pod_name=coalesce(pod, exported_pod, label_pod, "unknown")
| eval container_name=coalesce(container, label_container, "unknown")
| eval metric=coalesce(metric_name, name)
| eval resource_type=coalesce(resource, label_resource, "cpu")
| where resource_type="cpu" OR match(metric, "cpu_usage")
| eval val=tonumber(value)
| stats latest(eval(if(match(metric, "cpu_usage"), val, null()))) as cpu_usage_cores,
    latest(eval(if(match(metric, "resource_requests"), val, null()))) as cpu_request_cores,
    latest(eval(if(match(metric, "resource_limits"), val, null()))) as cpu_limit_cores
    by ns, pod_name, container_name
| where isnotnull(cpu_request_cores) AND cpu_request_cores > 0
| eval request_util_pct=round(100 * cpu_usage_cores / cpu_request_cores, 1)
| eval limit_util_pct=if(isnotnull(cpu_limit_cores) AND cpu_limit_cores > 0, round(100 * cpu_usage_cores / cpu_limit_cores, 1), null())
| eval sizing=case(
    request_util_pct < 20, "OVER_PROVISIONED",
    request_util_pct > 90 AND isnotnull(limit_util_pct) AND limit_util_pct > 80, "AT_RISK",
    request_util_pct > 90, "RIGHT_SIZED_HOT",
    1=1, "RIGHT_SIZED")
| stats avg(request_util_pct) as avg_req_util,
    avg(limit_util_pct) as avg_limit_util,
    dc(pod_name) as pod_count,
    count(eval(sizing="OVER_PROVISIONED")) as over_provisioned,
    count(eval(sizing="AT_RISK")) as at_risk
    by ns
| eval waste_score=round(100 - avg_req_util, 1)
| sort -waste_score
| table ns pod_count avg_req_util avg_limit_util over_provisioned at_risk waste_score

`comment("--- Memory Request vs Actual Utilization — OOM Risk Detection ---")`
index=containers (sourcetype="otel:metrics" OR sourcetype="prometheus:kube")
| where match(metric_name, "container_memory_working_set_bytes|kube_pod_container_resource_requests|kube_pod_container_resource_limits")
| eval ns=coalesce(namespace, exported_namespace, label_namespace, "unknown")
| eval pod_name=coalesce(pod, exported_pod, label_pod, "unknown")
| eval container_name=coalesce(container, label_container, "unknown")
| eval metric=coalesce(metric_name, name)
| eval resource_type=coalesce(resource, label_resource, "memory")
| where resource_type="memory" OR match(metric, "memory_working_set")
| eval val=tonumber(value)
| stats latest(eval(if(match(metric, "memory_working_set"), val, null()))) as mem_usage_bytes,
    latest(eval(if(match(metric, "resource_requests"), val, null()))) as mem_request_bytes,
    latest(eval(if(match(metric, "resource_limits"), val, null()))) as mem_limit_bytes
    by ns, pod_name, container_name
| where isnotnull(mem_limit_bytes) AND mem_limit_bytes > 0
| eval mem_usage_mb=round(mem_usage_bytes / 1048576, 0)
| eval mem_limit_mb=round(mem_limit_bytes / 1048576, 0)
| eval limit_util_pct=round(100 * mem_usage_bytes / mem_limit_bytes, 1)
| eval oom_risk=case(
    limit_util_pct > 95, "CRITICAL",
    limit_util_pct > 85, "HIGH",
    limit_util_pct > 70, "MODERATE",
    1=1, "LOW")
| where oom_risk != "LOW"
| sort -limit_util_pct
| head 50
| table ns pod_name container_name mem_usage_mb mem_limit_mb limit_util_pct oom_risk
```

## Visualization

Namespace waste score bar chart, memory OOM risk table, CPU request vs actual scatter plot, single-value tiles (cluster-wide waste %, at-risk containers, OOM events today).

## Known False Positives

**batch_workload_idle** — Batch processing jobs (CronJobs, Spark executors, data pipelines) alternate between full utilization during processing and near-zero usage between runs. Average utilization metrics classify these as OVER_PROVISIONED even though their peak utilization justifies the resource request. Use max or P95 utilization over a 24-hour window for batch workloads instead of average.

**hpa_scaling_headroom** — HorizontalPodAutoscaler targets a specific CPU utilization percentage (e.g., 50%) by scaling the replica count. Individual pods appear under-utilized relative to their requests because the HPA deliberately maintains headroom. The waste score reflects intentional HPA design, not misconfiguration.

**jvm_heap_reservation** — Java applications configured with -Xmx reserve the maximum heap size at startup, causing container_memory_working_set_bytes to stabilize at the JVM heap max even when actual object occupancy is low. Memory limit utilization appears high even though the JVM can handle more work within its allocated heap.

**init_container_spike** — Init containers run briefly during pod startup and may consume significant CPU or memory during their execution window. If the scrape coincides with init container activity, it captures a transient spike that does not represent steady-state utilization. Filter by container name to exclude init containers from the analysis.

**guaranteed_qos_design** — Containers in the Kubernetes Guaranteed QoS class (request equals limit for all resources) always show 100% request-to-limit ratio regardless of actual usage. This is intentional design for latency-sensitive workloads that need guaranteed scheduling. Do not flag these as AT_RISK based on the request/limit ratio alone.

**vertical_pod_autoscaler_transition** — When VPA updates resource requests, there is a transition period where the new request takes effect after pod restart but the old utilization baseline persists in the trend data. This creates a temporary misclassification until enough data accumulates under the new request values.

## References

- [Kubernetes — Resource Management for Pods and Containers](https://kubernetes.io/docs/concepts/configuration/manage-resources-containers/)
- [Kubernetes — Resource Requests and Limits Best Practices](https://kubernetes.io/docs/concepts/configuration/manage-resources-containers/#resource-requests-and-limits-of-pod-and-container)
- [kube-state-metrics — Pod Resource Metrics](https://github.com/kubernetes/kube-state-metrics/blob/main/docs/pod-metrics.md)
- [Splunk OpenTelemetry Collector for Kubernetes](https://github.com/signalfx/splunk-otel-collector-chart)
- [Kubernetes — OOMKilled Troubleshooting](https://kubernetes.io/docs/tasks/debug/debug-application/determine-reason-pod-failure/)
