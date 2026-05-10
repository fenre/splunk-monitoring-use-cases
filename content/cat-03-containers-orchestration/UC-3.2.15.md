<!-- AUTO-GENERATED from UC-3.2.15.json — DO NOT EDIT -->

---
id: "3.2.15"
title: "Kubernetes DaemonSet Rollout Drift, Per-Node Coverage Gaps, and Update-Strategy Stalls (DaemonSet Coverage Axis)"
status: "verified"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-3.2.15 · Kubernetes DaemonSet Rollout Drift, Per-Node Coverage Gaps, and Update-Strategy Stalls (DaemonSet Coverage Axis)

> **Criticality:** Medium &middot; **Difficulty:** Intermediate &middot; **Pillar:** Observability &middot; **Type:** Reliability, Availability &middot; **Wave:** Walk &middot; **Status:** Verified

*We watch the small fleet-wide helpers that must run on every eligible machine. When counts fall out of line, updates stall, or pods land on the wrong machines, logging, networking, or security layers can go partly blind, so we raise a clear signal.*

---

## Description

Detects Kubernetes DaemonSet coverage drift and update-strategy stalls using kube-state-metrics DaemonSet gauges and owner metadata rather than Deployment replica semantics or Node Ready heartbeats alone. The analytic correlates kube_daemonset_status_desired_number_scheduled against kube_daemonset_status_number_ready, kube_daemonset_status_current_number_scheduled, and kube_daemonset_status_number_available, surfaces kube_daemonset_status_number_misscheduled selector drift, compares kube_daemonset_status_updated_number_scheduled against desired for RollingUpdate lag sustained beyond rolling_stall_min_sec inside the search window, highlights kube_daemonset_metadata_generation ahead of kube_daemonset_status_observed_generation for controller lag, joins kube_node_labels fleet cardinality for placement troubleshooting, and cross-checks kube_pod_owner DaemonSet pod counts against scheduled gauges. UC-3.2.6 remains Deployment rollout health, UC-3.2.3 remains node NotReady liveness, UC-3.2.10 remains pod crash loops, and UC-3.2.41 remains Service zero-ready endpoints.

## Value

Platform, observability, and security teams gain one row per breached DaemonSet that names cluster, namespace, workload_class, gauge tuple, generation lag, rolling lag units, misschedule state, kube_pod_owner cardinality, kube_node_labels fleet scale, minute-derived coverage_gap_duration_sec, and tier-aware severity so they fix logging, CNI, kube-proxy, Falco, or Fluentd gaps before asymmetric blind spots become incidents. Customers avoid mysterious pockets without telemetry or policy enforcement when agents are DaemonSet-managed. Audit-friendly exports show controller truth distinct from Deployment-centric dashboards.

## Implementation

Ingest kube-state-metrics DaemonSet gauges plus kube_pod_owner DaemonSet parents into k8s_metrics, ship kube_node_labels for fleet selector context, publish daemonset_inventory.csv with owner_team and workload_class, save uc_3_2_15_kube_daemonset_coverage_axis every five minutes with earliest=-2h@m, route critical and high severities for tier-1 CNI or logging namespaces, and validate by inducing a lab selector mismatch while comparing Splunk to kubectl describe daemonset.

## Evidence

Saved search uc_3_2_15_kube_daemonset_coverage_axis with five-minute schedule; versioned daemonset_inventory.csv; weekly CSV export of the closing table to a restricted evidence index with kube-state-metrics chart version and collector digest.

## Control test

### Positive scenario

In lab namespace uc3215-lab apply a DaemonSet with a nodeSelector that excludes most Ready nodes while kube-state-metrics keeps scraping, wait until kube_daemonset_status_desired_number_scheduled differs from kube_daemonset_status_number_ready for longer than coverage_gap_min_sec inside the search window, run uc_3_2_15_kube_daemonset_coverage_axis, and expect a qualifying row with non-zero coverage_gap_duration_sec or ready_desired_gap when daemonset_inventory.csv marks tier prod.

### Negative scenario

Deploy a healthy DaemonSet that matches every node with a permissive nodeSelector in the same lab namespace, confirm gauges converge within two scrape intervals, and verify the saved search emits no qualifying rows for that DaemonSet across thirty minutes when no misschedule or generation lag is present.

## Detailed Implementation

### Step 1 — Prerequisites

Head of Platform owns this control with Kubernetes platform site reliability engineers, the observability team operating Splunk OpenTelemetry Collector plus kube-state-metrics, and security engineering when DaemonSets carry Falco, Cilium, Calico, kube-proxy, or Fluentd-class agents. This use case isolates the DaemonSet controller coverage axis only: per-node scheduling completeness, RollingUpdate convergence of updated pods against desired counts, OnDelete semantics where generation advances faster than pod turnover, observed generation lag behind metadata generation, and kube_daemonset_status_number_misscheduled drift where pods sit on nodes that no longer match the selector story. UC-3.2.6 remains the Deployment replica and Progressing condition plane; never treat replica convergence there as proof that a node-level agent DaemonSet is whole. UC-3.2.3 remains kubelet Ready=false and lease eviction blast radius on workers; a healthy Ready node can still miss a DaemonSet pod when selectors, taints, tolerations, or priority rules change. UC-3.2.10 remains CrashLoopBackOff and kubelet waiting reasons after a container starts; a DaemonSet can report ready counts that lag while pods restart underneath. UC-3.2.41 remains Service Endpoints and EndpointSlices with zero ready backends north of kube-proxy programming; that is service discovery emptiness, not the DaemonSet object status gauges exported by kube-state-metrics.

Signal inventory you must certify before alerts: kube_daemonset_status_desired_number_scheduled, kube_daemonset_status_number_ready, kube_daemonset_status_current_number_scheduled, kube_daemonset_status_number_available, kube_daemonset_status_number_misscheduled, kube_daemonset_status_updated_number_scheduled, kube_daemonset_status_observed_generation, kube_daemonset_metadata_generation, kube_daemonset_spec_strategy_rolling_update_max_unavailable when your kube-state-metrics build exposes the strategy gauges, kube_node_labels for fleet cardinality and selector troubleshooting context, and kube_pod_owner lines whose owner_kind equals DaemonSet for a secondary pod cardinality cross-check against current_number_scheduled. Splunk indexes follow other cat-3 gold controls: k8s_metrics for Prometheus text or OTLP-normalized scrapes, optional k8s when you dual-write object metrics, and governance index patterns documented in your landing zone. HEC tokens stay in vaults with quarterly rotation. RBAC for collectors must list watches on DaemonSets, Pods, Nodes, and controllers without granting Secret read unless policy demands it.

Governance lookup daemonset_inventory.csv must carry cluster, namespace, daemonset, owner_team, workload_class, and tier or workload_tier. workload_class should use coarse values such as logging, cni, security, kube_proxy, ebpf_agent, mesh, general so severity case logic can prioritize Calico, Cilium, Falco, Fluentd, Vector, kube-proxy, and eBPF sensor fleets without hard-coding every commercial name in SPL. Refresh the CSV when new platform DaemonSets onboard or when tier-1 contracts change. Optional columns such as ondelete_expected, gpu_selector_exclusion, and eks_fargate_scope let macros suppress legitimate shape differences.

CIM mapping uses Application_State because DaemonSet-managed agents are first-class application availability objects on each node: their ready and scheduled counts describe whether instrumentation and dataplane hooks are present, not merely whether a VM ping succeeds. Inventory is the second model because DaemonSets are inventory-bearing objects with generations, labels, and strategy knobs that auditors expect to see correlated against node and cluster inventory rows when you normalize Kubernetes entities into CMDB-style summaries.

Risk briefing for executives: a logging or CNI DaemonSet with holes means some nodes stop forwarding telemetry or stop enforcing network policy while others look fine, which creates asymmetric incident blindness and partial exploit surfaces. Generation lag with a nonzero kube_daemonset_status_number_misscheduled count often precedes painful manual deletes of stale pods that landed before a selector tightened.

Differentiation recap: DaemonSet coverage is the axis; Deployment rollouts, Node NotReady, CrashLoopBackOff, and Service endpoint emptiness are explicitly out of scope as primary detectors even though you will pivot to them during troubleshooting.

Hardware and cloud scope: Amazon EKS, Google GKE, Microsoft AKS, Red Hat OpenShift, VMware Tanzu, and self-managed clusters where kube-state-metrics RBAC can list DaemonSets cluster-wide; Arm and x86 worker fleets are in scope when metric text lines remain Prometheus compatible. Document Fargate or serverless worker classes where DaemonSets are not scheduled so inventory lookups carry eks_fargate_scope or equivalent to avoid cruel false escalations.

Training: teach responders to read desired versus current versus ready versus updated versus available together, and to treat kube_daemonset_status_observed_generation less than kube_daemonset_metadata_generation as controller reconcile debt distinct from image pull failures.

Review cadence: quarterly replay one historical DaemonSet incident after kube-state-metrics upgrades because label rewriting rules change.

FinOps alignment: stalled RollingUpdates still burn cloud spend when surge equivalents exhaust budgets on large nodes; pair this UC with capacity reviews when maxUnavailable semantics interact with huge machine shapes.

Security alignment: Falco or syscall sensor gaps on a subset of nodes violate assumed uniform detection posture; severity logic elevates security workload_class rows in production tiers.

Performance alignment: multisearch plus two joins costs scheduler time; keep alert cadence at five minutes for full joins and use a summary index for fleet dashboards at fifteen minutes if Job Inspector complains.

Documentation alignment: wiki-link this UC beside DaemonSet update strategy documentation, PodDisruptionBudget interactions with DaemonSet pods, and taint-and-toleration runbooks so new engineers land on the right detector first.

Telemetry hygiene: deduplicate overlapping Prometheus and OpenTelemetry scrapes without stable dedup keys only after you understand double-counting risk on histograms unrelated to this search.

Operator wellbeing note: pair this alert with shift handoff templates so secondary responders inherit gauge deltas without re-running the full SPL manually.

Post-incident review note: require root cause category selector_drift, taint_change, image_rollout, strategy_stall, capacity, cordon_maintenance, provider_exemption, or scrape_gap for every critical page from this UC.

Closing prerequisites checklist: indexes named, kube-state-metrics DaemonSet metric families enumerated, daemonset_inventory.csv schema documented, boundaries versus UC-3.2.6, UC-3.2.3, UC-3.2.10, and UC-3.2.41 restated, CIM Application_State plus Inventory rationale captured for reviewers who ask why Performance is not listed as a primary model here.

### Step 2 — Configure data collection

Deploy kube-state-metrics with cluster-scoped RBAC that can list DaemonSets, Pods, Nodes, and owners. Point Splunk OpenTelemetry Collector prometheus receiver or prometheus_simple scrape jobs at the kube-state-metrics Service on port 8080 or 8443 depending on your chart, preserve daemonset, namespace, pod, node, owner_kind, owner_name, and cluster labels through relabel_config blocks, and export to HEC into index=k8s_metrics with sourcetype prometheus:scrape:metrics. Mirror UC-3.2.6 collector hygiene: bearer_token_file for TLS kubelet scrapes is separate from kube-state-metrics HTTP scraping inside the cluster.

Concrete ServiceMonitor style reference:

apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: kube-state-metrics-daemonset
  namespace: monitoring
spec:
  selector:
    matchLabels:
      app.kubernetes.io/name: kube-state-metrics
  endpoints:
    - port: http-metrics
      interval: 30s
      path: /metrics

OpenTelemetry Collector fragment showing prometheus scrape plus splunk_hec exporter:

receivers:
  prometheus:
    config:
      scrape_configs:
        - job_name: kube-state-metrics
          kubernetes_sd_configs:
            - role: endpoints
          relabel_configs:
            - source_labels: [__meta_kubernetes_service_name]
              action: keep
              regex: kube-state-metrics
exporters:
  splunk_hec/metrics:
    token: ${SPLUNK_HEC_TOKEN}
    endpoint: https://splunk.example.com:8088/services/collector
    index: k8s_metrics
    sourcetype: prometheus:scrape:metrics
service:
  pipelines:
    metrics:
      receivers: [prometheus]
      exporters: [splunk_hec/metrics]

daemonset_inventory.csv sample schema:

cluster,namespace,daemonset,owner_team,workload_class,tier
prod-eks-us-east-1,kube-system,calico-node,platform-net,cni,prod
prod-eks-us-east-1,logging,fluent-bit,observability-sre,logging,prod
prod-eks-us-east-1,kube-system,kube-proxy,platform-net,kube_proxy,prod

Validate raw signal presence before alerts: index=k8s_metrics kube_daemonset_status_desired_number_scheduled earliest=-30m, index=k8s_metrics kube_pod_owner owner_kind=DaemonSet earliest=-30m, index=k8s_metrics kube_node_labels earliest=-30m. Skew between scrapes must stay under sixty seconds for meaningful minute_gap joins.

Security: redact internal hostnames from collector debug logs. Restrict elevated search roles to platform engineers.

props.conf guidance: normalize __name__, value, namespace, and daemonset fields onto indexed extractions where volume warrants tscollect experiments; keep coalesce ladders in SPL until extractions stabilize.

When HEC receives OpenTelemetry protobuf translations instead of Prometheus text, extend rex arms with metric_name coalesce paths identical to UC-3.2.14 patterns.

Cloud control planes: on EKS verify security groups still allow node to cluster IP reachability for metrics after landing-zone changes; on GKE verify managed Prometheus if you offloaded scrapes; on AKS verify managed Grafana agent label mapping still populates daemonset.

Frequency: scrape interval, alert interval, coverage_gap_min_sec, and rolling_stall_min_sec must align mathematically; a ten-minute coverage gate with one-minute bucketing and a five-minute alert schedule is a sane pairing for tier-1.

Back-pressure: if kube-apiserver watch disconnects, collector buffers should not grow without bound; set retry and drop policies per vendor guidance.

Version pinning: record kube-state-metrics chart version in evidence packs quarterly.

Integration with kubectl: operators should still run kubectl describe daemonset for instantaneous truth; Splunk carries history and correlation that kubectl alone lacks across clusters.

Dashboard seeds: single value of distinct DaemonSets in breach by cluster, timechart of kube_daemonset_status_number_misscheduled by namespace, and table of this UC output for executive summaries.

Summary index optional: materialize five-minute snapshots of DaemonSet gauge tuples into k8s_daemonset_summary when raw k8s_metrics scan costs dominate.

Closing data collection checklist: ServiceMonitor or scrape job live, validation searches green, collector TLS verified, deduplication story documented when dual agents scrape the same targets, daemonset_inventory.csv published with workload_class semantics agreed between platform and security.

### Step 3 — Create the search and alert

Save the SPL as uc_3_2_15_kube_daemonset_coverage_axis with five-minute schedule, dispatch earliest=-2h@m, dispatch latest=now, and alert when severity is critical or high for tier-1 rows. Throttle duplicate pages per cluster, namespace, and daemonset for thirty minutes unless severity escalates from high to critical. Attach drilldown searches to kube_pod_owner for the same DaemonSet and to UC-3.2.3 node panels when misschedule_flag suggests node skew.

Understanding the pipeline: the opening comment macro lists tunables so on-call engineers retune without opening this document. eval coverage_gap_min_sec and rolling_stall_min_sec centralize persistence gates referenced in rolling_update_stall logic. join with tstats against Inventory provides a CIM-aligned correlation tick count that helps justify dual-model mapping during audits; if Inventory acceleration is absent in a lab, the join still type=left preserves DaemonSet rows. multisearch fans two arms so silent kube_pod_owner exports cannot zero the entire detection while kube-state-metrics continues to emit DaemonSet gauges. The first arm ends with stats latest by cluster, namespace, and daemonset so rows collapse before the outer stats merges arms. coalesce ladders tolerate camelCase and snake_case label exports. The kube_pod_owner arm estimates distinct pods owned by DaemonSet controllers for a coarse parity check against kube_daemonset_status_current_number_scheduled when series stay healthy.

The first join subsearch rebuckets scrapes to one minute, recomputes desired, ready, and current per minute, flags minute_gap when coverage diverges, then measures coverage_gap_duration_sec as the span between earliest and latest gap minutes inside the search window. Treat this duration as supportive evidence for sustained mismatch; tighten gates in savedsearches.conf if your scrape interval is slower than one minute. The second join subsearch summarizes kube_node_labels cardinality per cluster for selector troubleshooting context referenced in runbooks. inputlookup daemonset_inventory.csv enriches owner_team, workload_class, and tier for case-based severity. eventstats median(...) by cluster adds fleet_ds_desired_median so analysts see whether a breached DaemonSet is an outlier. streamstats count by cluster labels ds_cluster_row_seq for cheap uniqueness in exports. The closing table lists analyst columns exactly as named in the implementation contract.

cimSpl in the JSON field mirrors Inventory and Application_State tstats usage for environments that map Kubernetes node identities into those models; adapt nodename filters to your TA.

Paste-and-run SPL for alerts and dashboards must match the spl JSON field exactly:

```spl
`comment("UC-3.2.15 Kubernetes DaemonSet coverage drift, misschedule, generation lag, RollingUpdate stall axis. Tunables: indexes k8s_metrics k8s; sourcetypes prometheus:scrape:metrics kube:objects:metrics; lookup daemonset_inventory.csv; coverage_gap_min_sec=600; rolling_stall_min_sec=1800; earliest=-2h@m latest=now")`
| eval coverage_gap_min_sec=600
| eval rolling_stall_min_sec=1800
| eval join_key="uc3215"
| join type=left join_key [
| tstats count AS inventory_context_tick FROM datamodel=Inventory WHERE nodename=Inventory earliest=-2h@h latest=now
| eval join_key="uc3215"
]
| fields - join_key inventory_context_tick
| multisearch [
    [ search ((index=k8s_metrics OR index=k8s) (sourcetype="prometheus:scrape:metrics" OR sourcetype="kube:objects:metrics")) earliest=-2h@m latest=now
      | eval cluster=trim(toString(coalesce(cluster, cluster_name, k8s_cluster_name, eks_cluster_name, gke_cluster_name, "")))
      | eval mn=lower(trim(toString(coalesce(metric_name, __name__, name, MetricName, ""))))
      | rex field=_raw "daemonset=\\\"(?<daemonset>[^\\\"]+)\\\""
      | rex field=_raw "namespace=\\\"(?<namespace>[^\\\"]+)\\\""
      | rex field=_raw "\\s(?<mval>[0-9.eE+-]+)\\s*$"
      | where like(mn, "kube_daemonset_%")
      | eval mval=tonumber(mval, 10)
      | eval kube_daemonset_status_desired_number_scheduled=if(like(mn, "%kube_daemonset_status_desired_number_scheduled%"), mval, null())
      | eval kube_daemonset_status_number_ready=if(like(mn, "%kube_daemonset_status_number_ready%"), mval, null())
      | eval kube_daemonset_status_current_number_scheduled=if(like(mn, "%kube_daemonset_status_current_number_scheduled%"), mval, null())
      | eval kube_daemonset_status_number_available=if(like(mn, "%kube_daemonset_status_number_available%"), mval, null())
      | eval kube_daemonset_status_number_misscheduled=if(like(mn, "%kube_daemonset_status_number_misscheduled%"), mval, null())
      | eval kube_daemonset_status_updated_number_scheduled=if(like(mn, "%kube_daemonset_status_updated_number_scheduled%"), mval, null())
      | eval kube_daemonset_status_observed_generation=if(like(mn, "%kube_daemonset_status_observed_generation%"), mval, null())
      | eval kube_daemonset_metadata_generation=if(like(mn, "%kube_daemonset_metadata_generation%"), mval, null())
      | eval kube_daemonset_spec_strategy_rolling_update_max_unavailable=if(like(mn, "%kube_daemonset_spec_strategy_rolling_update_max_unavailable%"), mval, null())
      | stats latest(kube_daemonset_status_desired_number_scheduled) AS kube_daemonset_status_desired_number_scheduled latest(kube_daemonset_status_number_ready) AS kube_daemonset_status_number_ready latest(kube_daemonset_status_current_number_scheduled) AS kube_daemonset_status_current_number_scheduled latest(kube_daemonset_status_number_available) AS kube_daemonset_status_number_available latest(kube_daemonset_status_number_misscheduled) AS kube_daemonset_status_number_misscheduled latest(kube_daemonset_status_updated_number_scheduled) AS kube_daemonset_status_updated_number_scheduled latest(kube_daemonset_status_observed_generation) AS kube_daemonset_status_observed_generation latest(kube_daemonset_metadata_generation) AS kube_daemonset_metadata_generation latest(kube_daemonset_spec_strategy_rolling_update_max_unavailable) AS kube_daemonset_spec_strategy_rolling_update_max_unavailable BY cluster namespace daemonset ]
    [ search ((index=k8s_metrics OR index=k8s) (sourcetype="prometheus:scrape:metrics" OR sourcetype="kube:objects:metrics")) earliest=-2h@m latest=now
      | eval cluster=trim(toString(coalesce(cluster, cluster_name, k8s_cluster_name, eks_cluster_name, gke_cluster_name, "")))
      | eval mn=lower(trim(toString(coalesce(metric_name, __name__, name, MetricName, ""))))
      | rex field=_raw "pod=\\\"(?<pod_nm>[^\\\"]+)\\\""
      | rex field=_raw "namespace=\\\"(?<pod_ns>[^\\\"]+)\\\""
      | rex field=_raw "owner_kind=\\\"(?<owner_kd>[^\\\"]+)\\\""
      | rex field=_raw "owner_name=\\\"(?<owner_nm>[^\\\"]+)\\\""
      | where like(mn, "%kube_pod_owner%") AND owner_kd="DaemonSet"
      | stats dc(pod_nm) AS kube_pod_owner_ds_pod_dc BY cluster pod_ns owner_nm
      | rename pod_ns AS namespace owner_nm AS daemonset ]
| stats max(kube_daemonset_status_desired_number_scheduled) AS kube_daemonset_status_desired_number_scheduled max(kube_daemonset_status_number_ready) AS kube_daemonset_status_number_ready max(kube_daemonset_status_current_number_scheduled) AS kube_daemonset_status_current_number_scheduled max(kube_daemonset_status_number_available) AS kube_daemonset_status_number_available max(kube_daemonset_status_number_misscheduled) AS kube_daemonset_status_number_misscheduled max(kube_daemonset_status_updated_number_scheduled) AS kube_daemonset_status_updated_number_scheduled max(kube_daemonset_status_observed_generation) AS kube_daemonset_status_observed_generation max(kube_daemonset_metadata_generation) AS kube_daemonset_metadata_generation max(kube_daemonset_spec_strategy_rolling_update_max_unavailable) AS kube_daemonset_spec_strategy_rolling_update_max_unavailable max(kube_pod_owner_ds_pod_dc) AS kube_pod_owner_ds_pod_dc BY cluster namespace daemonset
| join type=left max=0 cluster namespace daemonset [
    search ((index=k8s_metrics OR index=k8s) (sourcetype="prometheus:scrape:metrics" OR sourcetype="kube:objects:metrics")) earliest=-2h@m latest=now ("kube_daemonset_status_desired_number_scheduled" OR "kube_daemonset_status_number_ready" OR "kube_daemonset_status_current_number_scheduled")
      | eval cluster=trim(toString(coalesce(cluster, cluster_name, k8s_cluster_name, eks_cluster_name, gke_cluster_name, "")))
      | eval mn=lower(trim(toString(coalesce(metric_name, __name__, name, MetricName, ""))))
      | rex field=_raw "daemonset=\\\"(?<daemonset>[^\\\"]+)\\\""
      | rex field=_raw "namespace=\\\"(?<namespace>[^\\\"]+)\\\""
      | rex field=_raw "\\s(?<mval>[0-9.eE+-]+)\\s*$"
      | eval mval=tonumber(mval, 10)
      | bucket _time span=1m aligntime=earliest
      | stats max(eval(if(like(mn, "%kube_daemonset_status_desired_number_scheduled%"), mval, null()))) AS desired max(eval(if(like(mn, "%kube_daemonset_status_number_ready%"), mval, null()))) AS ready max(eval(if(like(mn, "%kube_daemonset_status_current_number_scheduled%"), mval, null()))) AS current BY cluster namespace daemonset _time
      | fillnull value=0 desired ready current
      | eval minute_gap=if((desired!=ready) OR (current<desired) OR (ready<desired), 1, 0)
      | where minute_gap=1
      | stats earliest(_time) AS coverage_gap_first_ts latest(_time) AS coverage_gap_last_ts BY cluster namespace daemonset
      | eval coverage_gap_duration_sec=round(coverage_gap_last_ts-coverage_gap_first_ts, 0) ]
| join type=left max=0 cluster [
    search ((index=k8s_metrics OR index=k8s) (sourcetype="prometheus:scrape:metrics" OR sourcetype="kube:objects:metrics")) earliest=-2h@m latest=now kube_node_labels
      | eval cluster=trim(toString(coalesce(cluster, cluster_name, k8s_cluster_name, eks_cluster_name, gke_cluster_name, "")))
      | eval mn=lower(trim(toString(coalesce(metric_name, __name__, name, MetricName, ""))))
      | rex field=_raw "node=\\\"(?<knode>[^\\\"]+)\\\""
      | where like(mn, "%kube_node_labels%") AND len(knode)>0
      | stats dc(knode) AS kube_node_labels_distinct_nodes BY cluster ]
| join type=left max=0 cluster namespace daemonset [
    | inputlookup daemonset_inventory.csv
      | eval cluster=trim(toString(coalesce(cluster, k8s_cluster, "")))
      | eval namespace=trim(toString(namespace))
      | eval daemonset=trim(toString(coalesce(daemonset, workload, "")))
      | eval owner_team=trim(toString(coalesce(owner_team, team, squad, platform_team, "unassigned")))
      | eval workload_class=lower(trim(toString(coalesce(workload_class, agent_role, "general"))))
      | eval tier=lower(trim(toString(coalesce(tier, workload_tier, env_tier, "dev"))))
      | fields cluster namespace daemonset owner_team workload_class tier ]
| fillnull value=0 kube_daemonset_status_desired_number_scheduled kube_daemonset_status_number_ready kube_daemonset_status_current_number_scheduled kube_daemonset_status_number_available kube_daemonset_status_number_misscheduled kube_daemonset_status_updated_number_scheduled kube_daemonset_status_observed_generation kube_daemonset_metadata_generation kube_pod_owner_ds_pod_dc kube_node_labels_distinct_nodes
| fillnull value="unassigned" owner_team
| fillnull value="general" workload_class
| fillnull value="dev" tier
| eval cluster=coalesce(nullif(trim(cluster), ""), "unknown-cluster")
| eval namespace=coalesce(nullif(trim(namespace), ""), "unknown-namespace")
| eval daemonset=coalesce(nullif(trim(daemonset), ""), "unknown-daemonset")
| eval gen_lag=if(kube_daemonset_metadata_generation>kube_daemonset_status_observed_generation, kube_daemonset_metadata_generation-kube_daemonset_status_observed_generation, 0)
| eval rolling_lag_units=kube_daemonset_status_desired_number_scheduled-kube_daemonset_status_updated_number_scheduled
| eval coverage_gap_duration_sec=coalesce(coverage_gap_duration_sec, 0)
| eval rolling_update_stall=if(rolling_lag_units>0 AND coverage_gap_duration_sec>=rolling_stall_min_sec, 1, 0)
| eval misschedule_flag=if(kube_daemonset_status_number_misscheduled>0, 1, 0)
| eval availability_gap=if(kube_daemonset_status_number_available<kube_daemonset_status_desired_number_scheduled, 1, 0)
| eval ready_desired_gap=if(kube_daemonset_status_number_ready<kube_daemonset_status_desired_number_scheduled, 1, 0)
| eval current_desired_gap=if(kube_daemonset_status_current_number_scheduled<kube_daemonset_status_desired_number_scheduled, 1, 0)
| eval pod_dc_desired_gap=if(kube_pod_owner_ds_pod_dc<kube_daemonset_status_desired_number_scheduled AND kube_daemonset_status_desired_number_scheduled>0, 1, 0)
| eval breach_core=if((coverage_gap_duration_sec>=coverage_gap_min_sec) OR misschedule_flag=1 OR gen_lag>0 OR rolling_update_stall=1 OR availability_gap=1 OR ready_desired_gap=1 OR current_desired_gap=1 OR pod_dc_desired_gap=1, 1, 0)
| where breach_core=1
| eventstats median(kube_daemonset_status_desired_number_scheduled) AS fleet_ds_desired_median BY cluster
| sort 0 cluster namespace daemonset
| streamstats global=f count AS ds_cluster_row_seq BY cluster
| eval severity=case(
    misschedule_flag=1 AND match(tier, "prod|production|tier1|tier-1|gold"), "critical",
    rolling_update_stall=1 AND match(workload_class, "cni|network|kube_proxy|ebpf_agent"), "critical",
    gen_lag>0 AND match(tier, "prod|production|tier1|tier-1|gold"), "high",
    coverage_gap_duration_sec>=1800 AND match(workload_class, "logging|security|falco|ids"), "high",
    ready_desired_gap=1 AND coverage_gap_duration_sec>=coverage_gap_min_sec, "high",
    current_desired_gap=1 AND coverage_gap_duration_sec>=coverage_gap_min_sec, "medium",
    pod_dc_desired_gap=1, "medium",
    rolling_lag_units>0, "medium",
    true(), "low")
| table cluster namespace daemonset owner_team workload_class tier kube_daemonset_status_desired_number_scheduled kube_daemonset_status_number_ready kube_daemonset_status_current_number_scheduled kube_daemonset_status_number_available kube_daemonset_status_number_misscheduled kube_daemonset_status_updated_number_scheduled kube_daemonset_metadata_generation kube_daemonset_status_observed_generation kube_daemonset_spec_strategy_rolling_update_max_unavailable gen_lag rolling_lag_units kube_pod_owner_ds_pod_dc kube_node_labels_distinct_nodes coverage_gap_duration_sec rolling_update_stall misschedule_flag severity fleet_ds_desired_median ds_cluster_row_seq
```

Alert actions: include cluster, namespace, daemonset, coverage_gap_duration_sec, rolling_update_stall, misschedule_flag, severity, owner_team, and workload_class in email or ITSI notable bodies. Provide a drilldown that runs index=k8s_metrics kube_pod_owner owner_kind=DaemonSet owner_name=$daemonset$ earliest=-2h. Provide a secondary drilldown for kubectl audit when index=k8s_audit is populated and you need proof of who changed nodeSelector or strategy.

Performance: if Job Inspector warns on join cost, split fleet dashboards into per-region saved searches or materialize kube_daemonset_status snapshots hourly.

Reliability: during kube-state-metrics upgrades expect brief gaps; require two consecutive intervals of missing metrics before paging scrape outages unless misschedule_flag stays nonzero.

Governance: weekly CSV export of alert rows with lookup commit hash satisfies internal platform evidence when paired with kube-state-metrics version stamps.

savedsearches.conf quantity thresholds should align with row counts from the table command; use alert.track=1 and suppress keys on cluster namespace daemonset.

Closing Step 3 checklist: fenced SPL present, matches spl field, references daemonset_inventory.csv, explains tstats join purpose, documents multisearch arms, clarifies rolling_update_stall logic, and names notification fields.

### Step 4 — Validate

Synthetic coverage gap: in lab namespace uc3215-lab apply a DaemonSet with a nodeSelector that matches only one node while the cluster has three Ready nodes, confirm kube_daemonset_status_desired_number_scheduled stays below three or mismatches ready, observe minute_gap buckets in the join subsearch, and expect coverage_gap_duration_sec to grow beyond coverage_gap_min_sec when you hold the bad selector for fifteen minutes.

Synthetic misschedule: temporarily park a stale pod on a cordoned node with a label that no longer matches the DaemonSet template in a disposable lab only, confirm kube_daemonset_status_number_misscheduled rises above zero in k8s_metrics, execute uc_3_2_15_kube_daemonset_coverage_axis, and expect misschedule_flag equals one with severity at least high when tier marks prod in daemonset_inventory.csv.

Synthetic RollingUpdate stall: set a broken readiness probe on the DaemonSet pod template with RollingUpdate strategy, confirm kube_daemonset_status_updated_number_scheduled lags kube_daemonset_status_desired_number_scheduled while kube_daemonset_metadata_generation advances, and expect rolling_update_stall equals one after rolling_stall_min_sec.

Negative test: deploy a healthy node-exporter-class DaemonSet with generous update strategy in the same lab namespace, confirm gauges converge within two scrape intervals, and verify the saved search emits no qualifying rows for that DaemonSet across thirty minutes when inventory marks it general tier dev.

Field sanity: rename a forwarder field to camelCase-only in a sandbox and verify coalesce still resolves namespace and daemonset labels.

RBAC: readers without k8s_metrics access must see zero rows.

Correlation: compare Splunk timestamps to kubectl get ds -o wide and kubectl get pods -l for the same minute.

Validation SPL for raw metrics presence:

| multisearch [
    [ search index=k8s_metrics earliest=-30m latest=now kube_daemonset_status_desired_number_scheduled | stats count ]
    [ search index=k8s_metrics earliest=-30m latest=now kube_pod_owner DaemonSet | stats count ]
  ]
| stats sum(count) AS samples

Tear-down: delete lab DaemonSets, restore selectors, and confirm saved search result counts return to zero.

Clock skew: verify NTP alignment between nodes, kube-apiserver, and Splunk indexers; skew beyond ninety seconds invalidates coverage_gap_duration_sec comparisons.

Documentation: attach kubectl describe daemonset screenshots to the evidence ticket without exposing Secrets.

Closing Step 4 checklist: positive coverage scenario, negative healthy DaemonSet, metrics presence multisearch, tear-down verified, clock skew warning documented.

### Step 5 — Operationalize & Troubleshoot

Case 1 — kube_daemonset_status_number_misscheduled greater than zero with selector tightening: treat as drift; kubectl get pods -o wide for the DaemonSet, identify nodes hosting pods that violate the current nodeSelector, delete stale pods only under change control, and verify new pods reschedule cleanly.

Case 2 — kube_daemonset_status_observed_generation lags kube_daemonset_metadata_generation for many minutes: treat as controller reconcile backlog; investigate apiserver latency, kube-controller-manager leader election, and etcd health per platform runbooks before restarting controllers.

Case 3 — RollingUpdate stall with kube_daemonset_status_updated_number_scheduled below desired: inspect maxUnavailable and maxSurge analogs, kube_pod_status scheduling events, image pull sibling UC-3.2.14, and probe sibling UC-3.2.43 before blaming the DaemonSet controller alone.

Case 4 — OnDelete strategy with generation advancing but pods on old revisions: confirm strategy in kubectl describe, plan orderly node drains or manual pod deletes per Kubernetes DaemonSet update documentation, and document intentional ondelete_expected in daemonset_inventory.csv when maintenance owns the pacing.

Case 5 — GPU or accelerator DaemonSet legitimately absent on CPU-only nodes: validate nodeSelector and workload_class gpu_selector_exclusion in inventory before paging platform bridges.

Case 6 — Node cordoned for maintenance with DaemonSet pod evicted intentionally: correlate UC-3.2.33 cordon narratives; suppress or downgrade when change records show expected eviction.

Case 7 — Cluster autoscaler adds fresh nodes: allow several minutes for DaemonSet placement after boot; pair with provider node lifecycle telemetry before declaring coverage failure.

Case 8 — Nightly OS patching or batched reboots: align allow_reboot_window style annotations in inventory so security patches do not page as incidents.

Case 9 — Calico or Cilium BGP or dataplane policy updates with brief node lag under ten minutes: require sustained misschedule_flag or minute_gap dwell beyond policy-defined thresholds before executive escalation.

Case 10 — Hardware-tag taints recently added: confirm toleration updates on the DaemonSet catch up; if not, patch tolerations and roll out before assuming CNI failure.

Case 11 — Intentional manual policy where old-generation pods remain by design: mark inventory and mute alerts until the maintenance completes.

Case 12 — Managed node pools with documented DaemonSet exemptions such as Fargate-style compute or provider constraints: ensure eks_fargate_scope or equivalent suppresses rows that can never schedule DaemonSets by architecture.

Dashboard hygiene: keep a panel for kube_daemonset_status_desired_number_scheduled minus kube_daemonset_status_number_ready as a heatmap by namespace, and overlay UC-3.2.3 node NotReady counts when misschedule correlates with node churn.

Evidence retention: archive weekly CSV exports with kube-state-metrics chart version, collector digest, and Splunk search head cluster name.

Training replay: twice-yearly game day that combines selector drift plus RollingUpdate stall to prove operators open this UC before reopening UC-3.2.6.

Governance: when legal requests preservation, include hashed DaemonSet manifests rather than raw Secret-laden YAML in tickets.

Fleet operations note: publish a clone saved search without the closing where clause for monthly reliability reviews so medium severity rolling lag trends remain visible even when paging macros stay tight.

Vendor escalation note: attach kube-controller-manager logs excerpts only when support NDAs permit; otherwise ship Splunk redacted exports with metric line samples only.

Runbook maintenance note: revisit links quarterly because Kubernetes minor releases occasionally rename user-facing event messages even when metrics stay stable.

Closing Step 5 checklist: twelve cases present with exact Case N — formatting, cross-links named to UC-3.2.14, UC-3.2.43, UC-3.2.33, selector and strategy guidance, provider exemption language, plus dashboard and evidence notes for long-term operations.


## SPL

```spl
`comment("UC-3.2.15 Kubernetes DaemonSet coverage drift, misschedule, generation lag, RollingUpdate stall axis. Tunables: indexes k8s_metrics k8s; sourcetypes prometheus:scrape:metrics kube:objects:metrics; lookup daemonset_inventory.csv; coverage_gap_min_sec=600; rolling_stall_min_sec=1800; earliest=-2h@m latest=now")`
| eval coverage_gap_min_sec=600
| eval rolling_stall_min_sec=1800
| eval join_key="uc3215"
| join type=left join_key [
| tstats count AS inventory_context_tick FROM datamodel=Inventory WHERE nodename=Inventory earliest=-2h@h latest=now
| eval join_key="uc3215"
]
| fields - join_key inventory_context_tick
| multisearch [
    [ search ((index=k8s_metrics OR index=k8s) (sourcetype="prometheus:scrape:metrics" OR sourcetype="kube:objects:metrics")) earliest=-2h@m latest=now
      | eval cluster=trim(toString(coalesce(cluster, cluster_name, k8s_cluster_name, eks_cluster_name, gke_cluster_name, "")))
      | eval mn=lower(trim(toString(coalesce(metric_name, __name__, name, MetricName, ""))))
      | rex field=_raw "daemonset=\\\"(?<daemonset>[^\\\"]+)\\\""
      | rex field=_raw "namespace=\\\"(?<namespace>[^\\\"]+)\\\""
      | rex field=_raw "\\s(?<mval>[0-9.eE+-]+)\\s*$"
      | where like(mn, "kube_daemonset_%")
      | eval mval=tonumber(mval, 10)
      | eval kube_daemonset_status_desired_number_scheduled=if(like(mn, "%kube_daemonset_status_desired_number_scheduled%"), mval, null())
      | eval kube_daemonset_status_number_ready=if(like(mn, "%kube_daemonset_status_number_ready%"), mval, null())
      | eval kube_daemonset_status_current_number_scheduled=if(like(mn, "%kube_daemonset_status_current_number_scheduled%"), mval, null())
      | eval kube_daemonset_status_number_available=if(like(mn, "%kube_daemonset_status_number_available%"), mval, null())
      | eval kube_daemonset_status_number_misscheduled=if(like(mn, "%kube_daemonset_status_number_misscheduled%"), mval, null())
      | eval kube_daemonset_status_updated_number_scheduled=if(like(mn, "%kube_daemonset_status_updated_number_scheduled%"), mval, null())
      | eval kube_daemonset_status_observed_generation=if(like(mn, "%kube_daemonset_status_observed_generation%"), mval, null())
      | eval kube_daemonset_metadata_generation=if(like(mn, "%kube_daemonset_metadata_generation%"), mval, null())
      | eval kube_daemonset_spec_strategy_rolling_update_max_unavailable=if(like(mn, "%kube_daemonset_spec_strategy_rolling_update_max_unavailable%"), mval, null())
      | stats latest(kube_daemonset_status_desired_number_scheduled) AS kube_daemonset_status_desired_number_scheduled latest(kube_daemonset_status_number_ready) AS kube_daemonset_status_number_ready latest(kube_daemonset_status_current_number_scheduled) AS kube_daemonset_status_current_number_scheduled latest(kube_daemonset_status_number_available) AS kube_daemonset_status_number_available latest(kube_daemonset_status_number_misscheduled) AS kube_daemonset_status_number_misscheduled latest(kube_daemonset_status_updated_number_scheduled) AS kube_daemonset_status_updated_number_scheduled latest(kube_daemonset_status_observed_generation) AS kube_daemonset_status_observed_generation latest(kube_daemonset_metadata_generation) AS kube_daemonset_metadata_generation latest(kube_daemonset_spec_strategy_rolling_update_max_unavailable) AS kube_daemonset_spec_strategy_rolling_update_max_unavailable BY cluster namespace daemonset ]
    [ search ((index=k8s_metrics OR index=k8s) (sourcetype="prometheus:scrape:metrics" OR sourcetype="kube:objects:metrics")) earliest=-2h@m latest=now
      | eval cluster=trim(toString(coalesce(cluster, cluster_name, k8s_cluster_name, eks_cluster_name, gke_cluster_name, "")))
      | eval mn=lower(trim(toString(coalesce(metric_name, __name__, name, MetricName, ""))))
      | rex field=_raw "pod=\\\"(?<pod_nm>[^\\\"]+)\\\""
      | rex field=_raw "namespace=\\\"(?<pod_ns>[^\\\"]+)\\\""
      | rex field=_raw "owner_kind=\\\"(?<owner_kd>[^\\\"]+)\\\""
      | rex field=_raw "owner_name=\\\"(?<owner_nm>[^\\\"]+)\\\""
      | where like(mn, "%kube_pod_owner%") AND owner_kd="DaemonSet"
      | stats dc(pod_nm) AS kube_pod_owner_ds_pod_dc BY cluster pod_ns owner_nm
      | rename pod_ns AS namespace owner_nm AS daemonset ]
| stats max(kube_daemonset_status_desired_number_scheduled) AS kube_daemonset_status_desired_number_scheduled max(kube_daemonset_status_number_ready) AS kube_daemonset_status_number_ready max(kube_daemonset_status_current_number_scheduled) AS kube_daemonset_status_current_number_scheduled max(kube_daemonset_status_number_available) AS kube_daemonset_status_number_available max(kube_daemonset_status_number_misscheduled) AS kube_daemonset_status_number_misscheduled max(kube_daemonset_status_updated_number_scheduled) AS kube_daemonset_status_updated_number_scheduled max(kube_daemonset_status_observed_generation) AS kube_daemonset_status_observed_generation max(kube_daemonset_metadata_generation) AS kube_daemonset_metadata_generation max(kube_daemonset_spec_strategy_rolling_update_max_unavailable) AS kube_daemonset_spec_strategy_rolling_update_max_unavailable max(kube_pod_owner_ds_pod_dc) AS kube_pod_owner_ds_pod_dc BY cluster namespace daemonset
| join type=left max=0 cluster namespace daemonset [
    search ((index=k8s_metrics OR index=k8s) (sourcetype="prometheus:scrape:metrics" OR sourcetype="kube:objects:metrics")) earliest=-2h@m latest=now ("kube_daemonset_status_desired_number_scheduled" OR "kube_daemonset_status_number_ready" OR "kube_daemonset_status_current_number_scheduled")
      | eval cluster=trim(toString(coalesce(cluster, cluster_name, k8s_cluster_name, eks_cluster_name, gke_cluster_name, "")))
      | eval mn=lower(trim(toString(coalesce(metric_name, __name__, name, MetricName, ""))))
      | rex field=_raw "daemonset=\\\"(?<daemonset>[^\\\"]+)\\\""
      | rex field=_raw "namespace=\\\"(?<namespace>[^\\\"]+)\\\""
      | rex field=_raw "\\s(?<mval>[0-9.eE+-]+)\\s*$"
      | eval mval=tonumber(mval, 10)
      | bucket _time span=1m aligntime=earliest
      | stats max(eval(if(like(mn, "%kube_daemonset_status_desired_number_scheduled%"), mval, null()))) AS desired max(eval(if(like(mn, "%kube_daemonset_status_number_ready%"), mval, null()))) AS ready max(eval(if(like(mn, "%kube_daemonset_status_current_number_scheduled%"), mval, null()))) AS current BY cluster namespace daemonset _time
      | fillnull value=0 desired ready current
      | eval minute_gap=if((desired!=ready) OR (current<desired) OR (ready<desired), 1, 0)
      | where minute_gap=1
      | stats earliest(_time) AS coverage_gap_first_ts latest(_time) AS coverage_gap_last_ts BY cluster namespace daemonset
      | eval coverage_gap_duration_sec=round(coverage_gap_last_ts-coverage_gap_first_ts, 0) ]
| join type=left max=0 cluster [
    search ((index=k8s_metrics OR index=k8s) (sourcetype="prometheus:scrape:metrics" OR sourcetype="kube:objects:metrics")) earliest=-2h@m latest=now kube_node_labels
      | eval cluster=trim(toString(coalesce(cluster, cluster_name, k8s_cluster_name, eks_cluster_name, gke_cluster_name, "")))
      | eval mn=lower(trim(toString(coalesce(metric_name, __name__, name, MetricName, ""))))
      | rex field=_raw "node=\\\"(?<knode>[^\\\"]+)\\\""
      | where like(mn, "%kube_node_labels%") AND len(knode)>0
      | stats dc(knode) AS kube_node_labels_distinct_nodes BY cluster ]
| join type=left max=0 cluster namespace daemonset [
    | inputlookup daemonset_inventory.csv
      | eval cluster=trim(toString(coalesce(cluster, k8s_cluster, "")))
      | eval namespace=trim(toString(namespace))
      | eval daemonset=trim(toString(coalesce(daemonset, workload, "")))
      | eval owner_team=trim(toString(coalesce(owner_team, team, squad, platform_team, "unassigned")))
      | eval workload_class=lower(trim(toString(coalesce(workload_class, agent_role, "general"))))
      | eval tier=lower(trim(toString(coalesce(tier, workload_tier, env_tier, "dev"))))
      | fields cluster namespace daemonset owner_team workload_class tier ]
| fillnull value=0 kube_daemonset_status_desired_number_scheduled kube_daemonset_status_number_ready kube_daemonset_status_current_number_scheduled kube_daemonset_status_number_available kube_daemonset_status_number_misscheduled kube_daemonset_status_updated_number_scheduled kube_daemonset_status_observed_generation kube_daemonset_metadata_generation kube_pod_owner_ds_pod_dc kube_node_labels_distinct_nodes
| fillnull value="unassigned" owner_team
| fillnull value="general" workload_class
| fillnull value="dev" tier
| eval cluster=coalesce(nullif(trim(cluster), ""), "unknown-cluster")
| eval namespace=coalesce(nullif(trim(namespace), ""), "unknown-namespace")
| eval daemonset=coalesce(nullif(trim(daemonset), ""), "unknown-daemonset")
| eval gen_lag=if(kube_daemonset_metadata_generation>kube_daemonset_status_observed_generation, kube_daemonset_metadata_generation-kube_daemonset_status_observed_generation, 0)
| eval rolling_lag_units=kube_daemonset_status_desired_number_scheduled-kube_daemonset_status_updated_number_scheduled
| eval coverage_gap_duration_sec=coalesce(coverage_gap_duration_sec, 0)
| eval rolling_update_stall=if(rolling_lag_units>0 AND coverage_gap_duration_sec>=rolling_stall_min_sec, 1, 0)
| eval misschedule_flag=if(kube_daemonset_status_number_misscheduled>0, 1, 0)
| eval availability_gap=if(kube_daemonset_status_number_available<kube_daemonset_status_desired_number_scheduled, 1, 0)
| eval ready_desired_gap=if(kube_daemonset_status_number_ready<kube_daemonset_status_desired_number_scheduled, 1, 0)
| eval current_desired_gap=if(kube_daemonset_status_current_number_scheduled<kube_daemonset_status_desired_number_scheduled, 1, 0)
| eval pod_dc_desired_gap=if(kube_pod_owner_ds_pod_dc<kube_daemonset_status_desired_number_scheduled AND kube_daemonset_status_desired_number_scheduled>0, 1, 0)
| eval breach_core=if((coverage_gap_duration_sec>=coverage_gap_min_sec) OR misschedule_flag=1 OR gen_lag>0 OR rolling_update_stall=1 OR availability_gap=1 OR ready_desired_gap=1 OR current_desired_gap=1 OR pod_dc_desired_gap=1, 1, 0)
| where breach_core=1
| eventstats median(kube_daemonset_status_desired_number_scheduled) AS fleet_ds_desired_median BY cluster
| sort 0 cluster namespace daemonset
| streamstats global=f count AS ds_cluster_row_seq BY cluster
| eval severity=case(
    misschedule_flag=1 AND match(tier, "prod|production|tier1|tier-1|gold"), "critical",
    rolling_update_stall=1 AND match(workload_class, "cni|network|kube_proxy|ebpf_agent"), "critical",
    gen_lag>0 AND match(tier, "prod|production|tier1|tier-1|gold"), "high",
    coverage_gap_duration_sec>=1800 AND match(workload_class, "logging|security|falco|ids"), "high",
    ready_desired_gap=1 AND coverage_gap_duration_sec>=coverage_gap_min_sec, "high",
    current_desired_gap=1 AND coverage_gap_duration_sec>=coverage_gap_min_sec, "medium",
    pod_dc_desired_gap=1, "medium",
    rolling_lag_units>0, "medium",
    true(), "low")
| table cluster namespace daemonset owner_team workload_class tier kube_daemonset_status_desired_number_scheduled kube_daemonset_status_number_ready kube_daemonset_status_current_number_scheduled kube_daemonset_status_number_available kube_daemonset_status_number_misscheduled kube_daemonset_status_updated_number_scheduled kube_daemonset_metadata_generation kube_daemonset_status_observed_generation kube_daemonset_spec_strategy_rolling_update_max_unavailable gen_lag rolling_lag_units kube_pod_owner_ds_pod_dc kube_node_labels_distinct_nodes coverage_gap_duration_sec rolling_update_stall misschedule_flag severity fleet_ds_desired_median ds_cluster_row_seq
```

## CIM SPL

```spl
| tstats summariesonly=t latest(Inventory.os) AS inv_os latest(Inventory.version) AS inv_ver count AS inv_ev FROM datamodel=Inventory WHERE nodename=Inventory earliest=-2h@h latest=@h BY Inventory.dest
| rename Inventory.dest AS correl_host
| join type=left max=0 correl_host [
| tstats summariesonly=t latest(Application_State.state) AS app_state latest(Application_State.info) AS app_info FROM datamodel=Application_State WHERE nodename=Application_State earliest=-2h@h latest=@h BY Application_State.dest
| rename Application_State.dest AS correl_host ]
| where like(lower(app_state), "degraded") OR like(lower(app_info), "daemonset") OR like(lower(inv_os), "linux")
| table correl_host inv_os inv_ver app_state app_info inv_ev
```

## Visualization

Primary table mirroring the closing SPL projection; timechart of kube_daemonset_status_number_misscheduled by namespace; single value of rolling_update_stall count by cluster; heatmap of desired minus ready; drilldowns to kube_pod_owner and optional node panels.

## Known False Positives

GPU or accelerator DaemonSets legitimately skip CPU-only nodes when nodeSelector excludes non-GPU fleets; confirm workload_class and inventory before paging. OnDelete strategies during deliberate maintenance can show updated counts lagging until operators delete pods; pair with ondelete_expected flags. Tolerations updated on freshly tainted nodes may need one or two reconcile intervals before DaemonSet pods reschedule; dampen short flaps. Recent metadata.generation bumps still rolling within thirty minutes can look like stalls when scrapes are coarse; require rolling_stall_min_sec dwell. Cordoned nodes and voluntary drains evict DaemonSet pods on purpose; correlate cordon state and change tickets. Nodes booting after autoscaler scale-out may lack DaemonSet pods for several minutes; use provider lifecycle metadata. Nightly OS patching cycles with batched reboots create predictable holes; align maintenance windows. Calico or Cilium BGP or policy updates may lag under ten minutes on large fleets; treat sub-threshold gaps as operational noise unless misschedule persists. Hardware-tag taints recently added without matching toleration edits look like incidents until the controller catches up. Intentional Always or manual rollout policies that keep older pod generations by design should carry inventory annotations so alerts mute. EKS Fargate and some AKS constrained profiles cannot run certain DaemonSets; document provider exemptions to avoid false escalations. Test clusters with synthetic partial failures may mimic production breaches; route lab noise with tier filters.

## References

- [Kubernetes — DaemonSet](https://kubernetes.io/docs/concepts/workloads/controllers/daemonset/)
- [Kubernetes — Perform a Rolling Update on a DaemonSet](https://kubernetes.io/docs/tasks/manage-daemon/update-daemon-set/)
- [Kubernetes API Reference — DaemonSet v1 apps](https://kubernetes.io/docs/reference/kubernetes-api/workload-resources/daemon-set-v1/)
- [Kubernetes Community — sig-apps DaemonSet contributor guide](https://github.com/kubernetes/community/blob/master/contributors/devel/sig-apps/daemonset.md)
- [kube-state-metrics — DaemonSet metrics](https://github.com/kubernetes/kube-state-metrics/blob/main/docs/metrics/workload/daemonset-metrics.md)
- [Kubernetes — Assigning Pods to Nodes](https://kubernetes.io/docs/concepts/scheduling-eviction/assign-pod-node/)
- [Amazon EKS — AWS Fargate considerations (DaemonSet limitations)](https://docs.aws.amazon.com/eks/latest/userguide/fargate.html)
- [Azure AKS — Kubernetes core concepts (workloads and nodes)](https://learn.microsoft.com/en-us/azure/aks/concepts-clusters-workloads)
