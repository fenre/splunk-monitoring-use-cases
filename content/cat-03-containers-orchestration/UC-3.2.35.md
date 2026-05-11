<!-- AUTO-GENERATED from UC-3.2.35.json — DO NOT EDIT -->

---
id: "3.2.35"
title: "Kubernetes Pod Anti-Affinity, TopologySpreadConstraints, and Failure-Domain Distribution Compliance"
status: "verified"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-3.2.35 · Kubernetes Pod Anti-Affinity, TopologySpreadConstraints, and Failure-Domain Distribution Compliance

> **Criticality:** Medium &middot; **Difficulty:** Advanced &middot; **Pillar:** Observability &middot; **Type:** Reliability, Availability &middot; **Wave:** Walk &middot; **Status:** Verified

*We watch when copies of an application pile into one geographic pocket or refuse to spread because placement rules cannot be met. We catch that early so teams fix spread settings before one pocket going dark takes the whole service.*

---

## Description

Detects Kubernetes topology-constraint-driven unschedulability and failure-domain skew: FailedScheduling events that cite didn't match pod topology spread constraints, didn't match Pod anti-affinity rules, MatchNodeSelector, taints, or insufficient cpu and memory inside zero nodes available summaries, fused with kube_pod_status_phase Pending soak, kube_pod_info placement, and kube_node_labels zone and region histograms per workload. Computes zone_distinct, skew_gap from per-zone replica counts, topology_risk_score for single-zone HA concentration, and cluster_worst_skew for fleet context, including ScheduleAnyway silent imbalance when skew exceeds policy intent without blocking scheduling. Distinct from UC-3.2.2 generic placement fit, UC-3.2.46 autoscaler scale-out refusal, UC-3.2.3 Node NotReady, and UC-3.2.6 Deployment rollout pipeline failures.

## Value

Platform and application teams gain one row that states cluster, namespace, workload, how many zones participate, CSV zone lists, replica counts, max zone replica, skew_gap, pending soak, classified failure_class, fused FailedScheduling text, topology_risk_score, fleet skew context, governance tier, owner_team, severity, and optional fleet memory overlay so leaders stop arguing whether the problem is spread policy, anti-affinity, selectors, taints, or raw capacity. Availability improves when DoNotSchedule blocks and hidden ScheduleAnyway imbalance are fixed before an AZ outage concentrates every replica. Audit and resilience reviewers retain evidence that HA topology intent was monitored against live placement, not only declared in YAML.

## Implementation

Provision k8s_metrics and k8s (or k8s_events) with distinct HEC tokens; scrape kube-state-metrics for kube_pod_status_phase, kube_pod_info, and kube_node_labels; stream kube:events; publish lookups/critical_namespaces.csv; save uc_3_2_35_topology_failure_domain_compliance every five minutes with earliest=-60m@m latest=now; route critical topology_risk_score rows for gold namespaces to platform scheduling bridges; validate using a lab Deployment with zone topologySpreadConstraints and insufficient zone diversity.

## Evidence

Saved search uc_3_2_35_topology_failure_domain_compliance with five-minute schedule; lookups/critical_namespaces.csv versioned in git; weekly CSV export of alert rows to a restricted evidence index with lookup commit hash for auditors.

## Control test

### Positive scenario

In lab namespace qa-topology-lab, apply a Deployment with zone topologySpreadConstraints using whenUnsatisfiable DoNotSchedule while only one schedulable zone exists in that pool; confirm kube:events shows FailedScheduling with topology spread language, kube_pod_status_phase Pending persists, and uc_3_2_35_topology_failure_domain_compliance returns a row with topology_risk_score at least fifty.

### Negative scenario

Restore multi-zone capacity or relax constraints, confirm pods schedule Running across zones with kube_pod_info showing distinct zone labels, skew_gap falls below alert thresholds, and the saved search emits no qualifying row for that workload within two intervals.

## Detailed Implementation

### Step 1 — Prerequisites

Head of Platform owns this control together with Kubernetes platform engineering, site reliability engineers who certify scheduling policy, observability teams operating Splunk OpenTelemetry Collector fleets, and application architects who declare high-availability topology expectations in Git. UC-3.2.35 isolates topology-constraint-driven unschedulability and failure-domain skew: when kube-scheduler cannot satisfy pod anti-affinity requiredDuringSchedulingIgnoredDuringExecution, when topologySpreadConstraints with whenUnsatisfiable DoNotSchedule block new replicas, when FailedScheduling narratives enumerate zero nodes available summaries that name topology spread or anti-affinity predicates, and when running or pending pods still concentrate in a single availability zone despite ScheduleAnyway policies that should only soften enforcement rather than guarantee balance. UC-3.2.2 remains the generic kube-scheduler placement and fit plane for Pending soak, kube_pod_status_scheduled false, and broad FailedScheduling classification including insufficient CPU, memory, taints, and volume node affinity conflicts without emphasizing topology skew math. UC-3.2.46 remains Cluster Autoscaler and Karpenter refusal to add nodes when cloud quotas, max node group sizes, or launch errors block scale-out; this UC may still fire while autoscaler succeeds yet placement rules cannot be satisfied on existing capacity. UC-3.2.3 remains Node NotReady and kubelet heartbeat semantics rather than scheduling predicates. UC-3.2.6 remains Deployment rollout condition and replica convergence analytics rather than zone distribution compliance. Keeping those boundaries crisp prevents duplicate tickets and preserves analyst trust when several sibling alerts fire during complex failures.

Index and token contracts precede saved-search authoring. Stand up index=k8s_metrics for prometheus:scrape:metrics text or normalized metric events scraped from kube-state-metrics with pod and node collectors enabled, including kube_pod_status_phase for Pending timelines, kube_pod_info for node assignment and owner references, and kube_node_labels for topology.kubernetes.io/zone, topology.kubernetes.io/region, and kubernetes.io/hostname style labels as exposed by your exporter version. Stand up index=k8s or index=k8s_events for sourcetype=kube:events streams with consistent cluster labels matching your kube-state-metrics external labels. Issue distinct HEC tokens per index class with role-based search restrictions so developers can troubleshoot namespaces without reading kube-system audit bodies. Document retention: metrics hot buckets at least fourteen days for replay, events at least thirty days for scheduling timelines.

Deploy kube-state-metrics with pod and node metric families enabled so kube_pod_info exposes namespace, pod, node, created_by_kind, and created_by_name labels per upstream documentation, and kube_node_labels exposes per-node label gauges you can rex into zone and region columns. Scrape intervals of thirty seconds are typical; fifteen seconds improves soak fidelity at license cost. For managed Kubernetes, confirm whether your distribution preserves topology labels on nodes consistently across spot and on-demand blends; Amazon EKS, Google GKE, and Microsoft AKS differ slightly in automatic topology label injection and private-zone edge cases.

Governance lookup lookups/critical_namespaces.csv must contain namespace, workload_tier taking values prod, production, preprod, staging, dev, sandbox, and owner_team or on_call_team strings for routing gold namespaces to voice bridges. Optional companion lookup ha_topology_policy.csv may add min_zones, max_skew_declared, and when_unsatisfiable_mode columns when your service catalog already encodes spread intent; the baseline SPL in this UC derives skew from live placement and events without requiring that file so sandboxes can adopt incrementally.

Risk briefing: accidental single-zone concentration for tier-one services means an availability zone outage becomes a customer-visible incident even when individual pods look healthy. DoNotSchedule semantics block scale-out during traffic spikes until architects relax constraints or add capacity in under-represented zones, which surfaces as Pending pods with explicit topology language in events. ScheduleAnyway semantics can hide imbalance until an audit compares declared maxSkew against observed zone histograms, which this UC approximates using kube-state-metrics placement samples fused with scheduler messages.

Licensing note: multisearch arms, joins, and appendcols tstats overlays keep search cost predictable; avoid unbounded scans across full metric indexes without metric name filters. Privacy note: event messages can include workload codenames and node hostnames; restrict dashboard ACLs.

Differentiation recap: topology spread and anti-affinity constraint compliance with failure-domain histograms and skew estimates, not generic Pending soak alone, not autoscaler cloud refusal, not node NotReady, not Deployment rollout conditions.

Collector architecture notes: self-managed clusters scrape kube-state-metrics inside the mesh; air-gapped environments mirror images before enabling wide pod collectors. Dual-stack IPv6 clusters must preserve consistent instance labels in relabel configs so node joins remain stable.

FinOps alignment: single-zone concentration sometimes precedes expensive emergency scale-out in one AZ; pair findings with capacity reviews before blindly raising replica counts.

Reliability alignment: integrate optional descheduler rebalance signals in runbooks when skew persists after kube-scheduler proves placement is feasible but historical decisions left imbalance.

Security alignment: kube-state-metrics RBAC grants list watch on pods and nodes; store service account tokens in vaults with quarterly rotation.

Performance alignment: keep kube_pod_info and kube_node_labels searches narrow with explicit earliest windows; high-cardinality pod labels inflate series counts when relabel rules are too permissive.

Training alignment: teach responders the difference between Pending caused by unsatisfiable topology spread versus Pending caused by Insufficient cpu on every node, using FailedScheduling text as the ground truth.

Documentation alignment: wiki-map this UC beside internal HA topology standards, zone outage game days, and cluster upgrade runbooks.

Review cadence: quarterly replay one historical topology incident through the SPL after kube-state-metrics upgrades.

Escalation alignment: critical plus gold workload_tier engages platform and application leadership jointly when skew_gap and topology_risk_score both breach.

Telemetry hygiene: deduplicate overlapping Prometheus agents that scrape kube-state-metrics without honor_labels discipline.

Governance alignment: CAB records should cover HEC token ACL changes and ServiceMonitor edits together when scrape paths move.

Platform scheduling depth note A: requiredDuringScheduling anti-affinity can make even abundant CPU unusable; correlate Insufficient-like summaries only after confirming zero nodes available text references affinity predicates.

Platform scheduling depth note B: topology.kubernetes.io/hostname spread behaves like rack-aware placement when zones are uniform; interpret hostname concentration as rack blast radius for bare-metal estates.

Platform scheduling depth note C: label selectors that reference custom failure-domain keys such as topology.kubernetes.io/rack require parallel rex arms in local macros when your cloud uses different label spellings.

Platform scheduling depth note D: kube-scheduler scoring versus filtering distinctions matter for ScheduleAnyway; low score placements may still land imbalanced without violating hard constraints.

Platform scheduling depth note E: PodDisruptionBudget minAvailable can interact with spread when simultaneous evictions skew counts; pair PDB analytics from sibling UCs when skew spikes during voluntary disruption windows.

Platform scheduling depth note F: init container resource totals participate in fit; skew investigations after init changes should revisit requests, not only spread fields.

Platform scheduling depth note G: static CPU manager and topology manager can shrink feasible domains on NUMA-heavy nodes; FailedScheduling may mention resources even when spread also fails.

Platform scheduling depth note H: Windows node pools sometimes omit familiar Linux topology labels; extend coalesce ladders after migrations and document compensating kubectl procedures when metrics are unavailable.

Platform scheduling depth note I: service mesh sidecars inflate resource requests and can change fit outcomes without changing spread declarations; compare before and after mesh rollouts.

Platform scheduling depth note J: cluster upgrades that rename metrics labels require props transforms updates before alerts mute falsely.

Closing Step 1 checklist: indexes named, kube-state-metrics metric families enumerated, boundaries versus UC-3.2.2, UC-3.2.46, UC-3.2.3, and UC-3.2.6 restated, governance lookup expectations documented, risk of silent ScheduleAnyway imbalance highlighted for auditors.

### Step 2 — Configure data collection

Deploy a ServiceMonitor or PodMonitor that selects kube-state-metrics and scrapes port 8080 metrics path /metrics with intervals and timeouts aligned to your kube-prometheus-stack baseline. Relabel rules must preserve namespace, pod, node, uid, created_by_kind, and created_by_name labels emitted by your kube-state-metrics version so Splunk coalesce ladders stay short. Confirm kube_node_labels series include topology.kubernetes.io/zone and topology.kubernetes.io/region when your cloud populates them; on self-managed clusters, verify kubectl get node --show-labels matches the rex arms used in the SPL.

Add a kubernetes_events or k8s_events receiver in watch mode so FailedScheduling narratives arrive with the same cluster field your metrics carry. OpenTelemetry Collector prometheus receiver jobs should forward kube-state-metrics series into the same k8s_metrics index with sourcetype=prometheus:scrape:metrics and identical cluster tags.

Example ServiceMonitor skeleton for kube-state-metrics pod and node collectors:

```yaml
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: kube-state-metrics-topology
  namespace: kube-system
  labels:
    release: prom
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
      path: /metrics
```

Collector fragment showing events export:

```yaml
receivers:
  k8s_events:
    auth_type: serviceAccount
    namespaces: []
exporters:
  splunk_hec/events:
    token: ${SPLUNK_HEC_TOKEN_K8S_EVENTS}
    endpoint: https://splunk-hec.example:8088/services/collector/event
    index: k8s
    sourcetype: kube:events
service:
  pipelines:
    logs/events:
      receivers: [k8s_events]
      exporters: [splunk_hec/events]
```

Sample critical_namespaces.csv:

```csv
namespace,workload_tier,owner_team,criticality
prod-payments,prod,payments-sre,gold
sandbox-batch,sandbox,data-platform,bronze
```

props and transforms guidance: normalize __name__, value, namespace, pod, node, phase, and cluster labels onto indexed fields; keep camelCase aliases from OTEL exporters in transforms.conf so SPL coalesce lists stay stable.

Validation before alert authoring: index=k8s_metrics kube_pod_info earliest=-30m must return node assignments for Running pods in busy clusters; index=k8s_metrics kube_node_labels earliest=-30m must return zone labels on workers in multi-AZ estates; index=k8s sourcetype=kube:events reason=FailedScheduling earliest=-24h should return topology or anti-affinity language when workloads are misconfigured. Clock skew between API server, kube-state-metrics, and Splunk _time must stay under sixty seconds.

Frequency and volume planning: FailedScheduling can be chatty during bad releases; sampling at the collector for verbatim message truncation is acceptable only when legal approves lossy event bodies, otherwise ship full messages and rely on Splunk throttling.

### Step 3 — Create the search and alert

Save the SPL as saved search uc_3_2_35_topology_failure_domain_compliance with five-minute schedule, dispatch earliest=-60m@m, dispatch latest=now, and throttle duplicate rows per cluster namespace workload for ninety minutes unless severity escalates from medium to critical. Route critical to immediate voice paging with platform scheduling bridges; route high to high-priority tickets with SMS backup for gold namespaces from critical_namespaces.csv.

Pipeline understanding for operators: the opening comment macro lists indexes and the time horizon. multisearch fans kube_pod_status_phase Pending soak timelines and kube:events FailedScheduling arms that emphasize topology spread, anti-affinity, node selector, taint, and insufficient resource narratives so a silent failure in one path still surfaces the other. streamstats measures continuous Pending duration per Pod using one-minute buckets. coalesce ladders normalize cluster, namespace, and pod labels across EKS, GKE, and AKS field habits. Joins attach kube_pod_info node assignments and kube_node_labels zone and region labels for histogram math. eventstats derives per-zone replica counts before workload-level stats compute skew_gap and zone_distinct. inputlookup critical_namespaces.csv enriches workload_tier and owner_team. case maps failure_class and topology_risk_score using scheduler message patterns and skew heuristics. appendcols runs an accelerated tstats average against Performance.Memory as a fleet memory pressure hint when Common Information Model summaries exist. The closing table lists eighteen analyst-facing columns for topology compliance review.

Paste-and-run SPL for alerts and dashboards must match the spl JSON field exactly:

```spl
`comment("UC-3.2.35 Kubernetes topology spread, anti-affinity, and failure-domain skew. earliest=-60m@m latest=now idx=k8s_metrics k8s k8s_events")`
| multisearch
    [ search index=k8s_metrics sourcetype="prometheus:scrape:metrics" earliest=-60m@m latest=now
      | eval cluster=lower(trim(toString(coalesce(k8s_cluster_name, cluster_name, cluster, eks_cluster_name, gke_cluster_name, aks_cluster_name, resource_cluster, ""))))
      | eval mn=lower(trim(toString(coalesce(__name__, metric_name, name, ""))))
      | eval mv=tonumber(tostring(coalesce(value, metric_value, Value, "")), 10)
      | eval ph=lower(trim(toString(coalesce(phase, phase_name, ""))))
      | where mn="kube_pod_status_phase" AND ph="pending" AND mv>0
      | eval pod=trim(toString(coalesce(pod, pod_name, "")))
      | eval namespace=trim(toString(coalesce(namespace, k8s_namespace, kube_namespace, ns, "")))
      | where len(cluster)>0 AND len(namespace)>0 AND len(pod)>0
      | bucket _time span=1m
      | stats max(mv) AS pend BY cluster namespace pod _time
      | where pend>0
      | sort 0 cluster namespace pod + _time
      | streamstats current=t global=f first(_time) AS pend_start BY cluster namespace pod
      | eval pending_soak_min=round((now()-pend_start)/60, 2)
      | stats latest(pending_soak_min) AS pending_soak_min BY cluster namespace pod
      | eval sched_blend="phase_pending"
      | eval fs_ts=0
      | eval fs_message="" ]
    [ search (index=k8s OR index=k8s_events) sourcetype="kube:events" earliest=-60m@m latest=now
      | eval cluster=lower(trim(toString(coalesce(k8s_cluster_name, cluster_name, cluster, source_cluster, ""))))
      | eval namespace=trim(toString(coalesce(metadata_namespace, namespace, involvedObject_namespace, "")))
      | eval pod=trim(toString(coalesce(involvedObject_name, `involvedObject.name`, "")))
      | eval ik=lower(trim(toString(coalesce(involvedObject_kind, `involvedObject.kind`, ""))))
      | eval reason=trim(toString(coalesce(reason, Reason, "")))
      | eval msg=toString(coalesce(message, Message, ""))
      | where reason="FailedScheduling" AND ik="pod" AND len(cluster)>0 AND len(namespace)>0 AND len(pod)>0
      | where match(lower(msg), "topology spread|topologyspread|anti-affinit|pod anti-affinity|didn.t match pod topology|didn.t match pod anti-affinity|0/\d+ nodes are available|matchnodeselect|insufficient cpu|insufficient memory|taint|nodes are available: didn.t satisfy pod anti-affinity")
      | stats latest(msg) AS fs_message max(_time) AS fs_ts BY cluster namespace pod
      | eval pending_soak_min=0
      | eval sched_blend="kube_event" ]
| stats max(pending_soak_min) AS pending_soak_min values(sched_blend) AS blend_mv max(fs_ts) AS fs_ts values(fs_message) AS fs_mv BY cluster namespace pod
| eval fs_message=coalesce(mvindex(mvdedup(fs_mv),0), "")
| eval pending_soak_min=coalesce(pending_soak_min, 0)
| join type=left max=0 cluster namespace pod
    [| search index=k8s_metrics sourcetype="prometheus:scrape:metrics" earliest=-60m@m latest=now
      | eval cluster=lower(trim(toString(coalesce(k8s_cluster_name, cluster_name, cluster, eks_cluster_name, gke_cluster_name, aks_cluster_name, resource_cluster, ""))))
      | eval mn=lower(trim(toString(coalesce(__name__, metric_name, name, ""))))
      | where mn="kube_pod_info" OR like(mn, "%kube_pod_info%")
      | rex field=_raw max_match=0 "pod=\"(?<pod_a>[^\"]+)\""
      | rex field=_raw max_match=0 "namespace=\"(?<ns_a>[^\"]+)\""
      | rex field=_raw max_match=0 "node=\"(?<node_a>[^\"]+)\""
      | rex field=_raw max_match=0 "created_by_kind=\"(?<cbk_a>[^\"]+)\""
      | rex field=_raw max_match=0 "created_by_name=\"(?<cbn_a>[^\"]+)\""
      | eval namespace=trim(toString(coalesce(ns_a, "")))
      | eval pod=trim(toString(pod_a))
      | eval node=lower(trim(toString(node_a)))
      | eval work_kind=lower(trim(toString(cbk_a)))
      | rex field=cbn_a max_match=0 "(?<wl_a>.+)-[a-f0-9]{8,10}$"
      | eval workload=coalesce(nullif(trim(wl_a),""), nullif(trim(cbn_a),""), pod)
      | where len(cluster)>0 AND len(namespace)>0 AND len(pod)>0
      | stats latest(node) AS node latest(work_kind) AS work_kind latest(workload) AS workload BY cluster namespace pod ]
| fillnull value="" node
| eval workload=coalesce(workload, pod)
| eval work_kind=coalesce(work_kind, "unknown")
| eval zone=""
| eval region=""
| join type=left max=0 cluster node
    [| search index=k8s_metrics sourcetype="prometheus:scrape:metrics" earliest=-60m@m latest=now
      | eval cluster=lower(trim(toString(coalesce(k8s_cluster_name, cluster_name, cluster, eks_cluster_name, gke_cluster_name, aks_cluster_name, resource_cluster, ""))))
      | eval mn=lower(trim(toString(coalesce(__name__, metric_name, name, ""))))
      | where like(mn, "kube_node_labels")
      | rex field=_raw max_match=0 "node=\"(?<node_b>[^\"]+)\""
      | rex field=_raw max_match=0 "label_topology_kubernetes_io_zone=\"(?<zb>[^\"]*)\""
      | rex field=_raw max_match=0 "label_topology_kubernetes_io_region=\"(?<rb>[^\"]*)\""
      | eval zone=coalesce(nullif(trim(zb),""), "unlabeled-zone")
      | eval region=coalesce(nullif(trim(rb),""), "unlabeled-region")
      | stats latest(zone) AS zone latest(region) AS region BY cluster node_b
      | rename node_b AS node ]
| eval zone=if(len(node)==0 OR node="", "unscheduled-no-node", coalesce(nullif(zone,""), "unlabeled-zone"))
| eval region=coalesce(nullif(region,""), "unlabeled-region")
| eventstats count AS zone_pop BY cluster namespace workload zone
| stats max(zone_pop) AS max_zone_replica min(zone_pop) AS min_zone_replica dc(zone) AS zone_distinct count AS pods_observed values(zone) AS zones_mv max(pending_soak_min) AS pending_soak_min latest(fs_message) AS fs_message latest(work_kind) AS work_kind BY cluster namespace workload
| eval skew_gap=max_zone_replica-min_zone_replica
| eval zones_csv=mvjoin(mvdedup(zones_mv), "|")
| eventstats max(skew_gap) AS cluster_worst_skew BY cluster
| join type=left max=0 namespace
    [| inputlookup critical_namespaces.csv
      | eval namespace=trim(toString(namespace))
      | eval workload_tier=lower(trim(toString(coalesce(workload_tier, env_tier, tier, criticality, "standard"))))
      | eval owner_team=trim(toString(coalesce(owner_team, squad, on_call_team, "")))
      | fields namespace workload_tier owner_team ]
| fillnull value="standard" workload_tier
| fillnull value="" owner_team
| eval failure_class=case(
    match(lower(fs_message), "(?i)topology spread|topologyspread|pod topology"), "topology_spread_unsatisfiable",
    match(lower(fs_message), "(?i)anti-affinit|inter-pod anti"), "pod_anti_affinity_unsatisfiable",
    match(lower(fs_message), "(?i)matchnodeselect|node selector"), "node_selector_mismatch",
    match(lower(fs_message), "(?i)insufficient cpu"), "insufficient_cpu",
    match(lower(fs_message), "(?i)insufficient memory"), "insufficient_memory",
    match(lower(fs_message), "(?i)taint"), "untolerated_taint",
    skew_gap>=3 AND zone_distinct<=2, "schedule_anyway_skew",
    zone_distinct==1 AND pods_observed>=3, "single_zone_ha_risk",
    true(), "placement_policy_review")
| eval topology_risk_score=case(
    failure_class IN ("topology_spread_unsatisfiable","pod_anti_affinity_unsatisfiable") AND pending_soak_min>=10, 100,
    failure_class IN ("topology_spread_unsatisfiable","pod_anti_affinity_unsatisfiable"), 90,
    zone_distinct==1 AND pods_observed>=3 AND match(workload_tier,"prod|gold|tier0|tier_0"), 85,
    skew_gap>=3, 75,
    pending_soak_min>=15, 65,
    true(), 30)
| eval severity=case(topology_risk_score>=85, "critical", topology_risk_score>=70, "high", topology_risk_score>=50, "medium", true(), "low")
| where topology_risk_score>=50 OR pending_soak_min>=8 OR len(fs_message)>50
| appendcols [| tstats summariesonly=t avg(Performance.mem_used_percent) AS cim_mem_fleet_avg FROM datamodel=Performance WHERE nodename=Performance.Memory earliest=-2h@h latest=now | head 1 ]
| table cluster namespace workload work_kind zone_distinct zones_csv pods_observed max_zone_replica skew_gap pending_soak_min failure_class fs_message topology_risk_score cluster_worst_skew workload_tier owner_team severity cim_mem_fleet_avg
```

Alert actions: include cluster, namespace, workload, topology_risk_score, skew_gap, failure_class, fs_message, severity, workload_tier, and owner_team in tickets; link to Dashboard Studio Kubernetes topology health view; attach three redacted kube events when legal approves.

Operational notes: when kube_pod_info samples are missing because a scrape dropped labels, investigate relabel configs before muting. When only events fire without placement metrics, assume kube-state-metrics outage rather than healthy spread. When ScheduleAnyway workloads show high skew without Pending, treat as silent imbalance per risk score rather than ignoring the row.

Dashboard publishing: heatmap of zone_distinct by namespace; single value critical count; table sorted by topology_risk_score then workload_tier.

Performance tuning: if Job Inspector shows multisearch queueing, materialize five-minute rollups into a summary index and point this alert at summaries while retaining raw scrapes for investigations.

### Step 4 — Validate

Synthetic topology spread DoNotSchedule: in namespace qa-topology-lab apply a Deployment with three replicas and a topologySpreadConstraints stanza referencing topology.kubernetes.io/zone with maxSkew 1 and whenUnsatisfiable DoNotSchedule while the cluster temporarily has only one schedulable zone in that pool, confirm kube:events shows FailedScheduling mentioning didn't match pod topology spread constraints or similar scheduler wording, confirm kube_pod_status_phase shows Pending soak, and uc_3_2_35_topology_failure_domain_compliance returns a qualifying row with failure_class topology_spread_unsatisfiable or equivalent classification.

Synthetic pod anti-affinity: apply requiredDuringSchedulingIgnoredDuringExecution podAntiAffinity that forbids co-location on hostname with more replicas than usable nodes, confirm FailedScheduling mentions anti-affinity or inter-pod affinity language, and verify pending_soak_min crosses the alert gate.

Synthetic running skew: park six Running replicas across two zones unevenly using nodeSelector or known node placement, confirm skew_gap rises, zone_distinct falls below declared intent in your internal policy spreadsheet, and topology_risk_score reflects HA concentration for gold namespaces from the lookup.

Field sanity: rename a sandbox forwarder label to pod_name only and verify coalesce still resolves pod. RBAC: readers without index access must see zero rows.

Correlation: compare alert timestamps to kubectl describe pod events and kubectl get events --field-selector reason=FailedScheduling; misalignment often means metrics lagged behind API writes.

Extended validation: snapshot the alert table before and after fixing spread or anti-affinity; store kubectl get pods -o wide output showing NODE and zone labels for auditors.

Investigative clones: widen earliest to four hours only in ad-hoc searches to reconstruct intermittent skew during rolling upgrades; keep the saved alert window at sixty minutes for cost control.

Audit correlation: when legal requests evidence, export the closing table with redacted fs_message bodies while preserving failure_class and timestamps for accountability.

### Step 5 — Operationalize & Troubleshoot

Case 1 — FailedScheduling cites didn't match pod topology spread constraints or topology spread constraint predicates: relax maxSkew cautiously, add capacity in under-represented zones, split workloads across namespaces only when policy allows, or change whenUnsatisfiable to ScheduleAnyway under architecture review with explicit blast-radius acceptance.
Case 2 — FailedScheduling cites didn't match Pod anti-affinity rules or inter-pod anti-affinity: reduce replicas temporarily, widen topology keys from hostname to zone when safe, or redesign soft versus hard anti-affinity with application architects before production promotion.
Case 3 — MatchNodeSelector or node label drift blocks placement: reconcile node labels with Git-declared selectors, fix mistaken node pool tags after cloud maintenance, and re-run rollout once labels converge.
Case 4 — Insufficient cpu or Insufficient memory appears alongside topology language: fix requests first, then revisit spread; otherwise new nodes may still not help if predicates fail before fit.
Case 5 — Untolerated taint lines dominate the message while spread also appears: add tolerations only when policy allows, or remove maintenance taints after windows close; do not mute topology debt without reading the full event body.
Case 6 — Running workloads show high skew_gap with ScheduleAnyway semantics in Git: treat as silent imbalance; use descheduler strategies or voluntary replays under change control, not only scheduler edits.
Case 7 — zone_distinct equals one for three or more replicas in gold namespaces: execute zone outage game-day assumptions, fail traffic at load balancers if needed, and add nodes in alternate AZs before declaring recovery.
Case 8 — cluster_worst_skew from eventstats shows fleet-wide concentration during a single change: freeze further releases, identify the shared node pool or label regression, and coordinate with network and platform squads.
Case 9 — Pending clears but skew remains after autoscaler adds nodes: confirm UC-3.2.46 scale-out succeeded yet placement rules still biased; tune spread maxSkew or pod affinity weighting rather than blaming cloud denial.
Case 10 — kube_node_labels missing zone while cloud console shows AZ: fix exporter relabel rules, reopen provider support tickets for label propagation bugs, and pause skew scoring until metrics return.
Case 11 — Symptoms resemble this UC but Deployment conditions show ProgressDeadlineExceeded without topology language: pivot to UC-3.2.6 for rollout pipeline truth before editing spread policies.
Case 12 — Symptoms resemble generic Pending without topology or anti-affinity text: pivot to UC-3.2.2 for broader scheduler fit classification while keeping this UC dashboard panels for histogram context.

Closing checklist: five step headers use plain em dashes as mandated; Step 3 fenced SPL matches the spl JSON field; multisearch covers Pending soak and FailedScheduling lanes; streamstats implements soak timing; joins pull kube_pod_info and kube_node_labels; eventstats derives zone histograms; inputlookup enriches governance; case implements failure_class and topology_risk_score; appendcols provides tstats Performance overlay; final table includes eighteen columns; monitoringType lists Reliability and Availability; cimModels lists Application_State and Performance; equipment lists kubernetes and opentelemetry; equipmentModels lists kubernetes_k8s.

Runbook micro-sections: if severity is critical and failure_class is topology_spread_unsatisfiable, attach zone histogram screenshots before approving policy relaxations. If failure_class is pod_anti_affinity_unsatisfiable, link architecture records for hard anti-affinity choices. If topology_risk_score is high while fs_message is short, rely on skew_gap and zone_distinct for executive narration.

FinOps alignment: chart skew_gap trends only after confirming kube-state-metrics scrape continuity so finance reviews are not based on missing-node artifacts.

Reliability alignment: pair with UC-3.2.46 when Pending persists seconds after scale-out events to separate cloud denial from pure constraint unsatisfiability.

Security alignment: redact internal hostnames in tickets when fs_message includes node names tied to regulated data halls.

Performance alignment: summary index materializations should retain cluster namespace workload keys to preserve deduplication after alert throttles.

Governance alignment: weekly CSV exports of qualifying rows with lookup commit hashes satisfy internal platform audit requests without exposing raw metric dumps.

Training alignment: game-day inject impossible maxSkew in sandbox monthly so new responders recognize failure_class taxonomy quickly.

Documentation alignment: link this saved search URL from the Kubernetes scheduling runbook index page maintained by platform engineering.

Closing narrative: this UC closes the gap between generic Pending noise and actionable topology compliance evidence by demanding FailedScheduling text, kube-state-metrics placement joins, zone histograms, soak timing, skew estimates, and ownership metadata in one row so incident commanders spend seconds deciding among spread policy, capacity, taint, and selector hypotheses.

## SPL

```spl
`comment("UC-3.2.35 Kubernetes topology spread, anti-affinity, and failure-domain skew. earliest=-60m@m latest=now idx=k8s_metrics k8s k8s_events")`
| multisearch
    [ search index=k8s_metrics sourcetype="prometheus:scrape:metrics" earliest=-60m@m latest=now
      | eval cluster=lower(trim(toString(coalesce(k8s_cluster_name, cluster_name, cluster, eks_cluster_name, gke_cluster_name, aks_cluster_name, resource_cluster, ""))))
      | eval mn=lower(trim(toString(coalesce(__name__, metric_name, name, ""))))
      | eval mv=tonumber(tostring(coalesce(value, metric_value, Value, "")), 10)
      | eval ph=lower(trim(toString(coalesce(phase, phase_name, ""))))
      | where mn="kube_pod_status_phase" AND ph="pending" AND mv>0
      | eval pod=trim(toString(coalesce(pod, pod_name, "")))
      | eval namespace=trim(toString(coalesce(namespace, k8s_namespace, kube_namespace, ns, "")))
      | where len(cluster)>0 AND len(namespace)>0 AND len(pod)>0
      | bucket _time span=1m
      | stats max(mv) AS pend BY cluster namespace pod _time
      | where pend>0
      | sort 0 cluster namespace pod + _time
      | streamstats current=t global=f first(_time) AS pend_start BY cluster namespace pod
      | eval pending_soak_min=round((now()-pend_start)/60, 2)
      | stats latest(pending_soak_min) AS pending_soak_min BY cluster namespace pod
      | eval sched_blend="phase_pending"
      | eval fs_ts=0
      | eval fs_message="" ]
    [ search (index=k8s OR index=k8s_events) sourcetype="kube:events" earliest=-60m@m latest=now
      | eval cluster=lower(trim(toString(coalesce(k8s_cluster_name, cluster_name, cluster, source_cluster, ""))))
      | eval namespace=trim(toString(coalesce(metadata_namespace, namespace, involvedObject_namespace, "")))
      | eval pod=trim(toString(coalesce(involvedObject_name, `involvedObject.name`, "")))
      | eval ik=lower(trim(toString(coalesce(involvedObject_kind, `involvedObject.kind`, ""))))
      | eval reason=trim(toString(coalesce(reason, Reason, "")))
      | eval msg=toString(coalesce(message, Message, ""))
      | where reason="FailedScheduling" AND ik="pod" AND len(cluster)>0 AND len(namespace)>0 AND len(pod)>0
      | where match(lower(msg), "topology spread|topologyspread|anti-affinit|pod anti-affinity|didn.t match pod topology|didn.t match pod anti-affinity|0/\d+ nodes are available|matchnodeselect|insufficient cpu|insufficient memory|taint|nodes are available: didn.t satisfy pod anti-affinity")
      | stats latest(msg) AS fs_message max(_time) AS fs_ts BY cluster namespace pod
      | eval pending_soak_min=0
      | eval sched_blend="kube_event" ]
| stats max(pending_soak_min) AS pending_soak_min values(sched_blend) AS blend_mv max(fs_ts) AS fs_ts values(fs_message) AS fs_mv BY cluster namespace pod
| eval fs_message=coalesce(mvindex(mvdedup(fs_mv),0), "")
| eval pending_soak_min=coalesce(pending_soak_min, 0)
| join type=left max=0 cluster namespace pod
    [| search index=k8s_metrics sourcetype="prometheus:scrape:metrics" earliest=-60m@m latest=now
      | eval cluster=lower(trim(toString(coalesce(k8s_cluster_name, cluster_name, cluster, eks_cluster_name, gke_cluster_name, aks_cluster_name, resource_cluster, ""))))
      | eval mn=lower(trim(toString(coalesce(__name__, metric_name, name, ""))))
      | where mn="kube_pod_info" OR like(mn, "%kube_pod_info%")
      | rex field=_raw max_match=0 "pod=\"(?<pod_a>[^\"]+)\""
      | rex field=_raw max_match=0 "namespace=\"(?<ns_a>[^\"]+)\""
      | rex field=_raw max_match=0 "node=\"(?<node_a>[^\"]+)\""
      | rex field=_raw max_match=0 "created_by_kind=\"(?<cbk_a>[^\"]+)\""
      | rex field=_raw max_match=0 "created_by_name=\"(?<cbn_a>[^\"]+)\""
      | eval namespace=trim(toString(coalesce(ns_a, "")))
      | eval pod=trim(toString(pod_a))
      | eval node=lower(trim(toString(node_a)))
      | eval work_kind=lower(trim(toString(cbk_a)))
      | rex field=cbn_a max_match=0 "(?<wl_a>.+)-[a-f0-9]{8,10}$"
      | eval workload=coalesce(nullif(trim(wl_a),""), nullif(trim(cbn_a),""), pod)
      | where len(cluster)>0 AND len(namespace)>0 AND len(pod)>0
      | stats latest(node) AS node latest(work_kind) AS work_kind latest(workload) AS workload BY cluster namespace pod ]
| fillnull value="" node
| eval workload=coalesce(workload, pod)
| eval work_kind=coalesce(work_kind, "unknown")
| eval zone=""
| eval region=""
| join type=left max=0 cluster node
    [| search index=k8s_metrics sourcetype="prometheus:scrape:metrics" earliest=-60m@m latest=now
      | eval cluster=lower(trim(toString(coalesce(k8s_cluster_name, cluster_name, cluster, eks_cluster_name, gke_cluster_name, aks_cluster_name, resource_cluster, ""))))
      | eval mn=lower(trim(toString(coalesce(__name__, metric_name, name, ""))))
      | where like(mn, "kube_node_labels")
      | rex field=_raw max_match=0 "node=\"(?<node_b>[^\"]+)\""
      | rex field=_raw max_match=0 "label_topology_kubernetes_io_zone=\"(?<zb>[^\"]*)\""
      | rex field=_raw max_match=0 "label_topology_kubernetes_io_region=\"(?<rb>[^\"]*)\""
      | eval zone=coalesce(nullif(trim(zb),""), "unlabeled-zone")
      | eval region=coalesce(nullif(trim(rb),""), "unlabeled-region")
      | stats latest(zone) AS zone latest(region) AS region BY cluster node_b
      | rename node_b AS node ]
| eval zone=if(len(node)==0 OR node="", "unscheduled-no-node", coalesce(nullif(zone,""), "unlabeled-zone"))
| eval region=coalesce(nullif(region,""), "unlabeled-region")
| eventstats count AS zone_pop BY cluster namespace workload zone
| stats max(zone_pop) AS max_zone_replica min(zone_pop) AS min_zone_replica dc(zone) AS zone_distinct count AS pods_observed values(zone) AS zones_mv max(pending_soak_min) AS pending_soak_min latest(fs_message) AS fs_message latest(work_kind) AS work_kind BY cluster namespace workload
| eval skew_gap=max_zone_replica-min_zone_replica
| eval zones_csv=mvjoin(mvdedup(zones_mv), "|")
| eventstats max(skew_gap) AS cluster_worst_skew BY cluster
| join type=left max=0 namespace
    [| inputlookup critical_namespaces.csv
      | eval namespace=trim(toString(namespace))
      | eval workload_tier=lower(trim(toString(coalesce(workload_tier, env_tier, tier, criticality, "standard"))))
      | eval owner_team=trim(toString(coalesce(owner_team, squad, on_call_team, "")))
      | fields namespace workload_tier owner_team ]
| fillnull value="standard" workload_tier
| fillnull value="" owner_team
| eval failure_class=case(
    match(lower(fs_message), "(?i)topology spread|topologyspread|pod topology"), "topology_spread_unsatisfiable",
    match(lower(fs_message), "(?i)anti-affinit|inter-pod anti"), "pod_anti_affinity_unsatisfiable",
    match(lower(fs_message), "(?i)matchnodeselect|node selector"), "node_selector_mismatch",
    match(lower(fs_message), "(?i)insufficient cpu"), "insufficient_cpu",
    match(lower(fs_message), "(?i)insufficient memory"), "insufficient_memory",
    match(lower(fs_message), "(?i)taint"), "untolerated_taint",
    skew_gap>=3 AND zone_distinct<=2, "schedule_anyway_skew",
    zone_distinct==1 AND pods_observed>=3, "single_zone_ha_risk",
    true(), "placement_policy_review")
| eval topology_risk_score=case(
    failure_class IN ("topology_spread_unsatisfiable","pod_anti_affinity_unsatisfiable") AND pending_soak_min>=10, 100,
    failure_class IN ("topology_spread_unsatisfiable","pod_anti_affinity_unsatisfiable"), 90,
    zone_distinct==1 AND pods_observed>=3 AND match(workload_tier,"prod|gold|tier0|tier_0"), 85,
    skew_gap>=3, 75,
    pending_soak_min>=15, 65,
    true(), 30)
| eval severity=case(topology_risk_score>=85, "critical", topology_risk_score>=70, "high", topology_risk_score>=50, "medium", true(), "low")
| where topology_risk_score>=50 OR pending_soak_min>=8 OR len(fs_message)>50
| appendcols [| tstats summariesonly=t avg(Performance.mem_used_percent) AS cim_mem_fleet_avg FROM datamodel=Performance WHERE nodename=Performance.Memory earliest=-2h@h latest=now | head 1 ]
| table cluster namespace workload work_kind zone_distinct zones_csv pods_observed max_zone_replica skew_gap pending_soak_min failure_class fs_message topology_risk_score cluster_worst_skew workload_tier owner_team severity cim_mem_fleet_avg
```

## CIM SPL

```spl
| tstats summariesonly=t latest(Application_State.state) AS app_state latest(Application_State.info) AS app_info FROM datamodel=Application_State WHERE nodename=Application_State (Application_State.app="kubernetes" OR Application_State.app="k8s" OR like(Application_State.app, "%kube%")) earliest=-4h@h latest=@h BY Application_State.dest
| rename Application_State.dest AS cim_host
| join type=left max=0 cim_host [| tstats summariesonly=t avg(Performance.cpu_load_percent) AS cpu_load_pct FROM datamodel=Performance WHERE nodename=Performance.CPU earliest=-4h@h latest=@h BY Performance.host | rename Performance.host AS cim_host ]
| table cim_host app_state app_info cpu_load_pct
```

## Visualization

Primary table mirroring the closing SPL projection; heatmap of zone_distinct by namespace; single value of critical severity count; timeline of FailedScheduling excerpts; drilldown from workload to kube:events and kube_pod_info samples.

## Known False Positives

Legitimately single-zone workloads are expected in single-AZ test clusters, many development namespaces, and specialized low-latency services where architects intentionally disable hard spread. Recently launched Deployments still scaling up can show temporary single-zone histograms until the rolling update finishes across zones. Clusters that temporarily have only one functional AZ during provider incidents will concentrate replicas without malicious intent; pair provider status pages before paging application teams. Capacity-constrained zones with cordoned nodes can force skew until capacity returns; corroborate node cordon and taint narratives. Intentional same-host placement for DaemonSet-like patterns or hostPort constraints can look like skew when grouped by Deployment name; filter known DaemonSet namespaces via lookup flags. Workloads with whenUnsatisfiable ScheduleAnyway are advisory at scheduling time; this UC deliberately surfaces silent skew as lower certainty findings rather than hard blocks. Workloads with requiredDuringScheduling node or pod affinity scoped to one zone for latency may always show zone_distinct equals one by design; inventory those rows. Transient evictions and rescheduling storms can temporarily distort histograms for one or two scrape intervals; require sustained skew or explicit FailedScheduling text before executive escalation. Scale-down-in-progress clusters may drain alternate zones first and look imbalanced until the operation completes. Autoscaler or Karpenter activity still adding nodes in alternate zones can overlap with skew signals; correlate UC-3.2.46 logs and metrics to avoid blaming spread policy when nodes are simply not Ready yet.

## References

- [Kubernetes — Pod Topology Spread Constraints](https://kubernetes.io/docs/concepts/workloads/pods/pod-topology-spread-constraints/)
- [Kubernetes — Assigning Pods to Nodes (affinity and anti-affinity)](https://kubernetes.io/docs/concepts/scheduling-eviction/assign-pod-node/)
- [kube-state-metrics — Pod metrics](https://github.com/kubernetes/kube-state-metrics/blob/main/docs/metrics/workload/pod-metrics.md)
- [Kubernetes — kube-scheduler](https://kubernetes.io/docs/concepts/scheduling-eviction/kube-scheduler/)
- [Kubernetes — Scheduling Framework](https://kubernetes.io/docs/concepts/scheduling-eviction/scheduling-framework/)
- [Kubernetes descheduler (rebalance skew)](https://github.com/kubernetes-sigs/descheduler)
- [Kubernetes — Well-Known Labels (topology.kubernetes.io/zone)](https://kubernetes.io/docs/reference/labels-annotations-taints/#topologykubernetesiozone)
- [kube-state-metrics — Node metrics](https://github.com/kubernetes/kube-state-metrics/blob/main/docs/metrics/workload/)
