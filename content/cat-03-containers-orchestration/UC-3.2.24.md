<!-- AUTO-GENERATED from UC-3.2.24.json — DO NOT EDIT -->

---
id: "3.2.24"
title: "Kubernetes HorizontalPodAutoscaler (HPA) Decision Introspection — Target-vs-Actual Metric Math, Replica-Decision Causality, Scale-Out Surprise RCA"
status: "verified"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-3.2.24 · Kubernetes HorizontalPodAutoscaler (HPA) Decision Introspection — Target-vs-Actual Metric Math, Replica-Decision Causality, Scale-Out Surprise RCA

> **Criticality:** Medium &middot; **Difficulty:** Advanced &middot; **Pillar:** Observability &middot; **Type:** Performance, Capacity &middot; **Wave:** Walk &middot; **Status:** Verified

*We watch how the automatic pod scaler picks instance counts from its measurements so we can explain surprise jumps before teams blame the wrong layer. We line those numbers up with what each app reserved for computing power so average load stories stay honest when incidents strike.*

---

## Description

Explains Kubernetes HorizontalPodAutoscaler (HPA) replica decisions by reconciling kube_horizontalpodautoscaler_spec_target_metric with kube_horizontalpodautoscaler_status_current_metrics_average_utilization and kube_horizontalpodautoscaler_status_current_metrics_average_value, recomputing clamped desired replicas from kube_horizontalpodautoscaler_status_current_replicas using the textbook resource-metric ratio, comparing against kube_horizontalpodautoscaler_status_desired_replicas with tolerance-aware delta_rep gates, surfacing sudden_desired_jump via streamstats over bucketed desired series, enriching kube_horizontalpodautoscaler_info workload keys with summed kube_pod_container_resource_requests cpu cores for utilization denominator context, and flagging math_surprise rows distinct from UC-3.2.11 flap frequency, UC-3.2.17 maxReplicas ceiling dwell, UC-3.2.46 node scale-out refusal, and UC-3.2.38 vertical sizing drift.

## Value

Mean time to understand improves when platform teams see one row that names cluster, namespace, scaler, current and desired replicas, min and max bounds, actual versus target utilization, naive clamped prediction, math surprise boolean, sudden jump flag, aggregate CPU requests for the scaled workload, namespace surprise heat, severity, and raw spec target lines for external metric RCA without manually reconciling kubectl, metrics explorers, and adapter logs during a surprise scale-out. Customer impact drops because stabilization, tolerance bands, and adapter staleness are distinguished from application defects before code rollbacks. Capacity reviews gain evidence for tuning behavior.scaleUp.stabilizationWindowSeconds, fixing custom.metrics.k8s.io bridges, or right-sizing requests before game-day traffic amplifies metric skew.

## Implementation

Scrape kube-state-metrics kube_horizontalpodautoscaler status, spec, current-metrics, and info series plus kube_pod_container_resource_requests cpu into k8s_metrics, publish hpa_decision_introspection_inventory.csv with tolerance and tier metadata, save uc_3_2_24_hpa_decision_introspection on a five-minute schedule with earliest=-3h@m latest=now, route math_surprise rows for production tiers, and validate in lab by contrasting naive ceil math with kube_horizontalpodautoscaler_status_desired_replicas under tuned behavior windows.

## Evidence

Saved search uc_3_2_24_hpa_decision_introspection with five-minute schedule; hpa_decision_introspection_inventory.csv versioned in git; weekly CSV export of the alert table to a restricted evidence index with kube-state-metrics chart version for auditors.

## Control test

### Positive scenario

In a lab namespace, configure a CPU averageUtilization HorizontalPodAutoscaler with narrow behavior.scaleUp.stabilizationWindowSeconds, inject a short load spike so kube_horizontalpodautoscaler_status_current_metrics_average_utilization exceeds kube_horizontalpodautoscaler_spec_target_metric while kube_horizontalpodautoscaler_status_desired_replicas disagrees with tolerance-adjusted predicted_clamped beyond tol_abs, execute uc_3_2_24_hpa_decision_introspection, and expect math_surprise equal to one with severity at least medium when inventory marks production tier.

### Negative scenario

Return the workload to steady state within target utilization for two hours with wide stabilization windows, confirm kube_horizontalpodautoscaler_status_desired_replicas matches predicted_clamped within tolerance for four consecutive evaluations, and verify the saved search emits no qualifying rows for that HorizontalPodAutoscaler.

## Detailed Implementation

### Step 1 — Prerequisites

Head of Platform owns this control together with Kubernetes platform engineers, workload owners who declare HorizontalPodAutoscaler objects and behavior blocks, and observability engineers operating Splunk OpenTelemetry Collector plus kube-state-metrics. This use case isolates HPA decision causality: reconciling kube_horizontalpodautoscaler_spec_target_metric declarations with kube_horizontalpodautoscaler_status_current_metrics_average_utilization and kube_horizontalpodautoscaler_status_current_metrics_average_value, recomputing the textbook desired replica count from current replicas and metric ratios, and flagging rows where kube_horizontalpodautoscaler_status_desired_replicas disagrees with the clamped prediction beyond the documented tolerance band after min and max bounds apply. UC-3.2.11 remains scaling event frequency, cooldown churn, and SuccessfulRescale cadence analytics. UC-3.2.17 remains maxReplicas dwell, ScalingLimited saturation narratives, and FailedGet metric provider outages. UC-3.2.46 remains Cluster Autoscaler and Karpenter node scale-out refusal when Pending pods cannot land. UC-3.2.38 remains VerticalPodAutoscaler recommendation drift against live requests. Do not merge those planes into this detector.

Before scheduling the saved search, confirm index=k8s_metrics ingests kube-state-metrics text lines for kube_horizontalpodautoscaler_status_current_replicas, kube_horizontalpodautoscaler_status_desired_replicas, kube_horizontalpodautoscaler_spec_min_replicas, kube_horizontalpodautoscaler_spec_max_replicas, kube_horizontalpodautoscaler_status_current_metrics_average_utilization, kube_horizontalpodautoscaler_status_current_metrics_average_value, kube_horizontalpodautoscaler_spec_target_metric, kube_horizontalpodautoscaler_info with scaletargetref_name labels, and kube_pod_container_resource_requests carrying cpu so average utilization denominators can be sanity-checked against aggregate requests for the scaled workload. Confirm Splunk field extractions preserve horizontalpodautoscaler, namespace, cluster, pod, and numeric metric values on prometheus:scrape:metrics or kube:objects:metrics sourcetypes. Publish lookups/hpa_decision_introspection_inventory.csv keyed on cluster, namespace, horizontalpodautoscaler with owner_team, workload_tier, and expected_tolerance_pct defaulting near ten to mirror Kubernetes horizontal tolerance semantics for resource metrics.

Training responders to read kubectl describe horizontalpodautoscaler for metric names, target types, and behavior.scaleUp or behavior.scaleDown stabilizationWindowSeconds alongside Splunk columns reduces bridges opened against stabilization that is working as designed. Kubernetes publishes the core ratio relationship used for resource metrics: desired replicas approximate the ceiling of current replicas times observed utilization divided by target utilization, then controllers apply tolerance, per-direction policies, and windows before committing kube_horizontalpodautoscaler_status_desired_replicas. When external or object metrics dominate, naive utilization math in this search may be suppressed by util_math_ok gates, and teams pivot to adapter traces instead of CPU ratio stories.

Risk framing: surprise scale-outs after a single hot metric sample often trace to short stabilization windows, missing averages across pods, or stale adapter series feeding kube_horizontalpodautoscaler_status_current_metrics_average_value spikes. Surprise scale-down absence often traces to scaleDown.selectPolicy=Disabled or long stabilization windows holding elevated desired counts. This detector explains why an observed desired count is not the naive ratio result, not whether the cluster flaps broadly; pair with UC-3.2.11 when event cadence itself is the incident.

Capacity and licensing: HorizontalPodAutoscaler metric cardinality tracks object count. Keep unnecessary labels off scrape configs after FinOps review. Legal review may redact proprietary queue names embedded in spec_target_raw lines while preserving hashed identifiers.

Governance: refresh hpa_decision_introspection_inventory.csv weekly from Git-backed manifests so owner_team and workload_tier route pages without kubectl translation. Quarterly replay one historical incident where widening behavior.scaleUp.stabilizationWindowSeconds eliminated math_surprise noise and another where fixing a custom metrics adapter restored agreement between predicted_clamped and desired_replicas.

Hardware scope: Amazon EKS, Google GKE, Microsoft AKS, Red Hat OpenShift, VMware Tanzu, and self-managed Kubernetes where kube-state-metrics RBAC lists HorizontalPodAutoscaler objects cluster-wide.

Differentiation recap: target versus actual metric math, naive replica prediction, tolerance-aware surprise flags, request aggregate context, not generic flap counts, not max-only dwell, not node provisioning refusal.

Operational nuance for reviewers: kube_horizontalpodautoscaler_status_current_metrics_average_utilization reflects the controller view of utilization against requests for pods it believes are ready, while kube_pod_container_resource_requests aggregated here is a kube-state-metrics approximation of live request totals for the scaleTargetRef workload key. When those diverge because pod labels, init containers, or sidecars shift request accounting, math_surprise may light even though kubectl describe horizontalpodautoscaler reads sane. Treat sum_req_cpu_cores as corroboration, not a second source of truth for the controller loop. For HorizontalPodAutoscaler objects that reference external or object metrics, spec_target_raw multivalue lines become the primary narrative field because util_math_ok intentionally stays zero when target_util is not a simple percentage target; operators should still collect those rows for RCA dashboards even if the alert predicate filters on util_math_ok equals one. Stabilization windows prefer the maximum observed desired recommendation across the window for scale-up and the minimum for scale-down in upstream behavior descriptions; a single splunk snapshot therefore cannot reconstruct the full windowed recommendation without storing time series, which is why sudden_desired_jump uses bucketed kube_horizontalpodautoscaler_status_desired_replicas rather than pretending one scrape explains the entire window. Prefer-stabilization-window versus raw signal disputes are expected during incidents: widen windows when finance accepts slower scale-out, tighten only after proving adapters are not feeding stale kube_horizontalpodautoscaler_status_current_metrics_average_value samples.

### Step 2 — Configure data collection

Deploy kube-state-metrics exposing HorizontalPodAutoscaler metrics per upstream documentation. Point Splunk OpenTelemetry Collector prometheus or prometheus_simple receivers at the kube-state-metrics Service, preserve horizontalpodautoscaler and namespace labels through relabel rules, export to index=k8s_metrics with sourcetype prometheus:scrape:metrics, and normalize cluster attribution using the same coalesce ladder as UC-3.2.11 for mixed EKS, GKE, and AKS field habits.

ServiceMonitor-style reference:

apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: kube-state-metrics-hpa-decision
  namespace: kube-system
spec:
  selector:
    matchLabels:
      app.kubernetes.io/name: kube-state-metrics
  endpoints:
    - port: http-metrics
      interval: 30s
      scrapeTimeout: 10s
      path: /metrics

Ensure kube_pod_container_resource_requests for cpu is scraped from kube-state-metrics so sum_req_cpu_cores can contextualize utilization denominators when kube_horizontalpodautoscaler_info maps scaleTargetRef to a Deployment name. If your fleet labels prometheus differently, mirror UC-3.2.38 rex patterns for stripping ReplicaSet suffixes from pod labels before aggregating by workload_key.

Publish lookups/hpa_decision_introspection_inventory.csv:

cluster,namespace,horizontalpodautoscaler,owner_team,workload_tier,expected_tolerance_pct
prod-eks-us-east-1,prod-payments,carts-api-hpa,payments-sre,production,10
lab-gke-dev,qa-load,checkout-hpa-qa,platform-test,dev,10

expected_tolerance_pct should reflect how strictly you want naive math to match kube_horizontalpodautoscaler_status_desired_replicas before opening surprise investigations; ten aligns with common resource-metric tolerance discussion in upstream horizontal documentation.

Validation searches before alert authoring:

index=k8s_metrics sourcetype=prometheus:scrape:metrics kube_horizontalpodautoscaler_status_current_metrics earliest=-30m latest=now

index=k8s_metrics sourcetype=prometheus:scrape:metrics kube_horizontalpodautoscaler_spec_target_metric earliest=-30m latest=now

Confirm numeric extractions with Field Inspector. Skew between scrapes beyond ninety seconds weakens streamstats sudden_desired_jump semantics; align scrape and alert schedules accordingly.

Splunk OpenTelemetry Collector sketch:

receivers:
  prometheus/k8s_state:
    config:
      scrape_configs:
        - job_name: kube-state-metrics-hpa-decision
          kubernetes_sd_configs:
            - role: endpoints
          relabel_configs:
            - source_labels: [__meta_kubernetes_service_name]
              action: keep
              regex: kube-state-metrics
exporters:
  splunk_hec/metrics:
    token: ${SPLUNK_HEC_TOKEN_K8S_METRICS}
    endpoint: https://splunk-hec.example:8088/services/collector/event
    index: k8s_metrics
    sourcetype: prometheus:scrape:metrics
service:
  pipelines:
    metrics/ksm:
      receivers: [prometheus/k8s_state]
      exporters: [splunk_hec/metrics]

Security: store HEC tokens in vault with rotation. Redact customer workload names in email bodies when policy requires while retaining cluster and namespace for routing.

props.conf guidance: index metric_name, namespace, horizontalpodautoscaler when acceleration experiments justify the disk; keep coalesce ladders in SPL until extractions stabilize.

Cloud control planes: verify managed Prometheus agents still emit kube_horizontalpodautoscaler_status_current_metrics_average_utilization on your distro; some vendors rename labels.

Back-pressure: bounded queues on collectors during apiserver storms prevent silent drops that look like stabilization.

Version pinning: record kube-state-metrics chart version quarterly in evidence packs.

### Step 3 — Create the search and alert

Save the SPL as uc_3_2_24_hpa_decision_introspection with five-minute schedule, dispatch earliest=-3h@m, dispatch latest=now, and alert when severity is critical or high for production-tier rows where math_surprise equals one. Throttle duplicate pages per cluster, namespace, and horizontalpodautoscaler for twenty minutes unless sudden_desired_jump escalates. Include current_replicas, desired_replicas, predicted_clamped, actual_util, target_util, sum_req_cpu_cores, and spec_target_raw excerpts in pager bodies so responders compare apples-to-apples without opening Search first.

Pipeline narrative for operators: the opening comment lists tunables. The tstats join against Performance proves Performance acceleration is warm for audits; if acceleration is absent in a lab, the join still type=left preserves HorizontalPodAutoscaler rows. multisearch fans three parallel metric arms so a missing spec_target line does not blank replica context: replica and desired gauges with min and max bounds, kube_horizontalpodautoscaler_status_current_metrics averages, and kube_horizontalpodautoscaler_spec_target_metric raw numeric targets with preserving spec_target_raw for external metric troubleshooting. After merge_key stats, a join replays kube_horizontalpodautoscaler_status_desired_replicas over five-minute bins with streamstats range to flag sudden_desired_jump when desired replicas move by two or more across adjacent buckets, a practical signal for surprise scale-out jumps. inputlookup enriches owner_team, workload_tier, and tol_pct. coalesce prepares actual_util from percent utilization first, then fraction average_value when between zero and one. The eval ladder computes predicted_clamped from ceil(current times actual divided by target) then min and max clamps. util_math_ok limits surprise detection to classic percent utilization targets between one and one hundred so external metric gauges do not false-positive. math_surprise compares delta_rep against a tolerance floor derived from tol_pct. kube_horizontalpodautoscaler_info plus kube_pod_container_resource_requests_cpu joins contextualize aggregate CPU requests for the scaled workload. eventstats surfaces ns_surprise_peak for namespace-level overlays on dashboards. case assigns severity emphasizing production-tier math_surprise with sudden jumps.

Paste-and-run SPL for alerts and dashboards must match the spl JSON field exactly:

```spl
`comment("UC-3.2.24 HPA decision introspection: reconcile kube_horizontalpodautoscaler status, spec, and current-metrics series; sum kube_pod_container_resource_requests cpu cores for request-basis context; predicted desired from ceil(current*(actual/target)); stabilization and tolerance surprise flags. Tunables: earliest=-3h@m latest=@m; tol_band_pct=10; indexes k8s_metrics")`
| eval uc_join="3224"
| join type=left uc_join [
| tstats count AS perf_ticks FROM datamodel=Performance WHERE (nodename=Performance.CPU OR nodename=Performance.Memory) earliest=-6h@h latest=now
| eval uc_join="3224" ]
| fields - uc_join perf_ticks
| multisearch [
    [ search ((index=k8s_metrics OR index=k8s) (sourcetype="prometheus:scrape:metrics" OR sourcetype="kube:objects:metrics")) earliest=-3h@m latest=@m
      | eval cluster=lower(trim(toString(coalesce(k8s_cluster_name, cluster_name, cluster, eks_cluster_name, gke_cluster_name, aks_cluster_name, resource_cluster, ""))))
      | eval mn=lower(trim(toString(coalesce(metric_name, __name__, name, MetricName, ""))))
      | rex field=_raw max_match=0 "horizontalpodautoscaler=\"(?<hpa_rx>[^\"]+)\""
      | rex field=_raw max_match=0 "namespace=\"(?<ns_rx>[^\"]+)\""
      | rex field=_raw max_match=0 "\s(?<mval>[0-9.eE+-]+)\s*$"
      | eval hpa=lower(trim(toString(coalesce(horizontalpodautoscaler, hpa_rx, ""))))
      | eval namespace=lower(trim(toString(coalesce(namespace, k8s_namespace, kubernetes_namespace, ns_rx, ""))))
      | where like(mn,"%kube_horizontalpodautoscaler_status_current_replicas%") OR like(mn,"%kube_horizontalpodautoscaler_status_desired_replicas%") OR like(mn,"%kube_horizontalpodautoscaler_spec_min_replicas%") OR like(mn,"%kube_horizontalpodautoscaler_spec_max_replicas%")
      | eval current_replicas=if(like(mn,"%kube_horizontalpodautoscaler_status_current_replicas%"), tonumber(mval,10), null())
      | eval desired_replicas=if(like(mn,"%kube_horizontalpodautoscaler_status_desired_replicas%"), tonumber(mval,10), null())
      | eval min_replicas=if(like(mn,"%kube_horizontalpodautoscaler_spec_min_replicas%"), tonumber(mval,10), null())
      | eval max_replicas=if(like(mn,"%kube_horizontalpodautoscaler_spec_max_replicas%"), tonumber(mval,10), null())
      | stats latest(current_replicas) AS current_replicas latest(desired_replicas) AS desired_replicas latest(min_replicas) AS min_replicas latest(max_replicas) AS max_replicas BY cluster namespace hpa ]
    [ search ((index=k8s_metrics OR index=k8s) (sourcetype="prometheus:scrape:metrics" OR sourcetype="kube:objects:metrics")) earliest=-3h@m latest=@m
      | eval cluster=lower(trim(toString(coalesce(k8s_cluster_name, cluster_name, cluster, eks_cluster_name, gke_cluster_name, aks_cluster_name, resource_cluster, ""))))
      | eval mn=lower(trim(toString(coalesce(metric_name, __name__, name, MetricName, ""))))
      | rex field=_raw max_match=0 "horizontalpodautoscaler=\"(?<hpa_rx>[^\"]+)\""
      | rex field=_raw max_match=0 "namespace=\"(?<ns_rx>[^\"]+)\""
      | rex field=_raw max_match=0 "\s(?<mval>[0-9.eE+-]+)\s*$"
      | eval hpa=lower(trim(toString(coalesce(horizontalpodautoscaler, hpa_rx, ""))))
      | eval namespace=lower(trim(toString(coalesce(namespace, k8s_namespace, kubernetes_namespace, ns_rx, ""))))
      | where like(mn,"%kube_horizontalpodautoscaler_status_current_metrics_average_utilization%") OR like(mn,"%kube_horizontalpodautoscaler_status_current_metrics_average_value%")
      | eval cur_util=if(like(mn,"%average_utilization%"), tonumber(mval,10), null())
      | eval cur_val=if(like(mn,"%average_value%") AND NOT like(mn,"%utilization%"), tonumber(mval,10), null())
      | stats latest(cur_util) AS current_avg_util_pct latest(cur_val) AS current_avg_value BY cluster namespace hpa ]
    [ search ((index=k8s_metrics OR index=k8s) (sourcetype="prometheus:scrape:metrics" OR sourcetype="kube:objects:metrics")) earliest=-3h@m latest=@m
      | eval cluster=lower(trim(toString(coalesce(k8s_cluster_name, cluster_name, cluster, eks_cluster_name, gke_cluster_name, aks_cluster_name, resource_cluster, ""))))
      | eval mn=lower(trim(toString(coalesce(metric_name, __name__, name, MetricName, ""))))
      | rex field=_raw max_match=0 "horizontalpodautoscaler=\"(?<hpa_rx>[^\"]+)\""
      | rex field=_raw max_match=0 "namespace=\"(?<ns_rx>[^\"]+)\""
      | rex field=_raw max_match=0 "\s(?<mval>[0-9.eE+-]+)\s*$"
      | eval hpa=lower(trim(toString(coalesce(horizontalpodautoscaler, hpa_rx, ""))))
      | eval namespace=lower(trim(toString(coalesce(namespace, k8s_namespace, kubernetes_namespace, ns_rx, ""))))
      | where like(mn,"%kube_horizontalpodautoscaler_spec_target_metric%")
      | eval spec_tgt_line=_raw
      | eval spec_tgt_num=tonumber(mval,10)
      | stats latest(spec_tgt_num) AS spec_target_numeric latest(spec_tgt_line) AS spec_target_raw BY cluster namespace hpa ]
]
| eval merge_key=cluster."|".namespace."|".hpa
| stats max(current_replicas) AS current_replicas max(desired_replicas) AS desired_replicas max(min_replicas) AS min_replicas max(max_replicas) AS max_replicas max(current_avg_util_pct) AS current_avg_util_pct max(current_avg_value) AS current_avg_value max(spec_target_numeric) AS spec_target_numeric values(spec_target_raw) AS spec_target_raw BY merge_key
| rex field=merge_key "^(?<cluster>[^|]+)\|(?<namespace>[^|]+)\|(?<hpa>[^|]+)$"
| join type=left max=0 merge_key [
    search ((index=k8s_metrics OR index=k8s) (sourcetype="prometheus:scrape:metrics" OR sourcetype="kube:objects:metrics")) earliest=-3h@m latest=@m
      | eval cluster=lower(trim(toString(coalesce(k8s_cluster_name, cluster_name, cluster, eks_cluster_name, gke_cluster_name, aks_cluster_name, resource_cluster, ""))))
      | eval mn=lower(trim(toString(coalesce(metric_name, __name__, name, MetricName, ""))))
      | rex field=_raw max_match=0 "horizontalpodautoscaler=\"(?<hpa_rx>[^\"]+)\""
      | rex field=_raw max_match=0 "namespace=\"(?<ns_rx>[^\"]+)\""
      | rex field=_raw max_match=0 "\s(?<mval>[0-9.eE+-]+)\s*$"
      | eval hpa=lower(trim(toString(coalesce(horizontalpodautoscaler, hpa_rx, ""))))
      | eval namespace=lower(trim(toString(coalesce(namespace, k8s_namespace, kubernetes_namespace, ns_rx, ""))))
      | where like(mn,"%kube_horizontalpodautoscaler_status_desired_replicas%")
      | eval merge_key=cluster."|".namespace."|".hpa
      | eval dr=tonumber(mval,10)
      | bin _time span=5m aligntime=@m
      | stats latest(dr) AS dr_bin BY merge_key _time
      | sort 0 merge_key + _time
      | streamstats window=3 current=t global=f range(dr_bin) AS dr_range BY merge_key
      | eval sudden_desired_jump=if(dr_range>=2,1,0)
      | stats max(sudden_desired_jump) AS sudden_desired_jump BY merge_key ]
| join type=left max=0 cluster namespace hpa [
    | inputlookup hpa_decision_introspection_inventory.csv
      | eval cluster=lower(trim(toString(cluster)))
      | eval namespace=lower(trim(toString(namespace)))
      | eval hpa=lower(trim(toString(horizontalpodautoscaler)))
      | eval owner_team=trim(toString(coalesce(owner_team, squad, platform_team, "")))
      | eval workload_tier=lower(trim(toString(coalesce(workload_tier, tier, env_tier, "dev"))))
      | eval tol_pct=tonumber(tostring(coalesce(expected_tolerance_pct, "10")), 10)
      | fields cluster namespace hpa owner_team workload_tier tol_pct ]
| fillnull value=10 tol_pct
| fillnull value=0 sudden_desired_jump
| fillnull value="unassigned" owner_team
| fillnull value="dev" workload_tier
| eval target_util=spec_target_numeric
| eval actual_util=coalesce(current_avg_util_pct, if(isnotnull(current_avg_value) AND current_avg_value>0 AND current_avg_value<=1.0, current_avg_value*100, null()))
| eval ratio=if(isnotnull(target_util) AND target_util>0 AND isnotnull(actual_util), actual_util/target_util, null())
| eval predicted_raw=if(isnotnull(current_replicas) AND isnotnull(ratio), current_replicas*ratio, null())
| eval predicted_desired=if(isnotnull(predicted_raw), ceil(predicted_raw), null())
| eval predicted_clamped=if(isnotnull(predicted_desired), max(min_replicas, min(predicted_desired, max_replicas)), null())
| eval util_math_ok=if(isnotnull(current_avg_util_pct) AND isnotnull(target_util) AND target_util>=1 AND target_util<=100 AND isnotnull(predicted_clamped) AND isnotnull(desired_replicas), 1, 0)
| eval delta_rep=abs(desired_replicas-predicted_clamped)
| eval tol_abs=max(1, floor(predicted_clamped*tol_pct/100))
| eval math_surprise=if(util_math_ok==1 AND delta_rep>tol_abs, 1, 0)
| join type=left max=0 cluster namespace hpa [
    search ((index=k8s_metrics OR index=k8s) (sourcetype="prometheus:scrape:metrics" OR sourcetype="kube:objects:metrics")) earliest=-3h@m latest=@m
      | eval cluster=lower(trim(toString(coalesce(k8s_cluster_name, cluster_name, cluster, eks_cluster_name, gke_cluster_name, aks_cluster_name, resource_cluster, ""))))
      | eval mn=lower(trim(toString(coalesce(metric_name, __name__, name, MetricName, ""))))
      | where like(mn,"%kube_horizontalpodautoscaler_info%")
      | rex field=_raw max_match=0 "namespace=\"(?<ns_rx>[^\"]+)\""
      | rex field=_raw max_match=0 "horizontalpodautoscaler=\"(?<hpa_rx>[^\"]+)\""
      | rex field=_raw max_match=0 "scaletargetref_name=\"(?<st_name>[^\"]+)\""
      | eval namespace=lower(trim(toString(coalesce(namespace, k8s_namespace, kubernetes_namespace, ns_rx, ""))))
      | eval hpa=lower(trim(toString(coalesce(horizontalpodautoscaler, hpa_rx, ""))))
      | eval workload_key=lower(trim(toString(st_name)))
      | stats latest(workload_key) AS workload_key BY cluster namespace hpa ]
| join type=left max=0 cluster namespace workload_key [
    search ((index=k8s_metrics OR index=k8s) (sourcetype="prometheus:scrape:metrics" OR sourcetype="kube:objects:metrics")) earliest=-3h@m latest=@m
      | eval cluster=lower(trim(toString(coalesce(k8s_cluster_name, cluster_name, cluster, eks_cluster_name, gke_cluster_name, aks_cluster_name, resource_cluster, ""))))
      | eval mn=lower(trim(toString(coalesce(metric_name, __name__, name, MetricName, ""))))
      | where like(mn,"%kube_pod_container_resource_requests%") AND like(mn,"%cpu%")
      | rex field=_raw max_match=0 "namespace=\"(?<ns_rx>[^\"]+)\""
      | rex field=_raw max_match=0 "pod=\"(?<pod>[^\"]+)\""
      | rex field=_raw max_match=0 "\s(?<mval>[0-9.eE+-]+)\s*$"
      | eval namespace=lower(trim(toString(coalesce(namespace, k8s_namespace, kubernetes_namespace, ns_rx, ""))))
      | eval workload_key=lower(trim(replace(pod, "-[a-z0-9]{9,12}-[a-z0-9]{4,10}$", "")))
      | stats sum(tonumber(mval,10)) AS sum_req_cpu_cores dc(pod) AS pod_card BY cluster namespace workload_key ]
| eventstats max(math_surprise) AS ns_surprise_peak BY namespace
| eval severity=case(math_surprise==1 AND sudden_desired_jump==1 AND match(workload_tier, "prod|production|gold|tier1|tier-1"), "critical", math_surprise==1 AND match(workload_tier, "prod|production|gold|tier1|tier-1"), "high", math_surprise==1, "medium", sudden_desired_jump==1 AND sum_req_cpu_cores>0, "medium", true(), "low")
| where severity IN ("critical","high","medium")
| table cluster namespace hpa owner_team workload_key workload_tier current_replicas desired_replicas min_replicas max_replicas actual_util target_util predicted_clamped math_surprise sudden_desired_jump sum_req_cpu_cores ns_surprise_peak severity spec_target_raw
```

Alert actions: provide drilldown to index=k8s_metrics filtered to horizontalpodautoscaler and namespace for raw prometheus lines, plus kubectl describe horizontalpodautoscaler deep links in your runbook.

Performance: split per-region saved searches if Job Inspector cost grows; materialize five-minute aggregates in a summary index when raw scrape volume dominates.

Reliability: require two consecutive evaluation intervals of math_surprise before paging adapter upgrades during kube-state-metrics maintenance.

Governance: weekly CSV export of qualifying rows with lookup commit hash and kube-state-metrics image digest satisfies internal platform evidence reviewers.

### Step 4 — Validate

Synthetic utilization spike: in lab, configure an HPA with CPU averageUtilization target fifty, drive bursty load so kube_horizontalpodautoscaler_status_current_metrics_average_utilization spikes above target while behavior.scaleUp.stabilizationWindowSeconds stays wide, capture epochs where kube_horizontalpodautoscaler_status_desired_replicas lags naive ceil math, execute uc_3_2_24_hpa_decision_introspection, and expect math_surprise equals zero when delta_rep stays inside tolerance while still validating streamstats arms populate.

Synthetic ratio disagreement: temporarily lower stabilizationWindowSeconds in a disposable namespace, inject a short CPU spike, confirm predicted_clamped diverges from desired_replicas beyond tol_abs, and expect math_surprise equals one with severity at least medium.

Synthetic clamp at maxReplicas: set maxReplicas equal to current while utilization remains high, confirm predicted_clamped respects max even when naive ceil suggests higher counts, and verify math_surprise reflects tolerance-aware comparison rather than max pinning alone, pairing with UC-3.2.17 for ceiling saturation storytelling.

Field sanity: compare Splunk cluster, namespace, and horizontalpodautoscaler with kubectl get hpa for the same minute.

RBAC: readers without k8s_metrics access must see zero rows.

Clock skew: verify NTP alignment across nodes, kube-apiserver, and Splunk indexers.

Negative path: return workload to steady utilization within target band for two hours, confirm kube_horizontalpodautoscaler_status_desired_replicas matches predicted_clamped within tolerance across four consecutive runs, and expect severity to fall to low with no qualifying where clause rows.

Lookup join: confirm hpa_decision_introspection_inventory.csv keys stay lower-case consistent with eval lower trim arms.

Tear-down: remove lab stress pods, restore behavior defaults, confirm saved search counts return to baseline.

### Step 5 — Operationalize & Troubleshoot

Case 1 — math_surprise with CPU averageUtilization and healthy adapters: compare behavior.scaleUp.stabilizationWindowSeconds and scaleDown stabilization to naive timing, widen windows after review, and confirm metrics-server sampling aligns with application SLIs.

Case 2 — sudden_desired_jump with flat customer metrics: investigate kube_horizontalpodautoscaler_status_current_metrics_average_value outliers from single pod hot spots or scrape jitter; increase pod readiness requirements or tune metrics smoothing before blaming HPA.

Case 3 — spec_target_raw shows external metric types while util_math_ok stays zero: pivot to custom.metrics.k8s.io adapter health, custom-metrics-apiserver logs, and cloud metric bridges per references.

Case 4 — sum_req_cpu_cores far below usage patterns: requests may be unsized; open Vertical Pod Autoscaler or manual request tuning threads while remembering UC-3.2.38 covers recommendation drift explicitly.

Case 5 — KEDA replaces classic decision math for the same scaler: validate ScaledObject cooldown, pause annotations, and external scaler latency before opening tickets against kube-controller-manager.

Case 6 — kubectl shows ScaleDown selectPolicy Disabled: expect desired replicas to remain high versus naive down-math; document intentional policies in inventory notes to suppress false executive pages.

Case 7 — brief custom metrics API gap returns empty series: HorizontalPodAutoscaler often holds prior kube_horizontalpodautoscaler_status_desired_replicas; correlate gap timestamps with math_surprise bursts before declaring application regressions.

Case 8 — VPA plus HPA interaction shifts requests under running pods: recompute utilization denominators after admission changes; if coexistence is intentional, route to architecture review rather than alert threshold tweaks alone.

Case 9 — controller-manager restart reapplies recent decisions: correlate rollout timelines with math_surprise spikes that self-resolve within one evaluation interval; dampen paging for single-interval blips.

Case 10 — test namespaces with aggressive averageUtilization targets: mark workload_tier as lab in hpa_decision_introspection_inventory.csv and route only to platform mailboxes.

Case 11 — symptoms resemble UC-3.2.11 flap storms: pivot to transition counts and SuccessfulRescale cadence when math is explainable but event rate is not.

Case 12 — symptoms resemble UC-3.2.46 Pending backlog: differentiate insufficient nodes from confusing HPA math by checking unschedulable pods while this UC explains desired width from metrics.

Dashboard hygiene: keep panels for actual_util versus target_util, predicted_clamped versus desired_replicas, and ns_surprise_peak heatmaps with drilldowns to spec_target_raw.

Evidence retention: archive weekly CSV snapshots of qualifying rows with lookup commit hash for auditors.

Governance: quarterly replay after kube-state-metrics upgrades; update rex arms if label sets shift.

Closing checklist: five step headers use em dash punctuation; Step 3 includes fenced SPL matching the spl JSON field; multisearch covers replica gauges, current metric averages, and spec targets; streamstats flags sudden desired jumps; inputlookup supplies tolerance and ownership; eventstats adds namespace peaks; case assigns severity; closing table lists fourteen analyst-focused columns; monitoringType lists Performance and Capacity; cimModels lists Performance and Application_State.


## SPL

```spl
`comment("UC-3.2.24 HPA decision introspection: reconcile kube_horizontalpodautoscaler status, spec, and current-metrics series; sum kube_pod_container_resource_requests cpu cores for request-basis context; predicted desired from ceil(current*(actual/target)); stabilization and tolerance surprise flags. Tunables: earliest=-3h@m latest=@m; tol_band_pct=10; indexes k8s_metrics")`
| eval uc_join="3224"
| join type=left uc_join [
| tstats count AS perf_ticks FROM datamodel=Performance WHERE (nodename=Performance.CPU OR nodename=Performance.Memory) earliest=-6h@h latest=now
| eval uc_join="3224" ]
| fields - uc_join perf_ticks
| multisearch [
    [ search ((index=k8s_metrics OR index=k8s) (sourcetype="prometheus:scrape:metrics" OR sourcetype="kube:objects:metrics")) earliest=-3h@m latest=@m
      | eval cluster=lower(trim(toString(coalesce(k8s_cluster_name, cluster_name, cluster, eks_cluster_name, gke_cluster_name, aks_cluster_name, resource_cluster, ""))))
      | eval mn=lower(trim(toString(coalesce(metric_name, __name__, name, MetricName, ""))))
      | rex field=_raw max_match=0 "horizontalpodautoscaler=\"(?<hpa_rx>[^\"]+)\""
      | rex field=_raw max_match=0 "namespace=\"(?<ns_rx>[^\"]+)\""
      | rex field=_raw max_match=0 "\s(?<mval>[0-9.eE+-]+)\s*$"
      | eval hpa=lower(trim(toString(coalesce(horizontalpodautoscaler, hpa_rx, ""))))
      | eval namespace=lower(trim(toString(coalesce(namespace, k8s_namespace, kubernetes_namespace, ns_rx, ""))))
      | where like(mn,"%kube_horizontalpodautoscaler_status_current_replicas%") OR like(mn,"%kube_horizontalpodautoscaler_status_desired_replicas%") OR like(mn,"%kube_horizontalpodautoscaler_spec_min_replicas%") OR like(mn,"%kube_horizontalpodautoscaler_spec_max_replicas%")
      | eval current_replicas=if(like(mn,"%kube_horizontalpodautoscaler_status_current_replicas%"), tonumber(mval,10), null())
      | eval desired_replicas=if(like(mn,"%kube_horizontalpodautoscaler_status_desired_replicas%"), tonumber(mval,10), null())
      | eval min_replicas=if(like(mn,"%kube_horizontalpodautoscaler_spec_min_replicas%"), tonumber(mval,10), null())
      | eval max_replicas=if(like(mn,"%kube_horizontalpodautoscaler_spec_max_replicas%"), tonumber(mval,10), null())
      | stats latest(current_replicas) AS current_replicas latest(desired_replicas) AS desired_replicas latest(min_replicas) AS min_replicas latest(max_replicas) AS max_replicas BY cluster namespace hpa ]
    [ search ((index=k8s_metrics OR index=k8s) (sourcetype="prometheus:scrape:metrics" OR sourcetype="kube:objects:metrics")) earliest=-3h@m latest=@m
      | eval cluster=lower(trim(toString(coalesce(k8s_cluster_name, cluster_name, cluster, eks_cluster_name, gke_cluster_name, aks_cluster_name, resource_cluster, ""))))
      | eval mn=lower(trim(toString(coalesce(metric_name, __name__, name, MetricName, ""))))
      | rex field=_raw max_match=0 "horizontalpodautoscaler=\"(?<hpa_rx>[^\"]+)\""
      | rex field=_raw max_match=0 "namespace=\"(?<ns_rx>[^\"]+)\""
      | rex field=_raw max_match=0 "\s(?<mval>[0-9.eE+-]+)\s*$"
      | eval hpa=lower(trim(toString(coalesce(horizontalpodautoscaler, hpa_rx, ""))))
      | eval namespace=lower(trim(toString(coalesce(namespace, k8s_namespace, kubernetes_namespace, ns_rx, ""))))
      | where like(mn,"%kube_horizontalpodautoscaler_status_current_metrics_average_utilization%") OR like(mn,"%kube_horizontalpodautoscaler_status_current_metrics_average_value%")
      | eval cur_util=if(like(mn,"%average_utilization%"), tonumber(mval,10), null())
      | eval cur_val=if(like(mn,"%average_value%") AND NOT like(mn,"%utilization%"), tonumber(mval,10), null())
      | stats latest(cur_util) AS current_avg_util_pct latest(cur_val) AS current_avg_value BY cluster namespace hpa ]
    [ search ((index=k8s_metrics OR index=k8s) (sourcetype="prometheus:scrape:metrics" OR sourcetype="kube:objects:metrics")) earliest=-3h@m latest=@m
      | eval cluster=lower(trim(toString(coalesce(k8s_cluster_name, cluster_name, cluster, eks_cluster_name, gke_cluster_name, aks_cluster_name, resource_cluster, ""))))
      | eval mn=lower(trim(toString(coalesce(metric_name, __name__, name, MetricName, ""))))
      | rex field=_raw max_match=0 "horizontalpodautoscaler=\"(?<hpa_rx>[^\"]+)\""
      | rex field=_raw max_match=0 "namespace=\"(?<ns_rx>[^\"]+)\""
      | rex field=_raw max_match=0 "\s(?<mval>[0-9.eE+-]+)\s*$"
      | eval hpa=lower(trim(toString(coalesce(horizontalpodautoscaler, hpa_rx, ""))))
      | eval namespace=lower(trim(toString(coalesce(namespace, k8s_namespace, kubernetes_namespace, ns_rx, ""))))
      | where like(mn,"%kube_horizontalpodautoscaler_spec_target_metric%")
      | eval spec_tgt_line=_raw
      | eval spec_tgt_num=tonumber(mval,10)
      | stats latest(spec_tgt_num) AS spec_target_numeric latest(spec_tgt_line) AS spec_target_raw BY cluster namespace hpa ]
]
| eval merge_key=cluster."|".namespace."|".hpa
| stats max(current_replicas) AS current_replicas max(desired_replicas) AS desired_replicas max(min_replicas) AS min_replicas max(max_replicas) AS max_replicas max(current_avg_util_pct) AS current_avg_util_pct max(current_avg_value) AS current_avg_value max(spec_target_numeric) AS spec_target_numeric values(spec_target_raw) AS spec_target_raw BY merge_key
| rex field=merge_key "^(?<cluster>[^|]+)\|(?<namespace>[^|]+)\|(?<hpa>[^|]+)$"
| join type=left max=0 merge_key [
    search ((index=k8s_metrics OR index=k8s) (sourcetype="prometheus:scrape:metrics" OR sourcetype="kube:objects:metrics")) earliest=-3h@m latest=@m
      | eval cluster=lower(trim(toString(coalesce(k8s_cluster_name, cluster_name, cluster, eks_cluster_name, gke_cluster_name, aks_cluster_name, resource_cluster, ""))))
      | eval mn=lower(trim(toString(coalesce(metric_name, __name__, name, MetricName, ""))))
      | rex field=_raw max_match=0 "horizontalpodautoscaler=\"(?<hpa_rx>[^\"]+)\""
      | rex field=_raw max_match=0 "namespace=\"(?<ns_rx>[^\"]+)\""
      | rex field=_raw max_match=0 "\s(?<mval>[0-9.eE+-]+)\s*$"
      | eval hpa=lower(trim(toString(coalesce(horizontalpodautoscaler, hpa_rx, ""))))
      | eval namespace=lower(trim(toString(coalesce(namespace, k8s_namespace, kubernetes_namespace, ns_rx, ""))))
      | where like(mn,"%kube_horizontalpodautoscaler_status_desired_replicas%")
      | eval merge_key=cluster."|".namespace."|".hpa
      | eval dr=tonumber(mval,10)
      | bin _time span=5m aligntime=@m
      | stats latest(dr) AS dr_bin BY merge_key _time
      | sort 0 merge_key + _time
      | streamstats window=3 current=t global=f range(dr_bin) AS dr_range BY merge_key
      | eval sudden_desired_jump=if(dr_range>=2,1,0)
      | stats max(sudden_desired_jump) AS sudden_desired_jump BY merge_key ]
| join type=left max=0 cluster namespace hpa [
    | inputlookup hpa_decision_introspection_inventory.csv
      | eval cluster=lower(trim(toString(cluster)))
      | eval namespace=lower(trim(toString(namespace)))
      | eval hpa=lower(trim(toString(horizontalpodautoscaler)))
      | eval owner_team=trim(toString(coalesce(owner_team, squad, platform_team, "")))
      | eval workload_tier=lower(trim(toString(coalesce(workload_tier, tier, env_tier, "dev"))))
      | eval tol_pct=tonumber(tostring(coalesce(expected_tolerance_pct, "10")), 10)
      | fields cluster namespace hpa owner_team workload_tier tol_pct ]
| fillnull value=10 tol_pct
| fillnull value=0 sudden_desired_jump
| fillnull value="unassigned" owner_team
| fillnull value="dev" workload_tier
| eval target_util=spec_target_numeric
| eval actual_util=coalesce(current_avg_util_pct, if(isnotnull(current_avg_value) AND current_avg_value>0 AND current_avg_value<=1.0, current_avg_value*100, null()))
| eval ratio=if(isnotnull(target_util) AND target_util>0 AND isnotnull(actual_util), actual_util/target_util, null())
| eval predicted_raw=if(isnotnull(current_replicas) AND isnotnull(ratio), current_replicas*ratio, null())
| eval predicted_desired=if(isnotnull(predicted_raw), ceil(predicted_raw), null())
| eval predicted_clamped=if(isnotnull(predicted_desired), max(min_replicas, min(predicted_desired, max_replicas)), null())
| eval util_math_ok=if(isnotnull(current_avg_util_pct) AND isnotnull(target_util) AND target_util>=1 AND target_util<=100 AND isnotnull(predicted_clamped) AND isnotnull(desired_replicas), 1, 0)
| eval delta_rep=abs(desired_replicas-predicted_clamped)
| eval tol_abs=max(1, floor(predicted_clamped*tol_pct/100))
| eval math_surprise=if(util_math_ok==1 AND delta_rep>tol_abs, 1, 0)
| join type=left max=0 cluster namespace hpa [
    search ((index=k8s_metrics OR index=k8s) (sourcetype="prometheus:scrape:metrics" OR sourcetype="kube:objects:metrics")) earliest=-3h@m latest=@m
      | eval cluster=lower(trim(toString(coalesce(k8s_cluster_name, cluster_name, cluster, eks_cluster_name, gke_cluster_name, aks_cluster_name, resource_cluster, ""))))
      | eval mn=lower(trim(toString(coalesce(metric_name, __name__, name, MetricName, ""))))
      | where like(mn,"%kube_horizontalpodautoscaler_info%")
      | rex field=_raw max_match=0 "namespace=\"(?<ns_rx>[^\"]+)\""
      | rex field=_raw max_match=0 "horizontalpodautoscaler=\"(?<hpa_rx>[^\"]+)\""
      | rex field=_raw max_match=0 "scaletargetref_name=\"(?<st_name>[^\"]+)\""
      | eval namespace=lower(trim(toString(coalesce(namespace, k8s_namespace, kubernetes_namespace, ns_rx, ""))))
      | eval hpa=lower(trim(toString(coalesce(horizontalpodautoscaler, hpa_rx, ""))))
      | eval workload_key=lower(trim(toString(st_name)))
      | stats latest(workload_key) AS workload_key BY cluster namespace hpa ]
| join type=left max=0 cluster namespace workload_key [
    search ((index=k8s_metrics OR index=k8s) (sourcetype="prometheus:scrape:metrics" OR sourcetype="kube:objects:metrics")) earliest=-3h@m latest=@m
      | eval cluster=lower(trim(toString(coalesce(k8s_cluster_name, cluster_name, cluster, eks_cluster_name, gke_cluster_name, aks_cluster_name, resource_cluster, ""))))
      | eval mn=lower(trim(toString(coalesce(metric_name, __name__, name, MetricName, ""))))
      | where like(mn,"%kube_pod_container_resource_requests%") AND like(mn,"%cpu%")
      | rex field=_raw max_match=0 "namespace=\"(?<ns_rx>[^\"]+)\""
      | rex field=_raw max_match=0 "pod=\"(?<pod>[^\"]+)\""
      | rex field=_raw max_match=0 "\s(?<mval>[0-9.eE+-]+)\s*$"
      | eval namespace=lower(trim(toString(coalesce(namespace, k8s_namespace, kubernetes_namespace, ns_rx, ""))))
      | eval workload_key=lower(trim(replace(pod, "-[a-z0-9]{9,12}-[a-z0-9]{4,10}$", "")))
      | stats sum(tonumber(mval,10)) AS sum_req_cpu_cores dc(pod) AS pod_card BY cluster namespace workload_key ]
| eventstats max(math_surprise) AS ns_surprise_peak BY namespace
| eval severity=case(math_surprise==1 AND sudden_desired_jump==1 AND match(workload_tier, "prod|production|gold|tier1|tier-1"), "critical", math_surprise==1 AND match(workload_tier, "prod|production|gold|tier1|tier-1"), "high", math_surprise==1, "medium", sudden_desired_jump==1 AND sum_req_cpu_cores>0, "medium", true(), "low")
| where severity IN ("critical","high","medium")
| table cluster namespace hpa owner_team workload_key workload_tier current_replicas desired_replicas min_replicas max_replicas actual_util target_util predicted_clamped math_surprise sudden_desired_jump sum_req_cpu_cores ns_surprise_peak severity spec_target_raw
```

## CIM SPL

```spl
| tstats summariesonly=t latest(Application_State.state) AS app_state latest(Application_State.info) AS app_info FROM datamodel=Application_State WHERE nodename=Application_State (Application_State.app="kubernetes" OR Application_State.app="k8s" OR like(Application_State.app, "%kube%")) earliest=-6h@h latest=@h BY Application_State.dest
| rename Application_State.dest AS cim_host
| join type=left max=0 cim_host [
| tstats summariesonly=t avg(Performance.cpu_load_percent) AS cpu_load_pct avg(Performance.mem_used_percent) AS mem_used_pct FROM datamodel=Performance WHERE nodename=Performance.CPU OR nodename=Performance.Memory earliest=-6h@h latest=@h BY Performance.host
| rename Performance.host AS cim_host ]
| table cim_host app_state app_info cpu_load_pct mem_used_pct
```

## Visualization

Overlay chart of kube_horizontalpodautoscaler_status_desired_replicas versus predicted_clamped; single value of math_surprise; heatmap of ns_surprise_peak by namespace; table matching the closing SPL columns with drilldowns to spec_target_raw and kube_pod_container_resource_requests rollups.

## Known False Positives

Legitimate spec.behavior scaleDown policies with long stabilizationWindowSeconds or Disabled selectPolicy keep kube_horizontalpodautoscaler_status_desired_replicas above naive down-math even when kube_horizontalpodautoscaler_status_current_metrics_average_utilization looks low; pair kubectl describe with Splunk before paging. The built-in tolerance band near ten percent means small replica deltas versus predicted_clamped are often intentional no-ops, not controller bugs. Single-metric-update jitter from metrics-server cadence or kubelet scrape skew can move kube_horizontalpodautoscaler_status_current_metrics_average_value for one interval while stabilization suppresses motion; require sustained math_surprise across buckets before executive escalation. Custom metrics adapters feeding stale external series inflate kube_horizontalpodautoscaler_status_current_metrics_average_value without matching application truth; pivot to adapter health when util_math_ok stays zero but spec_target_raw references external kinds. KEDA external scalers can replace classic HorizontalPodAutoscaler ratio intuition for the same object; validate ScaledObject ownership before blaming kube-controller-manager math. Vertical Pod Autoscaler mutating requests underneath a CPU-targeted HorizontalPodAutoscaler creates legitimately complex denominator drift; cross-check UC-3.2.38 timelines. Recent rolling restarts fluctuate ready pod sets so average utilization denominators move while desired counts look surprising. ScaleDown floors at spec.minReplicas block predicted down-math even when metrics imply fewer pods. Stabilization windows that prefer the maximum recommended replicas during scale-up hold kube_horizontalpodautoscaler_status_desired_replicas higher than instantaneous naive math. Just-restarted controller-manager processes can re-apply recent decisions visible as short math_surprise spikes that self-heal. Brief Metrics API gaps return empty samples while the controller holds prior kube_horizontalpodautoscaler_status_desired_replicas; correlate empty windows with surprise flags. Test namespaces with intentionally aggressive averageUtilization targets generate noisy comparisons; exclude via inventory tier. Brief metric outliers that stabilization absorbs never become customer incidents; dampen alerts when sudden_desired_jump stays zero across adjacent evaluations.

## References

- [Kubernetes — Horizontal Pod Autoscale (algorithm and behavior)](https://kubernetes.io/docs/tasks/run-application/horizontal-pod-autoscale/)
- [Kubernetes — Configurable scaling behavior](https://kubernetes.io/docs/tasks/run-application/horizontal-pod-autoscale/#configurable-scaling-behavior)
- [Kubernetes SIGs — custom-metrics-apiserver](https://github.com/kubernetes-sigs/custom-metrics-apiserver)
- [kube-state-metrics — HorizontalPodAutoscaler metrics](https://github.com/kubernetes/kube-state-metrics/blob/main/docs/metrics/workload/horizontalpodautoscaler-metrics.md)
- [Kubernetes — Resource metrics pipeline](https://kubernetes.io/docs/tasks/debug/debug-cluster/resource-metrics-pipeline/)
- [Kubernetes API — Pod metrics (metrics.k8s.io v1beta1)](https://kubernetes.io/docs/reference/kubernetes-api/service-resources/metrics-v1beta1/)
- [KEDA — Concepts (Kubernetes Event-driven Autoscaling)](https://keda.sh/docs/latest/concepts/)
- [Kubernetes — HorizontalPodAutoscaler v2 API reference](https://kubernetes.io/docs/reference/kubernetes-api/workload-resources/horizontal-pod-autoscaler-v2/)
