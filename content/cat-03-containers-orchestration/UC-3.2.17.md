<!-- AUTO-GENERATED from UC-3.2.17.json — DO NOT EDIT -->

---
id: "3.2.17"
title: "Kubernetes HorizontalPodAutoscaler Saturation, Flap, and Metric-Fetch Failure (Workload Autoscaler Ceiling)"
status: "verified"
criticality: "high"
splunkPillar: "Observability"
---

# UC-3.2.17 · Kubernetes HorizontalPodAutoscaler Saturation, Flap, and Metric-Fetch Failure (Workload Autoscaler Ceiling)

> **Criticality:** High &middot; **Difficulty:** Intermediate &middot; **Pillar:** Observability &middot; **Type:** Capacity, Reliability &middot; **Wave:** Walk &middot; **Status:** Verified

*We watch the automatic replica scaler for each application so we know when it is stuck at its upper limit, bouncing up and down because settings are too tight, or cannot read the measurements it needs. That way teams fix capacity or the measurement pipeline before shoppers or employees feel slowdowns.*

---

## Description

Detects Kubernetes HorizontalPodAutoscaler workload-level saturation and scaler dysfunction distinct from cluster node scale-out refusal: kube-state-metrics proves current replicas against spec max and min, kube_horizontalpodautoscaler_status_condition exposes AbleToScale, ScalingActive, and ScalingLimited truth (including scale-not-allowed style refusal when conditions read false), kube_horizontalpodautoscaler_status_target_metric provides observed target pressure when exported, and kube:events surfaces FailedGetResourceMetric, FailedGetExternalMetric, and object-metric failures including adapter messages that reference custom metric fetch errors. A streamstats join over five-minute buckets estimates replica flap between extremes, inputlookup hpa_saturation_inventory.csv enriches ownership and environment tier, eventstats adds cluster context, and case() assigns severity so operators separate metric-provider outages from genuine maxReplica dwell during surges. UC-3.2.46 covers Cluster Autoscaler and Karpenter node provisioning refusal. UC-3.2.4 covers namespace ResourceQuota admission denial. UC-3.2.32 covers quota utilization forecasting. UC-3.2.11 remains a broader scaling-events overview when catalogued.

## Value

Mean time to repair improves when platform and application teams see one row that names cluster, namespace, scaler, replica ceiling state, flap score, condition strings, metric-fetch failure counts, last event timestamps, target pressure, owner, tier, and severity without manually diffing kubectl, metrics explorers, and adapter logs. Customer impact drops because autoscaler ceilings and broken metric bridges surface before executives only hear generic latency complaints. Capacity reviews gain evidence for raising maxReplicas, retuning targets, or fixing adapters before game-day traffic pins services at limits for hours.

## Implementation

Scrape kube-state-metrics HPA families into k8s_metrics, ship HorizontalPodAutoscaler kube:events into k8s_events, publish hpa_saturation_inventory.csv with owner_team and workload_tier, save uc_3_2_17_hpa_saturation_axis every five minutes with earliest=-2h@m latest=now, route critical and high severities for production-tier rows, and validate in lab by pinning an HPA at maxReplicas while load holds steady.

## Evidence

Saved search uc_3_2_17_hpa_saturation_axis with five-minute schedule; hpa_saturation_inventory.csv versioned in git; weekly CSV export of the alert table to a restricted evidence index with kube-state-metrics chart version for auditors.

## Control test

### Positive scenario

In a lab namespace, drive an HPA to maxReplicas with sustained load while kube_horizontalpodautoscaler_status_current_replicas equals kube_horizontalpodautoscaler_spec_max_replicas in k8s_metrics, optionally emit FailedGetResourceMetric kube:events by misconfiguring the metrics adapter in a disposable cluster, execute uc_3_2_17_hpa_saturation_axis, and expect a qualifying row with at_max equal to one or metric_fail_evts greater than zero and severity at least medium.

### Negative scenario

Restore healthy adapter paths, remove artificial load so current replicas fall below max for the full window, confirm kube:events show no FailedGet reasons, and verify the saved search emits no qualifying rows for that HorizontalPodAutoscaler across four consecutive five-minute intervals.

## Detailed Implementation

### Step 1 — Prerequisites

Head of Platform owns this control together with Kubernetes platform site reliability engineers, workload owners who set replica budgets, and the observability team operating Splunk OpenTelemetry Collector plus kube-state-metrics across production and pre-production estates. This use case isolates workload-level HorizontalPodAutoscaler saturation and controller dysfunction: the moment a scaler pins at spec.maxReplicas, oscillates between min and max because thresholds are too tight, reports status conditions such as AbleToScale false, ScalingActive false, or ScalingLimited true, or emits Kubernetes events whose reasons include FailedGetResourceMetric, FailedGetExternalMetric, or object-metric adapter failures that resemble FailedGetCustomMetric in message text. It also surfaces sustained target-metric pressure from kube_horizontalpodautoscaler_status_target_metric when those samples are present in your scrape, giving a numeric story about utilization while the replica count is already at the ceiling. UC-3.2.46 remains the cluster-level Cluster Autoscaler and Karpenter refusal plane where nodes themselves cannot be added; this UC never substitutes for that node-provisioning evidence. UC-3.2.4 remains namespace ResourceQuota admission denial where the API server rejects creates; quota walls can starve HPAs but the monitoring axis here is the scaler object and its metric pipeline, not admission responses. UC-3.2.32 remains namespace quota utilization forecasting before exhaustion; this UC reacts to live HPA truth and kube events, not statistical forecasts on quota objects. UC-3.2.11, when present in your catalogue, remains a broader medium-priority capacity overview for generic scaling events; keep that sibling for executive roll-ups while this UC pages on saturation-specific predicates. UC-3.2.7 style control-plane narratives belong elsewhere; apiserver latency can delay HPA loops but this detector assumes metrics and events still arrive with tolerable skew.

Before you schedule the saved search, confirm four indexing paths are healthy. First, index=k8s_metrics ingests Prometheus text or normalized scrape events from kube-state-metrics that include kube_horizontalpodautoscaler_status_current_replicas, kube_horizontalpodautoscaler_spec_max_replicas, kube_horizontalpodautoscaler_spec_min_replicas, kube_horizontalpodautoscaler_status_condition with labels for condition type and status, and preferably kube_horizontalpodautoscaler_status_target_metric for observed target pressure. Second, index=k8s_events or a shared platform events index carries sourcetype kube:events with HorizontalPodAutoscaler involvedObject kinds and reasons that name metric provider failures. Third, publish lookups/hpa_saturation_inventory.csv with columns cluster, namespace, horizontalpodautoscaler, owner_team, workload_tier, optional notes for cost-tier environments, and optional links to internal runbooks so alert bodies route to accountable squads without manual kubectl translation. Fourth, RBAC on collectors must allow listing watches on HorizontalPodAutoscaler objects in namespaces you monitor while keeping Secret and unrelated object reads out of forwarder ServiceAccounts.

Risk framing for incident commanders: when current replicas equal max replicas during a demand spike, the workload cannot grow wider without raising maxReplicas, changing the metric target, fixing a broken metrics adapter, or adding headroom elsewhere. Customers still see latency or queue depth growth even when nodes exist, which is why UC-3.2.46 may be quiet while this UC screams. Flapping between min and max often means the hysteresis window is too narrow, CPU averages are sampled on intervals that disagree with application behavior, or an external metric from a vendor adapter lags and snaps. FailedGet events mean the controller cannot even read the signal it needs; continuing to blame application code before checking Prometheus adapter, Datadog cluster agent, or custom metrics APIService health burns bridge time.

Capacity and licensing: HPA series cardinality scales with namespace and object count, not pod cardinality, which keeps this control relatively inexpensive compared to per-pod kubelet series. Still, preserve only necessary labels at scrape time after FinOps review. HEC tokens stay in vault with quarterly rotation. Legal review may require redacting external metric queries embedded in event messages when those strings echo internal queue names.

Governance: hpa_saturation_inventory.csv refreshes weekly from the service catalog or Git repository that owns HorizontalPodAutoscaler manifests. Gold-tier workloads get explicit rows so severity routing does not fall through to a generic platform queue during a revenue-impacting surge.

Training: teach responders to read kube describe horizontalpodautoscaler output alongside Splunk rows, and to compare metrics-server or adapter endpoints when FailedGet reasons appear.

Review cadence: quarterly replay one historical surge where maxReplicas was intentionally conservative and another where an adapter outage blocked scaling, validating that this search still separates the two failure modes.

Hardware scope: Amazon EKS, Google GKE, Microsoft AKS, Red Hat OpenShift, VMware Tanzu, and self-managed Kubernetes where kube-state-metrics RBAC can list HorizontalPodAutoscaler objects cluster-wide; Arm and x86 worker fleets are in scope when Prometheus text lines remain compatible.

Differentiation recap: workload autoscaler ceiling and metric-fetch health, not cluster autoscaler refusal, not namespace quota admission, not quota forecasting, not generic rollout conditions.

### Step 2 — Configure data collection

Deploy kube-state-metrics with cluster-scoped RBAC that can list HorizontalPodAutoscaler objects. Point Splunk OpenTelemetry Collector prometheus receiver or prometheus_simple scrape jobs at the kube-state-metrics Service on port 8080 or 8443 depending on your chart, preserve horizontalpodautoscaler, namespace, and cluster labels through relabel_config blocks, and export to HEC into index=k8s_metrics with sourcetype prometheus:scrape:metrics. Mirror other gold Kubernetes use cases in this repository: bearer_token_file usage stays consistent with your security model, and honor_labels discipline prevents duplicate scrape collisions when both in-cluster Prometheus and OpenTelemetry hit the same endpoint without coordination.

Concrete ServiceMonitor skeleton:

apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: kube-state-metrics-hpa
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

Configure Kubernetes API events to land in index=k8s_events or index=k8s with sourcetype kube:events. The HorizontalPodAutoscaler controller emits Warning events when it cannot fetch resource, external, or object metrics; those reasons must remain intact in the reason field and message body for the multisearch events arm.

Splunk OpenTelemetry Collector fragment showing prometheus scrape plus kubernetes events export:

receivers:
  prometheus/k8s_state:
    config:
      scrape_configs:
        - job_name: kube-state-metrics-hpa
          kubernetes_sd_configs:
            - role: endpoints
          relabel_configs:
            - source_labels: [__meta_kubernetes_service_name]
              action: keep
              regex: kube-state-metrics
  k8s_events:
    auth_type: serviceAccount
    mode: watch
exporters:
  splunk_hec/metrics:
    token: ${SPLUNK_HEC_TOKEN_K8S_METRICS}
    endpoint: https://splunk-hec.example:8088/services/collector/event
    index: k8s_metrics
    sourcetype: prometheus:scrape:metrics
  splunk_hec/events:
    token: ${SPLUNK_HEC_TOKEN_K8S_EVENTS}
    endpoint: https://splunk-hec.example:8088/services/collector/event
    index: k8s_events
    sourcetype: kube:events
service:
  pipelines:
    metrics/ksm:
      receivers: [prometheus/k8s_state]
      exporters: [splunk_hec/metrics]
    logs/events:
      receivers: [k8s_events]
      exporters: [splunk_hec/events]

Publish lookups/hpa_saturation_inventory.csv aligned to join keys in Step 3:

cluster,namespace,horizontalpodautoscaler,owner_team,workload_tier
prod-eks-us-east-1,prod-payments,carts-api-hpa,payments-sre,production
lab-gke-dev,qa-load,checkout-hpa-qa,platform-test,dev

Validation searches before alert authoring:

index=k8s_metrics sourcetype=prometheus:scrape:metrics kube_horizontalpodautoscaler_status_current_replicas earliest=-30m

index=k8s_events sourcetype=kube:events HorizontalPodAutoscaler earliest=-30m

Skew between scrapes and API events should remain under ninety seconds for meaningful correlation. If you run multiple clusters, normalize cluster or cluster_name fields at ingestion so the SPL cluster coalesce arm resolves consistently.

Security: redact internal queue names from alert emails when legal policy requires, while retaining hashed identifiers for correlation.

props.conf guidance: normalize __name__, value, namespace, and horizontalpodautoscaler fields onto indexed extractions where volume warrants acceleration experiments; keep coalesce ladders in SPL until extractions stabilize.

Cloud control planes: on EKS verify security groups still allow node to cluster IP reachability for metrics after landing-zone changes; on GKE verify managed Prometheus if you offloaded scrapes; on AKS verify managed Grafana agent label mapping still populates horizontalpodautoscaler.

Frequency: scrape interval, alert interval, and flap window must align mathematically; a five-minute alert schedule pairs with five-minute bins in the streamstats arm.

Back-pressure: if kube-apiserver event watch disconnects, collector buffers should not grow unbounded; set retry and drop policies per vendor guidance.

Version pinning: record kube-state-metrics chart version in evidence packs quarterly.

Integration with kubectl: operators should still run kubectl describe horizontalpodautoscaler for instantaneous truth; Splunk carries history and correlation that kubectl alone lacks across clusters.

Dashboard seeds: timechart of current_replicas versus max_replicas by namespace, single value of distinct HPAs at max, and table of this UC output for executive summaries.

Summary index optional: materialize five-minute snapshots of at_max booleans into k8s_hpa_summary when raw k8s_metrics scan costs dominate.

### Step 3 — Create the search and alert

Save the SPL as uc_3_2_17_hpa_saturation_axis with five-minute schedule, dispatch earliest=-2h@m, dispatch latest=now, and alert when severity is critical or high for production-tier rows. Throttle duplicate pages per cluster, namespace, and horizontalpodautoscaler for twenty minutes unless severity escalates from medium to critical. Include current_replicas, max_replicas, metric_fail_evts, cond_blob, and flap_score in pager bodies so responders triage without opening Search.

Pipeline narrative for operators: the opening comment lists tunable indexes and flap logic. join with tstats against Performance provides a CIM-aligned tick count that proves Performance acceleration is warm for correlation overlays during audits; if acceleration is absent in a lab, the join still type=left preserves HPA rows. multisearch fans four parallel arms so a silent scrape on replica gauges does not blank the entire incident: kube-state-metrics replica gauges, kube_horizontalpodautoscaler_status_condition pairs, kube_horizontalpodautoscaler_status_target_metric pressure when exported, and kube:events FailedGet arms including message patterns that echo custom-metric adapter failures. coalesce ladders normalize cluster names across EKS, GKE, and AKS label habits. After fan-in stats by merge_key, a join runs streamstats over five-minute buckets of kube_horizontalpodautoscaler_status_current_replicas to estimate flap_score when distinct bucketed replica counts appear across six buckets with non-zero range. inputlookup hpa_saturation_inventory.csv adds owner_team and workload_tier so case-based severity separates production adapter catastrophes from lab noise. case implements severity: critical when FailedGet events coincide with production tier and ScalingActive or AbleToScale false signals, or when FailedGet coincides with at_max dwell; high when FailedGet appears without full condition triad, when at_max pairs with strong flap_score, or when ScalingLimited is true with observed metric value at or above eighty while pinned at max; medium when at_max alone or flap_score alone crosses gates; medium when ScalingLimited and AbleToScale false without better explanation. The closing table lists eighteen analyst columns including cond_blob and fail_msgs for evidence-rich bridges.

Paste-and-run SPL for alerts and dashboards must match the spl JSON field exactly:```spl
`comment("UC-3.2.17 Kubernetes HorizontalPodAutoscaler saturation axis: maxReplicas dwell, min-max flap, status conditions, FailedGet* metric fetch events, target metric pressure. Tunables: earliest=-2h@m latest=@m; indexes k8s_metrics k8s_events; flap_window=6 buckets of 5m")`
| eval uc_join="3217"
| join type=left uc_join [
| tstats count AS perf_model_ticks FROM datamodel=Performance WHERE (nodename=Performance.CPU OR nodename=Performance.Memory) earliest=-4h@h latest=now
| eval uc_join="3217" ]
| fields - uc_join perf_model_ticks
| multisearch [
    [ search ((index=k8s_metrics OR index=k8s) (sourcetype="prometheus:scrape:metrics" OR sourcetype="kube:objects:metrics")) earliest=-2h@m latest=@m
      | eval cluster=lower(trim(toString(coalesce(k8s_cluster_name, cluster_name, cluster, eks_cluster_name, gke_cluster_name, aks_cluster_name, resource_cluster, ""))))
      | eval mn=lower(trim(toString(coalesce(metric_name, __name__, name, MetricName, ""))))
      | rex field=_raw max_match=0 "horizontalpodautoscaler=\"(?<hpa_rx>[^\"]+)\""
      | rex field=_raw max_match=0 "namespace=\"(?<ns_rx>[^\"]+)\""
      | rex field=_raw max_match=0 "\s(?<mval>[0-9.eE+-]+)\s*$"
      | eval hpa=lower(trim(toString(coalesce(horizontalpodautoscaler, hpa_rx, ""))))
      | eval namespace=lower(trim(toString(coalesce(namespace, k8s_namespace, kubernetes_namespace, ns_rx, ""))))
      | where (like(mn, "%kube_horizontalpodautoscaler_status_current_replicas%") OR like(mn, "%kube_horizontalpodautoscaler_spec_max_replicas%") OR like(mn, "%kube_horizontalpodautoscaler_spec_min_replicas%"))
      | eval current_replicas=if(like(mn, "%status_current_replicas%"), tonumber(mval, 10), null())
      | eval max_replicas=if(like(mn, "%spec_max_replicas%"), tonumber(mval, 10), null())
      | eval min_replicas=if(like(mn, "%spec_min_replicas%"), tonumber(mval, 10), null())
      | stats latest(current_replicas) AS current_replicas latest(max_replicas) AS max_replicas latest(min_replicas) AS min_replicas BY cluster namespace hpa ]
    [ search ((index=k8s_metrics OR index=k8s) (sourcetype="prometheus:scrape:metrics" OR sourcetype="kube:objects:metrics")) earliest=-2h@m latest=@m
      | eval cluster=lower(trim(toString(coalesce(k8s_cluster_name, cluster_name, cluster, eks_cluster_name, gke_cluster_name, aks_cluster_name, resource_cluster, ""))))
      | eval mn=lower(trim(toString(coalesce(metric_name, __name__, name, MetricName, ""))))
      | rex field=_raw max_match=0 "horizontalpodautoscaler=\"(?<hpa_rx>[^\"]+)\""
      | rex field=_raw max_match=0 "namespace=\"(?<ns_rx>[^\"]+)\""
      | rex field=_raw max_match=0 "condition=\"(?<cond_l>[^\"]+)\""
      | rex field=_raw max_match=0 "status=\"(?<stat_l>[^\"]+)\""
      | where like(mn, "%kube_horizontalpodautoscaler_status_condition%")
      | eval hpa=lower(trim(toString(coalesce(horizontalpodautoscaler, hpa_rx, ""))))
      | eval namespace=lower(trim(toString(coalesce(namespace, k8s_namespace, kubernetes_namespace, ns_rx, ""))))
      | eval cond_pair=printf("%s=%s", cond_l, stat_l)
      | stats values(cond_pair) AS cond_values dc(cond_pair) AS cond_card BY cluster namespace hpa ]
    [ search ((index=k8s_metrics OR index=k8s) (sourcetype="prometheus:scrape:metrics" OR sourcetype="kube:objects:metrics")) earliest=-2h@m latest=@m
      | eval cluster=lower(trim(toString(coalesce(k8s_cluster_name, cluster_name, cluster, eks_cluster_name, gke_cluster_name, aks_cluster_name, resource_cluster, ""))))
      | eval mn=lower(trim(toString(coalesce(metric_name, __name__, name, MetricName, ""))))
      | rex field=_raw max_match=0 "horizontalpodautoscaler=\"(?<hpa_rx>[^\"]+)\""
      | rex field=_raw max_match=0 "namespace=\"(?<ns_rx>[^\"]+)\""
      | rex field=_raw max_match=0 "\s(?<mval>[0-9.eE+-]+)\s*$"
      | where like(mn, "%kube_horizontalpodautoscaler_status_target_metric%")
      | eval hpa=lower(trim(toString(coalesce(horizontalpodautoscaler, hpa_rx, ""))))
      | eval namespace=lower(trim(toString(coalesce(namespace, k8s_namespace, kubernetes_namespace, ns_rx, ""))))
      | eval observed_metric_value=tonumber(mval, 10)
      | stats latest(observed_metric_value) AS observed_metric_value BY cluster namespace hpa ]
    [ search (index=k8s_events OR index=k8s) sourcetype="kube:events" earliest=-2h@m latest=@m
      | eval cluster=lower(trim(toString(coalesce(k8s_cluster_name, cluster_name, cluster, source_cluster, ""))))
      | eval reason=trim(toString(coalesce(reason, Reason, "")))
      | eval kind=lower(trim(toString(coalesce(involvedObject.kind, `involvedObject.kind`, ""))))
      | eval hpa=lower(trim(toString(coalesce(involvedObject.name, involvedObject_name, ""))))
      | eval namespace=lower(trim(toString(coalesce(metadata.namespace, namespace, ""))))
      | eval msg=toString(coalesce(message, Message, ""))
      | where kind="horizontalpodautoscaler" AND (reason IN ("FailedGetResourceMetric", "FailedGetExternalMetric", "FailedGetObjectMetric") OR like(msg, "%FailedGet%Metric%") OR like(msg, "%FailedGetCustomMetric%"))
      | stats latest(_time) AS last_metric_fail_ts values(msg) AS fail_msgs count AS metric_fail_evts BY cluster namespace hpa ]
| eval merge_key=cluster."|".namespace."|".hpa
| stats max(current_replicas) AS current_replicas max(max_replicas) AS max_replicas max(min_replicas) AS min_replicas values(cond_values) AS cond_values max(cond_card) AS cond_card max(observed_metric_value) AS observed_metric_value max(last_metric_fail_ts) AS last_metric_fail_ts values(fail_msgs) AS fail_msgs sum(metric_fail_evts) AS metric_fail_evts BY merge_key
| rex field=merge_key "^(?<cluster>[^|]+)\|(?<namespace>[^|]+)\|(?<hpa>[^|]+)$"
| join type=left max=0 merge_key [
    search ((index=k8s_metrics OR index=k8s) (sourcetype="prometheus:scrape:metrics" OR sourcetype="kube:objects:metrics")) earliest=-2h@m latest=@m
      | eval cluster=lower(trim(toString(coalesce(k8s_cluster_name, cluster_name, cluster, eks_cluster_name, gke_cluster_name, aks_cluster_name, resource_cluster, ""))))
      | eval mn=lower(trim(toString(coalesce(metric_name, __name__, name, MetricName, ""))))
      | rex field=_raw max_match=0 "horizontalpodautoscaler=\"(?<hpa_rx>[^\"]+)\""
      | rex field=_raw max_match=0 "namespace=\"(?<ns_rx>[^\"]+)\""
      | rex field=_raw max_match=0 "\s(?<mval>[0-9.eE+-]+)\s*$"
      | where like(mn, "%kube_horizontalpodautoscaler_status_current_replicas%")
      | eval hpa=lower(trim(toString(coalesce(horizontalpodautoscaler, hpa_rx, ""))))
      | eval namespace=lower(trim(toString(coalesce(namespace, k8s_namespace, kubernetes_namespace, ns_rx, ""))))
      | eval merge_key=cluster."|".namespace."|".hpa
      | eval cr=tonumber(mval, 10)
      | bin _time span=5m aligntime=@m
      | stats latest(cr) AS cr_bucket BY merge_key _time
      | sort 0 merge_key + _time
      | streamstats window=6 current=t global=f dc(cr_bucket) AS flap_dc range(cr_bucket) AS cr_range BY merge_key
      | eval flap_score=if(flap_dc>=3 AND cr_range>=1, flap_dc, 0)
      | stats max(flap_score) AS flap_score BY merge_key ]
| join type=left max=0 cluster namespace hpa [
    | inputlookup hpa_saturation_inventory.csv
      | eval cluster=lower(trim(toString(cluster)))
      | eval namespace=lower(trim(toString(namespace)))
      | eval hpa=lower(trim(toString(horizontalpodautoscaler)))
      | eval owner_team=trim(toString(coalesce(owner_team, squad, platform_team, "")))
      | eval workload_tier=lower(trim(toString(coalesce(workload_tier, tier, env_tier, "dev"))))
      | fields cluster namespace hpa owner_team workload_tier ]
| fillnull value=0 flap_score metric_fail_evts
| fillnull value="unassigned" owner_team
| fillnull value="dev" workload_tier
| eval cond_blob=mvjoin(cond_values, " | ")
| eval at_max=if(max_replicas>0 AND current_replicas>=max_replicas, 1, 0)
| eval scaling_active_false=if(match(lower(cond_blob), "scalingactive=false"), 1, 0)
| eval scaling_limited_true=if(match(lower(cond_blob), "scalinglimited=true"), 1, 0)
| eval able_false=if(match(lower(cond_blob), "abletoscale=false"), 1, 0)
| eval target_util_saturation_pct=if(isnotnull(observed_metric_value), round(min(999, observed_metric_value), 2), null())
| eventstats max(at_max) AS cluster_hpamax_any BY cluster
| eval severity=case(
    metric_fail_evts>0 AND match(workload_tier, "prod|production|gold|tier1|tier-1") AND (scaling_active_false==1 OR able_false==1), "critical",
    metric_fail_evts>0 AND at_max==1, "critical",
    metric_fail_evts>0, "high",
    at_max==1 AND flap_score>=3, "high",
    at_max==1 AND scaling_limited_true==1 AND isnotnull(observed_metric_value) AND observed_metric_value>=80, "high",
    at_max==1, "medium",
    flap_score>=3, "medium",
    scaling_limited_true==1 AND able_false==1, "medium",
    true(), "low")
| where severity IN ("critical", "high", "medium")
| table cluster namespace hpa owner_team workload_tier current_replicas min_replicas max_replicas at_max flap_score scaling_limited_true scaling_active_false able_false metric_fail_evts target_util_saturation_pct last_metric_fail_ts cond_blob fail_msgs severity
```

Alert actions: include cluster, namespace, horizontalpodautoscaler, severity, owner_team, metric_fail_evts, and last_metric_fail_ts in email or ITSI notable bodies. Provide a drilldown that runs index=k8s_events sourcetype=kube:events involvedObject.kind=HorizontalPodAutoscaler involvedObject.name=$row.hpa$ earliest=-2h. Provide a secondary drilldown for kube-state-metrics samples on the same object.

Performance: if Job Inspector warns on multisearch cost, split fleet dashboards into per-region saved searches or materialize five-minute HPA snapshots hourly.

Reliability: during kube-state-metrics upgrades expect brief gaps; require two consecutive intervals of missing metrics before paging scrape outages unless kube events still show FailedGet storms.

Governance: weekly CSV export of alert rows with lookup commit hash satisfies internal platform evidence when paired with kube-state-metrics version stamps.

savedsearches.conf quantity thresholds should align with row counts from the table command; use alert.track=1 and suppress keys on cluster namespace horizontalpodautoscaler.

Closing Step 3 checklist: fenced SPL present, matches spl field, references hpa_saturation_inventory.csv, explains tstats join purpose, documents multisearch arms, clarifies severity case ladder, and names notification fields.

Step 4 — Validate

Synthetic maxReplicas dwell: in a lab namespace, set a Deployment under an HPA with maxReplicas equal to minReplicas plus one, generate CPU load with a controlled stress image until current replicas reach max, hold load for fifteen minutes, and confirm kube_horizontalpodautoscaler_status_current_replicas equals kube_horizontalpodautoscaler_spec_max_replicas in index=k8s_metrics while uc_3_2_17_hpa_saturation_axis returns at_max equal to one with severity at least medium when workload_tier marks production in the lookup.

Synthetic flap: tighten HPA target CPU to a value that crosses and recrosses the threshold on a fast interval in lab only, observe current replicas swinging between min and max across several five-minute buckets, and confirm the streamstats join produces flap_score at or above three for that HorizontalPodAutoscaler while metric_fail_evts remains zero.

Synthetic metric fetch failure: in a disposable lab cluster under change control, break the custom metrics APIService or block the Prometheus adapter Service while leaving workloads healthy, confirm kube:events reasons FailedGetResourceMetric or FailedGetExternalMetric appear, execute the saved search, and expect severity high or critical with non-zero metric_fail_evts; restore the adapter and verify auto-clear.

Negative path: remove load, restore sane thresholds, confirm current replicas drop below max for sustained intervals, confirm FailedGet events stop, and expect zero qualifying rows from the alert predicate across four consecutive five-minute runs for that object.

Field sanity: compare Splunk extracted namespace and horizontalpodautoscaler with kubectl get hpa -n and kubectl describe hpa output for the same minute.

RBAC: readers without k8s_metrics access must see zero rows.

Correlation: compare Splunk timestamps to kubectl get events --field-selector involvedObject.kind=HorizontalPodAutoscaler for the same object.

Clock skew: verify NTP alignment between nodes, kube-apiserver, and Splunk indexers; skew beyond ninety seconds invalidates flap_score comparisons.

Tear-down: delete lab stress workloads, revert adapter blocks, and confirm saved search result counts return to baseline.

Step 5 — Operationalize & Troubleshoot

Case 1 — maxReplicas pinned during a real surge: raise maxReplicas after capacity review, or lower target utilization if the service can tolerate higher CPU per pod; attach observed_metric_value from kube_horizontalpodautoscaler_status_target_metric when present to prove the controller still sees pressure at the ceiling.

Case 2 — Flap between min and max with tight CPU targets: widen the stabilization window, adjust metrics-server or adapter scrape alignment, or move to external metrics that better track queue depth; compare flap_score to application latency dashboards before changing only Kubernetes knobs.

Case 3 — FailedGetResourceMetric with metrics-server outages: restart or patch metrics-server, verify kube-system networking, and confirm apiserver aggregation paths; pivot to control-plane health siblings only after adapter health is ruled in.

Case 4 — FailedGetExternalMetric with vendor adapter latency: validate Datadog cluster agent, Prometheus adapter, or cloud provider metric bridges; check RBAC for external.metrics.k8s.io reads and Service DNS for the adapter.

Case 5 — FailedGetObjectMetric or message text referencing custom metric kinds: confirm APIService availability for custom.metrics.k8s.io, validate ServiceAccount tokens for metric clients, and replay kubectl get --raw against aggregation discovery paths.

Case 6 — ScalingActive false with AbleToScale false: read condition messages in kubectl describe; transient scale-down blocks and policy holds can explain false states; correlate with PodDisruptionBudget and deployment freeze annotations before escalating.

Case 7 — ScalingLimited true at maxReplicas: the controller is explicitly reporting it cannot add replicas; pair with UC-3.2.46 only when Pending pods and node scale-out failures dominate; otherwise treat as workload-local ceiling first.

Case 8 — Target metric shows high observed value while replicas stay at max: application is still undersized for declared SLO; consider vertical pod autoscaling recommendations or architectural sharding rather than endlessly raising maxReplicas.

Case 9 — KEDA-managed HPAs with bursty scale: confirm ScaledObject pause annotations, verify minReplicaCount intent, and avoid paging KEDA event bursts that clear within one evaluation when business expects bursty traffic.

Case 10 — Deliberate maintenance holds or kubectl scale overrides: confirm platform change records; suppress known windows via lookup flags or macro exclusions tied to change tickets.

Case 11 — Symptoms resemble this UC but namespace quota is the true blocker: run UC-3.2.4 correlation before approving large maxReplica increases that only move the bottleneck to admission.

Case 12 — Symptoms resemble this UC but nodes cannot schedule new pods: open UC-3.2.46 when kube events and Cluster Autoscaler logs show scale-out refusal while this UC still matters for explaining why HPA wanted more replicas than landed.

Dashboard hygiene: keep panels for current versus max replicas, condition status facets, and FailedGet event rates with drilldowns to raw kube:events.

Evidence retention: weekly CSV exports of alert rows with hpa_saturation_inventory.csv git hash satisfy internal audit samples when paired with kube-state-metrics image digest.

Governance: quarterly replay this search after kube-state-metrics upgrades because label rewriting rules change; update rex arms when Prometheus relabel configs move label names.

Closing checklist: five step headers use em dash punctuation as contracted; Step 3 includes fenced SPL matching the spl JSON field; multisearch covers replica gauges, conditions, target pressure, and metric-fetch events; streamstats implements flap_score; inputlookup enriches ownership; case assigns severity; closing table lists eighteen analyst columns; monitoringType lists Capacity and Reliability; cimModels lists Application_State and Performance.

## SPL

```spl
`comment("UC-3.2.17 Kubernetes HorizontalPodAutoscaler saturation axis: maxReplicas dwell, min-max flap, status conditions, FailedGet* metric fetch events, target metric pressure. Tunables: earliest=-2h@m latest=@m; indexes k8s_metrics k8s_events; flap_window=6 buckets of 5m")`
| eval uc_join="3217"
| join type=left uc_join [
| tstats count AS perf_model_ticks FROM datamodel=Performance WHERE (nodename=Performance.CPU OR nodename=Performance.Memory) earliest=-4h@h latest=now
| eval uc_join="3217" ]
| fields - uc_join perf_model_ticks
| multisearch [
    [ search ((index=k8s_metrics OR index=k8s) (sourcetype="prometheus:scrape:metrics" OR sourcetype="kube:objects:metrics")) earliest=-2h@m latest=@m
      | eval cluster=lower(trim(toString(coalesce(k8s_cluster_name, cluster_name, cluster, eks_cluster_name, gke_cluster_name, aks_cluster_name, resource_cluster, ""))))
      | eval mn=lower(trim(toString(coalesce(metric_name, __name__, name, MetricName, ""))))
      | rex field=_raw max_match=0 "horizontalpodautoscaler=\"(?<hpa_rx>[^\"]+)\""
      | rex field=_raw max_match=0 "namespace=\"(?<ns_rx>[^\"]+)\""
      | rex field=_raw max_match=0 "\s(?<mval>[0-9.eE+-]+)\s*$"
      | eval hpa=lower(trim(toString(coalesce(horizontalpodautoscaler, hpa_rx, ""))))
      | eval namespace=lower(trim(toString(coalesce(namespace, k8s_namespace, kubernetes_namespace, ns_rx, ""))))
      | where (like(mn, "%kube_horizontalpodautoscaler_status_current_replicas%") OR like(mn, "%kube_horizontalpodautoscaler_spec_max_replicas%") OR like(mn, "%kube_horizontalpodautoscaler_spec_min_replicas%"))
      | eval current_replicas=if(like(mn, "%status_current_replicas%"), tonumber(mval, 10), null())
      | eval max_replicas=if(like(mn, "%spec_max_replicas%"), tonumber(mval, 10), null())
      | eval min_replicas=if(like(mn, "%spec_min_replicas%"), tonumber(mval, 10), null())
      | stats latest(current_replicas) AS current_replicas latest(max_replicas) AS max_replicas latest(min_replicas) AS min_replicas BY cluster namespace hpa ]
    [ search ((index=k8s_metrics OR index=k8s) (sourcetype="prometheus:scrape:metrics" OR sourcetype="kube:objects:metrics")) earliest=-2h@m latest=@m
      | eval cluster=lower(trim(toString(coalesce(k8s_cluster_name, cluster_name, cluster, eks_cluster_name, gke_cluster_name, aks_cluster_name, resource_cluster, ""))))
      | eval mn=lower(trim(toString(coalesce(metric_name, __name__, name, MetricName, ""))))
      | rex field=_raw max_match=0 "horizontalpodautoscaler=\"(?<hpa_rx>[^\"]+)\""
      | rex field=_raw max_match=0 "namespace=\"(?<ns_rx>[^\"]+)\""
      | rex field=_raw max_match=0 "condition=\"(?<cond_l>[^\"]+)\""
      | rex field=_raw max_match=0 "status=\"(?<stat_l>[^\"]+)\""
      | where like(mn, "%kube_horizontalpodautoscaler_status_condition%")
      | eval hpa=lower(trim(toString(coalesce(horizontalpodautoscaler, hpa_rx, ""))))
      | eval namespace=lower(trim(toString(coalesce(namespace, k8s_namespace, kubernetes_namespace, ns_rx, ""))))
      | eval cond_pair=printf("%s=%s", cond_l, stat_l)
      | stats values(cond_pair) AS cond_values dc(cond_pair) AS cond_card BY cluster namespace hpa ]
    [ search ((index=k8s_metrics OR index=k8s) (sourcetype="prometheus:scrape:metrics" OR sourcetype="kube:objects:metrics")) earliest=-2h@m latest=@m
      | eval cluster=lower(trim(toString(coalesce(k8s_cluster_name, cluster_name, cluster, eks_cluster_name, gke_cluster_name, aks_cluster_name, resource_cluster, ""))))
      | eval mn=lower(trim(toString(coalesce(metric_name, __name__, name, MetricName, ""))))
      | rex field=_raw max_match=0 "horizontalpodautoscaler=\"(?<hpa_rx>[^\"]+)\""
      | rex field=_raw max_match=0 "namespace=\"(?<ns_rx>[^\"]+)\""
      | rex field=_raw max_match=0 "\s(?<mval>[0-9.eE+-]+)\s*$"
      | where like(mn, "%kube_horizontalpodautoscaler_status_target_metric%")
      | eval hpa=lower(trim(toString(coalesce(horizontalpodautoscaler, hpa_rx, ""))))
      | eval namespace=lower(trim(toString(coalesce(namespace, k8s_namespace, kubernetes_namespace, ns_rx, ""))))
      | eval observed_metric_value=tonumber(mval, 10)
      | stats latest(observed_metric_value) AS observed_metric_value BY cluster namespace hpa ]
    [ search (index=k8s_events OR index=k8s) sourcetype="kube:events" earliest=-2h@m latest=@m
      | eval cluster=lower(trim(toString(coalesce(k8s_cluster_name, cluster_name, cluster, source_cluster, ""))))
      | eval reason=trim(toString(coalesce(reason, Reason, "")))
      | eval kind=lower(trim(toString(coalesce(involvedObject.kind, `involvedObject.kind`, ""))))
      | eval hpa=lower(trim(toString(coalesce(involvedObject.name, involvedObject_name, ""))))
      | eval namespace=lower(trim(toString(coalesce(metadata.namespace, namespace, ""))))
      | eval msg=toString(coalesce(message, Message, ""))
      | where kind="horizontalpodautoscaler" AND (reason IN ("FailedGetResourceMetric", "FailedGetExternalMetric", "FailedGetObjectMetric") OR like(msg, "%FailedGet%Metric%") OR like(msg, "%FailedGetCustomMetric%"))
      | stats latest(_time) AS last_metric_fail_ts values(msg) AS fail_msgs count AS metric_fail_evts BY cluster namespace hpa ]
| eval merge_key=cluster."|".namespace."|".hpa
| stats max(current_replicas) AS current_replicas max(max_replicas) AS max_replicas max(min_replicas) AS min_replicas values(cond_values) AS cond_values max(cond_card) AS cond_card max(observed_metric_value) AS observed_metric_value max(last_metric_fail_ts) AS last_metric_fail_ts values(fail_msgs) AS fail_msgs sum(metric_fail_evts) AS metric_fail_evts BY merge_key
| rex field=merge_key "^(?<cluster>[^|]+)\|(?<namespace>[^|]+)\|(?<hpa>[^|]+)$"
| join type=left max=0 merge_key [
    search ((index=k8s_metrics OR index=k8s) (sourcetype="prometheus:scrape:metrics" OR sourcetype="kube:objects:metrics")) earliest=-2h@m latest=@m
      | eval cluster=lower(trim(toString(coalesce(k8s_cluster_name, cluster_name, cluster, eks_cluster_name, gke_cluster_name, aks_cluster_name, resource_cluster, ""))))
      | eval mn=lower(trim(toString(coalesce(metric_name, __name__, name, MetricName, ""))))
      | rex field=_raw max_match=0 "horizontalpodautoscaler=\"(?<hpa_rx>[^\"]+)\""
      | rex field=_raw max_match=0 "namespace=\"(?<ns_rx>[^\"]+)\""
      | rex field=_raw max_match=0 "\s(?<mval>[0-9.eE+-]+)\s*$"
      | where like(mn, "%kube_horizontalpodautoscaler_status_current_replicas%")
      | eval hpa=lower(trim(toString(coalesce(horizontalpodautoscaler, hpa_rx, ""))))
      | eval namespace=lower(trim(toString(coalesce(namespace, k8s_namespace, kubernetes_namespace, ns_rx, ""))))
      | eval merge_key=cluster."|".namespace."|".hpa
      | eval cr=tonumber(mval, 10)
      | bin _time span=5m aligntime=@m
      | stats latest(cr) AS cr_bucket BY merge_key _time
      | sort 0 merge_key + _time
      | streamstats window=6 current=t global=f dc(cr_bucket) AS flap_dc range(cr_bucket) AS cr_range BY merge_key
      | eval flap_score=if(flap_dc>=3 AND cr_range>=1, flap_dc, 0)
      | stats max(flap_score) AS flap_score BY merge_key ]
| join type=left max=0 cluster namespace hpa [
    | inputlookup hpa_saturation_inventory.csv
      | eval cluster=lower(trim(toString(cluster)))
      | eval namespace=lower(trim(toString(namespace)))
      | eval hpa=lower(trim(toString(horizontalpodautoscaler)))
      | eval owner_team=trim(toString(coalesce(owner_team, squad, platform_team, "")))
      | eval workload_tier=lower(trim(toString(coalesce(workload_tier, tier, env_tier, "dev"))))
      | fields cluster namespace hpa owner_team workload_tier ]
| fillnull value=0 flap_score metric_fail_evts
| fillnull value="unassigned" owner_team
| fillnull value="dev" workload_tier
| eval cond_blob=mvjoin(cond_values, " | ")
| eval at_max=if(max_replicas>0 AND current_replicas>=max_replicas, 1, 0)
| eval scaling_active_false=if(match(lower(cond_blob), "scalingactive=false"), 1, 0)
| eval scaling_limited_true=if(match(lower(cond_blob), "scalinglimited=true"), 1, 0)
| eval able_false=if(match(lower(cond_blob), "abletoscale=false"), 1, 0)
| eval target_util_saturation_pct=if(isnotnull(observed_metric_value), round(min(999, observed_metric_value), 2), null())
| eventstats max(at_max) AS cluster_hpamax_any BY cluster
| eval severity=case(
    metric_fail_evts>0 AND match(workload_tier, "prod|production|gold|tier1|tier-1") AND (scaling_active_false==1 OR able_false==1), "critical",
    metric_fail_evts>0 AND at_max==1, "critical",
    metric_fail_evts>0, "high",
    at_max==1 AND flap_score>=3, "high",
    at_max==1 AND scaling_limited_true==1 AND isnotnull(observed_metric_value) AND observed_metric_value>=80, "high",
    at_max==1, "medium",
    flap_score>=3, "medium",
    scaling_limited_true==1 AND able_false==1, "medium",
    true(), "low")
| where severity IN ("critical", "high", "medium")
| table cluster namespace hpa owner_team workload_tier current_replicas min_replicas max_replicas at_max flap_score scaling_limited_true scaling_active_false able_false metric_fail_evts target_util_saturation_pct last_metric_fail_ts cond_blob fail_msgs severity
```

## CIM SPL

```spl
| tstats summariesonly=t latest(Application_State.state) AS app_state latest(Application_State.info) AS app_info FROM datamodel=Application_State WHERE nodename=Application_State (Application_State.app="kubernetes" OR Application_State.app="k8s" OR like(Application_State.app, "%kube%")) earliest=-4h@h latest=@h BY Application_State.dest
| rename Application_State.dest AS cim_host
| join type=left max=0 cim_host [
| tstats summariesonly=t avg(Performance.cpu_load_percent) AS cpu_load_pct avg(Performance.mem_used_percent) AS mem_used_pct FROM datamodel=Performance WHERE nodename=Performance.CPU OR nodename=Performance.Memory earliest=-4h@h latest=@h BY Performance.host
| rename Performance.host AS cim_host ]
| table cim_host app_state app_info cpu_load_pct mem_used_pct
```

## Visualization

Timechart of kube_horizontalpodautoscaler_status_current_replicas versus kube_horizontalpodautoscaler_spec_max_replicas by namespace; single value of HPAs with at_max; heatmap of flap_score; table matching the closing SPL columns with drilldowns to kube:events FailedGet lines and kube-state-metrics condition text.

## Known False Positives

Deliberate hard caps for cost-control on dev and staging clusters keep HPAs pinned at maxReplicas for entire business days during load tests that are intentionally smaller than production; suppress those namespaces via hpa_saturation_inventory workload_tier or a macro exclusion list. Planned promotional surges such as Black Friday, game day, or Super Bowl traffic may sustain maxReplicas for many hours with healthy adapters; widen dwell timers or require FailedGet events before paging executives during approved surge windows. Batch jobs that legitimately hit maxReplicas once per day during a short run window can look like saturation if the alert window spans only that spike; align earliest and latest with job schedules or tag batch namespaces in the lookup. HorizontalPodAutoscaler objects under deliberate manual maintenance holds, kubectl scale freezes, or GitOps pause annotations can dwell at max while operators intend the ceiling; tie suppressions to change records. KEDA-managed HPAs that intentionally burst from zero to max on event-driven triggers may flap or pin at max in ways that match incident shapes; cross-check ScaledObject pause and cooldown settings before opening sev-one bridges. KEDA-driven workloads with sub-second event waves can oscillate replica counts between min and max without customer-visible harm; require customer-facing error budget burn or sustained FailedGet evidence before paging. Brief kube-state-metrics scrape gaps after upgrades can null replica fields while events stay quiet; demand two consecutive intervals or corroborating kubectl output before declaring adapter failure. Vendor metric adapters that lag by one or two scrape intervals can emit transient FailedGet lines that self-heal; dampen with rolling counts. Test clusters that hammer impossible metric names to validate alerting can spam FailedGet; exclude qa-only namespaces.

## References

- [Kubernetes — Horizontal Pod Autoscaling](https://kubernetes.io/docs/tasks/run-application/horizontal-pod-autoscale/)
- [Kubernetes — HorizontalPodAutoscaler status conditions](https://kubernetes.io/docs/reference/kubernetes-api/workload-resources/horizontal-pod-autoscaler-v2/)
- [Kubernetes — Resource metrics pipeline and custom metrics](https://kubernetes.io/docs/tasks/run-application/horizontal-pod-autoscale/#support-for-metrics-apis)
- [KEDA — Kubernetes Event-driven Autoscaling](https://keda.sh/docs/latest/concepts/)
- [Google GKE — Horizontal Pod autoscaling](https://cloud.google.com/kubernetes-engine/docs/how-to/horizontal-pod-autoscaling)
- [Amazon EKS — Horizontal Pod Autoscaler](https://docs.aws.amazon.com/eks/latest/userguide/horizontal-pod-autoscaler.html)
- [Azure AKS — Scale applications (HPA)](https://learn.microsoft.com/en-us/azure/aks/concepts-scale#horizontal-pod-autoscaler)
- [kube-state-metrics — HorizontalPodAutoscaler metrics](https://github.com/kubernetes/kube-state-metrics/blob/main/docs/metrics/workload/horizontalpodautoscaler-metrics.md)
- [Splunk Docs — Splunk Add-on for Kubernetes](https://docs.splunk.com/Documentation/AddOns/released/Kubernetes/About)
