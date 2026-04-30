<!-- AUTO-GENERATED from UC-3.3.25.json — DO NOT EDIT -->

---
id: "3.3.25"
title: "OpenShift ClusterResourceQuota and AppliedClusterResourceQuota Multi-Project Enforcement Drift, Hierarchical Burn-Rate, and Quota-Selector Coverage Gaps"
status: "verified"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-3.3.25 · OpenShift ClusterResourceQuota and AppliedClusterResourceQuota Multi-Project Enforcement Drift, Hierarchical Burn-Rate, and Quota-Selector Coverage Gaps

> **Criticality:** Medium &middot; **Difficulty:** Advanced &middot; **Pillar:** Observability &middot; **Type:** Capacity, Configuration &middot; **Wave:** Walk &middot; **Status:** Verified

*We watch shared budget caps that span many team spaces on OpenShift, and we catch when labels stop matching so new work lands outside the cap, when one team hogs the shared pool, or when changes to limits skip the approval paper trail you rely on.*

---

## Description

Detects drift and hierarchical burn on OpenShift multi-project ClusterResourceQuota enforcement by correlating federated quota status, per-namespace AppliedClusterResourceQuota views, selector coverage gaps, admission denial storms, ticketed limit changes, and rolling burn windows that vanilla single-namespace ResourceQuota analytics do not model.

## Value

OpenShift ClusterResourceQuota Multi-Project Enforcement and Hierarchical Burn-Rate

## Implementation

Land ocp_clusterresourcequota_snapshot and ocp_acrq_snapshot on ocp_inventory, kube:events and ocp_audit denial lanes, and quota.openshift.io clusterresourcequota audit mutations; publish approved_quota_changes.csv and tenant_slo.csv; save openshift_uc_3_3_25_crq_hierarchical_burn every fifteen minutes over earliest=-24h@h; route critical and high rows to platform capacity governance; archive weekly evidence exports with lookup commit hashes.

## Evidence

Saved search openshift_uc_3_3_25_crq_hierarchical_burn with fifteen minute schedule; versioned approved_quota_changes.csv and tenant_slo.csv in git; weekly CSV exports to a restricted evidence index; dashboard drilldowns on ocp_inventory snapshots, kube:events, and ocp_audit lanes.

## Control test

### Positive scenario

In a lab OpenShift cluster, ingest ocp_clusterresourcequota_snapshot showing low cpu headroom, ingest ocp_acrq_snapshot with dom_ns_burn_pct above fifty percent for one namespace, ingest kube:events with exceeded quota messages naming the ClusterResourceQuota, ingest ocp_audit showing patch on quota.openshift.io clusterresourcequotas without a matching approved_quota_changes.csv row, and confirm openshift_uc_3_3_25_crq_hierarchical_burn returns critical or high with non-null recommended_action within the scheduled window.

### Negative scenario

After recovery when selectors align, parent and AppliedClusterResourceQuota totals match oc get within one interval, denial_rate falls below max_denials_hr, and ticketed changes populate approved_quota_changes.csv, confirm severities return to info and the alert wrapper emits zero rows when filtering to critical and high only per policy.

## Detailed Implementation

### Step 1 — Prerequisites

Head of Platform owns this control jointly with the OpenShift multi-tenant governance lead, the capacity engineers who translate ClusterResourceQuota hard limits into finance-backed budgets, the identity and automation engineers who operate ProjectRequest templates and namespace label baselines, and the observability staff who steward Splunk HTTP Event Collector tokens plus inventory exporters that watch quota.openshift.io objects. This use case isolates OpenShift cluster-scoped ClusterResourceQuota and AppliedClusterResourceQuota semantics: a ClusterResourceQuota object applies a single hard limit across many namespaces selected by label selectors or annotation selectors, while the apiserver materializes per-namespace AppliedClusterResourceQuota rows so tenants can read their slice of the shared budget without listing cluster-scoped objects. The clusterquota reconciliation controller maintains status.namespaces membership, compares observed usage against spec.hard, and must stay aligned with the quotaclusterresources admission plugin that denies pod and PVC creates when the aggregate would exceed the cluster-wide envelope. UC-3.2.4 remains namespace-scoped ResourceQuota exhaustion where one quota object governs only its namespace. UC-3.2.32 remains single-namespace ResourceQuota trending and linear forecasts without the federated selector plane. UC-3.2.36 remains LimitRange defaults and per-container maxima, not aggregate multi-project enforcement. UC-3.3.6 remains ClusterOperator availability storytelling rather than quota object inventories. Splunk becomes the ledger that joins periodic ClusterResourceQuota snapshots, AppliedClusterResourceQuota snapshots, ProjectRequest and namespace label audits, kube events and apiserver audit lines that carry exceeded quota narratives, openshift-controller-manager logs when collectors forward them, and governance lookups that tie quota_name to tenants, service owners, and approved change identifiers.

Index and permission design land before field extraction. Designate index=ocp_inventory for structured object exports with sourcetype=ocp_clusterresourcequota_snapshot flattening metadata.name, spec.selector.labels, spec.selector.annotations, status.namespaces with namespace name and used maps, status.total.used and status.total.hard for cpu, memory, requests.storage, persistentvolumeclaims, pods, services.loadbalancers, services.nodeports, secrets, configmaps, openshift-specific counts such as deploymentconfigs.apps.openshift.io, imagestreams.image.openshift.io, templates.template.openshift.io, and buildconfigs.build.openshift.io when your cluster exposes those resources in quota. Emit companion sourcetype=ocp_acrq_snapshot from oc get appliedclusterresourcequota across tenant namespaces or from a controller-friendly export that lists namespace, quota name, total used, and limits mirrored from the parent ClusterResourceQuota. Designate index=ocp_events for Kubernetes events with sourcetype=kube:events or sourcetype=ocp_events. Designate index=ocp_audit for apiserver audit with sourcetype=ocp_audit or sourcetype=kube:apiserver:audit capturing quota.openshift.io clusterresourcequotas mutations and Forbidden admission outcomes on pod and persistentvolumeclaims creates. Optional index=ocp_logs may carry openshift-controller-manager or cluster-policy-controller messages when your forwarder ships control-plane journals; filter for clusterquota or reconciliation errors explicitly to avoid drowning in unrelated noise. Issue distinct HEC tokens per environment with least privilege: platform capacity roles may search all sourcetypes; application teams receive redacted views that omit requestObject bodies when counsel requires minimization. Retention should cover at least thirty days hot for quarterly capacity attestations, ninety days when regulated customers require historical replay of quota denials, and align cold storage with enterprise logging policy. Legal review should confirm namespace names, tenant labels, and business unit annotations are acceptable in Splunk.

RBAC and safety: inventory jobs that run oc get clusterresourcequota, oc get appliedclusterresourcequota, oc get namespace, and oc get projects.config.openshift.io must use a dedicated ServiceAccount with get and list on those APIs, not long-lived kubeadmin kubeconfig files on administrator laptops. Admission denial replay searches must never grant application teams raw access to unrelated audit partitions. Governance lookups approved_quota_changes.csv and tenant_slo.csv live in git with commit hashes referenced in evidence exports so auditors can trace who approved limit motion.

Audit policy depth: capture Metadata at minimum for high-volume reads on namespaces; capture RequestResponse or Request on create, update, patch, and delete for clusterresourcequotas so analysts can compare spec.hard motion without fabricating fields. Include successful and forbidden outcomes for pod and PVC creates where responseStatus.message references exceeded quota and the quota name embedded after the colon. ProjectRequest auditing should record who requested a project and which template instantiated labels so Splunk can prove whether new namespaces inherited CRQ-matching labels.

Field normalization: flatten objectRef.apiGroup, objectRef.resource, objectRef.name, user.username, verb, responseStatus.code, responseStatus.message, impersonatedUser.username when present. Cluster identity must appear on every event as cluster, openshift_cluster, or cluster_name. For inventory snapshots, flatten crq_name, selector_label_json, selector_annotation_json, namespace_member_count, cpu_used_millicores, cpu_hard_millicores, memory_used_ki, memory_hard_ki, storage_used, storage_hard, acrq_namespace, acrq_used_cpu_millicores, acrq_hard_cpu_millicores, expect_crq_membership, matching_crq_count.

Risk briefing: legitimate platform maintenance edits ClusterResourceQuota objects during finance-approved raises; pair Splunk rows with approved_quota_changes.csv before paging executives. OpenShift upgrades may briefly shift controller reconciliation cadence; compare denial bursts to ClusterVersion history. GitOps controllers that rewrite quota objects can create rapid audit velocity that resembles an incident until you recognize the automation actor. Penetration tests may intentionally exhaust quotas; ingest pentest windows into lookup suppressions. Duplicate HEC shipments double denial counts; dedupe on audit auditID when present.

Differentiation recap: OpenShift ClusterResourceQuota and AppliedClusterResourceQuota multi-project selector plane, hierarchical burn across namespaces, reconciliation and admission coupling, ProjectRequest template label coupling, and audit-backed governance joins, not vanilla single-namespace ResourceQuota analytics, not LimitRange enforcement, not ClusterOperator health alone.

Operational posture: maintain approved_quota_changes.csv with columns cluster, quota_name, change_ticket_id, approver, effective_epoch, and notes. Maintain tenant_slo.csv with cluster, quota_name, tenant, business_owner, slo_pct, max_denials_hr, and optional annotation_match_expected for governance tests. Document which projects.config.openshift.io cluster projectRequestTemplate object your cluster uses and store the template namespace or name hash in inventory so Splunk can correlate missing labels to template drift.

### Step 2 — Configure data collection

Stand up four complementary lanes Splunk multisearch can fuse: periodic ClusterResourceQuota snapshots with status.total used versus hard and namespace membership counts, AppliedClusterResourceQuota and namespace membership exports that highlight selector gaps and overlap counts, kube events plus optional audit replay for Forbidden exceeded quota messages tied to CRQ names, and apiserver audit focused on quota.openshift.io clusterresourcequotas verbs joined to approved change metadata.

ClusterResourceQuota snapshot lane: schedule a utility every five to fifteen minutes from a management host with kubeconfig authentication. The utility should run oc get clusterresourcequota -o json, flatten each item into one HEC JSON event per object or per cluster depending on volume caps, map status.total.used and status.total.hard into millicores and KiB consistently, count len(status.namespaces) when present, serialize spec.selector.matchLabels and matchExpressions into stable JSON strings for hash comparisons, and emit sourcetype=ocp_clusterresourcequota_snapshot into index=ocp_inventory with source=oc_get_clusterresourcequota. Include a sha256 hash of canonical JSON without volatile resourceVersion when tamper evidence is required.

AppliedClusterResourceQuota snapshot lane: schedule oc get appliedclusterresourcequota -A -o json or namespace-scoped exports for regulated tenants, flatten namespace, name, total used, limits mirrored from parent, and optional parent reference fields your OpenShift minor exposes. Emit sourcetype=ocp_acrq_snapshot with acrq_used_cpu_millicores, acrq_hard_cpu_millicores, crq_total_used_cpu_millicores when you join parent totals from the ClusterResourceQuota export in the same job, expect_crq_membership from your CMDB lookup injection, matching_crq_count when the exporter evaluates how many ClusterResourceQuota selectors include the namespace labels, and overlap flags when more than one parent matches.

Events and denial lane: forward Kubernetes events into index=ocp_events with sourcetype=kube:events using Splunk Connect for Kubernetes patterns, Splunk Add-on for Kubernetes, or OpenTelemetry k8s_events receiver. Ensure message text retains exceeded quota substrings. Optionally mirror the same denials from kube-apiserver audit with sourcetype=kube:apiserver:audit where responseStatus.code is 403 and responseStatus.message references forbidden and exceeded quota.

Audit mutation lane: ship kube-apiserver audit into index=ocp_audit with sourcetype=ocp_audit. Filter at search time for objectRef.apiGroup quota.openshift.io and objectRef.resource clusterresourcequotas with verbs in create, update, patch, delete. Preserve user.username, user.groups, and requestObject metadata when policy permits so Splunk can join actors to change tickets.

ProjectRequest and template validation lane: export projects.config.openshift.io cluster objects and Template instances used by oc adm create-bootstrap-project-template so Splunk can test whether default labels align with ClusterResourceQuota label selectors. Emit sourcetype=ocp_projectconfig_snapshot sparingly when governance requires explicit coupling proof.

Controller log lane optional: forward openshift-controller-manager logs when your observability standard mandates textual reconciliation errors; tag lines containing clusterquota or reconciliation failure tokens. Keep volume bounded with drop rules for chatty info logs.

Example oc verification operators run during design reviews:

```bash
oc get clusterresourcequota -o wide
oc describe clusterresourcequota tenant-alpha-pool
oc get appliedclusterresourcequota -n dev-team-one -o yaml
oc get projects.config.openshift.io cluster -o yaml
oc adm create-bootstrap-project-template -o yaml | grep -E 'metadata:|labels:|annotations:' -n
```

props.conf guidance: TRUNCATE sufficiently large for JSON exports, TIMESTAMP_FIELDS respected when HEC time is authoritative, LINE_BREAKER for newline-delimited JSON, FIELDALIAS maps from dotted API paths to underscore fields used in SPL coalesce ladders.

Pre-save validation: index=ocp_inventory sourcetype=ocp_clusterresourcequota_snapshot earliest=-1h must return non-zero counts after the first interval; ocp_acrq_snapshot must list at least one namespace in non-empty clusters; kube:events should show synthetic test denials after a controlled quota drill in lab; ocp_audit must show clusterresourcequotas verbs during intentional oc edit clusterresourcequota in lab under change control.

Dashboards: host a severity-colored table keyed on cluster, crq_name, and namespace with drilldowns to raw snapshot JSON, events, audit rows, and lookup matches. Pair panels with timechart of denial_rate and with headroom gauges for cpu and memory totals.

Volume controls: if RequestResponse audit is too heavy, keep RequestResponse for quota.openshift.io clusterresourcequotas only and use Metadata elsewhere, following OpenShift audit profile documentation.

### Step 3 — Create the search and alert

Save the SPL as openshift_uc_3_3_25_crq_hierarchical_burn with a fifteen minute schedule during steady-state production, dispatch earliest=-24h@h, dispatch latest=now, and alert when severity is critical, high, or medium per your routing matrix. Throttle duplicate cluster, crq_name, namespace, signal_lane rows for forty-five minutes unless severity escalates. Include recommended_action, denial_rate, cpu_headroom_pct, and dom_ns_burn_pct in pager descriptions so incident commanders open quota runbooks without re-running ad hoc searches.

Pipeline narrative for reviewers: multisearch fans ClusterResourceQuota status, AppliedClusterResourceQuota coverage hints, admission denial events, and audited CRQ mutations with an embedded join to approved_quota_changes.csv so unauthorized spec.hard motion surfaces immediately. coalesce() absorbs flattened versus dotted JSON field naming drift across exporters. streamstats with time_window implements one hour, six hour, and twenty four hour rolling windows on aggregate CPU millicores for hierarchical burn and saturation projection. eventstats adds fleet denial counts per cluster for capacity stand-ups. A join wraps tenant_slo.csv for tenant, business_owner, and max_denials_hr so denial_rate compares to a numeric hourly budget. case() maps selector gaps, overlap, AppliedClusterResourceQuota divergence hints, low headroom, dominant namespace burn above fifty percent of shared CPU hard limits, audit mutations without tickets, and denial storms into severity tiers. recommended_action encodes oc get clusterresourcequota, oc get appliedclusterresourcequota, oc describe namespace, template diff, and finance ticket steps without pretending Splunk replaces oc.

Fenced SPL must match the spl JSON field exactly:

```spl
`comment("UC-3.3.25 OpenShift ClusterResourceQuota plane — CRQ total used versus hard headroom, selector coverage with ACRQ delta hints, admission exceeded quota denials, audit mutations join approved_quota_changes. Tunables: earliest=-24h@h latest=now")`
| multisearch
    [ search index=ocp_inventory sourcetype=ocp_clusterresourcequota_snapshot earliest=-24h@h latest=now
      | eval cluster=lower(trim(toString(coalesce(cluster, openshift_cluster, cluster_name, k8s_cluster_name, ""))))
      | eval crq_name=trim(toString(coalesce(crq_name, clusterresourcequota_name, metadata_name, name, object_name, "")))
      | eval total_used_cpu_m=tonumber(trim(toString(coalesce(status_total_used_cpu_millicores, used_cpu_millicores, total_used_cpu_m, "0"))),10)
      | eval total_hard_cpu_m=tonumber(trim(toString(coalesce(status_total_hard_cpu_millicores, hard_cpu_millicores, total_hard_cpu_m, "0"))),10)
      | eval total_used_mem_ki=tonumber(trim(toString(coalesce(status_total_used_memory_ki, used_memory_ki, "0"))),10)
      | eval total_hard_mem_ki=tonumber(trim(toString(coalesce(status_total_hard_memory_ki, hard_memory_ki, "0"))),10)
      | eval ns_member_cnt=tonumber(trim(toString(coalesce(status_namespace_count, namespaces_selected, "0"))),10)
      | eval signal_lane="crq_status_headroom"
      | eval namespace="CRQ_AGGREGATE"
      | eval denial_flag=0
      | eval audit_verb=""
      | eval acrq_delta_hint=0
      | eval selector_gap=0
      | eval overlap_ns=0
      | eval change_ticket_id=""
      | eval approved_change=0
      | fields _time cluster crq_name signal_lane namespace total_used_cpu_m total_hard_cpu_m total_used_mem_ki total_hard_mem_ki ns_member_cnt denial_flag audit_verb acrq_delta_hint selector_gap overlap_ns change_ticket_id approved_change ]
    [ search index=ocp_inventory sourcetype=ocp_acrq_snapshot earliest=-24h@h latest=now
      | eval cluster=lower(trim(toString(coalesce(cluster, openshift_cluster, cluster_name, ""))))
      | eval crq_name=trim(toString(coalesce(crq_name, clusterresourcequota_name, quota_name, "")))
      | eval namespace=trim(toString(coalesce(namespace, metadata_namespace, ns, "")))
      | eval total_used_cpu_m=tonumber(trim(toString(coalesce(acrq_used_cpu_millicores, used_cpu_millicores, "0"))),10)
      | eval crq_status_used_cpu_m=tonumber(trim(toString(coalesce(crq_total_used_cpu_millicores, parent_crq_used_cpu_m, "0"))),10)
      | eval total_hard_cpu_m=tonumber(trim(toString(coalesce(acrq_hard_cpu_millicores, hard_cpu_millicores, "0"))),10)
      | eval total_used_mem_ki=tonumber(trim(toString(coalesce(acrq_used_memory_ki, "0"))),10)
      | eval total_hard_mem_ki=tonumber(trim(toString(coalesce(acrq_hard_memory_ki, "0"))),10)
      | eval acrq_delta_hint=if(crq_status_used_cpu_m>0 AND abs(total_used_cpu_m - crq_status_used_cpu_m)>(crq_status_used_cpu_m*0.15),1,0)
      | eval crq_overlap_cnt=tonumber(trim(toString(coalesce(matching_crq_count, crq_overlap_count, "0"))),10)
      | eval expect_crq=lower(trim(toString(coalesce(expect_crq_membership, sla_expects_crq, "false"))))
      | eval selector_gap=if(match(expect_crq,"true|1") AND len(crq_name)<1,1,0)
      | eval overlap_ns=if(crq_overlap_cnt>1,1,0)
      | eval ns_member_cnt=crq_overlap_cnt
      | eval signal_lane="selector_coverage_acrq"
      | eval denial_flag=0
      | eval audit_verb=""
      | eval change_ticket_id=""
      | eval approved_change=0
      | fields _time cluster crq_name signal_lane namespace total_used_cpu_m total_hard_cpu_m total_used_mem_ki total_hard_mem_ki ns_member_cnt denial_flag audit_verb acrq_delta_hint selector_gap overlap_ns change_ticket_id approved_change ]
    [ search (index=ocp_events OR index=openshift) (sourcetype=kube:events OR sourcetype=ocp_events) earliest=-24h@h latest=now
      | eval cluster=lower(trim(toString(coalesce(cluster, openshift_cluster, cluster_name, ""))))
      | eval msg=lower(toString(coalesce(message, Message, _raw, "")))
      | eval reason=trim(toString(coalesce(reason, Reason, "")))
      | where (reason="FailedCreate" OR like(reason,"%Failed%")) AND like(msg,"%exceeded quota%")
      | rex field=msg max_match=0 "(?i)exceeded quota\\:\\s*(?<crq_hit>[a-z0-9][a-z0-9._-]*)"
      | eval crq_name=trim(toString(coalesce(crq_hit, "unknown_crq")))
      | eval namespace=trim(toString(coalesce(metadata_namespace, namespace, involvedObject_namespace, "")))
      | eval signal_lane="crq_admission_denial"
      | eval denial_flag=1
      | eval total_used_cpu_m=0
      | eval total_hard_cpu_m=0
      | eval total_used_mem_ki=0
      | eval total_hard_mem_ki=0
      | eval ns_member_cnt=0
      | eval audit_verb=""
      | eval acrq_delta_hint=0
      | eval selector_gap=0
      | eval overlap_ns=0
      | eval change_ticket_id=""
      | eval approved_change=0
      | fields _time cluster crq_name signal_lane namespace total_used_cpu_m total_hard_cpu_m total_used_mem_ki total_hard_mem_ki ns_member_cnt denial_flag audit_verb acrq_delta_hint selector_gap overlap_ns change_ticket_id approved_change ]
    [ search (index=ocp_audit OR index=k8s_audit) (sourcetype=ocp_audit OR sourcetype=k8s_audit OR sourcetype="kube:apiserver:audit") earliest=-24h@h latest=now
      | eval cluster=lower(trim(toString(coalesce(cluster, openshift_cluster, cluster_name, k8s_cluster_name, ""))))
      | eval apig=lower(trim(toString(coalesce('objectRef.apiGroup', objectRef_apiGroup, objectRef.apigroup, ""))))
      | eval res=lower(trim(toString(coalesce('objectRef.resource', objectRef.resource, objectRef_resource, ""))))
      | eval verb=lower(trim(toString(coalesce(verb, requestVerb, request_verb, ""))))
      | where match(apig,"quota.openshift.io") AND match(res,"clusterresourcequotas") AND match(verb,"create|update|patch|delete")
      | eval crq_name=trim(toString(coalesce('objectRef.name', objectRef.name, objectRef_name, "")))
      | eval namespace="cluster_scope"
      | eval signal_lane="crq_audit_change"
      | eval audit_verb=verb
      | eval denial_flag=0
      | eval total_used_cpu_m=0
      | eval total_hard_cpu_m=0
      | eval total_used_mem_ki=0
      | eval total_hard_mem_ki=0
      | eval ns_member_cnt=0
      | eval acrq_delta_hint=0
      | eval selector_gap=0
      | eval overlap_ns=0
      | join type=left max=0 cluster crq_name
          [| inputlookup approved_quota_changes.csv
           | eval cluster=lower(trim(toString(cluster)))
           | eval crq_name=trim(toString(coalesce(quota_name, crq_name, "")))
           | eval change_ticket_id=trim(toString(coalesce(change_ticket_id, ticket, "")))
           | eval approved_change=if(len(change_ticket_id)>3,1,0)
           | fields cluster crq_name change_ticket_id approved_change ]
      | fields _time cluster crq_name signal_lane namespace total_used_cpu_m total_hard_cpu_m total_used_mem_ki total_hard_mem_ki ns_member_cnt denial_flag audit_verb acrq_delta_hint selector_gap overlap_ns change_ticket_id approved_change ]
| fillnull value=0 denial_flag acrq_delta_hint selector_gap overlap_ns approved_change
| fillnull value="" change_ticket_id audit_verb
| eval cpu_headroom_pct=if(total_hard_cpu_m>0 AND signal_lane=="crq_status_headroom", round(100.0*(total_hard_cpu_m-total_used_cpu_m)/total_hard_cpu_m,3), null())
| eval dom_ns_burn_pct=if(total_hard_cpu_m>0 AND signal_lane=="selector_coverage_acrq", round(100.0*total_used_cpu_m/total_hard_cpu_m,3), null())
| eval snap_cpu=if(signal_lane=="crq_status_headroom", total_used_cpu_m, null())
| sort 0 cluster crq_name _time
| streamstats time_window=3600 window=100000 global=f current=t first(snap_cpu) AS e1h last(snap_cpu) AS l1h BY cluster crq_name
| streamstats time_window=21600 window=100000 global=f current=t first(snap_cpu) AS e6h last(snap_cpu) AS l6h BY cluster crq_name
| streamstats time_window=86400 window=100000 global=f current=t first(snap_cpu) AS e24h last(snap_cpu) AS l24h BY cluster crq_name
| eval burn_1h=round(coalesce(l1h,0)-coalesce(e1h,0),2)
| eval burn_6h=round(coalesce(l6h,0)-coalesce(e6h,0),2)
| eval burn_24h=round(coalesce(l24h,0)-coalesce(e24h,0),2)
| eval slope_m_per_s=if(burn_6h!=0, burn_6h/21600.0, 0)
| eval sec_to_sat=if(signal_lane=="crq_status_headroom" AND slope_m_per_s>0 AND total_hard_cpu_m>total_used_cpu_m, round((total_hard_cpu_m-total_used_cpu_m)/slope_m_per_s,0), null())
| streamstats time_window=3600 window=100000 global=f current=t sum(denial_flag) AS denial_rate BY cluster crq_name
| eventstats sum(denial_flag) AS fleet_denials BY cluster
| join type=left max=0 cluster crq_name
    [| inputlookup tenant_slo.csv
     | eval cluster=lower(trim(toString(cluster)))
     | eval crq_name=trim(toString(coalesce(quota_name, crq_name, "")))
     | eval tenant=trim(toString(coalesce(tenant, business_unit, "")))
     | eval slo_pct=tonumber(trim(toString(coalesce(slo_pct, denial_budget_pct, "0.02"))),10)
     | eval business_owner=trim(toString(coalesce(business_owner, owner, "")))
     | eval max_denials_hr=tonumber(trim(toString(coalesce(max_denials_hr, max_denials_per_hour, "10"))),10)
     | fields cluster crq_name tenant slo_pct business_owner max_denials_hr ]
| fillnull value=10 max_denials_hr
| eval slo_breach=if(denial_rate>max_denials_hr,1,0)
| eval ticket_ok=approved_change
| eval severity=case(
    selector_gap==1 OR overlap_ns==1, "critical",
    acrq_delta_hint==1 AND signal_lane=="selector_coverage_acrq", "high",
    denial_rate>=10 AND slo_breach==1, "high",
    isnotnull(cpu_headroom_pct) AND cpu_headroom_pct<=5 AND signal_lane=="crq_status_headroom", "high",
    isnotnull(dom_ns_burn_pct) AND dom_ns_burn_pct>=50, "high",
    signal_lane=="crq_audit_change" AND ticket_ok==0 AND match(audit_verb,"patch|update|delete"), "high",
    denial_rate>=3, "medium",
    isnotnull(sec_to_sat) AND sec_to_sat>0 AND sec_to_sat<86400 AND signal_lane=="crq_status_headroom", "medium",
    true(), "info")
| eval recommended_action=case(
    selector_gap==1, "fix_namespace_labels_or_project_template_to_match_crq_selector",
    overlap_ns==1, "dedupe_crq_selectors_and_split_tenant_scopes",
    acrq_delta_hint==1, "compare_oc_get_appliedclusterresourcequota_to_clusterresourcequota_status",
    denial_rate>=3, "raise_shared_limits_or_right_size_workloads_under_crq",
    signal_lane=="crq_audit_change" AND ticket_ok==0, "backfill_change_ticket_review_audit_actor",
    true(), "correlate_inventory_events_audit_and_refresh_snapshots")
| table _time cluster tenant crq_name namespace signal_lane cpu_headroom_pct dom_ns_burn_pct burn_1h burn_6h burn_24h sec_to_sat denial_rate max_denials_hr slo_breach ticket_ok change_ticket_id severity recommended_action fleet_denials business_owner audit_verb acrq_delta_hint selector_gap overlap_ns
```

savedsearches.conf sketch:

```ini
[openshift_uc_3_3_25_crq_hierarchical_burn_alert]
cron_schedule = */15 * * * *
dispatch.earliest_time = -24h@h
dispatch.latest_time = now
enableSched = 1
action.email = 1
action.email.to = openshift-platform-capacity@example.com
action.email.subject = OCP CRQ governance $result.severity$ $result.cluster$ $result.crq_name$
counttype = number of events
relation = greater than
quantity = 0
search = | savedsearch openshift_uc_3_3_25_crq_hierarchical_burn | where severity IN ("critical","high","medium")
```

Performance: if Job Inspector shows multisearch queue time above internal service level objectives, materialize ocp_clusterresourcequota_snapshot hourly into a summary index keyed on cluster and crq_name, widen alert windows to earliest=-6h@h on summaries, and retain this full search for investigations.

### Step 4 — Validate

Ground truth always starts on-cluster. For Splunk cpu_headroom_pct rows, run oc describe clusterresourcequota name and compare status.total.used and status.total.hard to snapshot fields. When statuses disagree, verify resourceVersion freshness, indexer clock skew, and duplicate cluster labels across regions before blaming parsers.

AppliedClusterResourceQuota divergence: pick a high acrq_delta_hint row, run oc get appliedclusterresourcequota -n namespace -o yaml and compare totals to the parent ClusterResourceQuota status within the same minute. If deltas persist beyond one reconciliation interval, capture openshift-controller-manager logs and apiserver latency.

Selector gap validation: choose a namespace flagged selector_gap=1, run oc get namespace -o yaml, compare labels and annotations to spec.selector on the governing ClusterResourceQuota, and replay ProjectRequest audit to see which template version applied labels.

Overlap validation: when overlap_ns=1, enumerate ClusterResourceQuota objects whose selectors include the namespace and confirm whether multiple matches are intentional for phased migrations or accidental copy-paste drift.

Admission denial validation: reproduce a lab pod create that exceeds shared CPU or pod counts, confirm kube:events and audit Forbidden lines include the quota name Splunk extracted, then clear the test workload.

Audit mutation validation: under ticketed change control, patch a non-production ClusterResourceQuota hard limit, confirm ocp_audit rows include user.username and verb, confirm approved_quota_changes.csv join sets approved_change=1 when ticket identifiers match, then revert.

Governance negative test: remove a deliberate unauthorized edit scenario in lab and confirm high severity rows disappear when only ticketed changes occur.

Clock skew test: indexer time within thirty seconds of apiserver; otherwise streamstats time_window ordering mis-estimates burn.

Parser drift test: after OpenShift minor upgrades, validate FIELDALIAS rules still map dotted audit fields into objectRef_resource style aliases used by coalesce ladders.

### Step 5 — Operationalize & Troubleshoot

Case 1 — Selector label drift leaves new projects outside every ClusterResourceQuota: When it triggers: Splunk shows selector_gap=1 on namespaces where expect_crq_membership is true while crq_name is empty or membership lists omit the namespace. What to investigate: compare Namespace labels to ClusterResourceQuota spec.selector.matchLabels, review ProjectRequest audit actors, and open the live ProjectRequest template to see default labels. Who to involve: Head of Platform, tenant service owner, and the GitOps engineer who owns namespace factories. How to remediate: add required labels through template or mutating automation, or adjust selector keys with finance approval and a ticketed ClusterResourceQuota change. How to validate: oc get namespace labels match selectors, ocp_acrq_snapshot lists the namespace under the intended crq_name within one collection interval, and Splunk clears selector_gap for two consecutive windows.

Case 2 — Two ClusterResourceQuota objects unintentionally select the same namespace: When it triggers: overlap_ns=1 with matching_crq_count above one on ocp_acrq_snapshot rows. What to investigate: enumerate selectors on both ClusterResourceQuota objects, determine whether annotations or labels widened during a migration, and check for duplicate automation commits. Who to involve: multi-tenant governance lead and both tenant owners attached to the competing quotas. How to remediate: narrow selectors, split namespaces, or consolidate quotas under one parent object with finance sign-off. How to validate: oc get appliedclusterresourcequota shows a single authoritative parent per namespace intent, matching_crq_count returns to one, and Splunk overlap_ns clears.

Case 3 — AppliedClusterResourceQuota totals diverge from ClusterResourceQuota status: When it triggers: acrq_delta_hint=1 persists beyond a short reconciliation window. What to investigate: apiserver watch latency, overloaded openshift-controller-manager, and partial snapshot jobs that read objects at different seconds. Who to involve: OpenShift platform SRE and observability engineers forwarding inventory jobs. How to remediate: align exporter timestamps, increase job cadence during incidents, restart unhealthy controllers only under vendor guidance. How to validate: oc get outputs converge, delta hints return to zero, and audit shows healthy admission without spurious denies.

Case 4 — One namespace consumes more than half of a shared CPU hard limit while siblings starve: When it triggers: dom_ns_burn_pct>=50 on selector_coverage_acrq rows with elevated denial_rate on siblings. What to investigate: pod density, buggy horizontal pod autoscaler loops, batch jobs without requests, and missing requests that skew scheduling. Who to involve: application owner for the hot namespace and capacity engineering. How to remediate: right-size workloads, split tenants into separate ClusterResourceQuota pools, or raise hard limits with finance approval. How to validate: per-namespace used CPU falls under policy share, sibling namespaces resume creates, and denial_rate decays toward zero.

Case 5 — Cluster-wide hard limit headroom under five percent on CPU or memory: When it triggers: cpu_headroom_pct<=5 on crq_status_headroom rows. What to investigate: growth trend across all member namespaces, upcoming releases, and storage or pod count dimensions that often hit before CPU. Who to involve: Head of Platform and finance-backed capacity council. How to remediate: pre-approve raises, offload workloads, or enforce requests reductions before hard denial storms. How to validate: headroom rises above policy buffer or approved_exception metadata is present on HEC events, and sec_to_sat projections lengthen beyond alert thresholds.

Case 6 — ProjectRequest template omits labels expected by ClusterResourceQuota selectors: When it triggers: new namespaces consistently miss membership while legacy namespaces remain covered. What to investigate: projects.config.openshift.io cluster projectRequestTemplate reference, Template object parameters, and admission mutating webhooks that should stamp labels. Who to involve: platform automation lead and identity engineers operating project provisioning. How to remediate: update the bootstrap template with required labels, backfill existing namespaces under change control, document tenant onboarding steps. How to validate: synthetic ProjectRequest in lab inherits labels, Splunk selector_gap stays zero for new namespaces, and audit shows template version correlation.

Case 7 — CRQ spec.hard changes without an approved change ticket: When it triggers: crq_audit_change rows with patch, update, or delete verbs and ticket_ok=0 after the approved_quota_changes.csv join. What to investigate: user.username, break-glass procedures, automation service accounts, and GitOps repository commits outside merge windows. Who to involve: platform security delegate and change advisory board liaison. How to remediate: open retroactive tickets when legitimate, revert unauthorized edits, rotate credentials if automation leaked. How to validate: approved_change=1 on subsequent joins, finance records match Splunk timelines, and severities return toward info.

Case 8 — Admission denial storm exceeds tenant hourly budget: When it triggers: denial_rate above max_denials_hr from tenant_slo.csv with slo_breach=1. What to investigate: failing deployments, PVC churn, services.loadbalancers growth, and clusterquota admission plugin messages referencing specific resources. Who to involve: tenant on-call and network or storage SMEs when load balancer or PVC dimensions spike. How to remediate: unblock by raising the right dimension, fixing buggy controllers, or shifting workloads across CRQ pools. How to validate: kube:events denial volume drops, applications schedule successfully, and denial_rate falls below budget for two windows.

Case 9 — Linear saturation projection predicts exhaustion within twenty four hours: When it triggers: sec_to_sat<86400 on crq_status_headroom rows with positive six hour burn slope. What to investigate: verify slope stability, rule out one-off batch jobs, and compare memory or pod count dimensions that may saturate first. Who to involve: capacity engineering and affected tenant owners. How to remediate: schedule raises, throttle non-critical work, or rebalance namespaces. How to validate: projection resets beyond policy horizon after mitigation or finance approves a timed exception logged in lookups.

Case 10 — Inventory exporter lag misreports membership: When it triggers: snapshot timestamps trail live oc get by multiple intervals while incidents rely on Splunk. What to investigate: kubeconfig expiry, network partitions, and job concurrency locks. Who to involve: observability engineers operating the exporter fleet. How to remediate: renew credentials, shard exporters per region, backoff and alert on missed heartbeats. How to validate: _time deltas between inventory and apiserver stay within one collection interval.

Case 11 — Duplicate telemetry inflates denial_rate: When it triggers: denial counts exceed apiserver reality in lab comparisons. What to investigate: redundant kube_events forwarders, duplicated cluster labels, and replayed files. Who to involve: Splunk platform administrators. How to remediate: dedupe on involvedObject uid or audit auditID, remove duplicate inputs. How to validate: Splunk denial_rate matches manual counts from oc get events sampling.

Case 12 — Healthy steady state confirmation after remediation: When it triggers: post-change verification windows require proof of quiet. What to investigate: confirm no critical or high rows for mission clusters across two scheduled runs, spot-check oc get clusterresourcequota against Splunk headroom fields. Who to involve: platform capacity owner and audit sampling partner. How to remediate: none if healthy beyond documentation updates. How to validate: alert wrapper returns zero rows when filtered to critical and high per policy, and evidence exports archive with lookup commit hashes.

Closing checklist: five em-dash step headers are present; Step 3 fenced SPL matches the spl field exactly; multisearch lists CRQ status, selector and AppliedClusterResourceQuota hints, admission denials, and audited CRQ changes; join wraps approved_quota_changes.csv inside the audit arm and tenant_slo.csv after fan-in; coalesce, streamstats, eventstats, and case appear; closing table includes at least ten columns for analyst review including tenant, business_owner, denial_rate, headroom, burn windows, and governance flags.


## SPL

```spl
`comment("UC-3.3.25 OpenShift ClusterResourceQuota plane — CRQ total used versus hard headroom, selector coverage with ACRQ delta hints, admission exceeded quota denials, audit mutations join approved_quota_changes. Tunables: earliest=-24h@h latest=now")`
| multisearch
    [ search index=ocp_inventory sourcetype=ocp_clusterresourcequota_snapshot earliest=-24h@h latest=now
      | eval cluster=lower(trim(toString(coalesce(cluster, openshift_cluster, cluster_name, k8s_cluster_name, ""))))
      | eval crq_name=trim(toString(coalesce(crq_name, clusterresourcequota_name, metadata_name, name, object_name, "")))
      | eval total_used_cpu_m=tonumber(trim(toString(coalesce(status_total_used_cpu_millicores, used_cpu_millicores, total_used_cpu_m, "0"))),10)
      | eval total_hard_cpu_m=tonumber(trim(toString(coalesce(status_total_hard_cpu_millicores, hard_cpu_millicores, total_hard_cpu_m, "0"))),10)
      | eval total_used_mem_ki=tonumber(trim(toString(coalesce(status_total_used_memory_ki, used_memory_ki, "0"))),10)
      | eval total_hard_mem_ki=tonumber(trim(toString(coalesce(status_total_hard_memory_ki, hard_memory_ki, "0"))),10)
      | eval ns_member_cnt=tonumber(trim(toString(coalesce(status_namespace_count, namespaces_selected, "0"))),10)
      | eval signal_lane="crq_status_headroom"
      | eval namespace="CRQ_AGGREGATE"
      | eval denial_flag=0
      | eval audit_verb=""
      | eval acrq_delta_hint=0
      | eval selector_gap=0
      | eval overlap_ns=0
      | eval change_ticket_id=""
      | eval approved_change=0
      | fields _time cluster crq_name signal_lane namespace total_used_cpu_m total_hard_cpu_m total_used_mem_ki total_hard_mem_ki ns_member_cnt denial_flag audit_verb acrq_delta_hint selector_gap overlap_ns change_ticket_id approved_change ]
    [ search index=ocp_inventory sourcetype=ocp_acrq_snapshot earliest=-24h@h latest=now
      | eval cluster=lower(trim(toString(coalesce(cluster, openshift_cluster, cluster_name, ""))))
      | eval crq_name=trim(toString(coalesce(crq_name, clusterresourcequota_name, quota_name, "")))
      | eval namespace=trim(toString(coalesce(namespace, metadata_namespace, ns, "")))
      | eval total_used_cpu_m=tonumber(trim(toString(coalesce(acrq_used_cpu_millicores, used_cpu_millicores, "0"))),10)
      | eval crq_status_used_cpu_m=tonumber(trim(toString(coalesce(crq_total_used_cpu_millicores, parent_crq_used_cpu_m, "0"))),10)
      | eval total_hard_cpu_m=tonumber(trim(toString(coalesce(acrq_hard_cpu_millicores, hard_cpu_millicores, "0"))),10)
      | eval total_used_mem_ki=tonumber(trim(toString(coalesce(acrq_used_memory_ki, "0"))),10)
      | eval total_hard_mem_ki=tonumber(trim(toString(coalesce(acrq_hard_memory_ki, "0"))),10)
      | eval acrq_delta_hint=if(crq_status_used_cpu_m>0 AND abs(total_used_cpu_m - crq_status_used_cpu_m)>(crq_status_used_cpu_m*0.15),1,0)
      | eval crq_overlap_cnt=tonumber(trim(toString(coalesce(matching_crq_count, crq_overlap_count, "0"))),10)
      | eval expect_crq=lower(trim(toString(coalesce(expect_crq_membership, sla_expects_crq, "false"))))
      | eval selector_gap=if(match(expect_crq,"true|1") AND len(crq_name)<1,1,0)
      | eval overlap_ns=if(crq_overlap_cnt>1,1,0)
      | eval ns_member_cnt=crq_overlap_cnt
      | eval signal_lane="selector_coverage_acrq"
      | eval denial_flag=0
      | eval audit_verb=""
      | eval change_ticket_id=""
      | eval approved_change=0
      | fields _time cluster crq_name signal_lane namespace total_used_cpu_m total_hard_cpu_m total_used_mem_ki total_hard_mem_ki ns_member_cnt denial_flag audit_verb acrq_delta_hint selector_gap overlap_ns change_ticket_id approved_change ]
    [ search (index=ocp_events OR index=openshift) (sourcetype=kube:events OR sourcetype=ocp_events) earliest=-24h@h latest=now
      | eval cluster=lower(trim(toString(coalesce(cluster, openshift_cluster, cluster_name, ""))))
      | eval msg=lower(toString(coalesce(message, Message, _raw, "")))
      | eval reason=trim(toString(coalesce(reason, Reason, "")))
      | where (reason="FailedCreate" OR like(reason,"%Failed%")) AND like(msg,"%exceeded quota%")
      | rex field=msg max_match=0 "(?i)exceeded quota\\:\\s*(?<crq_hit>[a-z0-9][a-z0-9._-]*)"
      | eval crq_name=trim(toString(coalesce(crq_hit, "unknown_crq")))
      | eval namespace=trim(toString(coalesce(metadata_namespace, namespace, involvedObject_namespace, "")))
      | eval signal_lane="crq_admission_denial"
      | eval denial_flag=1
      | eval total_used_cpu_m=0
      | eval total_hard_cpu_m=0
      | eval total_used_mem_ki=0
      | eval total_hard_mem_ki=0
      | eval ns_member_cnt=0
      | eval audit_verb=""
      | eval acrq_delta_hint=0
      | eval selector_gap=0
      | eval overlap_ns=0
      | eval change_ticket_id=""
      | eval approved_change=0
      | fields _time cluster crq_name signal_lane namespace total_used_cpu_m total_hard_cpu_m total_used_mem_ki total_hard_mem_ki ns_member_cnt denial_flag audit_verb acrq_delta_hint selector_gap overlap_ns change_ticket_id approved_change ]
    [ search (index=ocp_audit OR index=k8s_audit) (sourcetype=ocp_audit OR sourcetype=k8s_audit OR sourcetype="kube:apiserver:audit") earliest=-24h@h latest=now
      | eval cluster=lower(trim(toString(coalesce(cluster, openshift_cluster, cluster_name, k8s_cluster_name, ""))))
      | eval apig=lower(trim(toString(coalesce('objectRef.apiGroup', objectRef_apiGroup, objectRef.apigroup, ""))))
      | eval res=lower(trim(toString(coalesce('objectRef.resource', objectRef.resource, objectRef_resource, ""))))
      | eval verb=lower(trim(toString(coalesce(verb, requestVerb, request_verb, ""))))
      | where match(apig,"quota.openshift.io") AND match(res,"clusterresourcequotas") AND match(verb,"create|update|patch|delete")
      | eval crq_name=trim(toString(coalesce('objectRef.name', objectRef.name, objectRef_name, "")))
      | eval namespace="cluster_scope"
      | eval signal_lane="crq_audit_change"
      | eval audit_verb=verb
      | eval denial_flag=0
      | eval total_used_cpu_m=0
      | eval total_hard_cpu_m=0
      | eval total_used_mem_ki=0
      | eval total_hard_mem_ki=0
      | eval ns_member_cnt=0
      | eval acrq_delta_hint=0
      | eval selector_gap=0
      | eval overlap_ns=0
      | join type=left max=0 cluster crq_name
          [| inputlookup approved_quota_changes.csv
           | eval cluster=lower(trim(toString(cluster)))
           | eval crq_name=trim(toString(coalesce(quota_name, crq_name, "")))
           | eval change_ticket_id=trim(toString(coalesce(change_ticket_id, ticket, "")))
           | eval approved_change=if(len(change_ticket_id)>3,1,0)
           | fields cluster crq_name change_ticket_id approved_change ]
      | fields _time cluster crq_name signal_lane namespace total_used_cpu_m total_hard_cpu_m total_used_mem_ki total_hard_mem_ki ns_member_cnt denial_flag audit_verb acrq_delta_hint selector_gap overlap_ns change_ticket_id approved_change ]
| fillnull value=0 denial_flag acrq_delta_hint selector_gap overlap_ns approved_change
| fillnull value="" change_ticket_id audit_verb
| eval cpu_headroom_pct=if(total_hard_cpu_m>0 AND signal_lane=="crq_status_headroom", round(100.0*(total_hard_cpu_m-total_used_cpu_m)/total_hard_cpu_m,3), null())
| eval dom_ns_burn_pct=if(total_hard_cpu_m>0 AND signal_lane=="selector_coverage_acrq", round(100.0*total_used_cpu_m/total_hard_cpu_m,3), null())
| eval snap_cpu=if(signal_lane=="crq_status_headroom", total_used_cpu_m, null())
| sort 0 cluster crq_name _time
| streamstats time_window=3600 window=100000 global=f current=t first(snap_cpu) AS e1h last(snap_cpu) AS l1h BY cluster crq_name
| streamstats time_window=21600 window=100000 global=f current=t first(snap_cpu) AS e6h last(snap_cpu) AS l6h BY cluster crq_name
| streamstats time_window=86400 window=100000 global=f current=t first(snap_cpu) AS e24h last(snap_cpu) AS l24h BY cluster crq_name
| eval burn_1h=round(coalesce(l1h,0)-coalesce(e1h,0),2)
| eval burn_6h=round(coalesce(l6h,0)-coalesce(e6h,0),2)
| eval burn_24h=round(coalesce(l24h,0)-coalesce(e24h,0),2)
| eval slope_m_per_s=if(burn_6h!=0, burn_6h/21600.0, 0)
| eval sec_to_sat=if(signal_lane=="crq_status_headroom" AND slope_m_per_s>0 AND total_hard_cpu_m>total_used_cpu_m, round((total_hard_cpu_m-total_used_cpu_m)/slope_m_per_s,0), null())
| streamstats time_window=3600 window=100000 global=f current=t sum(denial_flag) AS denial_rate BY cluster crq_name
| eventstats sum(denial_flag) AS fleet_denials BY cluster
| join type=left max=0 cluster crq_name
    [| inputlookup tenant_slo.csv
     | eval cluster=lower(trim(toString(cluster)))
     | eval crq_name=trim(toString(coalesce(quota_name, crq_name, "")))
     | eval tenant=trim(toString(coalesce(tenant, business_unit, "")))
     | eval slo_pct=tonumber(trim(toString(coalesce(slo_pct, denial_budget_pct, "0.02"))),10)
     | eval business_owner=trim(toString(coalesce(business_owner, owner, "")))
     | eval max_denials_hr=tonumber(trim(toString(coalesce(max_denials_hr, max_denials_per_hour, "10"))),10)
     | fields cluster crq_name tenant slo_pct business_owner max_denials_hr ]
| fillnull value=10 max_denials_hr
| eval slo_breach=if(denial_rate>max_denials_hr,1,0)
| eval ticket_ok=approved_change
| eval severity=case(
    selector_gap==1 OR overlap_ns==1, "critical",
    acrq_delta_hint==1 AND signal_lane=="selector_coverage_acrq", "high",
    denial_rate>=10 AND slo_breach==1, "high",
    isnotnull(cpu_headroom_pct) AND cpu_headroom_pct<=5 AND signal_lane=="crq_status_headroom", "high",
    isnotnull(dom_ns_burn_pct) AND dom_ns_burn_pct>=50, "high",
    signal_lane=="crq_audit_change" AND ticket_ok==0 AND match(audit_verb,"patch|update|delete"), "high",
    denial_rate>=3, "medium",
    isnotnull(sec_to_sat) AND sec_to_sat>0 AND sec_to_sat<86400 AND signal_lane=="crq_status_headroom", "medium",
    true(), "info")
| eval recommended_action=case(
    selector_gap==1, "fix_namespace_labels_or_project_template_to_match_crq_selector",
    overlap_ns==1, "dedupe_crq_selectors_and_split_tenant_scopes",
    acrq_delta_hint==1, "compare_oc_get_appliedclusterresourcequota_to_clusterresourcequota_status",
    denial_rate>=3, "raise_shared_limits_or_right_size_workloads_under_crq",
    signal_lane=="crq_audit_change" AND ticket_ok==0, "backfill_change_ticket_review_audit_actor",
    true(), "correlate_inventory_events_audit_and_refresh_snapshots")
| table _time cluster tenant crq_name namespace signal_lane cpu_headroom_pct dom_ns_burn_pct burn_1h burn_6h burn_24h sec_to_sat denial_rate max_denials_hr slo_breach ticket_ok change_ticket_id severity recommended_action fleet_denials business_owner audit_verb acrq_delta_hint selector_gap overlap_ns
```

## CIM SPL

```spl
| tstats summariesonly=true latest(Change.action) AS change_action latest(Change.object) AS change_object latest(Change.user) AS change_user FROM datamodel=Change WHERE nodename=Change earliest=-24h@h latest=now BY Change.dest
| rename Change.dest AS cim_dest
| join type=left max=0 cim_dest
    [| tstats summariesonly=true avg(Performance.cpu_load_percent) AS cpu_load_pct max(Performance.mem_used) AS mem_used FROM datamodel=Performance WHERE nodename=Performance.CPU earliest=-24h@h latest=now BY Performance.host
     | rename Performance.host AS cim_dest ]
| where like(lower(change_object), "%clusterresourcequota%") OR like(lower(change_object), "%quota.openshift.io%")
| table cim_dest change_action change_object change_user cpu_load_pct mem_used
```

## Visualization

Severity-colored table mirroring the closing SPL projection; timechart of denial_rate by cluster and crq_name; headroom gauges for cpu and memory totals; drilldown from signal_lane to snapshots, events, and audit JSON.

## Known False Positives

Short reconciliation lag after ClusterResourceQuota edits can spike acrq_delta_hint until controllers catch up; require persistence across multiple exporter intervals before paging application teams. Legitimate finance-approved raises emit audit mutations that look alarming until approved_quota_changes.csv contains matching ticket identifiers with correct effective times. Developer sandboxes that intentionally sit outside CRQ selectors will trigger selector_gap logic unless CMDB expect_crq_membership flags are accurate. EUS or maintenance windows that freeze snapshots may skew streamstats burn projections; pair sec_to_sat with live oc describe during incidents. OLM or catalog installs that burst pod creates can temporarily inflate denial_rate without sustained tenant impact; compare to deployment success ratios before executive escalation. Duplicate kube_events forwarders double denial_rate; dedupe on involvedObject uid when present. Penetration tests or chaos exercises that exhaust quotas should carry lookup suppressions with start and end epochs. Namespace label changes during live migrations may produce brief overlap_ns positives; confirm intentional dual-parent windows in governance lookups before forcing selector edits. Storage-heavy quotas may saturate requests.storage or persistentvolumeclaims before CPU burn math matters; extend dashboards beyond millicores when finance cares about those dimensions. Break-glass oc edit clusterresourcequota during incidents may lack preemptive CSV rows; use exception_expiry style columns in approved_quota_changes.csv to avoid noisy pages.

## References

- [OpenShift Documentation — Setting resource quotas across multiple projects](https://docs.openshift.com/container-platform/latest/applications/quotas/quotas-setting-across-multiple-projects.html)
- [Kubernetes Documentation — Resource quotas](https://kubernetes.io/docs/concepts/policy/resource-quotas/)
- [OpenShift API — quota v1 package reference](https://github.com/openshift/api/blob/master/quota/v1/doc.go)
- [OpenShift openshift-controller-manager repository](https://github.com/openshift/openshift-controller-manager)
- [Red Hat Documentation Portal — OpenShift Container Platform](https://docs.redhat.com/en/documentation/openshift_container_platform/)
- [OpenShift Documentation — Working with projects](https://docs.openshift.com/container-platform/latest/applications/working_with_projects.html)
- [Red Hat Blog — Managing compute resources with OpenShift and Kubernetes](https://www.redhat.com/en/blog/managing-compute-resources-openshiftkubernetes)
