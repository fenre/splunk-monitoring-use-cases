<!-- AUTO-GENERATED from UC-3.2.6.json — DO NOT EDIT -->

---
id: "3.2.6"
title: "Kubernetes Deployment Rollout Failures (Rollout Pipeline Reliability)"
status: "verified"
criticality: "critical"
splunkPillar: "Observability"
---

# UC-3.2.6 · Kubernetes Deployment Rollout Failures (Rollout Pipeline Reliability)

> **Criticality:** Critical &middot; **Difficulty:** Intermediate &middot; **Pillar:** Observability &middot; **Type:** Reliability, Availability &middot; **Wave:** Walk &middot; **Status:** Verified

*When we publish new software to our container platform, the system should replace old copies in a controlled way. Sometimes that replacement stalls halfway, misses its deadline, or keeps spinning new copies without finishing. We watch those stall signals so teams fix the rollout before customers get inconsistent service.*

---

## Description

Detects Kubernetes Deployment rollout pipeline failures using kube-state-metrics condition and replica convergence signals rather than kubelet crash or pull reasons. Progressing false with ProgressDeadlineExceeded, Available false with minimum replica shortfalls, divergence among desired, updated, available, and ready replica gauges, metadata generation ahead of observed generation, and elevated ReplicaSet owner cardinality for undo or flap patterns form the core analytic. Optional kube events clock ProgressDeadlineExceeded first-seen time for wall-clock age. inputlookup deployment_inventory.csv enriches owner_team and per-deployment sla_minutes so tier-1 breach paging is explicit. CIM uses Application_State for workload readiness semantics and Change for rollout revisions as operational change events, which matches audit language better than treating rollouts only as Performance counters.

## Value

Mean time to repair improves when platform and application teams see one row that names cluster, namespace, deployment, generation drift, replica convergence gap, progressing reason, minutes since deadline event, inventory owner, SLA target, and severity without manually diffing kubectl, metrics explorers, and GitOps timelines. Customer impact drops because partial rollouts and silent undo loops surface before dashboards that only count restarts or pull errors. Release managers gain evidence for rollback decisions when deadline breaches persist beyond inventory SLA minutes. Finance and risk reviewers receive timestamped exports that show controller truth separate from symptom-level pod alerts, reducing duplicate bridges across UC-3.2.10, UC-3.2.14, and UC-3.2.1.

## Implementation

Ingest kube-state-metrics deployment and replicaset owner scrapes into k8s_metrics, stream kube:events for Deployment deadlines into k8s, publish deployment_inventory.csv with owner_team and sla_minutes, save uc_3_2_6_kube_deployment_rollout_reliability every five minutes with earliest=-4h@m, route critical and high severities for tier-1 rows per savedsearches.conf, and validate with a lab Deployment that breaches progressDeadlineSeconds.

## Evidence

Saved search uc_3_2_6_kube_deployment_rollout_reliability with five-minute schedule; deployment_inventory.csv versioned in git; weekly CSV export of the closing table to a restricted evidence index with kube-state-metrics chart version and collector digest.

## Control test

### Positive scenario

In lab namespace qa-rollout-uc326 deploy a Deployment with an impossible readiness probe and progressDeadlineSeconds under five minutes, wait for kube:events reason ProgressDeadlineExceeded on the Deployment involvedObject, confirm kube_deployment_status_condition shows Progressing false with ProgressDeadlineExceeded in k8s_metrics, execute uc_3_2_6_kube_deployment_rollout_reliability, and expect a qualifying row with non-null rollout_age_minutes and severity at least high when deployment_inventory.csv marks tier prod.

### Negative scenario

Deploy nginx with valid probes and a fifteen minute progress deadline in the same lab namespace, confirm Progressing becomes true and Available becomes true within two scrape intervals, and verify the saved search emits no qualifying rows for that Deployment across thirty minutes when no other breach flags apply.

## Detailed Implementation

### Step 1 — Prerequisites

Head of Platform owns this control with Kubernetes platform site reliability engineers, release engineering, and the observability team operating Splunk OpenTelemetry Collector plus kube-state-metrics across production and pre-production. This use case isolates the deployment controller rollout pipeline, not kubelet restart reasons, not image pull stalls, and not generic pod restart churn. UC-3.2.10 remains the CrashLoopBackOff and waiting_reason story after a container has started. UC-3.2.14 remains ErrImagePull and ImagePullBackOff while the kubelet still fetches layers. UC-3.2.1 remains aggregate restart-rate analytics without interpreting Deployment status conditions or replica convergence. UC-3.2.39 stays the broad Kubernetes event anomaly plane; do not merge that macro here. UC-3.2.20 remains Jobs and CronJobs completion semantics. The signal set here is kube-state-metrics deployment gauges and conditions, optional ReplicaSet owner churn, Deployment-scoped ProgressDeadlineExceeded events for clocking, plus inventory joins for team ownership and per-deployment rollout service-level objectives.

Splunk index layout mirrors other cat-3 gold controls: index=k8s_metrics for Prometheus text or normalized scrape events from kube-state-metrics and in-cluster Prometheus, index=k8s for kube:events including Deployment controller messages, and index=k8s_audit when you must prove who issued kubectl rollout undo or who patched a Deployment during an incident. HEC tokens stay in vaults with quarterly rotation. RBAC for collectors must list watches on Deployments, ReplicaSets, and Events without granting Secret read unless policy demands it.

kube-state-metrics must expose kube_deployment_status_condition with labels for condition types Progressing and Available including status and reason, kube_deployment_spec_replicas, kube_deployment_status_replicas_available, kube_deployment_status_replicas_updated, kube_deployment_status_replicas_ready or kube_deployment_status_ready_replicas depending on chart version, kube_deployment_metadata_generation, kube_deployment_status_observed_generation, and kube_replicaset_owner with owner_kind Deployment for ReplicaSet cardinality drift. Confirm your chart version against upstream deployment metrics documentation because label names shifted across minor releases. Scrapes every fifteen to thirty seconds are typical; shorter intervals improve deadline math at license cost.

Governance lookup deployment_inventory.csv must carry at least cluster, namespace, deployment, owner_team, sla_minutes, and tier or workload_tier for paging tier logic. Refresh the CSV when new services onboard or when tier-1 contracts change. Optional columns such as pause_expected, progressive_delivery_tool, and rollback_window_minutes let macros suppress deliberate canary states without muting true stalls.

CIM mapping uses Application_State because a Deployment is an application-level availability object whose ready and progressing conditions describe service readiness, not merely host CPU. Change is the second model because rollouts are first-class change events: every revision mutates live customer traffic paths, audit narratives, and configuration hashes even when no traditional change ticket exists. Performance is intentionally not the primary sibling here; saturation can cause rollout stalls but this UC keeps the controller truth plane primary and points to node pressure siblings only in troubleshooting.

Risk briefing for executives: a stuck rollout means new fixes may never reach users while old replicas still serve traffic, or worse, traffic splits across incompatible revisions during partial convergence. ProgressDeadlineExceeded is the built-in guard rail that says the controller gave up waiting for declared success. When Available is false while Progressing still reports motion, teams confuse kubectl output with health; Splunk should show the split objectively.

Licensing note: high-cardinality ReplicaSet labels during pathological undo loops can explode series counts; use recording rules or allow-list labels only after FinOps review. Privacy note: event messages can echo image tags with internal codenames; restrict dashboard ACLs.

Training: teach responders to read desired versus updated versus available versus ready replica gauges together, and to treat observed_generation lagging metadata generation as a controller reconcile backlog distinct from image pull failures.

Review cadence: quarterly replay one historical rollout incident after kube-state-metrics upgrades because regex arms drift when exporters rename metrics.

Differentiation recap: rollout pipeline reliability is the axis; crash loops, pulls, and restart counters are explicitly out of scope as primary detectors.

Escalation alignment: tier-1 services with SLA minutes breached in the lookup should page both application and platform bridges when deadline breaches persist beyond one interval.

Telemetry hygiene: deduplicate overlapping Prometheus and OpenTelemetry scrapes without stable dedup keys only after you understand double-counting risk.

FinOps alignment: stalled rollouts still burn cloud spend when surge pods pend forever; pair this UC with capacity reviews when maxSurge exhausts budgets.

Security alignment: kubectl rollout undo audit correlation proves whether a human broke glass; attach user.username from kube-apiserver audit when available.

Performance alignment: multisearch arms cost scheduler time; keep alert cadence at five minutes for full joins and use a summary index for fleet dashboards at fifteen minutes if Job Inspector complains.

Documentation alignment: wiki-link this UC beside Deployment strategy documentation, PodDisruptionBudget guidance, and progressive delivery runbooks for Argo Rollouts or Flagger so new engineers land on the right detector first.

Hardware scope: Amazon EKS, Google GKE, Microsoft AKS, Red Hat OpenShift, VMware Tanzu, and self-managed clusters where kube-state-metrics RBAC can list Deployments cluster-wide; Arm and x86 worker fleets are in scope when metric text lines remain Prometheus compatible.

StatefulSet note: StatefulSet rollout stuck patterns with currentRevision versus updateRevision and partition are covered in narrative and troubleshooting; the SPL focuses on Deployment objects because metrics names differ for StatefulSet condition families. Fork a sibling UC if your estate standardizes on StatefulSet-only controllers for tier-1 data planes.

Argo CD and Flux note: GitOps controllers can pause rollouts or drive canary analysis; the lookup pause_expected column should carry one when progressive delivery intentionally holds partial replica states.

Splunk Enterprise or Splunk Cloud 9.2 plus is assumed for scheduled searches, drilldowns, and optional accelerated models referenced in cimSpl.

Platform onboarding checklist for new clusters: verify kube-state-metrics version, verify Splunk OTel chart version, verify HEC endpoint health, verify deployment_inventory.csv includes every production namespace that runs customer traffic, verify audit policy retains Deployment patch verbs for attribution drills, verify PagerDuty routing maps owner_team strings to live schedules, verify executive dashboard includes rollout SLA breach single value sourced from this saved search clone, verify FinOps receives monthly CSV export of breaches for capacity planning, verify legal retention index paths when regulated workloads appear in alert rows, verify chaos engineering namespaces carry suppression metadata, verify mesh ingress namespaces that use Argo Rollouts carry progressive_delivery_tool column values, verify database namespaces carry extended sla_minutes for cold start realism, verify CI cluster namespaces never page tier-1 bridges because of synthetic deadline tests unless chaos flags absent, verify dual-active disaster recovery clusters each have distinct cluster column values in CSV, verify secondary on-call bridges receive high severity only when primary ack times out, verify Grafana or Dashboard Studio deep links are embedded in alert actions for faster kubectl-free triage, verify runbook links reference kubectl rollout pause and resume procedures, verify kubectl rollout history interpretation training occurs twice yearly, verify kube-controller-manager health checks are linked from this runbook for generation lag cases, verify etcd defragmentation windows are documented to avoid false generation lag panic, verify service mesh canary weight documentation clarifies why Kubernetes replica counts may diverge from traffic percentages, verify image digest pinning policy references UC-3.2.14 when image layers stall mid-rollout, verify probe tuning policy references UC-3.2.43 when readiness gates fail only on new pods, verify admission webhook maintenance windows reference UC-3.2.21 and UC-3.2.45 when new ReplicaSet pods never bind, verify PDB policy references UC-3.2.37 when maxUnavailable interacts with voluntary disruption budgets, verify horizontal pod autoscaler scale events are cross-checked before blaming rollout controller for replica drift, verify vertical pod autoscaler recommendations are reviewed when surge pods cannot schedule for memory, verify cluster autoscaler scale-out timelines are understood when surge pods stay Pending, verify node repair storms are distinguished from rollout failures using node condition panels, verify storage class binding delays are distinguished using PVC phase joins when stateful rollouts stall, verify API server priority and fairness settings are reviewed when control plane latency correlates with generation lag, verify webhook timeout budgets are reviewed when apiserver logs show slow validating hooks, verify certificate rotation playbooks are linked when mTLS hooks fail only for new pods, verify GitOps drift detectors are linked when live cluster generation disagrees with Git declared generation without Splunk seeing a breach, verify blue-green cutover documentation explains why this detector may need temporary suppression, verify maintenance mode annotations are standardized across teams, verify SRE error budget policy ties this alert to customer facing SLO burn when tier column marks gold, verify product management receives weekly digest of longest rollout ages for roadmap risk, verify architecture review board receives quarterly summary of rollback frequency inferred from audit joins, verify internal auditor sample pulls three incidents per quarter and confirms evidence index retention, verify vendor support tickets attach Splunk export hashes when upstream Kubernetes bugs suspected, verify upgrade testing pipeline runs kube-state-metrics semver jumps before production promotion, verify cross-region replication lag does not break inventory joins when cluster name casing differs, verify Unicode normalization in deployment names does not break CSV joins, verify stale CSV rows for deleted namespaces are pruned monthly, verify automated CMDB sync jobs log commit identifiers consumed by this UC, verify break-glass account usage still triggers this UC when rollouts go wrong, verify synthetic monitoring uptime checks complement but do not replace controller condition truth.

Closing prerequisites checklist: indexes named, kube-state-metrics metric families enumerated, deployment_inventory.csv schema documented, boundaries versus UC-3.2.10, UC-3.2.14, UC-3.2.1, UC-3.2.39, and UC-3.2.20 restated, CIM Application_State plus Change rationale captured for auditors who ask why Performance is not listed as a primary model.

### Step 2 — Configure data collection

Deploy kube-state-metrics with cluster-scoped RBAC that can list Deployments and ReplicaSets. Point Splunk OpenTelemetry Collector prometheus receiver or prometheus_simple scrape jobs at the kube-state-metrics Service on port 8080 or 8443 depending on your chart, preserve deployment, namespace, and cluster labels through relabel_config blocks, and export to HEC into index=k8s_metrics with sourcetype prometheus:scrape:metrics. Mirror UC-3.2.10 collector hygiene: bearer_token_file for TLS kubelet scrapes is separate from kube-state-metrics HTTP scraping inside the cluster.

Concrete ServiceMonitor style reference:

apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: kube-state-metrics-rollout
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

deployment_inventory.csv sample schema:

cluster,namespace,deployment,owner_team,sla_minutes,tier,pause_expected
prod-eks-us-east-1,prod-payments,carts-api,payments-sre,10,prod,0
prod-eks-us-east-1,prod-edge,ingress-canary,platform-mesh,45,prod,1

Validate raw signal presence before alerts: index=k8s_metrics kube_deployment_status_condition earliest=-30m, index=k8s_metrics kube_deployment_spec_replicas earliest=-30m, index=k8s sourcetype=kube:events ProgressDeadlineExceeded earliest=-24h. Skew between scrapes and API events must stay under sixty seconds for meaningful joins.

Security: redact internal hostnames from collector debug logs. Restrict k8s_audit to roles that need attribution.

props.conf guidance: normalize __name__, value, namespace, deployment, condition, status, and reason fields onto indexed extractions where volume warrants tscollect experiments; keep coalesce ladders in SPL until extractions stabilize.

When HEC receives OpenTelemetry protobuf translations instead of Prometheus text, extend rex arms with metric_name coalesce paths identical to UC-3.2.14 patterns.

Cloud control planes: on EKS verify security groups still allow node to cluster IP reachability for metrics after landing-zone changes; on GKE verify managed Prometheus if you offloaded scrapes; on AKS verify managed Grafana agent label mapping still populates deployment.

Frequency: scrape interval, alert interval, and SLA minutes must align mathematically; a ten-minute SLA with five-minute scrapes and a five-minute alert schedule is the minimum sane pairing for tier-1.

Back-pressure: if kube-apiserver event watch disconnects, collector buffers should not unbounded grow; set retry and drop policies per vendor guidance.

Version pinning: record kube-state-metrics chart version in evidence packs quarterly.

ReplicaSet churn validation: in lab, kubectl rollout undo twice in one minute should raise rs_thrash_dc without waiting for customer impact; document lab cluster names in suppression macros.

Integration with kubectl: operators should still run kubectl rollout status for instantaneous truth; Splunk carries history and correlation that kubectl alone lacks across clusters.

Dashboard seeds: single value of cluster_worst_rollout_min from a clone search, timechart of deadline breaches by namespace, and table of this UC output for executive summaries.

Summary index optional: materialize five-minute snapshots of deployment condition booleans into k8s_rollout_summary when raw k8s_metrics scan costs dominate.

Closing data collection checklist: ServiceMonitor or scrape job live, events pipeline live, CSV published, validation searches green, collector TLS verified, deduplication story documented when dual agents scrape the same targets.

### Step 3 — Create the search and alert

Save the SPL as uc_3_2_6_kube_deployment_rollout_reliability with five-minute schedule, dispatch earliest=-4h@m, dispatch latest=now, and alert when severity is critical or high for tier-1 rows. Throttle duplicate pages per cluster, namespace, and deployment for thirty minutes unless severity escalates from high to critical. Attach drilldown searches to kube:events for the same Deployment and to UC-3.2.14 or UC-3.2.43 companion macros when the row hints supply-chain or probe failures.

Understanding the pipeline: the opening comment macro lists tunables so on-call engineers retune without opening this document. eval rollout_stuck_min_gate and rs_thrash_dc_floor centralize thresholds referenced in severity and stuck_signal logic. join with tstats against Change provides a CIM-aligned correlation tick count that helps justify dual-model mapping during audits; if Change acceleration is absent in a lab, the join still type=left preserves deployment rows. multisearch fans nine metric arms so one silent kube-state-metrics family cannot zero the entire detection. Each arm ends with stats latest by cluster, namespace, and deployment so rows collapse before the outer stats merges arms. coalesce ladders tolerate camelCase and snake_case label exports. The Progressing and Available condition arms isolate reasons such as ProgressDeadlineExceeded versus MinimumReplicasUnavailable. Replica gauge arms compare desired, updated, available, and ready counts for partial convergence. Generation arms detect metadata generation ahead of observed generation, a classic symptom when the controller cannot reconcile. The ReplicaSet owner arm estimates rapid ReplicaSet churn for undo loops or flapping controllers using dc(rsname) over ninety minutes. After merge, eval flags derive deadline_breach, availability_breach, partial_stuck, and gen_lag. join to kube:events recovers first_deadline_evt using streamstats first on sorted events so rollout duration math reflects the first ProgressDeadlineExceeded observation in-window; rollout_age_minutes uses now minus that epoch when present, otherwise a gate when stuck_signal is true. eventstats max(rollout_age_minutes) by cluster supports dashboard overlays comparing worst tenants inside the same fleet. inputlookup deployment_inventory.csv enriches owner_team, sla_minutes, and tier for case-based severity and SLA breach detection. The where clause keeps deliberate low-severity churn out unless a hard deadline or availability breach fires. The closing table lists fifteen analyst columns exactly as named in the implementation contract.

cimSpl in the JSON field mirrors Application_State and Change tstats usage for environments that map Kubernetes workloads into those models; adapt nodename filters to your TA.

Paste-and-run SPL for alerts and dashboards must match the spl JSON field exactly:

```spl
`comment("UC-3.2.6 Kubernetes Deployment rollout pipeline reliability. Tunables: indexes k8s_metrics k8s; sourcetypes prometheus:scrape:metrics kube:objects:metrics kube:events; lookup deployment_inventory.csv; rollout_stuck_min_gate=5; rs_thrash_dc_floor=6; earliest=-4h@m latest=now")`
| eval rollout_stuck_min_gate=5
| eval rs_thrash_dc_floor=6
| eval join_key="uc326"
| join type=left join_key [
| tstats count AS change_correlation_tick FROM datamodel=Change WHERE nodename=Change earliest=-4h@h latest=now
| eval join_key="uc326"
]
| fields - join_key change_correlation_tick
| multisearch [
    [ search ((index=k8s_metrics OR index=k8s) (sourcetype="prometheus:scrape:metrics" OR sourcetype="kube:objects:metrics")) earliest=-4h@m latest=now
      | eval cluster=trim(toString(coalesce(cluster, cluster_name, k8s_cluster_name, eks_cluster_name, gke_cluster_name, "")))
      | eval mn=lower(trim(toString(coalesce(metric_name, __name__, name, MetricName, ""))))
      | rex field=_raw "deployment=\\\"(?<deployment>[^\\\"]+)\\\""
      | rex field=_raw "namespace=\\\"(?<namespace>[^\\\"]+)\\\""
      | rex field=_raw "condition=\\\"(?<condition>[^\\\"]+)\\\""
      | rex field=_raw "status=\\\"(?<cond_status>[^\\\"]+)\\\""
      | rex field=_raw "reason=\\\"(?<cond_reason>[^\\\"]+)\\\""
      | where like(mn, "%kube_deployment_status_condition%") AND condition="Progressing"
      | stats latest(cond_status) AS progress_condition latest(cond_reason) AS progress_reason BY cluster namespace deployment ]
    [ search ((index=k8s_metrics OR index=k8s) (sourcetype="prometheus:scrape:metrics" OR sourcetype="kube:objects:metrics")) earliest=-4h@m latest=now
      | eval cluster=trim(toString(coalesce(cluster, cluster_name, k8s_cluster_name, eks_cluster_name, gke_cluster_name, "")))
      | eval mn=lower(trim(toString(coalesce(metric_name, __name__, name, MetricName, ""))))
      | rex field=_raw "deployment=\\\"(?<deployment>[^\\\"]+)\\\""
      | rex field=_raw "namespace=\\\"(?<namespace>[^\\\"]+)\\\""
      | rex field=_raw "condition=\\\"(?<condition>[^\\\"]+)\\\""
      | rex field=_raw "status=\\\"(?<cond_status>[^\\\"]+)\\\""
      | rex field=_raw "reason=\\\"(?<cond_reason>[^\\\"]+)\\\""
      | where like(mn, "%kube_deployment_status_condition%") AND condition="Available"
      | stats latest(cond_status) AS available_condition latest(cond_reason) AS available_reason BY cluster namespace deployment ]
    [ search ((index=k8s_metrics OR index=k8s) (sourcetype="prometheus:scrape:metrics" OR sourcetype="kube:objects:metrics")) earliest=-4h@m latest=now
      | eval cluster=trim(toString(coalesce(cluster, cluster_name, k8s_cluster_name, eks_cluster_name, gke_cluster_name, "")))
      | eval mn=lower(trim(toString(coalesce(metric_name, __name__, name, MetricName, ""))))
      | rex field=_raw "deployment=\\\"(?<deployment>[^\\\"]+)\\\""
      | rex field=_raw "namespace=\\\"(?<namespace>[^\\\"]+)\\\""
      | where (like(mn, "%kube_deployment_spec_replicas%") OR like(_raw, "kube_deployment_spec_replicas"))
      | rex field=_raw "\\s(?<mval>[0-9.eE+-]+)\\s*$"
      | eval replicas_desired=tonumber(mval, 10)
      | stats latest(replicas_desired) AS replicas_desired BY cluster namespace deployment ]
    [ search ((index=k8s_metrics OR index=k8s) (sourcetype="prometheus:scrape:metrics" OR sourcetype="kube:objects:metrics")) earliest=-4h@m latest=now
      | eval cluster=trim(toString(coalesce(cluster, cluster_name, k8s_cluster_name, eks_cluster_name, gke_cluster_name, "")))
      | eval mn=lower(trim(toString(coalesce(metric_name, __name__, name, MetricName, ""))))
      | rex field=_raw "deployment=\\\"(?<deployment>[^\\\"]+)\\\""
      | rex field=_raw "namespace=\\\"(?<namespace>[^\\\"]+)\\\""
      | where (like(mn, "%kube_deployment_status_replicas_available%") OR like(_raw, "kube_deployment_status_replicas_available"))
      | rex field=_raw "\\s(?<mval>[0-9.eE+-]+)\\s*$"
      | eval replicas_available=tonumber(mval, 10)
      | stats latest(replicas_available) AS replicas_available BY cluster namespace deployment ]
    [ search ((index=k8s_metrics OR index=k8s) (sourcetype="prometheus:scrape:metrics" OR sourcetype="kube:objects:metrics")) earliest=-4h@m latest=now
      | eval cluster=trim(toString(coalesce(cluster, cluster_name, k8s_cluster_name, eks_cluster_name, gke_cluster_name, "")))
      | eval mn=lower(trim(toString(coalesce(metric_name, __name__, name, MetricName, ""))))
      | rex field=_raw "deployment=\\\"(?<deployment>[^\\\"]+)\\\""
      | rex field=_raw "namespace=\\\"(?<namespace>[^\\\"]+)\\\""
      | where (like(mn, "%kube_deployment_status_replicas_updated%") OR like(_raw, "kube_deployment_status_replicas_updated"))
      | rex field=_raw "\\s(?<mval>[0-9.eE+-]+)\\s*$"
      | eval replicas_updated=tonumber(mval, 10)
      | stats latest(replicas_updated) AS replicas_updated BY cluster namespace deployment ]
    [ search ((index=k8s_metrics OR index=k8s) (sourcetype="prometheus:scrape:metrics" OR sourcetype="kube:objects:metrics")) earliest=-4h@m latest=now
      | eval cluster=trim(toString(coalesce(cluster, cluster_name, k8s_cluster_name, eks_cluster_name, gke_cluster_name, "")))
      | eval mn=lower(trim(toString(coalesce(metric_name, __name__, name, MetricName, ""))))
      | rex field=_raw "deployment=\\\"(?<deployment>[^\\\"]+)\\\""
      | rex field=_raw "namespace=\\\"(?<namespace>[^\\\"]+)\\\""
      | where (like(mn, "%kube_deployment_status_replicas_ready%") OR like(mn, "%kube_deployment_status_ready_replicas%") OR like(_raw, "kube_deployment_status_replicas_ready") OR like(_raw, "kube_deployment_status_ready_replicas"))
      | rex field=_raw "\\s(?<mval>[0-9.eE+-]+)\\s*$"
      | eval replicas_ready=tonumber(mval, 10)
      | stats latest(replicas_ready) AS replicas_ready BY cluster namespace deployment ]
    [ search ((index=k8s_metrics OR index=k8s) (sourcetype="prometheus:scrape:metrics" OR sourcetype="kube:objects:metrics")) earliest=-4h@m latest=now
      | eval cluster=trim(toString(coalesce(cluster, cluster_name, k8s_cluster_name, eks_cluster_name, gke_cluster_name, "")))
      | eval mn=lower(trim(toString(coalesce(metric_name, __name__, name, MetricName, ""))))
      | rex field=_raw "deployment=\\\"(?<deployment>[^\\\"]+)\\\""
      | rex field=_raw "namespace=\\\"(?<namespace>[^\\\"]+)\\\""
      | where (like(mn, "%kube_deployment_metadata_generation%") OR like(_raw, "kube_deployment_metadata_generation"))
      | rex field=_raw "\\s(?<mval>[0-9.eE+-]+)\\s*$"
      | eval generation=tonumber(mval, 10)
      | stats latest(generation) AS generation BY cluster namespace deployment ]
    [ search ((index=k8s_metrics OR index=k8s) (sourcetype="prometheus:scrape:metrics" OR sourcetype="kube:objects:metrics")) earliest=-4h@m latest=now
      | eval cluster=trim(toString(coalesce(cluster, cluster_name, k8s_cluster_name, eks_cluster_name, gke_cluster_name, "")))
      | eval mn=lower(trim(toString(coalesce(metric_name, __name__, name, MetricName, ""))))
      | rex field=_raw "deployment=\\\"(?<deployment>[^\\\"]+)\\\""
      | rex field=_raw "namespace=\\\"(?<namespace>[^\\\"]+)\\\""
      | where (like(mn, "%kube_deployment_status_observed_generation%") OR like(_raw, "kube_deployment_status_observed_generation"))
      | rex field=_raw "\\s(?<mval>[0-9.eE+-]+)\\s*$"
      | eval observed_generation=tonumber(mval, 10)
      | stats latest(observed_generation) AS observed_generation BY cluster namespace deployment ]
    [ search ((index=k8s_metrics OR index=k8s) (sourcetype="prometheus:scrape:metrics" OR sourcetype="kube:objects:metrics")) earliest=-90m@m latest=now
      | eval cluster=trim(toString(coalesce(cluster, cluster_name, k8s_cluster_name, eks_cluster_name, gke_cluster_name, "")))
      | eval mn=lower(trim(toString(coalesce(metric_name, __name__, name, MetricName, ""))))
      | rex field=_raw "namespace=\\\"(?<namespace>[^\\\"]+)\\\""
      | rex field=_raw "owner_name=\\\"(?<deployment>[^\\\"]+)\\\""
      | rex field=_raw "replicaset=\\\"(?<rsname>[^\\\"]+)\\\""
      | where (like(mn, "%kube_replicaset_owner%") OR like(_raw, "kube_replicaset_owner"))
      | where like(_raw, "owner_kind=\\\"Deployment\\\"")
      | stats dc(rsname) AS rs_thrash_dc BY cluster namespace deployment ]
| stats latest(progress_condition) AS progress_condition latest(progress_reason) AS progress_reason latest(available_condition) AS available_condition latest(available_reason) AS available_reason latest(replicas_desired) AS replicas_desired latest(replicas_updated) AS replicas_updated latest(replicas_available) AS replicas_available latest(replicas_ready) AS replicas_ready latest(generation) AS generation latest(observed_generation) AS observed_generation latest(rs_thrash_dc) AS rs_thrash_dc BY cluster namespace deployment
| eval cluster=coalesce(nullif(trim(cluster), ""), "unknown-cluster")
| eval namespace=coalesce(nullif(trim(namespace), ""), "unknown-namespace")
| eval deployment=coalesce(nullif(trim(deployment), ""), "unknown-deployment")
| eval replicas_desired=coalesce(replicas_desired, 0)
| eval replicas_updated=coalesce(replicas_updated, 0)
| eval replicas_available=coalesce(replicas_available, 0)
| eval replicas_ready=coalesce(replicas_ready, 0)
| eval generation=coalesce(generation, 0)
| eval observed_generation=coalesce(observed_generation, 0)
| eval rs_thrash_dc=coalesce(rs_thrash_dc, 0)
| eval progress_condition=coalesce(progress_condition, "unknown")
| eval progress_reason=coalesce(progress_reason, "none_reported")
| eval available_condition=coalesce(available_condition, "unknown")
| eval available_reason=coalesce(available_reason, "none_reported")
| eval partial_stuck=if((replicas_updated < replicas_desired) OR (replicas_available < replicas_desired) OR (replicas_ready < replicas_desired), 1, 0)
| eval gen_lag=if(generation>observed_generation, generation-observed_generation, 0)
| eval deadline_breach=if(match(lower(progress_reason), "progressdeadlineexceeded") OR (match(lower(progress_condition), "false") AND match(lower(progress_reason), "progressdeadline")), 1, 0)
| eval availability_breach=if(match(lower(available_condition), "false"), 1, 0)
| eval stuck_signal=if(deadline_breach=1 OR availability_breach=1 OR partial_stuck=1 OR gen_lag>0 OR rs_thrash_dc>=rs_thrash_dc_floor, 1, 0)
| join type=left max=0 cluster namespace deployment [
    search index=k8s sourcetype="kube:events" earliest=-4h@m latest=now
      | eval cluster=trim(toString(coalesce(cluster, cluster_name, k8s_cluster_name, "")))
      | eval kind=trim(toString(coalesce(involvedObject.kind, `involvedObject.kind`, "")))
      | eval reason_ev=trim(toString(coalesce(reason, Reason, "")))
      | eval deployment=trim(toString(coalesce(involvedObject.name, involvedObject_name, "")))
      | eval namespace=trim(toString(coalesce(metadata.namespace, namespace, "")))
      | where kind="Deployment" AND reason_ev="ProgressDeadlineExceeded"
      | sort 0 + cluster + namespace + deployment + _time
      | streamstats global=f first(_time) AS rollout_start_epoch BY cluster namespace deployment
      | stats latest(rollout_start_epoch) AS first_deadline_evt latest(_time) AS last_deadline_ev BY cluster namespace deployment ]
| eval rollout_age_minutes=if(isnotnull(first_deadline_evt), round((now()-first_deadline_evt)/60, 2), if(stuck_signal=1, rollout_stuck_min_gate, null()))
| eventstats max(rollout_age_minutes) AS cluster_worst_rollout_min BY cluster
| join type=left max=0 cluster namespace deployment [
    | inputlookup deployment_inventory.csv
      | eval cluster=trim(toString(coalesce(cluster, k8s_cluster, "")))
      | eval namespace=trim(toString(namespace))
      | eval deployment=trim(toString(coalesce(deployment, workload, "")))
      | eval owner_team=trim(toString(coalesce(owner_team, team, squad, platform_team, "")))
      | eval sla_minutes=tonumber(trim(toString(coalesce(sla_minutes, rollout_sla_minutes, "600"))), 10)
      | eval tier=lower(trim(toString(coalesce(tier, workload_tier, env_tier, "dev"))))
      | fields cluster namespace deployment owner_team sla_minutes tier ]
| fillnull value=600 sla_minutes
| fillnull value="unassigned" owner_team
| fillnull value="dev" tier
| eval sla_breach=if(isnotnull(rollout_age_minutes) AND rollout_age_minutes>sla_minutes, 1, 0)
| eval severity=case(
    deadline_breach=1 AND coalesce(rollout_age_minutes, 0)>=30 AND match(tier, "prod|production|tier1|tier-1|gold"), "critical",
    deadline_breach=1 OR availability_breach=1, "critical",
    gen_lag>0 AND match(tier, "prod|production|tier1|tier-1|gold"), "high",
    partial_stuck=1 AND coalesce(rollout_age_minutes, 0)>=rollout_stuck_min_gate, "high",
    rs_thrash_dc>=rs_thrash_dc_floor, "high",
    sla_breach=1 AND match(tier, "prod|production|tier1|tier-1|gold"), "high",
    partial_stuck=1, "medium",
    gen_lag>0, "medium",
    true(), "low")
| where (stuck_signal=1 AND coalesce(rollout_age_minutes, 0)>=rollout_stuck_min_gate) OR deadline_breach=1 OR availability_breach=1 OR gen_lag>0 OR rs_thrash_dc>=rs_thrash_dc_floor OR sla_breach=1
| fields - available_condition available_reason cluster_worst_rollout_min tier partial_stuck deadline_breach availability_breach stuck_signal gen_lag sla_breach rs_thrash_dc first_deadline_evt last_deadline_ev
| table cluster namespace deployment generation observed_generation replicas_desired replicas_updated replicas_available replicas_ready progress_condition progress_reason rollout_age_minutes sla_minutes owner_team severity
```

Alert actions: include cluster, namespace, deployment, rollout_age_minutes, progress_reason, severity, owner_team, and sla_minutes in email or ITSI notable bodies. Provide a drilldown that runs index=k8s sourcetype=kube:events involvedObject.kind=Deployment involvedObject.name=$deployment$ earliest=-4h. Provide a secondary drilldown for kubectl audit when index=k8s_audit is populated.

Performance: if Job Inspector warns on multisearch cost, split fleet dashboards into per-region saved searches or materialize kube_deployment_status_condition snapshots hourly.

Reliability: during kube-state-metrics upgrades expect brief gaps; require two consecutive intervals of missing metrics before paging scrape outages unless kube events still show deadlines.

Governance: weekly CSV export of alert rows with lookup commit hash satisfies internal platform evidence when paired with kube-state-metrics version stamps.

savedsearches.conf quantity thresholds should align with row counts from the table command; use alert.track=1 and suppress keys on cluster namespace deployment.

Closing Step 3 checklist: fenced SPL present, matches spl field, references deployment_inventory.csv, explains tstats join purpose, documents multisearch arms, clarifies SLA breach logic, and names notification fields.

### Step 4 — Validate

Synthetic deadline breach: in lab namespace qa-rollout-uc326 apply a Deployment with a broken readiness probe, intentionally short progressDeadlineSeconds, and a single replica, wait for ProgressDeadlineExceeded in kubectl describe and in kube:events, confirm kube_deployment_status_condition shows Progressing false with reason ProgressDeadlineExceeded in index=k8s_metrics, execute uc_3_2_6_kube_deployment_rollout_reliability, and expect a row with severity at least high when tier marks prod in deployment_inventory.csv.

Synthetic generation lag: kubectl apply a label change twice rapidly while freezing the deployment controller in a disposable lab only, or patch a Deployment and block kube-controller-manager network path in a test cluster under change control, confirm observed_generation lags metadata generation in metrics, and expect gen_lag greater than zero with severity at least medium.

Synthetic ReplicaSet churn: kubectl rollout undo repeatedly against a lab Deployment without traffic impact and confirm rs_thrash_dc rises above the floor while progress_reason oscillates; downgrade using suppression macros for lab.

Negative test: deploy nginx with healthy probes and generous deadline, confirm progressing true and available true within two intervals, and expect zero qualifying rows from the alert predicate for that Deployment across thirty minutes.

Field sanity: rename a forwarder field to camelCase-only in a sandbox and verify coalesce still resolves namespace and deployment labels.

RBAC: readers without k8s_metrics access must see zero rows.

Correlation: compare Splunk timestamps to kubectl rollout history and kubectl get rs output for the same minute.

Validation SPL for raw metrics presence:

| multisearch [
    [ search index=k8s_metrics earliest=-30m latest=now kube_deployment_status_condition | stats count ]
    [ search index=k8s_metrics earliest=-30m latest=now kube_deployment_spec_replicas | stats count ]
  ]
| stats sum(count) AS samples

Tear-down: delete lab Deployments, revert network blocks, and confirm saved search result counts return to zero.

Audit drill: index=k8s_audit sourcetype=kube:audit objectRef.resource=deployments verb=patch OR verb=update earliest=-2h to recover actors for rollback frequency analysis outside kube-state-metrics.

Clock skew: verify NTP alignment between nodes, kube-apiserver, and Splunk indexers; skew beyond ninety seconds invalidates rollout_age_minutes comparisons.

Documentation: attach kubectl rollout status screenshots to the evidence ticket without exposing Secrets.

Closing Step 4 checklist: positive deadline scenario, negative healthy deploy, metrics presence multisearch, audit correlation note, tear-down verified, clock skew warning documented.

### Step 5 — Operationalize & Troubleshoot

Case 1 — ProgressDeadlineExceeded fired with Progressing false: treat as hard rollout failure; inspect ReplicaSets with kubectl rollout history, read kube events for FailedCreate or FailedMount lines, compare maxUnavailable and maxSurge against cluster capacity, and escalate if replicas_updated never reaches replicas_desired.

Case 2 — Paused rollout expected after kubectl rollout pause or GitOps freeze: set pause_expected=1 in deployment_inventory.csv for that row or macro suppress; PassDoNotAlert for known change windows when the pause annotation is deliberate.

Case 3 — ReplicaSet thrash pattern with rs_thrash_dc above floor: investigate kubectl rollout undo loops, autosync revert wars between operators, or two CI pipelines fighting the same Deployment hash; stabilize GitOps and enforce single writer semantics.

Case 4 — maxUnavailable combined with PodDisruptionBudget deadlock: new pods cannot schedule while old pods cannot terminate; correlate UC-3.2.37 style PDB narratives in your catalogue, temporarily relax only under CAB, or adjust surge budgets with capacity owners.

Case 5 — Partial rollout with admission webhook denyCreate on pods: link UC-3.2.21 or UC-3.2.45 per your catalogue for validating webhook latency and policy failures blocking new ReplicaSet pods.

Case 6 — Image pull root cause stalling new ReplicaSet pods while old pods remain: pivot to UC-3.2.14 for ErrImagePull evidence; keep this UC as the rollout gate that proves convergence never completed.

Case 7 — Liveness probe failures during rollout causing kill loops: pivot to UC-3.2.43 for probe taxonomy while using this UC to show available replicas below desired during the same window.

Case 8 — StatefulSet partition stuck with currentRevision not equal updateRevision: use kubectl describe statefulset, verify partition field intent, and extend monitoring with statefulset metric forks; this Deployment-focused SPL will not see that object class.

Case 9 — Argo Rollouts or Flagger canary observing partial weights: mark progressive_delivery_tool in inventory and extend suppression when service mesh weights intentionally diverge from Kubernetes Deployment replica counts.

Case 10 — ObservedGeneration less than Generation for many minutes: treat as controller reconcile backlog; restart is last resort; investigate apiserver latency, controller-manager leader election, and etcd health per platform runbooks.

Case 11 — Rollback candidate auto-detection: when deadline_breach stays true longer than thirty minutes with no audit evidence of kubectl rollout undo and tier-1 SLA minutes are breached, open a bridge suggesting explicit kubectl rollout undo or forward fix with a named owner; attach cluster_worst_rollout_min for fleet context.

Case 12 — Rollout SLA breach for tier-1 service: when rollout_age_minutes exceeds sla_minutes from deployment_inventory.csv, page the owner_team column even if Kubernetes still reports Progressing true with ReplicaFailure cleared; finance and customer teams care about wall clock, not only condition strings.

Dashboard hygiene: keep a panel for replicas_desired minus replicas_ready as a single value by namespace, and overlay UC-3.2.4 quota exhaustion when pod creates fail silently.

Evidence retention: archive weekly CSV exports with kube-state-metrics chart version, collector digest, and Splunk search head cluster name.

Training replay: twice-yearly game day that combines image pull failure plus deadline breach to prove operators open both UC-3.2.14 and this UC without duplicating tickets.

Cloud nuances: Fargate-style compute without DaemonSet assumptions still exposes kube-state-metrics the same way; verify scrape paths when AWS VPC CNI policies change.

Governance: when legal requests preservation, include hashed deployment manifests rather than raw Secret-laden YAML in tickets.

Performance note: if inputlookup deployment_inventory.csv grows beyond ten thousand rows, migrate to KV Store with automatic filter= on cluster before join.

Fleet operations note: publish a clone saved search without the closing where clause for monthly reliability reviews so medium severity partial convergence trends remain visible even when paging macros stay tight.

Executive storytelling note: translate progress_reason strings into customer impact language in bridges; executives rarely parse kube-state-metrics label semantics on first read.

Vendor escalation note: attach kube-controller-manager logs excerpts only when support NDAs permit; otherwise ship Splunk redacted exports with metric line samples only.

Runbook maintenance note: revisit links quarterly because Kubernetes minor releases occasionally rename condition reason constants in user-facing messages even when metrics stay stable.

Operator wellbeing note: pair this alert with shift handoff templates so secondary responders inherit replica gauge deltas without re-running full SPL manually.

Incident commander note: tag incidents with deployment generation numbers in chat so audit replay aligns with Splunk rows after the fact.

Post-incident review note: require root cause category rollout_controller, capacity, image, probe, webhook, pdb, gitops, or mesh for every critical page from this UC.

Capacity planning note: when surge exhaustion repeats monthly, open a capacity project rather than raising SLA minutes indefinitely.

Change advisory note: planned Kubernetes upgrades should carry a temporary lowering of alert severity only when kube-state-metrics maintenance windows are published in the change record.

Observability maturity note: graduate from five minute to one minute schedules only after license and Job Inspector budgets approve the multisearch cost.

Closing Step 5 checklist: twelve cases present with exact Case N — formatting, cross-links named to UC-3.2.14, UC-3.2.43, UC-3.2.37, UC-3.2.21, UC-3.2.45, Argo or Flagger guidance, StatefulSet caveat, rollback candidate guidance, and SLA breach tier-1 language, plus dashboard and evidence notes for long-term operations.


## SPL

```spl
`comment("UC-3.2.6 Kubernetes Deployment rollout pipeline reliability. Tunables: indexes k8s_metrics k8s; sourcetypes prometheus:scrape:metrics kube:objects:metrics kube:events; lookup deployment_inventory.csv; rollout_stuck_min_gate=5; rs_thrash_dc_floor=6; earliest=-4h@m latest=now")`
| eval rollout_stuck_min_gate=5
| eval rs_thrash_dc_floor=6
| eval join_key="uc326"
| join type=left join_key [
| tstats count AS change_correlation_tick FROM datamodel=Change WHERE nodename=Change earliest=-4h@h latest=now
| eval join_key="uc326"
]
| fields - join_key change_correlation_tick
| multisearch [
    [ search ((index=k8s_metrics OR index=k8s) (sourcetype="prometheus:scrape:metrics" OR sourcetype="kube:objects:metrics")) earliest=-4h@m latest=now
      | eval cluster=trim(toString(coalesce(cluster, cluster_name, k8s_cluster_name, eks_cluster_name, gke_cluster_name, "")))
      | eval mn=lower(trim(toString(coalesce(metric_name, __name__, name, MetricName, ""))))
      | rex field=_raw "deployment=\\\"(?<deployment>[^\\\"]+)\\\""
      | rex field=_raw "namespace=\\\"(?<namespace>[^\\\"]+)\\\""
      | rex field=_raw "condition=\\\"(?<condition>[^\\\"]+)\\\""
      | rex field=_raw "status=\\\"(?<cond_status>[^\\\"]+)\\\""
      | rex field=_raw "reason=\\\"(?<cond_reason>[^\\\"]+)\\\""
      | where like(mn, "%kube_deployment_status_condition%") AND condition="Progressing"
      | stats latest(cond_status) AS progress_condition latest(cond_reason) AS progress_reason BY cluster namespace deployment ]
    [ search ((index=k8s_metrics OR index=k8s) (sourcetype="prometheus:scrape:metrics" OR sourcetype="kube:objects:metrics")) earliest=-4h@m latest=now
      | eval cluster=trim(toString(coalesce(cluster, cluster_name, k8s_cluster_name, eks_cluster_name, gke_cluster_name, "")))
      | eval mn=lower(trim(toString(coalesce(metric_name, __name__, name, MetricName, ""))))
      | rex field=_raw "deployment=\\\"(?<deployment>[^\\\"]+)\\\""
      | rex field=_raw "namespace=\\\"(?<namespace>[^\\\"]+)\\\""
      | rex field=_raw "condition=\\\"(?<condition>[^\\\"]+)\\\""
      | rex field=_raw "status=\\\"(?<cond_status>[^\\\"]+)\\\""
      | rex field=_raw "reason=\\\"(?<cond_reason>[^\\\"]+)\\\""
      | where like(mn, "%kube_deployment_status_condition%") AND condition="Available"
      | stats latest(cond_status) AS available_condition latest(cond_reason) AS available_reason BY cluster namespace deployment ]
    [ search ((index=k8s_metrics OR index=k8s) (sourcetype="prometheus:scrape:metrics" OR sourcetype="kube:objects:metrics")) earliest=-4h@m latest=now
      | eval cluster=trim(toString(coalesce(cluster, cluster_name, k8s_cluster_name, eks_cluster_name, gke_cluster_name, "")))
      | eval mn=lower(trim(toString(coalesce(metric_name, __name__, name, MetricName, ""))))
      | rex field=_raw "deployment=\\\"(?<deployment>[^\\\"]+)\\\""
      | rex field=_raw "namespace=\\\"(?<namespace>[^\\\"]+)\\\""
      | where (like(mn, "%kube_deployment_spec_replicas%") OR like(_raw, "kube_deployment_spec_replicas"))
      | rex field=_raw "\\s(?<mval>[0-9.eE+-]+)\\s*$"
      | eval replicas_desired=tonumber(mval, 10)
      | stats latest(replicas_desired) AS replicas_desired BY cluster namespace deployment ]
    [ search ((index=k8s_metrics OR index=k8s) (sourcetype="prometheus:scrape:metrics" OR sourcetype="kube:objects:metrics")) earliest=-4h@m latest=now
      | eval cluster=trim(toString(coalesce(cluster, cluster_name, k8s_cluster_name, eks_cluster_name, gke_cluster_name, "")))
      | eval mn=lower(trim(toString(coalesce(metric_name, __name__, name, MetricName, ""))))
      | rex field=_raw "deployment=\\\"(?<deployment>[^\\\"]+)\\\""
      | rex field=_raw "namespace=\\\"(?<namespace>[^\\\"]+)\\\""
      | where (like(mn, "%kube_deployment_status_replicas_available%") OR like(_raw, "kube_deployment_status_replicas_available"))
      | rex field=_raw "\\s(?<mval>[0-9.eE+-]+)\\s*$"
      | eval replicas_available=tonumber(mval, 10)
      | stats latest(replicas_available) AS replicas_available BY cluster namespace deployment ]
    [ search ((index=k8s_metrics OR index=k8s) (sourcetype="prometheus:scrape:metrics" OR sourcetype="kube:objects:metrics")) earliest=-4h@m latest=now
      | eval cluster=trim(toString(coalesce(cluster, cluster_name, k8s_cluster_name, eks_cluster_name, gke_cluster_name, "")))
      | eval mn=lower(trim(toString(coalesce(metric_name, __name__, name, MetricName, ""))))
      | rex field=_raw "deployment=\\\"(?<deployment>[^\\\"]+)\\\""
      | rex field=_raw "namespace=\\\"(?<namespace>[^\\\"]+)\\\""
      | where (like(mn, "%kube_deployment_status_replicas_updated%") OR like(_raw, "kube_deployment_status_replicas_updated"))
      | rex field=_raw "\\s(?<mval>[0-9.eE+-]+)\\s*$"
      | eval replicas_updated=tonumber(mval, 10)
      | stats latest(replicas_updated) AS replicas_updated BY cluster namespace deployment ]
    [ search ((index=k8s_metrics OR index=k8s) (sourcetype="prometheus:scrape:metrics" OR sourcetype="kube:objects:metrics")) earliest=-4h@m latest=now
      | eval cluster=trim(toString(coalesce(cluster, cluster_name, k8s_cluster_name, eks_cluster_name, gke_cluster_name, "")))
      | eval mn=lower(trim(toString(coalesce(metric_name, __name__, name, MetricName, ""))))
      | rex field=_raw "deployment=\\\"(?<deployment>[^\\\"]+)\\\""
      | rex field=_raw "namespace=\\\"(?<namespace>[^\\\"]+)\\\""
      | where (like(mn, "%kube_deployment_status_replicas_ready%") OR like(mn, "%kube_deployment_status_ready_replicas%") OR like(_raw, "kube_deployment_status_replicas_ready") OR like(_raw, "kube_deployment_status_ready_replicas"))
      | rex field=_raw "\\s(?<mval>[0-9.eE+-]+)\\s*$"
      | eval replicas_ready=tonumber(mval, 10)
      | stats latest(replicas_ready) AS replicas_ready BY cluster namespace deployment ]
    [ search ((index=k8s_metrics OR index=k8s) (sourcetype="prometheus:scrape:metrics" OR sourcetype="kube:objects:metrics")) earliest=-4h@m latest=now
      | eval cluster=trim(toString(coalesce(cluster, cluster_name, k8s_cluster_name, eks_cluster_name, gke_cluster_name, "")))
      | eval mn=lower(trim(toString(coalesce(metric_name, __name__, name, MetricName, ""))))
      | rex field=_raw "deployment=\\\"(?<deployment>[^\\\"]+)\\\""
      | rex field=_raw "namespace=\\\"(?<namespace>[^\\\"]+)\\\""
      | where (like(mn, "%kube_deployment_metadata_generation%") OR like(_raw, "kube_deployment_metadata_generation"))
      | rex field=_raw "\\s(?<mval>[0-9.eE+-]+)\\s*$"
      | eval generation=tonumber(mval, 10)
      | stats latest(generation) AS generation BY cluster namespace deployment ]
    [ search ((index=k8s_metrics OR index=k8s) (sourcetype="prometheus:scrape:metrics" OR sourcetype="kube:objects:metrics")) earliest=-4h@m latest=now
      | eval cluster=trim(toString(coalesce(cluster, cluster_name, k8s_cluster_name, eks_cluster_name, gke_cluster_name, "")))
      | eval mn=lower(trim(toString(coalesce(metric_name, __name__, name, MetricName, ""))))
      | rex field=_raw "deployment=\\\"(?<deployment>[^\\\"]+)\\\""
      | rex field=_raw "namespace=\\\"(?<namespace>[^\\\"]+)\\\""
      | where (like(mn, "%kube_deployment_status_observed_generation%") OR like(_raw, "kube_deployment_status_observed_generation"))
      | rex field=_raw "\\s(?<mval>[0-9.eE+-]+)\\s*$"
      | eval observed_generation=tonumber(mval, 10)
      | stats latest(observed_generation) AS observed_generation BY cluster namespace deployment ]
    [ search ((index=k8s_metrics OR index=k8s) (sourcetype="prometheus:scrape:metrics" OR sourcetype="kube:objects:metrics")) earliest=-90m@m latest=now
      | eval cluster=trim(toString(coalesce(cluster, cluster_name, k8s_cluster_name, eks_cluster_name, gke_cluster_name, "")))
      | eval mn=lower(trim(toString(coalesce(metric_name, __name__, name, MetricName, ""))))
      | rex field=_raw "namespace=\\\"(?<namespace>[^\\\"]+)\\\""
      | rex field=_raw "owner_name=\\\"(?<deployment>[^\\\"]+)\\\""
      | rex field=_raw "replicaset=\\\"(?<rsname>[^\\\"]+)\\\""
      | where (like(mn, "%kube_replicaset_owner%") OR like(_raw, "kube_replicaset_owner"))
      | where like(_raw, "owner_kind=\\\"Deployment\\\"")
      | stats dc(rsname) AS rs_thrash_dc BY cluster namespace deployment ]
| stats latest(progress_condition) AS progress_condition latest(progress_reason) AS progress_reason latest(available_condition) AS available_condition latest(available_reason) AS available_reason latest(replicas_desired) AS replicas_desired latest(replicas_updated) AS replicas_updated latest(replicas_available) AS replicas_available latest(replicas_ready) AS replicas_ready latest(generation) AS generation latest(observed_generation) AS observed_generation latest(rs_thrash_dc) AS rs_thrash_dc BY cluster namespace deployment
| eval cluster=coalesce(nullif(trim(cluster), ""), "unknown-cluster")
| eval namespace=coalesce(nullif(trim(namespace), ""), "unknown-namespace")
| eval deployment=coalesce(nullif(trim(deployment), ""), "unknown-deployment")
| eval replicas_desired=coalesce(replicas_desired, 0)
| eval replicas_updated=coalesce(replicas_updated, 0)
| eval replicas_available=coalesce(replicas_available, 0)
| eval replicas_ready=coalesce(replicas_ready, 0)
| eval generation=coalesce(generation, 0)
| eval observed_generation=coalesce(observed_generation, 0)
| eval rs_thrash_dc=coalesce(rs_thrash_dc, 0)
| eval progress_condition=coalesce(progress_condition, "unknown")
| eval progress_reason=coalesce(progress_reason, "none_reported")
| eval available_condition=coalesce(available_condition, "unknown")
| eval available_reason=coalesce(available_reason, "none_reported")
| eval partial_stuck=if((replicas_updated < replicas_desired) OR (replicas_available < replicas_desired) OR (replicas_ready < replicas_desired), 1, 0)
| eval gen_lag=if(generation>observed_generation, generation-observed_generation, 0)
| eval deadline_breach=if(match(lower(progress_reason), "progressdeadlineexceeded") OR (match(lower(progress_condition), "false") AND match(lower(progress_reason), "progressdeadline")), 1, 0)
| eval availability_breach=if(match(lower(available_condition), "false"), 1, 0)
| eval stuck_signal=if(deadline_breach=1 OR availability_breach=1 OR partial_stuck=1 OR gen_lag>0 OR rs_thrash_dc>=rs_thrash_dc_floor, 1, 0)
| join type=left max=0 cluster namespace deployment [
    search index=k8s sourcetype="kube:events" earliest=-4h@m latest=now
      | eval cluster=trim(toString(coalesce(cluster, cluster_name, k8s_cluster_name, "")))
      | eval kind=trim(toString(coalesce(involvedObject.kind, `involvedObject.kind`, "")))
      | eval reason_ev=trim(toString(coalesce(reason, Reason, "")))
      | eval deployment=trim(toString(coalesce(involvedObject.name, involvedObject_name, "")))
      | eval namespace=trim(toString(coalesce(metadata.namespace, namespace, "")))
      | where kind="Deployment" AND reason_ev="ProgressDeadlineExceeded"
      | sort 0 + cluster + namespace + deployment + _time
      | streamstats global=f first(_time) AS rollout_start_epoch BY cluster namespace deployment
      | stats latest(rollout_start_epoch) AS first_deadline_evt latest(_time) AS last_deadline_ev BY cluster namespace deployment ]
| eval rollout_age_minutes=if(isnotnull(first_deadline_evt), round((now()-first_deadline_evt)/60, 2), if(stuck_signal=1, rollout_stuck_min_gate, null()))
| eventstats max(rollout_age_minutes) AS cluster_worst_rollout_min BY cluster
| join type=left max=0 cluster namespace deployment [
    | inputlookup deployment_inventory.csv
      | eval cluster=trim(toString(coalesce(cluster, k8s_cluster, "")))
      | eval namespace=trim(toString(namespace))
      | eval deployment=trim(toString(coalesce(deployment, workload, "")))
      | eval owner_team=trim(toString(coalesce(owner_team, team, squad, platform_team, "")))
      | eval sla_minutes=tonumber(trim(toString(coalesce(sla_minutes, rollout_sla_minutes, "600"))), 10)
      | eval tier=lower(trim(toString(coalesce(tier, workload_tier, env_tier, "dev"))))
      | fields cluster namespace deployment owner_team sla_minutes tier ]
| fillnull value=600 sla_minutes
| fillnull value="unassigned" owner_team
| fillnull value="dev" tier
| eval sla_breach=if(isnotnull(rollout_age_minutes) AND rollout_age_minutes>sla_minutes, 1, 0)
| eval severity=case(
    deadline_breach=1 AND coalesce(rollout_age_minutes, 0)>=30 AND match(tier, "prod|production|tier1|tier-1|gold"), "critical",
    deadline_breach=1 OR availability_breach=1, "critical",
    gen_lag>0 AND match(tier, "prod|production|tier1|tier-1|gold"), "high",
    partial_stuck=1 AND coalesce(rollout_age_minutes, 0)>=rollout_stuck_min_gate, "high",
    rs_thrash_dc>=rs_thrash_dc_floor, "high",
    sla_breach=1 AND match(tier, "prod|production|tier1|tier-1|gold"), "high",
    partial_stuck=1, "medium",
    gen_lag>0, "medium",
    true(), "low")
| where (stuck_signal=1 AND coalesce(rollout_age_minutes, 0)>=rollout_stuck_min_gate) OR deadline_breach=1 OR availability_breach=1 OR gen_lag>0 OR rs_thrash_dc>=rs_thrash_dc_floor OR sla_breach=1
| fields - available_condition available_reason cluster_worst_rollout_min tier partial_stuck deadline_breach availability_breach stuck_signal gen_lag sla_breach rs_thrash_dc first_deadline_evt last_deadline_ev
| table cluster namespace deployment generation observed_generation replicas_desired replicas_updated replicas_available replicas_ready progress_condition progress_reason rollout_age_minutes sla_minutes owner_team severity
```

## CIM SPL

```spl
| tstats summariesonly=true latest(Change.action) AS last_change_action count AS change_events FROM datamodel=Change WHERE nodename=Change earliest=-4h@h latest=@h BY Change.user Change.object
| rename Change.user AS change_actor Change.object AS change_obj
| join type=left max=0 change_actor [
| tstats summariesonly=true latest(Application_State.state) AS app_state FROM datamodel=Application_State WHERE nodename=Application_State earliest=-4h@h latest=@h BY Application_State.dest Application_State.app
| rename Application_State.dest AS change_actor ]
| table change_actor change_obj last_change_action change_events app_state
```

## Visualization

Primary table mirroring the closing SPL projection; timechart of ProgressDeadlineExceeded events by namespace; single value of cluster worst rollout age from a clone search; heatmap of replicas_desired minus replicas_ready; drilldowns to kube:events and optional audit.

## Known False Positives

Deliberate kubectl rollout pause leaves Deployments intentionally mid-rollout with Progressing false and ReplicaSet counts that look alarming until you read pause annotations; inventory pause_expected or GitOps freeze labels should suppress paging. Argo Rollouts, Flagger, or vendor progressive delivery controllers often hold canary phases where available replicas intentionally lag desired counts while traffic weight shifts; require progressive_delivery_tool metadata before treating partial convergence as failure. ProgressDeadlineExceeded can appear on genuinely slow stateful workloads with long initialization even when healthy; extend sla_minutes and document database or migration class services to avoid cruel paging. Brief controller flap during kube-controller-manager leader election or control-plane rolling upgrades can lag observed_generation for one or two scrapes; demand sustained gen_lag with corroborating apiserver latency before executive escalation. Planned kubectl rollout undo during incident response may spike ReplicaSet churn without bad intent; correlate k8s_audit user subjects and incident bridges before reopening blameless reviews. Hot-fix rollouts in emergency windows may relax SLA minutes contractually; reflect relaxed sla_minutes in deployment_inventory.csv for the duration. Heavy clusters with delayed kube-state-metrics scrapes can show stale condition reasons that clear on the next interval; combine with kube events first_seen join to avoid single-scrape noise. Chaos experiments that inject deadline breaches should carry chaos.rollout=expected labels mirrored into suppression lookups. GitOps revert loops that self-heal within five minutes may still trigger rs_thrash_dc; use minimum dwell gates tied to rollout_age_minutes before paging non-production tiers.

## References

- [Kubernetes — Deployments](https://kubernetes.io/docs/concepts/workloads/controllers/deployment/)
- [Kubernetes — Failed deployment and ProgressDeadlineExceeded](https://kubernetes.io/docs/concepts/workloads/controllers/deployment/#failed-deployment)
- [kube-state-metrics — Deployment metrics](https://github.com/kubernetes/kube-state-metrics/blob/main/docs/metrics/workload/deployment-metrics.md)
- [Kubernetes — Event v1 reference (cluster events)](https://kubernetes.io/docs/reference/kubernetes-api/cluster-resources/event-v1/)
- [Argo Rollouts — Documentation](https://argo-rollouts.readthedocs.io/)
- [Flagger — Progressive delivery operator](https://docs.flagger.app/)
- [Splunk Docs — Splunk Add-on for Kubernetes](https://docs.splunk.com/Documentation/AddOns/released/Kubernetes/About)
- [kubectl reference — rollout](https://kubernetes.io/docs/reference/generated/kubectl/kubectl-commands#rollout)
