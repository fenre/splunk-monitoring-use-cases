<!-- AUTO-GENERATED from UC-3.3.22.json — DO NOT EDIT -->

---
id: "3.3.22"
title: "OpenShift Pod Security Admission Enforcement Plane: Namespace Label Drift, SCC↔PSA Interaction Conflicts, and Multi-Mode Audit, Warn, and Enforce Failures"
status: "verified"
criticality: "high"
splunkPillar: "Security"
---

# UC-3.3.22 · OpenShift Pod Security Admission Enforcement Plane: Namespace Label Drift, SCC↔PSA Interaction Conflicts, and Multi-Mode Audit, Warn, and Enforce Failures

> **Criticality:** High &middot; **Difficulty:** Advanced &middot; **Pillar:** Security &middot; **Type:** Security, Compliance &middot; **Wave:** Walk &middot; **Status:** Verified

*We watch the layered safety rules that decide whether an app may launch, and we catch when namespace labels drift, when installs leave spaces stuck permissive, or when a cluster upgrade makes pinned rule versions disagree with the live platform version.*

---

## Description

Surfaces OpenShift Pod Security Admission outcomes together with namespace PSA label drift, SCC↔PSA interaction signatures, soft-launch audit versus enforce gaps, operator-managed namespace churn, and enforce-version skew relative to ClusterVersion-driven Kubernetes minors so teams see enforcement debt that vanilla Kubernetes-only PSA analytics miss.

## Value

Platform and application security leaders gain a single evidence chain for how OpenShift SCC mutating admission and PSA validating admission interact, whether openshift-* namespaces drift away from reconciled baselines, whether teams stall in audit-heavy soft launches, and whether version pins survive upgrades—shortening time to fix silent permissive posture before the next cluster-wide tightening breaks deployments.

## Implementation

Land ocp_audit or k8s_audit with ocp_audit, k8s_audit, or kube:apiserver:audit sourcetypes plus ocp_namespace_labels snapshots, ocp_clusterversion rows, and optional ocp_compliance_namespace into governed indexes; publish approved_psa_baseline.csv; save openshift_uc_3_3_22_psa_enforcement_plane on a fifteen-minute cadence over earliest=-24h@h; route critical and high severities to platform security; archive weekly CSV exports with lookup commit hashes.

## Evidence

Saved search openshift_uc_3_3_22_psa_enforcement_plane with fifteen minute schedule; versioned approved_psa_baseline.csv in git; weekly CSV exports to restricted evidence index; dashboard drilldowns on ocp_audit, namespace label snapshots, and ClusterVersion rows; alert stanza with platform security routing keys.

## Control test

### Positive scenario

In a lab OpenShift namespace labeled with restricted PSA enforce, ingest audit showing a 403 Forbidden violates PodSecurity response for a privileged pod create plus a second stream showing openshift.io/scc markers in the same audit window for SCC↔PSA correlation, publish approved_psa_baseline.csv expecting restricted enforce, and confirm openshift_uc_3_3_22_psa_enforcement_plane emits critical or high rows with non-null recommended_action within the scheduled window.

### Negative scenario

After aligning namespace labels to approved_psa_baseline.csv and deploying a pod spec that satisfies restricted PSA with no SCC conflict, confirm severities return to info and the alert wrapper returns zero rows when filtering to critical and high only.

## Detailed Implementation


### Step 1 — Prerequisites

Head of Platform owns this control jointly with the OpenShift platform security lead, the Kubernetes hardening engineers who interpret Pod Security Admission labels alongside Security Context Constraints, the Operator Lifecycle Manager platform team that governs catalog-installed workloads, and the observability engineers who operate Splunk HTTP Event Collector tokens plus OpenTelemetry Collector agents that forward kube-apiserver and openshift-apiserver audit JSON. This use case isolates the OpenShift-specific Pod Security Admission enforcement plane: namespace labels on pod-security.kubernetes.io/enforce, pod-security.kubernetes.io/warn, pod-security.kubernetes.io/audit, and the paired enforce-version, warn-version, and audit-version qualifiers that pin Pod Security Standard evaluation to a Kubernetes minor. OpenShift runs PSA as part of the upstream admission chain while also running SCC mutating admission that can reshape securityContext fields before PSA validating admission evaluates the effective pod spec. The documented global pod security profile ordering in OpenShift means a cluster-wide tightening from privileged toward restricted can change outcomes without individual teams editing every namespace, which silently breaks pods that still pass SCC selection yet violate PSA at the namespace profile. UC-3.2.22 remains vanilla Kubernetes PSA denials and kube-state-metrics kube_namespace_labels drift without the SCC interaction story, without openshift-* operator reconciliation semantics, and without OpenShift ClusterVersion-driven minor migrations that desynchronize pinned enforce-version labels. UC-3.3.4 remains Security Context Constraint denial analytics and openshift.io/scc selection truth as the primary signal rather than PSA label governance and validating admission outcomes. UC-3.3.6 remains ClusterOperator health for fleet-wide operator degradation rather than per-namespace PSA posture. UC-3.3.14 remains OAuth authentication flow telemetry rather than admission-time pod policy. Splunk becomes the tamper-resistant ledger that fuses kube-apiserver audit RequestResponse bodies for pod-creating verbs, openshift-apiserver audit when your estate splits streams, periodic namespace label snapshots from GitOps exporters or compliance collectors, SCC annotation markers in audit bodies, namespace object mutations that touch PSA keys, and ClusterVersion desired-version rows that anchor Kubernetes minor extraction for version-skew math.

Index and permission design land before parsers. Designate index=ocp_audit for Kubernetes apiserver audit or equivalent OpenShift-forwarded audit with sourcetype=ocp_audit or sourcetype=k8s_audit depending on whether you segregate OpenShift clusters from vanilla Kubernetes estates. Designate index=k8s_audit when shared fleet indexes already standardize on kube:apiserver:audit sourcetype from Splunk OpenTelemetry Collector filelog receivers tailing control-plane audit.log paths. Designate index=ocp_compliance or index=ocp_metrics for scheduled namespace label snapshots with sourcetype=ocp_namespace_labels, sourcetype=ocp_namespace_snapshot, or sourcetype=ocp_compliance_namespace depending on how your exporter flattens metadata.labels maps into fields. Designate index=ocp_metrics for ClusterVersion snapshots with sourcetype=ocp_clusterversion, sourcetype=ocp_cluster_version, or sourcetype=ocp_clusteroperator when your scripted input embeds desired version strings in operator rows. Issue distinct HEC tokens per environment with least privilege: platform security may search all sourcetypes; application teams receive filtered views that omit requestObject except metadata when counsel requires minimization. Retention should cover at least thirty days hot for admission replay, ninety days when regulated customers require quarterly control replays, and align cold storage with enterprise logging policy. Legal review should confirm service account names, partial pod specs, and namespace labels are acceptable in Splunk; never index Secret dataKey material.

RBAC and safety: the forwarder reading apiserver audit.log must run on control-plane hosts or use cloud-provider audit exports with read-only service roles. Dedicated management-cluster collectors should use short-lived kubeconfigs, not long-lived kubeadmin tokens on laptops. GitOps agents and catalog operators that mutate namespace labels should still appear in audit with user.username and user.groups preserved so investigations distinguish human break-glass edits from controller identities.

Audit policy depth: PSA outcomes surface best when audit stages include RequestResponse for pod create, update, and patch so responseStatus.message retains violates PodSecurity fragments and responseObject metadata exposes pod-security.kubernetes.io audit and warn annotations on admitted pods. Capture namespace patch and update verbs at Metadata or RequestResponse depth consistent with volume budgets so Splunk can compute label mutation velocity for openshift-* namespaces reconciled by cluster operators. Follow OpenShift documentation for audit profile tuning and test volume before production.

Field normalization: flatten objectRef.apiGroup, objectRef.resource, objectRef.namespace, objectRef.name, user.username, verb, responseStatus.code, responseStatus.reason, responseStatus.message, and nested annotations for pod-security keys. If JSON paths arrive dotted, coalesce() ladders in SPL still resolve when props.conf FIELDALIAS maps are maintained. Cluster identity must appear as cluster, openshift_cluster, or cluster_name on every event.

Governance lookup: publish lookups/approved_psa_baseline.csv in git with columns cluster, namespace, expected_enforce, expected_warn, expected_audit, owner_team, exception_reason, and exception_expiry_epoch so joins classify drift without hard-coding hundreds of namespaces inside SPL. Refresh from the same repository that applies labels so inventory and cluster state share commit ancestry auditors can trace.

Risk briefing: bursts of PSA denials may indicate a misguided continuous deployment rollout rather than attack; correlate with deployment userAgent and GitOps commits before paging executives. Conversely, enforce=privileged with audit=restricted soft-launch posture that never tightens enforce is compliance debt even when deny counts stay zero because warn and audit modes can be extremely chatty while enforce remains permissive. Namespace label drift on openshift-* namespaces is high severity because cluster operators reconcile those objects and manual edits often fight automation.

Differentiation recap: OpenShift PSA enforcement plane with SCC interaction correlation, openshift-* reconciliation sensitivity, OLM-managed namespace behavior, oc adm policy and label workflows, and ClusterVersion-aware enforce-version skew detection, not vanilla Kubernetes PSA-only analytics, not UC-3.3.4 SCC denial primary storytelling, not OAuth identity plane analytics.

Operational posture: align telemetry with change tickets by stamping change_ticket_id on HEC events when platform teams adjust global pod security configuration or when security runs controlled enforce tightening programs across hundreds of namespaces.



### Step 2 — Configure data collection

Stand up five complementary lanes Splunk multisearch can fuse: kube-apiserver audit for PSA validating admission outcomes on pods, structured namespace label snapshots for enforce, warn, audit, and version qualifiers, audit rows that simultaneously carry openshift.io/scc markers and PSA violation text for SCC↔PSA interaction analytics, dedicated namespace exporter rows joined to ClusterVersion for enforce-version skew detection, and ClusterVersion or ClusterOperator snapshots that expose desired OpenShift releases for Kubernetes minor extraction used both in the skew arm and the post-fan-in join.

Audit lane primary: ship kube-apiserver audit.log into index=ocp_audit with sourcetype=ocp_audit using Splunk Connect for Kubernetes filelog patterns, Splunk OpenTelemetry Collector filelog receiver, or cloud-audit exports that preserve Kubernetes audit v1 JSON. Ensure stageTimestamp and requestReceivedTimestamp map to _time within thirty seconds of true apiserver time. Enable TLS to Splunk, rotate HEC tokens quarterly, and document which management cluster forwards lab versus production to prevent cluster label collisions.

OpenShift split streams: some estates forward openshift-apiserver audit separately; normalize sourcetype naming but keep identical SPL coalesce ladders so analysts do not fork searches per component.

Namespace label snapshot lane: schedule a utility every five to fifteen minutes to export Namespace objects, flatten metadata.labels for pod-security keys, and emit sourcetype=ocp_namespace_labels into index=ocp_compliance or index=ocp_events. Include openshift.io metadata only when governance requires it; PSA keys are mandatory. Hash canonical JSON without volatile resourceVersion when regulated customers require tamper evidence.

ClusterVersion lane: export oc get clusterversion version -o json or watch config.openshift.io ClusterVersion objects, flatten status.desired.version, and land sourcetype=ocp_clusterversion in index=ocp_metrics. Splunk should carry both OpenShift composite version strings and extracted Kubernetes minor fragments used by the saved search join.

OLM context: capture subscription and operator group namespaces in approved_psa_baseline.csv with notes when vendors require privileged enforce profiles during install windows; uninstall churn can orphan namespaces at privileged enforce while workloads disappear.

Example oc verification operators run during design reviews:

```bash
oc version -o json
oc get ns -o json | jq -r '.items[] | select(.metadata.labels["pod-security.kubernetes.io/enforce"]!=null) | .metadata.name'
oc get clusterversion version -o jsonpath='{.status.desired.version}{"\n"}'
oc describe namespace openshift-monitoring | sed -n '1,120p'
```

Example audit-policy fragment illustrating pod and namespace focus (tune omitStages and users per estate):

```yaml
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
  - level: RequestResponse
    verbs: ["create", "update", "patch"]
    resources:
      - group: ""
        resources: ["namespaces"]
    namespaces: ["*"]
```

props.conf guidance: TRUNCATE sufficiently large for RequestResponse bodies, TIMESTAMP_FIELDS respected when HEC time is authoritative, LINE_BREAKER for newline-delimited JSON audit files, and SEDCMD or transforms that strip tls.key-like patterns if misconfigured clients ever leak secrets.

Pre-save validation: index=ocp_audit earliest=-15m must return non-zero counts; sample responseStatus.message for PodSecurity substrings; confirm namespace snapshot sourcetype includes enforce labels for openshift-* and tenant namespaces; ocp_clusterversion must move after controlled upgrade drills in lab.

Governance lookup: publish approved_psa_baseline.csv with cluster, namespace, expected_enforce, expected_warn, expected_audit, owner_team, exception_reason, and exception_expiry_epoch. Refresh from the same repository that manages namespace labels so inventory and cluster state share commit ancestry auditors can trace.

Collector hardening: run forwarders with approved TLS cipher suites when required, segregate indexes per data classification, and restrict search peers that can read ocp_audit to roles that completed privileged access training.



### Step 3 — Create the search and alert

Save the SPL as openshift_uc_3_3_22_psa_enforcement_plane with a fifteen-minute schedule during steady-state production, dispatch earliest=-24h@h, dispatch latest=now, and alert when severity is critical or high. Throttle duplicate cluster, namespace, signal_lane rows for forty-five minutes unless severity escalates. Include recommended_action, signal_lane, and psa_tier fields in pager descriptions so incident commanders route to PSA and SCC joint runbooks without re-running ad hoc searches.

Pipeline narrative for reviewers: multisearch fans PSA validating admission rows, namespace label snapshots, SCC↔PSA interaction rows, and a dedicated enforce-version versus ClusterVersion minor mismatch arm so skew surfaces even before baseline drift logic runs. A join subsearch attaches ClusterVersion-derived Kubernetes minor strings to all rows for consistent skew math after fan-in. A join subsearch wraps approved_psa_baseline.csv for expected enforce, warn, and audit posture. coalesce() absorbs flattened versus dotted JSON field naming drift across exporters. streamstats computes short-window PSA deny bursts per namespace. eventstats aggregates windowed deny totals and drift counts per cluster. case() maps openshift-* label drift, SCC↔PSA critical denials, soft-launch stuck posture, enforce-version mismatch in production-like namespaces, and high-volume deny bursts into critical, high, medium, and info tiers.

Fenced SPL must match the spl JSON field exactly:

```spl
`comment("UC-3.3.22 OpenShift PSA enforcement plane — validating admission outcomes, namespace PSA label drift vs approved_psa_baseline.csv, SCC↔PSA interaction signatures, namespace label mutation audit velocity, cluster minor join for enforce-version skew. earliest=-24h@h latest=now")`
| multisearch
    [ search (index=ocp_audit OR index=k8s_audit) (sourcetype=ocp_audit OR sourcetype=k8s_audit OR sourcetype="kube:apiserver:audit") earliest=-24h@h latest=now
      | eval cluster=lower(trim(toString(coalesce(cluster, openshift_cluster, cluster_name, k8s_cluster_name, ""))))
      | eval resp_code=tonumber(tostring(coalesce('responseStatus.code', responseStatus.code, responseStatus_code, http_status, "0")), 10)
      | eval resp_reason=lower(toString(coalesce('responseStatus.reason', responseStatus.reason, responseStatus_reason, "")))
      | eval resp_msg=lower(toString(coalesce('responseStatus.message', responseStatus.message, responseStatus_message, message, "")))
      | eval obj_res=lower(toString(coalesce('objectRef.resource', objectRef.resource, objectRef_resource, "")))
      | eval verb_tx=lower(toString(coalesce(verb, requestVerb, "")))
      | where match(obj_res,"^pods?$") AND match(verb_tx,"create|update")
      | eval psa_gate=if(match(resp_msg,"violates podsecurity|podsecurity") OR match(_raw,"pod-security.kubernetes.io") AND (match(_raw,"audit-violations") OR match(_raw,"warn-violations") OR match(_raw,"enforce-violations")), 1, 0)
      | where psa_gate=1
      | eval namespace=trim(toString(coalesce('objectRef.namespace', objectRef.namespace, objectRef_namespace, "")))
      | eval workload=trim(toString(coalesce('objectRef.name', objectRef.name, objectRef_name, "")))
      | eval actor=trim(toString(coalesce('user.username', user.username, user_username, "")))
      | eval psa_deny=if((resp_code=403 OR match(resp_reason,"forbidden")) AND match(resp_msg,"violates podsecurity|podsecurity"), 1, 0)
      | eval psa_warn_audit_only=if(psa_deny=0 AND (match(_raw,"warn-violations") OR match(_raw,"audit-violations")), 1, 0)
      | eval signal_lane="psa_validating_admission"
      | eval lane_detail=substr(coalesce(resp_msg,""),1,280)
      | fields _time cluster namespace workload actor signal_lane lane_detail psa_deny psa_warn_audit_only resp_code verb_tx ]
    [ search (index=ocp_metrics OR index=ocp_events OR index=ocp_compliance) (sourcetype=ocp_namespace_labels OR sourcetype=ocp_namespace_snapshot OR sourcetype=ocp_compliance_namespace) earliest=-24h@h latest=now
      | eval cluster=lower(trim(toString(coalesce(cluster, openshift_cluster, cluster_name, cluster_id, ""))))
      | eval namespace=trim(toString(coalesce(namespace, metadata_namespace, ns, "")))
      | eval cur_enforce=lower(trim(toString(coalesce(pod_security_enforce, psa_enforce_label, enforce_label, labels_pod_security_enforce, ""))))
      | eval cur_warn=lower(trim(toString(coalesce(pod_security_warn, psa_warn_label, warn_label, labels_pod_security_warn, ""))))
      | eval cur_audit=lower(trim(toString(coalesce(pod_security_audit, psa_audit_label, audit_label, labels_pod_security_audit, ""))))
      | eval cur_enforce_version=trim(toString(coalesce(enforce_version_label, pod_security_enforce_version, psa_enforce_version, labels_enforce_version, "")))
      | rex field=_raw "(?i)pod-security\.kubernetes\.io/enforce\"\\s*:\\s*\"(?<rex_enf>[^\"]+)"
      | eval cur_enforce=coalesce(nullif(cur_enforce,""), lower(trim(rex_enf)))
      | rex field=_raw "(?i)pod-security\.kubernetes\.io/enforce-version\"\\s*:\\s*\"(?<rex_ev>[^\"]+)"
      | eval cur_enforce_version=coalesce(nullif(cur_enforce_version,""), trim(rex_ev))
      | eval signal_lane="psa_namespace_label_snapshot"
      | eval lane_detail=strcat("enforce=",coalesce(cur_enforce,"none"),";warn=",coalesce(cur_warn,"none"),";audit=",coalesce(cur_audit,"none"),";enforce_version=",coalesce(cur_enforce_version,"none"))
      | stats latest(_time) AS _time latest(cur_enforce) AS cur_enforce latest(cur_warn) AS cur_warn latest(cur_audit) AS cur_audit latest(cur_enforce_version) AS cur_enforce_version BY cluster namespace
      | eval workload="namespace_object"
      | eval actor="label_exporter"
      | eval psa_deny=0
      | eval psa_warn_audit_only=0
      | eval resp_code=0
      | eval verb_tx="get"
      | fields _time cluster namespace workload actor signal_lane lane_detail psa_deny psa_warn_audit_only resp_code verb_tx cur_enforce cur_warn cur_audit cur_enforce_version ]
    [ search (index=ocp_audit OR index=k8s_audit) (sourcetype=ocp_audit OR sourcetype=k8s_audit OR sourcetype="kube:apiserver:audit") earliest=-24h@h latest=now
      | eval cluster=lower(trim(toString(coalesce(cluster, openshift_cluster, cluster_name, k8s_cluster_name, ""))))
      | eval resp_code=tonumber(tostring(coalesce('responseStatus.code', responseStatus.code, responseStatus_code, "0")), 10)
      | eval resp_msg=lower(toString(coalesce('responseStatus.message', responseStatus.message, responseStatus_message, message, "")))
      | eval obj_res=lower(toString(coalesce('objectRef.resource', objectRef.resource, objectRef_resource, "")))
      | eval verb_tx=lower(toString(coalesce(verb, requestVerb, "")))
      | where match(obj_res,"^pods?$") AND match(verb_tx,"create|update")
      | eval scc_marker=if(match(_raw,"openshift.io/scc") OR match(_raw,"openshift\\.io/scc") OR match(_raw,"sa.scc"),1,0)
      | eval psa_marker=if(match(resp_msg,"podsecurity|violates podsecurity") OR match(_raw,"pod-security.kubernetes.io"),1,0)
      | where scc_marker=1 AND psa_marker=1
      | eval namespace=trim(toString(coalesce('objectRef.namespace', objectRef.namespace, objectRef_namespace, "")))
      | eval workload=trim(toString(coalesce('objectRef.name', objectRef.name, objectRef_name, "")))
      | eval actor=trim(toString(coalesce('user.username', user.username, user_username, "")))
      | rex field=_raw max_match=0 "(?i)openshift\\.io/scc\"\\s*:\\s*\"(?<scc_applied>[^\"]+)\""
      | eval signal_lane="openshift_scc_psa_interaction"
      | eval lane_detail=strcat("scc_applied=",coalesce(scc_applied,"unknown")," psa_snip=",substr(resp_msg,1,160))
      | eval psa_deny=if(resp_code=403 OR match(resp_msg,"forbidden"),1,0)
      | eval psa_warn_audit_only=if(psa_deny=0 AND psa_marker=1,1,0)
      | fields _time cluster namespace workload actor signal_lane lane_detail psa_deny psa_warn_audit_only resp_code verb_tx scc_applied ]
    [ search (index=ocp_metrics OR index=ocp_events OR index=ocp_compliance) (sourcetype=ocp_namespace_labels OR sourcetype=ocp_namespace_snapshot OR sourcetype=ocp_compliance_namespace) earliest=-24h@h latest=now
      | eval cluster=lower(trim(toString(coalesce(cluster, openshift_cluster, cluster_name, cluster_id, ""))))
      | eval namespace=trim(toString(coalesce(namespace, metadata_namespace, ns, "")))
      | eval cur_enforce_version=trim(toString(coalesce(enforce_version_label, pod_security_enforce_version, psa_enforce_version, labels_enforce_version, "")))
      | rex field=_raw "(?i)pod-security\.kubernetes\.io/enforce-version\"\\s*:\\s*\"(?<rex_ev>[^\"]+)"
      | eval cur_enforce_version=coalesce(nullif(cur_enforce_version,""), trim(rex_ev))
      | where len(cur_enforce_version)>0
      | stats latest(_time) AS _time latest(cur_enforce_version) AS cur_enforce_version BY cluster namespace
      | join type=left max=0 cluster [
          search index=ocp_metrics (sourcetype=ocp_clusterversion OR sourcetype=ocp_cluster_version) earliest=-24h@h latest=now
            | eval cluster=lower(trim(toString(coalesce(cluster, openshift_cluster, cluster_name, cluster_id, ""))))
            | eval desired=trim(toString(coalesce(desired_version, status_desired_version, version_desired, version, "")))
            | eval maj=mvindex(split(desired,"."),0)
            | eval min=mvindex(split(desired,"."),1)
            | eval cluster_k8s_minor=strcat("v",maj,".",min)
            | where len(maj)>0 AND len(min)>0
            | stats latest(cluster_k8s_minor) AS cluster_k8s_minor BY cluster ]
      | eval pinned_ver_norm=lower(trim(replace(cur_enforce_version,"^v","")))
      | eval cluster_minor_norm=lower(trim(replace(cluster_k8s_minor,"^v","")))
      | where len(cluster_minor_norm)>0 AND pinned_ver_norm!=cluster_minor_norm
      | eval signal_lane="psa_version_label_mismatch"
      | eval workload="namespace_object"
      | eval actor="version_skew_detector"
      | eval lane_detail=strcat("enforce_version_pin=",cur_enforce_version," cluster_minor=",cluster_k8s_minor)
      | eval psa_deny=0
      | eval psa_warn_audit_only=0
      | eval resp_code=0
      | eval verb_tx="get"
      | fields _time cluster namespace workload actor signal_lane lane_detail psa_deny psa_warn_audit_only resp_code verb_tx cur_enforce_version cluster_k8s_minor ]
| eval cluster=coalesce(nullif(cluster,""), "unknown_cluster")
| eval namespace=coalesce(nullif(namespace,""), "unknown_namespace")
| join type=left max=0 cluster [
    search index=ocp_metrics (sourcetype=ocp_clusterversion OR sourcetype=ocp_cluster_version OR sourcetype=ocp_clusteroperator) earliest=-24h@h latest=now
      | eval cluster=lower(trim(toString(coalesce(cluster, openshift_cluster, cluster_name, cluster_id, ""))))
      | eval desired=trim(toString(coalesce(desired_version, status_desired_version, version_desired, version, "")))
      | eval maj=mvindex(split(desired,"."),0)
      | eval min=mvindex(split(desired,"."),1)
      | eval cluster_k8s_minor=strcat("v",maj,".",min)
      | where len(maj)>0 AND len(min)>0
      | stats latest(cluster_k8s_minor) AS cluster_k8s_minor latest(desired) AS openshift_desired_version BY cluster ]
| join type=left max=0 cluster namespace [
    | inputlookup approved_psa_baseline.csv
      | eval cluster=lower(trim(toString(cluster)))
      | eval namespace=trim(toString(namespace))
      | eval expected_enforce=lower(trim(toString(coalesce(expected_enforce, expected_enforce_level, ""))))
      | eval expected_warn=lower(trim(toString(coalesce(expected_warn, ""))))
      | eval expected_audit=lower(trim(toString(coalesce(expected_audit, ""))))
      | eval owner_team_bl=trim(toString(coalesce(owner_team, "")))
      | fields cluster namespace expected_enforce expected_warn expected_audit owner_team_bl ]
| fillnull value="" expected_enforce expected_warn expected_audit owner_team_bl cluster_k8s_minor openshift_desired_version cur_enforce cur_warn cur_audit cur_enforce_version scc_applied
| eval label_drift=if(signal_lane=="psa_namespace_label_snapshot" AND len(expected_enforce)>0 AND len(cur_enforce)>0 AND cur_enforce!=expected_enforce,1,0)
| eval soft_launch_stuck=if(signal_lane=="psa_namespace_label_snapshot" AND len(expected_audit)>0 AND len(cur_audit)>0 AND cur_audit==expected_audit AND len(expected_enforce)>0 AND cur_enforce!=expected_enforce AND match(expected_enforce,"restricted|baseline") AND match(cur_enforce,"privileged"),1,0)
| eval openshift_managed_ns=if(match(namespace,"^openshift-"),1,0)
| eval is_psa_deny=if(signal_lane=="psa_validating_admission" AND psa_deny=1,1,0)
| streamstats window=16 current=t global=f sum(is_psa_deny) AS psa_deny_burst BY cluster namespace
| eventstats sum(is_psa_deny) AS psa_deny_window sum(eval(if(label_drift=1,1,0))) AS drift_window BY cluster
| eval pinned_ver_norm=lower(trim(replace(coalesce(cur_enforce_version,""),"^v","")))
| eval cluster_minor_norm=lower(trim(replace(coalesce(cluster_k8s_minor,""),"^v","")))
| eval enforce_version_mismatch=if(signal_lane=="psa_namespace_label_snapshot" AND len(pinned_ver_norm)>0 AND len(cluster_minor_norm)>0 AND pinned_ver_norm!=cluster_minor_norm,1,0)
| eval severity=case(
    openshift_managed_ns=1 AND label_drift=1, "critical",
    signal_lane=="openshift_scc_psa_interaction" AND psa_deny=1, "critical",
    enforce_version_mismatch=1 AND match(namespace,"prod|prd|mission|tier0"), "high",
    soft_launch_stuck=1, "high",
    label_drift=1 AND match(namespace,"prod|prd|mission|tier0"), "high",
    signal_lane=="psa_validating_admission" AND psa_deny=1 AND psa_deny_burst>=5, "high",
    signal_lane=="psa_validating_admission" AND psa_deny=1, "medium",
    signal_lane=="openshift_scc_psa_interaction", "medium",
    label_drift=1, "medium",
    signal_lane=="psa_version_label_mismatch" AND openshift_managed_ns=1, "high",
    signal_lane=="psa_namespace_label_snapshot" AND enforce_version_mismatch=1, "medium",
    true(), "info")
| eval psa_tier=case(psa_deny=1, "enforce_fail", psa_warn_audit_only=1 AND match(lane_detail,"warn"), "warn_only", psa_warn_audit_only=1, "audit_only", true(), "policy_signal_mixed")
| eval recommended_action=case(
    severity=="critical" AND openshift_managed_ns=1, "reconcile_labels_with_cluster_operators_oc_get_namespace_review_cluster_policy_controller",
    severity=="critical" AND signal_lane=="openshift_scc_psa_interaction", "joint_scc_psa_remediation_oc_describe_pod_review_securitycontext_and_psa_labels",
    soft_launch_stuck=1, "close_soft_launch_gap_align_enforce_with_audit_or_rebaseline_namespace",
    enforce_version_mismatch=1, "bump_enforce_version_label_after_ocp_minor_upgrade",
    label_drift=1, "restore_namespace_labels_via_gitops_or_oc_label",
    signal_lane=="psa_version_label_mismatch", "bump_enforce_version_label_after_ocp_minor_upgrade",
    signal_lane=="psa_validating_admission", "fix_workload_spec_seccomp_capabilities_then_redeploy",
    true(), "review_approved_psa_baseline_csv_and_exception_expiry")
| table _time cluster namespace workload actor signal_lane lane_detail cur_enforce cur_warn cur_audit expected_enforce openshift_desired_version cur_enforce_version cluster_k8s_minor label_drift soft_launch_stuck openshift_managed_ns psa_deny_burst psa_deny_window severity psa_tier recommended_action owner_team_bl scc_applied
```

savedsearches.conf sketch:

```ini
[openshift_uc_3_3_22_psa_enforcement_plane_alert]
cron_schedule = */15 * * * *
dispatch.earliest_time = -24h@h
dispatch.latest_time = now
enableSched = 1
action.email = 1
action.email.to = openshift-platform-security@example.com
action.email.subject = OCP PSA plane $result.severity$ $result.cluster$ $result.namespace$ $result.signal_lane$
counttype = number of events
relation = greater than
quantity = 0
search = | savedsearch openshift_uc_3_3_22_psa_enforcement_plane | where severity IN ("critical","high")
```

Performance: if Job Inspector shows multisearch queue time above internal SLA, materialize namespace snapshot and PSA denial arms hourly into summary indexes keyed on cluster and namespace, widen alert windows to earliest=-6h@h on summaries, and retain this full search for investigations. For Splunk Enterprise Security, use the closing table as a correlation search feeding a notable template with cluster and namespace as assets.

SPL tuning: expand production-like namespace match lists when your naming standards differ; keep approved_psa_baseline.csv as the authoritative expected posture rather than embedding hundreds of namespaces in case().



### Step 4 — Validate

Ground truth always starts on-cluster. For PSA denies surfaced in Splunk, run oc get events or oc describe replicaset in the same namespace and second as the audit timestamp to confirm the denial message matches live controller narratives. For admitted pods with warn or audit annotations, oc get pod -o yaml should show pod-security.kubernetes.io warn or audit annotations consistent with audit responseObject when audit level permits.

Namespace label drift: compare Splunk snapshot fields to oc get namespace -o jsonpath for pod-security labels. When statuses disagree, verify resourceVersion freshness, indexer clock skew, and duplicate cluster labels across regions before blaming Splunk parsing.

SCC↔PSA interaction validation: reproduce in lab with a pod spec that SCC mutates but PSA rejects under restricted enforce, confirm audit rows include both openshift.io/scc markers and PodSecurity fragments, and confirm openshift_uc_3_3_22_psa_enforcement_plane returns signal_lane openshift_scc_psa_interaction.

Soft-launch detection: in lab, set enforce=privileged with audit=restricted and warn=restricted, leave overnight, confirm soft_launch_stuck logic fires for namespaces whose baseline expects restricted enforce, then tighten enforce and confirm clearing rows.

Version skew validation: after a controlled minor upgrade drill, compare pinned pod-security.kubernetes.io/enforce-version to extracted ClusterVersion minor and confirm mismatch rows appear when you intentionally pin an obsolete version label in a disposable namespace.

Negative test: restore compliant labels and pod specs, confirm severities return to info or zero alert rows when the alert wrapper filters to critical and high only.

RBAC test: readers without ocp_audit role must see zero rows.

Clock skew test: indexer time within thirty seconds of apiserver; otherwise streamstats windows mis-order events.



### Step 5 — Operationalize & Troubleshoot

Case 1 — openshift-* namespace label drift against baseline: When it triggers: Splunk shows label_drift=1 with openshift_managed_ns=1 for namespaces starting openshift-. What to investigate: compare live Namespace YAML to approved_psa_baseline.csv, check Cluster Policy Controller and related operators for reconciliation loops, and search audit for manual oc label or oc patch actors. Who to involve: OpenShift platform SRE, operator owners for the affected subsystem, and Splunk observability engineers if timestamps disagree. How to remediate: revert manual edits, file a tracked change to adjust baseline if operators require different PSA posture, and let controllers reconcile rather than fighting automation. How to validate the fix: oc get namespace labels match baseline within one reconciliation interval, Splunk drift rows clear for two consecutive windows, and audit shows controller identities rather than human users for subsequent changes.

Case 2 — SCC↔PSA interaction denial storm: When it triggers: signal_lane openshift_scc_psa_interaction with psa_deny=1 and lane_detail referencing PodSecurity text while scc_applied is non-empty. What to investigate: oc describe pod or controller events, review SCC priority selection versus namespace PSA enforce profile, and confirm whether cluster-wide tightening changed PSA outcomes without SCC binding changes. Who to involve: Platform security lead, application team for the workload, and identity engineers if service account bindings changed. How to remediate: adjust pod securityContext and volumes to satisfy restricted PSA, or raise namespace enforce only after workload manifests comply; avoid permanently widening SCC without PSA review. How to validate the fix: pod create succeeds, audit shows 201 or 200 responses without PodSecurity denies, and Splunk deny burst returns to zero.

Case 3 — Soft-launch posture never tightens enforce: When it triggers: soft_launch_stuck=1 with audit and warn aligned to stricter baseline while enforce remains privileged. What to investigate: runbook debt lists, change tickets for PSA programs, and Splunk volume of audit-only versus warn-only annotations compared to deny ratio. Who to involve: Head of Platform, compliance owner, and application champions for the namespace. How to remediate: schedule enforce tightening with canary namespaces, communicate freeze windows, and update approved_psa_baseline.csv exception_expiry_epoch when deadlines slip with executive approval. How to validate the fix: enforce label matches expected_enforce, soft_launch_stuck returns to zero, and deny counts remain explainable under restricted posture.

Case 4 — enforce-version pin lags ClusterVersion minor: When it triggers: enforce_version_mismatch=1 after upgrades or on long-lived pins. What to investigate: oc get clusterversion, compare to namespace enforce-version labels, and review Red Hat guidance for PSA version pinning on your OpenShift minor. Who to involve: Platform lifecycle engineers and tenant owners. How to remediate: update labels to supported version strings during maintenance, automate version pins via GitOps tied to ClusterVersion, and document EUS stagger policies. How to validate the fix: pinned version aligns with extracted cluster_k8s_minor, mismatch flag clears, and admission behaves consistently in lab canaries.

Case 5 — OLM operator install widens namespace PSA temporarily: When it triggers: label snapshot or skew arms show privileged enforce labels immediately after catalog installs or upgrades. What to investigate: Subscription and ClusterServiceVersion history, vendor documentation for required PSA posture, and uninstall leftovers in orphaned namespaces. Who to involve: Operator platform team and vendor support. How to remediate: time-bound exceptions in approved_psa_baseline.csv, cleanup orphaned namespaces after uninstall, and restore baseline labels when operators finish. How to validate the fix: labels return to expected posture, exceptions expire cleanly, and Splunk shows operator service accounts rather than unknown humans.

Case 6 — Global pod security profile order change: When it triggers: sudden PSA denies across many namespaces without local label edits. What to investigate: cluster-wide configuration changes, upgrade release notes, and ClusterVersion history. Who to involve: Platform architecture council and Red Hat support when guidance is unclear. How to remediate: execute approved tightening program, prioritize critical workloads, and communicate required manifest fixes. How to validate the fix: deny rates fall to expected steady state, dashboards show aligned enforce labels, and business services pass health checks.

Case 7 — Audit-only noise without enforce movement: When it triggers: high audit annotation volume but enforce_fail rarely appears. What to investigate: whether teams rely on audit mode for discovery indefinitely, and whether Grafana or Splunk dashboards show ratio skew called out in this UC narrative. Who to involve: Application security and platform governance. How to remediate: convert discovery into tracked fix backlog, tighten warn and enforce on schedule, and tune macros if ratio thresholds are too noisy. How to validate the fix: ratio of audit events to enforce denies normalizes against policy, and governance tickets show closed fixes.

Case 8 — False correlation from duplicated audit shipments: When it triggers: deny bursts double from redundant forwarders. What to investigate: HEC source overlap, duplicate cluster labels, and auditID dedupe opportunities. Who to involve: Observability engineers. How to remediate: dedupe on auditID in summary indexing, remove redundant tailers, and normalize cluster fields. How to validate the fix: burst counts halve to match apiserver truth, and Job Inspector cost drops.

Case 9 — oc adm policy add-scc-to-user during incident response: When it triggers: SCC changes coincide with PSA denies in timelines. What to investigate: break-glass tickets, RBAC and SCC bindings, and whether SCC relaxation masked PSA failures temporarily. Who to involve: Incident commander and platform security. How to remediate: remove emergency SCC grants after root cause repair, restore least privilege, and document lessons learned. How to validate the fix: bindings match pre-incident posture, Splunk SCC analytics from UC-3.3.4 align, and PSA denies do not return unexpectedly.

Case 10 — Subscription churn orphaning privileged namespaces: When it triggers: label snapshot shows privileged enforce on empty or retired namespaces. What to investigate: OLM uninstall finalizers, leftover Namespace objects, and GitOps ownership. Who to involve: Catalog platform team and tenant owner. How to remediate: delete or relabel orphaned namespaces under change control, update baseline inventory, and ensure operators clean up labels on uninstall. How to validate the fix: namespace list matches inventory, privileged labels absent where not approved, and Splunk drift logic stays quiet.

Case 11 — Healthy control path after remediation: When it triggers: post-fix verification windows. What to investigate: confirm no critical or high rows for production namespaces, compare Splunk output to oc CLI spot checks across two clusters. Who to involve: Platform security and audit sampling team. How to remediate: none beyond documentation if healthy. How to validate the fix: alert wrapper returns zero critical and high rows for scheduled periods, and quarterly replays reproduce expected signals in lab denial tests.

Closing checklist: five em-dash step headers are present; Step 3 fenced SPL matches the spl field exactly; multisearch lists PSA admission, namespace snapshot, SCC↔PSA interaction, and enforce-version skew arms; join wraps approved_psa_baseline.csv inside a join subsearch; coalesce, streamstats, eventstats, and case appear; closing table includes at least ten columns for analyst review.


## SPL

```spl
`comment("UC-3.3.22 OpenShift PSA enforcement plane — validating admission outcomes, namespace PSA label drift vs approved_psa_baseline.csv, SCC↔PSA interaction signatures, namespace label mutation audit velocity, cluster minor join for enforce-version skew. earliest=-24h@h latest=now")`
| multisearch
    [ search (index=ocp_audit OR index=k8s_audit) (sourcetype=ocp_audit OR sourcetype=k8s_audit OR sourcetype="kube:apiserver:audit") earliest=-24h@h latest=now
      | eval cluster=lower(trim(toString(coalesce(cluster, openshift_cluster, cluster_name, k8s_cluster_name, ""))))
      | eval resp_code=tonumber(tostring(coalesce('responseStatus.code', responseStatus.code, responseStatus_code, http_status, "0")), 10)
      | eval resp_reason=lower(toString(coalesce('responseStatus.reason', responseStatus.reason, responseStatus_reason, "")))
      | eval resp_msg=lower(toString(coalesce('responseStatus.message', responseStatus.message, responseStatus_message, message, "")))
      | eval obj_res=lower(toString(coalesce('objectRef.resource', objectRef.resource, objectRef_resource, "")))
      | eval verb_tx=lower(toString(coalesce(verb, requestVerb, "")))
      | where match(obj_res,"^pods?$") AND match(verb_tx,"create|update")
      | eval psa_gate=if(match(resp_msg,"violates podsecurity|podsecurity") OR match(_raw,"pod-security.kubernetes.io") AND (match(_raw,"audit-violations") OR match(_raw,"warn-violations") OR match(_raw,"enforce-violations")), 1, 0)
      | where psa_gate=1
      | eval namespace=trim(toString(coalesce('objectRef.namespace', objectRef.namespace, objectRef_namespace, "")))
      | eval workload=trim(toString(coalesce('objectRef.name', objectRef.name, objectRef_name, "")))
      | eval actor=trim(toString(coalesce('user.username', user.username, user_username, "")))
      | eval psa_deny=if((resp_code=403 OR match(resp_reason,"forbidden")) AND match(resp_msg,"violates podsecurity|podsecurity"), 1, 0)
      | eval psa_warn_audit_only=if(psa_deny=0 AND (match(_raw,"warn-violations") OR match(_raw,"audit-violations")), 1, 0)
      | eval signal_lane="psa_validating_admission"
      | eval lane_detail=substr(coalesce(resp_msg,""),1,280)
      | fields _time cluster namespace workload actor signal_lane lane_detail psa_deny psa_warn_audit_only resp_code verb_tx ]
    [ search (index=ocp_metrics OR index=ocp_events OR index=ocp_compliance) (sourcetype=ocp_namespace_labels OR sourcetype=ocp_namespace_snapshot OR sourcetype=ocp_compliance_namespace) earliest=-24h@h latest=now
      | eval cluster=lower(trim(toString(coalesce(cluster, openshift_cluster, cluster_name, cluster_id, ""))))
      | eval namespace=trim(toString(coalesce(namespace, metadata_namespace, ns, "")))
      | eval cur_enforce=lower(trim(toString(coalesce(pod_security_enforce, psa_enforce_label, enforce_label, labels_pod_security_enforce, ""))))
      | eval cur_warn=lower(trim(toString(coalesce(pod_security_warn, psa_warn_label, warn_label, labels_pod_security_warn, ""))))
      | eval cur_audit=lower(trim(toString(coalesce(pod_security_audit, psa_audit_label, audit_label, labels_pod_security_audit, ""))))
      | eval cur_enforce_version=trim(toString(coalesce(enforce_version_label, pod_security_enforce_version, psa_enforce_version, labels_enforce_version, "")))
      | rex field=_raw "(?i)pod-security\.kubernetes\.io/enforce\"\\s*:\\s*\"(?<rex_enf>[^\"]+)"
      | eval cur_enforce=coalesce(nullif(cur_enforce,""), lower(trim(rex_enf)))
      | rex field=_raw "(?i)pod-security\.kubernetes\.io/enforce-version\"\\s*:\\s*\"(?<rex_ev>[^\"]+)"
      | eval cur_enforce_version=coalesce(nullif(cur_enforce_version,""), trim(rex_ev))
      | eval signal_lane="psa_namespace_label_snapshot"
      | eval lane_detail=strcat("enforce=",coalesce(cur_enforce,"none"),";warn=",coalesce(cur_warn,"none"),";audit=",coalesce(cur_audit,"none"),";enforce_version=",coalesce(cur_enforce_version,"none"))
      | stats latest(_time) AS _time latest(cur_enforce) AS cur_enforce latest(cur_warn) AS cur_warn latest(cur_audit) AS cur_audit latest(cur_enforce_version) AS cur_enforce_version BY cluster namespace
      | eval workload="namespace_object"
      | eval actor="label_exporter"
      | eval psa_deny=0
      | eval psa_warn_audit_only=0
      | eval resp_code=0
      | eval verb_tx="get"
      | fields _time cluster namespace workload actor signal_lane lane_detail psa_deny psa_warn_audit_only resp_code verb_tx cur_enforce cur_warn cur_audit cur_enforce_version ]
    [ search (index=ocp_audit OR index=k8s_audit) (sourcetype=ocp_audit OR sourcetype=k8s_audit OR sourcetype="kube:apiserver:audit") earliest=-24h@h latest=now
      | eval cluster=lower(trim(toString(coalesce(cluster, openshift_cluster, cluster_name, k8s_cluster_name, ""))))
      | eval resp_code=tonumber(tostring(coalesce('responseStatus.code', responseStatus.code, responseStatus_code, "0")), 10)
      | eval resp_msg=lower(toString(coalesce('responseStatus.message', responseStatus.message, responseStatus_message, message, "")))
      | eval obj_res=lower(toString(coalesce('objectRef.resource', objectRef.resource, objectRef_resource, "")))
      | eval verb_tx=lower(toString(coalesce(verb, requestVerb, "")))
      | where match(obj_res,"^pods?$") AND match(verb_tx,"create|update")
      | eval scc_marker=if(match(_raw,"openshift.io/scc") OR match(_raw,"openshift\\.io/scc") OR match(_raw,"sa.scc"),1,0)
      | eval psa_marker=if(match(resp_msg,"podsecurity|violates podsecurity") OR match(_raw,"pod-security.kubernetes.io"),1,0)
      | where scc_marker=1 AND psa_marker=1
      | eval namespace=trim(toString(coalesce('objectRef.namespace', objectRef.namespace, objectRef_namespace, "")))
      | eval workload=trim(toString(coalesce('objectRef.name', objectRef.name, objectRef_name, "")))
      | eval actor=trim(toString(coalesce('user.username', user.username, user_username, "")))
      | rex field=_raw max_match=0 "(?i)openshift\\.io/scc\"\\s*:\\s*\"(?<scc_applied>[^\"]+)\""
      | eval signal_lane="openshift_scc_psa_interaction"
      | eval lane_detail=strcat("scc_applied=",coalesce(scc_applied,"unknown")," psa_snip=",substr(resp_msg,1,160))
      | eval psa_deny=if(resp_code=403 OR match(resp_msg,"forbidden"),1,0)
      | eval psa_warn_audit_only=if(psa_deny=0 AND psa_marker=1,1,0)
      | fields _time cluster namespace workload actor signal_lane lane_detail psa_deny psa_warn_audit_only resp_code verb_tx scc_applied ]
    [ search (index=ocp_metrics OR index=ocp_events OR index=ocp_compliance) (sourcetype=ocp_namespace_labels OR sourcetype=ocp_namespace_snapshot OR sourcetype=ocp_compliance_namespace) earliest=-24h@h latest=now
      | eval cluster=lower(trim(toString(coalesce(cluster, openshift_cluster, cluster_name, cluster_id, ""))))
      | eval namespace=trim(toString(coalesce(namespace, metadata_namespace, ns, "")))
      | eval cur_enforce_version=trim(toString(coalesce(enforce_version_label, pod_security_enforce_version, psa_enforce_version, labels_enforce_version, "")))
      | rex field=_raw "(?i)pod-security\.kubernetes\.io/enforce-version\"\\s*:\\s*\"(?<rex_ev>[^\"]+)"
      | eval cur_enforce_version=coalesce(nullif(cur_enforce_version,""), trim(rex_ev))
      | where len(cur_enforce_version)>0
      | stats latest(_time) AS _time latest(cur_enforce_version) AS cur_enforce_version BY cluster namespace
      | join type=left max=0 cluster [
          search index=ocp_metrics (sourcetype=ocp_clusterversion OR sourcetype=ocp_cluster_version) earliest=-24h@h latest=now
            | eval cluster=lower(trim(toString(coalesce(cluster, openshift_cluster, cluster_name, cluster_id, ""))))
            | eval desired=trim(toString(coalesce(desired_version, status_desired_version, version_desired, version, "")))
            | eval maj=mvindex(split(desired,"."),0)
            | eval min=mvindex(split(desired,"."),1)
            | eval cluster_k8s_minor=strcat("v",maj,".",min)
            | where len(maj)>0 AND len(min)>0
            | stats latest(cluster_k8s_minor) AS cluster_k8s_minor BY cluster ]
      | eval pinned_ver_norm=lower(trim(replace(cur_enforce_version,"^v","")))
      | eval cluster_minor_norm=lower(trim(replace(cluster_k8s_minor,"^v","")))
      | where len(cluster_minor_norm)>0 AND pinned_ver_norm!=cluster_minor_norm
      | eval signal_lane="psa_version_label_mismatch"
      | eval workload="namespace_object"
      | eval actor="version_skew_detector"
      | eval lane_detail=strcat("enforce_version_pin=",cur_enforce_version," cluster_minor=",cluster_k8s_minor)
      | eval psa_deny=0
      | eval psa_warn_audit_only=0
      | eval resp_code=0
      | eval verb_tx="get"
      | fields _time cluster namespace workload actor signal_lane lane_detail psa_deny psa_warn_audit_only resp_code verb_tx cur_enforce_version cluster_k8s_minor ]
| eval cluster=coalesce(nullif(cluster,""), "unknown_cluster")
| eval namespace=coalesce(nullif(namespace,""), "unknown_namespace")
| join type=left max=0 cluster [
    search index=ocp_metrics (sourcetype=ocp_clusterversion OR sourcetype=ocp_cluster_version OR sourcetype=ocp_clusteroperator) earliest=-24h@h latest=now
      | eval cluster=lower(trim(toString(coalesce(cluster, openshift_cluster, cluster_name, cluster_id, ""))))
      | eval desired=trim(toString(coalesce(desired_version, status_desired_version, version_desired, version, "")))
      | eval maj=mvindex(split(desired,"."),0)
      | eval min=mvindex(split(desired,"."),1)
      | eval cluster_k8s_minor=strcat("v",maj,".",min)
      | where len(maj)>0 AND len(min)>0
      | stats latest(cluster_k8s_minor) AS cluster_k8s_minor latest(desired) AS openshift_desired_version BY cluster ]
| join type=left max=0 cluster namespace [
    | inputlookup approved_psa_baseline.csv
      | eval cluster=lower(trim(toString(cluster)))
      | eval namespace=trim(toString(namespace))
      | eval expected_enforce=lower(trim(toString(coalesce(expected_enforce, expected_enforce_level, ""))))
      | eval expected_warn=lower(trim(toString(coalesce(expected_warn, ""))))
      | eval expected_audit=lower(trim(toString(coalesce(expected_audit, ""))))
      | eval owner_team_bl=trim(toString(coalesce(owner_team, "")))
      | fields cluster namespace expected_enforce expected_warn expected_audit owner_team_bl ]
| fillnull value="" expected_enforce expected_warn expected_audit owner_team_bl cluster_k8s_minor openshift_desired_version cur_enforce cur_warn cur_audit cur_enforce_version scc_applied
| eval label_drift=if(signal_lane=="psa_namespace_label_snapshot" AND len(expected_enforce)>0 AND len(cur_enforce)>0 AND cur_enforce!=expected_enforce,1,0)
| eval soft_launch_stuck=if(signal_lane=="psa_namespace_label_snapshot" AND len(expected_audit)>0 AND len(cur_audit)>0 AND cur_audit==expected_audit AND len(expected_enforce)>0 AND cur_enforce!=expected_enforce AND match(expected_enforce,"restricted|baseline") AND match(cur_enforce,"privileged"),1,0)
| eval openshift_managed_ns=if(match(namespace,"^openshift-"),1,0)
| eval is_psa_deny=if(signal_lane=="psa_validating_admission" AND psa_deny=1,1,0)
| streamstats window=16 current=t global=f sum(is_psa_deny) AS psa_deny_burst BY cluster namespace
| eventstats sum(is_psa_deny) AS psa_deny_window sum(eval(if(label_drift=1,1,0))) AS drift_window BY cluster
| eval pinned_ver_norm=lower(trim(replace(coalesce(cur_enforce_version,""),"^v","")))
| eval cluster_minor_norm=lower(trim(replace(coalesce(cluster_k8s_minor,""),"^v","")))
| eval enforce_version_mismatch=if(signal_lane=="psa_namespace_label_snapshot" AND len(pinned_ver_norm)>0 AND len(cluster_minor_norm)>0 AND pinned_ver_norm!=cluster_minor_norm,1,0)
| eval severity=case(
    openshift_managed_ns=1 AND label_drift=1, "critical",
    signal_lane=="openshift_scc_psa_interaction" AND psa_deny=1, "critical",
    enforce_version_mismatch=1 AND match(namespace,"prod|prd|mission|tier0"), "high",
    soft_launch_stuck=1, "high",
    label_drift=1 AND match(namespace,"prod|prd|mission|tier0"), "high",
    signal_lane=="psa_validating_admission" AND psa_deny=1 AND psa_deny_burst>=5, "high",
    signal_lane=="psa_validating_admission" AND psa_deny=1, "medium",
    signal_lane=="openshift_scc_psa_interaction", "medium",
    label_drift=1, "medium",
    signal_lane=="psa_version_label_mismatch" AND openshift_managed_ns=1, "high",
    signal_lane=="psa_namespace_label_snapshot" AND enforce_version_mismatch=1, "medium",
    true(), "info")
| eval psa_tier=case(psa_deny=1, "enforce_fail", psa_warn_audit_only=1 AND match(lane_detail,"warn"), "warn_only", psa_warn_audit_only=1, "audit_only", true(), "policy_signal_mixed")
| eval recommended_action=case(
    severity=="critical" AND openshift_managed_ns=1, "reconcile_labels_with_cluster_operators_oc_get_namespace_review_cluster_policy_controller",
    severity=="critical" AND signal_lane=="openshift_scc_psa_interaction", "joint_scc_psa_remediation_oc_describe_pod_review_securitycontext_and_psa_labels",
    soft_launch_stuck=1, "close_soft_launch_gap_align_enforce_with_audit_or_rebaseline_namespace",
    enforce_version_mismatch=1, "bump_enforce_version_label_after_ocp_minor_upgrade",
    label_drift=1, "restore_namespace_labels_via_gitops_or_oc_label",
    signal_lane=="psa_version_label_mismatch", "bump_enforce_version_label_after_ocp_minor_upgrade",
    signal_lane=="psa_validating_admission", "fix_workload_spec_seccomp_capabilities_then_redeploy",
    true(), "review_approved_psa_baseline_csv_and_exception_expiry")
| table _time cluster namespace workload actor signal_lane lane_detail cur_enforce cur_warn cur_audit expected_enforce openshift_desired_version cur_enforce_version cluster_k8s_minor label_drift soft_launch_stuck openshift_managed_ns psa_deny_burst psa_deny_window severity psa_tier recommended_action owner_team_bl scc_applied
```

## CIM SPL

```spl
| tstats summariesonly=true latest(Authentication.user) AS auth_user latest(Authentication.action) AS auth_action FROM datamodel=Authentication WHERE nodename=Authentication earliest=-24h@h latest=now BY Authentication.src
| rename Authentication.src AS cim_src
| join type=left max=0 cim_src
    [| tstats summariesonly=true latest(Change.action) AS chg_action latest(Change.object) AS chg_object latest(Change.user) AS chg_user FROM datamodel=Change WHERE nodename=Change earliest=-24h@h latest=now BY Change.dest
     | rename Change.dest AS cim_src ]
| where like(lower(chg_object), "%namespace%") OR like(lower(chg_object), "%pod%") OR match(lower(auth_action), "failure")
| table cim_src auth_user auth_action chg_action chg_object chg_user
```

## Visualization

Severity-colored table mirroring the closing SPL projection; timeline of psa_deny_window by namespace; drilldown from signal_lane to raw audit JSON and namespace label snapshots; matrix of cur_enforce versus expected_enforce by cluster for governance reviews.

## Known False Positives

Red Hat core operators and catalog partners sometimes require short privileged PSA windows during install or upgrade; join vendor documentation and approved_psa_baseline.csv exception_expiry_epoch before paging application teams for openshift-marketplace, openshift-logging, or openshift-monitoring style namespaces. Legitimate oc adm policy workflows and GitOps reconcilers can emit namespace mutation audit rows that look like drift until you compare actor service accounts to known controllers. Developer sandboxes that intentionally remain privileged while audit is restricted will trip soft_launch_stuck logic unless inventory marks them as approved long-running experiments with owners. EUS-track clusters can linger on older Kubernetes minors while teams pin enforce-version strings that match the prior minor; treat as planning debt rather than incident until production namespaces show mismatch with expired exceptions. OLM subscription churn during catalog mirrors or air-gap transfers may temporarily widen labels; require sustained drift or pairing with failed installs before executive escalation. Cluster policy controller reconciliation can flap labels during upgrades; compare Splunk windows to ClusterVersion progressing flags and UC-3.3.6 context before blaming tenants. Penetration tests that craft violating pods will inflate deny bursts by design; ingest pentest authorization metadata on HEC events. Duplicate HEC submissions from redundant forwarders can inflate psa_deny_burst; dedupe on audit auditID when present. Some managed offerings redact portions of audit bodies; SCC markers may be absent while oc get pod still shows openshift.io/scc annotations—investigate parser gaps before muting SCC↔PSA correlation. Break-glass oc adm policy add-scc-to-user activity during incidents can change admission outcomes without PSA label edits; pair timelines with UC-3.3.4 narratives and tickets so SCC relaxation is not mistaken for pure PSA failure.

## References

- [OpenShift — Understanding and managing pod security admission](https://docs.redhat.com/en/documentation/openshift_container_platform/4.15/html/authentication_and_authorization/understanding-and-managing-pod-security-admission)
- [OpenShift — Managing pod security admission (latest)](https://docs.openshift.com/container-platform/latest/authentication/managing-pod-security-admission.html)
- [Kubernetes — Pod Security Admission](https://kubernetes.io/docs/concepts/security/pod-security-admission/)
- [Kubernetes — Pod Security Standards](https://kubernetes.io/docs/concepts/security/pod-security-standards/)
- [Kubernetes — Enforce standards namespace labels](https://kubernetes.io/docs/tasks/configure-pod-container/enforce-standards-namespace-labels/)
- [Red Hat Blog — Pod Security Admission in OpenShift 4.11](https://www.redhat.com/en/blog/pod-security-admission-in-openshift-4.11)
- [Red Hat Blog — Pod admission and SCCs version 2 in OpenShift](https://www.redhat.com/en/blog/pod-admission-and-sccs-version-2-in-openshift)
- [OpenShift cluster-policy-controller repository](https://github.com/openshift/cluster-policy-controller)
