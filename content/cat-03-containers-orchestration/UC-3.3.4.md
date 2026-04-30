<!-- AUTO-GENERATED from UC-3.3.4.json — DO NOT EDIT -->

---
id: "3.3.4"
title: "OpenShift Security Context Constraint Violations and Privilege Escalation Detection"
status: "verified"
criticality: "high"
splunkPillar: "Security"
---

# UC-3.3.4 · OpenShift Security Context Constraint Violations and Privilege Escalation Detection

> **Criticality:** High &middot; **Difficulty:** Advanced &middot; **Pillar:** Security &middot; **Type:** Security &middot; **Wave:** Walk &middot; **Status:** Verified

*OpenShift applies extra safety rules that decide how much power each workload may request before it ever runs. We catch when those rules block pods unexpectedly, when someone widens the rules without a paper trail, or when a workload lands in a broader rule than your team expects.*

---

## Description

Detects OpenShift SCC admission denials, SecurityContextConstraints mutations, pod admission outcomes annotated with openshift.io/scc, and controller events that echo SCC failures—correlating them to namespace SCC tier expectations so teams see privilege escalation paths distinct from vanilla PSA, generic RBAC analytics, Docker socket exposure, or CRI runtime privilege drift. The analytic multisearches audit lanes for forbidden pod creates, SCC CRUD on security.openshift.io, successful pod creates that rex-extract the openshift.io/scc annotation from audit bodies, and ocp_events arms for FailedCreate or Forbidden, then applies coalesce normalization, eventstats for denial and mutation counts, streamstats for denial bursts, join to openshift_scc_namespace_policy.csv for selection skew, and case-driven severity with recommended_action verbs.

## Value

Platform and application security leaders gain a tamper-resistant narrative for the OpenShift-specific admission layer that governs hostNetwork, hostPID, RunAsAny strategies, allowedCapabilities, SELinux contexts, fsGroup ranges, and SCC priority selection—surfaces attackers and insiders widen faster than namespace PSA labels imply, and surfaces broken automation before repeated denial noise turns into an emergency deploy freeze. Auditors see continuous evidence that SCC grants, SCC object integrity, and openshift.io/scc admission truth are monitored—not only static RBAC spreadsheets. Mean time to contain improves when Splunk shows which ServiceAccount, namespace, and SCC class diverged from openshift_scc_namespace_policy.csv without conflating the signal with UC-3.2.22 PSA, UC-3.2.12 RBAC permission anomalies, UC-3.2.23 cluster-admin binding lifecycle, UC-3.1.25 docker.sock hostPath exposure, or UC-3.1.6 runtime privileged container drift.

## Implementation

Land ocp_audit or k8s_audit with ocp_audit, k8s_audit, or ocp_admission sourcetypes plus ocp_events into governed indexes; enable RequestResponse audit for pods and securitycontextconstraints; publish openshift_scc_namespace_policy.csv; save openshift_uc_3_3_4_scc_violations_escalation on a fifteen-minute cadence over earliest=-24h@h; route critical and high severities to platform security; archive weekly CSV exports with lookup commit hashes.

## Evidence

Saved search openshift_uc_3_3_4_scc_violations_escalation with fifteen minute schedule; versioned openshift_scc_namespace_policy.csv in git; weekly CSV exports to restricted evidence index; dashboard drilldowns on ocp_audit, k8s_audit, ocp_admission, and ocp_events; alert stanza with platform security routing keys.

## Control test

### Positive scenario

In a lab OpenShift cluster, attempt a pod create that requests capabilities no SCC grants the namespace ServiceAccount, ingest audit showing 403 with unable to validate against any security context constraint, and confirm openshift_uc_3_3_4_scc_violations_escalation emits signal_lane scc_admission_deny with non-zero denial_count_24h within the scheduled window.

### Negative scenario

After applying a compliant pod spec admitted under restricted-v2 with openshift.io/scc matching oc get pod, with no SCC mutations and no matching FailedCreate events, confirm severities remain info and the alert wrapper returns zero rows when filtering to critical and high only.

## Detailed Implementation

### Step 1 — Prerequisites

Head of Platform owns this control jointly with the OpenShift platform security lead, the identity and authorization engineers who interpret RBAC versus admission boundaries, and the observability staff who operate Splunk HTTP Event Collector tokens and OpenShift audit forwarding. This use case isolates Red Hat OpenShift Security Context Constraints (SCC): cluster-scoped admission policy objects in the security.openshift.io API group that the SCC admission plugin evaluates after authentication and RBAC authorize, but before a Pod is persisted. SCC predates upstream Kubernetes Pod Security Admission (PSA). PSA reads namespace labels on pod-security.kubernetes.io keys; SCC instead matches ServiceAccount-bound roles, runtime requests in pod.spec.securityContext and container securityContext, volumes, capabilities, SELinux contexts, seccomp profiles, host namespaces, and priority-ordered SCC objects returned by oc get scc. The admission controller selects a single SCC using the documented selection algorithm: consider SCCs the pod ServiceAccount may use, sort by priority, then choose the most restrictive SCC that still admits the pod. After admission, the apiserver annotates the Pod with openshift.io/scc naming the SCC that actually applied. That annotation is the authoritative ground truth for which SCC won, not the workload author's inline comments and not PSA labels on the namespace.

UC-3.2.22 remains Pod Security Admission denials and namespace PSS label drift on vanilla Kubernetes: violates PodSecurity messages, enforce labels, and kube-state-metrics kube_namespace_labels. This UC does not duplicate PSA. UC-3.2.12 remains RBAC verb and resource anomalies such as escalate, bind, or wildcard rules on Roles and ClusterRoles; granting RBAC to use an SCC is related but this UC focuses on SCC lifecycle signals, SCC admission outcomes, openshift.io/scc selection, and denial text from the SCC plugin rather than generic RBAC graph analytics. UC-3.2.23 remains ClusterRoleBinding grants of cluster-admin and other cluster-scoped binding tampering; oc adm policy add-scc-to-user mutates RoleBinding or ClusterRoleBinding objects that reference SCC use permissions, and this UC consumes those audit rows when they touch securitycontextconstraints, but does not replace cluster-admin escalation tracking. UC-3.1.25 remains Docker socket hostPath exposure. UC-3.1.6 remains container runtime privilege escalation on the node CRI surface. Splunk becomes the reconciliation ledger that fuses apiserver audit JSON for denied pod creates, successful pod creates carrying openshift.io/scc, SecurityContextConstraints object mutations, and OpenShift events that surface FailedCreate or Forbidden with SCC text.

Index and permission design land before parsers. Designate index=ocp_audit for Kubernetes apiserver audit or equivalent OpenShift-forwarded audit with sourcetype=ocp_audit or sourcetype=k8s_audit depending on whether you segregate OpenShift clusters from vanilla Kubernetes estates. Designate sourcetype=ocp_admission when you split admission webhook or apiserver admission plugin diagnostics into a dedicated pipeline; many teams keep a unified ocp_audit stream and filter in SPL. Designate index=ocp_events with sourcetype=ocp_events for Kubernetes Events involving Pods, ReplicationControllers, ReplicaSets, Deployments, and Job failures. Issue distinct HEC tokens per environment with least privilege: platform security may search all sourcetypes; application teams receive redacted views that omit requestObject except metadata when counsel requires minimization. Retention should cover at least thirty days hot for privilege reviews, ninety days when regulated customers require quarterly replays, and align cold storage with enterprise logging policy. Legal review should confirm service account names, namespace labels, and partial pod specs are acceptable in Splunk; never index Secret dataKey material.

RBAC and safety: the forwarder reading apiserver audit.log must run on control-plane hosts or use cloud-provider audit exports with read-only service roles. Dedicated management-cluster collectors should use short-lived kubeconfigs, not long-lived kubeadmin tokens on laptops. Break-glass administrators who run oc adm policy add-scc-to-user or add-scc-to-group should expect their actions in audit with user.username and user.groups preserved.

Audit policy depth: SCC denial messages include the substring unable to validate against any security context constraint when no SCC matches the pod requested capabilities. Capture RequestResponse for pod-creating verbs so responseStatus.message retains the full denial text and, on successful creates, responseObject.metadata.annotations carries openshift.io/scc. Metadata-only policies reduce volume but strip annotations analysts need; regulated tiers should keep RequestResponse for create, update, and patch on pods and for create, update, patch, delete on securitycontextconstraints resources. Follow OpenShift documentation for audit profile tuning (WriteRequestBodies, Metadata, None) and test volume before production.

Field normalization: flatten objectRef.apiGroup, objectRef.resource, objectRef.namespace, objectRef.name, user.username, verb, responseStatus.code, responseStatus.reason, responseStatus.message, requestObject.kind, and nested responseObject.metadata.annotations for openshift.io/scc. If JSON paths arrive dotted, coalesce() ladders in SPL still resolve. Cluster identity must appear as cluster, openshift_cluster, or cluster_name on every event.

Risk briefing: a burst of denials may indicate a misguided continuous deployment rollout rather than attack; correlate with deployment userAgent and GitOps commits before paging executives. Conversely, a quiet cluster with sudden mass binding of system:authenticated to anyuid is catastrophic even if pods still start. Namespace SCC annotations such as openshift.io/sa.scc.supplemental-groups on namespaces interact with supplemental group strategies; analysts should read OpenShift SCC documentation for strategy-specific behavior rather than assuming one field explains admission.

Differentiation recap: OpenShift SCC admission plugin outcomes and openshift.io/scc annotation truth, not PSA namespace labels alone, not generic RBAC graphs alone, not Docker socket hostPath analytics alone, not CRI runtime privileged container drift alone.

Operational posture: align telemetry with change tickets by stamping change_ticket_id on HEC events when platform teams grant vendor operators broader SCC classes. Maintain openshift_scc_namespace_policy.csv with columns cluster, namespace, expected_scc_tier, owner_team, exception_expiry_epoch, and notes so joins can classify selection skew without hard-coding hundreds of namespaces inside SPL.

### Step 2 — Configure data collection

Stand up four complementary lanes Splunk multisearch can fuse: apiserver audit for SCC-related denials and successful pod admissions, audit for SecurityContextConstraints mutations and SCC-binding RBAC changes, OpenShift events for controller-level FailedCreate and Forbidden reasons, and optional duplicate routing of the same audit to a cold evidence index for legal hold.

Audit lane primary: ship kube-apiserver audit.log into index=ocp_audit with sourcetype=ocp_audit using Splunk Connect for Kubernetes filelog patterns, Splunk OpenTelemetry Collector filelog receiver, or cloud-audit exports that preserve Kubernetes audit v1 JSON. Ensure stageTimestamp and requestReceivedTimestamp map to _time within thirty seconds of true apiserver time. Enable TLS to Splunk, rotate HEC tokens quarterly, and document which management cluster forwards lab versus production to prevent cluster label collisions.

Audit lane SCC object verbs: include rules for securitycontextconstraints in the security.openshift.io API group at RequestResponse or Metadata levels consistent with your volume budget. Mutations to allowedCapabilities, allowPrivilegeEscalation, runAsUser strategy RunAsAny, seLinuxContext type RunAsAny, volumes lists, seccompProfiles, and priority fields are high-signal governance events. oc get scc -o yaml snapshots from a cron job can land as sourcetype=ocp_scc_snapshot for drift baselines; this UC SPL focuses on audit deltas rather than full periodic snapshots, but snapshots help when audit retention is shorter than compliance windows.

Admission diagnostics: when platform teams operate a dedicated sourcetype=ocp_admission for aggregated admission plugin logs, ensure SCC plugin lines include pod namespace, pod name, service account, and SCC candidates if your distribution enriches logs. Not every cluster exposes the same enrichment; fall back to audit-only arms when ocp_admission is absent.

Events lane: forward Kubernetes Events with sourcetype=ocp_events using Splunk Add-on for Kubernetes event inputs or OpenTelemetry k8s_events receiver. Retain involvedObject.kind, involvedObject.name, involvedObject.namespace, reason, message, type, count, and firstTimestamp or lastTimestamp. FailedCreate and FailedScheduling reasons often include SCC denial text copied from the apiserver message. Normalize cluster labels identically to audit.

Example oc verification operators run during design reviews:

```bash
oc get scc -o custom-columns=NAME:.metadata.name,PRIV:.allowPrivilegedUser,PRIORITY:.priority,RUNAS:.runAsUser.type,CAPS:.allowedCapabilities
oc adm policy who-can use scc/privileged -n default
```

Example audit-policy fragment illustrating SCC and pod focus (tune omitStages and users per estate):

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
        resources: ["pods"]
    namespaces: ["*"]
  - level: RequestResponse
    verbs: ["create", "update", "patch", "delete"]
    resources:
      - group: "security.openshift.io"
        resources: ["securitycontextconstraints"]
    namespaces: []
```

props.conf guidance: TRUNCATE sufficiently large for RequestResponse bodies, TIMESTAMP_FIELDS respected when HEC time is authoritative, LINE_BREAKER for newline-delimited JSON audit files, and SEDCMD or transforms that strip tls.key-like patterns if misconfigured clients ever leak secrets.

Pre-save validation: index=ocp_audit earliest=-15m must return non-zero counts; sample responseStatus.message for security context constraint substring; confirm successful pod creates include openshift.io/scc in responseObject when audit level permits; ocp_events must show FailedCreate during intentional SCC mismatch tests in lab.

Governance lookup: publish lookups/openshift_scc_namespace_policy.csv in git with cluster, namespace, expected_scc_tier values such as restricted_v2, nonroot_v2, anyuid_exception, hostnetwork_exception, owner_team, exception_reason, and exception_expiry_epoch. Refresh from the same repository that manages namespace openshift.io annotations so inventory and cluster state share commit ancestry auditors can trace.

Collector hardening: run forwarders with approved TLS cipher suites when required, segregate indexes per data classification, and restrict search peers that can read ocp_audit to roles that completed privileged access training.

### Step 3 — Create the search and alert

Save the SPL as openshift_uc_3_3_4_scc_violations_escalation with a fifteen-minute schedule during steady-state production, dispatch earliest=-24h@h, dispatch latest=now, and alert when severity is critical or high. Throttle duplicate cluster, namespace, signal_lane rows for forty-five minutes unless severity escalates. Include recommended_action, signal_lane, and admitted_scc fields in pager descriptions so incident commanders route to SCC runbooks without re-running ad hoc searches.

Pipeline narrative for reviewers: multisearch fans SCC admission denials, SecurityContextConstraints object mutations, successful pod admissions that extract openshift.io/scc, and OpenShift events citing SCC failures so a silent audit shipper does not hide controller-level errors. coalesce() absorbs flattened versus dotted JSON field naming drift across exporters. eventstats computes denial_count_24h and mutation_count_24h per cluster and namespace. streamstats detects rapid repeat denials from the same service account for brute-force style attempts. join type=left wraps openshift_scc_namespace_policy.csv to label expected_scc_tier versus admitted SCC skew. case() maps privileged-class admissions in restricted namespaces, SCC object broadening mutations, mass group bindings implied by repeated add-scc-to-group patterns, high-volume denials, and event corroboration into critical, high, medium, and info tiers. recommended_action encodes oc describe scc, oc adm policy remove-scc-from-user, review RoleBinding subjects, and must-gather collection steps without pretending Splunk replaces cluster access.

Fenced SPL must match the spl JSON field exactly:

```spl
`comment("UC-3.3.4 OpenShift SCC admission — ocp_audit/k8s_audit/ocp_admission + SCC CRUD + pod openshift.io/scc + ocp_events. Join openshift_scc_namespace_policy.csv. earliest=-24h@h latest=now")`
| multisearch
    [ search (index=ocp_audit OR index=k8s_audit) (sourcetype=ocp_audit OR sourcetype=k8s_audit OR sourcetype=ocp_admission) earliest=-24h@h latest=now
      | eval cluster=lower(trim(toString(coalesce(cluster, openshift_cluster, cluster_name, k8s_cluster_name, ""))))
      | eval resp_code=tonumber(tostring(coalesce('responseStatus.code', responseStatus.code, responseStatus_code, http_status, "0")), 10)
      | eval resp_reason=lower(toString(coalesce('responseStatus.reason', responseStatus.reason, responseStatus_reason, "")))
      | eval resp_msg=lower(toString(coalesce('responseStatus.message', responseStatus.message, responseStatus_message, message, "")))
      | eval obj_res=lower(toString(coalesce('objectRef.resource', objectRef.resource, objectRef_resource, "")))
      | eval verb_tx=lower(toString(coalesce(verb, requestVerb, "")))
      | eval scc_deny=if((resp_code=403 OR match(resp_reason,"forbidden")) AND match(resp_msg, "unable to validate against any security context constraint"), 1, 0)
      | where scc_deny=1 AND match(obj_res,"^pods?$")
      | eval namespace=trim(toString(coalesce('objectRef.namespace', objectRef.namespace, objectRef_namespace, "")))
      | eval workload=trim(toString(coalesce('objectRef.name', objectRef.name, objectRef_name, "")))
      | eval actor=trim(toString(coalesce('user.username', user.username, user_username, "")))
      | rex field=_raw max_match=0 "(?i)\"serviceAccountName\"\\s*:\\s*\"(?<rex_sa>[^\"]+)\""
      | eval service_account=trim(toString(coalesce(rex_sa, "")))
      | eval admitted_scc=""
      | eval scc_object=""
      | eval signal_lane="scc_admission_deny"
      | eval lane_detail=substr(resp_msg,1,240)
      | fields _time cluster namespace workload actor service_account admitted_scc scc_object signal_lane lane_detail resp_code ]
    [ search (index=ocp_audit OR index=k8s_audit) (sourcetype=ocp_audit OR sourcetype=k8s_audit) earliest=-24h@h latest=now
      | eval cluster=lower(trim(toString(coalesce(cluster, openshift_cluster, cluster_name, k8s_cluster_name, ""))))
      | eval obj_res=lower(toString(coalesce('objectRef.resource', objectRef.resource, objectRef_resource, "")))
      | eval obj_grp=lower(toString(coalesce('objectRef.apiGroup', objectRef.apiGroup, objectRef_apigroup, "")))
      | eval verb_tx=lower(toString(coalesce(verb, requestVerb, "")))
      | where match(obj_grp,"security.openshift.io") AND match(obj_res,"securitycontextconstraints") AND match(verb_tx,"create|update|patch|delete")
      | eval namespace="_cluster_"
      | eval workload=trim(toString(coalesce('objectRef.name', objectRef.name, objectRef_name, "")))
      | eval actor=trim(toString(coalesce('user.username', user.username, user_username, "")))
      | eval service_account="n_a"
      | eval admitted_scc=""
      | eval scc_object=workload
      | eval signal_lane="scc_resource_mutation"
      | eval resp_code=tonumber(tostring(coalesce('responseStatus.code', responseStatus.code, responseStatus_code, "0")), 10)
      | eval lane_detail=strcat(verb_tx,"_",workload)
      | fields _time cluster namespace workload actor service_account admitted_scc scc_object signal_lane lane_detail resp_code ]
    [ search (index=ocp_audit OR index=k8s_audit) (sourcetype=ocp_audit OR sourcetype=k8s_audit OR sourcetype=ocp_admission) earliest=-24h@h latest=now
      | eval cluster=lower(trim(toString(coalesce(cluster, openshift_cluster, cluster_name, k8s_cluster_name, ""))))
      | eval resp_code=tonumber(tostring(coalesce('responseStatus.code', responseStatus.code, responseStatus_code, "0")), 10)
      | eval obj_res=lower(toString(coalesce('objectRef.resource', objectRef.resource, objectRef_resource, "")))
      | eval verb_tx=lower(toString(coalesce(verb, requestVerb, "")))
      | where match(verb_tx,"create|update") AND resp_code>=200 AND resp_code<300 AND match(obj_res,"^pods?$")
      | rex field=_raw "(?i)\"openshift\\.io/scc\"\\s*:\\s*\"(?<adm_scc>[^\"]+)\""
      | where len(adm_scc)>1
      | eval namespace=trim(toString(coalesce('objectRef.namespace', objectRef.namespace, objectRef_namespace, "")))
      | eval workload=trim(toString(coalesce('objectRef.name', objectRef.name, objectRef_name, "")))
      | eval actor=trim(toString(coalesce('user.username', user.username, user_username, "")))
      | rex field=_raw max_match=0 "(?i)\"serviceAccountName\"\\s*:\\s*\"(?<rex_sa2>[^\"]+)\""
      | eval service_account=trim(toString(coalesce(rex_sa2, "")))
      | eval admitted_scc=lower(trim(toString(adm_scc)))
      | eval scc_object=""
      | eval signal_lane="scc_pod_admit"
      | eval lane_detail=strcat("admitted_under_",admitted_scc)
      | fields _time cluster namespace workload actor service_account admitted_scc scc_object signal_lane lane_detail resp_code ]
    [ search index=ocp_events sourcetype=ocp_events earliest=-24h@h latest=now
      | eval cluster=lower(trim(toString(coalesce(cluster, openshift_cluster, cluster_name, ""))))
      | eval em=lower(toString(coalesce(message, Message, "")))
      | eval er=lower(toString(coalesce(reason, "")))
      | where (match(er,"failedcreate|forbidden|failed") OR match(em,"unable to validate")) AND match(em,"security context constraint|securitycontextconstraint")
      | eval namespace=trim(toString(coalesce(involvedObject_namespace, namespace, "")))
      | eval workload=trim(toString(coalesce(involvedObject_name, object_name, "")))
      | eval actor="event_controller"
      | eval service_account="n_a"
      | eval admitted_scc=""
      | eval scc_object=""
      | eval signal_lane="scc_event_fail"
      | eval lane_detail=substr(em,1,240)
      | eval resp_code=0
      | fields _time cluster namespace workload actor service_account admitted_scc scc_object signal_lane lane_detail resp_code ]
| eval cluster=coalesce(nullif(cluster,""), "unknown_cluster")
| eval namespace=coalesce(nullif(namespace,""), "unknown_namespace")
| join type=left max=0 cluster namespace [
    | inputlookup openshift_scc_namespace_policy.csv
    | eval cluster=lower(trim(toString(cluster)))
    | eval namespace=trim(toString(namespace))
    | eval expected_scc_tier=lower(trim(toString(coalesce(expected_scc_tier, expected_tier, ""))))
    | eval owner_team_lu=trim(toString(coalesce(owner_team, "")))
    | eval exception_expiry=tonumber(tostring(coalesce(exception_expiry_epoch, "0")),10)
    | fields cluster namespace expected_scc_tier owner_team_lu exception_expiry ]
| fillnull value="" expected_scc_tier owner_team_lu
| eval owner_team=owner_team_lu
| eval privileged_admit=if(signal_lane=="scc_pod_admit" AND match(admitted_scc,"anyuid|privileged|hostnetwork|hostaccess|hostmount|node-exporter|elastic|traces|pipelines"),1,0)
| eval restricted_expect=if(match(expected_scc_tier,"restricted|nonroot|baseline"),1,0)
| eval selection_skew=if(privileged_admit==1 AND restricted_expect==1,1,0)
| eval is_deny=if(signal_lane=="scc_admission_deny",1,0)
| eval is_mut=if(signal_lane=="scc_resource_mutation",1,0)
| eventstats sum(is_deny) AS denial_count_24h sum(is_mut) AS mutation_count_24h BY cluster namespace
| streamstats window=48 current=t global=f sum(is_deny) AS deny_burst BY cluster namespace actor
| eval severity=case(
    signal_lane=="scc_resource_mutation" AND mutation_count_24h>=2, "critical",
    selection_skew==1, "critical",
    signal_lane=="scc_admission_deny" AND deny_burst>=5, "high",
    signal_lane=="scc_admission_deny", "medium",
    signal_lane=="scc_resource_mutation", "high",
    signal_lane=="scc_event_fail", "medium",
    true(), "info")
| eval recommended_action=case(
    severity=="critical" AND signal_lane=="scc_resource_mutation", "oc_get_scc_yaml_diff_and_rollback_unauthorized_change",
    severity=="critical" AND selection_skew==1, "oc_adm_policy_who_can_use_scc_review_bindings_and_remove_escalation",
    severity=="high" AND signal_lane=="scc_admission_deny", "fix_manifest_or_grant_minimal_scc_under_change_control",
    signal_lane=="scc_event_fail", "correlate_events_to_audit_and_restore_audit_shipper",
    signal_lane=="scc_pod_admit", "record_openshift_io_scc_for_config_management",
    true(), "review_scc_namespace_policy_lookup_and_exceptions")
| table _time cluster namespace workload service_account actor signal_lane admitted_scc scc_object lane_detail denial_count_24h mutation_count_24h deny_burst selection_skew owner_team severity recommended_action
```

savedsearches.conf sketch:

```ini
[openshift_uc_3_3_4_scc_violations_escalation_alert]
cron_schedule = */15 * * * *
dispatch.earliest_time = -24h@h
dispatch.latest_time = now
enableSched = 1
action.email = 1
action.email.to = openshift-platform-security@example.com
action.email.subject = OCP SCC $result.severity$ $result.cluster$ $result.namespace$ $result.signal_lane$
counttype = number of events
relation = greater than
quantity = 0
search = | savedsearch openshift_uc_3_3_4_scc_violations_escalation | where severity IN ("critical","high")
```

Performance: if Job Inspector shows multisearch queue time above internal SLA, materialize denial and mutation arms hourly into summary indexes keyed on cluster, namespace, and service_account, widen alert windows to earliest=-6h@h on summaries, and retain this full search for investigations. For Splunk Enterprise Security, use the closing table as a correlation search feeding a notable template with cluster and namespace as assets.

SPL tuning: expand privileged_class match lists when your cluster renames custom SCCs; keep a lookup openshift_scc_tiers.csv mapping scc_name to numeric tier_rank for skew math if case logic grows unwieldy.

### Step 4 — Validate

Ground truth always starts on-cluster. For denied pod creates surfaced in Splunk, run oc describe pod or review the ReplicaSet event in the same namespace and second as the audit timestamp to confirm the denial message matches. For successful admissions, oc get pod -o jsonpath against live pod metadata should match admitted_scc extracted from audit when the pod still exists; if the pod was deleted, rely on audit responseObject only.

SCC object mutations: compare audit user.username for changes to securitycontextconstraints with change tickets. Run oc get scc restricted-v2 -o yaml before and after the window to see allowedCapabilities or volumes drift. Splunk should list verbs and object names without fabricating fields absent from audit.

Synthetic denial test: in a lab namespace whose default ServiceAccount lacks privileged SCC, attempt oc run with a privileged pod spec and confirm audit shows responseStatus.code 403 with unable to validate against any security context constraint, then confirm openshift_uc_3_3_4_scc_violations_escalation returns signal_lane scc_admission_deny with non-zero denial_count_24h.

Synthetic admission test: grant a lab ServiceAccount use of nonroot-v2 only, deploy a compliant pod, capture audit ResponseComplete with openshift.io/scc annotation, and confirm signal_lane scc_pod_admit with admitted_scc matching oc get pod annotation.

Synthetic escalation test: under change control, run oc adm policy add-scc-to-user anyuid -z default -n lab-scc-test and confirm audit shows RoleBinding or ClusterRoleBinding mutations referencing security.openshift.io SCC use permissions; extend the SPL with a dedicated binding arm if your audit policy captures those objects at sufficient depth.

Negative test: remove lab bindings, revert SCC changes, and confirm severities return to info or zero alert rows when the alert wrapper filters to critical and high only.

Correlation test: pair timelines with UC-3.2.22 PSA analytics only on clusters where both SCC and PSA are relevant; on OpenShift 4 modern defaults, PSA may run alongside SCC—read Red Hat guidance for your minor version before merging narratives.

RBAC test: readers without ocp_audit role must see zero rows. Privacy test: requestObject bodies should not land in developer-shared indexes when they disclose secrets; redact at collection.

Clock skew test: indexer time within thirty seconds of apiserver; otherwise streamstats windows mis-order events.

### Step 5 — Operationalize & Troubleshoot

Case 1 — unable to validate against any security context constraint storm from a CI service account: treat as broken manifest or poisoned pipeline template; freeze deployments, compare Git commit history, and open an application security ticket with audit excerpts attached.

Case 2 — sporadic denials during node drain: Machine Config Operator or eviction activity can recreate pods; correlate with node maintenance windows before paging as hostile.

Case 3 — oc adm policy add-scc-to-user anyuid against a production namespace default ServiceAccount without ticket: critical; remove binding, rotate ServiceAccount tokens if policy requires, and review who executed the command via user.username and source IP enrichment.

Case 4 — oc adm policy add-scc-to-group system:authenticated or system:unauthenticated patterns: critical mass-assignment; expect immediate leadership notification, emergency binding removal, and identity provider verification.

Case 5 — SecurityContextConstraints patch widening allowedCapabilities: high; capture before and after YAML from change management, validate whether vendor operator documentation mandated the change, and engage Red Hat support if platform SCCs drifted unexpectedly.

Case 6 — Pod admitted under privileged while openshift_scc_namespace_policy.csv expects restricted_v2: high skew; validate namespace labels, PSA enforce labels if enabled, and review ServiceAccount bindings; attackers may have acquired use of privileged SCC through stolen credentials.

Case 7 — openshift.io/scc shows hostnetwork while workload manifest requests hostNetwork false: investigate stale audit versus live pod; possible admission replay or log duplication; dedupe on audit auditID.

Case 8 — ocp_events FailedCreate with SCC text but no matching audit row: check audit shipper health, HEC token expiration, or alternate apiserver instance without forwarding; restore audit before lowering alert fidelity.

Case 9 — cluster-logging or monitoring operators under vendor-documented SCC classes: use lookup exception_expiry_epoch and owner_team to downgrade noise when Red Hat or partner documentation confirms required SCC.

Case 10 — namespace stuck in Terminating with SCC-related finalizer errors: pair with namespace deletion runbooks; SCC is not always root cause but events may mention security context; verify remaining pods and finalizers.

Case 11 — custom SCC priority inversion after upgrade: oc get scc priorities may change; validate selection algorithm outputs with platform architects; update openshift_scc_namespace_policy.csv tiers after upgrades.

Case 12 — healthy control test: restricted namespace, compliant pods, no mutations, info severities only, alert wrapper silent for critical and high filters; replay quarterly to prove telemetry freshness.

Dashboard publishing: severity-colored table with drilldowns to raw audit JSON, ocp_events text, and lookup rows; timeline of denial_count_24h by namespace; single-value tiles for critical counts.

Evidence retention: weekly CSV exports of the closing table to a restricted evidence index with git commit hashes for openshift_scc_namespace_policy.csv satisfy many internal Kubernetes hardening scorecards when paired with tickets.

Governance: quarterly replay one historical SCC binding change through the SPL after OpenShift minor upgrades; update comment macros when indexes move.

Closing checklist: five em-dash step headers are present; Step 3 fenced SPL matches the spl field exactly; multisearch lists denial, SCC mutation, pod admit, and events arms; coalesce, streamstats, eventstats, and case appear; closing table includes at least ten columns for analyst review.

## SPL

```spl
`comment("UC-3.3.4 OpenShift SCC admission — ocp_audit/k8s_audit/ocp_admission + SCC CRUD + pod openshift.io/scc + ocp_events. Join openshift_scc_namespace_policy.csv. earliest=-24h@h latest=now")`
| multisearch
    [ search (index=ocp_audit OR index=k8s_audit) (sourcetype=ocp_audit OR sourcetype=k8s_audit OR sourcetype=ocp_admission) earliest=-24h@h latest=now
      | eval cluster=lower(trim(toString(coalesce(cluster, openshift_cluster, cluster_name, k8s_cluster_name, ""))))
      | eval resp_code=tonumber(tostring(coalesce('responseStatus.code', responseStatus.code, responseStatus_code, http_status, "0")), 10)
      | eval resp_reason=lower(toString(coalesce('responseStatus.reason', responseStatus.reason, responseStatus_reason, "")))
      | eval resp_msg=lower(toString(coalesce('responseStatus.message', responseStatus.message, responseStatus_message, message, "")))
      | eval obj_res=lower(toString(coalesce('objectRef.resource', objectRef.resource, objectRef_resource, "")))
      | eval verb_tx=lower(toString(coalesce(verb, requestVerb, "")))
      | eval scc_deny=if((resp_code=403 OR match(resp_reason,"forbidden")) AND match(resp_msg, "unable to validate against any security context constraint"), 1, 0)
      | where scc_deny=1 AND match(obj_res,"^pods?$")
      | eval namespace=trim(toString(coalesce('objectRef.namespace', objectRef.namespace, objectRef_namespace, "")))
      | eval workload=trim(toString(coalesce('objectRef.name', objectRef.name, objectRef_name, "")))
      | eval actor=trim(toString(coalesce('user.username', user.username, user_username, "")))
      | rex field=_raw max_match=0 "(?i)\"serviceAccountName\"\\s*:\\s*\"(?<rex_sa>[^\"]+)\""
      | eval service_account=trim(toString(coalesce(rex_sa, "")))
      | eval admitted_scc=""
      | eval scc_object=""
      | eval signal_lane="scc_admission_deny"
      | eval lane_detail=substr(resp_msg,1,240)
      | fields _time cluster namespace workload actor service_account admitted_scc scc_object signal_lane lane_detail resp_code ]
    [ search (index=ocp_audit OR index=k8s_audit) (sourcetype=ocp_audit OR sourcetype=k8s_audit) earliest=-24h@h latest=now
      | eval cluster=lower(trim(toString(coalesce(cluster, openshift_cluster, cluster_name, k8s_cluster_name, ""))))
      | eval obj_res=lower(toString(coalesce('objectRef.resource', objectRef.resource, objectRef_resource, "")))
      | eval obj_grp=lower(toString(coalesce('objectRef.apiGroup', objectRef.apiGroup, objectRef_apigroup, "")))
      | eval verb_tx=lower(toString(coalesce(verb, requestVerb, "")))
      | where match(obj_grp,"security.openshift.io") AND match(obj_res,"securitycontextconstraints") AND match(verb_tx,"create|update|patch|delete")
      | eval namespace="_cluster_"
      | eval workload=trim(toString(coalesce('objectRef.name', objectRef.name, objectRef_name, "")))
      | eval actor=trim(toString(coalesce('user.username', user.username, user_username, "")))
      | eval service_account="n_a"
      | eval admitted_scc=""
      | eval scc_object=workload
      | eval signal_lane="scc_resource_mutation"
      | eval resp_code=tonumber(tostring(coalesce('responseStatus.code', responseStatus.code, responseStatus_code, "0")), 10)
      | eval lane_detail=strcat(verb_tx,"_",workload)
      | fields _time cluster namespace workload actor service_account admitted_scc scc_object signal_lane lane_detail resp_code ]
    [ search (index=ocp_audit OR index=k8s_audit) (sourcetype=ocp_audit OR sourcetype=k8s_audit OR sourcetype=ocp_admission) earliest=-24h@h latest=now
      | eval cluster=lower(trim(toString(coalesce(cluster, openshift_cluster, cluster_name, k8s_cluster_name, ""))))
      | eval resp_code=tonumber(tostring(coalesce('responseStatus.code', responseStatus.code, responseStatus_code, "0")), 10)
      | eval obj_res=lower(toString(coalesce('objectRef.resource', objectRef.resource, objectRef_resource, "")))
      | eval verb_tx=lower(toString(coalesce(verb, requestVerb, "")))
      | where match(verb_tx,"create|update") AND resp_code>=200 AND resp_code<300 AND match(obj_res,"^pods?$")
      | rex field=_raw "(?i)\"openshift\\.io/scc\"\\s*:\\s*\"(?<adm_scc>[^\"]+)\""
      | where len(adm_scc)>1
      | eval namespace=trim(toString(coalesce('objectRef.namespace', objectRef.namespace, objectRef_namespace, "")))
      | eval workload=trim(toString(coalesce('objectRef.name', objectRef.name, objectRef_name, "")))
      | eval actor=trim(toString(coalesce('user.username', user.username, user_username, "")))
      | rex field=_raw max_match=0 "(?i)\"serviceAccountName\"\\s*:\\s*\"(?<rex_sa2>[^\"]+)\""
      | eval service_account=trim(toString(coalesce(rex_sa2, "")))
      | eval admitted_scc=lower(trim(toString(adm_scc)))
      | eval scc_object=""
      | eval signal_lane="scc_pod_admit"
      | eval lane_detail=strcat("admitted_under_",admitted_scc)
      | fields _time cluster namespace workload actor service_account admitted_scc scc_object signal_lane lane_detail resp_code ]
    [ search index=ocp_events sourcetype=ocp_events earliest=-24h@h latest=now
      | eval cluster=lower(trim(toString(coalesce(cluster, openshift_cluster, cluster_name, ""))))
      | eval em=lower(toString(coalesce(message, Message, "")))
      | eval er=lower(toString(coalesce(reason, "")))
      | where (match(er,"failedcreate|forbidden|failed") OR match(em,"unable to validate")) AND match(em,"security context constraint|securitycontextconstraint")
      | eval namespace=trim(toString(coalesce(involvedObject_namespace, namespace, "")))
      | eval workload=trim(toString(coalesce(involvedObject_name, object_name, "")))
      | eval actor="event_controller"
      | eval service_account="n_a"
      | eval admitted_scc=""
      | eval scc_object=""
      | eval signal_lane="scc_event_fail"
      | eval lane_detail=substr(em,1,240)
      | eval resp_code=0
      | fields _time cluster namespace workload actor service_account admitted_scc scc_object signal_lane lane_detail resp_code ]
| eval cluster=coalesce(nullif(cluster,""), "unknown_cluster")
| eval namespace=coalesce(nullif(namespace,""), "unknown_namespace")
| join type=left max=0 cluster namespace [
    | inputlookup openshift_scc_namespace_policy.csv
    | eval cluster=lower(trim(toString(cluster)))
    | eval namespace=trim(toString(namespace))
    | eval expected_scc_tier=lower(trim(toString(coalesce(expected_scc_tier, expected_tier, ""))))
    | eval owner_team_lu=trim(toString(coalesce(owner_team, "")))
    | eval exception_expiry=tonumber(tostring(coalesce(exception_expiry_epoch, "0")),10)
    | fields cluster namespace expected_scc_tier owner_team_lu exception_expiry ]
| fillnull value="" expected_scc_tier owner_team_lu
| eval owner_team=owner_team_lu
| eval privileged_admit=if(signal_lane=="scc_pod_admit" AND match(admitted_scc,"anyuid|privileged|hostnetwork|hostaccess|hostmount|node-exporter|elastic|traces|pipelines"),1,0)
| eval restricted_expect=if(match(expected_scc_tier,"restricted|nonroot|baseline"),1,0)
| eval selection_skew=if(privileged_admit==1 AND restricted_expect==1,1,0)
| eval is_deny=if(signal_lane=="scc_admission_deny",1,0)
| eval is_mut=if(signal_lane=="scc_resource_mutation",1,0)
| eventstats sum(is_deny) AS denial_count_24h sum(is_mut) AS mutation_count_24h BY cluster namespace
| streamstats window=48 current=t global=f sum(is_deny) AS deny_burst BY cluster namespace actor
| eval severity=case(
    signal_lane=="scc_resource_mutation" AND mutation_count_24h>=2, "critical",
    selection_skew==1, "critical",
    signal_lane=="scc_admission_deny" AND deny_burst>=5, "high",
    signal_lane=="scc_admission_deny", "medium",
    signal_lane=="scc_resource_mutation", "high",
    signal_lane=="scc_event_fail", "medium",
    true(), "info")
| eval recommended_action=case(
    severity=="critical" AND signal_lane=="scc_resource_mutation", "oc_get_scc_yaml_diff_and_rollback_unauthorized_change",
    severity=="critical" AND selection_skew==1, "oc_adm_policy_who_can_use_scc_review_bindings_and_remove_escalation",
    severity=="high" AND signal_lane=="scc_admission_deny", "fix_manifest_or_grant_minimal_scc_under_change_control",
    signal_lane=="scc_event_fail", "correlate_events_to_audit_and_restore_audit_shipper",
    signal_lane=="scc_pod_admit", "record_openshift_io_scc_for_config_management",
    true(), "review_scc_namespace_policy_lookup_and_exceptions")
| table _time cluster namespace workload service_account actor signal_lane admitted_scc scc_object lane_detail denial_count_24h mutation_count_24h deny_burst selection_skew owner_team severity recommended_action
```

## CIM SPL

```spl
| tstats summariesonly=true latest(Authentication.user) AS auth_user latest(Authentication.action) AS auth_action FROM datamodel=Authentication WHERE nodename=Authentication earliest=-24h@h latest=now BY Authentication.src
| rename Authentication.src AS cim_src
| join type=left max=0 cim_src
    [| tstats summariesonly=true latest(Change.action) AS chg_action latest(Change.object) AS chg_object latest(Change.user) AS chg_user FROM datamodel=Change WHERE nodename=Change earliest=-24h@h latest=now BY Change.dest
     | rename Change.dest AS cim_src ]
| where like(lower(chg_object), "%security.openshift.io%") OR like(lower(chg_object), "%securitycontextconstraint%")
| table cim_src auth_user auth_action chg_action chg_object chg_user
```

## Visualization

Severity-colored table mirroring the closing SPL projection; timeline of denial_count_24h by namespace; drilldown from signal_lane to raw audit JSON and ocp_events message text; matrix of admitted_scc by cluster for governance reviews.

## Known False Positives

Red Hat core operators for cluster monitoring, cluster logging, and ingress routinely require SCC classes such as node-exporter, privileged, or hostnetwork variants documented for your OpenShift minor; join vendor documentation and openshift_scc_namespace_policy.csv exception_expiry_epoch before paging application teams. Operator Lifecycle Manager and Red Hat-certified partner operators including Prisma Cloud, Falco, or Velero often ship with deliberately broader SCC bindings approved in change records; suppress when change_ticket_id metadata matches. Pod creation races during Machine Config Operator node reboots or eviction storms can emit transient FailedCreate events that mirror SCC denials even when the next reconcile succeeds; require sustained denial_count_24h or pairing with audit 403 rows. Legitimate oc adm policy add-scc-to-user executions during documented migrations look identical to abuse until you join ITSM tickets and approved maintenance windows. Audit RequestResponse volume spikes during upgrades can drop openshift.io/scc extraction if collectors sample; verify shipper health before declaring skew. Custom SCC names differ per cluster; tune privileged_admit match lists so internal aliases do not false-negative. Namespaces without lookup rows leave expected_scc_tier empty and suppress selection_skew; default behavior should remain informational rather than critical. Duplicate HEC submissions from redundant forwarders can inflate deny_burst; dedupe on audit auditID when present. Some managed OpenShift offerings redact portions of audit bodies; rex may miss openshift.io/scc while oc get pod still shows the annotation—investigate parser gaps before muting admissions. Developer sandboxes that intentionally test anyuid will page unless dev namespaces carry lookup tiers and lowered severities.

## References

- [OpenShift Documentation — Managing security context constraints](https://docs.openshift.com/container-platform/latest/authentication/managing-security-context-constraints.html)
- [OpenShift REST API Reference — SecurityContextConstraints](https://docs.openshift.com/container-platform/latest/rest_api/security_apis/securitycontextconstraints-security-openshift-io-v1.html)
- [OpenShift Documentation — Viewing audit logs](https://docs.openshift.com/container-platform/latest/security/audit-log-view.html)
- [OpenShift Documentation — Using RBAC](https://docs.openshift.com/container-platform/latest/authentication/using-rbac.html)
- [Kubernetes Documentation — Pod Security Admission](https://kubernetes.io/docs/concepts/security/pod-security-admission/)
- [Kubernetes Documentation — Pod Security Standards](https://kubernetes.io/docs/concepts/security/pod-security-standards/)
- [Red Hat Blog — Understanding service accounts and SCCs](https://www.redhat.com/en/blog/understanding-service-accounts-sccs)
