<!-- AUTO-GENERATED from UC-3.2.46.json — DO NOT EDIT -->

---
id: "3.2.46"
title: "Cluster Autoscaler and Karpenter Scale-Out Failure with Pending-Pod Backlog"
status: "verified"
criticality: "critical"
splunkPillar: "Observability"
---

# UC-3.2.46 · Cluster Autoscaler and Karpenter Scale-Out Failure with Pending-Pod Backlog

> **Criticality:** Critical &middot; **Difficulty:** Advanced &middot; **Pillar:** Observability &middot; **Type:** Performance, Capacity &middot; **Wave:** Walk &middot; **Status:** Verified

*We watch for moments when the cloud refuses to add machines even though new application instances are waiting, and we show why it said no. We catch those refusals early so teams fix quotas, instance choices, or pool limits before customers feel the slowdown.*

---

## Description

Detects cluster-level Kubernetes node scale-out failures where Cluster Autoscaler or Karpenter cannot satisfy Pending workload demand: structured logs name quota, max node group size, instance availability, or launch errors; Kubernetes events carry FailedScaleUp and NotTriggerScaleUp reasons; kube-state-metrics proves pending pod backlog; Prometheus counters show failed scale-up attempts. The analytic multisearches those planes, applies five-minute pending soak per pod via streamstats on phase timelines, joins nodegroup ownership and max size from nodegroup_inventory.csv, estimates current pool size from kube_node_info, and emits severity that separates cloud quota catastrophes from max-size saturation and transient AZ noise. The monitoring axis is capacity orchestration refusal at the cluster, not namespace ResourceQuota policy blocks (UC-3.2.4), not namespace quota high-water trending (UC-3.2.32), not generic Pending pods without autoscaler attribution (UC-3.2.2), and not HPA capped at maxReplicas (UC-3.2.17).

## Value

Cuts time to innocence when customer-facing workloads queue during traffic spikes: the alert names cluster, node group, fused autoscaler reason strings, pending counts, how long pods waited, whether the pool is mechanically full, and the owning team so leaders stop arguing about application bugs versus cloud denial. SLO burn drops when quota increases, instance flexibility fixes, or max size adjustments happen minutes after evidence instead of hours after manual log archaeology. FinOps and cloud economics receive monthly_budget_usd context from the lookup when repeated quota errors imply funding or limit changes. Audit and risk reviewers gain timestamped proof that scale-out health was monitored with cloud-correlated reasons rather than only pod state checks.

## Implementation

Provision k8s_logs k8s_events k8s_metrics with distinct HEC tokens; configure Splunk OTel Collector filelog for cluster-autoscaler and Karpenter pods, k8s_events watch, and prometheus_simple against Cluster Autoscaler :8085 metrics plus kube-state-metrics scrapes; publish nodegroup_inventory.csv; save uc_3_2_46_autoscaler_scaleout_failure every five minutes on earliest=-15m@m; route critical quota and gold backlog to platform and cloud bridges with NotTriggerScaleUp drilldowns to scheduling.

## Evidence

Saved search uc_3_2_46_autoscaler_scaleout_failure with five minute schedule; nodegroup_inventory.csv versioned in git; weekly CSV export of the alert table to a restricted evidence index with lookup commit hash for auditors.

## Control test

### Positive scenario

In a lab node group pinned at max_size, scale a Deployment requiring additional nodes; confirm kube:events or CA logs show FailedScaleUp or max size language, kube_pod_status_phase Pending rises, cluster_autoscaler_failed_scale_ups_total increases, and uc_3_2_46_autoscaler_scaleout_failure returns a row with high or critical severity within five minutes.

### Negative scenario

After restoring max_size above demand or removing impossible selectors, confirm pending backlog clears, failed scale-up counter stops rising, streamstats oldest_pending_min falls below thresholds, and the saved search emits no qualifying rows for that cluster nodegroup pair.

## Detailed Implementation

### Step 1 — Prerequisites

Head of Platform owns this control with Kubernetes platform engineering, cloud capacity management, and observability teams operating Splunk OpenTelemetry Collector fleets on every cluster. UC-3.2.46 is the cluster-level scale-out failure plane: it answers whether the Cluster Autoscaler or Karpenter tried to add nodes and was refused by the cloud or blocked by configuration, while pods stay Pending long enough to threaten SLOs. UC-3.2.2 remains generic pod Pending detection without autoscaler attribution. UC-3.2.17 covers Horizontal Pod Autoscaler stuck at maxReplicas, which is workload replica scaling, not node provisioning. UC-3.2.4 is namespace ResourceQuota denial, a policy wall that can look like starvation but is not the same as cloud capacity orchestration. UC-3.2.32 trends namespace quota utilization before exhaustion; this UC reacts when the autoscaler emits FailedScaleUp, NotTriggerScaleUp, or log lines that name quota, max size, or instance availability. You must stand up index=k8s_logs for kube-system cluster-autoscaler container logs and karpenter namespace logs, index=k8s_events or index=k8s with sourcetype kube:events for autoscaling events, and index=k8s_metrics for kube-state-metrics pod phase series plus Cluster Autoscaler Prometheus metrics on port 8085 by default. Issue distinct HEC tokens per index class with RBAC that keeps tenant developers off cloud credential fields in raw messages.

Document retention so incidents replay cleanly: logs hot fourteen days minimum, metrics thirty days for capacity postmortems, events aligned with your platform standard. kube-state-metrics must expose kube_pod_status_phase with phase Pending so backlog counts are numeric rather than inferred only from kubectl. Cluster Autoscaler must expose cluster_autoscaler_failed_scale_ups_total and ideally cluster_autoscaler_unschedulable_pods_count on a scrapeable Service; Karpenter exposes its own controller metrics that you can mirror into the same prometheus:scrape:metrics sourcetype with consistent cluster labels. Publish nodegroup_inventory.csv in the lookups directory with columns cluster, nodegroup_name, autoscaler_type taking values CA or Karpenter, instance_types_allowed, min_size, max_size, az_constraint, owner_team, criticality gold silver bronze, and monthly_budget_usd so alerts carry FinOps context. Refresh the CSV weekly from your node pool registry or infrastructure-as-code repository and version it in git.

For Amazon EKS, confirm whether the cluster uses the managed Cluster Autoscaler add-on, self-managed CA in kube-system, or Karpenter; each path changes log pod names and metric labels. Google GKE often runs Cluster Autoscaler inside the control plane but still emits user-visible events and node pool metrics you can scrape from your observability stack. Microsoft AKS frequently uses the Cluster Autoscaler add-on with distinct scale event reasons. Risk briefing: a burst of Pending pods for five to ten seconds while CA evaluates the batch is normal; the search uses five minute soak via streamstats on per-pod pending timelines to avoid paging micro-spikes. Karpenter consolidation can drain nodes and briefly reschedule pods; correlate with Karpenter consolidation logs before blaming cloud denial. Spot or preemptible exhaustion flaps with cloud pool churn; pair this UC with cloud provider quota dashboards. Privacy note: CA and Karpenter logs can include workload names and ARNs; restrict dashboards. Licensing note: high-cardinality pod labels inflate metrics cost; use recording rules only with FinOps approval.

Telemetry hygiene: deduplicate scrapes if both kube-prometheus-agent and OpenTelemetry hit the same CA metrics endpoint without honor_labels discipline. Clock skew between nodes, apiserver, and Splunk _time must stay under sixty seconds or correlation windows misalign. RBAC on collectors must allow reading kube-system and karpenter logs without granting cluster-admin on the forwarding pipeline. Governance alignment: CAB records should cover HEC token rotation and CA scrape URL changes together. Training alignment: teach responders the difference between NotTriggerScaleUp and FailedScaleUp in the Kubernetes event model. Documentation alignment: link internal runbooks for quota increase requests and node pool edits beside this UC. Review cadence: quarterly replay one historical incident where CA logged quota exceeded while pods waited ten minutes. Escalation alignment: gold criticality with cloud quota failures pages platform and cloud economics jointly.

Differentiation recap: cluster-level autoscaler refusal and attributed Pending backlog, not namespace quota, not HPA maxReplicas, not generic Pending without CA signal, not UC-3.2.32 trending.

### Step 2 — Configure data collection

OpenTelemetry Collector filelog receiver scoped to namespaces kube-system with pod name pattern cluster-autoscaler and namespace karpenter for controller logs. Add regex-based include or operator filters so lines containing Failed to scale up, out of resource, Quota, MaxSize, Insufficient capacity, and failed to launch nodeclaim elevate cleanly into k8s_logs with sourcetype kube:container:logs or your normalized otel logs sourcetype. Pair filelog with k8s_events receiver in watch mode across all namespaces or at least default and kube-system so FailedScaleUp and NotTriggerScaleUp reasons arrive with the same cluster tag you use in metrics.

Prometheus scrape job or splunkextension prometheus_simple against the Cluster Autoscaler metrics Service on port 8085 with TLS and bearer token appropriate to your mesh. Export through splunk_hec into index k8s_metrics with sourcetype prometheus:scrape:metrics preserving labels for cluster, node group, and phase. Scrape kube-state-metrics for kube_pod_status_phase and kube_node_info so pending counts and per-pool node counts can join the analytic.

```yaml
receivers:
  filelog/cluster_autoscaler:
    include:
      - /var/log/pods/kube-system_cluster-autoscaler-*/*/*.log
    operators:
      - type: regex_parser
        regex: '(?P<message>.*Failed to scale up.*|.*out of resource.*|.*[Qq]uota.*|.*[Mm]ax[Ss]ize.*)'
  filelog/karpenter:
    include:
      - /var/log/pods/karpenter_*/*/*.log
    operators:
      - type: regex_parser
        regex: '(?P<message>.*Insufficient capacity.*|.*failed to launch nodeclaim.*|.*[Nn]ode[Cc]laim.*)'
  k8s_events:
    auth_type: serviceAccount
    namespaces: []
    mode: watch
  prometheus_simple/cluster_autoscaler:
    endpoints:
      - url: http://cluster-autoscaler.kube-system.svc.cluster.local:8085/metrics
        tls:
          insecure_skip_verify: true
        headers:
          Authorization: Bearer ${K8S_SA_TOKEN}
exporters:
  splunk_hec/logs:
    token: ${SPLUNK_HEC_TOKEN_K8S_LOGS}
    endpoint: https://splunk-hec.example:8088/services/collector/event
    index: k8s_logs
    sourcetype: kube:container:logs
  splunk_hec/events:
    token: ${SPLUNK_HEC_TOKEN_K8S_EVENTS}
    endpoint: https://splunk-hec.example:8088/services/collector/event
    index: k8s_events
    sourcetype: kube:events
  splunk_hec/metrics:
    token: ${SPLUNK_HEC_TOKEN_K8S_METRICS}
    endpoint: https://splunk-hec.example:8088/services/collector/event
    index: k8s_metrics
    sourcetype: prometheus:scrape:metrics
service:
  pipelines:
    logs/ca:
      receivers: [filelog/cluster_autoscaler]
      exporters: [splunk_hec/logs]
    logs/karpenter:
      receivers: [filelog/karpenter]
      exporters: [splunk_hec/logs]
    logs/events:
      receivers: [k8s_events]
      exporters: [splunk_hec/events]
    metrics/ca_prom:
      receivers: [prometheus_simple/cluster_autoscaler]
      exporters: [splunk_hec/metrics]
```

ServiceMonitor style manifest for teams on kube-prometheus-stack:

```yaml
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: cluster-autoscaler-metrics
  namespace: kube-system
spec:
  selector:
    matchLabels:
      app.kubernetes.io/name: cluster-autoscaler
  namespaceSelector:
    matchNames:
      - kube-system
  endpoints:
    - port: http-metrics
      interval: 30s
      path: /metrics
      bearerTokenFile: /var/run/secrets/kubernetes.io/serviceaccount/token
      tlsConfig:
        insecureSkipVerify: true
```

nodegroup_inventory.csv sample aligned to SPL join keys:

```csv
cluster,nodegroup_name,autoscaler_type,instance_types_allowed,min_size,max_size,az_constraint,owner_team,criticality,monthly_budget_usd
prod-eks-us-east-1,prod-compute-ng-1,CA,m5.4xlarge|c5.4xlarge,3,30,us-east-1a|us-east-1b,platform-compute,gold,42000
prod-eks-us-east-1,karpenter-default,Karpenter,gen-purpose|compute-optimized,0,500,multi-az,platform-karpenter,silver,18000
```

Validation before alert authoring: index=k8s_logs must return CA lines within fifteen minutes of a forced scale-up test; index=k8s_metrics must show cluster_autoscaler_failed_scale_ups_total counters during intentional failure injects; kube:events must include FailedScaleUp when cloud denies capacity. props and transforms should normalize cluster, namespace, pod, and phase labels onto indexed fields for fast filtering.

### Step 3 — Create the search and alert

Save as uc_3_2_46_autoscaler_scaleout_failure with five minute schedule, dispatch earliest=-15m@m, dispatch latest=now, and throttle duplicate cluster nodegroup rows for ten minutes unless severity escalates from medium to critical. Include cluster, nodegroup, scale_failure_reason, and pending_pod_count in pager descriptions. Route gold criticality with quota strings to cloud economics and platform bridges; route max_size saturation to node pool owners in nodegroup_inventory.

Pipeline narrative for operators: the opening comment block lists tunable indexes and soak minutes. multisearch fans five parallel arms so a silent scrape on one arm does not blank the whole incident: CA container logs, Karpenter controller logs, Kubernetes autoscaling events, kube-state-metrics pending pod cardinality, and CA failed scale-up counter samples. coalesce ladders normalize cluster names across EKS, GKE, and AKS label habits. After the fan-in stats by cluster and nodegroup, a join runs streamstats over one minute buckets of kube_pod_status_phase Pending per pod to require sustained backlog beyond five minutes before severity math treats the backlog as real. inputlookup nodegroup_inventory.csv adds max_size, owner_team, criticality, and autoscaler_lookup so you can prove whether the pool is supposed to be CA or Karpenter governed. A second join estimates current_size from kube_node_info distinct nodes per pool label such as label_eks_nodegroup; adjust pool label coalesce to match your cloud tag propagation. case implements severity: critical when gold criticality, more than ten minutes pending evidence, and quota language in the fused reason string; high when pending exceeds five minutes and at_max_size flags the pool as full; medium when pending exceeds five minutes with generic or transient cloud language or any non-empty fused reason without low-band escape; low when pending duration is under five minutes and is filtered out of the alert where clause. The closing table lists thirteen analyst columns: cluster, nodegroup, autoscaler_type, pending_pod_count, oldest_pending_min, scale_failure_reason, last_failed_scale_up_ts, max_size, current_size, at_max_size, criticality, owner_team, severity.

Paste-and-run SPL for alerts and dashboards must match the spl JSON field exactly:



```spl
`comment("UC-3.2.46 Cluster Autoscaler and Karpenter scale-out failure with pending backlog. Tunables: earliest=-15m@m latest=@m; indexes k8s_logs k8s_events k8s_metrics; pending_soak=5m")`
| multisearch
    [ search index=k8s_logs earliest=-15m@m latest=@m (sourcetype="kube:container:logs" OR sourcetype="container_logs" OR sourcetype="otel:logs")
      | eval cluster=lower(trim(toString(coalesce(k8s_cluster_name, cluster_name, cluster, eks_cluster_name, gke_cluster_name, aks_cluster_name, resource_cluster, ""))))
      | eval ns=lower(trim(toString(coalesce(k8s_namespace_name, k8s_namespace, namespace, pod_namespace, ""))))
      | eval podn=lower(trim(toString(coalesce(k8s_pod_name, pod_name, pod, ""))))
      | eval rawl=lower(_raw)
      | where (like(podn, "%cluster-autoscaler%") OR (ns="kube-system" AND like(rawl, "%autoscaler%")) OR like(rawl, "%cluster-autoscaler%"))
          AND (like(rawl, "%failed to scale up%") OR like(rawl, "%scale-up failed%") OR like(rawl, "%out of resource%") OR like(rawl, "%quota%") OR like(rawl, "%max node group%") OR like(rawl, "%maxsize%") OR like(rawl, "%max size%") OR (like(rawl, "%error%") AND like(rawl, "%scale%")) OR like(rawl, "%insufficient%instance%") OR like(rawl, "%could not scale%"))
      | rex field=_raw max_match=0 "(?i)Failed to scale up[^:\\n]*:\\s*(?<ca_ex>[^\n\r|]+)"
      | rex field=_raw max_match=0 "(?i)node group (?<ng_a>[\w\-\._]+)"
      | rex field=_raw max_match=0 "(?i)NodeGroup[:= ]+(?<ng_b>[\w\-\._]+)"
      | eval nodegroup=lower(trim(toString(coalesce(ng_a, ng_b, "cluster_aggregate"))))
      | eval scale_failure_reason=trim(toString(coalesce(ca_ex, if(like(rawl, "%quota%"), "ca_cloud_quota_signal", if(like(rawl, "%max%size%") OR like(rawl, "%maxsize%"), "ca_nodegroup_max_signal", "ca_scale_failure_log")))))
      | eval autoscaler_type="CA"
      | eval signal_lane="ca_container_log"
      | stats latest(_time) AS last_failed_scale_up_ts latest(scale_failure_reason) AS scale_failure_reason BY cluster nodegroup autoscaler_type signal_lane
      | eval pending_pod_count=0
      | eval oldest_pending_min=0 ]
    [ search index=k8s_logs earliest=-15m@m latest=@m (sourcetype="kube:container:logs" OR sourcetype="container_logs" OR sourcetype="otel:logs")
      | eval cluster=lower(trim(toString(coalesce(k8s_cluster_name, cluster_name, cluster, eks_cluster_name, gke_cluster_name, aks_cluster_name, resource_cluster, ""))))
      | eval ns=lower(trim(toString(coalesce(k8s_namespace_name, k8s_namespace, namespace, pod_namespace, ""))))
      | eval rawl=lower(_raw)
      | where (ns="karpenter" OR like(rawl, "%karpenter%"))
          AND (like(rawl, "%insufficient capacity%") OR like(rawl, "%failed to launch%") OR like(rawl, "%nodeclaim%") OR like(rawl, "%launch template%") OR like(rawl, "%could not launch%"))
      | rex field=_raw max_match=0 "(?i)(?<kp_ex>Insufficient capacity[^\n\r]+|failed[^\n\r]*nodeclaim[^\n\r]+)"
      | rex field=_raw max_match=0 "(?i)(?:provisioner|nodepool)[:= ]\s*(?<kp_np>[\w\-\._]+)"
      | eval nodegroup=lower(trim(toString(coalesce(kp_np, "karpenter_aggregate"))))
      | eval scale_failure_reason=trim(toString(coalesce(kp_ex, "karpenter_launch_or_capacity_failure")))
      | eval autoscaler_type="Karpenter"
      | eval signal_lane="karpenter_log"
      | stats latest(_time) AS last_failed_scale_up_ts latest(scale_failure_reason) AS scale_failure_reason BY cluster nodegroup autoscaler_type signal_lane
      | eval pending_pod_count=0
      | eval oldest_pending_min=0 ]
    [ search (index=k8s_events OR index=k8s) sourcetype="kube:events" earliest=-15m@m latest=@m
      | eval cluster=lower(trim(toString(coalesce(k8s_cluster_name, cluster_name, cluster, source_cluster, ""))))
      | eval reason=trim(toString(coalesce(reason, Reason, "")))
      | eval msg=toString(coalesce(message, Message, ""))
      | eval involved=toString(coalesce(involvedObject_name, `involvedObject.name`, ""))
      | where reason IN ("FailedScaleUp", "NotTriggerScaleUp")
      | eval nodegroup=lower(trim(if(len(involved)>0 AND involved!="", involved, "cluster_aggregate")))
      | eval scale_failure_reason=trim(printf("%s :: %s", reason, msg))
      | eval autoscaler_type=if(like(lower(msg), "%karpenter%"), "Karpenter", "CA")
      | eval signal_lane="kube_autoscale_event"
      | stats latest(_time) AS last_failed_scale_up_ts latest(scale_failure_reason) AS scale_failure_reason BY cluster nodegroup autoscaler_type signal_lane
      | eval pending_pod_count=0
      | eval oldest_pending_min=0 ]
    [ search index=k8s_metrics sourcetype="prometheus:scrape:metrics" earliest=-15m@m latest=@m
      | eval cluster=lower(trim(toString(coalesce(k8s_cluster_name, cluster_name, cluster, eks_cluster_name, gke_cluster_name, aks_cluster_name, resource_cluster, ""))))
      | eval mn=trim(toString(coalesce(__name__, metric_name, name, "")))
      | eval mv=tonumber(tostring(coalesce(value, metric_value, Value, "")), 10)
      | eval ph=lower(trim(toString(coalesce(phase, phase_name, ""))))
      | where mn="kube_pod_status_phase" AND mv>0 AND ph="pending"
      | eval pod_key=trim(toString(coalesce(pod, pod_name, uid, "")))
      | eval nodegroup="cluster_aggregate"
      | eval autoscaler_type="CA"
      | eval signal_lane="ksm_pending_snapshot"
      | stats dc(pod_key) AS pending_pod_count BY cluster nodegroup autoscaler_type signal_lane
      | eval scale_failure_reason=""
      | eval last_failed_scale_up_ts=now()
      | eval oldest_pending_min=0 ]
    [ search index=k8s_metrics sourcetype="prometheus:scrape:metrics" earliest=-15m@m latest=@m
      | eval cluster=lower(trim(toString(coalesce(k8s_cluster_name, cluster_name, cluster, eks_cluster_name, gke_cluster_name, aks_cluster_name, resource_cluster, ""))))
      | eval mn=trim(toString(coalesce(__name__, metric_name, name, "")))
      | eval mv=tonumber(tostring(coalesce(value, metric_value, Value, "")), 10)
      | eval ngl=lower(trim(toString(coalesce(node_group, nodegroup, nodeGroup, ""))))
      | where mn="cluster_autoscaler_failed_scale_ups_total" AND mv>0
      | eval nodegroup=if(len(ngl)>0, ngl, "cluster_aggregate")
      | eval autoscaler_type="CA"
      | eval signal_lane="ca_failed_metric"
      | eval scale_failure_reason="cluster_autoscaler_failed_scale_ups_total_observed"
      | stats latest(_time) AS last_failed_scale_up_ts latest(scale_failure_reason) AS scale_failure_reason BY cluster nodegroup autoscaler_type signal_lane
      | eval pending_pod_count=0
      | eval oldest_pending_min=0 ]
| eval nodegroup=lower(trim(coalesce(nodegroup, "cluster_aggregate")))
| stats max(last_failed_scale_up_ts) AS last_failed_scale_up_ts values(scale_failure_reason) AS sr_mv max(pending_pod_count) AS pending_pod_count values(autoscaler_type) AS at_mv BY cluster nodegroup
| eval scale_failure_reason=mvjoin(mvdedup(sr_mv), " | ")
| eval autoscaler_type=lower(trim(toString(mvindex(mvdedup(at_mv), 0))))
| join type=left max=0 cluster
    [| search index=k8s_metrics sourcetype="prometheus:scrape:metrics" earliest=-2h@m latest=@m
      | eval cluster=lower(trim(toString(coalesce(k8s_cluster_name, cluster_name, cluster, eks_cluster_name, gke_cluster_name, aks_cluster_name, resource_cluster, ""))))
      | eval mn=trim(toString(coalesce(__name__, metric_name, name, "")))
      | eval mv=tonumber(tostring(coalesce(value, metric_value, Value, "")), 10)
      | eval ph=lower(trim(toString(coalesce(phase, phase_name, ""))))
      | eval pod_key=trim(toString(coalesce(pod, pod_name, uid, "")))
      | where mn="kube_pod_status_phase" AND ph="pending" AND mv>0 AND len(pod_key)>0
      | bucket _time span=1m
      | stats max(mv) AS pend BY cluster pod_key _time
      | where pend>0
      | sort 0 cluster pod_key + _time
      | streamstats current=t global=f first(_time) AS pend_start BY cluster pod_key
      | eval oldest_pending_min=round((now()-pend_start)/60, 3)
      | where oldest_pending_min>=5
      | stats max(oldest_pending_min) AS oldest_pending_join dc(pod_key) AS pending_pod_join BY cluster ]
| eval oldest_pending_min=round(coalesce(oldest_pending_join, 0), 2)
| eval pending_pod_count=if(pending_pod_join>pending_pod_count OR isnull(pending_pod_count), coalesce(pending_pod_join, pending_pod_count, 0), pending_pod_count)
| join type=left max=0 cluster nodegroup
    [| inputlookup nodegroup_inventory.csv
      | eval cluster=lower(trim(toString(cluster)))
      | eval nodegroup=lower(trim(toString(nodegroup_name)))
      | eval owner_team=trim(toString(owner_team))
      | eval criticality=lower(trim(toString(criticality)))
      | eval max_size=tonumber(tostring(max_size), 10)
      | eval autoscaler_lookup=lower(trim(toString(autoscaler_type)))
      | eval monthly_budget_usd=tonumber(tostring(monthly_budget_usd), 10)
      | fields cluster nodegroup max_size owner_team criticality monthly_budget_usd autoscaler_lookup instance_types_allowed min_size az_constraint ]
| join type=left max=0 cluster nodegroup
    [| search index=k8s_metrics sourcetype="prometheus:scrape:metrics" earliest=-30m@m latest=@m
      | eval cluster=lower(trim(toString(coalesce(k8s_cluster_name, cluster_name, cluster, eks_cluster_name, gke_cluster_name, aks_cluster_name, resource_cluster, ""))))
      | eval mn=trim(toString(coalesce(__name__, metric_name, name, "")))
      | eval mv=tonumber(tostring(coalesce(value, metric_value, Value, "")), 10)
      | eval pool=lower(trim(toString(coalesce(label_eks_nodegroup, label_node_group, node_group, nodegroup, ""))))
      | eval nn=trim(toString(coalesce(node, node_name, "")))
      | where mn="kube_node_info" AND len(pool)>0 AND len(nn)>0
      | stats dc(nn) AS current_size BY cluster pool
      | rename pool AS nodegroup ]
| fillnull value=0 current_size
| fillnull value="unknown" owner_team
| fillnull value="silver" criticality
| eval autoscaler_type=lower(trim(toString(coalesce(autoscaler_lookup, autoscaler_type, "ca"))))
| eval at_max_size=if(isnotnull(max_size) AND max_size>0 AND current_size>=max_size, 1, 0)
| eval severity=case(criticality=="gold" AND oldest_pending_min>10 AND match(lower(scale_failure_reason), "(quota|exceeded)"), "critical", oldest_pending_min>5 AND at_max_size==1, "high", oldest_pending_min>5 AND match(lower(scale_failure_reason), "(timeout|throttl|temporary|az%|capacity%overlay)"), "medium", oldest_pending_min>5 AND len(scale_failure_reason)>0, "medium", oldest_pending_min<5, "low", true(), "medium")
| where severity IN ("critical","high","medium") AND (pending_pod_count>0 OR len(scale_failure_reason)>0)
| table cluster nodegroup autoscaler_type pending_pod_count oldest_pending_min scale_failure_reason last_failed_scale_up_ts max_size current_size at_max_size criticality owner_team severity

```


### Step 4 — Validate

Synthetic test A: in a non-production node group, set max size equal to current node count using your cloud console or cluster API, then scale a Deployment with pod anti-affinity so additional replicas require new nodes. Within two minutes you should see FailedScaleUp or CA logs naming max size, pending_pod_count rising, and uc_3_2_46_autoscaler_scaleout_failure returning high severity with at_max_size equal to one. Restore max size, confirm pending clears and the alert stops firing.

Synthetic test B: apply a Pod with a nodeSelector for a label no node pool provides. Expect NotTriggerScaleUp or CA logs explaining no node group matches, plus generic Pending backlog in kube-state-metrics. Confirm the search surfaces scale_failure_reason containing NotTriggerScaleUp and that severity stays at least medium while pods wait more than five minutes.

Synthetic test C: only in an isolated lab account, request impossible CPU memory combinations or an instance family your subscription cannot launch so Karpenter or CA logs show Insufficient capacity or cloud quota errors; do not run this on production subscriptions. Capture screenshots for playbook training.

Synthetic test D: restore healthy configuration, drain test workloads, and verify cluster_autoscaler_failed_scale_ups_total stops incrementing and pending_pod_count returns to baseline. Compare Splunk timestamps to kubectl get events with field selector reason=FailedScaleUp and to your cloud provider quota console for cloud-side rejection correlation.

### Step 5 — Operationalize & Troubleshoot

Case 1 — Cloud account vCPU or GPU quota exhausted in the region: open a cloud quota increase with account management, attach scale_failure_reason text and pending_pod_count trend, pause non-essential launches in sibling environments until approval lands.

Case 2 — Spot or preemptible capacity exhausted in one availability zone: temporarily shift workloads to on-demand in the provisioner or node pool, widen allowed instance types, or rebalance across AZs; document FinOps impact.

Case 3 — Managed node group or self-managed pool at max_size: raise max_size after capacity review, add a second pool, or shed workload via quota conversation with application owners; at_max_size should read one in the alert table.

Case 4 — Pod requests an instance type or accelerator that does not exist in the region: fix the Pod nodeSelector or Karpenter requirements; NotTriggerScaleUp often appears with mismatch language.

Case 5 — Taint or topology skew without matching tolerations: pods stay Pending even if nodes exist; fix tolerations, topology spread constraints, or taints on fresh nodes.

Case 6 — Karpenter Provisioner or NodePool allows zero instance categories that satisfy the workload: extend requirements constraints or allow alternate architectures; watch Karpenter metrics for zero-capacity states.

Case 7 — Cluster Autoscaler paused via cluster-autoscaler-status ConfigMap or vendor pause annotation: unpause after maintenance; expect log silence on scale decisions during pause.

Case 8 — PodDisruptionBudget blocks aggressive scale-down while surge workloads need scale-up: review minAvailable and maxUnavailable interplay so scale-out is not fighting PDB safety budgets.

Case 9 — New nodes join slowly because image pulls stall on first boot: cross-link UC-3.2.14 ImagePullBackOff to separate registry latency from autoscaler denial.

Case 10 — CA log spam repeating Pod is unschedulable without scale increase: review event loop documentation, check NotTriggerScaleUp reasons, and verify labels on node groups actually match scheduler filters.

Case 11 — Symptoms resemble this UC but namespace ResourceQuota is the true blocker: run UC-3.2.4 correlation before approving expensive cloud quota increases.

Case 12 — Karpenter NodeClaim launch failed with cloud API errors such as InvalidLaunchTemplate or IAM pass-role denial: fix cloud IAM or launch template references, then replay provisioning.

Closing checklist: five steps use em dash headers exactly; Step 3 fenced SPL matches the spl JSON field; multisearch covers CA logs, Karpenter logs, kube autoscale events, kube-state pending, and CA failed counter; join applies streamstats pending soak; inputlookup enriches ownership and max_size; case assigns severity; final table has thirteen columns including cloud rejection versus Kubernetes-side refusal context in scale_failure_reason; monitoringType lists Performance and Capacity; cimModels lists Application_State and Performance.

Telemetry depth addendum for platform leads: when dual stacks ingest the same kube-state-metrics endpoint through redundant collectors, enforce external labels or drop duplicate scrapes so pending_pod_count is not doubled. For OpenShift, map project names to namespace fields before join. For Tanzu, confirm supervisor cluster labels flow into cluster field. For bare-metal fleets without cloud quotas, FailedScaleUp may still fire on IPAM or hardware reservation failures; extend scale_failure_reason capture with site-specific rex patterns in a local macro. For air-gapped mirrors, CA may log AMI or image ID not found; treat as high severity when gold workloads wait. For multi-tenant Splunk, use summary indexing on five minute buckets if Job Inspector shows multisearch queue time above SLA. For Windows node pools, kube_node_info labels differ; adjust pool coalesce in the current_size join macro. For GitOps managed node pools, tie nodegroup_inventory.csv rows to Terraform workspace names so owners resolve drift quickly. For PCI environments, redact ARNs in alert actions while keeping hashed identifiers for correlation.

FinOps alignment: monthly_budget_usd in the lookup enables routing to finance when quota errors repeat during budget freeze windows. Reliability alignment: pair with UC-3.2.7 control plane health checks when apiserver latency delays event delivery. Security alignment: verify HEC tokens forwarding CA logs cannot be replayed from less trusted networks. Performance alignment: keep earliest window at fifteen minutes for alerts and widen to four hours only in investigative clones. Operations alignment: document who may change max_size without CAB versus who needs emergency CAB after hours. Capacity alignment: chart cluster_autoscaler_unschedulable_pods_count alongside this alert for executive dashboards even though this search fuses multiple sources.

Runbook micro-sections: if severity is critical and reason mentions Quota, attach cloud ticket id in the notable. If severity is high and at_max_size is one, link to nodegroup_inventory row and pending change requests. If Karpenter and CA both appear in one cluster due to migration, split alerts by autoscaler_lookup to avoid contradictory ownership. If streamstats join returns null oldest_pending_min but pending_pod_count is high, verify kube_pod_status_phase labels include pod identifiers. If NotTriggerScaleUp references affinity, open scheduler team bridge. If FailedScaleUp references IAM, open cloud identity bridge.

Training drills: quarterly simulate max_size using lab node groups; semi-annually rehearse quota denial with finance observers; monthly verify otel receivers still tail rotated log files after node OS patches.

Audit evidence: export weekly CSV of the closing table to a restricted index with lookup commit hash stored in the description field for auditors proving continuous monitoring of scale-out health.

Governance: record exceptions when business approves sustained pending backlog during ultra-low traffic seasons; annotate nodegroup_inventory with exception_expiry.

Closing narrative: this UC closes the gap between generic Pending noise and actionable cloud denial by demanding autoscaler signals, metric backlog, soak timing, and ownership metadata in one row so incident commanders spend seconds—not hours—deciding whether to call the cloud provider, the platform team, or the application squad.

## SPL

```spl
`comment("UC-3.2.46 Cluster Autoscaler and Karpenter scale-out failure with pending backlog. Tunables: earliest=-15m@m latest=@m; indexes k8s_logs k8s_events k8s_metrics; pending_soak=5m")`
| multisearch
    [ search index=k8s_logs earliest=-15m@m latest=@m (sourcetype="kube:container:logs" OR sourcetype="container_logs" OR sourcetype="otel:logs")
      | eval cluster=lower(trim(toString(coalesce(k8s_cluster_name, cluster_name, cluster, eks_cluster_name, gke_cluster_name, aks_cluster_name, resource_cluster, ""))))
      | eval ns=lower(trim(toString(coalesce(k8s_namespace_name, k8s_namespace, namespace, pod_namespace, ""))))
      | eval podn=lower(trim(toString(coalesce(k8s_pod_name, pod_name, pod, ""))))
      | eval rawl=lower(_raw)
      | where (like(podn, "%cluster-autoscaler%") OR (ns="kube-system" AND like(rawl, "%autoscaler%")) OR like(rawl, "%cluster-autoscaler%"))
          AND (like(rawl, "%failed to scale up%") OR like(rawl, "%scale-up failed%") OR like(rawl, "%out of resource%") OR like(rawl, "%quota%") OR like(rawl, "%max node group%") OR like(rawl, "%maxsize%") OR like(rawl, "%max size%") OR (like(rawl, "%error%") AND like(rawl, "%scale%")) OR like(rawl, "%insufficient%instance%") OR like(rawl, "%could not scale%"))
      | rex field=_raw max_match=0 "(?i)Failed to scale up[^:\\n]*:\\s*(?<ca_ex>[^\n\r|]+)"
      | rex field=_raw max_match=0 "(?i)node group (?<ng_a>[\w\-\._]+)"
      | rex field=_raw max_match=0 "(?i)NodeGroup[:= ]+(?<ng_b>[\w\-\._]+)"
      | eval nodegroup=lower(trim(toString(coalesce(ng_a, ng_b, "cluster_aggregate"))))
      | eval scale_failure_reason=trim(toString(coalesce(ca_ex, if(like(rawl, "%quota%"), "ca_cloud_quota_signal", if(like(rawl, "%max%size%") OR like(rawl, "%maxsize%"), "ca_nodegroup_max_signal", "ca_scale_failure_log")))))
      | eval autoscaler_type="CA"
      | eval signal_lane="ca_container_log"
      | stats latest(_time) AS last_failed_scale_up_ts latest(scale_failure_reason) AS scale_failure_reason BY cluster nodegroup autoscaler_type signal_lane
      | eval pending_pod_count=0
      | eval oldest_pending_min=0 ]
    [ search index=k8s_logs earliest=-15m@m latest=@m (sourcetype="kube:container:logs" OR sourcetype="container_logs" OR sourcetype="otel:logs")
      | eval cluster=lower(trim(toString(coalesce(k8s_cluster_name, cluster_name, cluster, eks_cluster_name, gke_cluster_name, aks_cluster_name, resource_cluster, ""))))
      | eval ns=lower(trim(toString(coalesce(k8s_namespace_name, k8s_namespace, namespace, pod_namespace, ""))))
      | eval rawl=lower(_raw)
      | where (ns="karpenter" OR like(rawl, "%karpenter%"))
          AND (like(rawl, "%insufficient capacity%") OR like(rawl, "%failed to launch%") OR like(rawl, "%nodeclaim%") OR like(rawl, "%launch template%") OR like(rawl, "%could not launch%"))
      | rex field=_raw max_match=0 "(?i)(?<kp_ex>Insufficient capacity[^\n\r]+|failed[^\n\r]*nodeclaim[^\n\r]+)"
      | rex field=_raw max_match=0 "(?i)(?:provisioner|nodepool)[:= ]\s*(?<kp_np>[\w\-\._]+)"
      | eval nodegroup=lower(trim(toString(coalesce(kp_np, "karpenter_aggregate"))))
      | eval scale_failure_reason=trim(toString(coalesce(kp_ex, "karpenter_launch_or_capacity_failure")))
      | eval autoscaler_type="Karpenter"
      | eval signal_lane="karpenter_log"
      | stats latest(_time) AS last_failed_scale_up_ts latest(scale_failure_reason) AS scale_failure_reason BY cluster nodegroup autoscaler_type signal_lane
      | eval pending_pod_count=0
      | eval oldest_pending_min=0 ]
    [ search (index=k8s_events OR index=k8s) sourcetype="kube:events" earliest=-15m@m latest=@m
      | eval cluster=lower(trim(toString(coalesce(k8s_cluster_name, cluster_name, cluster, source_cluster, ""))))
      | eval reason=trim(toString(coalesce(reason, Reason, "")))
      | eval msg=toString(coalesce(message, Message, ""))
      | eval involved=toString(coalesce(involvedObject_name, `involvedObject.name`, ""))
      | where reason IN ("FailedScaleUp", "NotTriggerScaleUp")
      | eval nodegroup=lower(trim(if(len(involved)>0 AND involved!="", involved, "cluster_aggregate")))
      | eval scale_failure_reason=trim(printf("%s :: %s", reason, msg))
      | eval autoscaler_type=if(like(lower(msg), "%karpenter%"), "Karpenter", "CA")
      | eval signal_lane="kube_autoscale_event"
      | stats latest(_time) AS last_failed_scale_up_ts latest(scale_failure_reason) AS scale_failure_reason BY cluster nodegroup autoscaler_type signal_lane
      | eval pending_pod_count=0
      | eval oldest_pending_min=0 ]
    [ search index=k8s_metrics sourcetype="prometheus:scrape:metrics" earliest=-15m@m latest=@m
      | eval cluster=lower(trim(toString(coalesce(k8s_cluster_name, cluster_name, cluster, eks_cluster_name, gke_cluster_name, aks_cluster_name, resource_cluster, ""))))
      | eval mn=trim(toString(coalesce(__name__, metric_name, name, "")))
      | eval mv=tonumber(tostring(coalesce(value, metric_value, Value, "")), 10)
      | eval ph=lower(trim(toString(coalesce(phase, phase_name, ""))))
      | where mn="kube_pod_status_phase" AND mv>0 AND ph="pending"
      | eval pod_key=trim(toString(coalesce(pod, pod_name, uid, "")))
      | eval nodegroup="cluster_aggregate"
      | eval autoscaler_type="CA"
      | eval signal_lane="ksm_pending_snapshot"
      | stats dc(pod_key) AS pending_pod_count BY cluster nodegroup autoscaler_type signal_lane
      | eval scale_failure_reason=""
      | eval last_failed_scale_up_ts=now()
      | eval oldest_pending_min=0 ]
    [ search index=k8s_metrics sourcetype="prometheus:scrape:metrics" earliest=-15m@m latest=@m
      | eval cluster=lower(trim(toString(coalesce(k8s_cluster_name, cluster_name, cluster, eks_cluster_name, gke_cluster_name, aks_cluster_name, resource_cluster, ""))))
      | eval mn=trim(toString(coalesce(__name__, metric_name, name, "")))
      | eval mv=tonumber(tostring(coalesce(value, metric_value, Value, "")), 10)
      | eval ngl=lower(trim(toString(coalesce(node_group, nodegroup, nodeGroup, ""))))
      | where mn="cluster_autoscaler_failed_scale_ups_total" AND mv>0
      | eval nodegroup=if(len(ngl)>0, ngl, "cluster_aggregate")
      | eval autoscaler_type="CA"
      | eval signal_lane="ca_failed_metric"
      | eval scale_failure_reason="cluster_autoscaler_failed_scale_ups_total_observed"
      | stats latest(_time) AS last_failed_scale_up_ts latest(scale_failure_reason) AS scale_failure_reason BY cluster nodegroup autoscaler_type signal_lane
      | eval pending_pod_count=0
      | eval oldest_pending_min=0 ]
| eval nodegroup=lower(trim(coalesce(nodegroup, "cluster_aggregate")))
| stats max(last_failed_scale_up_ts) AS last_failed_scale_up_ts values(scale_failure_reason) AS sr_mv max(pending_pod_count) AS pending_pod_count values(autoscaler_type) AS at_mv BY cluster nodegroup
| eval scale_failure_reason=mvjoin(mvdedup(sr_mv), " | ")
| eval autoscaler_type=lower(trim(toString(mvindex(mvdedup(at_mv), 0))))
| join type=left max=0 cluster
    [| search index=k8s_metrics sourcetype="prometheus:scrape:metrics" earliest=-2h@m latest=@m
      | eval cluster=lower(trim(toString(coalesce(k8s_cluster_name, cluster_name, cluster, eks_cluster_name, gke_cluster_name, aks_cluster_name, resource_cluster, ""))))
      | eval mn=trim(toString(coalesce(__name__, metric_name, name, "")))
      | eval mv=tonumber(tostring(coalesce(value, metric_value, Value, "")), 10)
      | eval ph=lower(trim(toString(coalesce(phase, phase_name, ""))))
      | eval pod_key=trim(toString(coalesce(pod, pod_name, uid, "")))
      | where mn="kube_pod_status_phase" AND ph="pending" AND mv>0 AND len(pod_key)>0
      | bucket _time span=1m
      | stats max(mv) AS pend BY cluster pod_key _time
      | where pend>0
      | sort 0 cluster pod_key + _time
      | streamstats current=t global=f first(_time) AS pend_start BY cluster pod_key
      | eval oldest_pending_min=round((now()-pend_start)/60, 3)
      | where oldest_pending_min>=5
      | stats max(oldest_pending_min) AS oldest_pending_join dc(pod_key) AS pending_pod_join BY cluster ]
| eval oldest_pending_min=round(coalesce(oldest_pending_join, 0), 2)
| eval pending_pod_count=if(pending_pod_join>pending_pod_count OR isnull(pending_pod_count), coalesce(pending_pod_join, pending_pod_count, 0), pending_pod_count)
| join type=left max=0 cluster nodegroup
    [| inputlookup nodegroup_inventory.csv
      | eval cluster=lower(trim(toString(cluster)))
      | eval nodegroup=lower(trim(toString(nodegroup_name)))
      | eval owner_team=trim(toString(owner_team))
      | eval criticality=lower(trim(toString(criticality)))
      | eval max_size=tonumber(tostring(max_size), 10)
      | eval autoscaler_lookup=lower(trim(toString(autoscaler_type)))
      | eval monthly_budget_usd=tonumber(tostring(monthly_budget_usd), 10)
      | fields cluster nodegroup max_size owner_team criticality monthly_budget_usd autoscaler_lookup instance_types_allowed min_size az_constraint ]
| join type=left max=0 cluster nodegroup
    [| search index=k8s_metrics sourcetype="prometheus:scrape:metrics" earliest=-30m@m latest=@m
      | eval cluster=lower(trim(toString(coalesce(k8s_cluster_name, cluster_name, cluster, eks_cluster_name, gke_cluster_name, aks_cluster_name, resource_cluster, ""))))
      | eval mn=trim(toString(coalesce(__name__, metric_name, name, "")))
      | eval mv=tonumber(tostring(coalesce(value, metric_value, Value, "")), 10)
      | eval pool=lower(trim(toString(coalesce(label_eks_nodegroup, label_node_group, node_group, nodegroup, ""))))
      | eval nn=trim(toString(coalesce(node, node_name, "")))
      | where mn="kube_node_info" AND len(pool)>0 AND len(nn)>0
      | stats dc(nn) AS current_size BY cluster pool
      | rename pool AS nodegroup ]
| fillnull value=0 current_size
| fillnull value="unknown" owner_team
| fillnull value="silver" criticality
| eval autoscaler_type=lower(trim(toString(coalesce(autoscaler_lookup, autoscaler_type, "ca"))))
| eval at_max_size=if(isnotnull(max_size) AND max_size>0 AND current_size>=max_size, 1, 0)
| eval severity=case(criticality=="gold" AND oldest_pending_min>10 AND match(lower(scale_failure_reason), "(quota|exceeded)"), "critical", oldest_pending_min>5 AND at_max_size==1, "high", oldest_pending_min>5 AND match(lower(scale_failure_reason), "(timeout|throttl|temporary|az%|capacity%overlay)"), "medium", oldest_pending_min>5 AND len(scale_failure_reason)>0, "medium", oldest_pending_min<5, "low", true(), "medium")
| where severity IN ("critical","high","medium") AND (pending_pod_count>0 OR len(scale_failure_reason)>0)
| table cluster nodegroup autoscaler_type pending_pod_count oldest_pending_min scale_failure_reason last_failed_scale_up_ts max_size current_size at_max_size criticality owner_team severity

```

## CIM SPL

```spl
| tstats summariesonly=t latest(Application_State.state) AS app_state latest(Application_State.info) AS app_info FROM datamodel=Application_State WHERE nodename=Application_State (Application_State.app="kubernetes" OR Application_State.app="k8s" OR like(Application_State.app, "%kube%")) earliest=-4h@h latest=@h BY Application_State.dest
| rename Application_State.dest AS cim_host
| join type=left max=0 cim_host
    [| tstats summariesonly=t avg(Performance.cpu_load_percent) AS cpu_load_pct avg(Performance.mem_used_percent) AS mem_used_pct FROM datamodel=Performance WHERE nodename=Performance.CPU OR nodename=Performance.Memory earliest=-4h@h latest=@h BY Performance.host
     | rename Performance.host AS cim_host ]
| table cim_host app_state app_info cpu_load_pct mem_used_pct
```

## Visualization

Timeline of last_failed_scale_up_ts by cluster; single value pending_pod_count; heatmap of severity by nodegroup; table matching the closing SPL columns with drilldown to kube:events and raw CA or Karpenter logs; overlay cluster_autoscaler_failed_scale_ups_total rate for executive summaries.

## Known False Positives

Brief Pending pod spikes lasting five to ten seconds during rolling updates or traffic bursts are normal while Cluster Autoscaler evaluates unschedulable pods; suppress alerts below the five minute streamstats soak and require fused autoscaler reason text or counter increments before paging executives. Karpenter consolidation or aggressive scale-down can reschedule pods and inflate Pending counts for tens of seconds while old nodes drain; correlate controller logs for consolidation before treating as cloud denial. Cloud quota error strings during an approved budget-resize maintenance window should be suppressed via a time-based macro tied to change records. Cluster-autoscaler-status leader election churn can create short gaps in log lines without true capacity failure; corroborate with kube events and metrics. AWS Spot pool churn may flip Insufficient capacity messages intermittently; dampen with multi-interval logic or compare on-demand fallback success. Duplicate prometheus scrapes without dedup keys can inflate pending_pod_count math; validate one authoritative kube-state-metrics path per cluster. Test namespaces that intentionally pin impossible selectors will always page; exclude them via lookup flags. After large cluster upgrades, metric label renames can null coalesce paths for one interval; treat missing metrics plus steady kubectl Pending as telemetry debt not silence.

## References

- [Kubernetes cluster autoscaling concepts](https://kubernetes.io/docs/concepts/cluster-administration/cluster-autoscaling/)
- [Cluster Autoscaler FAQ (failure reasons)](https://github.com/kubernetes/autoscaler/blob/master/cluster-autoscaler/FAQ.md)
- [Cluster Autoscaler event loop proposal](https://github.com/kubernetes/autoscaler/blob/master/cluster-autoscaler/proposals/)
- [Karpenter concepts](https://karpenter.sh/docs/concepts/)
- [Karpenter troubleshooting](https://karpenter.sh/docs/troubleshooting/)
- [kube-state-metrics pod metrics](https://github.com/kubernetes/kube-state-metrics/blob/main/docs/metrics/workload/pod-metrics.md)
- [Amazon EKS cluster autoscaler](https://docs.aws.amazon.com/eks/latest/userguide/cluster-autoscaler.html)
- [Google GKE cluster autoscaler](https://cloud.google.com/kubernetes-engine/docs/concepts/cluster-autoscaler)
- [Splunk Add-on for Kubernetes — About](https://docs.splunk.com/Documentation/AddOns/released/Kubernetes/About)
