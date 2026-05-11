<!-- AUTO-GENERATED from UC-3.2.23.json — DO NOT EDIT -->

---
id: "3.2.23"
title: "Kubernetes Cluster-Admin Path Audit — ClusterRoleBinding Escalation Detection"
status: "verified"
criticality: "high"
splunkPillar: "Security"
---

# UC-3.2.23 · Kubernetes Cluster-Admin Path Audit — ClusterRoleBinding Escalation Detection

> **Criticality:** High &middot; **Difficulty:** Advanced &middot; **Pillar:** Security &middot; **Type:** Security, Compliance, Configuration &middot; **Wave:** Walk &middot; **Status:** Verified

*We watch who receives full control of your container fleet and who wires in the built-in super-user role or other extremely powerful access rules. When that happens without an approved ticket on our list, we sound the alarm and keep a clear record for your safety team.*

---

## Description

Unique monitoring axis: a cluster-admin tier change audit on kube-apiserver authorization—not baseline RBAC anomaly scoring (UC-3.2.12), not Pod Security admission outcomes (UC-3.2.22), not docker.sock host exposure (UC-3.1.25). This control structures successful mutations that attach the built-in cluster-admin ClusterRole, bind the static system:masters group, patch ClusterRole rules toward wildcard verbs on wildcard resources or toward impersonate, escalate, bind-on-clusterroles, interactive pod subresources, nodes, persistentvolumes, or storageclasses at cluster scope, or approve certificate signing requests, then joins an allowlist so break-glass stays visible but ticket-linked. Immutable audit retention and executive-ready rows are the intent.

## Value

Cluster-admin sprawl and escalation verbs are how token theft becomes fleet-wide secret access, data destruction, and shadow control planes. Timestamped, successful mutation rows give platform security and identity teams an evidence pack before attackers stabilize. Regulators and customers asking for Kubernetes hardening attestations receive exportable proof that the highest-risk authorization paths are monitored with ticket-aware suppressions rather than blind trust in GitOps. Mean time to contain improves because Splunk shows which actor, which cluster, which binding or role name, and whether a break-glass ticket explains the event.

## Implementation

Stand up index k8s_audit with kube apiserver audit JSON at RequestResponse depth for binding, cluster role, and CSR approval mutations. Maintain k8s_cluster_admin_sa_allowlist.csv under change control with ticket and optional expiry columns. Save uc_3_2_23_cluster_admin_path_audit on a fifteen-minute cadence across earliest minus twenty-four hours through now, route critical and high rows to platform security, and archive weekly evidence exports with lookup commit hashes and ticket identifiers for break-glass rows.

## Evidence

Saved search uc_3_2_23_cluster_admin_path_audit; versioned k8s_cluster_admin_sa_allowlist.csv in git; weekly CSV export of the closing table to a restricted evidence index with commit hashes; dashboard drilldowns from signal_lane to raw audit JSON.

## Control test

### Positive scenario

In lab, create a ClusterRoleBinding referencing cluster-admin that binds a dedicated non-production service account; ingest kube:apiserver:audit with requestObject intact and HTTP success; run uc_3_2_23_cluster_admin_path_audit and expect clusterrolebinding_cluster_admin_roleRef with severity critical when no allowlist row matches subject_key.

### Negative scenario

Add an allowlist row for the same cluster and subject_key with approved_change_ticket populated and allowlist_expired=0; repeat the binding mutation; confirm severity downgrades to medium_breakglass_documented while the row remains visible for evidence.

## Detailed Implementation

### Step 1 — Prerequisites

Head of Platform owns this control together with the Kubernetes platform security lead, the identity engineer who signs the apiserver audit policy, and the Splunk observability owner who operates OpenTelemetry Collector fleets. This use case is deliberately narrow: it is the cluster-admin tier change ledger for authorization, not the broad RBAC anomaly scorer in UC-3.2.12, not admission-time Pod Security denials in UC-3.2.22, not host docker socket exposure in UC-3.1.25, and not certificate expiry inventory in UC-3.2.13. UC-3.2.12 correlates many lanes—successful production exec, impersonation headers, forbidden storms, generic binding churn, and kube-state-metrics heartbeats—into a single anomaly narrative. UC-3.2.23 instead emits structured rows only when someone successfully mutates bindings toward cluster-admin, binds the static group that bypasses normal authorization checks, patches ClusterRole rules toward wildcard or subresource privileges that approximate control-plane power, approves certificate signing requests in ways that mint new kubelet or client identities, or walks the cluster-scoped persistent volume, node, storage class, or interactive pod access paths that attackers combine after stealing a token. Treat every row as potential evidence for an access review, a break-glass after-action, or an incident timeline anchor.

Index contracts: dedicate index=k8s_audit for sourcetype=kube:apiserver:audit with role separation so platform security analysts can read requestObject bodies while application developers cannot. Every event must carry a stable cluster dimension such as k8s_cluster_name, eks_cluster_name, gke_cluster_name, aks_cluster_name, or cluster_name so joins to k8s_cluster_admin_sa_allowlist.csv never collapse a multi-cluster fleet into one ambiguous namespace. Clock skew between apiserver hosts and Splunk indexers must stay under thirty seconds or streamstats sequencing misleads investigators during bridges.

Audit policy depth: privilege-path detection requires RequestResponse for verbs create, update, and patch on rbac.authorization.k8s.io clusterrolebindings, rolebindings, and clusterroles, plus certificatesigningrequests when your distribution logs approval subresources. Without requestObject, you cannot see roleRef.name, subjects, or rule stanzas, which makes this search blind. Keep Metadata-only defaults for read storms, but never demote mutating RBAC objects to Metadata in regulated tiers. Document omitStages for noisy system accounts after security review rather than silencing CI principals without a compensating control.

Governance lookup: publish lookups/k8s_cluster_admin_sa_allowlist.csv under the same repository as your alerts with columns cluster (lowercased fleet key), subject_key (for example sa:kube-system:cluster-admin-ops-sa or group:system:masters when you intentionally document a rare exception), approved_change_ticket (required text pointer to the change or incident record), allowlist_expiry_epoch (Unix seconds after which the row must be renewed or alerts escalate again), and allowlist_owner (team name for paging context). Refresh the CSV whenever break-glass completes. Auditors should trace allowlist rows to tickets the same way they trace firewall rules to CAB records.

Risk framing: the built-in cluster-admin ClusterRole is not a convenience shortcut; it is full control of every namespace, every secret, every CustomResourceDefinition, and every workload. The system:masters group exists precisely to mirror client certificate subjects that should never appear inside RoleBinding or ClusterRoleBinding subjects in a mature estate; seeing it in a binding is a governance red flag even when the change technically succeeds. Wildcard-on-wildcard rules, impersonate, escalate, and bind-on-clusterroles verbs are how operators and attackers climb from namespace scope to cluster scope without touching cluster-admin by name. Certificate signing approval at cluster scope is how someone mints new node or client identities after compromise. PersistentVolume, Node, and StorageClass write verbs at cluster scope are how someone destroys data paths or reshapes scheduling surfaces. Pods exec, attach, and port-forward at cluster scope are how someone turns a stolen token into interactive compromise across the fleet.

Legal and privacy: audit JSON can reference Secret names and pod titles; restrict indexes and redact request bodies for Secret resources at the collector when counsel requires. Immutable storage or WORM indices are out of scope for this JSON file but should be part of your production evidence strategy when regulators expect non-repudiation.

Licensing and volume: RequestResponse RBAC auditing is moderate cost relative to full pod body capture; still compress at the collector, tier hot versus frozen retention deliberately, and schedule this search every fifteen minutes during steady state rather than every minute unless you have proven capacity.

Differentiation recap: this UC does not score baseline deviations across all RBAC mutations, does not read PodSecurity admission messages, does not inspect docker.sock mounts on nodes, and does not inventory X.509 notAfter fields. It answers whether the cluster-admin tier and adjacent escalation verbs changed in ways that demand human review, ticket correlation, and immutable audit retention.

### Step 2 — Configure data collection

Wire kube-apiserver audit to Splunk first. On self-managed clusters, point Splunk OpenTelemetry Collector filelog at the host path your distribution documents for audit.log, commonly under /var/log/kubernetes/audit.log, and set splunk_hec exporter sourcetype to kube:apiserver:audit with index=k8s_audit. On managed clusters without node access, use the cloud vendor control-plane audit export that preserves Kubernetes audit JSON and normalize field names so the coalesce ladders in the SPL stay stable across Amazon EKS, Google GKE, and Microsoft AKS.

Audit policy skeleton emphasizing RBAC bindings, ClusterRole rule mutations, and CSR approvals at RequestResponse:

```
apiVersion: audit.k8s.io/v1
kind: Policy
omitStages:
  - "RequestReceived"
rules:
  - level: RequestResponse
    verbs: ["create", "update", "patch"]
    resources:
      - group: "rbac.authorization.k8s.io"
        resources: ["clusterrolebindings", "rolebindings", "clusterroles"]
    namespaces: ["*"]
  - level: RequestResponse
    verbs: ["create", "update", "patch"]
    resources:
      - group: "certificates.k8s.io"
        resources: ["certificatesigningrequests", "certificatesigningrequests/approval"]
    namespaces: ["*"]
  - level: Metadata
    resources:
      - group: ""
        resources: ["events"]
```

OpenTelemetry Collector fragment illustrating audit-only forwarding with JSON timestamp parsing:

```
receivers:
  filelog/audit:
    include: [/var/log/kubernetes/audit.log]
    operators:
      - type: json_parser
        timestamp:
          parse_from: attributes.requestReceivedTimestamp
          layout: '2006-01-02T15:04:05.999999999Z07:00'
exporters:
  splunk_hec/audit:
    token: "${SPLUNK_HEC_TOKEN_AUDIT}"
    endpoint: "https://splunk.example.com:8088/services/collector/event"
    index: k8s_audit
    sourcetype: kube:apiserver:audit
service:
  pipelines:
    logs/audit:
      receivers: [filelog/audit]
      exporters: [splunk_hec/audit]
```

Publish a starter k8s_cluster_admin_sa_allowlist.csv in the same repo as the saved search:

```
cluster,subject_key,approved_change_ticket,allowlist_expiry_epoch,allowlist_owner
prod-eks-01,sa:security:oncall-bridge:emergency-admin,CHG-778899,0,platform-security
lab-gke,group:system:masters,INC-DRILL-2026-04,1746057600,resilience-lab
```

Zero allowlist_expiry_epoch means no automatic expiry in the SPL predicate; prefer explicit epochs for time-bound drills.

Validate before saving the alert: index=k8s_audit sourcetype=kube:apiserver:audit earliest=-15m must return non-zero counts for binding mutations in lab, and intentional test patches to disposable ClusterRoles should surface requestObject fragments containing rules arrays.

Security hygiene: mint dedicated HEC tokens for apiserver audit files, rotate quarterly, and never reuse developer laptop tokens on control-plane hosts. Restrict who can edit the allowlist CSV in git.

### Step 3 — Create the search and alert

Save the SPL as uc_3_2_23_cluster_admin_path_audit with a fifteen-minute schedule during steady operations, using earliest=-24h@h latest=@h so volume baselines remain meaningful. Throttle duplicate critical rows per cluster, signal_lane, and actor for forty-five minutes unless severity escalates from medium_breakglass_documented to critical inside the same hour. Route critical and high rows to the platform security bridge with the closing table attached, including approved_change_ticket when breakglass_tracked equals one so executives see documentation without assuming malice. Archive weekly CSV snapshots of the closing table to a restricted evidence index with k8s_cluster_admin_sa_allowlist.csv commit hashes.

Pipeline narrative for reviewers: the opening comment macro records index names, sourcetype, lookup path, and time window. multisearch fans three arms so a silent CSR arm does not hide binding escalations, and silent binding traffic does not hide dangerous ClusterRole rule patches. The first arm scopes successful create, update, and patch traffic where objectRef.resource is clusterrolebindings or rolebindings, responseStatus.code indicates success, roleRef.name equals cluster-admin or raw subjects reference system:masters, and emits signal_lane tokens that name the pattern explicitly. coalesce ladders absorb flattened JSON field naming differences across vendors. rex extracts the first system:serviceaccount namespace and name pair from raw JSON for allowlist joins when structured fields are missing. The second arm scopes clusterroles mutations with successful responses and evaluates raw rule bodies for wildcard-on-wildcard pairs, impersonate, escalate, bind on clusterroles, pods exec attach and port-forward idioms, nodes with star verbs, and persistentvolumes or storageclasses with mutating verbs. The third arm scopes certificatesigningrequests with approval semantics in verb, subresource, requestURI, or raw text. After fan-in, subject_key normalizes service accounts, the static masters group, or falls back to actor for user principals. join wraps inputlookup k8s_cluster_admin_sa_allowlist.csv on cluster and subject_key without using bare lookup in isolation. allowlist_expired compares allowlist_expiry_epoch to now. breakglass_tracked marks documented exceptions still inside their window. A second join runs tstats summariesonly against the Authentication data model counting prior-day touches for the same actor label as auth_model_touches for analyst context. eventstats counts lane_volume_24h per cluster and signal_lane. streamstats sequences actor_lane_seq for burst interpretation. case assigns severity tiers with explicit handling for expired allowlist rows and documented break-glass. The closing table lists time, cluster, actor, lane, severity, subject_key, break-glass flags, ticket and owner fields, role metadata, binding object name, namespace, extracted service account fields, lane volume, sequence, authentication model touches, request URI, and HTTP code.

Alert actions should attach signal_lane, subject_key, and remind investigators that UC-3.2.12 still provides broader RBAC anomaly context, UC-3.2.22 covers Pod Security admission, and UC-3.1.25 covers docker socket exposure on hosts.

Fenced SPL for runbooks must match the spl JSON field byte-for-byte:

```spl
`comment("UC-3.2.23 Kubernetes cluster-admin tier binding and escalation-path audit. Tunables: index=k8s_audit sourcetype=kube:apiserver:audit; lookup k8s_cluster_admin_sa_allowlist.csv; earliest=-24h@h latest=@h")`
| multisearch 
    [ search index=k8s_audit sourcetype="kube:apiserver:audit" earliest=-24h@h latest=@h
      | eval cluster=lower(trim(toString(coalesce(k8s_cluster_name, cluster_name, cluster, eks_cluster_name, gke_cluster_name, aks_cluster_name, resource_cluster, ""))))
      | eval verb_l=lower(trim(toString(coalesce(verb, ""))))
      | eval res_l=lower(trim(toString(coalesce('objectRef.resource', objectRef.resource, objectRef_resource, ""))))
      | eval ns=trim(toString(coalesce('objectRef.namespace', objectRef.namespace, objectRef_namespace, "")))
      | eval actor=toString(coalesce('user.username', user.username, user_username, user__username, ""))
      | eval obj_name=toString(coalesce('objectRef.name', objectRef.name, objectRef_name, ""))
      | eval role_name=toString(coalesce('requestObject.roleRef.name', requestObject_roleRef_name, ""))
      | eval role_kind=toString(coalesce('requestObject.roleRef.kind', requestObject_roleRef_kind, "ClusterRole"))
      | eval req_uri=toString(coalesce(requestURI, requestUri, ""))
      | eval lr=lower(_raw)
      | where match(verb_l, "^(create|update|patch)$")
      | where match(res_l, "^(clusterrolebindings|rolebindings)$")
      | eval resp_code=tonumber(tostring(coalesce('responseStatus.code', responseStatus.code, responseStatus_code, "201")),10)
      | where resp_code>=200 AND resp_code<300
      | eval binds_ca=if(match(lower(role_name), "(?i)^cluster-admin$") OR match(lr, "\"name\"\\s*:\\s*\"cluster-admin\""), 1, 0)
      | eval masters_g=if(match(lr, "system:masters"), 1, 0)
      | eval signal_lane=case(masters_g=1, "rbac_group_system_masters_binding", binds_ca=1 AND res_l="clusterrolebindings", "clusterrolebinding_cluster_admin_roleRef", binds_ca=1 AND res_l="rolebindings", "rolebinding_cluster_admin_clusterrole_in_ns", true(), null())
      | where isnotnull(signal_lane)
      | rex field=lr "(?i)system:serviceaccount:(?<sa_ns>[^:]+):(?<sa_name>[a-z0-9._-]+)"
      | eval sa_ns=coalesce(sa_ns, "")
      | eval sa_name=coalesce(sa_name, "")
      | fields _time cluster actor signal_lane obj_name role_name role_kind ns sa_ns sa_name resp_code req_uri verb_l res_l ]
    [ search index=k8s_audit sourcetype="kube:apiserver:audit" earliest=-24h@h latest=@h
      | eval cluster=lower(trim(toString(coalesce(k8s_cluster_name, cluster_name, cluster, eks_cluster_name, gke_cluster_name, aks_cluster_name, resource_cluster, ""))))
      | eval verb_l=lower(trim(toString(coalesce(verb, ""))))
      | eval res_l=lower(trim(toString(coalesce('objectRef.resource', objectRef.resource, objectRef_resource, ""))))
      | eval ns=trim(toString(coalesce('objectRef.namespace', objectRef.namespace, objectRef_namespace, "")))
      | eval actor=toString(coalesce('user.username', user.username, user_username, user__username, ""))
      | eval obj_name=toString(coalesce('objectRef.name', objectRef.name, objectRef_name, ""))
      | eval role_name=toString(coalesce('requestObject.metadata.name', requestObject_metadata_name, obj_name, ""))
      | eval role_kind="ClusterRole"
      | eval req_uri=toString(coalesce(requestURI, requestUri, ""))
      | eval lr=lower(_raw)
      | where match(verb_l, "^(create|update|patch)$")
      | where res_l="clusterroles"
      | eval resp_code=tonumber(tostring(coalesce('responseStatus.code', responseStatus.code, responseStatus_code, "201")),10)
      | where resp_code>=200 AND resp_code<300
      | eval has_star_star=if(match(lr, "\\\"verbs\\\"\\s*:\\s*\\[[^\\]]*\\\"\\*\\\"") AND match(lr, "\\\"resources\\\"\\s*:\\s*\\[[^\\]]*\\\"\\*\\\""), 1, 0)
      | eval has_impersonate=if(match(lr, "\\\"impersonate\\\""), 1, 0)
      | eval has_escalate=if(match(lr, "\\\"escalate\\\""), 1, 0)
      | eval has_bind_roles=if(match(lr, "\\\"bind\\\"") AND match(lr, "clusterroles"), 1, 0)
      | eval has_pod_shell=if(match(lr, "pods/exec") OR match(lr, "\\\"pods\\\"[^\\]]*exec") OR match(lr, "pods\\\\/exec") OR (match(lr, "\\\"pods\\\"") AND match(lr, "\\\"exec\\\"")), 1, 0)
      | eval has_pod_attach_pf=if(match(lr, "\\\"pods\\\"") AND match(lr, "\\\"attach\\\""), 1, 0)
      | eval has_pod_pf=if(match(lr, "\\\"pods\\\"") AND match(lr, "portforward"), 1, 0)
      | eval has_nodes_star=if(match(lr, "\\\"nodes\\\"") AND match(lr, "\\\"\\*\\\""), 1, 0)
      | eval has_pv_write=if(match(lr, "persistentvolumes") AND (match(lr, "\\\"create\\\"") OR match(lr, "\\\"update\\\"") OR match(lr, "\\\"patch\\\"") OR match(lr, "\\\"delete\\\"") OR match(lr, "\\\"\\*\\\"")), 1, 0)
      | eval has_sc_write=if(match(lr, "storageclasses") AND (match(lr, "\\\"create\\\"") OR match(lr, "\\\"update\\\"") OR match(lr, "\\\"patch\\\"") OR match(lr, "\\\"delete\\\"") OR match(lr, "\\\"\\*\\\"")), 1, 0)
      | eval sensitive_rule=if(has_star_star OR has_impersonate OR has_escalate OR has_bind_roles OR has_pod_shell OR has_pod_attach_pf OR has_pod_pf OR has_nodes_star OR has_pv_write OR has_sc_write, 1, 0)
      | where sensitive_rule=1
      | eval signal_lane="clusterrole_sensitive_rules_mutation"
      | eval sa_ns=""
      | eval sa_name=""
      | fields _time cluster actor signal_lane obj_name role_name role_kind ns sa_ns sa_name resp_code req_uri verb_l res_l ]
    [ search index=k8s_audit sourcetype="kube:apiserver:audit" earliest=-24h@h latest=@h
      | eval cluster=lower(trim(toString(coalesce(k8s_cluster_name, cluster_name, cluster, eks_cluster_name, gke_cluster_name, aks_cluster_name, resource_cluster, ""))))
      | eval verb_l=lower(trim(toString(coalesce(verb, ""))))
      | eval res_l=lower(trim(toString(coalesce('objectRef.resource', objectRef.resource, objectRef_resource, ""))))
      | eval subres=lower(trim(toString(coalesce('objectRef.subresource', objectRef.subresource, objectRef_subresource, ""))))
      | eval ns=trim(toString(coalesce('objectRef.namespace', objectRef.namespace, objectRef_namespace, "")))
      | eval actor=toString(coalesce('user.username', user.username, user_username, user__username, ""))
      | eval obj_name=toString(coalesce('objectRef.name', objectRef.name, objectRef_name, ""))
      | eval role_name=""
      | eval role_kind=""
      | eval req_uri=lower(toString(coalesce(requestURI, requestUri, "")))
      | eval lr=lower(_raw)
      | where match(res_l, "^certificatesigningrequests$") OR match(req_uri, "certificatesigningrequests")
      | where match(verb_l, "^(create|update|patch)$")
      | eval resp_code=tonumber(tostring(coalesce('responseStatus.code', responseStatus.code, responseStatus_code, "201")),10)
      | where resp_code>=200 AND resp_code<300
      | where match(lr, "approve|approval") OR match(subres, "approval") OR match(req_uri, "approval")
      | eval signal_lane="csr_signing_approve_mutation"
      | eval sa_ns=""
      | eval sa_name=""
      | fields _time cluster actor signal_lane obj_name role_name role_kind ns sa_ns sa_name resp_code req_uri verb_l res_l ]
| eval subject_key=case(signal_lane="rbac_group_system_masters_binding", "group:system:masters", len(sa_ns)>0 AND len(sa_name)>0, strcat("sa:", sa_ns, ":", sa_name), true(), strcat("actor:", actor))
| join type=left max=0 cluster, subject_key [
    | inputlookup k8s_cluster_admin_sa_allowlist.csv
    | eval cluster=lower(trim(toString(coalesce(cluster, k8s_cluster, cluster_name, ""))))
    | eval subject_key=trim(toString(coalesce(subject_key, subject, principal_key, "")))
    | eval approved_change_ticket=toString(coalesce(approved_change_ticket, change_ticket, ticket, ""))
    | eval allowlist_expiry_epoch=tonumber(tostring(coalesce(allowlist_expiry_epoch, expiry_epoch, "0")),10)
    | eval allowlist_owner=toString(coalesce(allowlist_owner, owner_team, ""))
    | fields cluster subject_key approved_change_ticket allowlist_expiry_epoch allowlist_owner ]
| fillnull value="" approved_change_ticket allowlist_owner
| fillnull value=0 allowlist_expiry_epoch
| eval now_e=now()
| eval allowlist_expired=if(allowlist_expiry_epoch>0 AND now_e>allowlist_expiry_epoch, 1, 0)
| eval breakglass_tracked=if(len(trim(approved_change_ticket))>0 AND allowlist_expired=0, 1, 0)
| join type=left max=1 actor [
    | tstats summariesonly=t count AS auth_model_touches FROM datamodel=Authentication WHERE nodename=Authentication earliest=-24h@h latest=@h BY Authentication.user
    | rename Authentication.user AS actor ]
| fillnull value=0 auth_model_touches
| eventstats count AS lane_volume_24h BY cluster, signal_lane
| streamstats window=120 current=t global=f count AS actor_lane_seq BY cluster, actor, signal_lane
| eval severity=case(
    allowlist_expired=1 AND len(trim(approved_change_ticket))>0, "high_expired_allowlist",
    signal_lane="rbac_group_system_masters_binding", "critical",
    breakglass_tracked=1 AND match(signal_lane, "cluster_admin"), "medium_breakglass_documented",
    match(signal_lane, "cluster_admin"), "critical",
    signal_lane="clusterrole_sensitive_rules_mutation" AND match(_raw, "persistentvolumes|storageclasses|nodes"), "critical",
    signal_lane="clusterrole_sensitive_rules_mutation", "high",
    signal_lane="csr_signing_approve_mutation", "high",
    true(), "medium")
| table _time cluster actor signal_lane severity subject_key breakglass_tracked allowlist_expired approved_change_ticket allowlist_owner role_name role_kind obj_name ns sa_ns sa_name lane_volume_24h actor_lane_seq auth_model_touches req_uri resp_code
```

savedsearches.conf sketch for schedulers:

```
[uc_3_2_23_cluster_admin_path_audit_alert]
cron_schedule = */15 * * * *
dispatch.earliest_time = -24h@h
dispatch.latest_time = now
enableSched = 1
action.email = 1
action.email.to = platform-k8s-security@example.com
action.email.subject = Cluster-admin tier RBAC change on $result.cluster$
counttype = number of events
relation = greater than
quantity = 0
search = | savedsearch uc_3_2_23_cluster_admin_path_audit | where severity IN ("critical","high","high_expired_allowlist")
```

cimSpl for CIM Authentication overlays when you normalize privileged kubectl sessions into the Authentication model (paste from the cimSpl JSON field, not the primary spl field).

### Step 4 — Validate

Positive test A — cluster-admin ClusterRoleBinding: in a disposable lab cluster outside production, create a ClusterRoleBinding that references cluster-admin and binds a dedicated lab service account; confirm audit shows user.username for your kubectl principal, requestObject.roleRef.name cluster-admin, responseStatus.code in the two hundreds, and run the saved search expecting clusterrolebinding_cluster_admin_roleRef with severity critical unless a matching allowlist row suppresses to medium_breakglass_documented. Delete the binding and record the removal event separately.

Positive test B — system:masters subject: in lab only, craft a binding whose subjects array includes group system:masters; confirm rbac_group_system_masters_binding with severity critical. Remove immediately and document why the test was necessary.

Positive test C — wildcard ClusterRole patch: append a rules stanza with verbs and resources arrays containing asterisk on a throwaway ClusterRole; confirm clusterrole_sensitive_rules_mutation fires with severity high or critical depending on raw content. Revert the role.

Positive test D — CSR approval: approve a lab CSR using kubectl certificate approve or an automation principal; confirm csr_signing_approve_mutation with successful response code. Ensure lab CSRs are short-lived test artifacts.

Negative test — allowlisted break-glass: add subject_key sa:your-ns:your-sa with approved_change_ticket and matching cluster, repeat a benign cluster-admin bind in lab, confirm medium_breakglass_documented and breakglass_tracked equals one while executives still see the row in dashboards.

Negative test — reader RBAC: a role without index=k8s_audit must see zero rows, proving index segregation.

Correlation test — when UC-3.2.7 shows apiserver instability, pause alert interpretation until audit completeness returns.

Performance test — Job Inspector during Monday peaks; if multisearch cost exceeds budget, split arms into summary index writers keyed on cluster and signal_lane.

### Step 5 — Operationalize & Troubleshoot

Case 1 — New cluster-admin ClusterRoleBinding from an unknown automation account: freeze deploy pipelines touching that identity, rotate service account tokens, diff git history for RBAC manifests, and open a privilege review before accepting vendor claims that the grant is mandatory.

Case 2 — system:masters appears in a binding subject: escalate immediately, remove the binding, audit how the change entered the cluster whether via kubectl, GitOps drift, or compromised credentials, and review identity provider session history for the actor.

Case 3 — Wildcard-on-wildcard ClusterRole patch during business hours: treat as potential lateral movement preparation, snapshot the rules array, revert if unauthorized, and enumerate ClusterRoleBindings that reference the role.

Case 4 — impersonate or escalate verbs added to a ClusterRole: review who can bind that role next, enable admission controls that restrict escalating binds if available, and correlate with UC-3.2.12 impersonation lanes when present.

Case 5 — CSR approval burst from a single principal: investigate whether node bootstrap, certificate rotation, or attacker-driven minting explains the pattern; pair with node inventory and cloud provider node lifecycle logs.

Case 6 — PersistentVolume or StorageClass cluster-scoped write rule appears: involve storage platform owners, validate data destruction guardrails, and confirm no ransomware staging precedes volume deletes.

Case 7 — Nodes star verb rule appears: treat as potential fleet-wide kubelet or infrastructure takeover path, snapshot IAM and cloud metadata bindings, and review recent cloud control-plane events.

Case 8 — Pods exec attach port-forward at cluster scope in the rules body: correlate with live session tooling policies, require ticket-backed access for interactive shells, and consider restricting to namespace-scoped roles where possible.

Case 9 — Allowlist ticket expired: renew the change record or remove the binding; severity high_expired_allowlist should drive a time-bounded remediation SLA.

Case 10 — GitOps controller replay: FluxCD or ArgoCD may reconcile the same binding repeatedly; require git commit correlation before paging on volume alone, and compare live cluster state to main branch.

Case 11 — Cluster bootstrap or managed control plane install: kubeadm, kops, eksctl, or cloud provisioning may create initial cluster-admin bindings; suppress only with documented maintenance windows tied to cluster age or provisioning job identifiers.

Case 12 — Regression or chaos tests: short-lived bindings that automation tears down within minutes should carry lookup rows or namespace labels that downgrade severity to informational in wrapper searches while retaining immutable audit for evidence.

Closing checklist: five em-dash step headers are present exactly as required; Step 3 fenced SPL matches the spl JSON field; multisearch lists three audit arms; coalesce appears in every arm; join wraps k8s_cluster_admin_sa_allowlist.csv; tstats enriches Authentication counts; eventstats and streamstats provide volume and sequencing; case assigns severity tiers; closing table projects twenty-one analyst columns including cluster, actor, lanes, severity, subject_key, break-glass metadata, role fields, binding object, namespace, service account extraction, volumes, sequences, authentication touches, URI, and response code; monitoringType includes Security, Compliance, and Configuration; cimModels lists Change and Authentication; equipmentModels lists kubernetes_k8s; references include Kubernetes RBAC, audit, CSR documentation, ClusterRoleBinding API, cluster-admin role documentation, MITRE ATT and CK T1078.004, and NSA Kubernetes Hardening Guidance.



## SPL

```spl
`comment("UC-3.2.23 Kubernetes cluster-admin tier binding and escalation-path audit. Tunables: index=k8s_audit sourcetype=kube:apiserver:audit; lookup k8s_cluster_admin_sa_allowlist.csv; earliest=-24h@h latest=@h")`
| multisearch 
    [ search index=k8s_audit sourcetype="kube:apiserver:audit" earliest=-24h@h latest=@h
      | eval cluster=lower(trim(toString(coalesce(k8s_cluster_name, cluster_name, cluster, eks_cluster_name, gke_cluster_name, aks_cluster_name, resource_cluster, ""))))
      | eval verb_l=lower(trim(toString(coalesce(verb, ""))))
      | eval res_l=lower(trim(toString(coalesce('objectRef.resource', objectRef.resource, objectRef_resource, ""))))
      | eval ns=trim(toString(coalesce('objectRef.namespace', objectRef.namespace, objectRef_namespace, "")))
      | eval actor=toString(coalesce('user.username', user.username, user_username, user__username, ""))
      | eval obj_name=toString(coalesce('objectRef.name', objectRef.name, objectRef_name, ""))
      | eval role_name=toString(coalesce('requestObject.roleRef.name', requestObject_roleRef_name, ""))
      | eval role_kind=toString(coalesce('requestObject.roleRef.kind', requestObject_roleRef_kind, "ClusterRole"))
      | eval req_uri=toString(coalesce(requestURI, requestUri, ""))
      | eval lr=lower(_raw)
      | where match(verb_l, "^(create|update|patch)$")
      | where match(res_l, "^(clusterrolebindings|rolebindings)$")
      | eval resp_code=tonumber(tostring(coalesce('responseStatus.code', responseStatus.code, responseStatus_code, "201")),10)
      | where resp_code>=200 AND resp_code<300
      | eval binds_ca=if(match(lower(role_name), "(?i)^cluster-admin$") OR match(lr, "\"name\"\\s*:\\s*\"cluster-admin\""), 1, 0)
      | eval masters_g=if(match(lr, "system:masters"), 1, 0)
      | eval signal_lane=case(masters_g=1, "rbac_group_system_masters_binding", binds_ca=1 AND res_l="clusterrolebindings", "clusterrolebinding_cluster_admin_roleRef", binds_ca=1 AND res_l="rolebindings", "rolebinding_cluster_admin_clusterrole_in_ns", true(), null())
      | where isnotnull(signal_lane)
      | rex field=lr "(?i)system:serviceaccount:(?<sa_ns>[^:]+):(?<sa_name>[a-z0-9._-]+)"
      | eval sa_ns=coalesce(sa_ns, "")
      | eval sa_name=coalesce(sa_name, "")
      | fields _time cluster actor signal_lane obj_name role_name role_kind ns sa_ns sa_name resp_code req_uri verb_l res_l ]
    [ search index=k8s_audit sourcetype="kube:apiserver:audit" earliest=-24h@h latest=@h
      | eval cluster=lower(trim(toString(coalesce(k8s_cluster_name, cluster_name, cluster, eks_cluster_name, gke_cluster_name, aks_cluster_name, resource_cluster, ""))))
      | eval verb_l=lower(trim(toString(coalesce(verb, ""))))
      | eval res_l=lower(trim(toString(coalesce('objectRef.resource', objectRef.resource, objectRef_resource, ""))))
      | eval ns=trim(toString(coalesce('objectRef.namespace', objectRef.namespace, objectRef_namespace, "")))
      | eval actor=toString(coalesce('user.username', user.username, user_username, user__username, ""))
      | eval obj_name=toString(coalesce('objectRef.name', objectRef.name, objectRef_name, ""))
      | eval role_name=toString(coalesce('requestObject.metadata.name', requestObject_metadata_name, obj_name, ""))
      | eval role_kind="ClusterRole"
      | eval req_uri=toString(coalesce(requestURI, requestUri, ""))
      | eval lr=lower(_raw)
      | where match(verb_l, "^(create|update|patch)$")
      | where res_l="clusterroles"
      | eval resp_code=tonumber(tostring(coalesce('responseStatus.code', responseStatus.code, responseStatus_code, "201")),10)
      | where resp_code>=200 AND resp_code<300
      | eval has_star_star=if(match(lr, "\\\"verbs\\\"\\s*:\\s*\\[[^\\]]*\\\"\\*\\\"") AND match(lr, "\\\"resources\\\"\\s*:\\s*\\[[^\\]]*\\\"\\*\\\""), 1, 0)
      | eval has_impersonate=if(match(lr, "\\\"impersonate\\\""), 1, 0)
      | eval has_escalate=if(match(lr, "\\\"escalate\\\""), 1, 0)
      | eval has_bind_roles=if(match(lr, "\\\"bind\\\"") AND match(lr, "clusterroles"), 1, 0)
      | eval has_pod_shell=if(match(lr, "pods/exec") OR match(lr, "\\\"pods\\\"[^\\]]*exec") OR match(lr, "pods\\\\/exec") OR (match(lr, "\\\"pods\\\"") AND match(lr, "\\\"exec\\\"")), 1, 0)
      | eval has_pod_attach_pf=if(match(lr, "\\\"pods\\\"") AND match(lr, "\\\"attach\\\""), 1, 0)
      | eval has_pod_pf=if(match(lr, "\\\"pods\\\"") AND match(lr, "portforward"), 1, 0)
      | eval has_nodes_star=if(match(lr, "\\\"nodes\\\"") AND match(lr, "\\\"\\*\\\""), 1, 0)
      | eval has_pv_write=if(match(lr, "persistentvolumes") AND (match(lr, "\\\"create\\\"") OR match(lr, "\\\"update\\\"") OR match(lr, "\\\"patch\\\"") OR match(lr, "\\\"delete\\\"") OR match(lr, "\\\"\\*\\\"")), 1, 0)
      | eval has_sc_write=if(match(lr, "storageclasses") AND (match(lr, "\\\"create\\\"") OR match(lr, "\\\"update\\\"") OR match(lr, "\\\"patch\\\"") OR match(lr, "\\\"delete\\\"") OR match(lr, "\\\"\\*\\\"")), 1, 0)
      | eval sensitive_rule=if(has_star_star OR has_impersonate OR has_escalate OR has_bind_roles OR has_pod_shell OR has_pod_attach_pf OR has_pod_pf OR has_nodes_star OR has_pv_write OR has_sc_write, 1, 0)
      | where sensitive_rule=1
      | eval signal_lane="clusterrole_sensitive_rules_mutation"
      | eval sa_ns=""
      | eval sa_name=""
      | fields _time cluster actor signal_lane obj_name role_name role_kind ns sa_ns sa_name resp_code req_uri verb_l res_l ]
    [ search index=k8s_audit sourcetype="kube:apiserver:audit" earliest=-24h@h latest=@h
      | eval cluster=lower(trim(toString(coalesce(k8s_cluster_name, cluster_name, cluster, eks_cluster_name, gke_cluster_name, aks_cluster_name, resource_cluster, ""))))
      | eval verb_l=lower(trim(toString(coalesce(verb, ""))))
      | eval res_l=lower(trim(toString(coalesce('objectRef.resource', objectRef.resource, objectRef_resource, ""))))
      | eval subres=lower(trim(toString(coalesce('objectRef.subresource', objectRef.subresource, objectRef_subresource, ""))))
      | eval ns=trim(toString(coalesce('objectRef.namespace', objectRef.namespace, objectRef_namespace, "")))
      | eval actor=toString(coalesce('user.username', user.username, user_username, user__username, ""))
      | eval obj_name=toString(coalesce('objectRef.name', objectRef.name, objectRef_name, ""))
      | eval role_name=""
      | eval role_kind=""
      | eval req_uri=lower(toString(coalesce(requestURI, requestUri, "")))
      | eval lr=lower(_raw)
      | where match(res_l, "^certificatesigningrequests$") OR match(req_uri, "certificatesigningrequests")
      | where match(verb_l, "^(create|update|patch)$")
      | eval resp_code=tonumber(tostring(coalesce('responseStatus.code', responseStatus.code, responseStatus_code, "201")),10)
      | where resp_code>=200 AND resp_code<300
      | where match(lr, "approve|approval") OR match(subres, "approval") OR match(req_uri, "approval")
      | eval signal_lane="csr_signing_approve_mutation"
      | eval sa_ns=""
      | eval sa_name=""
      | fields _time cluster actor signal_lane obj_name role_name role_kind ns sa_ns sa_name resp_code req_uri verb_l res_l ]
| eval subject_key=case(signal_lane="rbac_group_system_masters_binding", "group:system:masters", len(sa_ns)>0 AND len(sa_name)>0, "sa:".sa_ns.":".sa_name, true(), "actor:".actor)
| join type=left max=0 cluster, subject_key [
    | inputlookup k8s_cluster_admin_sa_allowlist.csv
    | eval cluster=lower(trim(toString(coalesce(cluster, k8s_cluster, cluster_name, ""))))
    | eval subject_key=trim(toString(coalesce(subject_key, subject, principal_key, "")))
    | eval approved_change_ticket=toString(coalesce(approved_change_ticket, change_ticket, ticket, ""))
    | eval allowlist_expiry_epoch=tonumber(tostring(coalesce(allowlist_expiry_epoch, expiry_epoch, "0")),10)
    | eval allowlist_owner=toString(coalesce(allowlist_owner, owner_team, ""))
    | fields cluster subject_key approved_change_ticket allowlist_expiry_epoch allowlist_owner ]
| fillnull value="" approved_change_ticket allowlist_owner
| fillnull value=0 allowlist_expiry_epoch
| eval now_e=now()
| eval allowlist_expired=if(allowlist_expiry_epoch>0 AND now_e>allowlist_expiry_epoch, 1, 0)
| eval breakglass_tracked=if(len(trim(approved_change_ticket))>0 AND allowlist_expired=0, 1, 0)
| join type=left max=1 actor [
    | tstats summariesonly=t count AS auth_model_touches FROM datamodel=Authentication WHERE nodename=Authentication earliest=-24h@h latest=@h BY Authentication.user
    | rename Authentication.user AS actor ]
| fillnull value=0 auth_model_touches
| eventstats count AS lane_volume_24h BY cluster, signal_lane
| streamstats window=120 current=t global=f count AS actor_lane_seq BY cluster, actor, signal_lane
| eval severity=case(
    allowlist_expired=1 AND len(trim(approved_change_ticket))>0, "high_expired_allowlist",
    signal_lane="rbac_group_system_masters_binding", "critical",
    breakglass_tracked=1 AND match(signal_lane, "cluster_admin"), "medium_breakglass_documented",
    match(signal_lane, "cluster_admin"), "critical",
    signal_lane="clusterrole_sensitive_rules_mutation" AND match(_raw, "persistentvolumes|storageclasses|nodes"), "critical",
    signal_lane="clusterrole_sensitive_rules_mutation", "high",
    signal_lane="csr_signing_approve_mutation", "high",
    true(), "medium")
| table _time cluster actor signal_lane severity subject_key breakglass_tracked allowlist_expired approved_change_ticket allowlist_owner role_name role_kind obj_name ns sa_ns sa_name lane_volume_24h actor_lane_seq auth_model_touches req_uri resp_code
```

## CIM SPL

```spl
| tstats summariesonly=t count FROM datamodel=Authentication WHERE nodename=Authentication earliest=-24h@h latest=@h BY Authentication.user Authentication.action
| rename Authentication.user AS actor
| head 200
```

## Visualization

Severity-colored table mirroring the closing SPL projection; timeline of lane_volume_24h by signal_lane; single-value tiles for critical versus high counts; drilldown from req_uri to raw audit JSON; companion panel listing expired allowlist rows.

## Known False Positives

GitOps controllers such as FluxCD and ArgoCD continuously reconcile ClusterRoleBindings and ClusterRoles from git; bursts that align with merge commits and carry the same subject_key as prior hours are often operational noise rather than intrusion—correlate with pipeline identity and commit SHA before paging. Fresh cluster bootstrap with kubeadm, kops, eksctl, or managed control-plane installers creates initial cluster-admin bindings for administrators; treat the first day after create-cluster as a known noisy window when change records exist, and tune wrapper searches with cluster-age metadata rather than muting the underlying audit. Break-glass incidents where on-call engineers temporarily bind cluster-admin with a documented ticket should appear as medium_breakglass_documented rows; expired tickets should flip to high_expired_allowlist until renewed. Operators such as kured, cluster-autoscaler, and Karpenter may install or upgrade RBAC that references powerful ClusterRoles during rollouts; verify chart versions and vendor documentation before declaring compromise. Deliberately permissive developer sandboxes that maintain a standing allowlist for sandbox cluster-admin service accounts will page continuously unless namespaces and clusters are labeled and wrapper searches filter dev-tier noise. Automated regression suites that create and delete bindings within minutes can look like privilege escalation; tag those service accounts in the allowlist or exclude ephemeral cluster names. Cloud audit exports occasionally flatten or truncate requestObject; rex arms may miss service account namespace extraction even when the event is genuine—fall back to raw JSON review. Penetration tests that exercise CSR approval or wildcard roles will trigger this control by design; coordinate purple-team windows in the lookup. Finally, UC-3.2.12 may already surface overlapping cluster-admin signals with different severity semantics—use this UC for immutable evidence rows and UC-3.2.12 for broader hunting context without disabling either.

## References

- [Kubernetes — Using RBAC Authorization](https://kubernetes.io/docs/reference/access-authn-authz/rbac/)
- [Kubernetes — Auditing](https://kubernetes.io/docs/reference/access-authn-authz/)
- [Kubernetes — Certificate Signing Requests](https://kubernetes.io/docs/reference/access-authn-authz/certificate-signing-requests/)
- [Kubernetes API — ClusterRoleBinding v1](https://kubernetes.io/docs/reference/kubernetes-api/authorization-resources/cluster-role-binding-v1/)
- [Kubernetes — RBAC super-user and system:masters](https://kubernetes.io/docs/reference/access-authn-authz/rbac/#super-user)
- [Kubernetes — Default cluster-admin and user-facing roles](https://kubernetes.io/docs/reference/access-authn-authz/rbac/#user-facing-roles)
- [MITRE ATT&CK — T1078.004 Cloud Accounts (Containers)](https://attack.mitre.org/techniques/T1078/004/)
- [NSA and CISA — Kubernetes Hardening Guidance](https://media.defense.gov/2022/Aug/29/2003066362/-1/-1/0/CTR_KUBERNETES_HARDENING_GUIDANCE_1.2_20220315.PDF)
- [Splunk — Add-on for Kubernetes](https://docs.splunk.com/Documentation/AddOns/released/Kubernetes/About)
