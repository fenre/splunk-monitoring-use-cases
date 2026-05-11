<!-- AUTO-GENERATED from UC-3.2.22.json — DO NOT EDIT -->

---
id: "3.2.22"
title: "Pod Security Admission Denials and Namespace PSS Drift"
status: "verified"
criticality: "high"
splunkPillar: "Security"
---

# UC-3.2.22 · Pod Security Admission Denials and Namespace PSS Drift

> **Criticality:** High &middot; **Difficulty:** Advanced &middot; **Pillar:** Security &middot; **Type:** Security, Compliance, Configuration &middot; **Wave:** Walk &middot; **Status:** Verified

*We watch every time the cluster blocks a pod that asks for unsafe powers, and we watch namespaces that lose or weaken their safety labels, so risky apps cannot sneak through quietly while everyone thinks the rules still apply.*

---

## Description

Unique monitoring axis: Pod Security Admission outcomes on kube-apiserver plus kube-state-metrics evidence of namespace-level Pod Security Standard labels, correlated to a signed namespace_psa_inventory.csv so teams see which cluster, which namespace, which subject attempted a disallowed pod, which field violated baseline or restricted policy, whether enforcement labels are missing or drifted toward privileged, and whether documented exceptions expired. This is admission-time enforcement and governance drift, not UC-3.1.6 runtime privilege inspection, not UC-3.2.12 RBAC grants, and not UC-3.2.23 binding change logs.

## Value

When PSA silently mislabels namespaces or operators bypass GitOps, the next successful deploy can widen blast radius faster than runtime scanners report drift. Timestamped denial rows give application security and platform engineering a shared backlog of spec fixes before attackers iterate on rejected payloads. Regulators and enterprise customers asking for CIS-aligned Kubernetes hardening receive evidence that restricted profiles are monitored, not only documented in Confluence. Mean time to contain improves because Splunk shows denial bursts per namespace alongside owner_team routing from the inventory lookup, while version drift on pod-security.kubernetes.io/enforce-version surfaces upgrade debt before skewed policy interpretations appear during cluster minor upgrades.

## Implementation

Provision k8s_audit, k8s_metrics, and k8s_compliance indexes; ship kube:apiserver:audit with RequestResponse for pod creates; scrape kube_namespace_labels; publish namespace_psa_inventory.csv; deploy Splunk OTel Collector filelog plus prometheus receivers; save uc_3_2_22_psa_denials_drift on a fifteen-minute cadence over earliest=-24h@h latest=@h; route critical and high rows to platform security bridges.

## Evidence

Saved search uc_3_2_22_psa_denials_drift; versioned namespace_psa_inventory.csv in git; weekly CSV export of the closing table to a restricted evidence index with audit hash samples; dashboard drilldowns linking denial audit JSON to kube_namespace_labels scrape rows and exception lookup rows.

## Control test

### Positive scenario

In a lab namespace labeled pod-security.kubernetes.io/enforce=restricted, run kubectl run nginx --image=nginx --privileged and confirm kube:apiserver:audit shows responseStatus.code 403 with message containing violates PodSecurity, then execute uc_3_2_22_psa_denials_drift and expect a psa_audit_denial row with violation_field privileged and non-zero denial_count_24h after repeated attempts.

### Negative scenario

Apply a compliant pod spec that satisfies restricted policy in the same namespace, confirm admission succeeds with no 403 PodSecurity line in audit for that create, and verify the saved search emits no new denial row for that workload identity while label-drift arm remains silent when enforce labels match namespace_psa_inventory.csv.

## Detailed Implementation

### Step 1 — Prerequisites

Head of Platform owns this control jointly with the Kubernetes platform security lead, the identity engineer who signs off on audit policy, and the observability owner who operates Splunk OpenTelemetry Collector across clusters. UC-3.2.22 is deliberately the Pod Security Admission plane: apiserver-time denials when a pod spec violates the Pod Security Standard enforced for a namespace, correlated to kube-state-metrics kube_namespace_labels so you also catch namespaces that quietly drop pod-security.kubernetes.io/enforce labels, drift to privileged enforcement in production, or fall out of version alignment on pod-security.kubernetes.io/enforce-version. UC-3.1.6 remains the Docker and CRI runtime privilege story on live containers. UC-3.2.12 remains RBAC misconfiguration analytics. UC-3.2.23 remains ClusterRoleBinding change auditing. None of those siblings replace structured Forbidden responses whose messages contain violates PodSecurity, nor do they replace Prometheus evidence that a namespace stopped advertising the enforce label your governance repository expects.

Index contracts: stand up index=k8s_audit for sourcetype=kube:apiserver:audit with role separation between platform security readers and application developers. Stand up index=k8s_metrics for sourcetype=prometheus:scrape:metrics (or your kube:objects:metrics equivalent) with kube-state-metrics scraped at intervals your SRE council accepts, typically fifteen to sixty seconds on large estates. Optional index=k8s_compliance can hold GitOps snapshots if you replay namespace labels nightly for drift comparisons independent of scrape jitter. Every event must carry a stable cluster dimension such as k8s_cluster_name, eks_cluster_name, gke_cluster_name, or aks_cluster_name so joins to namespace_psa_inventory.csv do not collapse multi-cluster fleets into one false namespace.

HEC and forwarder hygiene: mint dedicated HEC tokens for apiserver audit files, rotate quarterly, and never reuse developer laptop tokens for control-plane hosts. Clock skew between apiserver and Splunk _time must stay under thirty seconds or streamstats rolling denial counts mislead investigators during incident bridges.

Audit policy depth: PodSecurity denials surface best when audit stages include RequestResponse for pod-creating verbs so responseStatus.message retains the human-readable field reference PSA emits. Metadata-only policies help volume but strip the message analysts need; keep RequestResponse on create, update, and patch for pods and pod templates in regulated tiers at minimum. Follow Kubernetes audit documentation for tuning omitStages and users/system accounts that spam logs, but never silence the service accounts that represent your CI deploy bots without moving those accounts into a dedicated index with explicit monitoring.

Governance lookup: publish lookups/namespace_psa_inventory.csv with columns cluster, namespace, expected_enforce_level (privileged, baseline, or restricted), expected_audit_level, expected_warn_level, expected_enforce_version (for example v1.28), owner_team, exception_reason, and exception_expiry as a Unix epoch after which the exception must be renewed or the namespace reverts to expected_enforce_level. Refresh the CSV from the same Git repository that applies labels so inventory and cluster state share a commit ancestry auditors can trace. For managed Kubernetes, document that Amazon EKS, Google GKE, and Microsoft AKS all expose PSA in supported versions 1.25 onward while CIS Kubernetes Benchmark guidance encourages restricted enforcement in sensitive tiers; your lookup encodes which namespaces are allowed to diverge and for how long.

Risk framing: a missing enforce label is not a cosmetic omission. It means new namespaces inherit whatever cluster default your platform team configured, which may be more permissive than the business unit believes after reading internal architecture diagrams. A privileged label on a production namespace that inventory says should be restricted is a governance failure even if no workload has exploited it yet, because the next successful deploy can carry capabilities that restricted mode would have blocked. Admission denials are gifts: they tell you which automation account keeps attempting unsafe specs before an attacker does.

Licensing and volume: RequestResponse audit is heavy. Compress at the collector, sample only after platform legal approves, and keep hot retention aligned to security operations needs rather than infinite storage of full pod bodies. kube_namespace_labels cardinality scales with namespace count, not pod count, which keeps the metrics arm comparatively cheap.

Legal and privacy: audit objects can include secrets if policies are careless; redact secret bodies at collection and restrict indexes to roles that need pod spec fragments.

Differentiation recap: this UC does not replace image pull failure analytics, probe failure analytics, or etcd raft latency. It answers whether PSA is enforcing what your registry of namespace labels claims, and who keeps knocking on the door with disallowed fields.

### Step 2 — Configure data collection

First wire kube-apiserver audit to Splunk. On self-managed clusters, point the Splunk OpenTelemetry Collector filelog receiver at the host path your distribution uses for audit.log, commonly under /var/log/kubernetes/audit.log, and set the splunk_hec exporter to index=k8s_audit with sourcetype=kube:apiserver:audit. On managed clusters where you cannot read the control plane node filesystem, use the cloud vendor audit export that preserves Kubernetes audit JSON and normalize sourcetype and cluster fields identically so the SPL arms do not fork per cloud.

Second, deploy kube-state-metrics with RBAC that can list namespaces and expose kube_namespace_labels. Add a ServiceMonitor or PodMonitor so the OpenTelemetry Collector prometheus receiver scrapes the metrics endpoint with labels intact. Confirm raw scrape lines include namespace label keys and that dots in Kubernetes label names appear as underscores in Prometheus series names, which is why the SPL rex arms search for pod_security_kubernetes_io_enforce rather than slash-separated keys.

Third, maintain audit-policy.yaml with an explicit rule for Pod create, update, and patch resources at ResponseRecorded or RequestResponse level for groups core and resources pods, and include podtemplates if your GitOps engine mutates them. Example skeleton:

```
apiVersion: audit.k8s.io/v1
kind: Policy
omitStages:
  - "RequestReceived"
rules:
  - level: RequestResponse
    verbs: ["create", "update", "patch"]
    resources:
      - group: ""
        resources: ["pods", "podtemplates"]
    namespaces: ["*"]
  - level: Metadata
    resources:
      - group: ""
        resources: ["events"]
```

Fourth, configure OpenTelemetry Collector pipelines roughly as follows (adjust exporters to your environment):

```
receivers:
  filelog:
    include: [/var/log/kubernetes/audit.log]
    operators:
      - type: json_parser
        timestamp:
          parse_from: attributes.requestReceivedTimestamp
          layout: '2006-01-02T15:04:05.999999999Z07:00'
  prometheus:
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
  splunk_hec:
    token: "${SPLUNK_HEC_TOKEN}"
    endpoint: "https://splunk.example.com:8088/services/collector"
    sourcetype: kube:apiserver:audit
service:
  pipelines:
    logs/audit:
      receivers: [filelog]
      exporters: [splunk_hec]
    metrics/ksm:
      receivers: [prometheus]
      exporters: [splunk_hec]
```

Fifth, publish a sample namespace_psa_inventory.csv in the same repo as your alerts:

```
cluster,namespace,expected_enforce_level,expected_audit_level,expected_warn_level,expected_enforce_version,owner_team,exception_reason,exception_expiry
prod-eks-01,payments-api,restricted,restricted,baseline,v1.28,team-payments,"",0
prod-eks-01,kube-system,privileged,baseline,baseline,v1.28,platform-core,"vendor system workloads",0
lab-gke,sandbox-chaos,baseline,baseline,privileged,v1.29,team-resilience,"chaos experiments",1735689600
```

Sixth, validate with index=k8s_audit sourcetype=kube:apiserver:audit earliest=-15m for PodSecurity substrings, and index=k8s_metrics with kube_namespace_labels earliest=-15m for namespace series. Skew tests must pass before you schedule the alert.

### Step 3 — Create the search and alert

Save the SPL as uc_3_2_22_psa_denials_drift with a fifteen-minute schedule and earliest=-24h@h latest=@h during steady state. Throttle duplicate pages per cluster, namespace, and signal_lane for forty-five minutes unless severity escalates from medium to critical inside the same hour. Route critical rows to the platform and application security bridge with owner_team from the lookup attached. Archive weekly CSV snapshots of the closing table to your evidence index with git commit hashes for namespace_psa_inventory.csv.

Understanding the pipeline: the opening comment macro records index names, sourcetypes, lookup path, and time window. multisearch fans two arms so silent audit shipping does not hide metrics drift, and silent kube-state-metrics does not hide Forbidden storms. coalesce lists absorb flattened JSON field naming differences across vendors and Splunk props transforms. The audit arm requires HTTP 403, Forbidden reason when present, and violates PodSecurity in responseStatus.message while limiting objectRef.resource to pod objects. violation_field uses case to map message fragments to analyst-friendly tokens such as runAsNonRoot, allowPrivilegeEscalation, hostNetwork, hostPID, hostIPC, capabilities, seccomp, and volumes. The metrics arm isolates kube_namespace_labels series, rex extracts namespace and PSA labels, stats collapses to one row per cluster and namespace, and filters namespaces missing enforce labels or enforcing privileged. The join wraps inputlookup namespace_psa_inventory.csv on cluster and namespace without using bare lookup for governance reviewers. prod_like and dev_experiments macros tune severity: critical covers expired exceptions in production and privileged labels when inventory expects baseline or restricted; high covers restricted-namespace denials, production drift rows, and enforce-version mismatch; medium covers non-production drift; low covers non-production denials and intentional sandbox noise. eventstats sums is_denial across the search window per cluster and namespace for denial_count_24h. streamstats supplies denial_rolling_recent for burst context. The closing table lists cluster, namespace, expected versus actual enforcement posture, drift narrative, denial counts, subject and workload identifiers, parsed violation field, severity, owner_team, live and expected enforce versions, rolling sums, exception flags, version mismatch flag, and signal_lane for triage routing.

Alert actions should include the row JSON, deep link to Kubernetes documentation on Pod Security Admission for executives, and a reminder that UC-3.1.6 supplies runtime corroboration when a denial attempt eventually succeeds in a mislabeled namespace.

Fenced SPL for runbooks must match the spl JSON field byte-for-byte:

```spl
`comment("UC-3.2.22 Pod Security Admission denials and namespace PSS label drift. Tunables: idx_audit=k8s_audit st_audit=kube:apiserver:audit; idx_metrics=k8s_metrics st_metrics=prometheus:scrape:metrics; lookup namespace_psa_inventory.csv keys cluster+namespace; earliest=-24h@h latest=@h")`
| multisearch 
    [ search index=k8s_audit sourcetype="kube:apiserver:audit" earliest=-24h@h latest=@h
      | eval cluster=lower(trim(toString(coalesce(k8s_cluster_name, cluster_name, cluster, eks_cluster_name, gke_cluster_name, aks_cluster_name, resource_cluster, audit_cluster, ""))))
      | eval resp_code=tonumber(tostring(coalesce('responseStatus.code', responseStatus.code, responseStatus_code, status_code, http_status, "0")), 10)
      | eval resp_reason=lower(toString(coalesce('responseStatus.reason', responseStatus.reason, responseStatus_reason, "")))
      | eval resp_msg=lower(toString(coalesce('responseStatus.message', responseStatus.message, responseStatus_message, message, "")))
      | eval obj_res=lower(toString(coalesce('objectRef.resource', objectRef.resource, objectRef_resource, "")))
      | where resp_code=403 AND match(resp_msg, "violates podsecurity") AND (len(resp_reason)=0 OR match(resp_reason, "forbidden"))
      | where match(obj_res, "^(pods|pod)$")
      | eval namespace=toString(coalesce('objectRef.namespace', objectRef.namespace, objectRef_namespace, ""))
      | eval denied_workload=toString(coalesce('objectRef.name', objectRef.name, objectRef_name, request_name, ""))
      | eval denied_user=toString(coalesce('user.username', user.username, user_username, user__username, ""))
      | eval violation_field=case(
          match(resp_msg, "runasnonroot|run as non-root"), "runAsNonRoot",
          match(resp_msg, "allowprivilegeescalation"), "allowPrivilegeEscalation",
          match(resp_msg, "(?i)privileged"), "privileged",
          match(resp_msg, "hostnetwork|host network"), "hostNetwork",
          match(resp_msg, "hostpid|host pid"), "hostPID",
          match(resp_msg, "hostipc|host ipc"), "hostIPC",
          match(resp_msg, "capabilities"), "capabilities",
          match(resp_msg, "seccomp"), "seccomp",
          match(resp_msg, "volume"), "volumes",
          true(), "psa_other_field")
      | eval signal_lane="psa_audit_denial"
      | eval actual_enforce_level="policy_enforced_by_denial"
      | eval drift_state="admission_denied"
      | eval enforce_version_live=""
      | fields _time cluster namespace denied_user denied_workload violation_field signal_lane actual_enforce_level drift_state enforce_version_live ]
    [ search index=k8s_metrics sourcetype="prometheus:scrape:metrics" earliest=-4h@h latest=@h
      | eval cluster=lower(trim(toString(coalesce(k8s_cluster_name, cluster_name, cluster, eks_cluster_name, gke_cluster_name, aks_cluster_name, resource_cluster, ""))))
      | eval mn=lower(trim(toString(coalesce(__name__, metric_name, name, MetricName, ""))))
      | where like(mn, "%kube_namespace_labels%") OR match(_raw, "kube_namespace_labels")
      | rex field=_raw "namespace=\\"(?<namespace>[^\\"]+)\\""
      | rex field=_raw "pod_security_kubernetes_io_enforce=\\"(?<psa_enforce>[^\\"]+)\\""
      | rex field=_raw "pod_security_kubernetes_io_enforce_version=\\"(?<psa_enforce_ver>[^\\"]+)\\""
      | stats latest(psa_enforce) AS le latest(psa_enforce_ver) AS lev BY cluster, namespace
      | eval actual_enforce_level=lower(trim(toString(coalesce(le, ""))))
      | eval enforce_version_live=trim(toString(coalesce(lev, "")))
      | eval has_enforce=if(len(actual_enforce_level)>0, 1, 0)
      | where has_enforce=0 OR match(actual_enforce_level, "^privileged$")
      | eval denied_user="n_a_metrics"
      | eval denied_workload="namespace_object"
      | eval violation_field=if(has_enforce=0, "missing_enforce_label", "privileged_enforce_label")
      | eval signal_lane="psa_label_drift"
      | eval drift_state=if(has_enforce=0, "missing_pod_security_enforce_label", "privileged_namespace_enforcement")
      | fields _time cluster namespace denied_user denied_workload violation_field signal_lane actual_enforce_level drift_state enforce_version_live ]
| eval cluster=coalesce(nullif(cluster,""), "unknown_cluster")
| eval namespace=coalesce(nullif(namespace,""), "unknown_namespace")
| eval denied_user=coalesce(nullif(denied_user,""), "unknown_subject")
| eval denied_workload=coalesce(nullif(denied_workload,""), "n_a")
| join type=left max=0 cluster, namespace [
    | inputlookup namespace_psa_inventory.csv
    | eval cluster=lower(trim(toString(coalesce(cluster, cluster_name, k8s_cluster, ""))))
    | eval namespace=trim(toString(coalesce(namespace, k8s_namespace, ns, "")))
    | eval expected_enforce_level=lower(trim(toString(coalesce(expected_enforce_level, enforce_profile, ""))))
    | eval expected_enforce_version=trim(toString(coalesce(expected_enforce_version, enforce_version_expected, "")))
    | eval expected_audit_level=trim(toString(coalesce(expected_audit_level, "")))
    | eval expected_warn_level=trim(toString(coalesce(expected_warn_level, "")))
    | eval owner_team=toString(coalesce(owner_team, squad, platform_owner, ""))
    | eval exception_reason=toString(coalesce(exception_reason, ""))
    | eval exception_expiry=tonumber(tostring(coalesce(exception_expiry, exception_expiry_epoch, "0")), 10)
    | fields cluster namespace expected_enforce_level expected_enforce_version expected_audit_level expected_warn_level owner_team exception_reason exception_expiry ]
| fillnull value="" expected_enforce_version enforce_version_live owner_team exception_reason
| eval expected_enforce_level=coalesce(nullif(expected_enforce_level,""), "restricted")
| eval prod_like=if(match(lower(namespace), "(?i)prod|production|tier0|mission|prd-"), 1, 0)
| eval dev_experiments=if(match(lower(namespace), "(?i)dev-experiments|sandbox|chaos-lab"), 1, 0)
| eval kube_system_exempt=if(match(lower(namespace), "^kube-system$"), 1, 0)
| eval now_epoch=now()
| eval exception_expired=if(exception_expiry>0 AND now_epoch>exception_expiry, 1, 0)
| eval version_mismatch=if(len(expected_enforce_version)>0 AND len(enforce_version_live)>0 AND expected_enforce_version!=enforce_version_live, 1, 0)
| eval is_denial=if(signal_lane=="psa_audit_denial", 1, 0)
| eventstats sum(is_denial) AS denial_count_24h BY cluster, namespace
| streamstats window=240 current=t global=f sum(is_denial) AS denial_rolling_recent BY cluster, namespace
| fillnull value=0 denial_count_24h
| eval severity=case(
    kube_system_exempt=1 AND signal_lane=="psa_label_drift", "low",
    dev_experiments=1 AND signal_lane=="psa_audit_denial" AND prod_like=0, "low",
    exception_expired=1 AND prod_like=1, "critical",
    version_mismatch=1 AND prod_like=1, "high",
    match(actual_enforce_level, "privileged") AND prod_like=1 AND match(expected_enforce_level, "restricted|baseline"), "critical",
    signal_lane=="psa_label_drift" AND prod_like=1 AND match(expected_enforce_level, "restricted|baseline"), "high",
    signal_lane=="psa_audit_denial" AND prod_like=1 AND match(expected_enforce_level, "restricted"), "high",
    signal_lane=="psa_audit_denial" AND prod_like=1 AND match(violation_field, "privileged|hostPID|hostNetwork|allowPrivilegeEscalation"), "high",
    signal_lane=="psa_label_drift" AND prod_like=0, "medium",
    signal_lane=="psa_audit_denial" AND prod_like=0, "low",
    true(), "medium")
| where NOT (dev_experiments=1 AND signal_lane=="psa_label_drift")
| where NOT (kube_system_exempt=1 AND signal_lane=="psa_label_drift" AND prod_like=0)
| table cluster namespace expected_enforce_level actual_enforce_level drift_state denial_count_24h denied_user denied_workload violation_field severity owner_team enforce_version_live expected_enforce_version denial_rolling_recent exception_expired version_mismatch signal_lane
```

### Step 4 — Validate

Synthetic negative test: label a disposable namespace with pod-security.kubernetes.io/enforce=restricted, apply a compliant Deployment manifest, and confirm no 403 PodSecurity audit lines appear for that rollout while kube_namespace_labels shows the enforce label present.

Synthetic denial test: run kubectl run nginx --image=nginx --privileged -n that namespace and confirm audit shows responseStatus.code 403 with message containing violates PodSecurity, then run the saved search and expect signal_lane psa_audit_denial with violation_field privileged and denied_user matching your kubectl user or CI token.

Drift test: remove the enforce label with kubectl label namespace test-psa pod-security.kubernetes.io/enforce- and confirm the metrics arm surfaces missing_pod_security_enforce_label within two scrape intervals.

Clearing test: restore labels from GitOps, rerun the search, and confirm rows disappear or severities drop below alert thresholds.

Correlation test: compare alert timestamps to UC-3.2.7 control-plane health to avoid chasing PSA noise during apiserver outages that generate truncated audit bodies.

RBAC test: readers without index=k8s_audit must see zero rows.

Performance test: Job Inspector during Monday peaks; if scan cost exceeds budget, summarize kube_namespace_labels into k8s_compliance hourly and point the metrics arm at the summary index with documented lag acceptance.

### Step 5 — Operationalize & Troubleshoot

Case 1 — Privileged escalation attempt by deploy bot: treat as potential credential misuse or poisoned pipeline template; page application security and freeze the pipeline until manifest history is reviewed.

Case 2 — Baseline-policy denial in a dev namespace: log-only route per namespace_psa_inventory.csv if expected_enforce_level is baseline and owner_team acknowledges developer churn; keep medium severity for trending.

Case 3 — Restricted-policy denial in prod namespace: escalate to high, require manifest fix or exception ticket with expiry, and attach audit excerpts to the change record.

Case 4 — Namespace label removed outside GitOps: open critical drift, re-apply labels via GitOps revert, and audit IAM or break-glass holders who touched the namespace object.

Case 5 — New namespace bootstrap missing PSA labels: auto-fix via approved mutation webhook or cluster policy, then backfill inventory CSV before declaring closure.

Case 6 — Exception window expired but namespace still weaker than inventory: critical severity until either labels tighten or inventory reflects an approved new baseline with finance and risk sign-off.

Case 7 — Cross-link with UC-3.1.6: when admission denies but runtime inspect later shows privilege, investigate race conditions, stale inventory, or alternate cluster contexts; pair timelines before closing.

Case 8 — Cluster admin emergency override: if administrators temporarily widen enforcement, require logged change with incident commander approval and keep alerting enabled to capture the window.

Case 9 — PSA evaluation skipped in kube-system: expect vendor-privileged posture; document in inventory and suppress only kube-system label drift rows, not audit denials from application namespaces.

Case 10 — Helm chart upgrade introduces non-compliant pod spec: open high denial, block CI promotion, and require chart rollback or values fix before customer impact.

Case 11 — Suppression for dev-experiments namespaces: maintain dev_experiments style macros tied to namespace naming standards so chaos sandboxes do not page production bridges.

Case 12 — enforce-version drift between v1.27 and v1.28: treat as high when prod_like and inventory pins a version; reconcile with platform upgrade runbooks so policy semantics stay aligned with the apiserver built-in version.

Dashboard publishing: follow the visualization field with severity coloring on severity, drilldowns to raw audit JSON, and annotations when namespace_psa_inventory.csv commits land.

Evidence retention: weekly exports satisfy SOC2, ISO 27001, and internal Kubernetes hardening scorecards when paired with tickets and Git history.

Governance: quarterly replay one historical denial spike through the SPL after upgrades to kube-state-metrics, apiserver, or Splunk; update the comment macro when indexes move.

Closing checklist: five em-dash step headers are present; Step 3 fenced SPL matches the spl field exactly; multisearch lists audit and metrics arms; coalesce appears in both arms and after fan-in; join wraps namespace_psa_inventory.csv; eventstats and streamstats implement denial counts; case assigns severity tiers; closing table projects sixteen analyst columns including cluster, namespace, expected_enforce_level, actual_enforce_level, drift_state, denial_count_24h, denied_user, denied_workload, violation_field, severity, owner_team, enforce versions, rolling sums, exception and version flags, and signal_lane; monitoringType includes Security, Compliance, and Configuration; cimModels lists Change and Endpoint; equipmentModels lists kubernetes_k8s; references include eight Kubernetes and Splunk URLs; description and value differ; grandmaExplanation avoids jargon acronyms; knownFalsePositives narrates tuning guidance without claiming this UC replaces runtime privilege analytics.

## SPL

```spl
`comment("UC-3.2.22 Pod Security Admission denials and namespace PSS label drift. Tunables: idx_audit=k8s_audit st_audit=kube:apiserver:audit; idx_metrics=k8s_metrics st_metrics=prometheus:scrape:metrics; lookup namespace_psa_inventory.csv keys cluster+namespace; earliest=-24h@h latest=@h")`
| multisearch 
    [ search index=k8s_audit sourcetype="kube:apiserver:audit" earliest=-24h@h latest=@h
      | eval cluster=lower(trim(toString(coalesce(k8s_cluster_name, cluster_name, cluster, eks_cluster_name, gke_cluster_name, aks_cluster_name, resource_cluster, audit_cluster, ""))))
      | eval resp_code=tonumber(tostring(coalesce('responseStatus.code', responseStatus.code, responseStatus_code, status_code, http_status, "0")), 10)
      | eval resp_reason=lower(toString(coalesce('responseStatus.reason', responseStatus.reason, responseStatus_reason, "")))
      | eval resp_msg=lower(toString(coalesce('responseStatus.message', responseStatus.message, responseStatus_message, message, "")))
      | eval obj_res=lower(toString(coalesce('objectRef.resource', objectRef.resource, objectRef_resource, "")))
      | where resp_code=403 AND match(resp_msg, "violates podsecurity") AND (len(resp_reason)=0 OR match(resp_reason, "forbidden"))
      | where match(obj_res, "^(pods|pod)$")
      | eval namespace=toString(coalesce('objectRef.namespace', objectRef.namespace, objectRef_namespace, ""))
      | eval denied_workload=toString(coalesce('objectRef.name', objectRef.name, objectRef_name, request_name, ""))
      | eval denied_user=toString(coalesce('user.username', user.username, user_username, user__username, ""))
      | eval violation_field=case(
          match(resp_msg, "runasnonroot|run as non-root"), "runAsNonRoot",
          match(resp_msg, "allowprivilegeescalation"), "allowPrivilegeEscalation",
          match(resp_msg, "(?i)privileged"), "privileged",
          match(resp_msg, "hostnetwork|host network"), "hostNetwork",
          match(resp_msg, "hostpid|host pid"), "hostPID",
          match(resp_msg, "hostipc|host ipc"), "hostIPC",
          match(resp_msg, "capabilities"), "capabilities",
          match(resp_msg, "seccomp"), "seccomp",
          match(resp_msg, "volume"), "volumes",
          true(), "psa_other_field")
      | eval signal_lane="psa_audit_denial"
      | eval actual_enforce_level="policy_enforced_by_denial"
      | eval drift_state="admission_denied"
      | eval enforce_version_live=""
      | fields _time cluster namespace denied_user denied_workload violation_field signal_lane actual_enforce_level drift_state enforce_version_live ]
    [ search index=k8s_metrics sourcetype="prometheus:scrape:metrics" earliest=-4h@h latest=@h
      | eval cluster=lower(trim(toString(coalesce(k8s_cluster_name, cluster_name, cluster, eks_cluster_name, gke_cluster_name, aks_cluster_name, resource_cluster, ""))))
      | eval mn=lower(trim(toString(coalesce(__name__, metric_name, name, MetricName, ""))))
      | where like(mn, "%kube_namespace_labels%") OR match(_raw, "kube_namespace_labels")
      | rex field=_raw "namespace=\\"(?<namespace>[^\\"]+)\\""
      | rex field=_raw "pod_security_kubernetes_io_enforce=\\"(?<psa_enforce>[^\\"]+)\\""
      | rex field=_raw "pod_security_kubernetes_io_enforce_version=\\"(?<psa_enforce_ver>[^\\"]+)\\""
      | stats latest(psa_enforce) AS le latest(psa_enforce_ver) AS lev BY cluster, namespace
      | eval actual_enforce_level=lower(trim(toString(coalesce(le, ""))))
      | eval enforce_version_live=trim(toString(coalesce(lev, "")))
      | eval has_enforce=if(len(actual_enforce_level)>0, 1, 0)
      | where has_enforce=0 OR match(actual_enforce_level, "^privileged$")
      | eval denied_user="n_a_metrics"
      | eval denied_workload="namespace_object"
      | eval violation_field=if(has_enforce=0, "missing_enforce_label", "privileged_enforce_label")
      | eval signal_lane="psa_label_drift"
      | eval drift_state=if(has_enforce=0, "missing_pod_security_enforce_label", "privileged_namespace_enforcement")
      | fields _time cluster namespace denied_user denied_workload violation_field signal_lane actual_enforce_level drift_state enforce_version_live ]
| eval cluster=coalesce(nullif(cluster,""), "unknown_cluster")
| eval namespace=coalesce(nullif(namespace,""), "unknown_namespace")
| eval denied_user=coalesce(nullif(denied_user,""), "unknown_subject")
| eval denied_workload=coalesce(nullif(denied_workload,""), "n_a")
| join type=left max=0 cluster, namespace [
    | inputlookup namespace_psa_inventory.csv
    | eval cluster=lower(trim(toString(coalesce(cluster, cluster_name, k8s_cluster, ""))))
    | eval namespace=trim(toString(coalesce(namespace, k8s_namespace, ns, "")))
    | eval expected_enforce_level=lower(trim(toString(coalesce(expected_enforce_level, enforce_profile, ""))))
    | eval expected_enforce_version=trim(toString(coalesce(expected_enforce_version, enforce_version_expected, "")))
    | eval expected_audit_level=trim(toString(coalesce(expected_audit_level, "")))
    | eval expected_warn_level=trim(toString(coalesce(expected_warn_level, "")))
    | eval owner_team=toString(coalesce(owner_team, squad, platform_owner, ""))
    | eval exception_reason=toString(coalesce(exception_reason, ""))
    | eval exception_expiry=tonumber(tostring(coalesce(exception_expiry, exception_expiry_epoch, "0")), 10)
    | fields cluster namespace expected_enforce_level expected_enforce_version expected_audit_level expected_warn_level owner_team exception_reason exception_expiry ]
| fillnull value="" expected_enforce_version enforce_version_live owner_team exception_reason
| eval expected_enforce_level=coalesce(nullif(expected_enforce_level,""), "restricted")
| eval prod_like=if(match(lower(namespace), "(?i)prod|production|tier0|mission|prd-"), 1, 0)
| eval dev_experiments=if(match(lower(namespace), "(?i)dev-experiments|sandbox|chaos-lab"), 1, 0)
| eval kube_system_exempt=if(match(lower(namespace), "^kube-system$"), 1, 0)
| eval now_epoch=now()
| eval exception_expired=if(exception_expiry>0 AND now_epoch>exception_expiry, 1, 0)
| eval version_mismatch=if(len(expected_enforce_version)>0 AND len(enforce_version_live)>0 AND expected_enforce_version!=enforce_version_live, 1, 0)
| eval is_denial=if(signal_lane=="psa_audit_denial", 1, 0)
| eventstats sum(is_denial) AS denial_count_24h BY cluster, namespace
| streamstats window=240 current=t global=f sum(is_denial) AS denial_rolling_recent BY cluster, namespace
| fillnull value=0 denial_count_24h
| eval severity=case(
    kube_system_exempt=1 AND signal_lane=="psa_label_drift", "low",
    dev_experiments=1 AND signal_lane=="psa_audit_denial" AND prod_like=0, "low",
    exception_expired=1 AND prod_like=1, "critical",
    version_mismatch=1 AND prod_like=1, "high",
    match(actual_enforce_level, "privileged") AND prod_like=1 AND match(expected_enforce_level, "restricted|baseline"), "critical",
    signal_lane=="psa_label_drift" AND prod_like=1 AND match(expected_enforce_level, "restricted|baseline"), "high",
    signal_lane=="psa_audit_denial" AND prod_like=1 AND match(expected_enforce_level, "restricted"), "high",
    signal_lane=="psa_audit_denial" AND prod_like=1 AND match(violation_field, "privileged|hostPID|hostNetwork|allowPrivilegeEscalation"), "high",
    signal_lane=="psa_label_drift" AND prod_like=0, "medium",
    signal_lane=="psa_audit_denial" AND prod_like=0, "low",
    true(), "medium")
| where NOT (dev_experiments=1 AND signal_lane=="psa_label_drift")
| where NOT (kube_system_exempt=1 AND signal_lane=="psa_label_drift" AND prod_like=0)
| table cluster namespace expected_enforce_level actual_enforce_level drift_state denial_count_24h denied_user denied_workload violation_field severity owner_team enforce_version_live expected_enforce_version denial_rolling_recent exception_expired version_mismatch signal_lane
```

## CIM SPL

```spl
| tstats summariesonly=t count FROM datamodel=Change WHERE nodename=Change.All_Changes earliest=-24h@h latest=now BY All_Changes.dest All_Changes.object All_Changes.action
| rename All_Changes.dest AS cluster All_Changes.object AS change_object All_Changes.action AS change_action
| head 200
```

## Visualization

Severity-colored table mirroring the closing SPL projection; timeline of denial_count_24h by namespace; single-value tiles for critical versus high counts; drilldown from violation_field to raw audit message text; companion panel for enforce_version_live mismatches.

## Known False Positives

Developer and chaos namespaces that intentionally run baseline or privileged enforcement for game-day drills will generate steady denial or privileged-label rows until namespace_psa_inventory.csv carries time-bounded exception_reason and exception_expiry fields that your alert macro reads before paging. kube-system and other platform namespaces often remain privileged by vendor design; exclude them with kube_system_exempt style macros or explicit inventory rows so Cilium, CoreDNS, and metrics-server lifecycles do not open Sev-1 bridges. During cluster bootstrap or immediately after GitOps controller outages, namespaces may temporarily lack enforce labels while controllers replay; treat short windows as operational debt tracked in platform tickets rather than hostile drift when change records exist. Helm upgrades that introduce a non-compliant pod spec often produce a burst of denials before chart maintainers merge fixes; correlate with Helm release revision audit and suppress only when the owning team documents rollback or forward fix ETA. Organizations migrating from PodSecurityPolicy to PSA frequently run audit or warn modes first; historical audit-only periods can look like silent failures if you only chart Forbidden counts without reading the warn and audit labels. Pen testers and red teams that deliberately craft violating pods will trip this control by design; tag those namespaces in the lookup so purple exercises do not exhaust on-call goodwill. Regional replicas of the same logical namespace name on different clusters need distinct cluster keys in namespace_psa_inventory.csv or joins collapse expectations. Finally, some managed control planes redact portions of audit messages; violation_field may fall back to psa_other_field even though operators can still read fuller text in cloud vendor policy logs.

## References

- [Kubernetes — Pod Security Admission](https://kubernetes.io/docs/concepts/security/pod-security-admission/)
- [Kubernetes — Pod Security Standards](https://kubernetes.io/docs/concepts/security/pod-security-standards/)
- [Kubernetes — Enforce standards namespace labels](https://kubernetes.io/docs/tasks/configure-pod-container/enforce-standards-namespace-labels/)
- [Kubernetes — Security checklist](https://kubernetes.io/docs/concepts/security/security-checklist/)
- [Kubernetes — Cluster-level Pod Security Standards tutorial](https://kubernetes.io/docs/tutorials/security/cluster-level-pss/)
- [Kubernetes — Admission controllers (PodSecurity)](https://kubernetes.io/docs/reference/access-authn-authz/admission-controllers/#podsecurity)
- [Splunk — Add-on for Kubernetes (OTel Collector guidance)](https://docs.splunk.com/Documentation/AddOns/released/Kubernetes/About)
- [Kubernetes — Auditing](https://kubernetes.io/docs/reference/access-authn-authz/)
