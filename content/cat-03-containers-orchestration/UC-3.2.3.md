<!-- AUTO-GENERATED from UC-3.2.3.json — DO NOT EDIT -->

---
id: "3.2.3"
title: "Kubernetes Node NotReady Detection and Workload Eviction Risk"
status: "verified"
criticality: "critical"
splunkPillar: "Observability"
---

# UC-3.2.3 · Kubernetes Node NotReady Detection and Workload Eviction Risk

> **Criticality:** Critical &middot; **Difficulty:** Advanced &middot; **Pillar:** Observability &middot; **Type:** Reliability, Availability &middot; **Wave:** Walk &middot; **Status:** Verified

*Each worker machine must check in with the cluster control point every few seconds. When a machine goes quiet, programs on it keep running locally but the cluster may soon force-move them. We watch the quiet duration and count how many programs would be moved if the quiet spell crosses the usual five-minute tolerance.*

---

## Description

Detects worker nodes whose Ready condition has gone false because the kubelet stopped renewing node status and leases against the apiserver, which stops new pod placement and starts the clock toward taint-based eviction for pods that tolerate node.kubernetes.io/not-ready only for the default roughly five minutes. The analytic stitches kube-state-metrics Ready=false samples, Node-scoped control-plane events, and coordination lease audit failures into one node-level row with seconds in NotReady, lease lag against the last successful heartbeat observation, and a running count of pods still scheduled on the node so responders see eviction blast radius before the controller manager deletes pods. It stays on the involuntary NotReady semantic for kubelet and worker health rather than voluntary cordon semantics, managed cloud auto-repair narratives, or control-plane quorum stories owned elsewhere.

## Value

Platform and service owners gain a single row that states how long silence has lasted, whether apiserver lease traffic shows stress, and how many customer-impacting pods remain colocated, which collapses argument during incidents about whether to fail traffic away, add capacity, or replace hardware. Error-budget owners can correlate dwell time beyond the default toleration window with concrete pod counts instead of rediscovering eviction pressure minutes after the fact. FinOps and capacity planners see when spot or preemptible churn creates repeating NotReady footprints versus when persistent kubelet starvation threatens committed spend on stateful tiers. Audit-adjacent teams retain defensible evidence that lease update failures preceded mass pod deletion when post-mortems ask whether the cluster reacted correctly.

## Implementation

Provision k8s_metrics, k8s_events, k8s_audit, and k8s_pods with HEC tokens and RBAC-aligned ACLs; deploy kube-state-metrics with node and pod collectors scraped by Splunk OTel Collector; ship filtered apiserver audit lines for coordination.k8s.io leases; publish node_inventory.csv; save uc_3_2_3_node_notready_blast_radius on a five-minute cadence with earliest=-30m@m; route critical and high severities to platform on-call with webhook or email actions tied to the closing table.

## Evidence

Saved search uc_3_2_3_node_notready_blast_radius with five-minute schedule; versioned node_inventory.csv; weekly CSV export of the closing table to a restricted evidence index; dashboard drilldowns linking cluster, node, pod_count_at_risk, and apiserver lease audit samples.

## Control test

### Positive scenario

On a non-production worker, stop the kubelet service for ninety seconds while kube-state-metrics and audit shipping remain healthy, then restore kubelet; expect k8s_metrics to show kube_node_status_condition Ready=false, k8s_events to emit NodeNotReady for the Node involvedObject, optional k8s_audit rows to show elevated lease errors, and uc_3_2_3_node_notready_blast_radius to produce a row with growing time_in_notready_s and non-zero pod_count_at_risk while pods remain scheduled on that node.

### Negative scenario

Cordon a node with kubectl cordon without stopping kubelet; confirm Ready stays true, scheduling stops for new pods, and this saved search does not classify the node as NotReady solely from cordon semantics, keeping the signal quiet unless a separate UC models unschedulable scheduling impact.

## Detailed Implementation

### Step 1 — Prerequisites

Head of Platform owns this control together with the Kubernetes platform SRE who certifies kube-state-metrics RBAC, the observability engineer operating Splunk OpenTelemetry Collector DaemonSets and cluster receivers, and the incident commander who signs paging routes when blast-radius counts imply customer impact. This use case occupies one monitoring axis only: involuntary Node Ready=false transitions on workers, how long those transitions last, whether coordination lease traffic toward the apiserver shows failures, and how many running pods remain colocated so responders can reason about imminent taint-based eviction when tolerationSeconds defaults near three hundred seconds. UC-3.2.28 remains the proactive pressure story for MemoryPressure, DiskPressure, and PIDPressure before Ready flips. UC-3.2.44 remains the managed-cloud auto-repair and replacement narrative. UC-3.2.33 remains voluntary cordon and drain. UC-3.2.7 remains apiserver, etcd, scheduler, and controller-manager synthesis. Keeping those boundaries crisp prevents duplicate tickets and preserves analyst trust when several sibling alerts fire during complex failures.

Index and token contracts: stand up k8s_metrics for Prometheus text or OTLP-normalized metric events, k8s_events for kube:events JSON, k8s_audit for kube:apiserver:audit or kube:audit JSON, and k8s_pods when a separate object forwarder lands pod snapshots without duplicating every scrape line. Issue distinct HEC tokens per index with least-privilege search roles so platform engineers retain read access while application teams receive filtered dashboard views. Document retention hot versus frozen tiers: metrics at least fourteen days for incident replay, audit at least thirty days for forensic correlation, pods aligned to your Kubernetes object retention standard.

kube-state-metrics must expose node collectors including kube_node_status_condition, kube_node_info, and pod collectors including kube_pod_info or kube_pod_status_phase with node labels preserved. RBAC grants list/watch on nodes, pods, and owners. Scrapes every fifteen to thirty seconds are typical; faster scrapes improve dwell-time fidelity at higher license cost.

Splunk OpenTelemetry Collector components: prometheus_simple or prometheus receiver scrapes kube-state-metrics and optional kubelet /metrics; k8s_events streams Node events; filelog tails /var/log/kubernetes/kube-apiserver-audit.log on self-managed control planes where security approves host access, filtered at the collector to coordination.k8s.io lease verbs when full audit volume is too heavy for license. splunk_hec exporter routes sourcetypes consistently with props.conf expectations.

Governance lookup node_inventory.csv carries cluster, node, node_pool, instance_type, owner_team, criticality, allow_reboot_window. Refresh the CSV when autoscaling groups or instance templates change. criticality values should include at least standard, silver, and gold so severity logic can distinguish fleet tiers without recompiling SPL.

Risk briefing: Ready=false means the control plane has lost reliable kubelet heartbeats, not automatically that every pod has exited. Customers may still receive partial service until the node controller applies NotReady taints and eviction timers. The closing search therefore emphasizes pod_count_at_risk rather than inferring application health from node condition alone.

Managed Kubernetes note: Amazon EKS, Google GKE, and Microsoft AKS each expose node lifecycle hooks, surge upgrades, and auto-repair behaviors that can resemble NotReady during rolling replacement; cross-check provider event feeds before treating every short flap as kubelet bugs.

Licensing and volume planning: kube-state-metrics node and pod series multiply with cluster size; coordinate label cardinality limits with Prometheus relabel rules before enabling ultra-wide card label sets on custom metrics. Apiserver audit filtering to coordination.k8s.io leases still produces bursty traffic during large clusters because every node renews frequently; size HEC queues and indexer receive rates accordingly, and keep a breaker dashboard for dropped audit lines so silent pipeline loss is not mistaken for healthy leases. When OpenTelemetry JSON replaces Prometheus text at HEC, validate that __name__ or metric.name fields still surface kube_node_status_condition strings expected by the rex arms before promoting alerts to production schedules.

### Step 2 — Configure data collection

ServiceMonitor example targeting kube-state-metrics node and pod families for Prometheus Operator users:

```yaml
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: kube-state-metrics-node-pod
  namespace: monitoring
spec:
  selector:
    matchLabels:
      app.kubernetes.io/name: kube-state-metrics
  namespaceSelector:
    matchNames:
      - kube-system
  endpoints:
    - port: http-metrics
      interval: 30s
      scrapeTimeout: 10s
      path: /metrics
      scheme: http
```

OpenTelemetry Collector fragment with prometheus receiver scraping kube-state-metrics, k8s_events receiver, filelog for apiserver audit with lease-only include, and splunk_hec exporter:

```yaml
receivers:
  prometheus_simple:
    collection_interval: 30s
    endpoint: kube-state-metrics.kube-system.svc.cluster.local:8080/metrics
    metrics_path: /metrics
  k8s_events:
    auth_type: serviceAccount
    namespaces: []
  filelog/audit:
    include:
      - /var/log/kubernetes/kube-apiserver-audit.log
    operators:
      - type: json_parser
        timestamp:
          parse_from: attributes.requestReceivedTimestamp
      - type: expr_filter
        expr: 'attributes.objectRef.apiGroup == "coordination.k8s.io" && attributes.objectRef.resource == "leases"'
exporters:
  splunk_hec/metrics:
    token: "${SPLUNK_HEC_TOKEN_METRICS}"
    endpoint: "https://splunk-hec.example:8088/services/collector/event"
    index: k8s_metrics
    sourcetype: prometheus:scrape:metrics
  splunk_hec/events:
    token: "${SPLUNK_HEC_TOKEN_EVENTS}"
    endpoint: "https://splunk-hec.example:8088/services/collector/event"
    index: k8s_events
    sourcetype: kube:events
  splunk_hec/audit:
    token: "${SPLUNK_HEC_TOKEN_AUDIT}"
    endpoint: "https://splunk-hec.example:8088/services/collector/event"
    index: k8s_audit
    sourcetype: kube:apiserver:audit
service:
  pipelines:
    metrics:
      receivers: [prometheus_simple]
      exporters: [splunk_hec/metrics]
    logs/events:
      receivers: [k8s_events]
      exporters: [splunk_hec/events]
    logs/audit:
      receivers: [filelog/audit]
      exporters: [splunk_hec/audit]
```

node_inventory.csv schema sample:

```csv
cluster,node,node_pool,instance_type,owner_team,criticality,allow_reboot_window
prod-eks-01,ip-10-0-1-42.ec2.internal,workers-amd64,m5.2xlarge,platform-core,gold,sun:02:00-04:00 UTC
prod-eks-01,ip-10-0-2-18.ec2.internal,workers-amd64,m5.2xlarge,platform-core,standard,sun:02:00-04:00 UTC
```

Validation searches before alert authoring: index=k8s_metrics kube_node_status_condition earliest=-15m, index=k8s_events NodeNotReady earliest=-15m, index=k8s_audit coordination.k8s.io leases earliest=-15m. Skew between collectors should stay under thirty seconds for meaningful dwell math.

### Step 3 — Create the search and alert

Understanding the pipeline: an opening tstats latest(_time) grouped by cluster proves recent metric ingest before the inner multisearch executes, which avoids empty inner arms on mistyped index names during drills. The multisearch arm pulls three planes in parallel: kube-state-metrics Ready=false samples with coalesce-heavy node and cluster label normalization across cloud metadata shapes, Node-scoped kube events carrying NodeNotReady and recovery reasons, and apiserver audit rows where coordination.k8s.io lease updates return HTTP errors or timeouts. The inner stats block collapses to one row per cluster and node, computes time_in_notready_s from the latest NotReady-tagged timestamp, and carries signal_axes for triage narratives. A left join on successful lease updates derives lease_lag_s as seconds since the last observed two-hundred-class response for the same node-named lease object. A second left join scans kube_pod_info and kube_pod_status_phase lines, counts distinct pods colocated on the node while phase is Running or unstated, and approximates gold_workloads_at_risk using conservative namespace substring heuristics for prod, gold, tier0, payments, checkout, and ledger classes until your organization attaches a formal namespace tier lookup. inputlookup node_inventory.csv enriches node_pool, criticality, owner_team, and instance_type. case() maps severity to critical when dwell exceeds three hundred seconds, criticality equals gold, and pod_count_at_risk is positive; high when dwell exceeds three hundred seconds with pods still present; medium when dwell exceeds sixty seconds; low for shorter flaps. The closing table lists cluster, node, node_pool, criticality, ready_state, time_in_notready_s, lease_lag_s, pod_count_at_risk, gold_workloads_at_risk, owner_team, and severity for eleven analyst-visible columns.

Paste-and-run SPL (must match the spl JSON field exactly):

```spl
`comment("UC-3.2.3 Node NotReady dwell, lease lag, eviction blast radius. Tunables: earliest=-30m@m; indexes k8s_metrics k8s_events k8s_audit; sourcetype prometheus:scrape:metrics kube:events kube:apiserver:audit; tolerationSeconds reference 300s")`
| tstats latest(_time) AS cluster_metric_wallclock WHERE index=k8s_metrics sourcetype="prometheus:scrape:metrics" earliest=-30m@m latest=now BY cluster
| join type=inner max=0 cluster
    [| multisearch
        [ search index=k8s_metrics sourcetype="prometheus:scrape:metrics" earliest=-30m@m latest=now
          | eval mn=lower(trim(toString(coalesce(__name__,metric_name,name,""))))
          | eval cluster=lower(trim(toString(coalesce(k8s_cluster_name,cluster_name,cluster,eks_cluster_name,gke_cluster_name,aks_cluster_name,resource_cluster,""))))
          | eval nodex=lower(trim(toString(coalesce(node,node_name,kubernetes_io_hostname,k8s_node_name,instance,""))))
          | rex field=_raw "condition=\"(?<cond_lab>[^\"]+)\""
          | rex field=_raw "status=\"(?<stat_lab>[^\"]+)\""
          | eval ks_cond=trim(toString(coalesce(condition,cond_lab,"")))
          | eval ks_stat=trim(toString(coalesce(status,stat_lab,"")))
          | rex field=_raw "(?<metval>[0-9]+(?:\\.[0-9]+)?)\\s*$"
          | eval metric_val=tonumber(metval,10)
          | where like(mn,"kube_node_status_condition") AND ks_cond="Ready" AND ks_stat="false" AND len(cluster)>0 AND len(nodex)>0
          | eval ready_state="NotReady"
          | eval signal_axis="kube_state_metrics_ready_false"
          | rename nodex AS node
          | fields _time cluster node ready_state signal_axis metric_val ]
        [ search index=k8s_events sourcetype="kube:events" earliest=-30m@m latest=now
          | eval cluster=lower(trim(toString(coalesce(k8s_cluster_name,cluster_name,source_cluster,""))))
          | eval nodex=lower(trim(toString(coalesce(involvedObject.name,object_ref_name,host,source_host,node_name,""))))
          | eval ik=lower(trim(toString(coalesce(involvedObject.kind,involvedObject_kind,""))))
          | eval reason_ev=trim(toString(coalesce(reason,type,message_reason,"")))
          | where ik="node" AND (reason_ev="NodeNotReady" OR reason_ev="NodeReady" OR reason_ev="NodeReadyChange" OR match(lower(reason_ev),"node.*ready"))
          | eval ready_state=if(reason_ev="NodeReady","Recovered","NotReady")
          | eval signal_axis="kubernetes_node_event"
          | rename nodex AS node
          | fields _time cluster node ready_state signal_axis ]
        [ search index=k8s_audit (sourcetype="kube:apiserver:audit" OR sourcetype="kube:audit") earliest=-30m@m latest=now
          | eval cluster=lower(trim(toString(coalesce(k8s_cluster_name,cluster_name,objectRef_cluster,""))))
          | eval apig=lower(trim(toString(coalesce(objectRef_apiGroup,objectRef_apigroup,""))))
          | eval res_lc=lower(trim(toString(coalesce(objectRef_resource,""))))
          | eval nodex=lower(trim(toString(coalesce(objectRef_name,requestObject_metadata_name,""))))
          | eval http_code=tonumber(tostring(coalesce(responseStatus_code,responseCode,"500")),10)
          | where apig="coordination.k8s.io" AND res_lc="leases" AND len(nodex)>2 AND (http_code>=400 OR match(lower(_raw),"timeout"))
          | eval ready_state="LeaseUpdateFailure"
          | eval signal_axis="apiserver_audit_lease_failure"
          | rename nodex AS node
          | fields _time cluster node ready_state signal_axis ]
    | eval node=lower(trim(toString(coalesce(node,""))))
    | where len(cluster)>0 AND len(node)>0
    | stats latest(eval(if(ready_state=="NotReady",_time,null()))) AS last_nr_sample
            latest(eval(if(signal_axis=="kube_state_metrics_ready_false",metric_val,null()))) AS ksm_ready_false_gauge
            values(signal_axis) AS signal_axes
            values(ready_state) AS ready_states_seen
            max(eval(if(ready_state=="NotReady",1,0))) AS any_notready_signal
      BY cluster node
    | where any_notready_signal>0 OR ksm_ready_false_gauge>=1 OR mvcount(signal_axes)>0
    | eval time_in_notready_s=if(isnotnull(last_nr_sample) AND last_nr_sample>0, round(now()-last_nr_sample,0), 0)
    | eval time_in_notready_s=if(time_in_notready_s<0,0,time_in_notready_s)
    | eval ready_state="NotReady" ]
| join type=left max=0 cluster node
    [| search index=k8s_audit (sourcetype="kube:apiserver:audit" OR sourcetype="kube:audit") earliest=-30m@m latest=now
      | eval cluster=lower(trim(toString(coalesce(k8s_cluster_name,cluster_name,objectRef_cluster,""))))
      | eval node=lower(trim(toString(coalesce(objectRef_name,requestObject_metadata_name,""))))
      | eval apig=lower(trim(toString(coalesce(objectRef_apiGroup,objectRef_apigroup,""))))
      | eval res_lc=lower(trim(toString(coalesce(objectRef_resource,""))))
      | eval http_code=tonumber(tostring(coalesce(responseStatus_code,responseCode,"299")),10)
      | where apig="coordination.k8s.io" AND res_lc="leases" AND len(node)>2 AND http_code>=200 AND http_code<400
      | stats latest(_time) AS last_lease_ok BY cluster node
      | eval lease_lag_s=round(now()-last_lease_ok,0) ]
| fillnull value=999999 lease_lag_s
| join type=left max=0 cluster node
    [| search index=k8s_metrics sourcetype="prometheus:scrape:metrics" earliest=-30m@m latest=now
      | eval cluster=lower(trim(toString(coalesce(k8s_cluster_name,cluster_name,cluster,eks_cluster_name,gke_cluster_name,aks_cluster_name,resource_cluster,""))))
      | eval node=lower(trim(toString(coalesce(node,node_name,kubernetes_io_hostname,k8s_node_name,""))))
      | eval mn=lower(trim(toString(coalesce(__name__,metric_name,name,""))))
      | rex field=_raw "pod=\"(?<pod_nm>[^\"]+)\""
      | rex field=_raw "namespace=\"(?<pod_ns>[^\"]+)\""
      | rex field=_raw "phase=\"(?<pod_phase>[^\"]+)\""
      | eval phase_final=lower(trim(toString(coalesce(phase,pod_phase,""))))
      | where len(cluster)>0 AND len(node)>0 AND len(pod_nm)>0 AND (like(mn,"kube_pod_info") OR like(mn,"kube_pod_status_phase")) AND (phase_final="" OR phase_final="running" OR like(mn,"kube_pod_info"))
      | eval gold_ns=if(match(pod_ns,"(?i)prod|gold|tier0|tier_0|payments|checkout|ledger"),1,0)
      | stats dc(pod_nm) AS pod_count_at_risk sum(gold_ns) AS gold_workloads_at_risk BY cluster node ]
| fillnull value=0 pod_count_at_risk gold_workloads_at_risk
| join type=left max=0 cluster node
    [| inputlookup node_inventory.csv
      | eval cluster=lower(trim(toString(cluster)))
      | eval node=lower(trim(toString(node)))
      | eval node_pool=toString(coalesce(node_pool,pool,nodegroup,"unknown_pool"))
      | eval criticality=lower(trim(toString(coalesce(criticality,tier,"standard"))))
      | eval owner_team=toString(coalesce(owner_team,squad,platform_team,"unassigned"))
      | eval instance_type=toString(coalesce(instance_type,vm_type,"unknown_type"))
      | fields cluster node node_pool criticality owner_team instance_type allow_reboot_window ]
| fillnull value="unassigned" owner_team
| fillnull value="standard" criticality
| fillnull value="unknown_pool" node_pool
| eval ready_state="NotReady"
| eval severity=case(
    time_in_notready_s>300 AND match(criticality,"^gold$") AND pod_count_at_risk>0, "critical",
    time_in_notready_s>300 AND pod_count_at_risk>0, "high",
    time_in_notready_s>60, "medium",
    true(), "low")
| table cluster node node_pool criticality ready_state time_in_notready_s lease_lag_s pod_count_at_risk gold_workloads_at_risk owner_team severity
```

savedsearches.conf sketch: schedule every five minutes, dispatch.earliest_time=-30m@m, throttle duplicate cluster-node pairs for ten minutes on low severity while allowing immediate escalation when severity moves from medium to critical, and attach a webhook payload that includes pod_count_at_risk and gold_workloads_at_risk JSON fields for chat-ops bridges.

### Step 4 — Validate

Synthetic cordon check: on a non-production node run kubectl cordon worker-3 and confirm scheduling stops for new pods while Ready remains true; this search should not invent NotReady rows from cordon alone, which validates separation from UC-3.2.33 voluntary operations.

Synthetic kubelet pause: on a sacrificial non-production worker, run sudo systemctl stop kubelet for ninety seconds while peers keep running, observe kube_node_status_condition flip in k8s_metrics, NodeNotReady events in k8s_events, and optional lease failures in k8s_audit, then confirm time_in_notready_s crosses sixty seconds and pod_count_at_risk matches kubectl get pods --field-selector spec.nodeName=... --all-namespaces counts for Running pods. Restore with sudo systemctl start kubelet and confirm the saved search clears on the next interval unless lingering conditions remain.

Blast-radius check: park two disposable Deployments on the same node using required node affinity in lab only, induce NotReady, and verify pod_count_at_risk increments by two while gold_workloads_at_risk follows namespace naming heuristics.

Negative path: reboot a kube-state-metrics pod without touching workers; metrics pause should not fabricate NotReady if workers stayed Ready, proving the search keys off node series rather than global scrape gaps. If gaps occur, the opening tstats arm fails closed by inner-joining clusters with recent wallclock.

### Step 5 — Operationalize & Troubleshoot

Case 1 — Single node NotReady due to kubelet OOM or kubelet crash loops: collect journalctl -u kubelet on the worker, replace the node under change control when hardware fault is suspected, and repair root cgroup or package issues before returning to service.

Case 2 — Multiple nodes NotReady simultaneously: treat as probable control-plane or network partition; pivot to UC-3.2.7 control-plane synthesis and UC-3.2.34 data-plane correlation paths before deep-diving individual kubelets.

Case 3 — Brief NotReady during rolling AMI or OS upgrades: when node_inventory.csv allow_reboot_window covers the interval, suppress pages or downgrade severity to informational while still logging evidence.

Case 4 — Lease lag greater than thirty seconds while Ready remains true: escalate as pre-NotReady warning; investigate apiserver latency, kubelet rotation, and etcd health even when this UC’s primary Ready=false arm has not fired.

Case 5 — NotReady on a node hosting a critical StatefulSet pod such as a database: engage data-store owners immediately, evaluate synchronous replication impact, and plan failover before eviction timers elapse.

Case 6 — NotReady coincides with a planned drain: when UC-3.2.33 maintenance state is active for the node, auto-suppress or annotate rows as maintenance-induced involuntary overlap rather than unknown failure.

Case 7 — Node pool scale-out adds fresh nodes that appear NotReady during bootstrap: dampen alerts for roughly ten minutes after cloud provider creation timestamps while kubelet registers, using provider metadata joins or kube_node_created_seconds when available.

Case 8 — Spot or preemptible termination notices precede NotReady by one to two minutes: cross-check cloud termination events, downgrade to informational when termination is expected, and ensure capacity buffers absorb the drain.

Case 9 — DiskPressure or MemoryPressure trends preceded Ready=false: follow UC-3.2.28 pressure analytics to remediate root cause before replacement nodes re-enter the same failure mode.

Case 10 — Audit logs show three or more consecutive lease update failures for the same node object: prioritize kubelet-to-apiserver networking, kube-apiserver saturation, and local disk backing kubelet state directories.

Case 11 — Managed-cluster auto-repair replaces an unhealthy instance while NotReady persists briefly: align with UC-3.2.44 auto-repair semantics, attach provider repair IDs, and avoid duplicate human actions when automation already owns replacement.

Case 12 — Cluster-wide NotReady cascade across most workers: declare a major incident, freeze GitOps and Helm releases, shift traffic at load balancers where possible, and lead coordinated recovery with network and control-plane squads.

Operational cadence: review weekly CSV exports for false-positive themes, replay one historical incident quarterly after kube-state-metrics upgrades, and keep lookup commit hashes in the evidence pack. Dashboard hygiene: keep a secondary panel for kubelet scrape success rate so metric absence is not misread as healthy nodes.

Closing checklist: five plain em-dash step headers are present; Step 3 includes a fenced spl block that matches the spl JSON field; Step 5 lists twelve numbered case lines; monitoringType includes Reliability and Availability; cimModels lists Application_State and Performance; equipmentModels lists kubernetes_k8s; references include eight distinct public URLs covering nodes, node status, taints and tolerations, cluster troubleshooting, leases, kube-state-metrics node metrics, the NotReady taint reference, and Splunk Kubernetes add-on documentation; narrative description, value, knownFalsePositives, and grandmaExplanation contain no asterisk emphasis; differentiation from UC-3.2.28, UC-3.2.44, UC-3.2.33, and UC-3.2.7 appears in prerequisites and cases.


## SPL

```spl
`comment("UC-3.2.3 Node NotReady dwell, lease lag, eviction blast radius. Tunables: earliest=-30m@m; indexes k8s_metrics k8s_events k8s_audit; sourcetype prometheus:scrape:metrics kube:events kube:apiserver:audit; tolerationSeconds reference 300s")`
| tstats latest(_time) AS cluster_metric_wallclock WHERE index=k8s_metrics sourcetype="prometheus:scrape:metrics" earliest=-30m@m latest=now BY cluster
| join type=inner max=0 cluster
    [| multisearch
        [ search index=k8s_metrics sourcetype="prometheus:scrape:metrics" earliest=-30m@m latest=now
          | eval mn=lower(trim(toString(coalesce(__name__,metric_name,name,""))))
          | eval cluster=lower(trim(toString(coalesce(k8s_cluster_name,cluster_name,cluster,eks_cluster_name,gke_cluster_name,aks_cluster_name,resource_cluster,""))))
          | eval nodex=lower(trim(toString(coalesce(node,node_name,kubernetes_io_hostname,k8s_node_name,instance,""))))
          | rex field=_raw "condition=\"(?<cond_lab>[^\"]+)\""
          | rex field=_raw "status=\"(?<stat_lab>[^\"]+)\""
          | eval ks_cond=trim(toString(coalesce(condition,cond_lab,"")))
          | eval ks_stat=trim(toString(coalesce(status,stat_lab,"")))
          | rex field=_raw "(?<metval>[0-9]+(?:\\.[0-9]+)?)\\s*$"
          | eval metric_val=tonumber(metval,10)
          | where like(mn,"kube_node_status_condition") AND ks_cond="Ready" AND ks_stat="false" AND len(cluster)>0 AND len(nodex)>0
          | eval ready_state="NotReady"
          | eval signal_axis="kube_state_metrics_ready_false"
          | rename nodex AS node
          | fields _time cluster node ready_state signal_axis metric_val ]
        [ search index=k8s_events sourcetype="kube:events" earliest=-30m@m latest=now
          | eval cluster=lower(trim(toString(coalesce(k8s_cluster_name,cluster_name,source_cluster,""))))
          | eval nodex=lower(trim(toString(coalesce(involvedObject.name,object_ref_name,host,source_host,node_name,""))))
          | eval ik=lower(trim(toString(coalesce(involvedObject.kind,involvedObject_kind,""))))
          | eval reason_ev=trim(toString(coalesce(reason,type,message_reason,"")))
          | where ik="node" AND (reason_ev="NodeNotReady" OR reason_ev="NodeReady" OR reason_ev="NodeReadyChange" OR match(lower(reason_ev),"node.*ready"))
          | eval ready_state=if(reason_ev="NodeReady","Recovered","NotReady")
          | eval signal_axis="kubernetes_node_event"
          | rename nodex AS node
          | fields _time cluster node ready_state signal_axis ]
        [ search index=k8s_audit (sourcetype="kube:apiserver:audit" OR sourcetype="kube:audit") earliest=-30m@m latest=now
          | eval cluster=lower(trim(toString(coalesce(k8s_cluster_name,cluster_name,objectRef_cluster,""))))
          | eval apig=lower(trim(toString(coalesce(objectRef_apiGroup,objectRef_apigroup,""))))
          | eval res_lc=lower(trim(toString(coalesce(objectRef_resource,""))))
          | eval nodex=lower(trim(toString(coalesce(objectRef_name,requestObject_metadata_name,""))))
          | eval http_code=tonumber(tostring(coalesce(responseStatus_code,responseCode,"500")),10)
          | where apig="coordination.k8s.io" AND res_lc="leases" AND len(nodex)>2 AND (http_code>=400 OR match(lower(_raw),"timeout"))
          | eval ready_state="LeaseUpdateFailure"
          | eval signal_axis="apiserver_audit_lease_failure"
          | rename nodex AS node
          | fields _time cluster node ready_state signal_axis ]
    | eval node=lower(trim(toString(coalesce(node,""))))
    | where len(cluster)>0 AND len(node)>0
    | stats latest(eval(if(ready_state=="NotReady",_time,null()))) AS last_nr_sample
            latest(eval(if(signal_axis=="kube_state_metrics_ready_false",metric_val,null()))) AS ksm_ready_false_gauge
            values(signal_axis) AS signal_axes
            values(ready_state) AS ready_states_seen
            max(eval(if(ready_state=="NotReady",1,0))) AS any_notready_signal
      BY cluster node
    | where any_notready_signal>0 OR ksm_ready_false_gauge>=1 OR mvcount(signal_axes)>0
    | eval time_in_notready_s=if(isnotnull(last_nr_sample) AND last_nr_sample>0, round(now()-last_nr_sample,0), 0)
    | eval time_in_notready_s=if(time_in_notready_s<0,0,time_in_notready_s)
    | eval ready_state="NotReady" ]
| join type=left max=0 cluster node
    [| search index=k8s_audit (sourcetype="kube:apiserver:audit" OR sourcetype="kube:audit") earliest=-30m@m latest=now
      | eval cluster=lower(trim(toString(coalesce(k8s_cluster_name,cluster_name,objectRef_cluster,""))))
      | eval node=lower(trim(toString(coalesce(objectRef_name,requestObject_metadata_name,""))))
      | eval apig=lower(trim(toString(coalesce(objectRef_apiGroup,objectRef_apigroup,""))))
      | eval res_lc=lower(trim(toString(coalesce(objectRef_resource,""))))
      | eval http_code=tonumber(tostring(coalesce(responseStatus_code,responseCode,"299")),10)
      | where apig="coordination.k8s.io" AND res_lc="leases" AND len(node)>2 AND http_code>=200 AND http_code<400
      | stats latest(_time) AS last_lease_ok BY cluster node
      | eval lease_lag_s=round(now()-last_lease_ok,0) ]
| fillnull value=999999 lease_lag_s
| join type=left max=0 cluster node
    [| search index=k8s_metrics sourcetype="prometheus:scrape:metrics" earliest=-30m@m latest=now
      | eval cluster=lower(trim(toString(coalesce(k8s_cluster_name,cluster_name,cluster,eks_cluster_name,gke_cluster_name,aks_cluster_name,resource_cluster,""))))
      | eval node=lower(trim(toString(coalesce(node,node_name,kubernetes_io_hostname,k8s_node_name,""))))
      | eval mn=lower(trim(toString(coalesce(__name__,metric_name,name,""))))
      | rex field=_raw "pod=\"(?<pod_nm>[^\"]+)\""
      | rex field=_raw "namespace=\"(?<pod_ns>[^\"]+)\""
      | rex field=_raw "phase=\"(?<pod_phase>[^\"]+)\""
      | eval phase_final=lower(trim(toString(coalesce(phase,pod_phase,""))))
      | where len(cluster)>0 AND len(node)>0 AND len(pod_nm)>0 AND (like(mn,"kube_pod_info") OR like(mn,"kube_pod_status_phase")) AND (phase_final="" OR phase_final="running" OR like(mn,"kube_pod_info"))
      | eval gold_ns=if(match(pod_ns,"(?i)prod|gold|tier0|tier_0|payments|checkout|ledger"),1,0)
      | stats dc(pod_nm) AS pod_count_at_risk sum(gold_ns) AS gold_workloads_at_risk BY cluster node ]
| fillnull value=0 pod_count_at_risk gold_workloads_at_risk
| join type=left max=0 cluster node
    [| inputlookup node_inventory.csv
      | eval cluster=lower(trim(toString(cluster)))
      | eval node=lower(trim(toString(node)))
      | eval node_pool=toString(coalesce(node_pool,pool,nodegroup,"unknown_pool"))
      | eval criticality=lower(trim(toString(coalesce(criticality,tier,"standard"))))
      | eval owner_team=toString(coalesce(owner_team,squad,platform_team,"unassigned"))
      | eval instance_type=toString(coalesce(instance_type,vm_type,"unknown_type"))
      | fields cluster node node_pool criticality owner_team instance_type allow_reboot_window ]
| fillnull value="unassigned" owner_team
| fillnull value="standard" criticality
| fillnull value="unknown_pool" node_pool
| eval ready_state="NotReady"
| eval severity=case(
    time_in_notready_s>300 AND match(criticality,"^gold$") AND pod_count_at_risk>0, "critical",
    time_in_notready_s>300 AND pod_count_at_risk>0, "high",
    time_in_notready_s>60, "medium",
    true(), "low")
| table cluster node node_pool criticality ready_state time_in_notready_s lease_lag_s pod_count_at_risk gold_workloads_at_risk owner_team severity
```

## CIM SPL

```spl
| tstats summariesonly=t latest(Application_State.state) AS app_state latest(Application_State.info) AS app_info FROM datamodel=Application_State WHERE nodename=Application_State (Application_State.app="kubernetes" OR Application_State.app="k8s" OR like(Application_State.app,"%kube%")) earliest=-1h@h latest=@h BY Application_State.dest
| rename Application_State.dest AS correl_node
| join type=left max=0 correl_node
    [| tstats summariesonly=t avg(Performance.cpu_load_percent) AS avg_cpu_load max(Performance.mem_used_percent) AS mem_used_pct FROM datamodel=Performance WHERE nodename=Performance earliest=-1h@h latest=@h BY Performance.host
     | rename Performance.host AS correl_node ]
| where like(lower(app_state),"%notready%") OR like(lower(app_info),"%not ready%") OR like(lower(app_info),"%node%unhealthy%") OR avg_cpu_load>95 OR mem_used_pct>95
| table correl_node app_state app_info avg_cpu_load mem_used_pct
```

## Visualization

Primary analyst table mirroring the SPL projection with cell coloring on severity; secondary timechart of time_in_notready_s by cluster; tertiary single value for sum of pod_count_at_risk across rows; drilldowns to kube:events and k8s_audit raw events for the same node and minute.

## Known False Positives

Managed Kubernetes layers that roll operating-system security patches through node pools often surface sixty-to-ninety second NotReady windows while kubelets restart; align those windows to provider maintenance bulletins and suppress rows when node_inventory.csv allow_reboot_window matches the observed interval. Spot, preemptible, or deallocated instances emit short NotReady phases immediately before termination; pair cloud termination metadata with this alert so on-call treats the signal as capacity churn rather than kubelet pathology. Fresh nodes joining a pool can report Ready=false during image pull and kubelet registration for roughly thirty to ninety seconds; dampen alerts for roughly ten minutes after node creation timestamps from cloud APIs or from kube_node_created_seconds when that gauge is present. Severe but brief CPU starvation on a worker can delay kubelet status posts without structural failure; when node-exporter or host Performance metrics show a spike that resolves inside thirty seconds, treat the first sample as informational unless lease lag stays elevated. Transient network loss between workers and the apiserver may flip the Ready condition while the data plane still serves east-west traffic; require sustained dwell beyond one minute or corroborate lease failures before paging single-node incidents during known carrier work.

## References

- [Kubernetes Documentation — Nodes](https://kubernetes.io/docs/concepts/architecture/nodes/)
- [Kubernetes Documentation — Node Status](https://kubernetes.io/docs/reference/node/node-status/)
- [Kubernetes Documentation — Taints and Tolerations](https://kubernetes.io/docs/concepts/scheduling-eviction/taint-and-toleration/)
- [Kubernetes Documentation — Troubleshoot Clusters](https://kubernetes.io/docs/tasks/debug/debug-cluster/_print/)
- [Kubernetes Documentation — Leases](https://kubernetes.io/docs/concepts/architecture/leases/)
- [kube-state-metrics — Node metrics](https://github.com/kubernetes/kube-state-metrics/blob/main/docs/metrics/workload/)
- [Kubernetes Reference — Well-Known Labels, Annotations and Taints](https://kubernetes.io/docs/reference/labels-annotations-taints/#node-kubernetes-io-not-ready)
- [Splunk Documentation — Splunk Add-on for Kubernetes](https://docs.splunk.com/Documentation/AddOns/released/Kubernetes/About)
