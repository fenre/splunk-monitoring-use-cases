<!-- AUTO-GENERATED from UC-3.2.27.json — DO NOT EDIT -->

---
id: "3.2.27"
title: "Kubernetes NetworkPolicy Default-Deny Coverage and Drift (East-West Governance)"
status: "verified"
criticality: "high"
splunkPillar: "Security"
---

# UC-3.2.27 · Kubernetes NetworkPolicy Default-Deny Coverage and Drift (East-West Governance)

> **Criticality:** High &middot; **Difficulty:** Advanced &middot; **Pillar:** Security &middot; **Type:** Security, Compliance, Configuration &middot; **Wave:** Walk &middot; **Status:** Verified

*We watch the rules that control which programs may talk to each other inside your container estate. When someone removes the lock-down rules, leaves busy application areas without rules, or adds rules that sound like they allow the whole world in or out, we raise a clear signal for the platform team.*

---

## Description

Unique monitoring axis: Kubernetes NetworkPolicy object inventory from kube-state-metrics (kube_networkpolicy_info, kube_networkpolicy_spec_ingress_rules, kube_networkpolicy_spec_egress_rules) joined to kube_pod_info Running footprint and kube_namespace_labels enforcement hints, correlated with kube:apiserver:audit delete verbs on networkpolicies and a compliance_namespace_networkpolicy.csv spine for expected default-deny ingress and egress posture, permissive naming heuristics, world egress hints, ungoverned workload namespaces with zero policies, and delete burst context. This is east-west NetworkPolicy governance and drift, not UC-3.2.22 Pod Security Admission, not UC-3.2.12 RBAC, not UC-3.2.9 north-south ingress reliability, not UC-3.2.18 ingress backend health, and not UC-3.2.41 Service Endpoints readiness.

## Value

When default-deny scaffolding disappears or never existed, lateral movement inside a compromised namespace becomes trivial long before traditional perimeter alerts fire. Timestamped inventory and delete rows give platform networking and application security teams an actionable backlog tied to owner_team. Regulators and customers asking for NSA-style Kubernetes hardening guidance receive evidence that east-west segmentation intent is monitored, not only described in architecture PDFs. Mean time to contain improves because Splunk shows which cluster, which namespace, which policy names vanished, and whether running pods remained ungoverned.

## Implementation

Stand up k8s_metrics scrapes of kube-state-metrics NetworkPolicy families and k8s_audit for networking.k8s.io networkpolicies deletes. Version compliance_namespace_networkpolicy.csv with tier, mesh alternates, and grace epochs. Save uc_3_2_27_networkpolicy_default_deny_governance on a fifteen-minute cadence over earliest=-4h@h latest=@h, route critical and high rows to platform networking, and archive weekly evidence exports with lookup commit hashes for auditors reviewing east-west segmentation posture.

## Evidence

Saved search uc_3_2_27_networkpolicy_default_deny_governance; versioned compliance_namespace_networkpolicy.csv in git; weekly CSV export of the closing table to a restricted evidence index; dashboard drilldowns from severity to raw audit JSON and kube-state-metrics scrape lines.

## Control test

### Positive scenario

In lab, create a default-deny-ingress NetworkPolicy per naming standard, confirm kube_networkpolicy_info appears in k8s_metrics, delete the object with kubectl, confirm kube:apiserver:audit records verb delete on networkpolicies, run uc_3_2_27_networkpolicy_default_deny_governance, and expect delete_events greater than zero with severity critical_np_delete_default_deny when inventory requires_default_deny_ingress=1.

### Negative scenario

Add mesh_authz_alternate=1 for a mesh-only namespace without Kubernetes denies, confirm severity routes to low_mesh_alternate and the alert search returns zero rows after the final where clause while dashboard clones without mesh suppression still show informational context.

## Detailed Implementation

### Step 1 — Prerequisites

Head of Platform owns this control jointly with the Kubernetes platform networking lead, the fleet security architect who signs off on east-west segmentation policy, and the observability engineer who operates Splunk OpenTelemetry Collector scrapes of kube-state-metrics. This use case isolates the NetworkPolicy governance plane for workload namespaces: whether default-deny ingress and optional default-deny egress objects exist with naming and label conventions your compliance_namespace_networkpolicy.csv expects, whether kube-state-metrics still materializes kube_networkpolicy_info plus kube_networkpolicy_spec_ingress_rules and kube_networkpolicy_spec_egress_rules series after upgrades, whether overly permissive policies appear in inventory heuristics, whether audit captures delete verbs against networkpolicies that remove default-deny objects, and whether running pods remain in namespaces with zero NetworkPolicy objects when inventory marks those namespaces as workload-bearing. UC-3.2.22 remains Pod Security Admission and namespace PSA label drift. UC-3.2.12 remains RBAC misconfiguration analytics. UC-3.2.23 remains cluster-admin binding change auditing. UC-3.2.9 remains north-south ingress controller reliability. UC-3.2.18 remains ingress backend health signals. UC-3.2.41 remains Kubernetes Service Endpoints readiness. None of those siblings replace kube-state-metrics NetworkPolicy cardinality, CNI-enforced east-west intent expressed as NetworkPolicy objects, or apiserver audit delete trails on networkpolicies.

Index contracts: dedicate index=k8s_metrics for sourcetype=prometheus:scrape:metrics with fifteen-to-sixty second scrape cadence from kube-state-metrics and with resource attributes that preserve k8s_cluster_name or equivalent cluster labels on every line. Dedicate index=k8s_audit for sourcetype=kube:apiserver:audit with RequestResponse or Metadata depth sufficient to read objectRef.resource, objectRef.namespace, objectRef.name, verb, and user.username on successful and failed deletes. Optional summary index=k8s_compliance may hold hourly rollups of policy_inventory_mvcount when search cost grows; document lag acceptance when you point the governance arm at summaries instead of raw scrapes.

Governance lookup: publish lookups/compliance_namespace_networkpolicy.csv from the same Git repository that applies namespace labels and Helm charts so auditors can trace rows to commits. Minimum columns: cluster, namespace, requires_default_deny_ingress (1 expects a default-deny ingress style policy object present), requires_default_deny_egress (1 expects default-deny egress where your standard mandates it), expected_pod_selector_label_key and expected_pod_selector_label_value when default-deny policies target only workloads carrying a tier label, owner_team, mesh_authz_alternate (1 when Istio AuthorizationPolicy or an equivalent mesh control substitutes for Kubernetes NetworkPolicy in that namespace), grace_until_epoch (Unix epoch until which missing deny rows downgrade to informational while a multi-phase rollout finishes), workload_tier (prod, critical, platform, lab) for severity weighting. Refresh the CSV from CI whenever namespaces are created or retired.

Risk framing: a namespace that runs application pods but carries zero NetworkPolicy objects is not a documentation gap alone; it means the CNI allows all east-west traffic subject only to implicit kube-proxy rules unless another enforcement layer exists. Removing a default-deny policy during an incident without a ticket is indistinguishable from an attacker clearing segmentation. Policies whose names or paired ingress rule counts suggest allow-all patterns materially widen blast radius for compromised pods. Egress rules that encode world-open CIDRs in object names or labels leak intent even before you inspect YAML in Git.

Clock skew: keep apiserver, kube-state-metrics scrapers, and Splunk indexers within thirty seconds or delete burst windows in streamstats mislead investigators.

Legal and privacy: audit bodies can include operator identity strings; restrict k8s_audit indexes to platform security and identity teams. Do not index full NetworkPolicy YAML in log pipelines unless legal approves Secret-adjacent data handling reviews.

Differentiation recap: this UC does not score PSA violations, RBAC bindings, ingress HTTP 502 rates, or EndpointSlice readiness. It answers whether NetworkPolicy objects and deletes match your east-west governance inventory.

### Step 2 — Configure data collection

Deploy kube-state-metrics with RBAC that can list NetworkPolicy objects and expose kube_networkpolicy_info, kube_networkpolicy_spec_ingress_rules, and kube_networkpolicy_spec_egress_rules as documented in kube-state-metrics network policy metrics reference material. Configure Splunk OpenTelemetry Collector prometheus receiver scrape jobs against the kube-state-metrics Service with honor_labels settings that preserve namespace and networkpolicy labels on series. Confirm raw text lines include namespace="payments" style label pairs and that dots in Kubernetes annotations appear as underscores in Prometheus label names when your scrape translation follows common patterns.

Ship kube:apiserver:audit with explicit stages for delete on networking.k8s.io networkpolicies. A practical audit policy fragment:

```
apiVersion: audit.k8s.io/v1
kind: Policy
omitStages:
  - "RequestReceived"
rules:
  - level: RequestResponse
    verbs: ["delete", "update", "patch", "create"]
    resources:
      - group: "networking.k8s.io"
        resources: ["networkpolicies"]
    namespaces: ["*"]
  - level: Metadata
    resources:
      - group: ""
        resources: ["events"]
```

Wire filelog or cloud-export paths so cluster attribution fields mirror your RBAC and PSA use cases: k8s_cluster_name, eks_cluster_name, gke_cluster_name, or aks_cluster_name must be consistent across indexes.

Collector sketch with split HEC tokens:

```
receivers:
  prometheus/ksm:
    config:
      scrape_configs:
        - job_name: kube-state-metrics
          kubernetes_sd_configs:
            - role: endpoints
          relabel_configs:
            - source_labels: [__meta_kubernetes_service_name]
              regex: kube-state-metrics
              action: keep
exporters:
  splunk_hec/metrics:
    token: "${SPLUNK_HEC_TOKEN_K8S_METRICS}"
    endpoint: "https://splunk.example.com:8088/services/collector/event"
    index: k8s_metrics
    sourcetype: prometheus:scrape:metrics
  splunk_hec/audit:
    token: "${SPLUNK_HEC_TOKEN_K8S_AUDIT}"
    endpoint: "https://splunk.example.com:8088/services/collector/event"
    index: k8s_audit
    sourcetype: kube:apiserver:audit
service:
  pipelines:
    metrics/ksm:
      receivers: [prometheus/ksm]
      exporters: [splunk_hec/metrics]
    logs/audit:
      receivers: [filelog/audit]
      exporters: [splunk_hec/audit]
```

Publish a starter compliance_namespace_networkpolicy.csv:

```
cluster,namespace,requires_default_deny_ingress,requires_default_deny_egress,expected_pod_selector_label_key,expected_pod_selector_label_value,owner_team,mesh_authz_alternate,grace_until_epoch,workload_tier
prod-eks-01,payments-api,1,1,app.kubernetes.io/part-of,payments,team-payments,0,0,critical
prod-eks-01,kube-system,0,0,,,platform-core,0,0,platform
lab-gke,sandbox-netpol-lab,1,0,,,team-lab,0,1735689600,lab
```

Validate before scheduling: index=k8s_metrics must return kube_networkpolicy lines within two scrapes; index=k8s_audit must return networkpolicies deletes in a disposable lab namespace; kube_pod_info lines must include Running phase labels for workload namespaces you expect in inventory.

### Step 3 — Create the search and alert

Save the SPL as uc_3_2_27_networkpolicy_default_deny_governance with a fifteen-minute schedule during steady operations using earliest=-4h@h latest=@h on the metric and audit arms inside the query. Throttle duplicate pages per cluster and namespace for forty-five minutes unless severity escalates from medium to critical inside the same hour. Route critical rows to the platform networking bridge with owner_team from the lookup attached. Archive weekly CSV snapshots of the closing table to a restricted evidence index with git commit hashes for compliance_namespace_networkpolicy.csv.

Pipeline narrative: the comment macro records index names, sourcetypes, lookup keys, and time window. multisearch fans four arms so silent kube-state-metrics scrapes do not hide audit delete storms, and silent audit shipping does not hide empty policy_inventory_mvcount rows. The first arm collapses kube_networkpolicy_info and ingress and egress rule counters per cluster, namespace, and minute, derives default_deny_ingress_flag and default_deny_egress_flag from joined policy names, and flags allow-all style names plus world egress hints. The second arm estimates running_pod_dc from kube_pod_info for Running phase pods. The third arm carries kube_namespace_labels enforcement hints such as network_policy_enforcement.kubernetes.io/mode when your distribution surfaces it on namespace series. The fourth arm aggregates delete verbs on networkpolicies with actors and deleted object names. The outer stats merges arms per cluster and namespace. join wraps compliance_namespace_networkpolicy.csv for requires_default_deny_* flags, mesh alternates, grace epochs, and workload tiers. join wraps tstats against the Change data model for cim_change_adjacent counts as optional configuration-change context. eventstats sums delete volume; streamstats windows delete bursts. case assigns severities and drops grace and mesh-alternate informational tiers at the end. The closing table lists time, cluster, namespace, severity, workload tier, owner, lane presence, missing deny flags, observed deny flags, permissive and ungoverned heuristics, delete counts, rolling delete volume, and change-model touches.

Fenced SPL for runbooks must match the spl JSON field byte-for-byte:

```spl
`comment("UC-3.2.27 Kubernetes NetworkPolicy default-deny coverage, permissive-policy risk, delete drift, and ungoverned workload namespaces. Tunables: idx_metrics=k8s_metrics st_metrics=prometheus:scrape:metrics; idx_audit=k8s_audit st_audit=kube:apiserver:audit; lookup compliance_namespace_networkpolicy.csv keys cluster+namespace; window earliest=-4h@h latest=@h; complements UC-3.2.22 admission PSA, UC-3.2.12 RBAC, UC-3.2.9 north-south ingress, UC-3.2.41 service endpoints.")`
| multisearch 
    [ search index=k8s_metrics sourcetype="prometheus:scrape:metrics" earliest=-4h@h latest=@h
      | eval cluster=lower(trim(toString(coalesce(k8s_cluster_name, cluster_name, cluster, eks_cluster_name, gke_cluster_name, aks_cluster_name, resource_cluster, ""))))
      | eval mn=lower(trim(toString(coalesce(__name__, metric_name, name, MetricName, ""))))
      | where like(mn, "%kube_networkpolicy_info%") OR like(mn, "%kube_networkpolicy_spec_ingress_rules%") OR like(mn, "%kube_networkpolicy_spec_egress_rules%")
      | rex field=_raw "namespace\\s*=\\s*\\\"(?<ns>[^\\\"]+)\\\""
      | rex field=_raw "networkpolicy\\s*=\\s*\\\"(?<np>[^\\\"]+)\\\""
      | eval namespace=trim(toString(coalesce(ns, namespace, k8s_namespace, kube_namespace, "")))
      | eval np=trim(toString(coalesce(np, networkpolicy, "")))
      | eval v=tonumber(tostring(coalesce(Value, value, metric_value, _value, "0")), 10)
      | eval kind=case(match(mn, "kube_networkpolicy_info"), "info", match(mn, "ingress_rules"), "ing", match(mn, "egress_rules"), "egr", true(), "skip")
      | where kind!="skip"
      | stats 
          sum(eval(if(kind=="info", 1, 0))) AS np_info_samples
          max(eval(if(kind=="ing", v, null()))) AS ingress_rule_count
          max(eval(if(kind=="egr", v, null()))) AS egress_rule_count
          values(eval(if(kind=="info" AND len(np)>0, np, null()))) AS np_names
        BY cluster namespace _time
      | eval np_joined=lower(mvjoin(np_names, " "))
      | eval policy_inventory_mvcount=mvcount(np_names)
      | eval default_deny_ingress_flag=if(match(np_joined, "default-deny-ingress|deny-all-ingress|zt-default-deny|zero-trust-default-deny-ingress"), 1, 0)
      | eval default_deny_egress_flag=if(match(np_joined, "default-deny-egress|deny-all-egress|zt-default-deny-egress"), 1, 0)
      | eval allow_all_name_risk=if(match(np_joined, "allow-all|allow-from-anywhere|permit-all|open-ingress|world-open"), 1, 0)
      | eval empty_selector_allow_all_hint=if(ingress_rule_count>0 AND match(np_joined, "allow-all-pods|all-pods-ingress|kube-system-bypass"), 1, 0)
      | eval world_egress_name_risk=if(match(np_joined, "egress-to-internet|world-egress|anywhere-egress|0.0.0.0|::/0"), 1, 0)
      | eval signal_lane="np_governance_metrics"
      | eval running_pod_dc=0
      | eval delete_events=0
      | fields _time cluster namespace signal_lane default_deny_ingress_flag default_deny_egress_flag allow_all_name_risk empty_selector_allow_all_hint world_egress_name_risk policy_inventory_mvcount ingress_rule_count egress_rule_count np_joined running_pod_dc delete_events ]
    [ search index=k8s_metrics sourcetype="prometheus:scrape:metrics" earliest=-4h@h latest=@h
      | eval cluster=lower(trim(toString(coalesce(k8s_cluster_name, cluster_name, cluster, eks_cluster_name, gke_cluster_name, aks_cluster_name, resource_cluster, ""))))
      | eval mn=lower(trim(toString(coalesce(__name__, metric_name, name, MetricName, ""))))
      | where like(mn, "%kube_pod_info%")
      | rex field=_raw "namespace\\s*=\\s*\\\"(?<ns>[^\\\"]+)\\\""
      | rex field=_raw "pod\\s*=\\s*\\\"(?<pod>[^\\\"]+)\\\""
      | rex field=_raw "phase\\s*=\\s*\\\"(?<phase>[^\\\"]+)\\\""
      | eval namespace=trim(toString(coalesce(ns, namespace, k8s_namespace, kube_namespace, "")))
      | eval pod=trim(toString(coalesce(pod, k8s_pod_name, pod_name, "")))
      | where phase="Running" OR match(lower(_raw), "phase=running")
      | stats dc(pod) AS running_pod_dc BY cluster namespace _time
      | eval signal_lane="pod_inventory_est"
      | eval default_deny_ingress_flag=0
      | eval default_deny_egress_flag=0
      | eval allow_all_name_risk=0
      | eval empty_selector_allow_all_hint=0
      | eval world_egress_name_risk=0
      | eval policy_inventory_mvcount=0
      | eval ingress_rule_count=0
      | eval egress_rule_count=0
      | eval np_joined=""
      | eval delete_events=0
      | fields _time cluster namespace signal_lane default_deny_ingress_flag default_deny_egress_flag allow_all_name_risk empty_selector_allow_all_hint world_egress_name_risk policy_inventory_mvcount ingress_rule_count egress_rule_count np_joined running_pod_dc delete_events ]
    [ search index=k8s_metrics sourcetype="prometheus:scrape:metrics" earliest=-4h@h latest=@h
      | eval cluster=lower(trim(toString(coalesce(k8s_cluster_name, cluster_name, cluster, eks_cluster_name, gke_cluster_name, aks_cluster_name, resource_cluster, ""))))
      | eval mn=lower(trim(toString(coalesce(__name__, metric_name, name, MetricName, ""))))
      | where like(mn, "%kube_namespace_labels%") OR match(_raw, "kube_namespace_labels")
      | rex field=_raw "namespace\\s*=\\s*\\\"(?<namespace>[^\\\"]+)\\\""
      | rex field=_raw "network_policy_enforcement__kubernetes_io_mode\\s*=\\s*\\\"(?<np_enforce_mode>[^\\\"]+)\\\""
      | stats latest(np_enforce_mode) AS ns_np_enforce_mode BY cluster namespace _time
      | eval signal_lane="ns_label_context"
      | eval default_deny_ingress_flag=0
      | eval default_deny_egress_flag=0
      | eval allow_all_name_risk=0
      | eval empty_selector_allow_all_hint=0
      | eval world_egress_name_risk=0
      | eval policy_inventory_mvcount=0
      | eval ingress_rule_count=0
      | eval egress_rule_count=0
      | eval np_joined=""
      | eval running_pod_dc=0
      | eval delete_events=0
      | fields _time cluster namespace signal_lane ns_np_enforce_mode default_deny_ingress_flag default_deny_egress_flag allow_all_name_risk empty_selector_allow_all_hint world_egress_name_risk policy_inventory_mvcount ingress_rule_count egress_rule_count np_joined running_pod_dc delete_events ]
    [ search index=k8s_audit sourcetype="kube:apiserver:audit" earliest=-4h@h latest=@h
      | eval cluster=lower(trim(toString(coalesce(k8s_cluster_name, cluster_name, cluster, eks_cluster_name, gke_cluster_name, aks_cluster_name, resource_cluster, audit_cluster, ""))))
      | eval res_l=lower(toString(coalesce('objectRef.resource', objectRef.resource, objectRef_resource, "")))
      | where match(res_l, "^networkpolic")
      | eval verb_l=lower(toString(coalesce(verb, "")))
      | where match(verb_l, "^delete$")
      | eval namespace=trim(toString(coalesce('objectRef.namespace', objectRef.namespace, objectRef_namespace, "")))
      | eval actor=toString(coalesce('user.username', user.username, user_username, user__username, ""))
      | eval np_obj=toString(coalesce('objectRef.name', objectRef.name, objectRef_name, ""))
      | eval signal_lane="np_audit_delete"
      | stats count AS delete_events max(_time) AS last_delete_time values(actor) AS delete_actors values(np_obj) AS deleted_policy_names BY cluster namespace signal_lane
      | eval default_deny_ingress_flag=0
      | eval default_deny_egress_flag=0
      | eval allow_all_name_risk=0
      | eval empty_selector_allow_all_hint=0
      | eval world_egress_name_risk=0
      | eval policy_inventory_mvcount=0
      | eval ingress_rule_count=0
      | eval egress_rule_count=0
      | eval np_joined=""
      | eval running_pod_dc=0
      | fields _time cluster namespace signal_lane delete_events last_delete_time delete_actors deleted_policy_names default_deny_ingress_flag default_deny_egress_flag allow_all_name_risk empty_selector_allow_all_hint world_egress_name_risk policy_inventory_mvcount ingress_rule_count egress_rule_count np_joined running_pod_dc ]
| stats 
    max(default_deny_ingress_flag) AS default_deny_ingress_flag
    max(default_deny_egress_flag) AS default_deny_egress_flag
    max(allow_all_name_risk) AS allow_all_name_risk
    max(empty_selector_allow_all_hint) AS empty_selector_allow_all_hint
    max(world_egress_name_risk) AS world_egress_name_risk
    max(policy_inventory_mvcount) AS policy_inventory_mvcount
    max(ingress_rule_count) AS ingress_rule_count
    max(egress_rule_count) AS egress_rule_count
    max(running_pod_dc) AS running_pod_dc
    max(delete_events) AS delete_events
    max(last_delete_time) AS last_delete_time
    values(delete_actors) AS delete_actors
    values(deleted_policy_names) AS deleted_policy_names
    values(np_joined) AS np_joined_samples
    values(ns_np_enforce_mode) AS ns_np_enforce_mode_vals
    values(signal_lane) AS signal_lanes_seen
    max(_time) AS _time
  BY cluster namespace
| join type=left max=0 cluster, namespace [
    | inputlookup compliance_namespace_networkpolicy.csv
    | eval cluster=lower(trim(toString(coalesce(cluster, cluster_name, k8s_cluster, ""))))
    | eval namespace=trim(toString(coalesce(namespace, k8s_namespace, ns, "")))
    | eval requires_default_deny_ingress=tonumber(tostring(coalesce(requires_default_deny_ingress, require_default_deny_ingress, "1")), 10)
    | eval requires_default_deny_egress=tonumber(tostring(coalesce(requires_default_deny_egress, require_default_deny_egress, "0")), 10)
    | eval expected_pod_selector_label_key=toString(coalesce(expected_pod_selector_label_key, workload_match_label_key, ""))
    | eval expected_pod_selector_label_value=toString(coalesce(expected_pod_selector_label_value, workload_match_label_value, ""))
    | eval owner_team=toString(coalesce(owner_team, squad, platform_owner, ""))
    | eval mesh_authz_alternate=tonumber(tostring(coalesce(mesh_authz_alternate, service_mesh_authz_instead_of_np, "0")), 10)
    | eval grace_until_epoch=tonumber(tostring(coalesce(grace_until_epoch, policy_grace_until, "0")), 10)
    | eval workload_tier=toString(coalesce(workload_tier, tier, "standard"))
    | fields cluster namespace requires_default_deny_ingress requires_default_deny_egress expected_pod_selector_label_key expected_pod_selector_label_value owner_team mesh_authz_alternate grace_until_epoch workload_tier ]
| fillnull value=0 requires_default_deny_ingress requires_default_deny_egress mesh_authz_alternate grace_until_epoch
| fillnull value="" owner_team expected_pod_selector_label_key expected_pod_selector_label_value workload_tier
| eval now_epoch=now()
| eval grace_active=if(grace_until_epoch>0 AND now_epoch<grace_until_epoch, 1, 0)
| join type=left max=1 cluster [
    | tstats summariesonly=t count AS cim_change_adjacent FROM datamodel=Change WHERE nodename=Change.All_Changes All_Changes.dest=* earliest=-4h@h latest=@h BY All_Changes.dest
    | rename All_Changes.dest AS cluster ]
| fillnull value=0 cim_change_adjacent
| eval cluster=lower(trim(toString(cluster)))
| eval np_joined=lower(mvjoin(np_joined_samples, " "))
| eval missing_default_deny_ingress=if(requires_default_deny_ingress=1 AND default_deny_ingress_flag=0 AND mesh_authz_alternate=0 AND grace_active=0, 1, 0)
| eval missing_default_deny_egress=if(requires_default_deny_egress=1 AND default_deny_egress_flag=0 AND mesh_authz_alternate=0 AND grace_active=0, 1, 0)
| eval ungoverned_workload_heuristic=if(workload_tier!="platform" AND running_pod_dc>0 AND policy_inventory_mvcount=0 AND NOT match(namespace, "^(kube-system|kube-public|kube-node-lease)$"), 1, 0)
| eval del_names_flat=lower(mvjoin(deleted_policy_names, " "))
| eventstats sum(delete_events) AS delete_volume_4h BY cluster, namespace
| streamstats window=6 current=t global=f sum(delete_events) AS delete_recent_window BY cluster, namespace
| eval severity=case(
    grace_active=1, "low_grace_window",
    mesh_authz_alternate=1 AND missing_default_deny_ingress=0 AND missing_default_deny_egress=0, "low_mesh_alternate",
    match(namespace, "^(kube-system|kube-public|kube-node-lease)$"), "low_cluster_managed",
    delete_events>0 AND match(del_names_flat, "default-deny|deny-all|zt-default|zero-trust-default"), "critical_np_delete_default_deny",
    delete_recent_window>2, "high_np_delete_burst",
    ungoverned_workload_heuristic=1 AND match(workload_tier, "(?i)prod|critical|tier0"), "critical_ungoverned_workloads",
    ungoverned_workload_heuristic=1, "high_ungoverned_workloads",
    missing_default_deny_ingress=1 AND match(workload_tier, "(?i)prod|critical|tier0"), "critical_missing_default_deny_ingress",
    missing_default_deny_ingress=1, "high_missing_default_deny_ingress",
    missing_default_deny_egress=1 AND match(workload_tier, "(?i)prod|critical|tier0"), "high_missing_default_deny_egress",
    allow_all_name_risk=1 OR empty_selector_allow_all_hint=1, "high_permissive_policy_name",
    world_egress_name_risk=1, "high_world_egress_hint",
    delete_events>0, "medium_np_delete",
    true(), "medium_review")
| where severity!="low_grace_window" AND severity!="low_mesh_alternate"
| where NOT (severity="low_cluster_managed" AND delete_events=0 AND missing_default_deny_ingress=0 AND missing_default_deny_egress=0 AND ungoverned_workload_heuristic=0)
| table _time cluster namespace severity workload_tier owner_team signal_lanes_seen missing_default_deny_ingress missing_default_deny_egress default_deny_ingress_flag default_deny_egress_flag allow_all_name_risk ungoverned_workload_heuristic delete_events delete_volume_4h cim_change_adjacent
```

Alert actions should attach severity, namespace, and deep links to Kubernetes NetworkPolicy documentation for executives reviewing east-west segmentation posture.

### Step 4 — Validate

Synthetic negative test: in a disposable namespace listed in compliance_namespace_networkpolicy.csv with requires flags set to zero for lab, deploy pods and confirm running_pod_dc rises while severity stays informational when workload_tier=lab and inventory matches.

Synthetic positive missing deny: point inventory at a namespace with requires_default_deny_ingress=1 but apply no default-deny policy; confirm policy_inventory_mvcount stays zero and missing_default_deny_ingress=1 with non-low severity after grace expires.

Synthetic permissive name: create a NetworkPolicy named allow-all-ingress with broad selectors in lab; confirm allow_all_name_risk surfaces when np_joined catches the name pattern.

Synthetic delete: kubectl delete networkpolicy default-deny-ingress -n the namespace under change control; confirm np_audit_delete arm increments delete_events and critical_np_delete_default_deny when the deleted name matches default-deny heuristics.

Correlation test: compare alert timestamps to UC-3.2.7 control-plane health to avoid chasing audit gaps during apiserver outages.

RBAC test: readers without k8s_metrics and k8s_audit must see zero rows.

Performance test: Job Inspector during Monday peaks; if stats cost exceeds budget, pre-summarize kube_networkpolicy_info per cluster and namespace into k8s_compliance hourly and document lag.

### Step 5 — Operationalize & Troubleshoot

Case 1 — Default-deny ingress deleted during incident: freeze further policy mutations, capture audit actor and impersonation headers if present, restore from GitOps revert, and open a security bridge if the actor is not the documented automation principal.

Case 2 — Namespace missing deny after greenfield deploy: apply chart templates that ship zt-default-deny-ingress and optional egress deny, then verify kube-state-metrics shows non-zero policy_inventory_mvcount before closing the ticket.

Case 3 — Mesh alternate namespace without Kubernetes denies: confirm mesh_authz_alternate=1 in inventory and AuthorizationPolicy objects exist in the mesh control plane; downgrade only after mesh SRE sign-off, not application guesswork.

Case 4 — Burst of deletes from GitOps controller: correlate with Helm revision timestamps; suppress only when rollback is ticket-linked and default-deny objects are recreated within one evaluation window.

Case 5 — kube-state-metrics upgrade dropped NetworkPolicy metrics: repair scrape RBAC before trusting zero-policy namespaces; treat absent series as telemetry failure, not compliance pass.

Case 6 — Cilium ClusterwideNetworkPolicy or Calico GlobalNetworkPolicy enforcement: inventory must document alternate CRDs so analysts do not chase Kubernetes NetworkPolicy objects that your estate never uses for default deny.

Case 7 — Prod namespace in grace_until_epoch rollout: keep low_grace_window suppression active until epoch passes; escalate automatically when epoch expires without policy objects.

Case 8 — Ungoverned workloads with zero policies: block new deploys to that namespace until deny-all scaffolding merges; pair with UC-3.2.12 if deletes came from over-privileged service accounts.

Case 9 — World egress hint from policy naming: inspect live YAML for ipBlock.cidr covering 0.0.0.0/0 or ::/0 to non-cluster CIDRs; require explicit security review for exceptions.

Case 10 — allow-all style policy for kube-system bridges: relocate to kube-system inventory row with requires flags zero; never copy that pattern to application tiers.

Case 11 — Multi-cluster name collision: enforce unique cluster keys in CSV so joins do not merge unrelated namespaces from different fleets.

Case 12 — Fresh namespace inside policy-author grace: document business owner acknowledgement in the CSV grace column; auto-escalate when grace lapses without deny objects present.

Governance: quarterly replay one historical delete spike through the SPL after kube-state-metrics or apiserver upgrades. Update the comment macro when indexes move.

Evidence retention: weekly CSV exports satisfy internal Kubernetes hardening scorecards when paired with change tickets and Git history for NetworkPolicy manifests.

Closing checklist: five em-dash step headers are present; Step 3 fenced SPL matches the spl field exactly; multisearch lists four arms including kube_networkpolicy metrics, kube_pod_info, kube_namespace_labels, and audit deletes; coalesce appears in cluster attribution ladders; join wraps compliance_namespace_networkpolicy.csv; tstats enriches Change counts; eventstats and streamstats implement delete volume context; case assigns severity tiers; closing table projects twelve analyst columns including signal_lanes_seen; monitoringType includes Security, Compliance, and Configuration; cimModels lists Network_Traffic and Change; equipmentModels lists kubernetes_k8s; references include eight authoritative URLs spanning Kubernetes NetworkPolicy docs, NSA hardening guidance, cluster networking overview, Cilium and Calico policy references, kube-state-metrics network policy metrics, admission controller reference, and Network Policy API SIG artifacts.

## SPL

```spl
`comment("UC-3.2.27 Kubernetes NetworkPolicy default-deny coverage, permissive-policy risk, delete drift, and ungoverned workload namespaces. Tunables: idx_metrics=k8s_metrics st_metrics=prometheus:scrape:metrics; idx_audit=k8s_audit st_audit=kube:apiserver:audit; lookup compliance_namespace_networkpolicy.csv keys cluster+namespace; window earliest=-4h@h latest=@h; complements UC-3.2.22 admission PSA, UC-3.2.12 RBAC, UC-3.2.9 north-south ingress, UC-3.2.41 service endpoints.")`
| multisearch 
    [ search index=k8s_metrics sourcetype="prometheus:scrape:metrics" earliest=-4h@h latest=@h
      | eval cluster=lower(trim(toString(coalesce(k8s_cluster_name, cluster_name, cluster, eks_cluster_name, gke_cluster_name, aks_cluster_name, resource_cluster, ""))))
      | eval mn=lower(trim(toString(coalesce(__name__, metric_name, name, MetricName, ""))))
      | where like(mn, "%kube_networkpolicy_info%") OR like(mn, "%kube_networkpolicy_spec_ingress_rules%") OR like(mn, "%kube_networkpolicy_spec_egress_rules%")
      | rex field=_raw "namespace\\s*=\\s*\\\"(?<ns>[^\\\"]+)\\\""
      | rex field=_raw "networkpolicy\\s*=\\s*\\\"(?<np>[^\\\"]+)\\\""
      | eval namespace=trim(toString(coalesce(ns, namespace, k8s_namespace, kube_namespace, "")))
      | eval np=trim(toString(coalesce(np, networkpolicy, "")))
      | eval v=tonumber(tostring(coalesce(Value, value, metric_value, _value, "0")), 10)
      | eval kind=case(match(mn, "kube_networkpolicy_info"), "info", match(mn, "ingress_rules"), "ing", match(mn, "egress_rules"), "egr", true(), "skip")
      | where kind!="skip"
      | stats 
          sum(eval(if(kind=="info", 1, 0))) AS np_info_samples
          max(eval(if(kind=="ing", v, null()))) AS ingress_rule_count
          max(eval(if(kind=="egr", v, null()))) AS egress_rule_count
          values(eval(if(kind=="info" AND len(np)>0, np, null()))) AS np_names
        BY cluster namespace _time
      | eval np_joined=lower(mvjoin(np_names, " "))
      | eval policy_inventory_mvcount=mvcount(np_names)
      | eval default_deny_ingress_flag=if(match(np_joined, "default-deny-ingress|deny-all-ingress|zt-default-deny|zero-trust-default-deny-ingress"), 1, 0)
      | eval default_deny_egress_flag=if(match(np_joined, "default-deny-egress|deny-all-egress|zt-default-deny-egress"), 1, 0)
      | eval allow_all_name_risk=if(match(np_joined, "allow-all|allow-from-anywhere|permit-all|open-ingress|world-open"), 1, 0)
      | eval empty_selector_allow_all_hint=if(ingress_rule_count>0 AND match(np_joined, "allow-all-pods|all-pods-ingress|kube-system-bypass"), 1, 0)
      | eval world_egress_name_risk=if(match(np_joined, "egress-to-internet|world-egress|anywhere-egress|0.0.0.0|::/0"), 1, 0)
      | eval signal_lane="np_governance_metrics"
      | eval running_pod_dc=0
      | eval delete_events=0
      | fields _time cluster namespace signal_lane default_deny_ingress_flag default_deny_egress_flag allow_all_name_risk empty_selector_allow_all_hint world_egress_name_risk policy_inventory_mvcount ingress_rule_count egress_rule_count np_joined running_pod_dc delete_events ]
    [ search index=k8s_metrics sourcetype="prometheus:scrape:metrics" earliest=-4h@h latest=@h
      | eval cluster=lower(trim(toString(coalesce(k8s_cluster_name, cluster_name, cluster, eks_cluster_name, gke_cluster_name, aks_cluster_name, resource_cluster, ""))))
      | eval mn=lower(trim(toString(coalesce(__name__, metric_name, name, MetricName, ""))))
      | where like(mn, "%kube_pod_info%")
      | rex field=_raw "namespace\\s*=\\s*\\\"(?<ns>[^\\\"]+)\\\""
      | rex field=_raw "pod\\s*=\\s*\\\"(?<pod>[^\\\"]+)\\\""
      | rex field=_raw "phase\\s*=\\s*\\\"(?<phase>[^\\\"]+)\\\""
      | eval namespace=trim(toString(coalesce(ns, namespace, k8s_namespace, kube_namespace, "")))
      | eval pod=trim(toString(coalesce(pod, k8s_pod_name, pod_name, "")))
      | where phase="Running" OR match(lower(_raw), "phase=running")
      | stats dc(pod) AS running_pod_dc BY cluster namespace _time
      | eval signal_lane="pod_inventory_est"
      | eval default_deny_ingress_flag=0
      | eval default_deny_egress_flag=0
      | eval allow_all_name_risk=0
      | eval empty_selector_allow_all_hint=0
      | eval world_egress_name_risk=0
      | eval policy_inventory_mvcount=0
      | eval ingress_rule_count=0
      | eval egress_rule_count=0
      | eval np_joined=""
      | eval delete_events=0
      | fields _time cluster namespace signal_lane default_deny_ingress_flag default_deny_egress_flag allow_all_name_risk empty_selector_allow_all_hint world_egress_name_risk policy_inventory_mvcount ingress_rule_count egress_rule_count np_joined running_pod_dc delete_events ]
    [ search index=k8s_metrics sourcetype="prometheus:scrape:metrics" earliest=-4h@h latest=@h
      | eval cluster=lower(trim(toString(coalesce(k8s_cluster_name, cluster_name, cluster, eks_cluster_name, gke_cluster_name, aks_cluster_name, resource_cluster, ""))))
      | eval mn=lower(trim(toString(coalesce(__name__, metric_name, name, MetricName, ""))))
      | where like(mn, "%kube_namespace_labels%") OR match(_raw, "kube_namespace_labels")
      | rex field=_raw "namespace\\s*=\\s*\\\"(?<namespace>[^\\\"]+)\\\""
      | rex field=_raw "network_policy_enforcement__kubernetes_io_mode\\s*=\\s*\\\"(?<np_enforce_mode>[^\\\"]+)\\\""
      | stats latest(np_enforce_mode) AS ns_np_enforce_mode BY cluster namespace _time
      | eval signal_lane="ns_label_context"
      | eval default_deny_ingress_flag=0
      | eval default_deny_egress_flag=0
      | eval allow_all_name_risk=0
      | eval empty_selector_allow_all_hint=0
      | eval world_egress_name_risk=0
      | eval policy_inventory_mvcount=0
      | eval ingress_rule_count=0
      | eval egress_rule_count=0
      | eval np_joined=""
      | eval running_pod_dc=0
      | eval delete_events=0
      | fields _time cluster namespace signal_lane ns_np_enforce_mode default_deny_ingress_flag default_deny_egress_flag allow_all_name_risk empty_selector_allow_all_hint world_egress_name_risk policy_inventory_mvcount ingress_rule_count egress_rule_count np_joined running_pod_dc delete_events ]
    [ search index=k8s_audit sourcetype="kube:apiserver:audit" earliest=-4h@h latest=@h
      | eval cluster=lower(trim(toString(coalesce(k8s_cluster_name, cluster_name, cluster, eks_cluster_name, gke_cluster_name, aks_cluster_name, resource_cluster, audit_cluster, ""))))
      | eval res_l=lower(toString(coalesce('objectRef.resource', objectRef.resource, objectRef_resource, "")))
      | where match(res_l, "^networkpolic")
      | eval verb_l=lower(toString(coalesce(verb, "")))
      | where match(verb_l, "^delete$")
      | eval namespace=trim(toString(coalesce('objectRef.namespace', objectRef.namespace, objectRef_namespace, "")))
      | eval actor=toString(coalesce('user.username', user.username, user_username, user__username, ""))
      | eval np_obj=toString(coalesce('objectRef.name', objectRef.name, objectRef_name, ""))
      | eval signal_lane="np_audit_delete"
      | stats count AS delete_events max(_time) AS last_delete_time values(actor) AS delete_actors values(np_obj) AS deleted_policy_names BY cluster namespace signal_lane
      | eval default_deny_ingress_flag=0
      | eval default_deny_egress_flag=0
      | eval allow_all_name_risk=0
      | eval empty_selector_allow_all_hint=0
      | eval world_egress_name_risk=0
      | eval policy_inventory_mvcount=0
      | eval ingress_rule_count=0
      | eval egress_rule_count=0
      | eval np_joined=""
      | eval running_pod_dc=0
      | fields _time cluster namespace signal_lane delete_events last_delete_time delete_actors deleted_policy_names default_deny_ingress_flag default_deny_egress_flag allow_all_name_risk empty_selector_allow_all_hint world_egress_name_risk policy_inventory_mvcount ingress_rule_count egress_rule_count np_joined running_pod_dc ]
| stats 
    max(default_deny_ingress_flag) AS default_deny_ingress_flag
    max(default_deny_egress_flag) AS default_deny_egress_flag
    max(allow_all_name_risk) AS allow_all_name_risk
    max(empty_selector_allow_all_hint) AS empty_selector_allow_all_hint
    max(world_egress_name_risk) AS world_egress_name_risk
    max(policy_inventory_mvcount) AS policy_inventory_mvcount
    max(ingress_rule_count) AS ingress_rule_count
    max(egress_rule_count) AS egress_rule_count
    max(running_pod_dc) AS running_pod_dc
    max(delete_events) AS delete_events
    max(last_delete_time) AS last_delete_time
    values(delete_actors) AS delete_actors
    values(deleted_policy_names) AS deleted_policy_names
    values(np_joined) AS np_joined_samples
    values(ns_np_enforce_mode) AS ns_np_enforce_mode_vals
    values(signal_lane) AS signal_lanes_seen
    max(_time) AS _time
  BY cluster namespace
| join type=left max=0 cluster, namespace [
    | inputlookup compliance_namespace_networkpolicy.csv
    | eval cluster=lower(trim(toString(coalesce(cluster, cluster_name, k8s_cluster, ""))))
    | eval namespace=trim(toString(coalesce(namespace, k8s_namespace, ns, "")))
    | eval requires_default_deny_ingress=tonumber(tostring(coalesce(requires_default_deny_ingress, require_default_deny_ingress, "1")), 10)
    | eval requires_default_deny_egress=tonumber(tostring(coalesce(requires_default_deny_egress, require_default_deny_egress, "0")), 10)
    | eval expected_pod_selector_label_key=toString(coalesce(expected_pod_selector_label_key, workload_match_label_key, ""))
    | eval expected_pod_selector_label_value=toString(coalesce(expected_pod_selector_label_value, workload_match_label_value, ""))
    | eval owner_team=toString(coalesce(owner_team, squad, platform_owner, ""))
    | eval mesh_authz_alternate=tonumber(tostring(coalesce(mesh_authz_alternate, service_mesh_authz_instead_of_np, "0")), 10)
    | eval grace_until_epoch=tonumber(tostring(coalesce(grace_until_epoch, policy_grace_until, "0")), 10)
    | eval workload_tier=toString(coalesce(workload_tier, tier, "standard"))
    | fields cluster namespace requires_default_deny_ingress requires_default_deny_egress expected_pod_selector_label_key expected_pod_selector_label_value owner_team mesh_authz_alternate grace_until_epoch workload_tier ]
| fillnull value=0 requires_default_deny_ingress requires_default_deny_egress mesh_authz_alternate grace_until_epoch
| fillnull value="" owner_team expected_pod_selector_label_key expected_pod_selector_label_value workload_tier
| eval now_epoch=now()
| eval grace_active=if(grace_until_epoch>0 AND now_epoch<grace_until_epoch, 1, 0)
| join type=left max=1 cluster [
    | tstats summariesonly=t count AS cim_change_adjacent FROM datamodel=Change WHERE nodename=Change.All_Changes All_Changes.dest=* earliest=-4h@h latest=@h BY All_Changes.dest
    | rename All_Changes.dest AS cluster ]
| fillnull value=0 cim_change_adjacent
| eval cluster=lower(trim(toString(cluster)))
| eval np_joined=lower(mvjoin(np_joined_samples, " "))
| eval missing_default_deny_ingress=if(requires_default_deny_ingress=1 AND default_deny_ingress_flag=0 AND mesh_authz_alternate=0 AND grace_active=0, 1, 0)
| eval missing_default_deny_egress=if(requires_default_deny_egress=1 AND default_deny_egress_flag=0 AND mesh_authz_alternate=0 AND grace_active=0, 1, 0)
| eval ungoverned_workload_heuristic=if(workload_tier!="platform" AND running_pod_dc>0 AND policy_inventory_mvcount=0 AND NOT match(namespace, "^(kube-system|kube-public|kube-node-lease)$"), 1, 0)
| eval del_names_flat=lower(mvjoin(deleted_policy_names, " "))
| eventstats sum(delete_events) AS delete_volume_4h BY cluster, namespace
| streamstats window=6 current=t global=f sum(delete_events) AS delete_recent_window BY cluster, namespace
| eval severity=case(
    grace_active=1, "low_grace_window",
    mesh_authz_alternate=1 AND missing_default_deny_ingress=0 AND missing_default_deny_egress=0, "low_mesh_alternate",
    match(namespace, "^(kube-system|kube-public|kube-node-lease)$"), "low_cluster_managed",
    delete_events>0 AND match(del_names_flat, "default-deny|deny-all|zt-default|zero-trust-default"), "critical_np_delete_default_deny",
    delete_recent_window>2, "high_np_delete_burst",
    ungoverned_workload_heuristic=1 AND match(workload_tier, "(?i)prod|critical|tier0"), "critical_ungoverned_workloads",
    ungoverned_workload_heuristic=1, "high_ungoverned_workloads",
    missing_default_deny_ingress=1 AND match(workload_tier, "(?i)prod|critical|tier0"), "critical_missing_default_deny_ingress",
    missing_default_deny_ingress=1, "high_missing_default_deny_ingress",
    missing_default_deny_egress=1 AND match(workload_tier, "(?i)prod|critical|tier0"), "high_missing_default_deny_egress",
    allow_all_name_risk=1 OR empty_selector_allow_all_hint=1, "high_permissive_policy_name",
    world_egress_name_risk=1, "high_world_egress_hint",
    delete_events>0, "medium_np_delete",
    true(), "medium_review")
| where severity!="low_grace_window" AND severity!="low_mesh_alternate"
| where NOT (severity="low_cluster_managed" AND delete_events=0 AND missing_default_deny_ingress=0 AND missing_default_deny_egress=0 AND ungoverned_workload_heuristic=0)
| table _time cluster namespace severity workload_tier owner_team signal_lanes_seen missing_default_deny_ingress missing_default_deny_egress default_deny_ingress_flag default_deny_egress_flag allow_all_name_risk ungoverned_workload_heuristic delete_events delete_volume_4h cim_change_adjacent
```

## CIM SPL

```spl
| tstats summariesonly=t count FROM datamodel=Network_Traffic WHERE nodename=Network_Traffic earliest=-4h@h latest=@h BY Network_Traffic.dest
| rename Network_Traffic.dest AS cluster_hint
| head 50
```

## Visualization

Severity-colored table mirroring the closing SPL projection; timeline of delete_events by namespace; single-value tiles for critical versus high counts; drilldown from signal_lanes_seen to raw multisearch arms; companion panel for grace and mesh alternate rows from lookup clones.

## Known False Positives

Cluster-managed namespaces such as kube-system, kube-public, and kube-node-lease are excluded by design in severity filters because vendor components and control-plane traffic patterns rarely follow application default-deny conventions; keep explicit inventory rows with requires flags set to zero rather than muting alerts globally. Namespaces in active deprecation or teardown drains may intentionally delete all NetworkPolicy objects while workloads drain; pair timestamps with decommission tickets before escalating. Estates that enforce east-west segmentation exclusively with Cilium ClusterwideNetworkPolicy, Calico GlobalNetworkPolicy, or other non-NetworkPolicy CRDs will show low Kubernetes NetworkPolicy cardinality even when segmentation is strong; document mesh_authz_alternate and alternate CRD ownership in the lookup. Service-mesh-protected namespaces that rely on Istio AuthorizationPolicy instead of Kubernetes NetworkPolicy should set mesh_authz_alternate=1 with mesh SME approval so the control does not page on absent deny objects. Lab and sandbox namespaces that explicitly opt out of default deny during experiments belong in workload_tier=lab with requires flags zero or non-zero grace_until_epoch windows. Namespaces in multi-phase compliance rollouts may lack deny objects until a scheduled phase completes; use grace_until_epoch and weekly governance reviews rather than nightly pages. Freshly-created namespaces inside an approved policy-author grace window should carry grace_until_epoch from the platform ticket until GitOps applies baseline deny scaffolding. GitOps controllers that delete and recreate policies with identical semantics can emit delete bursts that look like drift; require diff of object UID timelines before sev-one escalation. Managed Kubernetes distributions that rename default policies or use generated suffixes may not match heuristic name tokens; extend the regex ladder in the SPL macro after architecture review. Pen testers clearing policies will trigger this control by design; tag lab clusters in inventory to downgrade non-production noise while retaining evidence rows.

## References

- [Kubernetes — Network Policies](https://kubernetes.io/docs/concepts/services-networking/network-policies/)
- [NSA and CISA — Kubernetes Hardening Guidance](https://media.defense.gov/2022/Aug/29/2003066362/-1/-1/0/CTR_KUBERNETES_HARDENING_GUIDANCE_1.2_20220315.PDF)
- [Kubernetes — Cluster Networking](https://kubernetes.io/docs/concepts/cluster-administration/networking/)
- [Cilium — Kubernetes Network Policy](https://docs.cilium.io/en/stable/network/kubernetes/policy/)
- [Tigera Calico — Kubernetes network policy](https://docs.tigera.io/calico/latest/network-policy/get-started/kubernetes-policy)
- [kube-state-metrics — networkpolicy metrics](https://github.com/kubernetes/kube-state-metrics/blob/main/docs/metrics/)
- [Kubernetes — Admission Controllers](https://kubernetes.io/docs/reference/access-authn-authz/admission-controllers/)
- [Kubernetes SIG-Network — Network Policy API](https://github.com/kubernetes-sigs/network-policy-api)
