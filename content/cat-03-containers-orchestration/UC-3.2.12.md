<!-- AUTO-GENERATED from UC-3.2.12.json — DO NOT EDIT -->

---
id: "3.2.12"
title: "Kubernetes RBAC Anomalies and Excessive-Permission Detection"
status: "verified"
criticality: "high"
splunkPillar: "Security"
---

# UC-3.2.12 · Kubernetes RBAC Anomalies and Excessive-Permission Detection

> **Criticality:** High &middot; **Difficulty:** Advanced &middot; **Pillar:** Security &middot; **Type:** Security, Compliance &middot; **Wave:** Walk &middot; **Status:** Verified

*We watch who receives powerful control inside your container platform and who tries to touch private settings they should not see. When automation accounts gain dangerous powers or strangers probe sensitive areas, we raise the alarm early.*

---

## Description

Unique monitoring axis: Kubernetes RBAC authorization signals—who binds cluster-admin or high-impact roles to automation principals, who receives forbidden outcomes on secrets, nodes, or config maps, who succeeds with exec or port-forward class verbs in production namespaces, and whether impersonation headers appear without matching change records—correlated to kube-state-metrics RBAC binding scrape presence and a trusted_admin_users.csv suppression plane. This is who can do what, not UC-3.2.22 pod security admission outcomes, not UC-3.2.18 or UC-3.2.41 data-plane scopes, and not generic apiserver latency without RBAC context.

## Value

Privilege sprawl and silent cluster-admin grants are common precursors to secret theft, destructive object deletes, and cryptomining installs that bypass workload scanners. Timestamped RBAC mutations plus forbidden storms give platform security and identity teams a prioritized backlog before attackers stabilize persistence. Regulators and enterprise customers asking for CIS, NSA CISA, or BSI-aligned Kubernetes hardening receive exportable evidence that bindings and risky verbs are monitored, not only documented in wikis. Mean time to contain improves because Splunk shows which service account, which namespace, and which roleRef changed in the same window as suspicious denials.

## Implementation

Stand up k8s_audit for kube:apiserver:audit with RequestResponse rules on rbac.authorization.k8s.io mutations and pod exec or port-forward verbs; mirror kube-state-metrics scrapes into k8s_metrics for corroboration. Version trusted_admin_users.csv with ticket-backed suppressions for break-glass identities. Save uc_3_2_12_rbac_anomalies on a fifteen-minute cadence over earliest=-24h@h latest=@h, route critical and high severity rows to platform security, and archive weekly exports of the closing table with lookup commit hashes for auditors.

## Evidence

Saved search uc_3_2_12_rbac_anomalies; versioned trusted_admin_users.csv; weekly CSV export of the closing table to a restricted evidence index; dashboard drilldowns from signal_lane to raw audit JSON and kube-state-metrics scrape lines.

## Control test

### Positive scenario

In lab, create a ClusterRoleBinding referencing cluster-admin that binds a non-kube-system service account; ingest kube:apiserver:audit with requestObject intact; run uc_3_2_12_rbac_anomalies and expect sa_cluster_admin_bind or cluster_admin_binding_change with severity critical or high and non-null role_name cluster-admin.

### Negative scenario

Add the executing principal to trusted_admin_users.csv with suppress_alerts=1 and matching cluster or asterisk; repeat a harmless binding create; confirm the scheduled alert search returns zero unsuppressed rows while audit volume remains visible in a dashboard clone that omits the suppression filter.

## Detailed Implementation

### Step 1 — Prerequisites

Head of Platform owns this control with the Kubernetes platform security lead, the identity engineer who approves audit policy depth, and the Splunk observability owner who operates OpenTelemetry Collector fleets across clusters. This use case isolates the RBAC plane: who can mutate Role, ClusterRole, RoleBinding, and ClusterRole objects, who receives cluster-admin or wildcard-equivalent grants, which principals hit forbidden outcomes when touching secrets, nodes, or config maps, and which subjects successfully use exec, attach, port-forward, or proxy-style verbs against production namespaces. UC-3.2.22 remains admission-time Pod Security Standard enforcement and namespace label drift; it never substitutes for authorization graphs. UC-3.2.18, UC-3.2.41, and data-plane networking or workload health siblings stay in their lanes. Pair UC-3.2.7 only when apiserver instability might truncate audit bodies during incident bridges.

Index contracts: dedicate index=k8s_audit for sourcetype=kube:apiserver:audit with role-based access separating platform security readers from wide developer roles. Optional index=k8s_metrics carries kube-state-metrics text lines so analysts can corroborate that RBAC-related series still scrape when audit volume spikes. Every event must expose a stable cluster dimension such as k8s_cluster_name, eks_cluster_name, gke_cluster_name, aks_cluster_name, or cluster_name so joins and suppressions do not collapse multi-cluster estates.

Audit policy depth: RBAC investigations require RequestResponse for verbs create, update, and patch on rbac.authorization.k8s.io resources including roles, clusterroles, rolebindings, and clusterrolebindings. Without requestObject, analysts cannot see subjects and roleRef pairs your SPL tests. Keep Metadata-only rules for high-volume read noise, but never demote mutating RBAC objects to Metadata in regulated tiers. Include impersonation headers in the policy where your distribution supports logging impersonatedUser blocks.

Governance lookup: publish trusted_admin_users.csv under change control with columns username (apiserver audit user.username form, lowercased in the join), cluster or asterisk for fleet-wide rows, suppress_alerts (1 mutes paging while retaining dashboard rows if you fork the SPL), notes or justification ticket pointers, and optional expiry_epoch for time-bound break-glass. Refresh the CSV from the same system of record that issues emergency access so auditors can trace suppressions to tickets.

Risk framing: a ClusterRoleBinding that grants cluster-admin to a namespace-scoped automation service account is not a paperwork issue; it is lateral movement fuel because any compromise of that token becomes control of the entire fleet. Wildcard verbs inside ClusterRole rules are softer but still dangerous when aggregated with escalating bindings. Forbidden storms against secrets while a novel service account appears often precedes secret enumeration. Successful exec into production pods from identities outside the on-call roster is rarely benign.

Legal and privacy: audit bodies can include Secret names; avoid indexing Secret data fields. Redact at the collector when policies accidentally capture request objects for Secret resources beyond metadata.

Differentiation recap: this UC does not evaluate pod security admission decisions, image vulnerabilities, CNI dataplane loss, or kubelet health. It answers whether RBAC posture and risky verbs align with least privilege expectations.

Clock skew: keep apiserver, worker nodes, and Splunk indexers within thirty seconds or ordering tricks in streamstats mislead burst interpretation during forensics.

Licensing: RequestResponse RBAC auditing is moderate volume compared to full pod body capture; still compress at the collector and tier hot versus frozen retention deliberately.

### Step 2 — Configure data collection

Wire kube-apiserver audit to Splunk first. On self-managed clusters, point Splunk OpenTelemetry Collector filelog at the host path your distribution documents for audit.log, commonly under /var/log/kubernetes/audit.log, and set splunk_hec exporter sourcetype to kube:apiserver:audit with index=k8s_audit. On managed clusters without node access, use the cloud audit export that preserves Kubernetes audit JSON and normalize field names so the coalesce ladders in the SPL stay stable.

Deploy kube-state-metrics with a scrape interval your SRE council accepts, typically fifteen to sixty seconds, and forward prometheus:scrape:metrics into k8s_metrics. Confirm raw text includes kube_role_binding or kube_clusterrole_binding families so the metrics arm proves the scraper still sees RBAC inventory signals even when you are not alerting on them directly.

Audit policy skeleton emphasizing RBAC mutations at RequestResponse:

```
apiVersion: audit.k8s.io/v1
kind: Policy
omitStages:
  - "RequestReceived"
rules:
  - level: RequestResponse
    verbs: ["create", "update", "patch", "delete"]
    resources:
      - group: "rbac.authorization.k8s.io"
        resources: ["roles", "clusterroles", "rolebindings", "clusterrolebindings"]
    namespaces: ["*"]
  - level: RequestResponse
    verbs: ["create", "connect"]
    resources:
      - group: ""
        resources: ["pods/exec", "pods/attach", "pods/portforward", "pods/proxy", "services/proxy"]
    namespaces: ["*"]
  - level: Metadata
    resources:
      - group: ""
        resources: ["events"]
```

OpenTelemetry Collector fragment illustrating dual export paths:

```
receivers:
  filelog/audit:
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
  splunk_hec/audit:
    token: "${SPLUNK_HEC_TOKEN_AUDIT}"
    endpoint: "https://splunk.example.com:8088/services/collector/event"
    index: k8s_audit
    sourcetype: kube:apiserver:audit
  splunk_hec/metrics:
    token: "${SPLUNK_HEC_TOKEN_METRICS}"
    endpoint: "https://splunk.example.com:8088/services/collector/event"
    index: k8s_metrics
    sourcetype: prometheus:scrape:metrics
service:
  pipelines:
    logs/audit:
      receivers: [filelog/audit]
      exporters: [splunk_hec/audit]
    metrics/ksm:
      receivers: [prometheus]
      exporters: [splunk_hec/metrics]
```

trusted_admin_users.csv sample:

```
username,cluster,suppress_alerts,notes,expiry_epoch
breakglass.platform,*,1,CHG-4412 emergency etcd access,0
ci.deploy.bot,prod-eks-01,0,Pipeline identity — do not suppress,0
```

Validate before saving the alert: index=k8s_audit sourcetype=kube:apiserver:audit earliest=-15m must return non-zero counts for RBAC mutations in lab, and index=k8s_metrics must show kube-state binding metrics within the same cluster labels you expect in production dashboards.

### Step 3 — Create the search and alert

Save the SPL as uc_3_2_12_rbac_anomalies with a fifteen-minute schedule during steady operations, using earliest=-24h@h latest=@h so volume baselines remain meaningful without scanning thirty days every run. Throttle duplicate critical rows per cluster_row, signal_lane, and actor for forty-five minutes unless severity escalates from medium to critical within the same hour. Route critical rows to the platform security bridge with the closing table attached. Archive weekly CSV snapshots to a restricted evidence index with trusted_admin_users.csv commit hashes.

Pipeline narrative: the opening comment macro records index names, sourcetypes, lookup path, and time window. multisearch fans five arms so a silent metrics scrape does not hide RBAC mutations, and silent bindings do not hide forbidden storms. Arm one isolates successful create, update, and patch traffic against RoleBinding and ClusterRoleBinding objects, evaluates cluster-admin roleRef names, service account subjects, and non-system binding namespaces, and tags sa_cluster_admin_bind, cluster_admin_binding_change, or new_binding_non_system_sa lanes. Arm two captures HTTP 403 outcomes on secrets, nodes, and config maps plus pod subresources caught by RBAC-style forbidden messages, tagging rbac_denied_or_blocked_sensitive. Arm three requires production-like namespaces and successful pod exec, attach, or port-forward style URIs, tagging prod_pod_exec_proxy_success. Arm four surfaces impersonation by requiring a populated impersonatedUser username in audit JSON. Arm five samples kube-state-metrics lines for kube role binding families to prove scraper visibility with ksm_rbac_binding_metric_tick. After fan-in, user_key lowercases actor for a left join wrapping inputlookup trusted_admin_users.csv with optional per-cluster scoping via lookup_cluster versus cluster_row equality or asterisk wildcard. Rows marked trusted_suppress downgrade to suppressed_trusted_actor and drop from the alert path while you can clone the search for audit dashboards that still display them. A second left join runs tstats summariesonly against the Authentication data model counting prior-day touches for the same actor label, producing auth_model_events_24h for analyst context. eventstats counts signal_volume_24h per cluster and lane; streamstats sequences bursts per actor. case assigns severity tiers with production namespace weighting. The closing table lists _time, cluster_row, signal_lane, severity, actor, namespace, object name, resource, verb, role name, role kind, response code, URI excerpt, twenty-four hour lane volume, authentication model touch count, and stream sequence.

Fenced SPL for runbooks must match the spl JSON field byte-for-byte:

```spl
`comment("UC-3.2.12 Kubernetes RBAC anomalies and excessive-permission detection. Tunables: idx_audit=k8s_audit st_audit=kube:apiserver:audit; idx_metrics=k8s_metrics st_metrics=prometheus:scrape:metrics; lookup trusted_admin_users.csv; earliest=-24h@h latest=@h")`
| multisearch 
    [ search index=k8s_audit sourcetype="kube:apiserver:audit" earliest=-24h@h latest=@h
      | eval cluster=lower(trim(toString(coalesce(k8s_cluster_name, cluster_name, cluster, eks_cluster_name, gke_cluster_name, aks_cluster_name, resource_cluster, ""))))
      | eval verb_l=lower(trim(toString(coalesce(verb, ""))))
      | eval res_l=lower(trim(toString(coalesce('objectRef.resource', objectRef.resource, objectRef_resource, ""))))
      | eval ns=trim(toString(coalesce('objectRef.namespace', objectRef.namespace, objectRef_namespace, "")))
      | eval actor=toString(coalesce('user.username', user.username, user_username, user__username, ""))
      | eval obj_name=toString(coalesce('objectRef.name', objectRef.name, objectRef_name, ""))
      | eval role_name=toString(coalesce('requestObject.roleRef.name', requestObject_roleRef_name, ""))
      | eval role_kind=toString(coalesce('requestObject.roleRef.kind', requestObject_roleRef_kind, ""))
      | eval lr=lower(_raw)
      | where match(verb_l, "^(create|update|patch)$")
      | where match(res_l, "^(clusterrolebindings|rolebindings)$")
      | eval resp_code=tonumber(tostring(coalesce('responseStatus.code', responseStatus.code, responseStatus_code, "201")),10)
      | eval binds_cluster_admin=if(match(role_name, "(?i)^cluster-admin$") OR match(lr, "\"name\"\\s*:\\s*\"cluster-admin\""), 1, 0)
      | eval sa_subject=if(match(lr, "system:serviceaccount:") AND match(lr, "subjects"), 1, 0)
      | eval non_system_binding_ns=if(len(ns)==0 OR NOT match(ns, "^(kube-system|kube-public|kube-node-lease)$"), 1, 0)
      | eval signal_lane=case(binds_cluster_admin=1 AND sa_subject=1 AND non_system_binding_ns=1, "sa_cluster_admin_bind", binds_cluster_admin=1, "cluster_admin_binding_change", sa_subject=1 AND non_system_binding_ns=1 AND match(verb_l, "^create$"), "new_binding_non_system_sa", true(), "role_binding_mutation_review")
      | where NOT (signal_lane="role_binding_mutation_review" AND resp_code>=400)
      | where signal_lane!="role_binding_mutation_review" OR (sa_subject=1 AND match(verb_l, "^create$") AND non_system_binding_ns=1)
      | eval object_uri=toString(coalesce(requestURI, requestUri, ""))
      | fields _time cluster actor ns obj_name res_l verb_l role_name role_kind signal_lane object_uri resp_code ]
    [ search index=k8s_audit sourcetype="kube:apiserver:audit" earliest=-24h@h latest=@h
      | eval cluster=lower(trim(toString(coalesce(k8s_cluster_name, cluster_name, cluster, eks_cluster_name, gke_cluster_name, aks_cluster_name, resource_cluster, ""))))
      | eval verb_l=lower(trim(toString(coalesce(verb, ""))))
      | eval res_l=lower(trim(toString(coalesce('objectRef.resource', objectRef.resource, objectRef_resource, ""))))
      | eval ns=trim(toString(coalesce('objectRef.namespace', objectRef.namespace, objectRef_namespace, "")))
      | eval actor=toString(coalesce('user.username', user.username, user_username, user__username, ""))
      | eval obj_name=toString(coalesce('objectRef.name', objectRef.name, objectRef_name, ""))
      | eval resp_code=tonumber(tostring(coalesce('responseStatus.code', responseStatus.code, responseStatus_code, "0")),10)
      | eval resp_reason=lower(toString(coalesce('responseStatus.reason', responseStatus.reason, responseStatus_reason, "")))
      | eval resp_msg=lower(toString(coalesce('responseStatus.message', responseStatus.message, responseStatus_message, "")))
      | where resp_code=403
      | where match(res_l, "^(secrets|nodes|configmaps)$") OR match(res_l, "^pods$") AND match(lower(toString(coalesce('objectRef.subresource', objectRef.subresource, ""))), "^(exec|attach|portforward)$")
      | where match(resp_reason, "forbidden") OR match(resp_msg, "forbidden|cannot|rbac|subjectaccessreview|not allowed")
      | eval signal_lane="rbac_denied_or_blocked_sensitive"
      | eval role_name=""
      | eval role_kind=""
      | eval object_uri=toString(coalesce(requestURI, requestUri, ""))
      | fields _time cluster actor ns obj_name res_l verb_l role_name role_kind signal_lane object_uri resp_code ]
    [ search index=k8s_audit sourcetype="kube:apiserver:audit" earliest=-24h@h latest=@h
      | eval cluster=lower(trim(toString(coalesce(k8s_cluster_name, cluster_name, cluster, eks_cluster_name, gke_cluster_name, aks_cluster_name, resource_cluster, ""))))
      | eval verb_l=lower(trim(toString(coalesce(verb, ""))))
      | eval res_l=lower(trim(toString(coalesce('objectRef.resource', objectRef.resource, objectRef_resource, ""))))
      | eval sub_l=lower(trim(toString(coalesce('objectRef.subresource', objectRef.subresource, objectRef_subresource, ""))))
      | eval ns=trim(toString(coalesce('objectRef.namespace', objectRef.namespace, objectRef_namespace, "")))
      | eval actor=toString(coalesce('user.username', user.username, user_username, user__username, ""))
      | eval obj_name=toString(coalesce('objectRef.name', objectRef.name, objectRef_name, ""))
      | eval uri=lower(toString(coalesce(requestURI, requestUri, "")))
      | eval prod_like=if(match(lower(ns), "(?i)prod|production|tier0|mission|prd-"), 1, 0)
      | where prod_like=1
      | where res_l="pods"
      | where match(sub_l, "^(exec|attach|portforward)$") OR match(uri, "/exec|portforward|/proxy/")
      | eval resp_code=tonumber(tostring(coalesce('responseStatus.code', responseStatus.code, responseStatus_code, "201")),10)
      | where resp_code>=200 AND resp_code<300
      | eval signal_lane="prod_pod_exec_proxy_success"
      | eval role_name=""
      | eval role_kind=""
      | eval object_uri=toString(coalesce(requestURI, requestUri, ""))
      | fields _time cluster actor ns obj_name res_l verb_l role_name role_kind signal_lane object_uri resp_code ]
    [ search index=k8s_audit sourcetype="kube:apiserver:audit" earliest=-24h@h latest=@h
      | eval cluster=lower(trim(toString(coalesce(k8s_cluster_name, cluster_name, cluster, eks_cluster_name, gke_cluster_name, aks_cluster_name, resource_cluster, ""))))
      | eval verb_l=lower(trim(toString(coalesce(verb, ""))))
      | eval res_l=lower(trim(toString(coalesce('objectRef.resource', objectRef.resource, objectRef_resource, ""))))
      | eval ns=trim(toString(coalesce('objectRef.namespace', objectRef.namespace, objectRef_namespace, "")))
      | eval actor=toString(coalesce('user.username', user.username, user_username, user__username, ""))
      | eval obj_name=toString(coalesce('objectRef.name', objectRef.name, objectRef_name, ""))
      | eval imp=toString(coalesce('impersonatedUser.username', impersonatedUser_username, impersonatedUser__username, ""))
      | where len(imp)>0
      | eval signal_lane="apiserver_impersonation_audit"
      | eval role_name=imp
      | eval role_kind="impersonated_user"
      | eval resp_code=tonumber(tostring(coalesce('responseStatus.code', responseStatus.code, responseStatus_code, "201")),10)
      | eval object_uri=toString(coalesce(requestURI, requestUri, ""))
      | fields _time cluster actor ns obj_name res_l verb_l role_name role_kind signal_lane object_uri resp_code ]
    [ search index=k8s_metrics sourcetype="prometheus:scrape:metrics" earliest=-4h@h latest=@h
      | eval cluster=lower(trim(toString(coalesce(k8s_cluster_name, cluster_name, cluster, eks_cluster_name, gke_cluster_name, aks_cluster_name, resource_cluster, ""))))
      | where match(_raw, "kube_clusterrole_binding") OR match(_raw, "kube_role_binding")
      | eval mn=lower(trim(toString(coalesce(__name__, metric_name, name, MetricName, ""))))
      | where like(mn, "%kube_%binding%") AND NOT like(mn, "%_created")
      | stats dc(_raw) AS ksm_binding_series_dc BY cluster _time
      | eval actor="kube_state_metrics"
      | eval ns=""
      | eval obj_name="kube_state_rbac_footprint"
      | eval res_l="metrics"
      | eval verb_l="scrape"
      | eval role_name=""
      | eval role_kind=""
      | eval signal_lane="ksm_rbac_binding_metric_tick"
      | eval object_uri="prometheus_kube_state_binding_family"
      | eval resp_code=0
      | fields _time cluster actor ns obj_name res_l verb_l role_name role_kind signal_lane object_uri resp_code ]
| eval user_key=lower(trim(toString(actor)))
| join type=left max=0 user_key [
    | inputlookup trusted_admin_users.csv
    | eval user_key=lower(trim(toString(coalesce(username, user, principal, breakglass_user, ""))))
    | eval lookup_cluster=lower(trim(toString(coalesce(cluster, k8s_cluster, "*"))))
    | eval trusted_suppress_raw=tonumber(tostring(coalesce(suppress_alerts, trusted_suppress_flag, "0")),10)
    | eval breakglass_note=toString(coalesce(notes, justification, ""))
    | fields user_key lookup_cluster trusted_suppress_raw breakglass_note ]
| eval cluster_row=coalesce(nullif(cluster,""), "unknown_cluster")
| eval lookup_match=if(isnotnull(lookup_cluster) AND (lookup_cluster="*" OR lookup_cluster=cluster_row), 1, 0)
| eval trusted_suppress=if(lookup_match=1 AND trusted_suppress_raw=1, 1, 0)
| join type=left max=1 actor [
    | tstats summariesonly=true count AS auth_model_events_24h FROM datamodel=Authentication WHERE nodename=Authentication earliest=-24h@h latest=@h BY Authentication.user
    | rename Authentication.user AS actor ]
| fillnull value=0 auth_model_events_24h trusted_suppress trusted_suppress_raw lookup_match
| eval prod_namespace=if(match(lower(ns), "(?i)prod|production|tier0|mission|prd-"), 1, 0)
| eventstats count AS signal_volume_24h BY cluster_row, signal_lane
| streamstats window=120 current=t global=f count AS stream_event_seq BY cluster_row, actor, signal_lane
| eval severity=case(
    signal_lane="sa_cluster_admin_bind", "critical",
    signal_lane="cluster_admin_binding_change" AND prod_namespace=1, "critical",
    signal_lane="cluster_admin_binding_change", "high",
    signal_lane="new_binding_non_system_sa" AND prod_namespace=1, "high",
    signal_lane="new_binding_non_system_sa", "medium",
    signal_lane="rbac_denied_or_blocked_sensitive" AND match(res_l, "^nodes$"), "high",
    signal_lane="rbac_denied_or_blocked_sensitive", "medium",
    signal_lane="prod_pod_exec_proxy_success", "high",
    signal_lane="apiserver_impersonation_audit", "high",
    signal_lane="ksm_rbac_binding_metric_tick", "low",
    true(), "medium")
| eval severity=if(trusted_suppress=1, "suppressed_trusted_actor", severity)
| where severity!="suppressed_trusted_actor"
| table _time cluster_row signal_lane severity actor ns obj_name res_l verb_l role_name role_kind resp_code object_uri signal_volume_24h auth_model_events_24h stream_event_seq
```

savedsearches.conf sketch (INI syntax, not SPL):

```ini
[uc_3_2_12_rbac_anomalies_alert]
cron_schedule = */15 * * * *
dispatch.earliest_time = -24h@h
dispatch.latest_time = now
enableSched = 1
action.email = 1
action.email.to = platform-k8s-security@example.com
action.email.subject = RBAC anomaly $result.severity$ on $result.cluster_row$
counttype = number of events
relation = greater than
quantity = 0
search = | savedsearch uc_3_2_12_rbac_anomalies | where severity IN ("critical","high")
```

cimSpl for CIM Authentication overlays when you normalize privileged kubectl sessions into the Authentication model (paste from the cimSpl JSON field, not the primary spl field):

```text
| tstats summariesonly=true count FROM datamodel=Authentication WHERE nodename=Authentication earliest=-24h@h latest=@h BY Authentication.user Authentication.action
| rename Authentication.user AS actor | head 200
```

Alert actions should attach signal_lane, object_uri, and remind investigators that UC-3.2.22 covers pod admission denials, not RBAC grants.

### Step 4 — Validate

Positive test A — cluster-admin binding: in a disposable lab namespace outside kube-system, create a RoleBinding or ClusterRoleBinding that references cluster-admin and binds a dedicated lab service account; confirm audit shows user.username for your kubectl principal, requestObject.roleRef.name cluster-admin, and subjects containing system:serviceaccount; run the saved search and expect sa_cluster_admin_bind or cluster_admin_binding_change with severity critical or high, then delete the binding.

Positive test B — forbidden secret read: use kubectl with a low-privilege kubeconfig to attempt kubectl get secret -n default something; confirm 403 audit rows with objectRef.resource secrets and rbac_denied_or_blocked_sensitive.

Positive test C — exec success signal: from an approved break-glass account not in trusted_admin_users.csv suppression, kubectl exec into a pod in a namespace whose name includes prod; confirm prod_pod_exec_proxy_success with HTTP success codes only if your lab policy allows it; tear down afterward.

Negative test — suppressed break-glass: add your lab principal to trusted_admin_users.csv with suppress_alerts=1, repeat a benign binding mutation that still logs, confirm the alert search emits no row while a dashboard clone without the suppression filter still shows the event.

Correlation test — control plane instability: when UC-3.2.7 shows critical apiserver health, pause RBAC alert interpretation until audit completeness returns.

RBAC test: readers without k8s_audit must see zero rows.

Performance test: Job Inspector during Monday peaks; if multisearch cost exceeds budget, split arms into separate saved searches writing to a summary index keyed on cluster and signal_lane.

### Step 5 — Operationalize & Troubleshoot

Case 1 — Service account received cluster-admin outside kube-system: freeze deploy pipelines touching that namespace, rotate the service account token secret, and open a privilege review ticket before accepting any vendor claim that the grant is mandatory.

Case 2 — Wildcard verb ClusterRole update during business hours: diff the rules stanza against git main, revert if unauthorized, and scan for bindings that reference the role.

Case 3 — Burst of forbidden reads against secrets from a novel principal: treat as enumeration rehearsal, isolate the identity at the identity provider, and hunt for successful reads that followed.

Case 4 — Successful production exec from a contractor identity: verify change tickets, enable session recording if available, and revoke kubeconfig if none exists.

Case 5 — Impersonation audit rows without matching change record: escalate because impersonation headers should map to documented automation or support workflows.

Case 6 — kube-state-metrics arm silent while RBAC mutations continue: repair scrapes before trusting absence of ksm_rbac_binding_metric_tick rows as evidence of health.

Case 7 — trusted_admin_users.csv stale: expired break-glass still suppressed; reconcile expiry_epoch logic in a macro weekly.

Case 8 — GitOps controller churn: Argo CD or Flux may reconcile bindings rapidly; require git commit correlation before paging on volume alone.

Case 9 — CI service account permission updates: align alerts with deployment windows or label pipelines in the lookup to downgrade medium severity.

Case 10 — Vendor operators requiring cluster-admin: document operator namespace exceptions and map them to inventory rows rather than global suppression.

Case 11 — Node bootstrap RBAC churn: expect transient bindings during upgrades; cross-check with node provisioning runbooks and mute short windows only with recorded maintenance.

Case 12 — Migration from blanket cluster-admin to least privilege: temporarily raises binding-change noise; track migration phase in a lookup column and tune severities until stabilization.

Closing checklist: five em-dash step headers present; Step 3 fenced SPL matches spl; multisearch lists five arms including kube-state-metrics scrape; coalesce appears in each audit arm; join wraps trusted_admin_users.csv; tstats enriches Authentication counts; eventstats and streamstats provide volume and sequencing; case assigns severity; final table includes thirteen analyst columns; monitoringType includes Security and Compliance; cimModels lists Change and Authentication; equipmentModels lists kubernetes_k8s.

## SPL

```spl
`comment("UC-3.2.12 Kubernetes RBAC anomalies and excessive-permission detection. Tunables: idx_audit=k8s_audit st_audit=kube:apiserver:audit; idx_metrics=k8s_metrics st_metrics=prometheus:scrape:metrics; lookup trusted_admin_users.csv; earliest=-24h@h latest=@h")`
| multisearch 
    [ search index=k8s_audit sourcetype="kube:apiserver:audit" earliest=-24h@h latest=@h
      | eval cluster=lower(trim(toString(coalesce(k8s_cluster_name, cluster_name, cluster, eks_cluster_name, gke_cluster_name, aks_cluster_name, resource_cluster, ""))))
      | eval verb_l=lower(trim(toString(coalesce(verb, ""))))
      | eval res_l=lower(trim(toString(coalesce('objectRef.resource', objectRef.resource, objectRef_resource, ""))))
      | eval ns=trim(toString(coalesce('objectRef.namespace', objectRef.namespace, objectRef_namespace, "")))
      | eval actor=toString(coalesce('user.username', user.username, user_username, user__username, ""))
      | eval obj_name=toString(coalesce('objectRef.name', objectRef.name, objectRef_name, ""))
      | eval role_name=toString(coalesce('requestObject.roleRef.name', requestObject_roleRef_name, ""))
      | eval role_kind=toString(coalesce('requestObject.roleRef.kind', requestObject_roleRef_kind, ""))
      | eval lr=lower(_raw)
      | where match(verb_l, "^(create|update|patch)$")
      | where match(res_l, "^(clusterrolebindings|rolebindings)$")
      | eval resp_code=tonumber(tostring(coalesce('responseStatus.code', responseStatus.code, responseStatus_code, "201")),10)
      | eval binds_cluster_admin=if(match(role_name, "(?i)^cluster-admin$") OR match(lr, "\"name\"\\s*:\\s*\"cluster-admin\""), 1, 0)
      | eval sa_subject=if(match(lr, "system:serviceaccount:") AND match(lr, "subjects"), 1, 0)
      | eval non_system_binding_ns=if(len(ns)==0 OR NOT match(ns, "^(kube-system|kube-public|kube-node-lease)$"), 1, 0)
      | eval signal_lane=case(binds_cluster_admin=1 AND sa_subject=1 AND non_system_binding_ns=1, "sa_cluster_admin_bind", binds_cluster_admin=1, "cluster_admin_binding_change", sa_subject=1 AND non_system_binding_ns=1 AND match(verb_l, "^create$"), "new_binding_non_system_sa", true(), "role_binding_mutation_review")
      | where NOT (signal_lane="role_binding_mutation_review" AND resp_code>=400)
      | where signal_lane!="role_binding_mutation_review" OR (sa_subject=1 AND match(verb_l, "^create$") AND non_system_binding_ns=1)
      | eval object_uri=toString(coalesce(requestURI, requestUri, ""))
      | fields _time cluster actor ns obj_name res_l verb_l role_name role_kind signal_lane object_uri resp_code ]
    [ search index=k8s_audit sourcetype="kube:apiserver:audit" earliest=-24h@h latest=@h
      | eval cluster=lower(trim(toString(coalesce(k8s_cluster_name, cluster_name, cluster, eks_cluster_name, gke_cluster_name, aks_cluster_name, resource_cluster, ""))))
      | eval verb_l=lower(trim(toString(coalesce(verb, ""))))
      | eval res_l=lower(trim(toString(coalesce('objectRef.resource', objectRef.resource, objectRef_resource, ""))))
      | eval ns=trim(toString(coalesce('objectRef.namespace', objectRef.namespace, objectRef_namespace, "")))
      | eval actor=toString(coalesce('user.username', user.username, user_username, user__username, ""))
      | eval obj_name=toString(coalesce('objectRef.name', objectRef.name, objectRef_name, ""))
      | eval resp_code=tonumber(tostring(coalesce('responseStatus.code', responseStatus.code, responseStatus_code, "0")),10)
      | eval resp_reason=lower(toString(coalesce('responseStatus.reason', responseStatus.reason, responseStatus_reason, "")))
      | eval resp_msg=lower(toString(coalesce('responseStatus.message', responseStatus.message, responseStatus_message, "")))
      | where resp_code=403
      | where match(res_l, "^(secrets|nodes|configmaps)$") OR match(res_l, "^pods$") AND match(lower(toString(coalesce('objectRef.subresource', objectRef.subresource, ""))), "^(exec|attach|portforward)$")
      | where match(resp_reason, "forbidden") OR match(resp_msg, "forbidden|cannot|rbac|subjectaccessreview|not allowed")
      | eval signal_lane="rbac_denied_or_blocked_sensitive"
      | eval role_name=""
      | eval role_kind=""
      | eval object_uri=toString(coalesce(requestURI, requestUri, ""))
      | fields _time cluster actor ns obj_name res_l verb_l role_name role_kind signal_lane object_uri resp_code ]
    [ search index=k8s_audit sourcetype="kube:apiserver:audit" earliest=-24h@h latest=@h
      | eval cluster=lower(trim(toString(coalesce(k8s_cluster_name, cluster_name, cluster, eks_cluster_name, gke_cluster_name, aks_cluster_name, resource_cluster, ""))))
      | eval verb_l=lower(trim(toString(coalesce(verb, ""))))
      | eval res_l=lower(trim(toString(coalesce('objectRef.resource', objectRef.resource, objectRef_resource, ""))))
      | eval sub_l=lower(trim(toString(coalesce('objectRef.subresource', objectRef.subresource, objectRef_subresource, ""))))
      | eval ns=trim(toString(coalesce('objectRef.namespace', objectRef.namespace, objectRef_namespace, "")))
      | eval actor=toString(coalesce('user.username', user.username, user_username, user__username, ""))
      | eval obj_name=toString(coalesce('objectRef.name', objectRef.name, objectRef_name, ""))
      | eval uri=lower(toString(coalesce(requestURI, requestUri, "")))
      | eval prod_like=if(match(lower(ns), "(?i)prod|production|tier0|mission|prd-"), 1, 0)
      | where prod_like=1
      | where res_l="pods"
      | where match(sub_l, "^(exec|attach|portforward)$") OR match(uri, "/exec|portforward|/proxy/")
      | eval resp_code=tonumber(tostring(coalesce('responseStatus.code', responseStatus.code, responseStatus_code, "201")),10)
      | where resp_code>=200 AND resp_code<300
      | eval signal_lane="prod_pod_exec_proxy_success"
      | eval role_name=""
      | eval role_kind=""
      | eval object_uri=toString(coalesce(requestURI, requestUri, ""))
      | fields _time cluster actor ns obj_name res_l verb_l role_name role_kind signal_lane object_uri resp_code ]
    [ search index=k8s_audit sourcetype="kube:apiserver:audit" earliest=-24h@h latest=@h
      | eval cluster=lower(trim(toString(coalesce(k8s_cluster_name, cluster_name, cluster, eks_cluster_name, gke_cluster_name, aks_cluster_name, resource_cluster, ""))))
      | eval verb_l=lower(trim(toString(coalesce(verb, ""))))
      | eval res_l=lower(trim(toString(coalesce('objectRef.resource', objectRef.resource, objectRef_resource, ""))))
      | eval ns=trim(toString(coalesce('objectRef.namespace', objectRef.namespace, objectRef_namespace, "")))
      | eval actor=toString(coalesce('user.username', user.username, user_username, user__username, ""))
      | eval obj_name=toString(coalesce('objectRef.name', objectRef.name, objectRef_name, ""))
      | eval imp=toString(coalesce('impersonatedUser.username', impersonatedUser_username, impersonatedUser__username, ""))
      | where len(imp)>0
      | eval signal_lane="apiserver_impersonation_audit"
      | eval role_name=imp
      | eval role_kind="impersonated_user"
      | eval resp_code=tonumber(tostring(coalesce('responseStatus.code', responseStatus.code, responseStatus_code, "201")),10)
      | eval object_uri=toString(coalesce(requestURI, requestUri, ""))
      | fields _time cluster actor ns obj_name res_l verb_l role_name role_kind signal_lane object_uri resp_code ]
    [ search index=k8s_metrics sourcetype="prometheus:scrape:metrics" earliest=-4h@h latest=@h
      | eval cluster=lower(trim(toString(coalesce(k8s_cluster_name, cluster_name, cluster, eks_cluster_name, gke_cluster_name, aks_cluster_name, resource_cluster, ""))))
      | where match(_raw, "kube_clusterrole_binding") OR match(_raw, "kube_role_binding")
      | eval mn=lower(trim(toString(coalesce(__name__, metric_name, name, MetricName, ""))))
      | where like(mn, "%kube_%binding%") AND NOT like(mn, "%_created")
      | stats dc(_raw) AS ksm_binding_series_dc BY cluster _time
      | eval actor="kube_state_metrics"
      | eval ns=""
      | eval obj_name="kube_state_rbac_footprint"
      | eval res_l="metrics"
      | eval verb_l="scrape"
      | eval role_name=""
      | eval role_kind=""
      | eval signal_lane="ksm_rbac_binding_metric_tick"
      | eval object_uri="prometheus_kube_state_binding_family"
      | eval resp_code=0
      | fields _time cluster actor ns obj_name res_l verb_l role_name role_kind signal_lane object_uri resp_code ]
| eval user_key=lower(trim(toString(actor)))
| join type=left max=0 user_key [
    | inputlookup trusted_admin_users.csv
    | eval user_key=lower(trim(toString(coalesce(username, user, principal, breakglass_user, ""))))
    | eval lookup_cluster=lower(trim(toString(coalesce(cluster, k8s_cluster, "*"))))
    | eval trusted_suppress_raw=tonumber(tostring(coalesce(suppress_alerts, trusted_suppress_flag, "0")),10)
    | eval breakglass_note=toString(coalesce(notes, justification, ""))
    | fields user_key lookup_cluster trusted_suppress_raw breakglass_note ]
| eval cluster_row=coalesce(nullif(cluster,""), "unknown_cluster")
| eval lookup_match=if(isnotnull(lookup_cluster) AND (lookup_cluster="*" OR lookup_cluster=cluster_row), 1, 0)
| eval trusted_suppress=if(lookup_match=1 AND trusted_suppress_raw=1, 1, 0)
| join type=left max=1 actor [
    | tstats summariesonly=true count AS auth_model_events_24h FROM datamodel=Authentication WHERE nodename=Authentication earliest=-24h@h latest=@h BY Authentication.user
    | rename Authentication.user AS actor ]
| fillnull value=0 auth_model_events_24h trusted_suppress trusted_suppress_raw lookup_match
| eval prod_namespace=if(match(lower(ns), "(?i)prod|production|tier0|mission|prd-"), 1, 0)
| eventstats count AS signal_volume_24h BY cluster_row, signal_lane
| streamstats window=120 current=t global=f count AS stream_event_seq BY cluster_row, actor, signal_lane
| eval severity=case(
    signal_lane="sa_cluster_admin_bind", "critical",
    signal_lane="cluster_admin_binding_change" AND prod_namespace=1, "critical",
    signal_lane="cluster_admin_binding_change", "high",
    signal_lane="new_binding_non_system_sa" AND prod_namespace=1, "high",
    signal_lane="new_binding_non_system_sa", "medium",
    signal_lane="rbac_denied_or_blocked_sensitive" AND match(res_l, "^nodes$"), "high",
    signal_lane="rbac_denied_or_blocked_sensitive", "medium",
    signal_lane="prod_pod_exec_proxy_success", "high",
    signal_lane="apiserver_impersonation_audit", "high",
    signal_lane="ksm_rbac_binding_metric_tick", "low",
    true(), "medium")
| eval severity=if(trusted_suppress=1, "suppressed_trusted_actor", severity)
| where severity!="suppressed_trusted_actor"
| table _time cluster_row signal_lane severity actor ns obj_name res_l verb_l role_name role_kind resp_code object_uri signal_volume_24h auth_model_events_24h stream_event_seq
```

## CIM SPL

```spl
| tstats summariesonly=true count FROM datamodel=Authentication WHERE nodename=Authentication earliest=-24h@h latest=@h BY Authentication.user Authentication.action
| rename Authentication.user AS actor
| head 200
```

## Visualization

Severity-colored table mirroring the closing projection; timeline of signal_volume_24h by signal_lane; single-value tiles for critical versus high counts; drilldown from object_uri to raw audit JSON; companion panel for suppressed actors from a cloned search.

## Known False Positives

Legitimate platform administration during published change windows produces bursts of RoleBinding updates, cluster-admin elevations for etcd or apiserver recovery, and impersonation headers used by support tooling—correlate with tickets or trusted_admin_users.csv before paging. GitOps controllers such as Argo CD and Flux continuously reconcile RBAC manifests; volume spikes that align with git commits are expected, while divergent live bindings signal drift worth investigating. Break-glass accounts during incidents may temporarily bind cluster-admin; suppress only with time-bound lookup rows and owner notes. CI and CD pipeline service accounts often receive expanded RBAC during rollout windows; tie suppressions to pipeline identities rather than muting entire clusters. Vendor operators including Velero, cert-manager, ingress controllers, and OpenShift platform operators sometimes ship ClusterRoleBindings that appear alarming but are documented; maintain an operator exception inventory keyed by namespace and chart version. Node-bootstrap and kubeadm upgrade paths churn system:node and CSR-related bindings; treat short maintenance-adjacent windows as normal when node provisioning runbooks match timestamps. Fleet migrations from blanket cluster-admin to least-privilege roles create transient elevations and denials while workloads adapt; phase annotations in your lookup prevent false escalations. Pen testers and purple-team exercises will intentionally trigger forbidden responses; tag those namespaces in governance data. Regional cluster name collisions without proper cluster labels can mis-join suppressions—enforce unique cluster_row values in CSVs.

## References

- [Kubernetes — Using RBAC Authorization](https://kubernetes.io/docs/reference/access-authn-authz/rbac/)
- [Kubernetes — Auditing](https://kubernetes.io/docs/reference/access-authn-authz/audit/)
- [Aqua Security — kube-bench (CIS Kubernetes Benchmark checker)](https://github.com/aquasecurity/kube-bench)
- [NSA and CISA — Kubernetes Hardening Guidance](https://media.defense.gov/2022/Aug/29/2003066362/-1/-1/0/CTR_KUBERNETES_HARDENING_GUIDANCE_1.2_20220315.PDF)
- [BSI — Cloud Computing (Kubernetes guidance overview)](https://www.bsi.bund.de/EN/Themen/Unternehmen-und-Organisationen/Informationen-und-Empfehlungen/Empfehlungen-nach-Themen/Cloud-Computing/cloud_node.html)
- [MITRE ATT&CK — Containers Matrix](https://attack.mitre.org/matrices/enterprise/containers/)
- [CIS — Kubernetes Benchmark community page](https://www.cisecurity.org/benchmark/kubernetes)
