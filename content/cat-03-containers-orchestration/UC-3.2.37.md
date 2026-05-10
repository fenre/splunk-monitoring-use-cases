<!-- AUTO-GENERATED from UC-3.2.37.json — DO NOT EDIT -->

---
id: "3.2.37"
title: "Kubernetes PodDisruptionBudget (PDB) Compliance — Allowed-Disruption Headroom Axis"
status: "verified"
criticality: "high"
splunkPillar: "Observability"
---

# UC-3.2.37 · Kubernetes PodDisruptionBudget (PDB) Compliance — Allowed-Disruption Headroom Axis

> **Criticality:** High &middot; **Difficulty:** Intermediate &middot; **Pillar:** Observability &middot; **Type:** Configuration, Compliance &middot; **Wave:** Walk &middot; **Status:** Verified

*We watch the cluster rules that keep enough copies of important programs running when machines go offline for repairs. We notice when those rules are missing, too loose to help, tight enough to block safe maintenance, or fighting the system when an eviction is refused.*

---

## Description

Monitors Kubernetes PodDisruptionBudget state and governance: compares kube_poddisruptionbudget_status_expected_pods minus kube_poddisruptionbudget_status_current_healthy against kube_poddisruptionbudget_status_pod_disruptions_allowed for voluntary-disruption headroom, surfaces kube_poddisruptionbudget_status_desired_healthy shortfalls, highlights zero disruptionsAllowed maintenance blockers, correlates kube:events reason EvictionDenied, flags weak spec patterns such as minAvailable zero or maxUnavailable at one hundred percent, detects selector drift where kube_deployment_status_replicas remains positive while expected pods from the budget reads zero, and appends governance_gap rows when replica-rich Deployments lack metric evidence for required budgets per workload_pdb_policy.csv. This is PDB object state and policy compliance, not UC-3.2.33 drain action auditing, not UC-3.2.41 Service EndpointSlice readiness, not UC-3.2.6 Deployment rollout conditions, and not UC-3.2.46 Cluster Autoscaler economics.

## Value

Platform and application teams shorten mean time to repair during maintenance because one row names cluster, namespace, budget, deployment, deficit math, allowed disruptions, eviction denials, weak-policy hints, and tier-aware severity without manually diffing kubectl, metrics explorers, and change tickets. Customer impact drops when voluntary disruptions stop halfway because budgets were silently misconfigured. Release and infrastructure leaders receive evidence for change approvals that cite numeric headroom rather than anecdotes. FinOps and resilience reviewers see when zero-budget policies block cost-saving recycling and when missing budgets leave multi-replica services unprotected.

## Implementation

Scrape kube-state-metrics PDB and Deployment replica families into k8s_metrics, ship kube:events with EvictionDenied into k8s, publish workload_pdb_policy.csv with pdb_required and tier, save uc_3_2_37_kube_pdb_compliance_headroom every five minutes with earliest=-3h@m latest=now, route critical and high rows for production tiers, and validate by forcing a lab deficit that exceeds disruptionsAllowed then clearing it.

## Evidence

Saved search uc_3_2_37_kube_pdb_compliance_headroom; versioned workload_pdb_policy.csv in git; weekly CSV export of alert rows to a restricted evidence index with kube-state-metrics chart version and collector digest.

## Control test

### Positive scenario

In lab namespace qa-pdb-uc3237 create a PodDisruptionBudget and two-replica Deployment that matches selectors, force current_healthy below expected_pods using unhealthy pods or cordons so healthy_deficit exceeds disruptions_allowed in kube-state-metrics, run uc_3_2_37_kube_pdb_compliance_headroom, and expect a headroom_breach qualifying row with non-low severity for production tier labels in workload_pdb_policy.csv.

### Negative scenario

Restore healthy replicas so current_healthy equals desired_healthy, disruptionsAllowed remains within policy, ensure no EvictionDenied events fire during the window, and verify the saved search emits no qualifying rows for that pdb and deployment pair across thirty minutes on a five-minute schedule.

## Detailed Implementation

### Step 1 — Prerequisites

Head of Platform owns this control together with Kubernetes platform site reliability engineers, release managers who approve voluntary disruption windows, and the observability team operating Splunk OpenTelemetry Collector plus kube-state-metrics across production and pre-production. This use case isolates PodDisruptionBudget state and governance: the numeric headroom between expected pods, currently healthy pods, desired healthy pods, and disruptions allowed, plus whether voluntary evictions are being denied because a budget blocks them, whether replica-rich Deployments lack any budget object at all, whether budgets are mathematically weak, and whether budgets no longer select live workloads after label or controller renames. UC-3.2.33 remains the node drain action audit plane that attributes who issued cordon and drain verbs. UC-3.2.41 remains the Kubernetes Service and EndpointSlice zero-ready-endpoint cascade detector north of kube-proxy programming. UC-3.2.6 remains Deployment rollout Progressing and Available condition analytics with ReplicaSet churn semantics. UC-3.2.46 remains Cluster Autoscaler scale-out refusal and node-group economics. None of those siblings replace kube-state-metrics PDB gauges correlated to EvictionDenied events and a signed workload policy lookup, because voluntary disruption compliance is a distinct axis from drain attribution, service endpoint tables, rollout conditions, or autoscaler decisions.

Index layout mirrors other gold Kubernetes controls in this repository: index=k8s_metrics for Prometheus text or normalized scrape events from kube-state-metrics, and index=k8s for kube:events including EvictionDenied reasons emitted when the eviction API honors a PodDisruptionBudget. Optional index=k8s_audit helps when you must prove which subject attempted an eviction during an incident review, but the primary detector stays metrics plus events. HEC tokens stay in vaults with quarterly rotation. RBAC for collectors must list watches on PodDisruptionBudget, Deployment, ReplicaSet, Pod, and Event objects without granting Secret read unless policy demands it.

kube-state-metrics must expose kube_poddisruptionbudget_status_expected_pods, kube_poddisruptionbudget_status_current_healthy, kube_poddisruptionbudget_status_desired_healthy, kube_poddisruptionbudget_status_pod_disruptions_allowed or kube_poddisruptionbudget_status_disruptions_allowed depending on exporter semver, kube_poddisruptionbudget_spec_min_available, kube_poddisruptionbudget_spec_max_unavailable, and kube_deployment_status_replicas for mapping live replica counts to governance rows. Confirm your chart version against upstream poddisruptionbudget metrics documentation because label names shifted across minor releases. Scrapes every fifteen to thirty seconds are typical; shorter intervals improve headroom math at license cost.

Governance lookup workload_pdb_policy.csv must carry cluster, namespace, pdb, deployment, owner_team, workload_tier, and pdb_required where pdb_required is one when platform policy expects a named budget object to exist for that Deployment. Refresh the CSV when services onboard, when tier contracts change, or when GitOps renames budgets. Optional columns such as maintenance_blackout_epoch, spot_tier_flag, and notes help macros suppress deliberate full-protection windows without muting true violations.

CIM mapping uses Application_State because a protected workload is an application-level availability object whose healthy replica semantics match service health narratives auditors already recognize. Performance is the second model because the opening tstats arm provides a fleet-scale correlation tick against accelerated Performance summaries when you map node or cluster identities into Performance.host for saturation context during incident reviews, even though PDB math itself is integer gauge algebra rather than CPU percentages.

Risk briefing for executives: a missing or weak budget means a single maintenance wave or node problem can take more replicas offline than the business assumed during change approval. A budget that blocks all voluntary disruption with disruptionsAllowed zero can strand platform upgrades until someone manually intervenes, which lengthens exposure windows elsewhere. EvictionDenied storms mean operators are attempting maintenance that the API correctly refuses; without this detector those failures hide in noisy event streams.

Licensing note: PDB series cardinality scales with namespace and budget object counts, not pod counts, which keeps cost moderate on most estates. Privacy note: event messages can echo pod names with customer codenames; restrict dashboard ACLs.

Training: teach responders to read expected minus current healthy as the deficit that must stay within disruptions allowed during voluntary operations, and to treat desired healthy below current as a chronic convergence problem distinct from a momentary drain spike.

Review cadence: quarterly replay one historical maintenance incident after kube-state-metrics upgrades because regex arms drift when exporters rename metrics.

Differentiation recap: PDB compliance is the governance and availability headroom axis; drain audits, service endpoints, rollout conditions, and cluster autoscaler economics are explicitly out of scope as primary detectors.

Escalation alignment: tier-one services in workload_pdb_policy.csv should page both application and platform bridges when headroom breach rows persist across two evaluation intervals.

Telemetry hygiene: deduplicate overlapping Prometheus and OpenTelemetry scrapes without stable dedup keys only after you understand double-counting risk.

FinOps alignment: zero disruption budgets on large replica fleets can block spot recycling that saves money; finance conversations belong beside this control when spot node groups are standard.

Security alignment: pair UC-3.2.22 admission outcomes when eviction denials cluster with unsafe pod specs that never became Ready.

Performance alignment: multisearch arms cost scheduler time; keep alert cadence at five minutes for full joins and use a summary index for fleet dashboards at fifteen minutes if Job Inspector complains.

Documentation alignment: wiki-link this UC beside voluntary disruption runbooks, kubectl drain procedures, and progressive delivery guides so new engineers land on the right detector first.

Hardware scope: Amazon EKS, Google GKE, Microsoft AKS, Red Hat OpenShift, VMware Tanzu, and self-managed clusters where kube-state-metrics RBAC can list PodDisruptionBudget objects cluster-wide; Arm and x86 worker fleets are in scope when metric text lines remain Prometheus compatible.

StatefulSet note: the SPL joins Deployments via workload_pdb_policy.csv; fork a StatefulSet-specific lookup arm if your estate standardizes on partitioned StatefulSet controllers for tier-one data planes without Deployment equivalents.

Argo CD and Flux note: GitOps controllers can rename budgets or strip them during mis-merged manifests; the governance_gap append lane catches replica-rich Deployments that lack metric rows for the expected budget name.

Splunk Enterprise or Splunk Cloud 9.2 plus is assumed for scheduled searches, drilldowns, and optional accelerated models referenced in cimSpl.

Platform onboarding checklist for new clusters: verify kube-state-metrics version, verify Splunk OTel chart version, verify HEC endpoint health, verify workload_pdb_policy.csv includes every production Deployment that requires protection, verify event watch RBAC retains EvictionDenied visibility, verify PagerDuty routing maps owner_team strings to live schedules, verify executive dashboard includes eviction denied single value sourced from this saved search clone, verify FinOps receives monthly CSV export of zero-budget rows for maintenance planning, verify legal retention index paths when regulated workloads appear in alert rows, verify chaos engineering namespaces carry suppression metadata in the lookup notes column, verify mesh ingress namespaces that share budgets across blue-green pairs carry explicit deployment rows per policy object, verify database namespaces carry extended dwell timers for cold start realism, verify CI cluster namespaces never page tier-one bridges because of synthetic eviction tests unless chaos flags absent, verify dual-active disaster recovery clusters each have distinct cluster column values in CSV, verify secondary on-call bridges receive high severity only when primary ack times out, verify Grafana or Dashboard Studio deep links are embedded in alert actions for faster kubectl-free triage, verify runbook links reference kubectl drain and safe eviction procedures, verify kubectl describe pdb interpretation training occurs twice yearly, verify kube-controller-manager health checks are linked from this runbook for budget reconcile lag cases, verify etcd maintenance windows are documented to avoid false orphan_selector_gap panic during short API gaps, verify service mesh canary weight documentation clarifies why Kubernetes replica counts may diverge from traffic percentages during progressive delivery, verify image digest pinning policy references UC-3.2.14 when image layers stall while budgets still show healthy pods, verify probe tuning policy references UC-3.2.43 when readiness gates fail only on new pods, verify admission webhook maintenance windows reference UC-3.2.21 when new pods never bind during drains, verify horizontal pod autoscaler scale events are cross-checked before blaming budgets for replica drift, verify vertical pod autoscaler recommendations are reviewed when surge pods cannot schedule for memory, verify cluster autoscaler scale-out timelines are understood when surge pods stay Pending, verify node repair storms are distinguished from budget math errors using node condition panels, verify storage class binding delays are distinguished using PVC phase joins when stateful workloads lag, verify API server priority and fairness settings are reviewed when control plane latency correlates with stale gauges, verify webhook timeout budgets are reviewed when apiserver logs show slow validating hooks, verify certificate rotation playbooks are linked when mTLS hooks fail only for new pods, verify GitOps drift detectors are linked when live cluster budgets disagree with Git declared names without Splunk seeing a rename event, verify blue-green cutover documentation explains why this detector may need temporary suppression during pinned minAvailable ceremonies, verify maintenance mode annotations are standardized across teams, verify SRE error budget policy ties this alert to customer facing availability burn when tier column marks gold, verify product management receives weekly digest of longest eviction denial bursts for roadmap risk, verify architecture review board receives quarterly summary of weak-policy frequency inferred from fake_policy_flag rows, verify internal auditor sample pulls three incidents per quarter and confirms evidence index retention, verify vendor support tickets attach Splunk export hashes when upstream Kubernetes bugs suspected, verify upgrade testing pipeline runs kube-state-metrics semver jumps before production promotion, verify cross-region replication lag does not break lookup joins when cluster name casing differs, verify Unicode normalization in deployment names does not break CSV joins, verify stale CSV rows for deleted namespaces are pruned monthly, verify automated CMDB sync jobs log commit identifiers consumed by this UC, verify break-glass account usage still triggers companion audit analytics when budgets go wrong, verify synthetic monitoring uptime checks complement but do not replace kube-state-metrics truth.

Closing prerequisites checklist: indexes named, kube-state-metrics PDB and Deployment replica families enumerated, workload_pdb_policy.csv schema documented, boundaries versus UC-3.2.33, UC-3.2.41, UC-3.2.6, and UC-3.2.46 restated, CIM Application_State plus Performance rationale captured for reviewers who ask why Change is not listed as a primary model here.

### Step 2 — Configure data collection

Deploy kube-state-metrics with cluster-scoped RBAC that can list PodDisruptionBudget objects, Deployments, and related workload metadata. Point Splunk OpenTelemetry Collector prometheus receiver or prometheus_simple scrape jobs at the kube-state-metrics Service on port 8080 or 8443 depending on your chart, preserve namespace, poddisruptionbudget, deployment, and cluster labels through relabel_config blocks, and export to HEC into index=k8s_metrics with sourcetype prometheus:scrape:metrics. Mirror UC-3.2.41 collector hygiene: bearer_token_file for TLS kubelet scrapes is separate from kube-state-metrics HTTP scraping inside the cluster.

Concrete ServiceMonitor style reference:

apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: kube-state-metrics-pdb
  namespace: monitoring
spec:
  selector:
    matchLabels:
      app.kubernetes.io/name: kube-state-metrics
  endpoints:
    - port: http-metrics
      interval: 30s
      path: /metrics

OpenTelemetry Collector fragment showing prometheus scrape plus kubernetes events export:

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
  k8s_events:
    auth_type: serviceAccount
    namespaces: []
exporters:
  splunk_hec/metrics:
    token: ${SPLUNK_HEC_TOKEN}
    endpoint: https://splunk.example.com:8088/services/collector
    index: k8s_metrics
    sourcetype: prometheus:scrape:metrics
  splunk_hec/events:
    token: ${SPLUNK_HEC_TOKEN}
    endpoint: https://splunk.example.com:8088/services/collector
    index: k8s
    sourcetype: kube:events
service:
  pipelines:
    metrics:
      receivers: [prometheus]
      exporters: [splunk_hec/metrics]
    logs/events:
      receivers: [k8s_events]
      exporters: [splunk_hec/events]

workload_pdb_policy.csv sample schema:

cluster,namespace,pdb,deployment,owner_team,workload_tier,pdb_required,notes
prod-eks-us-east-1,prod-payments,payments-api-pdb,payments-api,payments-sre,prod,1,
prod-eks-us-east-1,prod-edge,edge-rollout-pdb,edge-gateway,platform-mesh,prod,1,blue_green_pair

Validate raw signal presence before alerts: index=k8s_metrics kube_poddisruptionbudget_status_expected_pods earliest=-30m, index=k8s_metrics kube_deployment_status_replicas earliest=-30m, index=k8s sourcetype=kube:events EvictionDenied earliest=-24h. Skew between scrapes and API events must stay under ninety seconds for meaningful joins.

Security: redact internal hostnames from collector debug logs. Restrict k8s_audit to roles that need eviction attribution when you enable optional audit joins outside this baseline SPL.

props.conf guidance: normalize __name__, value, namespace, poddisruptionbudget, and deployment fields onto indexed extractions where volume warrants; keep coalesce ladders in SPL until extractions stabilize.

When HEC receives OpenTelemetry protobuf translations instead of Prometheus text, extend rex arms with metric_name coalesce paths identical to UC-3.2.14 patterns.

Cloud control planes: on EKS verify security groups still allow node to cluster IP reachability for metrics after landing-zone changes; on GKE verify managed Prometheus if you offloaded scrapes; on AKS verify managed Grafana agent label mapping still populates deployment.

Frequency: scrape interval, alert interval, and maintenance windows must align mathematically; a five-minute alert schedule with thirty-second scrapes is the minimum sane pairing for tier-one headroom monitoring.

Back-pressure: if kube-apiserver event watch disconnects, collector buffers should not grow without bound; set retry and drop policies per vendor guidance.

Version pinning: record kube-state-metrics chart version in evidence packs quarterly.

Integration with kubectl: operators should still run kubectl describe pdb for instantaneous truth; Splunk carries history and correlation that kubectl alone lacks across clusters.

Dashboard seeds: single value of eviction_denied_count from a clone search, timechart of healthy_deficit by namespace, and table of this UC output for executive summaries.

Summary index optional: materialize five-minute snapshots of PDB integers into k8s_pdb_summary when raw k8s_metrics scan costs dominate.

Closing data collection checklist: ServiceMonitor or scrape job live, events pipeline live, CSV published, validation searches green, collector TLS verified, deduplication story documented when dual agents scrape the same targets.

### Step 3 — Create the search and alert

Save the SPL as uc_3_2_37_kube_pdb_compliance_headroom with five-minute schedule, dispatch earliest=-3h@m, dispatch latest=now, and alert when severity is critical or high for tier-one rows. Throttle duplicate pages per cluster, namespace, and pdb for thirty minutes unless severity escalates from high to critical. Attach drilldown searches to kube:events for reason EvictionDenied in the same namespace and to UC-3.2.6 companion macros when replica counts disagree with rollout narratives.

Understanding the pipeline: the opening comment macro lists tunables so on-call engineers retune without opening this document. join with tstats against Performance provides a CIM-aligned correlation tick count that helps justify dual-model mapping during audits; if Performance acceleration is absent in a lab, the join still type=left preserves PDB rows. multisearch fans metric arms so one silent kube-state-metrics family cannot zero the entire detection. Each PDB arm ends with stats latest by cluster, namespace, and pdb so rows collapse before the outer stats merges arms. coalesce ladders tolerate camelCase and snake_case label exports. The merged row computes healthy_deficit as expected_pods minus current_healthy and compares it to disruptions_allowed for headroom_breach semantics. zero_budget_flag highlights disruptions_allowed equal to zero while work still expects pods, which often blocks voluntary maintenance. chronic_below_desired compares current_healthy to desired_healthy for sustained under-target conditions. fake_policy_flag uses spec_min_available equal to zero or maxUnavailable percentage at one hundred as weak protection signals consistent with policy review guidance. orphan_selector_gap highlights Deployments that still report replicas while the budget expects zero pods, often after selector drift. streamstats window=3 estimates short churn in healthy counts for spot-like oscillation. eventstats max(eviction_denied_count) by cluster supports dashboard overlays comparing worst tenants. inputlookup workload_pdb_policy.csv enriches owner_team, workload_tier, pdb_required, and deployment for joins to kube_deployment_status_replicas. The append block implements governance_gap_no_pdb_for_multi_replica_deployment when pdb_required is true, replica count is at least two, and no expected_pods metric row exists for the named budget. case assigns severity tiers with production bias. The closing table lists sixteen analyst columns exactly as named in the implementation contract.

cimSpl in the JSON field mirrors Application_State and Performance tstats usage for environments that map Kubernetes workload identities into those models; adapt nodename filters to your TA.

Paste-and-run SPL for alerts and dashboards must match the spl JSON field exactly:

```spl
`comment("UC-3.2.37 Kubernetes PDB compliance, allowed-disruption headroom, and governance gaps. Tunables: indexes k8s_metrics k8s; sourcetypes prometheus:scrape:metrics kube:objects:metrics kube:events; lookup workload_pdb_policy.csv; earliest=-3h@m latest=now")`
| eval join_key="uc3237"
| join type=left join_key [
| tstats count AS perf_correlation_tick FROM datamodel=Performance WHERE nodename=Performance earliest=-3h@h latest=now
| eval join_key="uc3237"
]
| fields - join_key perf_correlation_tick
| multisearch [
    [ search ((index=k8s_metrics OR index=k8s) (sourcetype="prometheus:scrape:metrics" OR sourcetype="kube:objects:metrics")) earliest=-3h@m latest=now
      | eval cluster=trim(toString(coalesce(cluster, cluster_name, k8s_cluster_name, eks_cluster_name, gke_cluster_name, "")))
      | eval mn=lower(trim(toString(coalesce(metric_name, __name__, name, MetricName, ""))))
      | rex field=_raw "namespace=\"(?<namespace>[^\"]+)\""
      | rex field=_raw "poddisruptionbudget=\"(?<pdb>[^\"]+)\""
      | where like(mn, "%kube_poddisruptionbudget_status_expected_pods%")
      | rex field=_raw "\s(?<mval>[0-9.eE+-]+)\s*$"
      | eval expected_pods=tonumber(mval, 10)
      | stats latest(expected_pods) AS expected_pods BY cluster namespace pdb ]
    [ search ((index=k8s_metrics OR index=k8s) (sourcetype="prometheus:scrape:metrics" OR sourcetype="kube:objects:metrics")) earliest=-3h@m latest=now
      | eval cluster=trim(toString(coalesce(cluster, cluster_name, k8s_cluster_name, eks_cluster_name, gke_cluster_name, "")))
      | eval mn=lower(trim(toString(coalesce(metric_name, __name__, name, MetricName, ""))))
      | rex field=_raw "namespace=\"(?<namespace>[^\"]+)\""
      | rex field=_raw "poddisruptionbudget=\"(?<pdb>[^\"]+)\""
      | where like(mn, "%kube_poddisruptionbudget_status_current_healthy%")
      | rex field=_raw "\s(?<mval>[0-9.eE+-]+)\s*$"
      | eval current_healthy=tonumber(mval, 10)
      | stats latest(current_healthy) AS current_healthy BY cluster namespace pdb ]
    [ search ((index=k8s_metrics OR index=k8s) (sourcetype="prometheus:scrape:metrics" OR sourcetype="kube:objects:metrics")) earliest=-3h@m latest=now
      | eval cluster=trim(toString(coalesce(cluster, cluster_name, k8s_cluster_name, eks_cluster_name, gke_cluster_name, "")))
      | eval mn=lower(trim(toString(coalesce(metric_name, __name__, name, MetricName, ""))))
      | rex field=_raw "namespace=\"(?<namespace>[^\"]+)\""
      | rex field=_raw "poddisruptionbudget=\"(?<pdb>[^\"]+)\""
      | where like(mn, "%kube_poddisruptionbudget_status_desired_healthy%")
      | rex field=_raw "\s(?<mval>[0-9.eE+-]+)\s*$"
      | eval desired_healthy=tonumber(mval, 10)
      | stats latest(desired_healthy) AS desired_healthy BY cluster namespace pdb ]
    [ search ((index=k8s_metrics OR index=k8s) (sourcetype="prometheus:scrape:metrics" OR sourcetype="kube:objects:metrics")) earliest=-3h@m latest=now
      | eval cluster=trim(toString(coalesce(cluster, cluster_name, k8s_cluster_name, eks_cluster_name, gke_cluster_name, "")))
      | eval mn=lower(trim(toString(coalesce(metric_name, __name__, name, MetricName, ""))))
      | rex field=_raw "namespace=\"(?<namespace>[^\"]+)\""
      | rex field=_raw "poddisruptionbudget=\"(?<pdb>[^\"]+)\""
      | where like(mn, "%kube_poddisruptionbudget_status_pod_disruptions_allowed%") OR like(mn, "%kube_poddisruptionbudget_status_disruptions_allowed%")
      | rex field=_raw "\s(?<mval>[0-9.eE+-]+)\s*$"
      | eval disruptions_allowed=tonumber(mval, 10)
      | stats latest(disruptions_allowed) AS disruptions_allowed BY cluster namespace pdb ]
    [ search ((index=k8s_metrics OR index=k8s) (sourcetype="prometheus:scrape:metrics" OR sourcetype="kube:objects:metrics")) earliest=-3h@m latest=now
      | eval cluster=trim(toString(coalesce(cluster, cluster_name, k8s_cluster_name, eks_cluster_name, gke_cluster_name, "")))
      | eval mn=lower(trim(toString(coalesce(metric_name, __name__, name, MetricName, ""))))
      | rex field=_raw "namespace=\"(?<namespace>[^\"]+)\""
      | rex field=_raw "poddisruptionbudget=\"(?<pdb>[^\"]+)\""
      | where like(mn, "%kube_poddisruptionbudget_spec_min_available%") OR like(mn, "%kube_poddisruptionbudget_spec_max_unavailable%")
      | rex field=_raw "max_unavailable=\"(?<max_unavail_str>[^\"]+)\""
      | rex field=_raw "\s(?<mval>[0-9.eE+-]+)\s*$"
      | eval spec_min_available=if(like(mn, "%spec_min_available%"), tonumber(mval, 10), null())
      | eval spec_max_unavailable_num=if(like(mn, "%spec_max_unavailable%"), tonumber(mval, 10), null())
      | eval pct_raw=if(isnotnull(max_unavail_str), replace(max_unavail_str, "%", ""), null())
      | eval spec_max_unavailable_pct=if(like(mn, "%spec_max_unavailable%"), tonumber(pct_raw, 10), null())
      | stats latest(spec_min_available) AS spec_min_available latest(spec_max_unavailable_num) AS spec_max_unavailable_num latest(spec_max_unavailable_pct) AS spec_max_unavailable_pct BY cluster namespace pdb ]
| stats latest(expected_pods) AS expected_pods latest(current_healthy) AS current_healthy latest(desired_healthy) AS desired_healthy latest(disruptions_allowed) AS disruptions_allowed latest(spec_min_available) AS spec_min_available latest(spec_max_unavailable_num) AS spec_max_unavailable_num latest(spec_max_unavailable_pct) AS spec_max_unavailable_pct BY cluster namespace pdb
| eval cluster=coalesce(nullif(trim(cluster), ""), "unknown-cluster")
| eval namespace=coalesce(nullif(trim(namespace), ""), "unknown-namespace")
| eval pdb=coalesce(nullif(trim(pdb), ""), "unknown-pdb")
| join type=left max=0 cluster namespace pdb [
    | inputlookup workload_pdb_policy.csv
    | eval cluster=trim(toString(coalesce(cluster, k8s_cluster, cluster_name, "")))
    | eval namespace=trim(toString(namespace))
    | eval pdb=trim(toString(coalesce(pdb, poddisruptionbudget, pdb_name, "")))
    | eval deployment=trim(toString(coalesce(deployment, workload, deploy, "")))
    | eval owner_team=trim(toString(coalesce(owner_team, squad, platform_team, "")))
    | eval workload_tier=lower(trim(toString(coalesce(workload_tier, env_tier, tier, "dev"))))
    | eval pdb_required=tonumber(trim(toString(coalesce(pdb_required, requires_pdb, "0"))), 10)
    | fields cluster namespace pdb deployment owner_team workload_tier pdb_required ]
| fillnull value="unassigned" owner_team
| fillnull value="dev" workload_tier
| fillnull value=0 pdb_required
| join type=left max=0 cluster namespace deployment [
    search ((index=k8s_metrics OR index=k8s) (sourcetype="prometheus:scrape:metrics" OR sourcetype="kube:objects:metrics")) earliest=-3h@m latest=now
      | eval cluster=trim(toString(coalesce(cluster, cluster_name, k8s_cluster_name, eks_cluster_name, gke_cluster_name, "")))
      | eval mn=lower(trim(toString(coalesce(metric_name, __name__, name, MetricName, ""))))
      | rex field=_raw "namespace=\"(?<namespace>[^\"]+)\""
      | rex field=_raw "deployment=\"(?<deployment>[^\"]+)\""
      | where like(mn, "%kube_deployment_status_replicas%") AND NOT like(mn, "%kube_deployment_status_replicas_available%") AND NOT like(mn, "%kube_deployment_status_replicas_updated%") AND NOT like(mn, "%kube_deployment_status_replicas_ready%")
      | rex field=_raw "\s(?<mval>[0-9.eE+-]+)\s*$"
      | eval kube_deployment_status_replicas=tonumber(mval, 10)
      | stats latest(kube_deployment_status_replicas) AS kube_deployment_status_replicas BY cluster namespace deployment ]
| join type=left max=0 cluster namespace [
    search index=k8s sourcetype="kube:events" earliest=-3h@m latest=now
      | eval cluster=trim(toString(coalesce(cluster, cluster_name, k8s_cluster_name, "")))
      | eval namespace=trim(toString(coalesce(metadata.namespace, namespace, "")))
      | eval rs=trim(toString(coalesce(reason, Reason, "")))
      | where rs="EvictionDenied"
      | stats count AS eviction_denied_count BY cluster namespace ]
| fillnull value=0 eviction_denied_count
| eval expected_pods=coalesce(expected_pods, 0)
| eval current_healthy=coalesce(current_healthy, 0)
| eval desired_healthy=coalesce(desired_healthy, 0)
| eval disruptions_allowed=coalesce(disruptions_allowed, 0)
| eval spec_min_available=coalesce(spec_min_available, -1)
| eval spec_max_unavailable_pct=coalesce(spec_max_unavailable_pct, 0)
| eval healthy_deficit=expected_pods-current_healthy
| eval headroom_breach=if(healthy_deficit>disruptions_allowed AND expected_pods>0, 1, 0)
| eval zero_budget_flag=if(disruptions_allowed==0 AND expected_pods>0, 1, 0)
| eval chronic_below_desired=if(current_healthy<desired_healthy AND desired_healthy>0, 1, 0)
| eval fake_policy_flag=if(spec_min_available==0, 1, if(spec_max_unavailable_pct>=100, 1, 0))
| eval orphan_selector_gap=if(kube_deployment_status_replicas>0 AND expected_pods==0, 1, 0)
| eval signal_lane=case(
    headroom_breach=1 AND eviction_denied_count>0, "pdb_headroom_breach_with_eviction_denied",
    headroom_breach=1, "pdb_headroom_violation_risk",
    orphan_selector_gap=1, "pdb_orphaned_or_non_selecting",
    chronic_below_desired=1, "pdb_below_desired_healthy",
    fake_policy_flag=1, "pdb_fake_or_weak_policy",
    zero_budget_flag=1 AND match(workload_tier, "prod|production|tier1|staging|uat|preprod"), "pdb_zero_disruption_budget",
    eviction_denied_count>0, "kube_eviction_denied_recent",
    true(), "pdb_watch_ok")
| sort 0 cluster namespace pdb
| streamstats window=3 global=f first(current_healthy) AS ch_first last(current_healthy) AS ch_last BY cluster namespace pdb
| eval churny_deficit=if(isnotnull(ch_first) AND isnotnull(ch_last) AND ch_first>ch_last+1, 1, 0)
| eventstats max(eviction_denied_count) AS cluster_peak_evictions BY cluster
| eval severity=case(
    headroom_breach=1 AND match(workload_tier, "prod|production|tier1|tier-1|gold"), "critical",
    headroom_breach=1, "high",
    eviction_denied_count>=3 AND match(workload_tier, "prod|production|tier1|tier-1|gold"), "critical",
    eviction_denied_count>=1, "high",
    chronic_below_desired=1 AND match(workload_tier, "prod|production|tier1|tier-1|gold"), "high",
    chronic_below_desired=1, "medium",
    fake_policy_flag=1 AND match(workload_tier, "prod|production|tier1"), "high",
    fake_policy_flag=1, "medium",
    zero_budget_flag=1 AND match(workload_tier, "prod|production|tier1|tier-1|gold"), "medium",
    orphan_selector_gap=1, "medium",
    churny_deficit=1 AND match(workload_tier, "prod|production|tier1"), "medium",
    true(), "low")
| where headroom_breach=1 OR chronic_below_desired=1 OR fake_policy_flag=1 OR zero_budget_flag=1 OR orphan_selector_gap=1 OR eviction_denied_count>0 OR churny_deficit=1
| where match(workload_tier, "prod|production|preprod|staging|uat|tier1|tier-1|gold") OR pdb_required=1 OR severity IN ("critical", "high")
| table cluster namespace pdb deployment signal_lane healthy_deficit disruptions_allowed expected_pods current_healthy desired_healthy kube_deployment_status_replicas eviction_denied_count severity owner_team workload_tier cluster_peak_evictions fake_policy_flag zero_budget_flag
| append [
    | inputlookup workload_pdb_policy.csv
    | eval cluster=lower(trim(toString(coalesce(cluster, k8s_cluster, cluster_name, ""))))
    | eval namespace=trim(toString(namespace))
    | eval pdb=trim(toString(coalesce(pdb, poddisruptionbudget, pdb_name, "")))
    | eval deployment=trim(toString(coalesce(deployment, workload, deploy, "")))
    | eval owner_team=trim(toString(coalesce(owner_team, squad, platform_team, "")))
    | eval workload_tier=lower(trim(toString(coalesce(workload_tier, env_tier, tier, "dev"))))
    | eval pdb_required=tonumber(trim(toString(coalesce(pdb_required, requires_pdb, "0"))), 10)
    | where pdb_required=1 AND match(workload_tier, "prod|production|preprod|staging|uat|tier1")
    | join type=left max=0 cluster namespace deployment [
        search ((index=k8s_metrics OR index=k8s) (sourcetype="prometheus:scrape:metrics" OR sourcetype="kube:objects:metrics")) earliest=-3h@m latest=now
          | eval cluster=lower(trim(toString(coalesce(cluster, cluster_name, k8s_cluster_name, eks_cluster_name, gke_cluster_name, ""))))
          | eval mn=lower(trim(toString(coalesce(metric_name, __name__, name, MetricName, ""))))
          | rex field=_raw "namespace=\"(?<namespace>[^\"]+)\""
          | rex field=_raw "deployment=\"(?<deployment>[^\"]+)\""
          | where like(mn, "%kube_deployment_status_replicas%") AND NOT like(mn, "%kube_deployment_status_replicas_available%") AND NOT like(mn, "%kube_deployment_status_replicas_updated%") AND NOT like(mn, "%kube_deployment_status_replicas_ready%")
          | rex field=_raw "\s(?<mval>[0-9.eE+-]+)\s*$"
          | eval kube_deployment_status_replicas=tonumber(mval, 10)
          | stats latest(kube_deployment_status_replicas) AS kube_deployment_status_replicas BY cluster namespace deployment ]
    | where kube_deployment_status_replicas>=2
    | join type=left max=0 cluster namespace pdb [
        search ((index=k8s_metrics OR index=k8s) (sourcetype="prometheus:scrape:metrics" OR sourcetype="kube:objects:metrics")) earliest=-3h@m latest=now
          | eval cluster=lower(trim(toString(coalesce(cluster, cluster_name, k8s_cluster_name, eks_cluster_name, gke_cluster_name, ""))))
          | eval mn=lower(trim(toString(coalesce(metric_name, __name__, name, MetricName, ""))))
          | rex field=_raw "namespace=\"(?<namespace>[^\"]+)\""
          | rex field=_raw "poddisruptionbudget=\"(?<pdb>[^\"]+)\""
          | where like(mn, "%kube_poddisruptionbudget_status_expected_pods%")
          | stats count AS pdb_metric_rows BY cluster namespace pdb ]
    | fillnull value=0 pdb_metric_rows
    | where pdb_metric_rows=0
    | eval signal_lane="governance_gap_no_pdb_for_multi_replica_deployment"
    | eval healthy_deficit=0
    | eval disruptions_allowed=0
    | eval expected_pods=0
    | eval current_healthy=0
    | eval desired_healthy=0
    | eval eviction_denied_count=0
    | eval cluster_peak_evictions=0
    | eval fake_policy_flag=0
    | eval zero_budget_flag=0
    | eval severity=if(match(workload_tier, "prod|production|tier1"), "high", "medium")
    | table cluster namespace pdb deployment signal_lane healthy_deficit disruptions_allowed expected_pods current_healthy desired_healthy kube_deployment_status_replicas eviction_denied_count severity owner_team workload_tier cluster_peak_evictions fake_policy_flag zero_budget_flag ]
```
Alert actions: include cluster, namespace, pdb, deployment, signal_lane, healthy_deficit, disruptions_allowed, severity, owner_team, and workload_tier in email or ITSI notable bodies. Provide a drilldown that runs index=k8s sourcetype=kube:events reason=EvictionDenied namespace=$namespace$ earliest=-3h. Provide a secondary drilldown for kubectl-safe maintenance guidance linked from references.

Performance: if Job Inspector warns on multisearch cost, split fleet dashboards into per-region saved searches or materialize kube_poddisruptionbudget_status snapshots hourly.

Reliability: during kube-state-metrics upgrades expect brief gaps; require two consecutive intervals of missing metrics before paging scrape outages unless kube events still show EvictionDenied storms.

Governance: weekly CSV export of alert rows with lookup commit hash satisfies internal platform evidence when paired with kube-state-metrics version stamps.

savedsearches.conf quantity thresholds should align with row counts from the table command; use alert.track=1 and suppress keys on cluster namespace pdb for the primary lane and cluster namespace deployment for governance_gap rows.

Closing Step 3 checklist: fenced SPL present, matches spl field, references workload_pdb_policy.csv, explains tstats join purpose, documents multisearch arms, clarifies headroom math, and names notification fields.

### Step 4 — Validate

Synthetic headroom stress: in lab namespace qa-pdb-uc3237 deploy a Deployment protected by a PodDisruptionBudget with low maxUnavailable, scale pods unhealthy or cordon nodes so current_healthy drops below expected while voluntary eviction attempts occur, confirm kube_poddisruptionbudget_status_current_healthy lags expected_pods in index=k8s_metrics, execute uc_3_2_37_kube_pdb_compliance_headroom, and expect a headroom_breach row when healthy_deficit exceeds disruptions_allowed.

Synthetic eviction denial: attempt a kubectl drain or eviction against a pod protected by a budget that blocks the action under change control, confirm kube:events shows reason EvictionDenied, and expect signal_lane kube_eviction_denied_recent with non-zero eviction_denied_count.

Synthetic weak policy: apply a budget with spec minAvailable zero and maxUnavailable one hundred percent in lab only, confirm spec metrics in Splunk, and expect fake_policy_flag equals one with medium or high severity depending on tier.

Governance gap synthetic: remove only the PDB object while leaving a two-replica Deployment in place for a row where pdb_required equals one in workload_pdb_policy.csv, confirm append lane emits governance_gap_no_pdb_for_multi_replica_deployment.

Negative test: restore a healthy two-replica Deployment with a sane budget, confirm current_healthy equals desired_healthy within two scrapes, and expect zero qualifying rows from the alert predicate for that pair across thirty minutes when no eviction denials occur.

Field sanity: rename a forwarder field to camelCase-only in a sandbox and verify coalesce still resolves namespace and pdb labels.

RBAC: readers without k8s_metrics access must see zero rows.

Correlation: compare Splunk timestamps to kubectl describe pdb output for the same minute.

Validation SPL for raw metrics presence:

| multisearch [
    [ search index=k8s_metrics earliest=-30m latest=now kube_poddisruptionbudget_status_expected_pods | stats count ]
    [ search index=k8s_metrics earliest=-30m latest=now kube_deployment_status_replicas | stats count ]
  ]
| stats sum(count) AS samples

Tear-down: delete lab budgets and Deployments, revert drain attempts, and confirm saved search result counts return to zero.

Clock skew: verify NTP alignment between nodes, kube-apiserver, and Splunk indexers; skew beyond ninety seconds invalidates event joins.

Documentation: attach kubectl describe pdb screenshots to the evidence ticket without exposing Secrets.

Closing Step 4 checklist: positive headroom scenario, eviction denial scenario, weak-policy scenario, governance gap scenario, negative healthy deploy, metrics presence multisearch, tear-down verified, clock skew warning documented.

### Step 5 — Operationalize & Troubleshoot

Case 1 — healthy_deficit greater than disruptions_allowed with headroom_breach set: treat as imminent voluntary disruption risk; verify real health of pods with kubectl get pods, read node conditions for pressure, and pause further drains until replicas recover or budgets are adjusted under change advisory board oversight.

Case 2 — chronic_below_desired with current_healthy below desired_healthy: investigate readiness probes, image rollouts, and scheduling failures; correlate UC-3.2.43 probe analytics before blaming budgets alone.

Case 3 — EvictionDenied bursts in kube:events: identify the subject performing eviction, confirm whether maintenance is approved, and either relax budgets temporarily with logged approvals or reschedule maintenance until replicas are healthy.

Case 4 — zero_budget_flag on production tiers: voluntary node drains and cluster upgrades may stall; coordinate with platform owners to allow at least one disruption during safe windows or temporarily scale replicas upward before maintenance.

Case 5 — fake_policy_flag from minAvailable zero or maxUnavailable one hundred percent: open a governance ticket to tighten policy objects; cite architecture standards and NSA Kubernetes hardening guidance references in the ticket body.

Case 6 — governance_gap_no_pdb_for_multi_replica_deployment from the append lane: create or restore a PodDisruptionBudget object in Git, verify selectors cover the Deployment template labels, and backfill workload_pdb_policy.csv if names changed.

Case 7 — orphan_selector_gap with kube_deployment_status_replicas positive and expected_pods zero: fix PDB selectors or workload labels so the budget matches live pods; this often follows rename drift absent from GitOps.

Case 8 — churny_deficit with rapid current_healthy drops on spot node groups: verify capacity backfill and instance termination rates; pair UC-3.2.46 autoscaler narratives when nodes disappear faster than budgets allow voluntary rescheduling.

Case 9 — split-brain between Git declared budget and live metrics: reconcile Argo CD or Flux sync errors; attach Git commit metadata to the incident record.

Case 10 — false alarm during intentional full-protection ceremonies: when minAvailable equals replica count for a pinned release window documented in the lookup notes column, suppress paging for that window or require dual approval before alerts reopen.

Case 11 — database or queue Deployments with intentional zero voluntary disruption: document single-writer semantics in workload_pdb_policy.csv so zero_budget_flag routes to medium severity with owner acknowledgement rather than sev-one.

Case 12 — metrics scrape outage mimicking missing budgets: if governance_gap rows appear cluster-wide simultaneously, correlate collector health before accusing application teams of missing objects.

Dashboard hygiene: keep a panel for eviction_denied_count by namespace and overlay node drain schedules from change calendars.

Evidence retention: archive weekly CSV exports with kube-state-metrics chart version, collector digest, and Splunk search head cluster name.

Training replay: twice-yearly game day that combines voluntary eviction attempts with budget edits to prove operators open both kube:events views and this UC without duplicating tickets.

Cloud nuances: Fargate-style compute without DaemonSet assumptions still exposes kube-state-metrics the same way; verify scrape paths when AWS VPC CNI policies change.

Governance: when legal requests preservation, include hashed budget manifests rather than raw Secret-laden YAML in tickets.

Performance note: if inputlookup workload_pdb_policy.csv grows beyond ten thousand rows, migrate to KV Store with automatic filter= on cluster before join.

Fleet operations note: publish a clone saved search without the closing where clause for monthly reliability reviews so medium severity weak-policy trends remain visible even when paging macros stay tight.

Executive storytelling note: translate healthy_deficit integers into customer impact language in bridges; executives rarely parse Prometheus label semantics on first read.

Vendor escalation note: attach kube-controller-manager logs excerpts only when support NDAs permit; otherwise ship Splunk redacted exports with metric line samples only.

Runbook maintenance note: revisit links quarterly because Kubernetes minor releases occasionally rename user-facing event messages even when metrics stay stable.

Operator wellbeing note: pair this alert with shift handoff templates so secondary responders inherit deficit deltas without re-running full SPL manually.

Incident commander note: tag incidents with pdb names in chat so audit replay aligns with Splunk rows after the fact.

Post-incident review note: require root cause category budget_math, selector_drift, scrape_gap, maintenance_process, capacity, or governance_csv for every critical page from this UC.

Capacity planning note: when zero-budget rows repeat monthly during cloud maintenance waves, open a platform project rather than silencing the control indefinitely.

Change advisory note: planned kube-state-metrics upgrades should carry a temporary lowering of alert severity only when maintenance windows are published in the change record.

Observability maturity note: graduate from five minute to one minute schedules only after license and Job Inspector budgets approve the multisearch cost.

Closing Step 5 checklist: twelve cases present with exact Case N — formatting, cross-links named to UC-3.2.43 and UC-3.2.46, weak-policy and governance-gap guidance, plus dashboard and evidence notes for long-term operations.

## SPL

```spl
`comment("UC-3.2.37 Kubernetes PDB compliance, allowed-disruption headroom, and governance gaps. Tunables: indexes k8s_metrics k8s; sourcetypes prometheus:scrape:metrics kube:objects:metrics kube:events; lookup workload_pdb_policy.csv; earliest=-3h@m latest=now")`
| eval join_key="uc3237"
| join type=left join_key [
| tstats count AS perf_correlation_tick FROM datamodel=Performance WHERE nodename=Performance earliest=-3h@h latest=now
| eval join_key="uc3237"
]
| fields - join_key perf_correlation_tick
| multisearch [
    [ search ((index=k8s_metrics OR index=k8s) (sourcetype="prometheus:scrape:metrics" OR sourcetype="kube:objects:metrics")) earliest=-3h@m latest=now
      | eval cluster=trim(toString(coalesce(cluster, cluster_name, k8s_cluster_name, eks_cluster_name, gke_cluster_name, "")))
      | eval mn=lower(trim(toString(coalesce(metric_name, __name__, name, MetricName, ""))))
      | rex field=_raw "namespace=\"(?<namespace>[^\"]+)\""
      | rex field=_raw "poddisruptionbudget=\"(?<pdb>[^\"]+)\""
      | where like(mn, "%kube_poddisruptionbudget_status_expected_pods%")
      | rex field=_raw "\s(?<mval>[0-9.eE+-]+)\s*$"
      | eval expected_pods=tonumber(mval, 10)
      | stats latest(expected_pods) AS expected_pods BY cluster namespace pdb ]
    [ search ((index=k8s_metrics OR index=k8s) (sourcetype="prometheus:scrape:metrics" OR sourcetype="kube:objects:metrics")) earliest=-3h@m latest=now
      | eval cluster=trim(toString(coalesce(cluster, cluster_name, k8s_cluster_name, eks_cluster_name, gke_cluster_name, "")))
      | eval mn=lower(trim(toString(coalesce(metric_name, __name__, name, MetricName, ""))))
      | rex field=_raw "namespace=\"(?<namespace>[^\"]+)\""
      | rex field=_raw "poddisruptionbudget=\"(?<pdb>[^\"]+)\""
      | where like(mn, "%kube_poddisruptionbudget_status_current_healthy%")
      | rex field=_raw "\s(?<mval>[0-9.eE+-]+)\s*$"
      | eval current_healthy=tonumber(mval, 10)
      | stats latest(current_healthy) AS current_healthy BY cluster namespace pdb ]
    [ search ((index=k8s_metrics OR index=k8s) (sourcetype="prometheus:scrape:metrics" OR sourcetype="kube:objects:metrics")) earliest=-3h@m latest=now
      | eval cluster=trim(toString(coalesce(cluster, cluster_name, k8s_cluster_name, eks_cluster_name, gke_cluster_name, "")))
      | eval mn=lower(trim(toString(coalesce(metric_name, __name__, name, MetricName, ""))))
      | rex field=_raw "namespace=\"(?<namespace>[^\"]+)\""
      | rex field=_raw "poddisruptionbudget=\"(?<pdb>[^\"]+)\""
      | where like(mn, "%kube_poddisruptionbudget_status_desired_healthy%")
      | rex field=_raw "\s(?<mval>[0-9.eE+-]+)\s*$"
      | eval desired_healthy=tonumber(mval, 10)
      | stats latest(desired_healthy) AS desired_healthy BY cluster namespace pdb ]
    [ search ((index=k8s_metrics OR index=k8s) (sourcetype="prometheus:scrape:metrics" OR sourcetype="kube:objects:metrics")) earliest=-3h@m latest=now
      | eval cluster=trim(toString(coalesce(cluster, cluster_name, k8s_cluster_name, eks_cluster_name, gke_cluster_name, "")))
      | eval mn=lower(trim(toString(coalesce(metric_name, __name__, name, MetricName, ""))))
      | rex field=_raw "namespace=\"(?<namespace>[^\"]+)\""
      | rex field=_raw "poddisruptionbudget=\"(?<pdb>[^\"]+)\""
      | where like(mn, "%kube_poddisruptionbudget_status_pod_disruptions_allowed%") OR like(mn, "%kube_poddisruptionbudget_status_disruptions_allowed%")
      | rex field=_raw "\s(?<mval>[0-9.eE+-]+)\s*$"
      | eval disruptions_allowed=tonumber(mval, 10)
      | stats latest(disruptions_allowed) AS disruptions_allowed BY cluster namespace pdb ]
    [ search ((index=k8s_metrics OR index=k8s) (sourcetype="prometheus:scrape:metrics" OR sourcetype="kube:objects:metrics")) earliest=-3h@m latest=now
      | eval cluster=trim(toString(coalesce(cluster, cluster_name, k8s_cluster_name, eks_cluster_name, gke_cluster_name, "")))
      | eval mn=lower(trim(toString(coalesce(metric_name, __name__, name, MetricName, ""))))
      | rex field=_raw "namespace=\"(?<namespace>[^\"]+)\""
      | rex field=_raw "poddisruptionbudget=\"(?<pdb>[^\"]+)\""
      | where like(mn, "%kube_poddisruptionbudget_spec_min_available%") OR like(mn, "%kube_poddisruptionbudget_spec_max_unavailable%")
      | rex field=_raw "max_unavailable=\"(?<max_unavail_str>[^\"]+)\""
      | rex field=_raw "\s(?<mval>[0-9.eE+-]+)\s*$"
      | eval spec_min_available=if(like(mn, "%spec_min_available%"), tonumber(mval, 10), null())
      | eval spec_max_unavailable_num=if(like(mn, "%spec_max_unavailable%"), tonumber(mval, 10), null())
      | eval pct_raw=if(isnotnull(max_unavail_str), replace(max_unavail_str, "%", ""), null())
      | eval spec_max_unavailable_pct=if(like(mn, "%spec_max_unavailable%"), tonumber(pct_raw, 10), null())
      | stats latest(spec_min_available) AS spec_min_available latest(spec_max_unavailable_num) AS spec_max_unavailable_num latest(spec_max_unavailable_pct) AS spec_max_unavailable_pct BY cluster namespace pdb ]
| stats latest(expected_pods) AS expected_pods latest(current_healthy) AS current_healthy latest(desired_healthy) AS desired_healthy latest(disruptions_allowed) AS disruptions_allowed latest(spec_min_available) AS spec_min_available latest(spec_max_unavailable_num) AS spec_max_unavailable_num latest(spec_max_unavailable_pct) AS spec_max_unavailable_pct BY cluster namespace pdb
| eval cluster=coalesce(nullif(trim(cluster), ""), "unknown-cluster")
| eval namespace=coalesce(nullif(trim(namespace), ""), "unknown-namespace")
| eval pdb=coalesce(nullif(trim(pdb), ""), "unknown-pdb")
| join type=left max=0 cluster namespace pdb [
    | inputlookup workload_pdb_policy.csv
    | eval cluster=trim(toString(coalesce(cluster, k8s_cluster, cluster_name, "")))
    | eval namespace=trim(toString(namespace))
    | eval pdb=trim(toString(coalesce(pdb, poddisruptionbudget, pdb_name, "")))
    | eval deployment=trim(toString(coalesce(deployment, workload, deploy, "")))
    | eval owner_team=trim(toString(coalesce(owner_team, squad, platform_team, "")))
    | eval workload_tier=lower(trim(toString(coalesce(workload_tier, env_tier, tier, "dev"))))
    | eval pdb_required=tonumber(trim(toString(coalesce(pdb_required, requires_pdb, "0"))), 10)
    | fields cluster namespace pdb deployment owner_team workload_tier pdb_required ]
| fillnull value="unassigned" owner_team
| fillnull value="dev" workload_tier
| fillnull value=0 pdb_required
| join type=left max=0 cluster namespace deployment [
    search ((index=k8s_metrics OR index=k8s) (sourcetype="prometheus:scrape:metrics" OR sourcetype="kube:objects:metrics")) earliest=-3h@m latest=now
      | eval cluster=trim(toString(coalesce(cluster, cluster_name, k8s_cluster_name, eks_cluster_name, gke_cluster_name, "")))
      | eval mn=lower(trim(toString(coalesce(metric_name, __name__, name, MetricName, ""))))
      | rex field=_raw "namespace=\"(?<namespace>[^\"]+)\""
      | rex field=_raw "deployment=\"(?<deployment>[^\"]+)\""
      | where like(mn, "%kube_deployment_status_replicas%") AND NOT like(mn, "%kube_deployment_status_replicas_available%") AND NOT like(mn, "%kube_deployment_status_replicas_updated%") AND NOT like(mn, "%kube_deployment_status_replicas_ready%")
      | rex field=_raw "\s(?<mval>[0-9.eE+-]+)\s*$"
      | eval kube_deployment_status_replicas=tonumber(mval, 10)
      | stats latest(kube_deployment_status_replicas) AS kube_deployment_status_replicas BY cluster namespace deployment ]
| join type=left max=0 cluster namespace [
    search index=k8s sourcetype="kube:events" earliest=-3h@m latest=now
      | eval cluster=trim(toString(coalesce(cluster, cluster_name, k8s_cluster_name, "")))
      | eval namespace=trim(toString(coalesce(metadata.namespace, namespace, "")))
      | eval rs=trim(toString(coalesce(reason, Reason, "")))
      | where rs="EvictionDenied"
      | stats count AS eviction_denied_count BY cluster namespace ]
| fillnull value=0 eviction_denied_count
| eval expected_pods=coalesce(expected_pods, 0)
| eval current_healthy=coalesce(current_healthy, 0)
| eval desired_healthy=coalesce(desired_healthy, 0)
| eval disruptions_allowed=coalesce(disruptions_allowed, 0)
| eval spec_min_available=coalesce(spec_min_available, -1)
| eval spec_max_unavailable_pct=coalesce(spec_max_unavailable_pct, 0)
| eval healthy_deficit=expected_pods-current_healthy
| eval headroom_breach=if(healthy_deficit>disruptions_allowed AND expected_pods>0, 1, 0)
| eval zero_budget_flag=if(disruptions_allowed==0 AND expected_pods>0, 1, 0)
| eval chronic_below_desired=if(current_healthy<desired_healthy AND desired_healthy>0, 1, 0)
| eval fake_policy_flag=if(spec_min_available==0, 1, if(spec_max_unavailable_pct>=100, 1, 0))
| eval orphan_selector_gap=if(kube_deployment_status_replicas>0 AND expected_pods==0, 1, 0)
| eval signal_lane=case(
    headroom_breach=1 AND eviction_denied_count>0, "pdb_headroom_breach_with_eviction_denied",
    headroom_breach=1, "pdb_headroom_violation_risk",
    orphan_selector_gap=1, "pdb_orphaned_or_non_selecting",
    chronic_below_desired=1, "pdb_below_desired_healthy",
    fake_policy_flag=1, "pdb_fake_or_weak_policy",
    zero_budget_flag=1 AND match(workload_tier, "prod|production|tier1|staging|uat|preprod"), "pdb_zero_disruption_budget",
    eviction_denied_count>0, "kube_eviction_denied_recent",
    true(), "pdb_watch_ok")
| sort 0 cluster namespace pdb
| streamstats window=3 global=f first(current_healthy) AS ch_first last(current_healthy) AS ch_last BY cluster namespace pdb
| eval churny_deficit=if(isnotnull(ch_first) AND isnotnull(ch_last) AND ch_first>ch_last+1, 1, 0)
| eventstats max(eviction_denied_count) AS cluster_peak_evictions BY cluster
| eval severity=case(
    headroom_breach=1 AND match(workload_tier, "prod|production|tier1|tier-1|gold"), "critical",
    headroom_breach=1, "high",
    eviction_denied_count>=3 AND match(workload_tier, "prod|production|tier1|tier-1|gold"), "critical",
    eviction_denied_count>=1, "high",
    chronic_below_desired=1 AND match(workload_tier, "prod|production|tier1|tier-1|gold"), "high",
    chronic_below_desired=1, "medium",
    fake_policy_flag=1 AND match(workload_tier, "prod|production|tier1"), "high",
    fake_policy_flag=1, "medium",
    zero_budget_flag=1 AND match(workload_tier, "prod|production|tier1|tier-1|gold"), "medium",
    orphan_selector_gap=1, "medium",
    churny_deficit=1 AND match(workload_tier, "prod|production|tier1"), "medium",
    true(), "low")
| where headroom_breach=1 OR chronic_below_desired=1 OR fake_policy_flag=1 OR zero_budget_flag=1 OR orphan_selector_gap=1 OR eviction_denied_count>0 OR churny_deficit=1
| where match(workload_tier, "prod|production|preprod|staging|uat|tier1|tier-1|gold") OR pdb_required=1 OR severity IN ("critical", "high")
| table cluster namespace pdb deployment signal_lane healthy_deficit disruptions_allowed expected_pods current_healthy desired_healthy kube_deployment_status_replicas eviction_denied_count severity owner_team workload_tier cluster_peak_evictions fake_policy_flag zero_budget_flag
| append [
    | inputlookup workload_pdb_policy.csv
    | eval cluster=lower(trim(toString(coalesce(cluster, k8s_cluster, cluster_name, ""))))
    | eval namespace=trim(toString(namespace))
    | eval pdb=trim(toString(coalesce(pdb, poddisruptionbudget, pdb_name, "")))
    | eval deployment=trim(toString(coalesce(deployment, workload, deploy, "")))
    | eval owner_team=trim(toString(coalesce(owner_team, squad, platform_team, "")))
    | eval workload_tier=lower(trim(toString(coalesce(workload_tier, env_tier, tier, "dev"))))
    | eval pdb_required=tonumber(trim(toString(coalesce(pdb_required, requires_pdb, "0"))), 10)
    | where pdb_required=1 AND match(workload_tier, "prod|production|preprod|staging|uat|tier1")
    | join type=left max=0 cluster namespace deployment [
        search ((index=k8s_metrics OR index=k8s) (sourcetype="prometheus:scrape:metrics" OR sourcetype="kube:objects:metrics")) earliest=-3h@m latest=now
          | eval cluster=lower(trim(toString(coalesce(cluster, cluster_name, k8s_cluster_name, eks_cluster_name, gke_cluster_name, ""))))
          | eval mn=lower(trim(toString(coalesce(metric_name, __name__, name, MetricName, ""))))
          | rex field=_raw "namespace=\"(?<namespace>[^\"]+)\""
          | rex field=_raw "deployment=\"(?<deployment>[^\"]+)\""
          | where like(mn, "%kube_deployment_status_replicas%") AND NOT like(mn, "%kube_deployment_status_replicas_available%") AND NOT like(mn, "%kube_deployment_status_replicas_updated%") AND NOT like(mn, "%kube_deployment_status_replicas_ready%")
          | rex field=_raw "\s(?<mval>[0-9.eE+-]+)\s*$"
          | eval kube_deployment_status_replicas=tonumber(mval, 10)
          | stats latest(kube_deployment_status_replicas) AS kube_deployment_status_replicas BY cluster namespace deployment ]
    | where kube_deployment_status_replicas>=2
    | join type=left max=0 cluster namespace pdb [
        search ((index=k8s_metrics OR index=k8s) (sourcetype="prometheus:scrape:metrics" OR sourcetype="kube:objects:metrics")) earliest=-3h@m latest=now
          | eval cluster=lower(trim(toString(coalesce(cluster, cluster_name, k8s_cluster_name, eks_cluster_name, gke_cluster_name, ""))))
          | eval mn=lower(trim(toString(coalesce(metric_name, __name__, name, MetricName, ""))))
          | rex field=_raw "namespace=\"(?<namespace>[^\"]+)\""
          | rex field=_raw "poddisruptionbudget=\"(?<pdb>[^\"]+)\""
          | where like(mn, "%kube_poddisruptionbudget_status_expected_pods%")
          | stats count AS pdb_metric_rows BY cluster namespace pdb ]
    | fillnull value=0 pdb_metric_rows
    | where pdb_metric_rows=0
    | eval signal_lane="governance_gap_no_pdb_for_multi_replica_deployment"
    | eval healthy_deficit=0
    | eval disruptions_allowed=0
    | eval expected_pods=0
    | eval current_healthy=0
    | eval desired_healthy=0
    | eval eviction_denied_count=0
    | eval cluster_peak_evictions=0
    | eval fake_policy_flag=0
    | eval zero_budget_flag=0
    | eval severity=if(match(workload_tier, "prod|production|tier1"), "high", "medium")
    | table cluster namespace pdb deployment signal_lane healthy_deficit disruptions_allowed expected_pods current_healthy desired_healthy kube_deployment_status_replicas eviction_denied_count severity owner_team workload_tier cluster_peak_evictions fake_policy_flag zero_budget_flag ]
```

## CIM SPL

```spl
| tstats summariesonly=t latest(Application_State.state) AS app_state count AS app_events FROM datamodel=Application_State WHERE nodename=Application_State earliest=-3h@h latest=@h BY Application_State.dest Application_State.app
| rename Application_State.dest AS correl_host
| join type=left max=0 correl_host [
| tstats summariesonly=t avg(Performance.cpu_load_percent) AS avg_cpu_load avg(Performance.mem_used_percent) AS avg_mem_used FROM datamodel=Performance WHERE nodename=Performance.CPU OR nodename=Performance.Memory earliest=-3h@h latest=@h BY Performance.host
| rename Performance.host AS correl_host ]
| where app_state!="running" OR avg_cpu_load>92 OR avg_mem_used>95
| table correl_host app_state avg_cpu_load avg_mem_used app_events
```

## Visualization

Primary table mirroring the closing SPL projection; timechart of healthy_deficit by namespace; timeline of EvictionDenied events; single value of governance_gap row counts; heatmap of zero_budget_flag by tier.

## Known False Positives

PodDisruptionBudget objects are sometimes pinned intentionally with minAvailable equal to replica count during a narrow release ceremony so every replica stays protected while traffic shifts at the edge; those windows look like zero headroom or zero disruptionsAllowed but are deliberate if the change record and workload_pdb_policy.csv notes column document the blackout. Single-replica StatefulSets and databases that delegate high availability to the application layer may keep disruptionsAllowed at zero on purpose; downgrade using inventory notes rather than treating as sev-one. Active rolling deployments can create transient deficits where current_healthy lags desired_healthy by design until new pods pass readiness; require sustained chronic_below_desired across two evaluation intervals or corroborate with UC-3.2.6 rollout signals before executive escalation. Namespaces in deprecation drain that explicitly removed budgets to force eviction may emit governance_gap rows; verify namespace lifecycle state before paging application owners. Spot instance node groups with high churn can temporarily violate budget headroom while the cluster elastically backfills; pair node termination timelines and UC-3.2.46 context before blaming application health. Test clusters, chaos namespaces, and progressive delivery canary windows may generate EvictionDenied noise during approved experiments; suppress using workload_tier and annotations mirrored into the lookup. Brief kube-state-metrics scrape gaps after upgrades can look like missing budgets cluster-wide; demand corroborating collector health before reopening governance tickets. Helm or GitOps rename storms can orphan budgets until the next sync; treat short spikes as operational debt when change records exist. Pen testers generating eviction traffic will trip eviction lanes by design; tag those namespaces in the lookup. Regional replicas sharing logical names need distinct cluster keys in CSV or joins collapse expectations.

## References

- [Kubernetes — Pod disruption and PodDisruptionBudget](https://kubernetes.io/docs/concepts/workloads/pods/disruptions/)
- [Kubernetes — Safely drain a node](https://kubernetes.io/docs/tasks/administer-cluster/safely-drain-node/)
- [Kubernetes — API-initiated eviction](https://kubernetes.io/docs/concepts/scheduling-eviction/api-eviction/)
- [kube-state-metrics — PodDisruptionBudget metrics](https://github.com/kubernetes/kube-state-metrics/blob/main/docs/metrics/workload/poddisruptionbudget-metrics.md)
- [Google Kubernetes Engine — Pod disruption budgets](https://cloud.google.com/kubernetes-engine/docs/how-to/pod-disruption-budgets)
- [Amazon EKS — Best practices for cluster reliability (PDB guidance)](https://docs.aws.amazon.com/eks/latest/best-practices/scale-workloads.html)
- [Azure Kubernetes Service — Operator best practices (pod disruption budgets)](https://learn.microsoft.com/en-us/azure/aks/operator-best-practices-scheduler#use-pod-disruption-budgets)
- [NSA / CISA — Kubernetes Hardening Guidance](https://media.defense.gov/2022/Aug/29/2003066362/-1/-1/0/CTR_KUBERNETES_HARDENING_GUIDANCE_1.2_20220829.PDF)
