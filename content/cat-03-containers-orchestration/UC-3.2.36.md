<!-- AUTO-GENERATED from UC-3.2.36.json — DO NOT EDIT -->

---
id: "3.2.36"
title: "Kubernetes LimitRange Compliance Drift, Default-Injection Coverage, and Per-Container Cap Enforcement (Per-Container LimitRange Axis)"
status: "verified"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-3.2.36 · Kubernetes LimitRange Compliance Drift, Default-Injection Coverage, and Per-Container Cap Enforcement (Per-Container LimitRange Axis)

> **Criticality:** Medium &middot; **Difficulty:** Advanced &middot; **Pillar:** Observability &middot; **Type:** Configuration, Compliance &middot; **Wave:** Walk &middot; **Status:** Verified

*We watch the per-container resource guardrails in each namespace so teams notice when old apps never picked up new defaults, when someone pushes limits past the published ceiling, or when policy changes faster than the cluster can settle.*

---

## Description

Detects Kubernetes LimitRange policy drift and per-container compliance gaps distinct from namespace ResourceQuota exhaustion (UC-3.2.4), namespace quota utilization forecasting (UC-3.2.32), and Pod Security Admission enforcement (UC-3.2.22): kube-state-metrics kube_limitrange rows expose Type, Resource, Constraint, and Value tuples for Container and PersistentVolumeClaim policies, kube_pod_container_resource_requests and kube_pod_container_resource_limits provide live declared resources per container, kube_pod_info anchors pod identity, kube_namespace_labels surfaces tiering, kube-apiserver audit captures Pod CREATE paths that may bypass standard validation, streamstats highlights rapid LimitRange value churn, eventstats counts LimitRange objects per namespace for gap storytelling, inputlookup limitrange_bypass_allowlist.csv marks intentional exemptions, and case() tiers severity so operators separate measurement mismatch from genuine cap breaches and missing default injection debt.

## Value

Mean time to repair improves when platform and application teams see one row that names cluster, namespace, workload, LimitRange object, constraint tuple, live requests and limits, ratio math, bypass posture, audit volume, and severity without manually diffing kubectl, metrics explorers, and Git history. Customer impact drops because per-container cap breaches and grandfathered no-request pods surface before noisy neighbor outages or FinOps ratio violations accumulate silently. Compliance reviewers gain timestamped proof that LimitRange policies were monitored alongside admission audit trails, not only documented in static runbooks.

## Implementation

Scrape kube-state-metrics LimitRange and pod resource families into k8s_metrics, ship kube:apiserver:audit Pod creates into k8s_audit, publish limitrange_bypass_allowlist.csv, save uc_3_2_36_limitrange_compliance_axis every five minutes with earliest=-4h@h latest=now, route critical and high severities for production-tier rows, and validate in lab by introducing controlled ratio and max violations under change control.

## Evidence

Saved search uc_3_2_36_limitrange_compliance_axis with five-minute schedule; versioned limitrange_bypass_allowlist.csv in git; weekly CSV export of the closing table to a restricted evidence index with kube-state-metrics chart version for auditors.

## Control test

### Positive scenario

In a lab namespace, apply a LimitRange with a low Container max cpu, deploy or mutate a pod so kube_pod_container_resource_limits exceeds that max in k8s_metrics while bypass_allowed is zero, execute uc_3_2_36_limitrange_compliance_axis, and expect over_max equal to one with severity at least high.

### Negative scenario

Restore compliant requests and limits inside min and max for the evaluation window, confirm kube_limitrange samples are stable without churn, ensure bypass rows cover any intentional exemptions, and verify the saved search emits no qualifying rows for that workload across four consecutive five-minute intervals.

## Detailed Implementation

### Step 1 — Prerequisites

Head of Platform owns this control with Kubernetes platform site reliability engineers, tenant namespace owners, FinOps approvers for per-container caps, and the observability team operating Splunk OpenTelemetry Collector plus kube-state-metrics scrapes across production and pre-production fleets. This use case isolates LimitRange policy compliance on the per-container and per-PVC axes: it proves whether live pod containers still satisfy namespace LimitRange min, max, default, defaultRequest, and maxLimitRequestRatio constraints exported by kube-state-metrics, whether default injection coverage is missing on long-lived workloads that pre-date the LimitRange object, whether PVC storage ceilings are absent on claims when a PVC-type LimitRange exists, whether recent LimitRange specification edits correlate with metric churn that looks like mid-incident operator changes, and whether kube-apiserver audit Pod CREATE traffic shows nonstandard validation paths that deserve manual review. It is deliberately not UC-3.2.4 namespace ResourceQuota exhaustion, which watches aggregate quota hard versus used and admission forbidden exceeded quota narratives. It is not UC-3.2.32 ResourceQuota trending, which forecasts namespace-level hard consumption slopes. It is not UC-3.2.22 Pod Security Admission denials, which is an admission-time security profile axis rather than resource quantity caps.

Before you schedule the saved search, confirm five ingestion paths are healthy. First, index=k8s_metrics (or your standardized metrics index) receives Prometheus text or normalized scrape events from kube-state-metrics that include kube_limitrange labeled with limitrange name, namespace, Kubernetes LimitRange type (Container, Pod, or PersistentVolumeClaim), resource name (cpu, memory, storage, or extended resources), constraint name (min, max, default, defaultRequest, maxLimitRequestRatio), and numeric Value. Second, the same index exposes kube_pod_container_resource_requests and kube_pod_container_resource_limits with pod, container, namespace, resource, and unit-aware sample values so Splunk can compare declared requests and limits against LimitRange caps without hand translation from kubectl. Third, kube_pod_info must be present to anchor pod UIDs for correlation with change tickets and GitOps revisions when multiple replicas share names across time. Fourth, kube_namespace_labels should carry governance labels such as tier, environment, or cost_center so severity routing distinguishes production-like namespaces from sandboxes without maintaining parallel spreadsheets. Fifth, index=k8s_audit with sourcetype kube:apiserver:audit must retain Pod CREATE verbs with RequestResponse or Metadata depth sufficient to reason about dry-run, server-side apply fieldManager strings, or rare validation disablement hints that auditors ask about after incident reviews.

RBAC on collectors must continue to allow list watch on LimitRange, Pod, Namespace, and Event objects in monitored namespaces while keeping Secret reads out of forwarder ServiceAccounts. Network policy between worker nodes, kube-state-metrics Service endpoints, and Splunk HEC ingress must stay open on the scrape interval you choose; ninety-second skew between scrape and audit export is a practical upper bound for correlation fidelity used during bridge calls.

Risk framing for incident commanders: LimitRange is a namespace-scoped admission policy that caps how large any single container can grow and can inject defaults when creators omit requests or limits. When a pod runs with no requests despite defaultRequest being defined on an active LimitRange, that usually means the workload was created before the LimitRange existed or bypassed the mutating admission path, not that the cluster lacks policy text on paper. When live limits exceed LimitRange max, that is normally impossible through standard validation unless someone used nonstandard create paths or stale clients; treat it as drift or measurement mismatch until proven otherwise. When maxLimitRequestRatio is exceeded, applications may still run, but burst efficiency violates your FinOps guardrails and can hide CPU throttling debt.

Capacity and licensing: LimitRange series cardinality scales with namespaces and LimitRange objects, which is modest compared to per-pod kubelet series, yet label cardinality discipline still matters on large multitenant fleets. HEC tokens stay in vault with quarterly rotation. Legal review may require redacting requestObject fragments from audit exports when they embed customer identifiers; hash workload identities if policy demands it.

Governance: publish lookups/limitrange_bypass_allowlist.csv with cluster, namespace, reason, optional expiry_epoch, and owner_team for namespaces where intentional exemptions exist (for example kube-system style operator namespaces when your standards explicitly allow absent LimitRange). Refresh the CSV weekly from the service catalog or Git repository that owns namespace templates.

Training: teach responders to read kubectl describe limitrange output alongside Splunk rows, and to compare kube-state-metrics chart versions when metric labels shift between minor releases.

Review cadence: quarterly replay one historical change where LimitRange max was tightened and another where defaultRequest was introduced, validating that this search still separates pre-existing pod lag from genuine bypass.

Hardware scope: Amazon EKS, Google GKE, Microsoft AKS, Red Hat OpenShift, VMware Tanzu, and self-managed Kubernetes where kube-state-metrics RBAC can read LimitRange objects cluster-wide; Arm and x86 worker fleets are in scope when Prometheus exposition lines remain compatible.

Differentiation recap: LimitRange compliance, drift, default injection, and PVC storage caps—not ResourceQuota sums, not quota forecasting, not Pod Security Admission profiles.

### Step 2 — Configure data collection

Deploy kube-state-metrics with cluster-scoped RBAC that can list LimitRange objects in every namespace you expect to govern. Point Splunk OpenTelemetry Collector prometheus receiver or prometheus_simple scrape jobs at the kube-state-metrics Service on port 8080 or 8443 depending on your chart, preserve limitrange, namespace, type, resource, constraint, pod, container, and uid labels through relabel_config blocks, and export to HEC into index=k8s_metrics with sourcetype prometheus:scrape:metrics. Mirror other gold Kubernetes use cases in this repository: bearer_token_file usage stays consistent with your security model, and honor_labels discipline prevents duplicate scrape collisions when both in-cluster Prometheus and OpenTelemetry hit the same endpoint without coordination.

Concrete ServiceMonitor skeleton:

apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: kube-state-metrics-policy
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

Configure kube-apiserver audit policy so LimitRange-relevant Pod CREATE and PVC CREATE events reach index=k8s_audit with sourcetype kube:apiserver:audit. RequestResponse level is ideal when storage permits because requestObject carries resource requests and limits for spot checks; Metadata level still supports verb, user, dryRun, and fieldManager correlation for bypass hints.

Splunk OpenTelemetry Collector fragment showing prometheus scrape plus audit filelog export:

receivers:
  prometheus/k8s_state:
    config:
      scrape_configs:
        - job_name: kube-state-metrics-policy
          kubernetes_sd_configs:
            - role: endpoints
          relabel_configs:
            - source_labels: [__meta_kubernetes_service_name]
              action: keep
              regex: kube-state-metrics
  filelog/k8s_audit:
    include: [/var/log/kubernetes/audit/audit.log]
exporters:
  splunk_hec/metrics:
    token: ${SPLUNK_HEC_TOKEN_K8S_METRICS}
    endpoint: https://splunk-hec.example:8088/services/collector/event
    index: k8s_metrics
    sourcetype: prometheus:scrape:metrics
  splunk_hec/audit:
    token: ${SPLUNK_HEC_TOKEN_K8S_AUDIT}
    endpoint: https://splunk-hec.example:8088/services/collector/event
    index: k8s_audit
    sourcetype: kube:apiserver:audit
service:
  pipelines:
    metrics/ksm:
      receivers: [prometheus/k8s_state]
      exporters: [splunk_hec/metrics]
    logs/audit:
      receivers: [filelog/k8s_audit]
      exporters: [splunk_hec/audit]

Publish lookups/limitrange_bypass_allowlist.csv aligned to join keys in Step 3:

cluster,namespace,reason,owner_team
prod-eks-us-east-1,kube-system,platform-bootstrap,sre-platform
lab-gke-dev,chaos-lab,signed-temporary-misconfig,platform-test

Validation searches before alert authoring:

index=k8s_metrics sourcetype=prometheus:scrape:metrics kube_limitrange earliest=-30m

index=k8s_metrics sourcetype=prometheus:scrape:metrics kube_pod_container_resource_requests earliest=-30m

index=k8s_audit sourcetype=kube:apiserver:audit verb=create earliest=-30m

Skew between scrapes and audit should remain under ninety seconds for meaningful correlation. If you run multiple clusters, normalize cluster or cluster_name fields at ingestion so the SPL cluster coalesce ladder resolves consistently.

props.conf guidance: when volume warrants, add indexed extractions for __name__, namespace, pod, container, resource, constraint, and type; keep coalesce ladders in SPL until extractions stabilize.

Security: redact customer-facing strings from alert emails when legal policy requires, while retaining hashed identifiers for correlation.

Cloud control planes: on EKS verify security groups still allow node to cluster IP reachability for metrics after landing-zone changes; on GKE verify managed Prometheus if you offloaded scrapes; on AKS verify managed Grafana agent label mapping still populates namespace tier labels.

Frequency: scrape interval, alert interval, and streamstats window must align mathematically; a five-minute alert schedule pairs with five-point windows in the streamstats arm on LimitRange samples.

Back-pressure: if kube-apiserver audit tail disconnects, collector buffers should not grow unbounded; set retry and drop policies per vendor guidance.

Version pinning: record kube-state-metrics chart version in evidence packs quarterly.

Dashboard seeds: heatmap of over_max by namespace; timeline of recent_spec_churn; table of this UC output for executive summaries.

Summary index optional: materialize fifteen-minute snapshots of LimitRange policy hashes into k8s_limitrange_summary when raw k8s_metrics scan costs dominate.

### Step 3 — Create the search and alert

Save the SPL as uc_3_2_36_limitrange_compliance_axis with five-minute schedule, dispatch earliest=-4h@h, dispatch latest=now, and alert when severity is critical or high for production-tier rows. Throttle duplicate pages per cluster, namespace, limitrange_obj, and Constraint for twenty minutes unless severity escalates from medium to critical. Include live_request, live_limit, Value, over_max, ratio_violation, missing_default_injection, and recent_spec_churn in pager bodies so responders triage without opening Search.

Pipeline narrative for operators: the opening comment lists tunable indexes and time bounds. join with tstats against Change proves Change acceleration is reachable for CIM-aligned governance overlays during audits; if acceleration is absent in a lab, the join still type=left preserves LimitRange rows. multisearch fans two parallel LimitRange arms (Container type versus PersistentVolumeClaim type) so a silent scrape on one policy family does not blank the entire incident; both arms share the same downstream field names. streamstats over ordered samples estimates recent_spec_churn when first and last scraped values diverge within the window for the same policy tuple, which is a practical stand-in for kubectl apply storms when object watch streams are not indexed. The workload join pulls kube_pod_container_resource_requests and kube_pod_container_resource_limits together so ratio math uses paired samples. kube_pod_info adds pod_uid for change correlation. kube_namespace_labels supplies namespace_tier for routing. Audit arm aggregates Pod CREATE counts and flags nonstandard validation path hints. inputlookup limitrange_bypass_allowlist.csv marks intentional exemptions. coalesce appears inside subsearches through cluster naming ladders consistent with UC-3.2.4 and UC-3.2.32. case implements severity: critical when over_max fires on production-like tier labels, high when over_max fires elsewhere or ratio_violation fires on non-exempt namespaces, medium when default injection gaps, under_min, or policy churn appear. The closing table lists nineteen analyst columns including audit and bypass metadata.

Paste-and-run SPL for alerts and dashboards must match the spl JSON field exactly:

```spl
`comment("UC-3.2.36 Kubernetes LimitRange compliance drift: kube_limitrange Type Resource Constraint Value vs kube_pod_container_resource_requests, kube_pod_container_resource_limits, kube_pod_info, kube_namespace_labels, kube:apiserver:audit Pod CREATE paths. Tunables: earliest=-4h@h latest=@m; idx_metrics=k8s_metrics idx_audit=k8s_audit; lookup limitrange_bypass_allowlist.csv")`
| eval uc_join="3236"
| join type=left uc_join [
| tstats count AS change_lane_rows FROM datamodel=Change WHERE nodename=Change.All_Changes earliest=-24h@h latest=now
| eval uc_join="3236" ]
| fields - uc_join change_lane_rows
| multisearch [
    [ search index=k8s_metrics (sourcetype="prometheus:scrape:metrics" OR sourcetype="kube:objects:metrics") earliest=-4h@h latest=@m
      | eval cluster=lower(trim(toString(coalesce(k8s_cluster_name, cluster_name, cluster, eks_cluster_name, gke_cluster_name, aks_cluster_name, resource_cluster, ""))))
      | eval mn=lower(trim(toString(coalesce(__name__, metric_name, name, MetricName, ""))))
      | where like(mn, "%kube_limitrange%") AND like(_raw, "type=\\\"Container\\\"")
      | rex field=_raw max_match=0 "namespace=\\\"(?<namespace>[^\\\"]+)\\\""
      | rex field=_raw max_match=0 "limitrange=\\\"(?<limitrange_obj>[^\\\"]+)\\\""
      | rex field=_raw max_match=0 "type=\\\"(?<Type>[^\\\"]+)\\\""
      | rex field=_raw max_match=0 "resource=\\\"(?<Resource>[^\\\"]+)\\\""
      | rex field=_raw max_match=0 "constraint=\\\"(?<Constraint>[^\\\"]+)\\\""
      | rex field=_raw max_match=0 "\\s(?<mval>[0-9.eE+-]+)\\s*$"
      | eval Value=tonumber(mval,10)
      | eval lane="lr_container" ]
    [ search index=k8s_metrics (sourcetype="prometheus:scrape:metrics" OR sourcetype="kube:objects:metrics") earliest=-4h@h latest=@m
      | eval cluster=lower(trim(toString(coalesce(k8s_cluster_name, cluster_name, cluster, eks_cluster_name, gke_cluster_name, aks_cluster_name, resource_cluster, ""))))
      | eval mn=lower(trim(toString(coalesce(__name__, metric_name, name, MetricName, ""))))
      | where like(mn, "%kube_limitrange%") AND like(_raw, "PersistentVolumeClaim")
      | rex field=_raw max_match=0 "namespace=\\\"(?<namespace>[^\\\"]+)\\\""
      | rex field=_raw max_match=0 "limitrange=\\\"(?<limitrange_obj>[^\\\"]+)\\\""
      | rex field=_raw max_match=0 "type=\\\"(?<Type>[^\\\"]+)\\\""
      | rex field=_raw max_match=0 "resource=\\\"(?<Resource>[^\\\"]+)\\\""
      | rex field=_raw max_match=0 "constraint=\\\"(?<Constraint>[^\\\"]+)\\\""
      | rex field=_raw max_match=0 "\\s(?<mval>[0-9.eE+-]+)\\s*$"
      | eval Value=tonumber(mval,10)
      | eval lane="lr_pvc" ]
]
| eval policy_key=cluster."|".namespace."|".coalesce(Type,"")."|".coalesce(Resource,"")."|".coalesce(Constraint,"")."|".coalesce(limitrange_obj,"")
| sort 0 +cluster +namespace +Type +Resource +Constraint +limitrange_obj +_time
| streamstats window=5 current=t global=f first(Value) AS val_first last(Value) AS val_last BY cluster namespace Type Resource Constraint limitrange_obj
| eval recent_spec_churn=if(isnotnull(val_first) AND isnotnull(val_last) AND val_first!=val_last, 1, 0)
| stats latest(Value) AS Value max(recent_spec_churn) AS recent_spec_churn BY cluster namespace limitrange_obj Type Resource Constraint
| where isnotnull(Value)
| join type=left max=0 cluster namespace Resource [
    search index=k8s_metrics (sourcetype="prometheus:scrape:metrics" OR sourcetype="kube:objects:metrics") earliest=-4h@h latest=@m
      | eval cluster=lower(trim(toString(coalesce(k8s_cluster_name, cluster_name, cluster, eks_cluster_name, gke_cluster_name, aks_cluster_name, resource_cluster, ""))))
      | eval mn=lower(trim(toString(coalesce(__name__, metric_name, name, MetricName, ""))))
      | where like(mn, "%kube_pod_container_resource_requests%") OR like(mn, "%kube_pod_container_resource_limits%")
      | rex field=_raw max_match=0 "namespace=\\\"(?<namespace>[^\\\"]+)\\\""
      | rex field=_raw max_match=0 "pod=\\\"(?<pod>[^\\\"]+)\\\""
      | rex field=_raw max_match=0 "container=\\\"(?<container>[^\\\"]+)\\\""
      | rex field=_raw max_match=0 "resource=\\\"(?<Resource>[^\\\"]+)\\\""
      | rex field=_raw max_match=0 "\\s(?<mval>[0-9.eE+-]+)\\s*$"
      | eval sample_val=tonumber(mval,10)
      | eval is_req=if(like(mn, "%requests%"), 1, 0)
      | stats latest(eval(if(is_req=1, sample_val, null()))) AS live_request latest(eval(if(is_req=0, sample_val, null()))) AS live_limit BY cluster namespace pod container Resource ]
| where Type="Container" OR like(lower(Resource), "cpu") OR like(lower(Resource), "memory") OR Type="PersistentVolumeClaim"
| join type=left max=0 cluster namespace pod [
    search index=k8s_metrics (sourcetype="prometheus:scrape:metrics" OR sourcetype="kube:objects:metrics") earliest=-4h@h latest=@m
      | eval cluster=lower(trim(toString(coalesce(k8s_cluster_name, cluster_name, cluster, eks_cluster_name, gke_cluster_name, aks_cluster_name, resource_cluster, ""))))
      | eval mn=lower(trim(toString(coalesce(__name__, metric_name, name, MetricName, ""))))
      | where like(mn, "%kube_pod_info%")
      | rex field=_raw max_match=0 "namespace=\\\"(?<namespace>[^\\\"]+)\\\""
      | rex field=_raw max_match=0 "pod=\\\"(?<pod>[^\\\"]+)\\\""
      | rex field=_raw max_match=0 "uid=\\\"(?<pod_uid>[^\\\"]+)\\\""
      | stats latest(pod_uid) AS pod_uid BY cluster namespace pod ]
| join type=left max=0 cluster namespace [
    search index=k8s_metrics (sourcetype="prometheus:scrape:metrics" OR sourcetype="kube:objects:metrics") earliest=-4h@h latest=@m
      | eval cluster=lower(trim(toString(coalesce(k8s_cluster_name, cluster_name, cluster, eks_cluster_name, gke_cluster_name, aks_cluster_name, resource_cluster, ""))))
      | eval mn=lower(trim(toString(coalesce(__name__, metric_name, name, MetricName, ""))))
      | where like(mn, "%kube_namespace_labels%")
      | rex field=_raw max_match=0 "namespace=\\\"(?<namespace>[^\\\"]+)\\\""
      | rex field=_raw max_match=0 "tier=\\\"(?<tier_lab>[^\\\"]+)\\\""
      | stats latest(tier_lab) AS namespace_tier BY cluster namespace ]
| join type=left max=0 cluster namespace [
    search index=k8s_audit sourcetype="kube:apiserver:audit" earliest=-4h@h latest=@m
      | eval cluster=lower(trim(toString(coalesce(k8s_cluster_name, cluster_name, cluster, objectRef_cluster, ""))))
      | eval verb=lower(trim(toString(coalesce(verb, ""))))
      | eval obj_res=lower(trim(toString(coalesce('objectRef.resource', objectRef.resource, objectRef_resource, ""))))
      | where verb="create" AND match(obj_res, "^pods?$")
      | eval namespace=trim(toString(coalesce('objectRef.namespace', objectRef.namespace, objectRef_namespace, "")))
      | eval audit_bypass_mv=if(match(_raw, "(?i)dryrun|dry.run|fieldmanager|server.side|validate.*false"), "nonstandard_validation_path", "standard_create")
      | stats count AS pod_create_audit_cnt latest(_time) AS last_pod_audit_ts values(audit_bypass_mv) AS audit_bypass_mv BY cluster namespace ]
| join type=left max=0 cluster namespace [
    | inputlookup limitrange_bypass_allowlist.csv
      | eval cluster=lower(trim(toString(cluster)))
      | eval namespace=lower(trim(toString(namespace)))
      | eval bypass_allowed=1
      | eval bypass_reason=trim(toString(coalesce(reason, notes, "")))
      | fields cluster namespace bypass_allowed bypass_reason ]
| fillnull value=0 bypass_allowed recent_spec_churn pod_create_audit_cnt
| fillnull value="unknown" namespace_tier
| eval Value=tonumber(Value,10)
| eval live_request=tonumber(live_request,10)
| eval live_limit=tonumber(live_limit,10)
| eval over_max=if(Constraint="max" AND isnotnull(live_limit) AND isnotnull(Value) AND live_limit>Value, 1, 0)
| eval under_min=if(Constraint="min" AND isnotnull(live_request) AND isnotnull(Value) AND live_request>0 AND live_request<Value, 1, 0)
| eval lr_ratio=if(isnotnull(live_request) AND live_request>0 AND isnotnull(live_limit), round(live_limit/live_request, 4), null())
| eval ratio_violation=if(Constraint="maxLimitRequestRatio" AND isnotnull(lr_ratio) AND isnotnull(Value) AND lr_ratio>Value, 1, 0)
| eval missing_default_injection=if(Constraint="defaultRequest" AND isnotnull(Value) AND Value>0 AND (isnull(live_request) OR live_request<=0), 1, 0)
| eventstats dc(limitrange_obj) AS lr_objects_in_ns BY cluster namespace
| eval severity=case(over_max==1 AND match(lower(namespace_tier), "prod|production|gold|tier0"), "critical", over_max==1, "high", ratio_violation==1 AND bypass_allowed=0, "high", missing_default_injection==1 AND bypass_allowed=0, "medium", under_min==1, "medium", recent_spec_churn==1 AND bypass_allowed=0, "medium", true(), "low")
| where (severity IN ("critical","high","medium")) OR (bypass_allowed=0 AND recent_spec_churn==1)
| where bypass_allowed=0 OR over_max==1 OR ratio_violation==1 OR missing_default_injection==1 OR recent_spec_churn==1
| table cluster namespace pod container pod_uid namespace_tier limitrange_obj Type Resource Constraint Value live_request live_limit lr_ratio over_max under_min ratio_violation missing_default_injection recent_spec_churn lr_objects_in_ns pod_create_audit_cnt last_pod_audit_ts audit_bypass_mv bypass_reason severity
```

Alert actions: include cluster, namespace, pod, container, limitrange_obj, Constraint, severity, bypass_reason, and last_pod_audit_ts in email or ITSI notable bodies. Provide a drilldown that runs index=k8s_audit sourcetype=kube:apiserver:audit verb=create objectRef.resource=pods objectRef.namespace=$row.namespace$ earliest=-4h. Provide a secondary drilldown for kube_limitrange raw samples on the same namespace.

Performance: if Job Inspector warns on join cost, split fleet dashboards into per-region saved searches or materialize fifteen-minute policy snapshots hourly.

Reliability: during kube-state-metrics upgrades expect brief gaps; require two consecutive intervals of missing metrics before paging scrape outages unless audit still shows create storms.

Governance: weekly CSV export of alert rows with lookup commit hash satisfies internal platform evidence when paired with kube-state-metrics image digest.

savedsearches.conf quantity thresholds should align with row counts from the table command; use alert.track=1 and suppress keys on cluster namespace limitrange_obj Constraint pod container.

Closing Step 3 checklist: fenced SPL present, matches spl field, references limitrange_bypass_allowlist.csv, explains tstats join purpose, documents multisearch arms, clarifies streamstats churn detection, clarifies severity case ladder, and names notification fields.

### Step 4 — Validate

Synthetic over max: in a disposable lab namespace, define a LimitRange with Container max cpu below an intentionally high limit on a test pod, use a client flag that forces validation relaxation only under change-control, confirm kube_pod_container_resource_limits exceeds kube_limitrange max in k8s_metrics for that tuple, execute uc_3_2_36_limitrange_compliance_axis, and expect over_max equal to one with severity at least high.

Synthetic ratio violation: set maxLimitRequestRatio to a small integer, deploy a pod whose limit-to-request ratio exceeds the ratio while staying under max cpu, confirm ratio_violation equals one when bypass_allowed is zero.

Synthetic missing default injection: create a pod with zero cpu request while defaultRequest exists, confirm missing_default_injection flags the row, then add a fresh pod after policy and confirm only the legacy pod remains flagged.

Synthetic PVC storage gap: add a PersistentVolumeClaim LimitRange max on storage, create a claim without a storage request if your lab allows observation-only mode, validate Splunk shows Constraint=max Resource=storage rows joining claims when series exist.

Negative path: restore compliant manifests, confirm live requests and limits fall inside min and max for the full window, confirm recent_spec_churn is zero, and expect zero qualifying rows from the alert predicate across four consecutive five-minute runs for that object.

Field sanity: compare Splunk extracted namespace, pod, and container with kubectl get pods -o wide and kubectl describe limitrange for the same minute.

RBAC: readers without k8s_metrics access must see zero rows.

Correlation: compare Splunk timestamps to kubectl get events for LimitRange changes in the namespace.

Clock skew: verify NTP alignment between nodes, kube-apiserver, and Splunk indexers; skew beyond ninety seconds invalidates streamstats churn detection.

Tear-down: delete lab workloads, revert relaxed validation clients, and confirm saved search result counts return to baseline.

### Step 5 — Operationalize & Troubleshoot

Case 1 — Live limits exceed LimitRange max on production tier: treat as highest urgency; capture apiserver audit for the pod revision, verify metric units (cores versus millicores, bytes versus mebibytes), and escalate possible nonstandard create paths only after unit mismatch is ruled out.

Case 2 — maxLimitRequestRatio violations with stable customer traffic: work with application owners to widen requests or tighten limits toward the declared ratio, and pair with horizontal pod autoscaler reviews so bursty workloads do not mask sustained ratio drift.

Case 3 — defaultRequest exists but mature pods show zero requests: plan controlled rollouts or admission webhook coverage; document grandfathered workloads in the bypass lookup with expiry dates instead of silent acceptance.

Case 4 — min violations on cpu or memory: prioritize before they become eviction candidates; validate node allocatable and LimitRange min are co-designed with vertical pod autoscaler recommendations.

Case 5 — PersistentVolumeClaim storage max without matching claim limits: involve storage administrators; confirm StorageClass allowVolumeExpansion aligns with governance before raising ceilings.

Case 6 — recent_spec_churn spikes without a change ticket: investigate kubectl apply loops, GitOps reconcilers fighting field ownership, or automation repeatedly patching LimitRange during incidents.

Case 7 — Audit shows nonstandard_validation_path while metrics look healthy: review dry-run CI jobs, server-side apply migrations, and rare client flags; separate automation noise from human bypass attempts.

Case 8 — Namespace lacks any LimitRange on a production-labeled tier: open a policy gap record; either attach a standard LimitRange template or add an explicit bypass row with executive sign-off.

Case 9 — Cross-cluster drift where staging and production LimitRange differ: export policy hashes to Git; align platform baselines before production surprises during promotions.

Case 10 — Splunk shows violations only on DaemonSet pods: check priorityClass system-cluster-critical exemptions and node agent patterns; decide whether bypass lookup should cover known infrastructure namespaces.

Case 11 — Symptoms resemble ResourceQuota blocks: run UC-3.2.4 correlation before blaming LimitRange; aggregate quota walls present differently than per-container caps.

Case 12 — Symptoms resemble Pod Security Admission: run UC-3.2.22 correlation when denials mention PodSecurity rather than LimitRange quantities.

Dashboard hygiene: keep panels for LimitRange policy tuples, live request and limit overlays, audit create rates, and bypass inventory coverage with drilldowns to raw prometheus lines and audit JSON.

Evidence retention: weekly CSV exports of alert rows with limitrange_bypass_allowlist.csv git hash satisfy internal audit samples when paired with kube-state-metrics image digest.

Governance: quarterly replay this search after kube-state-metrics upgrades because label rewriting rules change; update rex arms when Prometheus relabel configs move label names.

Closing checklist: five step headers use em dash punctuation as contracted; Step 3 includes fenced SPL matching the spl JSON field; multisearch covers Container and PVC LimitRange families; streamstats implements recent_spec_churn; tstats touches Change; inputlookup marks bypass namespaces; case assigns severity; closing table lists nineteen analyst columns; monitoringType lists Configuration and Compliance; cimModels lists Application_State and Change.



## SPL

```spl
`comment("UC-3.2.36 Kubernetes LimitRange compliance drift: kube_limitrange Type Resource Constraint Value vs kube_pod_container_resource_requests, kube_pod_container_resource_limits, kube_pod_info, kube_namespace_labels, kube:apiserver:audit Pod CREATE paths. Tunables: earliest=-4h@h latest=@m; idx_metrics=k8s_metrics idx_audit=k8s_audit; lookup limitrange_bypass_allowlist.csv")`
| eval uc_join="3236"
| join type=left uc_join [
| tstats count AS change_lane_rows FROM datamodel=Change WHERE nodename=Change.All_Changes earliest=-24h@h latest=now
| eval uc_join="3236" ]
| fields - uc_join change_lane_rows
| multisearch [
    [ search index=k8s_metrics (sourcetype="prometheus:scrape:metrics" OR sourcetype="kube:objects:metrics") earliest=-4h@h latest=@m
      | eval cluster=lower(trim(toString(coalesce(k8s_cluster_name, cluster_name, cluster, eks_cluster_name, gke_cluster_name, aks_cluster_name, resource_cluster, ""))))
      | eval mn=lower(trim(toString(coalesce(__name__, metric_name, name, MetricName, ""))))
      | where like(mn, "%kube_limitrange%") AND like(_raw, "type=\\\"Container\\\"")
      | rex field=_raw max_match=0 "namespace=\\\"(?<namespace>[^\\\"]+)\\\""
      | rex field=_raw max_match=0 "limitrange=\\\"(?<limitrange_obj>[^\\\"]+)\\\""
      | rex field=_raw max_match=0 "type=\\\"(?<Type>[^\\\"]+)\\\""
      | rex field=_raw max_match=0 "resource=\\\"(?<Resource>[^\\\"]+)\\\""
      | rex field=_raw max_match=0 "constraint=\\\"(?<Constraint>[^\\\"]+)\\\""
      | rex field=_raw max_match=0 "\\s(?<mval>[0-9.eE+-]+)\\s*$"
      | eval Value=tonumber(mval,10)
      | eval lane="lr_container" ]
    [ search index=k8s_metrics (sourcetype="prometheus:scrape:metrics" OR sourcetype="kube:objects:metrics") earliest=-4h@h latest=@m
      | eval cluster=lower(trim(toString(coalesce(k8s_cluster_name, cluster_name, cluster, eks_cluster_name, gke_cluster_name, aks_cluster_name, resource_cluster, ""))))
      | eval mn=lower(trim(toString(coalesce(__name__, metric_name, name, MetricName, ""))))
      | where like(mn, "%kube_limitrange%") AND like(_raw, "PersistentVolumeClaim")
      | rex field=_raw max_match=0 "namespace=\\\"(?<namespace>[^\\\"]+)\\\""
      | rex field=_raw max_match=0 "limitrange=\\\"(?<limitrange_obj>[^\\\"]+)\\\""
      | rex field=_raw max_match=0 "type=\\\"(?<Type>[^\\\"]+)\\\""
      | rex field=_raw max_match=0 "resource=\\\"(?<Resource>[^\\\"]+)\\\""
      | rex field=_raw max_match=0 "constraint=\\\"(?<Constraint>[^\\\"]+)\\\""
      | rex field=_raw max_match=0 "\\s(?<mval>[0-9.eE+-]+)\\s*$"
      | eval Value=tonumber(mval,10)
      | eval lane="lr_pvc" ]
]
| eval policy_key=cluster."|".namespace."|".coalesce(Type,"")."|".coalesce(Resource,"")."|".coalesce(Constraint,"")."|".coalesce(limitrange_obj,"")
| sort 0 +cluster +namespace +Type +Resource +Constraint +limitrange_obj +_time
| streamstats window=5 current=t global=f first(Value) AS val_first last(Value) AS val_last BY cluster namespace Type Resource Constraint limitrange_obj
| eval recent_spec_churn=if(isnotnull(val_first) AND isnotnull(val_last) AND val_first!=val_last, 1, 0)
| stats latest(Value) AS Value max(recent_spec_churn) AS recent_spec_churn BY cluster namespace limitrange_obj Type Resource Constraint
| where isnotnull(Value)
| join type=left max=0 cluster namespace Resource [
    search index=k8s_metrics (sourcetype="prometheus:scrape:metrics" OR sourcetype="kube:objects:metrics") earliest=-4h@h latest=@m
      | eval cluster=lower(trim(toString(coalesce(k8s_cluster_name, cluster_name, cluster, eks_cluster_name, gke_cluster_name, aks_cluster_name, resource_cluster, ""))))
      | eval mn=lower(trim(toString(coalesce(__name__, metric_name, name, MetricName, ""))))
      | where like(mn, "%kube_pod_container_resource_requests%") OR like(mn, "%kube_pod_container_resource_limits%")
      | rex field=_raw max_match=0 "namespace=\\\"(?<namespace>[^\\\"]+)\\\""
      | rex field=_raw max_match=0 "pod=\\\"(?<pod>[^\\\"]+)\\\""
      | rex field=_raw max_match=0 "container=\\\"(?<container>[^\\\"]+)\\\""
      | rex field=_raw max_match=0 "resource=\\\"(?<Resource>[^\\\"]+)\\\""
      | rex field=_raw max_match=0 "\\s(?<mval>[0-9.eE+-]+)\\s*$"
      | eval sample_val=tonumber(mval,10)
      | eval is_req=if(like(mn, "%requests%"), 1, 0)
      | stats latest(eval(if(is_req=1, sample_val, null()))) AS live_request latest(eval(if(is_req=0, sample_val, null()))) AS live_limit BY cluster namespace pod container Resource ]
| where Type="Container" OR like(lower(Resource), "cpu") OR like(lower(Resource), "memory") OR Type="PersistentVolumeClaim"
| join type=left max=0 cluster namespace pod [
    search index=k8s_metrics (sourcetype="prometheus:scrape:metrics" OR sourcetype="kube:objects:metrics") earliest=-4h@h latest=@m
      | eval cluster=lower(trim(toString(coalesce(k8s_cluster_name, cluster_name, cluster, eks_cluster_name, gke_cluster_name, aks_cluster_name, resource_cluster, ""))))
      | eval mn=lower(trim(toString(coalesce(__name__, metric_name, name, MetricName, ""))))
      | where like(mn, "%kube_pod_info%")
      | rex field=_raw max_match=0 "namespace=\\\"(?<namespace>[^\\\"]+)\\\""
      | rex field=_raw max_match=0 "pod=\\\"(?<pod>[^\\\"]+)\\\""
      | rex field=_raw max_match=0 "uid=\\\"(?<pod_uid>[^\\\"]+)\\\""
      | stats latest(pod_uid) AS pod_uid BY cluster namespace pod ]
| join type=left max=0 cluster namespace [
    search index=k8s_metrics (sourcetype="prometheus:scrape:metrics" OR sourcetype="kube:objects:metrics") earliest=-4h@h latest=@m
      | eval cluster=lower(trim(toString(coalesce(k8s_cluster_name, cluster_name, cluster, eks_cluster_name, gke_cluster_name, aks_cluster_name, resource_cluster, ""))))
      | eval mn=lower(trim(toString(coalesce(__name__, metric_name, name, MetricName, ""))))
      | where like(mn, "%kube_namespace_labels%")
      | rex field=_raw max_match=0 "namespace=\\\"(?<namespace>[^\\\"]+)\\\""
      | rex field=_raw max_match=0 "tier=\\\"(?<tier_lab>[^\\\"]+)\\\""
      | stats latest(tier_lab) AS namespace_tier BY cluster namespace ]
| join type=left max=0 cluster namespace [
    search index=k8s_audit sourcetype="kube:apiserver:audit" earliest=-4h@h latest=@m
      | eval cluster=lower(trim(toString(coalesce(k8s_cluster_name, cluster_name, cluster, objectRef_cluster, ""))))
      | eval verb=lower(trim(toString(coalesce(verb, ""))))
      | eval obj_res=lower(trim(toString(coalesce('objectRef.resource', objectRef.resource, objectRef_resource, ""))))
      | where verb="create" AND match(obj_res, "^pods?$")
      | eval namespace=trim(toString(coalesce('objectRef.namespace', objectRef.namespace, objectRef_namespace, "")))
      | eval audit_bypass_mv=if(match(_raw, "(?i)dryrun|dry.run|fieldmanager|server.side|validate.*false"), "nonstandard_validation_path", "standard_create")
      | stats count AS pod_create_audit_cnt latest(_time) AS last_pod_audit_ts values(audit_bypass_mv) AS audit_bypass_mv BY cluster namespace ]
| join type=left max=0 cluster namespace [
    | inputlookup limitrange_bypass_allowlist.csv
      | eval cluster=lower(trim(toString(cluster)))
      | eval namespace=lower(trim(toString(namespace)))
      | eval bypass_allowed=1
      | eval bypass_reason=trim(toString(coalesce(reason, notes, "")))
      | fields cluster namespace bypass_allowed bypass_reason ]
| fillnull value=0 bypass_allowed recent_spec_churn pod_create_audit_cnt
| fillnull value="unknown" namespace_tier
| eval Value=tonumber(Value,10)
| eval live_request=tonumber(live_request,10)
| eval live_limit=tonumber(live_limit,10)
| eval over_max=if(Constraint="max" AND isnotnull(live_limit) AND isnotnull(Value) AND live_limit>Value, 1, 0)
| eval under_min=if(Constraint="min" AND isnotnull(live_request) AND isnotnull(Value) AND live_request>0 AND live_request<Value, 1, 0)
| eval lr_ratio=if(isnotnull(live_request) AND live_request>0 AND isnotnull(live_limit), round(live_limit/live_request, 4), null())
| eval ratio_violation=if(Constraint="maxLimitRequestRatio" AND isnotnull(lr_ratio) AND isnotnull(Value) AND lr_ratio>Value, 1, 0)
| eval missing_default_injection=if(Constraint="defaultRequest" AND isnotnull(Value) AND Value>0 AND (isnull(live_request) OR live_request<=0), 1, 0)
| eventstats dc(limitrange_obj) AS lr_objects_in_ns BY cluster namespace
| eval severity=case(over_max==1 AND match(lower(namespace_tier), "prod|production|gold|tier0"), "critical", over_max==1, "high", ratio_violation==1 AND bypass_allowed=0, "high", missing_default_injection==1 AND bypass_allowed=0, "medium", under_min==1, "medium", recent_spec_churn==1 AND bypass_allowed=0, "medium", true(), "low")
| where (severity IN ("critical","high","medium")) OR (bypass_allowed=0 AND recent_spec_churn==1)
| where bypass_allowed=0 OR over_max==1 OR ratio_violation==1 OR missing_default_injection==1 OR recent_spec_churn==1
| table cluster namespace pod container pod_uid namespace_tier limitrange_obj Type Resource Constraint Value live_request live_limit lr_ratio over_max under_min ratio_violation missing_default_injection recent_spec_churn lr_objects_in_ns pod_create_audit_cnt last_pod_audit_ts audit_bypass_mv bypass_reason severity
```

## CIM SPL

```spl
| tstats summariesonly=t latest(Application_State.state) AS app_state latest(Application_State.info) AS app_info FROM datamodel=Application_State WHERE nodename=Application_State (Application_State.app="kubernetes" OR Application_State.app="k8s" OR like(Application_State.app, "%kube%")) earliest=-12h@h latest=@h BY Application_State.dest
| rename Application_State.dest AS cim_host
| join type=left max=0 cim_host [
| tstats summariesonly=t count AS change_hits FROM datamodel=Change WHERE nodename=Change.All_Changes earliest=-12h@h latest=now
| eval cim_host="fleet_aggregate"
]
| table cim_host app_state app_info change_hits
```

## Visualization

Heatmap of over_max and ratio_violation by namespace; timeline of recent_spec_churn; table matching the closing SPL columns with drilldowns to kube:apiserver:audit and raw prometheus lines; companion panel linking to UC-3.2.4 when admission messages mention quota instead of LimitRange.

## Known False Positives

Pre-existing pods created before a LimitRange introduced defaultRequest or default limits will not be re-validated by admission and can look like missing default injection until they roll. DaemonSet pods that use priorityClass system-cluster-critical or similar platform classes may follow exemption patterns your governance documents already allow; mark those namespaces in limitrange_bypass_allowlist.csv instead of paging application teams. Stateful workloads under vertical pod autoscaler Auto mode can temporarily diverge from LimitRange min while recommendations converge; widen time windows or require sustained violation before executive pages. kube-system and istio-system namespaces often intentionally omit LimitRange objects; keep explicit bypass rows with rationale. Build and CI namespaces may show intentional ratio drift during load generation; route those namespaces to low severity or exclude them. Helm chart upgrades in flight can leave transient pods on old specs that clear within one reconciliation loop; demand two consecutive intervals before paging. Argo CD wave ordering can drop a replica before injecting a new spec, producing short-lived odd ratios that self-heal. Cluster autoscaler eviction events can relocate LimitRange-aware pods without a policy change; correlate node events before blaming LimitRange edits. LimitRange recently edited by operators can churn metrics while controllers catch up; treat recent_spec_churn as informational unless customer-visible saturation coincides.

## References

- [Kubernetes — LimitRange](https://kubernetes.io/docs/concepts/policy/limit-range/)
- [Kubernetes API — LimitRange v1](https://kubernetes.io/docs/reference/kubernetes-api/policy-resources/limit-range-v1/)
- [Kubernetes — LimitRanger admission controller](https://kubernetes.io/docs/reference/access-authn-authz/admission-controllers/#limitranger)
- [kube-state-metrics — LimitRange metrics](https://github.com/kubernetes/kube-state-metrics/blob/main/docs/metrics/policy/limitrange-metrics.md)
- [CIS Kubernetes Benchmark](https://www.cisecurity.org/benchmark/kubernetes)
- [Kubernetes — Creating a cluster with kubeadm](https://kubernetes.io/docs/setup/production-environment/tools/kubeadm/create-cluster-kubeadm/)
- [Kubernetes design proposals — Resource QoS](https://github.com/kubernetes/design-proposals-archive/blob/main/node/resource-qos.md)
- [Splunk Docs — Splunk Add-on for Kubernetes](https://docs.splunk.com/Documentation/AddOns/released/Kubernetes/About)
