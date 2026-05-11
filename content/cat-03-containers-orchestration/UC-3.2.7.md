<!-- AUTO-GENERATED from UC-3.2.7.json — DO NOT EDIT -->

---
id: "3.2.7"
title: "Kubernetes Control Plane Health (apiserver, etcd, scheduler, controller-manager)"
status: "verified"
criticality: "critical"
splunkPillar: "Observability"
---

# UC-3.2.7 · Kubernetes Control Plane Health (apiserver, etcd, scheduler, controller-manager)

> **Criticality:** Critical &middot; **Difficulty:** Expert &middot; **Pillar:** Observability &middot; **Type:** Reliability, Availability &middot; **Wave:** Run &middot; **Status:** Verified

*The control plane is the brain of a Kubernetes cluster. If the brain is unhealthy, you can't deploy, you can't scale, and recovery from any other failure becomes impossible. This use case watches the brain itself.*

---

## Description

Synthesizes end-to-end Kubernetes control-plane reliability from four cluster-level components—kube-apiserver, etcd, kube-scheduler, and kube-controller-manager—into a single per-cluster verdict (down through healthy) with per-component drill-down. The analytic correlates apiserver request latency, server-error share, and inflight admission pressure against etcd leader stability and member health proxies, scheduler scheduling-attempt failure pressure plus leader-election posture, and controller-manager workqueue depth with REST client error share. It is the sentinel use case for the brain of the cluster: when any pillar degrades, scheduling, reconciliation, and declarative updates stall cluster-wide. This UC deliberately stays at the control-plane synthesis layer. UC-3.2.8 and UC-3.2.26 own deep etcd performance and latency forensics; UC-3.2.21 and UC-3.2.45 own admission webhook latency planes on top of apiserver; this UC cites those siblings only as cross-links without duplicating their SPL contracts.

## Value

A unified control-plane score collapses mean time to innocence during incidents: operators see whether apiserver saturation, etcd instability, scheduler leader loss, or controller backlog is the limiting factor before application teams burn cycles redeploying workloads. Executive and SRE stakeholders receive evidence suitable for error-budget reviews because min-of-pillars scoring mirrors how Kubernetes actually fails—one broken pillar caps the entire cluster’s ability to converge state. FinOps and platform finance conversations gain defensible signal when noisy application alerts during control-plane storms are deprioritized in favor of this UC, reducing duplicate paging and Splunk search concurrency during etcd compaction or rolling control-plane upgrades. Managed-cloud estates still benefit because cloud-exported control-plane metrics and audit narratives land in the same correlation model as self-managed scrapes, preserving one runbook language across EKS, GKE, AKS, and on-prem Kubeadm fleets.

## Implementation

Stand up k8s_metrics, k8s_audit, and k8s_logs indexes with HEC ACLs; deploy OTel Collector prometheus jobs for apiserver, etcd, scheduler, and controller-manager; normalize cluster labels in props; enable audit policy RequestResponse for cluster-scoped mutating verbs; publish cluster_platform_routing.csv; save uc_3_2_7_control_plane_health every five minutes; route down and critical to platform on-call with ITSI and PagerDuty actions.

## Evidence

Saved search uc_3_2_7_control_plane_health with five-minute schedule; cluster_platform_routing.csv versioned in git; dashboard panels for per-pillar trends and overall_health_score single-value; weekly CSV export of closing table to a restricted evidence index with audit log sample hashes when incidents invoke kube:apiserver:audit.

## Control test

### Positive scenario

In a lab cluster with scrapes landing in k8s_metrics, inject apiserver load or drop etcd follower network partition so apiserver error_rate_pct, etcd_has_leader, or workqueue_depth crosses the ladder thresholds within thirty minutes; confirm uc_3_2_7_control_plane_health emits down or critical overall_state with the weakest pillar reflected in overall_health_score and the join populates on_call_team from cluster_platform_routing.csv.

### Negative scenario

Steady-state production window with all four components healthy, no maintenance flags, and suppress_single_node_dev respected for dev clusters; the saved search returns only healthy rows or zero rows when optional lookup suppresses non-prod noise, and no duplicate pages fire across sibling webhook-only UCs.

## Detailed Implementation

### Step 1 — Prerequisites

Head of Platform owns this control together with the Kubernetes platform engineering team and the observability engineers who operate Splunk OpenTelemetry Collector fleets. This use case occupies a single monitoring axis: the four pillars of the Kubernetes control plane (kube-apiserver, etcd, kube-scheduler, kube-controller-manager) plus their leader-election posture, synthesized into one min-of-pillars health score per cluster. It is intentionally broader than UC-3.2.8 and UC-3.2.26, which drill into etcd performance and raft latency alone. It is intentionally shallower than UC-3.2.21 and UC-3.2.45, which isolate admission webhook latency on top of apiserver. When this alert fires, application owners should pause rollouts until the brain recovers; continuing to push YAML through a degraded apiserver or etcd amplifies partial state and extends outages.

Index and ACL contracts: create or designate index=k8s_metrics for Prometheus-style scrape events, index=k8s_audit for kube-apiserver audit JSON, and index=k8s_logs for optional static-pod and host wrapper logs. Issue distinct HEC tokens per index with role-based search restrictions so platform engineers retain read access while application teams receive dashboard-only filtered views. Document retention: metrics hot buckets at least fourteen days for incident replay, audit at least thirty days for forensic correlation, logs aligned with your platform standard.

Scrape topology: vanilla Kubernetes requires reachable /metrics endpoints on kube-apiserver, etcd, kube-scheduler, and kube-controller-manager. Prometheus Operator users install ServiceMonitor objects (or PodMonitor objects where static pods are targeted) with label selectors that match kube-system control-plane pods and etcd members. RBAC: grant the scraping identity a ClusterRole with get on nodes/metrics and pods/metrics when kubelet scraping is used, and get/list/watch on endpoints and pods in kube-system for service discovery. GKE: export control-plane metrics through Google Cloud Monitoring and forward into Splunk via a metrics export pipeline because customer pods cannot scrape the managed apiserver. EKS: use CloudWatch Container Insights or the EKS control-plane metric surfaces documented for your AWS Organizations standard, then land those series in k8s_metrics with a cloud_cluster label that feeds the same coalesce ladder as self-managed scrapes. AKS: use Azure Monitor platform metrics for managed Kubernetes control-plane availability and latency, normalized into the same schema via OpenTelemetry Collector transform processors.

Parsing: add props.conf and transforms.conf for sourcetype=prometheus:scrape:metrics so __name__, le, code, verb, resource, job, and instance labels become indexed fields where possible. The SPL below assumes metric_name or __name__ and a numeric value field; adjust field aliases if your collector emits otel.metric.name instead.

Audit policy: ship kube:apiserver:audit with at least RequestResponse level for cluster-scoped update, delete, and patch verbs so you retain a second eye when metrics look healthy but mutating traffic stalled. The policy fragment in Step 2 illustrates verbs and omitStages.

Governance lookup: maintain lookup cluster_platform_routing.csv with cluster, cloud, on_call_team, suppress_single_node_dev. Dev clusters running Minikube, Kind, or single-node K3d should set suppress_single_node_dev=1 so HA-only thresholds do not page overnight.

Risk briefing: apiserver_request_total semantics follow upstream instrumentation guidance including STREAM_BUFFER counting rules; treat sudden verb or resource cardinality explosions as data-quality incidents before tuning SLO gates. etcd leader changes after maintenance are normal; repeated churn without a change ticket is not.

### Step 2 — Configure data collection

ServiceMonitor example covering the four control-plane jobs (adjust namespace and matchLabels to your kube-prometheus-stack release):

```yaml
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: k8s-control-plane-four-pillars
  namespace: monitoring
spec:
  selector:
    matchExpressions:
      - key: k8s-app
        operator: In
        values:
          - kube-apiserver
          - kube-controller-manager
          - kube-scheduler
  namespaceSelector:
    matchNames:
      - kube-system
  endpoints:
    - port: https
      scheme: https
      tlsConfig:
        insecureSkipVerify: true
      bearerTokenFile: /var/run/secrets/kubernetes.io/serviceaccount/token
---
apiVersion: monitoring.coreos.com/v1
kind: PodMonitor
metadata:
  name: etcd-metrics
  namespace: monitoring
spec:
  selector:
    matchLabels:
      component: etcd
  namespaceSelector:
    matchNames:
      - kube-system
  podMetricsEndpoints:
    - port: metrics
      scheme: http
```

OpenTelemetry Collector fragment routing metrics to k8s_metrics and audit to k8s_audit (simplify endpoints and tokens for your estate):

```yaml
receivers:
  prometheus:
    config:
      scrape_configs:
        - job_name: kube-apiserver
          scheme: https
          kubernetes_sd_configs:
            - role: endpoints
          relabel_configs:
            - source_labels: [__meta_kubernetes_service_name]
              regex: kubernetes
              action: keep
        - job_name: kube-controller-manager
          kubernetes_sd_configs:
            - role: endpoints
          relabel_configs:
            - source_labels: [__meta_kubernetes_endpoint_port_name]
              regex: https
              action: keep
        - job_name: kube-scheduler
          kubernetes_sd_configs:
            - role: endpoints
        - job_name: etcd
          kubernetes_sd_configs:
            - role: pod
          relabel_configs:
            - source_labels: [__meta_kubernetes_pod_label_component]
              regex: etcd
              action: keep
exporters:
  splunk_hec:
    token: "${SPLUNK_HEC_TOKEN_METRICS}"
    endpoint: "https://splunk-hec.example:8088/services/collector/event"
    index: k8s_metrics
    sourcetype: prometheus:scrape:metrics
processors:
  resource:
    attributes:
      - key: k8s.cluster.name
        from_attribute: k8s.cluster.name
        action: insert
```

Audit policy example emphasizing cluster-scoped mutations at RequestResponse:

```yaml
apiVersion: audit.k8s.io/v1
kind: Policy
rules:
  - level: RequestResponse
    verbs: ["update", "patch", "delete"]
    resources:
      - group: "*"
        resources: ["*"]
    namespaces: []
  - level: Metadata
    omitStages: ["RequestReceived"]
    resources:
      - group: ""
        resources: ["events"]
```

Optional kube-state-metrics deployment remains valuable for Lease objects and leader annotations when prometheus native leader_election_master_status is missing from your build; keep kube_state_metrics lease_info as a secondary source outside this SPL to avoid double-counting.

### Step 3 — Create the search and alert

Understanding the pipeline: multisearch runs four parallel metric arms—apiserver, etcd, scheduler, controller-manager—each normalizing cluster with coalesce() across cloud and on-prem label names. Five-minute buckets align counters and gauges. The apiserver arm estimates error_rate_pct from apiserver_request_total style counters with HTTP code labels, tracks apiserver_current_inflight_requests, and uses apiserver_request_duration-derived samples for request_p99_ms. The etcd arm watches etcd_server_has_leader, etcd_server_leader_changes_seen_total deltas, etcd_disk_wal_fsync_duration_seconds, and etcd_network_peer_round_trip_time_seconds. The scheduler arm aggregates scheduler_scheduling_attempts_failed_total, scheduler_pending_pods, and leader_election_master_status. The controller-manager arm joins workqueue_depth, workqueue_adds_total context, and rest_client_requests_total errors. After union, component_score applies a ladder from zero to one hundred, overall_health_score is the minimum score across pillars for the cluster window, and severity_tier mirrors overall_state in five tiers (down, critical, high, medium, healthy). A left join enriches on_call_team from cluster_platform_routing.csv. kube:apiserver:audit supplies last_change_event_time when cluster-scoped mutations last succeeded.

Paste-and-run SPL (must match the spl JSON field exactly):

```spl
`comment("UC-3.2.7 Kubernetes control-plane health synthesis. Tunables: idx_metrics=k8s_metrics idx_audit=k8s_audit; st_metrics=prometheus:scrape:metrics st_audit=kube:apiserver:audit; cluster label coalesce list; inflight_warn=800 err_warn_pct=2 p99_warn_ms=800 etcd_leader_chg_warn=3 sched_fail_warn=5 wq_depth_warn=200 rest_5xx_warn_pct=1; earliest=-30m@m latest=@m")`
| multisearch
    [ search index=k8s_metrics sourcetype="prometheus:scrape:metrics" earliest=-30m@m latest=@m
      | eval cluster=lower(trim(toString(coalesce(k8s_cluster_name, cluster_name, cluster, eks_cluster_name, gke_cluster_name, aks_cluster_name, resource_cluster, ""))))
      | eval job_l=lower(trim(toString(coalesce(job, scrape_job, kubernetes_job, k8s_job, ""))))
      | eval mn=trim(toString(coalesce(__name__, metric_name, name, "")))
      | eval mv=tonumber(tostring(coalesce(value, metric_value, Value, "")), 10)
      | eval code=trim(tostring(coalesce(code, status_code, http_status, "")))
      | where len(cluster)>0 AND (match(job_l, "(?i)apiserver|kube-apiserver|kubernetes-apiservers") OR match(mn, "^apiserver_"))
      | eval component="kube_apiserver"
      | eval is_5xx=if(match(code, "^5[0-9]{2}$"), 1, 0)
      | eval is_2xx=if(match(code, "^2[0-9]{2}$"), 1, 0)
      | eval dur_ms=if(match(mn, "(?i)apiserver_request_duration_seconds_sum") OR mn=="apiserver_request_duration_seconds", mv*1000, null())
      | bucket _time span=5m
      | stats sum(eval(if(is_5xx==1, mv, 0))) AS err_cnt sum(eval(if(is_2xx==1, mv, 0))) AS ok_cnt perc95(dur_ms) AS request_p99_ms max(eval(if(mn=="apiserver_current_inflight_requests" OR match(mn, "apiserver_current_inflight_requests$"), mv, null()))) AS inflight_requests BY cluster _time
      | eval denom=err_cnt + ok_cnt
      | eval error_rate_pct=if(denom>0, round(100.0 * err_cnt / denom, 3), 0)
      | eval leader_changes_5m=0
      | eval workqueue_depth=0
      | eval pending_pods=0
      | eval sched_fail_cnt=0
      | eval etcd_has_leader=1
      | eval wal_fsync_ms=0
      | eval rest_5xx_cnt=0
      | eval rest_total=0
      | eval leader_held_by="n_a"
      | eval leader_held_seconds=0
      | eval last_change_event_time=strftime(_time, "%Y-%m-%dT%H:%M:%SZ")
      | fields _time cluster component request_p99_ms error_rate_pct inflight_requests leader_changes_5m workqueue_depth pending_pods sched_fail_cnt etcd_has_leader wal_fsync_ms rest_5xx_cnt rest_total leader_held_by leader_held_seconds last_change_event_time ]
    [ search index=k8s_metrics sourcetype="prometheus:scrape:metrics" earliest=-30m@m latest=@m
      | eval cluster=lower(trim(toString(coalesce(k8s_cluster_name, cluster_name, cluster, eks_cluster_name, gke_cluster_name, aks_cluster_name, resource_cluster, ""))))
      | eval job_l=lower(trim(toString(coalesce(job, scrape_job, kubernetes_job, k8s_job, ""))))
      | eval mn=trim(toString(coalesce(__name__, metric_name, name, "")))
      | eval mv=tonumber(tostring(coalesce(value, metric_value, Value, "")), 10)
      | where len(cluster)>0 AND (match(job_l, "(?i)etcd") OR match(mn, "^etcd_"))
      | eval component="etcd"
      | bucket _time span=5m
      | stats min(eval(if(mn=="etcd_server_has_leader", mv, null()))) AS etcd_has_leader max(eval(if(mn=="etcd_server_leader_changes_seen_total", mv, null()))) AS leader_chg_hi max(eval(if(mn=="etcd_disk_wal_fsync_duration_seconds", mv, null()))) AS wal_fsync_ms max(eval(if(mn=="etcd_network_peer_round_trip_time_seconds", mv, null()))) AS peer_rtt_s BY cluster _time
      | sort 0 + cluster -_time
      | streamstats window=2 current=t global=f first(leader_chg_hi) AS prev_chg last(leader_chg_hi) AS cur_chg BY cluster
      | eval leader_changes_5m=max(0, coalesce(cur_chg,0) - coalesce(prev_chg,0))
      | eval request_p99_ms=0
      | eval error_rate_pct=0
      | eval inflight_requests=0
      | eval workqueue_depth=0
      | eval pending_pods=0
      | eval sched_fail_cnt=0
      | eval wal_fsync_ms=round(coalesce(wal_fsync_ms,0)*1000, 3)
      | eval rest_5xx_cnt=0
      | eval rest_total=0
      | eval leader_held_by="etcd_quorum"
      | eval leader_held_seconds=0
      | eval last_change_event_time=strftime(_time, "%Y-%m-%dT%H:%M:%SZ")
      | fields _time cluster component request_p99_ms error_rate_pct inflight_requests leader_changes_5m workqueue_depth pending_pods sched_fail_cnt etcd_has_leader wal_fsync_ms rest_5xx_cnt rest_total leader_held_by leader_held_seconds last_change_event_time ]
    [ search index=k8s_metrics sourcetype="prometheus:scrape:metrics" earliest=-30m@m latest=@m
      | eval cluster=lower(trim(toString(coalesce(k8s_cluster_name, cluster_name, cluster, eks_cluster_name, gke_cluster_name, aks_cluster_name, resource_cluster, ""))))
      | eval job_l=lower(trim(toString(coalesce(job, scrape_job, kubernetes_job, k8s_job, ""))))
      | eval mn=trim(toString(coalesce(__name__, metric_name, name, "")))
      | eval mv=tonumber(tostring(coalesce(value, metric_value, Value, "")), 10)
      | where len(cluster)>0 AND (match(job_l, "(?i)scheduler|kube-scheduler") OR match(mn, "^scheduler_"))
      | eval component="kube_scheduler"
      | bucket _time span=5m
      | stats sum(eval(if(mn=="scheduler_scheduling_attempts_failed_total" OR match(mn, "scheduler_scheduling_attempts_failed"), mv, 0))) AS sched_fail_cnt max(eval(if(mn=="scheduler_pending_pods", mv, null()))) AS pending_pods max(eval(if(mn=="leader_election_master_status", mv, null()))) AS master_status BY cluster _time
      | eval request_p99_ms=0
      | eval error_rate_pct=0
      | eval inflight_requests=0
      | eval leader_changes_5m=if(coalesce(master_status,1)==0, 1, 0)
      | eval workqueue_depth=0
      | eval etcd_has_leader=1
      | eval wal_fsync_ms=0
      | eval rest_5xx_cnt=0
      | eval rest_total=0
      | eval leader_held_by=if(master_status==1, "scheduler_leader", "scheduler_non_leader")
      | eval leader_held_seconds=0
      | eval last_change_event_time=strftime(_time, "%Y-%m-%dT%H:%M:%SZ")
      | fields _time cluster component request_p99_ms error_rate_pct inflight_requests leader_changes_5m workqueue_depth pending_pods sched_fail_cnt etcd_has_leader wal_fsync_ms rest_5xx_cnt rest_total leader_held_by leader_held_seconds last_change_event_time ]
    [ search index=k8s_metrics sourcetype="prometheus:scrape:metrics" earliest=-30m@m latest=@m
      | eval cluster=lower(trim(toString(coalesce(k8s_cluster_name, cluster_name, cluster, eks_cluster_name, gke_cluster_name, aks_cluster_name, resource_cluster, ""))))
      | eval job_l=lower(trim(toString(coalesce(job, scrape_job, kubernetes_job, k8s_job, ""))))
      | eval mn=trim(toString(coalesce(__name__, metric_name, name, "")))
      | eval mv=tonumber(tostring(coalesce(value, metric_value, Value, "")), 10)
      | eval code=trim(tostring(coalesce(code, status_code, http_status, "")))
      | where len(cluster)>0 AND (match(job_l, "(?i)controller-manager|kube-controller-manager") OR match(mn, "^workqueue_|^rest_client_"))
      | eval component="kube_controller_manager"
      | eval is_5xx=if(match(code, "^5[0-9]{2}$"), 1, 0)
      | eval is_total=if(match(code, "^[0-9]{3}$"), 1, 0)
      | bucket _time span=5m
      | stats max(eval(if(mn=="workqueue_depth", mv, null()))) AS workqueue_depth sum(eval(if(mn=="workqueue_adds_total", mv, 0))) AS wq_adds sum(eval(if(match(mn, "rest_client_requests_total") AND is_5xx==1, mv, 0))) AS rest_5xx_cnt sum(eval(if(match(mn, "rest_client_requests_total") AND is_total==1, mv, 0))) AS rest_total max(eval(if(mn=="leader_election_master_status", mv, null()))) AS cm_master BY cluster _time
      | eval request_p99_ms=0
      | eval error_rate_pct=0
      | eval inflight_requests=0
      | eval leader_changes_5m=if(coalesce(cm_master,1)==0, 1, 0)
      | eval pending_pods=0
      | eval sched_fail_cnt=0
      | eval etcd_has_leader=1
      | eval wal_fsync_ms=0
      | eval rest_denom=rest_total
      | eval error_rate_pct=if(rest_denom>0, round(100.0 * rest_5xx_cnt / rest_denom, 3), 0)
      | eval leader_held_by=if(cm_master==1, "controller_manager_leader", "controller_manager_non_leader")
      | eval leader_held_seconds=0
      | eval last_change_event_time=strftime(_time, "%Y-%m-%dT%H:%M:%SZ")
      | fields _time cluster component request_p99_ms error_rate_pct inflight_requests leader_changes_5m workqueue_depth pending_pods sched_fail_cnt etcd_has_leader wal_fsync_ms rest_5xx_cnt rest_total leader_held_by leader_held_seconds last_change_event_time ]
| eval cluster=if(len(cluster)==0, "unknown_cluster", cluster)
| eventstats max(_time) AS win_end BY cluster
| eval audit_anchor=strftime(win_end, "%Y-%m-%dT%H:%M:%SZ")
| join type=left max=0 cluster
    [| search index=k8s_audit sourcetype="kube:apiserver:audit" earliest=-30m@m latest=@m
      | eval cluster=lower(trim(toString(coalesce(k8s_cluster_name, cluster_name, cluster, objectRef_cluster, ""))))
      | eval verb=lower(trim(toString(coalesce(verb, requestObject_verb, ""))))
      | eval scope=lower(trim(toString(coalesce(objectRef_scope, scope, ""))))
      | where scope="cluster" AND match(verb, "update|delete|patch")
      | stats latest(_time) AS last_audit_mutate BY cluster
      | eval audit_last_change=strftime(last_audit_mutate, "%Y-%m-%dT%H:%M:%SZ") ]
| eval last_change_event_time=coalesce(audit_last_change, last_change_event_time, audit_anchor)
| eval component_score=case(
    component=="kube_apiserver" AND (error_rate_pct>=5 OR coalesce(inflight_requests,0)>=2000 OR coalesce(request_p99_ms,0)>=5000), 0,
    component=="kube_apiserver" AND (error_rate_pct>=2 OR coalesce(inflight_requests,0)>=800 OR coalesce(request_p99_ms,0)>=800), 20,
    component=="kube_apiserver" AND (error_rate_pct>=0.5 OR coalesce(inflight_requests,0)>=400 OR coalesce(request_p99_ms,0)>=400), 50,
    component=="kube_apiserver", 100,
    component=="etcd" AND coalesce(etcd_has_leader,1)==0, 0,
    component=="etcd" AND coalesce(leader_changes_5m,0)>=5, 20,
    component=="etcd" AND (coalesce(leader_changes_5m,0)>=3 OR coalesce(wal_fsync_ms,0)>=50), 50,
    component=="etcd" AND coalesce(wal_fsync_ms,0)>=20, 75,
    component=="etcd", 100,
    component=="kube_scheduler" AND coalesce(sched_fail_cnt,0)>=50, 20,
    component=="kube_scheduler" AND (coalesce(sched_fail_cnt,0)>=10 OR coalesce(pending_pods,0)>=500 OR leader_held_by=="scheduler_non_leader"), 50,
    component=="kube_scheduler" AND coalesce(sched_fail_cnt,0)>=5, 75,
    component=="kube_scheduler", 100,
    component=="kube_controller_manager" AND coalesce(workqueue_depth,0)>=2000, 0,
    component=="kube_controller_manager" AND (coalesce(workqueue_depth,0)>=500 OR coalesce(error_rate_pct,0)>=2), 20,
    component=="kube_controller_manager" AND (coalesce(workqueue_depth,0)>=200 OR coalesce(error_rate_pct,0)>=1), 50,
    component=="kube_controller_manager" AND coalesce(workqueue_depth,0)>=75, 75,
    component=="kube_controller_manager", 100,
    true(), 100)
| eval current_state=case(
    component_score==0, "down",
    component_score<=20, "critical",
    component_score<=50, "high",
    component_score<100, "medium",
    true(), "healthy")
| eventstats min(component_score) AS overall_health_score BY cluster _time
| eval overall_state=case(
    overall_health_score==0, "down",
    overall_health_score<=20, "critical",
    overall_health_score<=50, "high",
    overall_health_score<100, "medium",
    true(), "healthy")
| eval severity_tier=overall_state
| join type=left max=0 cluster
    [| inputlookup cluster_platform_routing.csv
      | eval cluster=lower(trim(toString(cluster)))
      | eval on_call_team=toString(coalesce(on_call_team, squad, platform_team, "platform_core"))
      | eval suppress_single_node_dev=tonumber(tostring(coalesce(suppress_single_node_dev, "0")), 10)
      | fields cluster on_call_team suppress_single_node_dev ]
| fillnull value="platform_core" on_call_team
| where coalesce(suppress_single_node_dev,0)==0 OR overall_state IN ("down","critical")
| eval severity_tier=case(
    overall_state=="down", "down",
    overall_state=="critical", "critical",
    overall_state=="high", "high",
    overall_state=="medium", "medium",
    true(), "healthy")
| table cluster component current_state request_p99_ms error_rate_pct inflight_requests leader_changes_5m workqueue_depth leader_held_by leader_held_seconds last_change_event_time severity_tier overall_health_score on_call_team pending_pods sched_fail_cnt etcd_has_leader wal_fsync_ms overall_state
```

savedsearches.conf example for paging when the platform is truly on fire:

```ini
[uc_3_2_7_control_plane_health]
action.email = 1
action.email.to = platform-oncall@example.com
action.email.subject = Kubernetes control plane $result.severity_tier$ on cluster $result.cluster$
action.email.message = Component $result.component$ state $result.current_state$ overall $result.overall_state$ score $result.overall_health_score$
alert.track = 1
counttype = number of events
quantity = 0
relation = greater than
cron_schedule = */5 * * * *
dispatch.earliest_time = -30m@m
dispatch.latest_time = now
enableSched = 1
is_visible = 1
search = | savedsearch uc_3_2_7_control_plane_health_base
request.ui_dispatch_app = search
alert.suppress = 1
alert.suppress.period = 300s
alert.comparator = >
alert_condition = | where severity_tier IN ("down","critical")
action.notable = 0
action.rsa = 0
action.summary_index = 0
action.webhook = 1
action.webhook.param.url = https://events.pagerduty.com/integration/your-routing-key/enqueue
```

For Splunk ITSI, bind the same search to a service KPI named Kubernetes Control Plane Health with critical threshold on overall_health_score below twenty and drilldown episode action linking to this UC runbook. Configure a second webhook action for ITSI notable forwarding if your deployment uses the ITSI custom alert action instead of raw webhook JSON.

### Step 4 — Validate

Synthetic test A — leader churn: on a disposable lab cluster, run kubectl delete lease kube-controller-manager -n kube-system and observe lease recreation; confirm leader_election_master_status or workqueue anomalies surface in k8s_metrics within two scrape intervals and that uc_3_2_7_control_plane_health raises at least a high-tier row when repeated.

Synthetic test B — apiserver pressure: for i in {1..10000}; do kubectl get pods -A &>/dev/null & done; wait; verify apiserver inflight_requests and request_p99_ms escalate and error_rate_pct stays interpretable against STREAM_BUFFER semantics; throttle the script if your lab is small.

Synthetic test C — etcd disk latency: on a lab etcd member, apply a cgroup blkio throttle to the etcd data volume device class; watch etcd_disk_wal_fsync_duration_seconds rise and confirm etcd pillar drops below healthy on the ladder.

Steady-state false-positive check (last twenty-four hours on a quiet lab):

```spl
index=k8s_metrics sourcetype=prometheus:scrape:metrics earliest=-24h latest=@h
| eval cluster=lower(trim(toString(coalesce(k8s_cluster_name, cluster_name, cluster, ""))))
| stats count BY cluster
| where count<100
```

If a cluster ingests fewer than one hundred metric events per day, scrapes are broken; do not tune alert thresholds until volume recovers.

### Step 5 — Operationalize & Troubleshoot

Case 1 — Apiserver inflight surge during massive kubectl apply or controller storm: throttle GitOps reconcilers, raise APF concurrency shares under change control, shard large applies, and pause nonessential list calls; pair with audit volume for the same verbs.

Case 2 — Etcd disk fsync above ten milliseconds for more than five minutes: plan etcd defragmentation and disk class upgrade; verify fysnc latency on NVMe versus remote block store; engage storage owners before expanding the cluster.

Case 3 — Scheduler cannot elect leader after network partition: confirm kube-system endpoints and lease objects, restore quorum networking, and verify RBAC for scheduler health probes; treat as multi-pillar incident if apiserver still serves but scheduling stops.

Case 4 — Controller-manager workqueue depth grows monotonically: identify the offending controller from workqueue labels in raw metrics, capture goroutine profiles under change control, and search for finalizer or CRD migration loops; restart only with a ticket.

Case 5 — Apiserver 5xx during webhook outage: correlate with UC-3.2.21 admission webhook latency signals; fail-closed webhooks amplify 5xx; route to admission owners, not etcd, when webhook rejection counters move in lockstep.

Case 6 — Etcd member behind on raft log: inspect etcd_network_peer_round_trip_time_seconds and member list; slow followers need network or disk remediation; avoid defrag on all members simultaneously.

Case 7 — controller-manager rest_client_requests_total spike: isolate runaway informers or buggy controllers issuing API storms; compare with apiserver inflight and user-agent labels if exported.

Case 8 — scheduler pending_pods spike with scheduling failures: check node drain storms, PDB conflicts, taints, and resource starvation; differentiate from genuine scheduler bugs using failure reason metrics when available.

Case 9 — Apiserver p99 latency spike during etcd compaction: annotate maintenance windows; do not page on single-bucket spikes when etcd maintenance_started label or known compaction cron is true; UC-3.2.8 provides deeper etcd context if duration extends.

Case 10 — Authentication failure surge on apiserver audits: token rotation skew between cloud IAM and on-cluster service accounts can masquerade as control-plane instability; correlate responseStatus for 401 versus 5xx.

Case 11 — Etcd database size above eighty percent of quota: open emergency defrag and compaction tickets, audit revision history retention, and validate automated compaction jobs; capacity breach precedes write stalls.

Case 12 — Single-node control plane in Minikube or Kind: set suppress_single_node_dev=1 and rely on developer workstations for signal; document that HA thresholds are invalid on these topologies.

Operational cadence: schedule uc_3_2_7_control_plane_health every five minutes with earliest=-30m@m, archive weekly CSV snapshots of the closing table to a restricted evidence index, and rehearse correlation with cloud provider status pages for managed Kubernetes.

Closing checklist: multisearch lists four metric arms; coalesce normalizes cluster labels; eventstats supplies overall_health_score as the minimum pillar score; case() implements five severity tiers; final projection includes cluster, component, current_state, request_p99_ms, error_rate_pct, inflight_requests, leader_changes_5m, workqueue_depth, leader_held_by, leader_held_seconds, last_change_event_time, severity_tier, overall_health_score, on_call_team, pending_pods, sched_fail_cnt, etcd_has_leader, wal_fsync_ms, and overall_state for nineteen analyst-visible columns; references include Kubernetes components, metrics reference, etcd monitoring, admission controllers, leases, STREAM_BUFFER, Splunk Kubernetes add-on documentation, and control-plane communication documentation.


## SPL

```spl
`comment("UC-3.2.7 Kubernetes control-plane health synthesis. Tunables: idx_metrics=k8s_metrics idx_audit=k8s_audit; st_metrics=prometheus:scrape:metrics st_audit=kube:apiserver:audit; cluster label coalesce list; inflight_warn=800 err_warn_pct=2 p99_warn_ms=800 etcd_leader_chg_warn=3 sched_fail_warn=5 wq_depth_warn=200 rest_5xx_warn_pct=1; earliest=-30m@m latest=@m")`
| multisearch
    [ search index=k8s_metrics sourcetype="prometheus:scrape:metrics" earliest=-30m@m latest=@m
      | eval cluster=lower(trim(toString(coalesce(k8s_cluster_name, cluster_name, cluster, eks_cluster_name, gke_cluster_name, aks_cluster_name, resource_cluster, ""))))
      | eval job_l=lower(trim(toString(coalesce(job, scrape_job, kubernetes_job, k8s_job, ""))))
      | eval mn=trim(toString(coalesce(__name__, metric_name, name, "")))
      | eval mv=tonumber(tostring(coalesce(value, metric_value, Value, "")), 10)
      | eval code=trim(tostring(coalesce(code, status_code, http_status, "")))
      | where len(cluster)>0 AND (match(job_l, "(?i)apiserver|kube-apiserver|kubernetes-apiservers") OR match(mn, "^apiserver_"))
      | eval component="kube_apiserver"
      | eval is_5xx=if(match(code, "^5[0-9]{2}$"), 1, 0)
      | eval is_2xx=if(match(code, "^2[0-9]{2}$"), 1, 0)
      | eval dur_ms=if(match(mn, "(?i)apiserver_request_duration_seconds_sum") OR mn=="apiserver_request_duration_seconds", mv*1000, null())
      | bucket _time span=5m
      | stats sum(eval(if(is_5xx==1, mv, 0))) AS err_cnt sum(eval(if(is_2xx==1, mv, 0))) AS ok_cnt perc95(dur_ms) AS request_p99_ms max(eval(if(mn=="apiserver_current_inflight_requests" OR match(mn, "apiserver_current_inflight_requests$"), mv, null()))) AS inflight_requests BY cluster _time
      | eval denom=err_cnt + ok_cnt
      | eval error_rate_pct=if(denom>0, round(100.0 * err_cnt / denom, 3), 0)
      | eval leader_changes_5m=0
      | eval workqueue_depth=0
      | eval pending_pods=0
      | eval sched_fail_cnt=0
      | eval etcd_has_leader=1
      | eval wal_fsync_ms=0
      | eval rest_5xx_cnt=0
      | eval rest_total=0
      | eval leader_held_by="n_a"
      | eval leader_held_seconds=0
      | eval last_change_event_time=strftime(_time, "%Y-%m-%dT%H:%M:%SZ")
      | fields _time cluster component request_p99_ms error_rate_pct inflight_requests leader_changes_5m workqueue_depth pending_pods sched_fail_cnt etcd_has_leader wal_fsync_ms rest_5xx_cnt rest_total leader_held_by leader_held_seconds last_change_event_time ]
    [ search index=k8s_metrics sourcetype="prometheus:scrape:metrics" earliest=-30m@m latest=@m
      | eval cluster=lower(trim(toString(coalesce(k8s_cluster_name, cluster_name, cluster, eks_cluster_name, gke_cluster_name, aks_cluster_name, resource_cluster, ""))))
      | eval job_l=lower(trim(toString(coalesce(job, scrape_job, kubernetes_job, k8s_job, ""))))
      | eval mn=trim(toString(coalesce(__name__, metric_name, name, "")))
      | eval mv=tonumber(tostring(coalesce(value, metric_value, Value, "")), 10)
      | where len(cluster)>0 AND (match(job_l, "(?i)etcd") OR match(mn, "^etcd_"))
      | eval component="etcd"
      | bucket _time span=5m
      | stats min(eval(if(mn=="etcd_server_has_leader", mv, null()))) AS etcd_has_leader max(eval(if(mn=="etcd_server_leader_changes_seen_total", mv, null()))) AS leader_chg_hi max(eval(if(mn=="etcd_disk_wal_fsync_duration_seconds", mv, null()))) AS wal_fsync_ms max(eval(if(mn=="etcd_network_peer_round_trip_time_seconds", mv, null()))) AS peer_rtt_s BY cluster _time
      | sort 0 + cluster -_time
      | streamstats window=2 current=t global=f first(leader_chg_hi) AS prev_chg last(leader_chg_hi) AS cur_chg BY cluster
      | eval leader_changes_5m=max(0, coalesce(cur_chg,0) - coalesce(prev_chg,0))
      | eval request_p99_ms=0
      | eval error_rate_pct=0
      | eval inflight_requests=0
      | eval workqueue_depth=0
      | eval pending_pods=0
      | eval sched_fail_cnt=0
      | eval wal_fsync_ms=round(coalesce(wal_fsync_ms,0)*1000, 3)
      | eval rest_5xx_cnt=0
      | eval rest_total=0
      | eval leader_held_by="etcd_quorum"
      | eval leader_held_seconds=0
      | eval last_change_event_time=strftime(_time, "%Y-%m-%dT%H:%M:%SZ")
      | fields _time cluster component request_p99_ms error_rate_pct inflight_requests leader_changes_5m workqueue_depth pending_pods sched_fail_cnt etcd_has_leader wal_fsync_ms rest_5xx_cnt rest_total leader_held_by leader_held_seconds last_change_event_time ]
    [ search index=k8s_metrics sourcetype="prometheus:scrape:metrics" earliest=-30m@m latest=@m
      | eval cluster=lower(trim(toString(coalesce(k8s_cluster_name, cluster_name, cluster, eks_cluster_name, gke_cluster_name, aks_cluster_name, resource_cluster, ""))))
      | eval job_l=lower(trim(toString(coalesce(job, scrape_job, kubernetes_job, k8s_job, ""))))
      | eval mn=trim(toString(coalesce(__name__, metric_name, name, "")))
      | eval mv=tonumber(tostring(coalesce(value, metric_value, Value, "")), 10)
      | where len(cluster)>0 AND (match(job_l, "(?i)scheduler|kube-scheduler") OR match(mn, "^scheduler_"))
      | eval component="kube_scheduler"
      | bucket _time span=5m
      | stats sum(eval(if(mn=="scheduler_scheduling_attempts_failed_total" OR match(mn, "scheduler_scheduling_attempts_failed"), mv, 0))) AS sched_fail_cnt max(eval(if(mn=="scheduler_pending_pods", mv, null()))) AS pending_pods max(eval(if(mn=="leader_election_master_status", mv, null()))) AS master_status BY cluster _time
      | eval request_p99_ms=0
      | eval error_rate_pct=0
      | eval inflight_requests=0
      | eval leader_changes_5m=if(coalesce(master_status,1)==0, 1, 0)
      | eval workqueue_depth=0
      | eval etcd_has_leader=1
      | eval wal_fsync_ms=0
      | eval rest_5xx_cnt=0
      | eval rest_total=0
      | eval leader_held_by=if(master_status==1, "scheduler_leader", "scheduler_non_leader")
      | eval leader_held_seconds=0
      | eval last_change_event_time=strftime(_time, "%Y-%m-%dT%H:%M:%SZ")
      | fields _time cluster component request_p99_ms error_rate_pct inflight_requests leader_changes_5m workqueue_depth pending_pods sched_fail_cnt etcd_has_leader wal_fsync_ms rest_5xx_cnt rest_total leader_held_by leader_held_seconds last_change_event_time ]
    [ search index=k8s_metrics sourcetype="prometheus:scrape:metrics" earliest=-30m@m latest=@m
      | eval cluster=lower(trim(toString(coalesce(k8s_cluster_name, cluster_name, cluster, eks_cluster_name, gke_cluster_name, aks_cluster_name, resource_cluster, ""))))
      | eval job_l=lower(trim(toString(coalesce(job, scrape_job, kubernetes_job, k8s_job, ""))))
      | eval mn=trim(toString(coalesce(__name__, metric_name, name, "")))
      | eval mv=tonumber(tostring(coalesce(value, metric_value, Value, "")), 10)
      | eval code=trim(tostring(coalesce(code, status_code, http_status, "")))
      | where len(cluster)>0 AND (match(job_l, "(?i)controller-manager|kube-controller-manager") OR match(mn, "^workqueue_|^rest_client_"))
      | eval component="kube_controller_manager"
      | eval is_5xx=if(match(code, "^5[0-9]{2}$"), 1, 0)
      | eval is_total=if(match(code, "^[0-9]{3}$"), 1, 0)
      | bucket _time span=5m
      | stats max(eval(if(mn=="workqueue_depth", mv, null()))) AS workqueue_depth sum(eval(if(mn=="workqueue_adds_total", mv, 0))) AS wq_adds sum(eval(if(match(mn, "rest_client_requests_total") AND is_5xx==1, mv, 0))) AS rest_5xx_cnt sum(eval(if(match(mn, "rest_client_requests_total") AND is_total==1, mv, 0))) AS rest_total max(eval(if(mn=="leader_election_master_status", mv, null()))) AS cm_master BY cluster _time
      | eval request_p99_ms=0
      | eval error_rate_pct=0
      | eval inflight_requests=0
      | eval leader_changes_5m=if(coalesce(cm_master,1)==0, 1, 0)
      | eval pending_pods=0
      | eval sched_fail_cnt=0
      | eval etcd_has_leader=1
      | eval wal_fsync_ms=0
      | eval rest_denom=rest_total
      | eval error_rate_pct=if(rest_denom>0, round(100.0 * rest_5xx_cnt / rest_denom, 3), 0)
      | eval leader_held_by=if(cm_master==1, "controller_manager_leader", "controller_manager_non_leader")
      | eval leader_held_seconds=0
      | eval last_change_event_time=strftime(_time, "%Y-%m-%dT%H:%M:%SZ")
      | fields _time cluster component request_p99_ms error_rate_pct inflight_requests leader_changes_5m workqueue_depth pending_pods sched_fail_cnt etcd_has_leader wal_fsync_ms rest_5xx_cnt rest_total leader_held_by leader_held_seconds last_change_event_time ]
| eval cluster=if(len(cluster)==0, "unknown_cluster", cluster)
| eventstats max(_time) AS win_end BY cluster
| eval audit_anchor=strftime(win_end, "%Y-%m-%dT%H:%M:%SZ")
| join type=left max=0 cluster
    [| search index=k8s_audit sourcetype="kube:apiserver:audit" earliest=-30m@m latest=@m
      | eval cluster=lower(trim(toString(coalesce(k8s_cluster_name, cluster_name, cluster, objectRef_cluster, ""))))
      | eval verb=lower(trim(toString(coalesce(verb, requestObject_verb, ""))))
      | eval scope=lower(trim(toString(coalesce(objectRef_scope, scope, ""))))
      | where scope="cluster" AND match(verb, "update|delete|patch")
      | stats latest(_time) AS last_audit_mutate BY cluster
      | eval audit_last_change=strftime(last_audit_mutate, "%Y-%m-%dT%H:%M:%SZ") ]
| eval last_change_event_time=coalesce(audit_last_change, last_change_event_time, audit_anchor)
| eval component_score=case(
    component=="kube_apiserver" AND (error_rate_pct>=5 OR coalesce(inflight_requests,0)>=2000 OR coalesce(request_p99_ms,0)>=5000), 0,
    component=="kube_apiserver" AND (error_rate_pct>=2 OR coalesce(inflight_requests,0)>=800 OR coalesce(request_p99_ms,0)>=800), 20,
    component=="kube_apiserver" AND (error_rate_pct>=0.5 OR coalesce(inflight_requests,0)>=400 OR coalesce(request_p99_ms,0)>=400), 50,
    component=="kube_apiserver", 100,
    component=="etcd" AND coalesce(etcd_has_leader,1)==0, 0,
    component=="etcd" AND coalesce(leader_changes_5m,0)>=5, 20,
    component=="etcd" AND (coalesce(leader_changes_5m,0)>=3 OR coalesce(wal_fsync_ms,0)>=50), 50,
    component=="etcd" AND coalesce(wal_fsync_ms,0)>=20, 75,
    component=="etcd", 100,
    component=="kube_scheduler" AND coalesce(sched_fail_cnt,0)>=50, 20,
    component=="kube_scheduler" AND (coalesce(sched_fail_cnt,0)>=10 OR coalesce(pending_pods,0)>=500 OR leader_held_by=="scheduler_non_leader"), 50,
    component=="kube_scheduler" AND coalesce(sched_fail_cnt,0)>=5, 75,
    component=="kube_scheduler", 100,
    component=="kube_controller_manager" AND coalesce(workqueue_depth,0)>=2000, 0,
    component=="kube_controller_manager" AND (coalesce(workqueue_depth,0)>=500 OR coalesce(error_rate_pct,0)>=2), 20,
    component=="kube_controller_manager" AND (coalesce(workqueue_depth,0)>=200 OR coalesce(error_rate_pct,0)>=1), 50,
    component=="kube_controller_manager" AND coalesce(workqueue_depth,0)>=75, 75,
    component=="kube_controller_manager", 100,
    true(), 100)
| eval current_state=case(
    component_score==0, "down",
    component_score<=20, "critical",
    component_score<=50, "high",
    component_score<100, "medium",
    true(), "healthy")
| eventstats min(component_score) AS overall_health_score BY cluster _time
| eval overall_state=case(
    overall_health_score==0, "down",
    overall_health_score<=20, "critical",
    overall_health_score<=50, "high",
    overall_health_score<100, "medium",
    true(), "healthy")
| eval severity_tier=overall_state
| join type=left max=0 cluster
    [| inputlookup cluster_platform_routing.csv
      | eval cluster=lower(trim(toString(cluster)))
      | eval on_call_team=toString(coalesce(on_call_team, squad, platform_team, "platform_core"))
      | eval suppress_single_node_dev=tonumber(tostring(coalesce(suppress_single_node_dev, "0")), 10)
      | fields cluster on_call_team suppress_single_node_dev ]
| fillnull value="platform_core" on_call_team
| where coalesce(suppress_single_node_dev,0)==0 OR overall_state IN ("down","critical")
| eval severity_tier=case(
    overall_state=="down", "down",
    overall_state=="critical", "critical",
    overall_state=="high", "high",
    overall_state=="medium", "medium",
    true(), "healthy")
| table cluster component current_state request_p99_ms error_rate_pct inflight_requests leader_changes_5m workqueue_depth leader_held_by leader_held_seconds last_change_event_time severity_tier overall_health_score on_call_team pending_pods sched_fail_cnt etcd_has_leader wal_fsync_ms overall_state
```

## CIM SPL

```spl
| tstats summariesonly=t latest(Application_State.state) AS svc_state latest(Application_State.info) AS svc_info FROM datamodel=Application_State WHERE nodename=Application_State (Application_State.app="kubernetes" OR Application_State.app="k8s" OR like(Application_State.app, "%kube%")) earliest=-1h@h latest=@h BY Application_State.dest Application_State.app
| rename Application_State.dest AS cim_host Application_State.app AS cim_app
| join type=left max=0 cim_host
    [| tstats summariesonly=t avg(Performance.cpu_load_percent) AS avg_cpu_load FROM datamodel=Performance WHERE nodename=Performance.CPU earliest=-1h@h latest=@h BY Performance.host
     | rename Performance.host AS cim_host ]
| join type=left max=0 cim_host
    [| tstats summariesonly=t max(Performance.mem_free) AS mem_free_mb FROM datamodel=Performance WHERE nodename=Performance.Memory earliest=-1h@h latest=@h BY Performance.host
     | rename Performance.host AS cim_host ]
| where like(lower(svc_state), "%down%") OR like(lower(svc_state), "%fail%") OR like(lower(svc_info), "%unhealthy%") OR avg_cpu_load>92
| table cim_host cim_app svc_state svc_info avg_cpu_load mem_free_mb
```

## Visualization

Five-row status board per cluster (four pillars plus aggregate), timechart of overall_health_score, overlay charts for apiserver p99 versus etcd wal fsync, scheduler pending pods versus failures, controller workqueue depth versus REST 5xx share, with drilldown to raw prometheus events and audit mutate rate.

## Known False Positives

Etcd periodic compaction and defragmentation windows routinely amplify apiserver request latency histograms for roughly five to ten minutes while the store is consistent; pair apiserver alerts with etcd maintenance annotations or a maintenance=true label on cluster rows so SLO burn during compaction does not page as control-plane failure. Cluster-autoscaler scale-out storms and massive DaemonSet rollouts create short inflight-request bursts on apiserver that clear within one or two scrape intervals; require two consecutive five-minute buckets above threshold or correlate with a known workload event before paging. Kops, Kubeadm, Cluster API, or vendor rolling control-plane upgrades legitimately increment etcd_server_leader_changes_seen_total and flip leader_election_master_status samples; suppress when change_ticket_id is present on the HEC event or when cluster carries upgrade_in_progress=true in cluster_platform_routing.csv, and alert only on repeated leader churn after the maintenance window closes. Amazon EKS, Google GKE, and Microsoft AKS managed control planes occasionally restart apiserver instances during transparent platform maintenance; cross-check cloud provider health dashboards and provider_event streams, and downgrade to informational when the cloud status page acknowledges regional control-plane work. Single-node Minikube, Kind, K3d, and Docker Desktop clusters exhibit perpetual non-HA etcd and scheduler/controller noise; set suppress_single_node_dev=1 in cluster_platform_routing.csv for those names so developers are not paged. Admission webhook outages (UC-3.2.21) can raise apiserver 5xx and latency; when webhook_failure_total or audit denial narratives spike in sibling indexes, route to service-mesh or admission owners instead of etcd on-call. Backup controllers issuing list-watch storms after watch reconnection can inflate workqueue_depth without user impact until depth persists for fifteen minutes; require slope-based escalation using a secondary saved search if this pattern is common in your estate.

## References

- [Kubernetes Components](https://kubernetes.io/docs/concepts/overview/components/)
- [Kubernetes Metrics Reference](https://kubernetes.io/docs/reference/instrumentation/metrics/)
- [etcd Operations Guide — Monitoring](https://etcd.io/docs/latest/op-guide/monitoring/)
- [Admission Controllers](https://kubernetes.io/docs/reference/access-authn-authz/admission-controllers/)
- [Leases](https://kubernetes.io/docs/concepts/architecture/leases/)
- [Kubernetes SIG Instrumentation — STREAM_BUFFER (apiserver_request_total semantics)](https://github.com/kubernetes/community/blob/master/sig-instrumentation/)
- [Splunk Add-on for Kubernetes — About](https://docs.splunk.com/Documentation/AddOns/released/Kubernetes/About)
- [Control Plane Node Communication](https://kubernetes.io/docs/concepts/architecture/control-plane-node-communication/)
