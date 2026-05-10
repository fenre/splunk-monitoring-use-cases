<!-- AUTO-GENERATED from UC-3.3.21.json — DO NOT EDIT -->

---
id: "3.3.21"
title: "OpenShift ClusterRole and ClusterRoleBinding Drift, Bundled Role Modification Detection, OAuth-Mapped Subject Governance, and Aggregated RBAC Escalation Signals"
status: "verified"
criticality: "high"
splunkPillar: "Security"
---

# UC-3.3.21 · OpenShift ClusterRole and ClusterRoleBinding Drift, Bundled Role Modification Detection, OAuth-Mapped Subject Governance, and Aggregated RBAC Escalation Signals

> **Criticality:** High &middot; **Difficulty:** Advanced &middot; **Pillar:** Security &middot; **Type:** Configuration, Compliance &middot; **Wave:** Walk &middot; **Status:** Verified

*We watch the master permission lists for the whole cluster like building master keys. We catch when the keys the platform ships get altered, when name tags point to people who no longer exist, and when someone hands out many new cluster-wide keys all at once.*

---

## Description

Splunk correlates apiserver and OAuth audit lanes with periodic RBAC snapshots to surface governance drift on OpenShift cluster-scoped roles and bindings—bundled platform roles, OAuth-mapped subjects, aggregation label expansion, and binding bursts—without reducing the story to cluster-admin escalation alone.

## Value

OpenShift RBAC governance that catches bundled platform role tampering, OAuth identity mismatches in cluster-wide bindings, quiet aggregation expansion, and automation-driven binding storms before tenant isolation erodes.

## Implementation

Land ocp_audit, openshift-apiserver, and optional ocp_oauth_audit with RBAC mutation depth; publish ocp_rbac_snapshot and ocp_oauth_user_identity_snapshot; maintain approved_cluster_roles.csv; save openshift_uc_3_3_21_rbac_governance_drift every fifteen minutes over earliest=-24h@h; route critical and high rows to platform security; archive weekly evidence exports with lookup commit hashes.

## Evidence

Saved search openshift_uc_3_3_21_rbac_governance_drift with fifteen minute schedule; versioned approved_cluster_roles.csv and ocp_oauth_user_identity_snapshot.csv in git; weekly CSV exports to a restricted evidence index; dashboard drilldowns on ocp_audit and ocp_rbac_snapshot lanes.

## Control test

### Positive scenario

In a lab OpenShift cluster, ingest audit showing patch on bundled cluster-reader with success response, ingest ocp_rbac_snapshot showing aggregate label counts increasing on a custom ClusterRole, and confirm openshift_uc_3_3_21_rbac_governance_drift returns critical or high with non-null recommended_action within the scheduled window.

### Negative scenario

After rollback when oc get clusterrole shows restored rules, aggregate labels removed, identity snapshots include bound users, and binding velocity returns to baseline, confirm severities return to info and the alert wrapper emits zero rows when filtering to critical and high only per policy.

## Detailed Implementation

### Step 1 — Prerequisites

Head of Platform owns this control jointly with the OpenShift platform security lead, the identity and access management engineers who operate the OAuth server and corporate identity providers, the Kubernetes authorization maintainers who interpret ClusterRole aggregation semantics, and the observability staff who steward Splunk HTTP Event Collector tokens plus audit log forwarders from kube-apiserver, openshift-apiserver, and oauth-apiserver. This use case isolates OpenShift cluster-scoped RBAC governance drift: modifications to bundled ClusterRoles that Red Hat ships with the platform, ClusterRoleBinding subjects that reference OAuth-mapped users and groups with weak lifecycle hygiene, sudden bursts of cluster-wide binding grants that indicate automation mistakes or hostile mass assignment, aggregated ClusterRole label drift where custom roles inherit into broader aggregates, and integrity signals for bootstrap roles that should remain stable outside approved upgrades. UC-3.2.23 remains the narrow cluster-admin tier escalation audit on successful bindings to the built-in cluster-admin ClusterRole, system:masters group wiring, wildcard ClusterRole rule mutations, and certificate signing approval paths. This document deliberately avoids centering cluster-admin alone; it prioritizes platform bundle integrity, subject hygiene, aggregation expansion, and velocity of cluster-scoped grants. UC-3.3.4 remains Security Context Constraint admission outcomes and openshift.io/scc annotation truth on pods. UC-3.3.6 remains ClusterOperator reconciliation health including authentication operator availability as an operational plane signal rather than an RBAC object inventory. UC-3.2.12, when present in your catalogue, remains generic RBAC permission anomaly scoring across verbs such as escalate and bind without the OpenShift-specific bundled role catalogue and OAuth identity join semantics prescribed here.

Index and permission design land before field extraction. Designate index=ocp_audit for Kubernetes API audit v1 JSON forwarded from management clusters with sourcetype=ocp_audit or sourcetype=k8s_audit depending on whether you segregate OpenShift from vanilla Kubernetes estates. Forward oauth-apiserver audit to the same index with a distinct sourcetype such as ocp_oauth_audit when your collectors split streams; otherwise retain a unified ocp_audit stream and filter userAgent or stage fields in SPL. Designate index=ocp_inventory for periodic object snapshots with sourcetype=ocp_rbac_snapshot capturing ClusterRole rule counts, aggregationRule presence, label keys matching rbac.authorization.k8s.io/aggregate-to-*, and ClusterRoleBinding subject tuples including kind, name, namespace, and apiGroup. Designate optional index=ocp_identity for user.openshift.io User, user.openshift.io Identity, and oauth.openshift.io OAuthClient inventory rows when you export oc get user, oc get identity, and oc get oauthclient snapshots for Splunk joins. Issue distinct HEC tokens per environment with least privilege: platform security may search all sourcetypes; application teams receive redacted views that omit requestObject bodies when counsel requires minimization. Retention should cover at least thirty days hot for quarterly access attestations, ninety days when regulated customers require historical replay of binding storms, and align cold storage with enterprise logging policy. Legal review should confirm corporate usernames, group names, and service account namespaces appearing in audit and inventory are acceptable in Splunk.

RBAC and safety: collectors that run oc get clusterrole -o json, oc get clusterrolebinding -o json, oc get user -o json, and oc get identity -o json must use a dedicated ServiceAccount with cluster-scoped get and list on those resources, not long-lived kubeadmin kubeconfig files on administrator laptops. Break-glass administrators who run oc adm policy add-cluster-role-to-user should expect their actions in audit with user.username and user.groups preserved. Metrics federation identities are unrelated to this control except as a telemetry transport; do not grant cluster-admin to metrics scrapers.

Audit policy depth: capture Metadata at minimum for high-volume read traffic on clusterroles and clusterrolebindings; capture RequestResponse or Request on create, update, patch, and delete so analysts can compare rules arrays, aggregationRule selectors, metadata.labels, and subjects arrays without fabricating fields in Splunk. Include openshift-apiserver audit when platform extensions mutate RBAC objects. Include oauth-apiserver audit for authentication.openshift.io resources when your threat model covers OAuthClient secret rotations and identity provider mapping changes that correlate to subject anomalies.

Field normalization: flatten objectRef.apiGroup, objectRef.resource, objectRef.name, objectRef.namespace, user.username, verb, responseStatus.code, impersonatedUser.username when present, and requestObject metadata and spec fragments when audit bodies include them. Cluster identity must appear on every event as cluster, openshift_cluster, or cluster_name. For inventory snapshots, flatten clusterrole_name, rules_count, agg_rule_flag, aggregate_label_count, binding_name, subject_kind, subject_name, subject_namespace, role_ref_name, role_ref_kind.

Risk briefing: legitimate Operator Lifecycle Manager installs routinely create new ClusterRoles and ClusterRoleBindings; tune lookups and change_ticket_id metadata before paging application teams on every new operator CSV apply. OpenShift upgrades reconcile bundled roles and may emit bursts of update verbs during reconciliation; pair Splunk rows with ClusterVersion history. GitOps controllers that enforce RBAC from repositories can create velocity spikes that look like incidents until you join Flux or Argo CD audit actors. Penetration tests and red-team exercises may mutate test ClusterRoles; ingest pentest authorization lookups with start and end epochs.

Differentiation recap: OpenShift bundled ClusterRole integrity, OAuth-mapped subject hygiene, aggregation label drift, mass ClusterRoleBinding velocity, and bootstrap role stability—not UC-3.2.23 cluster-admin binding exclusivity, not SCC admission, not ClusterOperator Available versus Degraded storytelling alone.

Operational posture: maintain approved_cluster_roles.csv with columns cluster, clusterrole_name, change_ticket_id, owner_team, approved_state such as bundled_readonly or custom_allowed, and exception_expiry_epoch for temporary vendor exceptions. Maintain ocp_oauth_user_identity_snapshot.csv refreshed hourly from oc get user and oc get identity with columns cluster, user_name, identity_resource_name, idp_name, idp_trusted_flag, and last_seen_epoch so Splunk can flag bindings that reference principals missing from the snapshot. Document the four core bootstrap ClusterRole names your organization treats as immutable without vendor guidance: admin, edit, view, and cluster-admin in the Kubernetes documentation sense, plus OpenShift system catalog roles such as cluster-reader, basic-user, cluster-monitoring-view, cluster-status, system:discovery, system:public-info-viewer, system:basic-user, and representative system:openshift:* readers and console helpers as expanded in platform standards.

Bootstrap role integrity narrative: administrators sometimes attempt to “simplify” default roles by deleting rules from view, edit, or admin to block namespaces from using certain APIs. That approach is fragile because aggregated roles, operators, and console workflows expect the default composition. Splunk should treat rule removals on those bootstrap names as governance-critical even when the actor is a well-meaning platform engineer. Likewise, deleting bundled discovery roles can break unauthenticated discovery flows and break clients that rely on consistent discovery semantics; treat deletes on system:discovery, system:public-info-viewer, and system:basic-user as high priority review items.

OAuth subject narrative: OpenShift represents interactive users as User objects and links them to Identity objects that record provider-specific names. ClusterRoleBindings may list subjects of kind User with a name that must exist for the binding to make sense in enterprise access reviews. When HR offboarding removes a corporate account but a ClusterRoleBinding still lists the OpenShift User name, you have a governance defect even if tokens no longer mint. When an IdP is removed from the OAuth configuration but identities linger, analysts may see orphaned provider metadata. This use case joins inventory snapshots to highlight those mismatches at cluster scope where blast radius is highest.

Aggregation narrative: Kubernetes aggregated ClusterRoles use aggregationRule label selectors and controller-manager reconciliation to merge rules from other ClusterRoles that carry matching aggregate-to labels. A custom ClusterRole that adds rbac.authorization.k8s.io/aggregate-to-view or aggregate-to-edit style labels can unintentionally widen default bundles. Splunk inventory arms count those labels and compare against approved_cluster_roles.csv so you can separate vendor-intended aggregation from tenant experiments.

Service account cluster binding narrative: workload automation sometimes grants cluster-admin or powerful bundled roles to ServiceAccount subjects in application namespaces. Even without reaching the UC-3.2.23 cluster-admin exclusive framing, cluster-scoped bindings for non-system namespaces are a governance red flag worth tracking as drift velocity and subject namespace anomalies.

Fleet narrative: platform security leaders often need evidence that RBAC drift is monitored continuously, not only during annual access reviews. This saved search produces exportable rows suitable for audit packs when paired with lookup commit hashes and change tickets.

### Step 2 — Configure data collection

Stand up four complementary lanes Splunk multisearch can fuse: kube-apiserver and openshift-apiserver audit for rbac.authorization.k8s.io clusterroles and clusterrolebindings mutations, periodic RBAC inventory snapshots with aggregation metadata, oauth-apiserver and kube-apiserver audit correlated to User and Identity inventory for OAuth subject hygiene, and filtered audit replay for bundled OpenShift ClusterRole names.

Audit lane primary: ship kube-apiserver audit.log and openshift-apiserver audit streams into index=ocp_audit with sourcetype=ocp_audit using Splunk Connect for Kubernetes filelog patterns, Splunk OpenTelemetry Collector filelog receiver, or cloud-audit exports that preserve Kubernetes audit v1 JSON. Ensure stageTimestamp maps to _time within thirty seconds of true apiserver time. Enable TLS to Splunk, rotate HEC tokens quarterly, and document which management cluster forwards lab versus production to prevent cluster label collisions.

OAuth audit lane: forward oauth-apiserver audit into index=ocp_audit with sourcetype=ocp_oauth_audit when available. Retain user.username for administrative verbs on user.openshift.io User, user.openshift.io Identity, and oauth.openshift.io OAuthClient objects. When oauth-apiserver audit is unavailable, rely on kube-apiserver audit of the same resources if your audit policy captures those API groups at sufficient depth.

Inventory snapshot lane: schedule a utility every fifteen to sixty minutes from a management host with kubeconfig authentication. The utility should run oc get clusterrole -o json, oc get clusterrolebinding -o json, compute rules_count per ClusterRole from len(rules) when aggregationRule is absent, set agg_rule_flag when aggregationRule is non-null, count metadata.labels keys matching rbac.authorization.k8s.io/aggregate-to-, flatten each ClusterRoleBinding subjects[] into child rows with subject_kind, subject_name, subject_namespace, role_ref_name, and emit HTTP Event Collector JSON with sourcetype=ocp_rbac_snapshot and source=oc_get_rbac_inventory. Include a sha256 hash of canonical JSON without volatile resourceVersion when tamper evidence is required.

Identity snapshot lane: schedule oc get user -o json and oc get identity -o json on the same cadence, emitting sourcetype=ocp_identity_snapshot or landing rows into a CSV that forwarders index into a lookup-friendly index. Preserve user.metadata.name, identity.user.name, identity.providerName, and identity.extra keys when present so Splunk can correlate HTPasswd, LDAP, and OIDC styles without assuming one field shape.

Governance lookups: publish approved_cluster_roles.csv in git with cluster, clusterrole_name, approved_state, owner_team, change_ticket_id, exception_expiry_epoch, and notes. Refresh from the same repository that manages exceptions so auditors can trace commit ancestry.

Example oc verification operators run during design reviews:

```bash
oc get clusterrole cluster-reader -o yaml | head -n 40
oc get clusterrolebinding | wc -l
oc adm policy who-can bind clusterrole/admin
oc get user; oc get identity
```

props.conf guidance: TRUNCATE sufficiently large for RequestResponse bodies, TIMESTAMP_FIELDS respected when HEC time is authoritative, LINE_BREAKER for newline-delimited JSON audit files, FIELDALIAS maps from dotted API paths to underscore fields used in SPL coalesce ladders.

Pre-save validation: index=ocp_audit sourcetype=ocp_audit earliest=-15m must return non-zero counts; intentional lab oc create clusterrolebinding should appear with verbs create or update; ocp_rbac_snapshot must list bundled roles such as cluster-reader after the first interval; identity snapshots must include at least one user row on clusters with OAuth integration.

Dashboards: the Splunk OpenShift App or an equivalent security dashboard should host a severity-colored table keyed on cluster and signal_lane with drilldowns to raw audit JSON, snapshot rows, and lookup matches. Splunk Enterprise Security users may treat recommended_action as an adaptive response hint field without auto-remediation.

Volume controls: if RequestResponse audit is too heavy, keep RequestResponse for cluster-scoped RBAC resources only and use Metadata elsewhere, following OpenShift audit profile documentation. Revisit volume after each minor upgrade because new APIs can increase baseline noise.

Label consistency: enforce cluster naming conventions on HTTP Event Collector metadata so ocp_rbac_snapshot and ocp_audit share identical cluster keys for joins. Mixed case or mixed label names break join type=left arms silently.

### Step 3 — Create the search and alert

Save the SPL as openshift_uc_3_3_21_rbac_governance_drift with a fifteen minute schedule during steady-state production, dispatch earliest=-24h@h, dispatch latest=now, and alert when severity is critical, high, or medium per your routing matrix. Throttle duplicate cluster, signal_type, cr_or_crb_name rows for forty-five minutes unless severity escalates. Include recommended_action, bundled_hit, binding_velocity_win, and orphan_subject in pager descriptions so incident commanders open RBAC runbooks without re-running ad hoc searches.

Pipeline narrative for reviewers: multisearch fans rbac audit mutations, RBAC inventory drift hints, OAuth subject hygiene rows derived from snapshot joins, and bundled-role-focused audit replay so a silent inventory exporter does not hide live mutations. coalesce() absorbs flattened versus dotted JSON field naming drift across exporters. streamstats measures short-window ClusterRoleBinding mutation counts per cluster after sorting events. eventstats adds fleet context such as cluster-level peaks for binding velocity windows. join type=left wraps approved_cluster_roles.csv to classify approved versus unexpected bundled mutations. case() maps bundled role deletions, aggregation label additions on custom roles, high binding velocity, orphan OAuth subjects, and automation without baselines into severity tiers. recommended_action encodes oc get clusterrole, oc get clusterrolebinding, oc adm policy who-can, oc get user, oc get identity, and GitOps diff steps without pretending Splunk replaces kubectl.

Fenced SPL must match the spl JSON field exactly:

```spl
`comment("UC-3.3.21 OpenShift RBAC governance — audit rbac + ocp_rbac_snapshot + OAuth subject hygiene + bundled ClusterRole focus. Join approved_cluster_roles.csv baseline. Tunables: vel_high=6 vel_crit=12 earliest=-24h@h latest=now")`
| multisearch
    [ search (index=ocp_audit OR index=k8s_audit) (sourcetype=ocp_audit OR sourcetype=k8s_audit OR sourcetype="kube:apiserver:audit") earliest=-24h@h latest=now
      | eval cluster=lower(trim(toString(coalesce(cluster, openshift_cluster, cluster_name, k8s_cluster_name, ""))))
      | eval apig=lower(trim(toString(coalesce('objectRef.apiGroup', objectRef_apiGroup, objectRef.apigroup, ""))))
      | eval res=lower(trim(toString(coalesce('objectRef.resource', objectRef.resource, objectRef_resource, ""))))
      | eval verb=lower(trim(toString(coalesce(verb, requestVerb, request_verb, ""))))
      | eval actor=trim(toString(coalesce('user.username', user.username, user_username, "")))
      | eval obj=trim(toString(coalesce('objectRef.name', objectRef.name, objectRef_name, "")))
      | where (match(apig,"rbac.authorization.k8s.io") OR len(apig)==0) AND match(res,"clusterroles|clusterrolebindings") AND match(verb,"create|update|patch|delete")
      | eval resp_code=tonumber(toString(coalesce('responseStatus.code', responseStatus.code, responseStatus_code, "201")),10)
      | where resp_code>=200 AND resp_code<300
      | eval signal_lane="rbac_audit_mut"
      | eval cr_or_crb_name=obj
      | eval bundled_hit=0
      | eval agg_label_drift=0
      | eval orphan_subject=0
      | eval rules_cnt=null()
      | eval agg_flag=null()
      | eval agg_lbl_cnt=null()
      | eval bind_user=""
      | fields _time cluster actor verb res obj signal_lane cr_or_crb_name bundled_hit agg_label_drift orphan_subject rules_cnt agg_flag agg_lbl_cnt bind_user ]
    [ search index=ocp_inventory sourcetype=ocp_rbac_snapshot earliest=-24h@h latest=now
      | eval cluster=lower(trim(toString(coalesce(cluster, openshift_cluster, cluster_name, ""))))
      | eval cr_name=lower(trim(toString(coalesce(clusterrole_name, name, metadata_name, ""))))
      | eval rules_cnt=tonumber(trim(toString(coalesce(rules_count, rules_cnt, "0"))),10)
      | eval agg_flag=tonumber(trim(toString(coalesce(agg_rule_flag, aggregation_rule_flag, "0"))),10)
      | eval agg_lbl_cnt=tonumber(trim(toString(coalesce(aggregate_label_count, agg_label_cnt, "0"))),10)
      | eval signal_lane="rbac_snap_drift"
      | eval cr_or_crb_name=cr_name
      | eval actor="inventory_exporter"
      | eval verb="snapshot"
      | eval res="clusterroles"
      | eval obj=cr_name
      | eval bundled_hit=0
      | eval agg_label_drift=if(agg_lbl_cnt>=1 AND !match(cr_name,"^system:aggregator|^system:controller:|^system:|^openshift:"),1,0)
      | eval orphan_subject=0
      | eval bind_user=""
      | where agg_flag>=1 OR agg_lbl_cnt>=1 OR rules_cnt<=0
      | fields _time cluster actor verb res obj signal_lane cr_or_crb_name bundled_hit agg_label_drift orphan_subject rules_cnt agg_flag agg_lbl_cnt bind_user ]
    [ search (index=ocp_audit OR index=k8s_audit) (sourcetype=ocp_audit OR sourcetype=k8s_audit OR sourcetype=ocp_oauth_audit OR sourcetype="kube:apiserver:audit") earliest=-24h@h latest=now
      | eval cluster=lower(trim(toString(coalesce(cluster, openshift_cluster, cluster_name, k8s_cluster_name, ""))))
      | eval res=lower(trim(toString(coalesce('objectRef.resource', objectRef.resource, objectRef_resource, ""))))
      | eval verb=lower(trim(toString(coalesce(verb, requestVerb, request_verb, ""))))
      | where match(res,"clusterrolebindings") AND match(verb,"create|update|patch")
      | eval lr=lower(_raw)
      | rex field=lr max_match=0 "(?i)\"kind\"\s*:\s*\"User\"\s*,\s*\"name\"\s*:\s*\"(?<subj_user>[^\"]+)\""
      | eval bind_user=lower(trim(toString(coalesce(subj_user, ""))))
      | where len(bind_user)>1
      | join type=left max=0 cluster bind_user
          [| inputlookup ocp_oauth_user_identity_snapshot.csv
           | eval cluster=lower(trim(toString(cluster)))
           | eval bind_user=lower(trim(toString(coalesce(user_name, username, ""))))
           | eval idp_trusted=tonumber(trim(toString(coalesce(idp_trusted_flag, "1"))),10)
           | eval snap_present=1
           | fields cluster bind_user idp_trusted snap_present ]
      | eval actor=trim(toString(coalesce('user.username', user.username, user_username, "")))
      | eval cr_or_crb_name=trim(toString(coalesce('objectRef.name', objectRef.name, objectRef_name, "")))
      | eval orphan_subject=if(coalesce(snap_present,0)==0 OR idp_trusted==0,1,0)
      | eval signal_lane="oauth_bind_hygiene"
      | eval bundled_hit=0
      | eval agg_label_drift=0
      | eval obj=cr_or_crb_name
      | eval res="clusterrolebindings"
      | eval rules_cnt=null()
      | eval agg_flag=null()
      | eval agg_lbl_cnt=null()
      | fields _time cluster actor verb res obj signal_lane cr_or_crb_name bundled_hit agg_label_drift orphan_subject rules_cnt agg_flag agg_lbl_cnt bind_user ]
    [ search (index=ocp_audit OR index=k8s_audit) (sourcetype=ocp_audit OR sourcetype=k8s_audit OR sourcetype="kube:apiserver:audit") earliest=-24h@h latest=now
      | eval cluster=lower(trim(toString(coalesce(cluster, openshift_cluster, cluster_name, k8s_cluster_name, ""))))
      | eval res=lower(trim(toString(coalesce('objectRef.resource', objectRef.resource, objectRef_resource, ""))))
      | eval verb=lower(trim(toString(coalesce(verb, requestVerb, request_verb, ""))))
      | eval obj=lower(trim(toString(coalesce('objectRef.name', objectRef.name, objectRef_name, ""))))
      | where match(res,"clusterroles|clusterrolebindings") AND match(verb,"create|update|patch|delete")
      | eval bundled_hit=if(match(obj,"^(cluster-reader|cluster-monitoring-view|cluster-status|view|edit|admin|basic-user|system:discovery|system:public-info-viewer|system:basic-user)$") OR match(obj,"^system:openshift:"),1,0)
      | where bundled_hit=1
      | eval actor=trim(toString(coalesce('user.username', user.username, user_username, "")))
      | eval signal_lane="bundled_role_touch"
      | eval cr_or_crb_name=obj
      | eval agg_label_drift=0
      | eval orphan_subject=0
      | eval rules_cnt=null()
      | eval agg_flag=null()
      | eval agg_lbl_cnt=null()
      | eval bind_user=""
      | fields _time cluster actor verb res obj signal_lane cr_or_crb_name bundled_hit agg_label_drift orphan_subject rules_cnt agg_flag agg_lbl_cnt bind_user ]
| eval signal_type=signal_lane
| eval is_bind_evt=if(signal_lane=="rbac_audit_mut" AND match(res,"clusterrolebindings"),1,0)
| sort 0 cluster cr_or_crb_name - _time
| streamstats window=20 current=t global=f sum(is_bind_evt) AS bind_window_cnt by cluster
| eventstats max(bind_window_cnt) AS cluster_bind_peak by cluster
| eval binding_velocity_win=coalesce(bind_window_cnt,0)
| join type=left max=0 cluster cr_or_crb_name
    [| inputlookup approved_cluster_roles.csv
     | eval cluster=lower(trim(toString(cluster)))
     | eval cr_or_crb_name=lower(trim(toString(coalesce(clusterrole_name, cr_name, ""))))
     | eval approved_state=trim(toString(coalesce(approved_state, state, "")))
     | eval owner_team_lu=trim(toString(coalesce(owner_team, "")))
     | eval exception_expiry=tonumber(trim(toString(coalesce(exception_expiry_epoch, "0"))),10)
     | fields cluster cr_or_crb_name approved_state owner_team_lu exception_expiry ]
| fillnull value="" approved_state owner_team_lu
| eval now_e=now()
| eval baseline_ok=if(match(approved_state,"bundled_readonly|custom_allowed|approved") AND (exception_expiry==0 OR now_e<=exception_expiry),1,0)
| eval severity=case(
    bundled_hit==1 AND verb!="snapshot" AND match(verb,"patch|update|delete") AND baseline_ok==0, "critical",
    orphan_subject==1, "high",
    agg_label_drift==1 AND baseline_ok==0, "high",
    binding_velocity_win>=12, "high",
    bundled_hit==1 AND verb!="snapshot" AND baseline_ok==0, "medium",
    binding_velocity_win>=6, "medium",
    signal_lane=="rbac_audit_mut" AND match(res,"clusterrolebindings") AND baseline_ok==0, "medium",
    true(), "info")
| eval recommended_action=case(
    bundled_hit==1 AND match(verb,"delete"), "restore_bundled_clusterrole_from_supported_backup_and_open_vendor_case",
    orphan_subject==1, "oc_get_clusterrolebinding_prune_stale_subjects_and_reconcile_idp_mappings",
    agg_label_drift==1, "oc_get_clusterrole_labels_remove_unapproved_aggregate_labels",
    binding_velocity_win>=12, "freeze_gitops_rbac_and_review_automation_actor",
    true(), "correlate_audit_to_change_ticket_and_refresh_inventory_snapshot")
| table _time cluster signal_type cr_or_crb_name verb actor res bundled_hit agg_label_drift orphan_subject binding_velocity_win cluster_bind_peak baseline_ok approved_state owner_team_lu severity recommended_action bind_user rules_cnt agg_flag agg_lbl_cnt
```

savedsearches.conf sketch:

```ini
[openshift_uc_3_3_21_rbac_governance_drift_alert]
cron_schedule = */15 * * * *
dispatch.earliest_time = -24h@h
dispatch.latest_time = now
enableSched = 1
action.email = 1
action.email.to = openshift-platform-security@example.com
action.email.subject = OCP RBAC governance $result.severity$ $result.cluster$ $result.signal_type$
counttype = number of events
relation = greater than
quantity = 0
search = | savedsearch openshift_uc_3_3_21_rbac_governance_drift | where severity IN ("critical","high","medium")
```

Performance: if Job Inspector shows multisearch queue time above internal service level objectives, materialize ocp_rbac_snapshot hourly into a summary index keyed on cluster and cr_or_crb_name, widen alert searches to earliest=-6h@h on summaries, and retain this full search for investigations.

### Step 4 — Validate

Ground truth always starts on-cluster. For bundled role mutations surfaced in Splunk, run oc get clusterrole object_name -o yaml and compare resourceVersion and rules to change tickets. When statuses disagree, verify indexer clock skew and duplicate cluster labels across regions before blaming parsers.

ClusterRoleBinding validation: pick a Splunk row with orphan_subject=1, run oc get clusterrolebinding name -o yaml, and compare subjects to oc get user and oc get identity for the same principal. Confirm whether the binding references a deleted corporate account or a stale group mapping.

Synthetic bundled touch: in lab under change control, attempt a benign oc label clusterrole custom-aggregate-test rbac.authorization.k8s.io/aggregate-to-view=true and confirm agg_label_drift arms fire on snapshot or audit depending on exporter configuration. Remove the label and confirm severities return toward info.

Synthetic velocity: in lab, script a short burst of non-production ClusterRoleBinding creates using a dedicated service account with ticket authorization, confirm binding_velocity_win rises, then delete bindings and confirm decay.

Negative test: on a cluster with quiet RBAC change calendars and healthy identity snapshots, confirm the alert wrapper returns zero rows when filtering to critical and high only if your routing policy suppresses medium.

Privacy test: requestObject bodies should not land in developer-shared indexes when they disclose secrets; redact at collection.

Correlation test: pair timelines with UC-3.2.23 only when cluster-admin roleRefs appear; this UC should still emit bundled integrity rows without requiring cluster-admin mutations.

Synthetic identity gap: create a ClusterRoleBinding referencing a User name that does not exist in oc get user and confirm oauth_bind_hygiene classification after the join marks snap_present null.

Clock skew test: indexer time within thirty seconds of apiserver; otherwise streamstats windows mis-order events.

Parser drift test: after OpenShift minor upgrades, validate FIELDALIAS rules still map dotted audit fields into objectRef_resource style aliases used by coalesce ladders.

### Step 5 — Operationalize & Troubleshoot

Case 1 — Bundled ClusterRole rule shrink or delete without ticket: when this triggers, audit shows delete or patch verbs on cluster-reader, admin, edit, view, basic-user, system:discovery, system:public-info-viewer, system:basic-user, or representative system:openshift roles outside approved maintenance windows. Investigate user.username, session enrichment, and change calendars for authorized platform work. Involve platform security, the OpenShift operations lead, and the change advisory board delegate when no ticket exists. Remediate by restoring supported object definitions from backup or allowing controllers to reconcile per vendor guidance, then rotate credentials implicated in unauthorized edits. Validate by comparing oc get clusterrole YAML to a known-good export and confirming Splunk returns info severities after recovery.

Case 2 — Aggregation label added to a custom ClusterRole: when this triggers, inventory shows rbac.authorization.k8s.io/aggregate-to-* labels on tenant-owned roles without matching approved_state. Investigate Git history, Helm charts, and operator manifests that inject labels automatically. Involve application platform engineering and the service owner who requested visibility changes. Remediate by removing unapproved labels or filing a formal exception with expiry in approved_cluster_roles.csv. Validate by rerunning the snapshot exporter and confirming agg_label_drift clears in Splunk.

Case 3 — ClusterRoleBinding references OAuth User not present in identity snapshot: when this triggers, the join marks orphan_subject for User subjects. Investigate HR offboarding lag, directory sync failures, or stale test accounts. Involve identity operations and human resources liaison per internal policy. Remediate by pruning bindings or restoring users through the identity provider. Validate with oc get clusterrolebinding and a refreshed ocp_oauth_user_identity_snapshot.csv ingest.

Case 4 — ServiceAccount in a tenant namespace granted powerful cluster-scoped roles: when audit or inventory shows subject_kind ServiceAccount with subject_namespace outside openshift-*, kube-*, or documented system namespaces paired with powerful roleRef names, investigate automation and CI tokens. Involve DevSecOps and the owning product team. Remediate by replacing cluster bindings with namespaced RoleBindings or narrower ClusterRoles. Validate with oc adm policy who-can and by confirming Splunk no longer flags the tuple.

Case 5 — Mass binding additions in minutes: when streamstats binding_velocity_win crosses thresholds, investigate batch applies from GitOps, Terraform, or compromised tokens. Involve platform on-call and incident commander if compromise is plausible. Remediate by freezing automation credentials, rolling tokens, and reverting commits. Validate by observing velocity decay and normal audit cadence.

Case 6 — Group binding maps to unusually large directory population: when governance reviews show Group subjects correlated to directory membership spikes, investigate nested groups and filter changes. Involve enterprise directory teams. Remediate by tightening mappings or splitting roles. Validate with directory samples and reduced effective membership on test authentication.

Case 7 — Aggregated ClusterRole expansion after operator upgrade: when aggregationRule or label sets change post-upgrade, investigate operator release notes and CSV-owned ClusterRoles. Involve operator platform owners. Remediate by pinning channels or opening vendor defects when expansion is unintended. Validate by comparing snapshot hashes of rules_count and labels across upgrades.

Case 8 — Identity provider removed but bindings remain: when idp_trusted_flag is zero while users from that provider still appear in bindings, investigate IdP cutover runbooks. Involve identity engineering. Remediate by migrating users and pruning stale Identity objects. Validate by successful login tests and clearing Splunk orphan signals.

Case 9 — Emergency oc adm policy without ticket metadata: when expected break-glass occurs but HEC payloads lack change_ticket_id, investigate documentation gaps. Involve platform leadership for break-glass policy. Remediate by retroactively filing tickets and updating approved_cluster_roles.csv with exception windows. Validate by joins showing baseline_ok with accurate exception_expiry.

Case 10 — Duplicate forwarders inflate velocity: when auditID duplicates appear, investigate redundant collectors. Involve observability engineers. Remediate by deduping at ingest or summary index layers. Validate by matching Splunk counts to apiserver audit cardinality samples.

Case 11 — Inventory exporter lag: when ocp_rbac_snapshot timestamps trail audit activity materially, investigate kubeconfig expiry and job failures. Involve automation owners. Remediate by renewing credentials and restoring schedules. Validate by aligned _time across sourcetypes within one collection interval.

Closing checklist: multisearch lists rbac audit, snapshot drift, OAuth hygiene join, and bundled role arms; coalesce normalizes cluster fields; streamstats and eventstats quantify velocity; join approved_cluster_roles.csv supplies governance baseline; case() implements severity tiers; closing table includes _time, cluster, signal_type, cr_or_crb_name, verb, actor, res, bundled_hit, agg_label_drift, orphan_subject, binding_velocity_win, cluster_bind_peak, baseline_ok, approved_state, owner_team_lu, severity, recommended_action, bind_user, rules_cnt, agg_flag, agg_lbl_cnt for nineteen analyst-visible columns.

## SPL

```spl
`comment("UC-3.3.21 OpenShift RBAC governance — audit rbac + ocp_rbac_snapshot + OAuth subject hygiene + bundled ClusterRole focus. Join approved_cluster_roles.csv baseline. Tunables: vel_high=6 vel_crit=12 earliest=-24h@h latest=now")`
| multisearch
    [ search (index=ocp_audit OR index=k8s_audit) (sourcetype=ocp_audit OR sourcetype=k8s_audit OR sourcetype="kube:apiserver:audit") earliest=-24h@h latest=now
      | eval cluster=lower(trim(toString(coalesce(cluster, openshift_cluster, cluster_name, k8s_cluster_name, ""))))
      | eval apig=lower(trim(toString(coalesce('objectRef.apiGroup', objectRef_apiGroup, objectRef.apigroup, ""))))
      | eval res=lower(trim(toString(coalesce('objectRef.resource', objectRef.resource, objectRef_resource, ""))))
      | eval verb=lower(trim(toString(coalesce(verb, requestVerb, request_verb, ""))))
      | eval actor=trim(toString(coalesce('user.username', user.username, user_username, "")))
      | eval obj=trim(toString(coalesce('objectRef.name', objectRef.name, objectRef_name, "")))
      | where (match(apig,"rbac.authorization.k8s.io") OR len(apig)==0) AND match(res,"clusterroles|clusterrolebindings") AND match(verb,"create|update|patch|delete")
      | eval resp_code=tonumber(toString(coalesce('responseStatus.code', responseStatus.code, responseStatus_code, "201")),10)
      | where resp_code>=200 AND resp_code<300
      | eval signal_lane="rbac_audit_mut"
      | eval cr_or_crb_name=obj
      | eval bundled_hit=0
      | eval agg_label_drift=0
      | eval orphan_subject=0
      | eval rules_cnt=null()
      | eval agg_flag=null()
      | eval agg_lbl_cnt=null()
      | eval bind_user=""
      | fields _time cluster actor verb res obj signal_lane cr_or_crb_name bundled_hit agg_label_drift orphan_subject rules_cnt agg_flag agg_lbl_cnt bind_user ]
    [ search index=ocp_inventory sourcetype=ocp_rbac_snapshot earliest=-24h@h latest=now
      | eval cluster=lower(trim(toString(coalesce(cluster, openshift_cluster, cluster_name, ""))))
      | eval cr_name=lower(trim(toString(coalesce(clusterrole_name, name, metadata_name, ""))))
      | eval rules_cnt=tonumber(trim(toString(coalesce(rules_count, rules_cnt, "0"))),10)
      | eval agg_flag=tonumber(trim(toString(coalesce(agg_rule_flag, aggregation_rule_flag, "0"))),10)
      | eval agg_lbl_cnt=tonumber(trim(toString(coalesce(aggregate_label_count, agg_label_cnt, "0"))),10)
      | eval signal_lane="rbac_snap_drift"
      | eval cr_or_crb_name=cr_name
      | eval actor="inventory_exporter"
      | eval verb="snapshot"
      | eval res="clusterroles"
      | eval obj=cr_name
      | eval bundled_hit=0
      | eval agg_label_drift=if(agg_lbl_cnt>=1 AND !match(cr_name,"^system:aggregator|^system:controller:|^system:|^openshift:"),1,0)
      | eval orphan_subject=0
      | eval bind_user=""
      | where agg_flag>=1 OR agg_lbl_cnt>=1 OR rules_cnt<=0
      | fields _time cluster actor verb res obj signal_lane cr_or_crb_name bundled_hit agg_label_drift orphan_subject rules_cnt agg_flag agg_lbl_cnt bind_user ]
    [ search (index=ocp_audit OR index=k8s_audit) (sourcetype=ocp_audit OR sourcetype=k8s_audit OR sourcetype=ocp_oauth_audit OR sourcetype="kube:apiserver:audit") earliest=-24h@h latest=now
      | eval cluster=lower(trim(toString(coalesce(cluster, openshift_cluster, cluster_name, k8s_cluster_name, ""))))
      | eval res=lower(trim(toString(coalesce('objectRef.resource', objectRef.resource, objectRef_resource, ""))))
      | eval verb=lower(trim(toString(coalesce(verb, requestVerb, request_verb, ""))))
      | where match(res,"clusterrolebindings") AND match(verb,"create|update|patch")
      | eval lr=lower(_raw)
      | rex field=lr max_match=0 "(?i)\"kind\"\s*:\s*\"User\"\s*,\s*\"name\"\s*:\s*\"(?<subj_user>[^\"]+)\""
      | eval bind_user=lower(trim(toString(coalesce(subj_user, ""))))
      | where len(bind_user)>1
      | join type=left max=0 cluster bind_user
          [| inputlookup ocp_oauth_user_identity_snapshot.csv
           | eval cluster=lower(trim(toString(cluster)))
           | eval bind_user=lower(trim(toString(coalesce(user_name, username, ""))))
           | eval idp_trusted=tonumber(trim(toString(coalesce(idp_trusted_flag, "1"))),10)
           | eval snap_present=1
           | fields cluster bind_user idp_trusted snap_present ]
      | eval actor=trim(toString(coalesce('user.username', user.username, user_username, "")))
      | eval cr_or_crb_name=trim(toString(coalesce('objectRef.name', objectRef.name, objectRef_name, "")))
      | eval orphan_subject=if(coalesce(snap_present,0)==0 OR idp_trusted==0,1,0)
      | eval signal_lane="oauth_bind_hygiene"
      | eval bundled_hit=0
      | eval agg_label_drift=0
      | eval obj=cr_or_crb_name
      | eval res="clusterrolebindings"
      | eval rules_cnt=null()
      | eval agg_flag=null()
      | eval agg_lbl_cnt=null()
      | fields _time cluster actor verb res obj signal_lane cr_or_crb_name bundled_hit agg_label_drift orphan_subject rules_cnt agg_flag agg_lbl_cnt bind_user ]
    [ search (index=ocp_audit OR index=k8s_audit) (sourcetype=ocp_audit OR sourcetype=k8s_audit OR sourcetype="kube:apiserver:audit") earliest=-24h@h latest=now
      | eval cluster=lower(trim(toString(coalesce(cluster, openshift_cluster, cluster_name, k8s_cluster_name, ""))))
      | eval res=lower(trim(toString(coalesce('objectRef.resource', objectRef.resource, objectRef_resource, ""))))
      | eval verb=lower(trim(toString(coalesce(verb, requestVerb, request_verb, ""))))
      | eval obj=lower(trim(toString(coalesce('objectRef.name', objectRef.name, objectRef_name, ""))))
      | where match(res,"clusterroles|clusterrolebindings") AND match(verb,"create|update|patch|delete")
      | eval bundled_hit=if(match(obj,"^(cluster-reader|cluster-monitoring-view|cluster-status|view|edit|admin|basic-user|system:discovery|system:public-info-viewer|system:basic-user)$") OR match(obj,"^system:openshift:"),1,0)
      | where bundled_hit=1
      | eval actor=trim(toString(coalesce('user.username', user.username, user_username, "")))
      | eval signal_lane="bundled_role_touch"
      | eval cr_or_crb_name=obj
      | eval agg_label_drift=0
      | eval orphan_subject=0
      | eval rules_cnt=null()
      | eval agg_flag=null()
      | eval agg_lbl_cnt=null()
      | eval bind_user=""
      | fields _time cluster actor verb res obj signal_lane cr_or_crb_name bundled_hit agg_label_drift orphan_subject rules_cnt agg_flag agg_lbl_cnt bind_user ]
| eval signal_type=signal_lane
| eval is_bind_evt=if(signal_lane=="rbac_audit_mut" AND match(res,"clusterrolebindings"),1,0)
| sort 0 cluster cr_or_crb_name - _time
| streamstats window=20 current=t global=f sum(is_bind_evt) AS bind_window_cnt by cluster
| eventstats max(bind_window_cnt) AS cluster_bind_peak by cluster
| eval binding_velocity_win=coalesce(bind_window_cnt,0)
| join type=left max=0 cluster cr_or_crb_name
    [| inputlookup approved_cluster_roles.csv
     | eval cluster=lower(trim(toString(cluster)))
     | eval cr_or_crb_name=lower(trim(toString(coalesce(clusterrole_name, cr_name, ""))))
     | eval approved_state=trim(toString(coalesce(approved_state, state, "")))
     | eval owner_team_lu=trim(toString(coalesce(owner_team, "")))
     | eval exception_expiry=tonumber(trim(toString(coalesce(exception_expiry_epoch, "0"))),10)
     | fields cluster cr_or_crb_name approved_state owner_team_lu exception_expiry ]
| fillnull value="" approved_state owner_team_lu
| eval now_e=now()
| eval baseline_ok=if(match(approved_state,"bundled_readonly|custom_allowed|approved") AND (exception_expiry==0 OR now_e<=exception_expiry),1,0)
| eval severity=case(
    bundled_hit==1 AND verb!="snapshot" AND match(verb,"patch|update|delete") AND baseline_ok==0, "critical",
    orphan_subject==1, "high",
    agg_label_drift==1 AND baseline_ok==0, "high",
    binding_velocity_win>=12, "high",
    bundled_hit==1 AND verb!="snapshot" AND baseline_ok==0, "medium",
    binding_velocity_win>=6, "medium",
    signal_lane=="rbac_audit_mut" AND match(res,"clusterrolebindings") AND baseline_ok==0, "medium",
    true(), "info")
| eval recommended_action=case(
    bundled_hit==1 AND match(verb,"delete"), "restore_bundled_clusterrole_from_supported_backup_and_open_vendor_case",
    orphan_subject==1, "oc_get_clusterrolebinding_prune_stale_subjects_and_reconcile_idp_mappings",
    agg_label_drift==1, "oc_get_clusterrole_labels_remove_unapproved_aggregate_labels",
    binding_velocity_win>=12, "freeze_gitops_rbac_and_review_automation_actor",
    true(), "correlate_audit_to_change_ticket_and_refresh_inventory_snapshot")
| table _time cluster signal_type cr_or_crb_name verb actor res bundled_hit agg_label_drift orphan_subject binding_velocity_win cluster_bind_peak baseline_ok approved_state owner_team_lu severity recommended_action bind_user rules_cnt agg_flag agg_lbl_cnt
```

## CIM SPL

```spl
| tstats summariesonly=t latest(Change.action) AS change_action latest(Change.object) AS change_object latest(Change.user) AS change_user FROM datamodel=Change WHERE nodename=Change earliest=-24h@h latest=now BY Change.dest
| rename Change.dest AS cim_dest
| join type=left max=0 cim_dest
    [| tstats summariesonly=t latest(Authentication.user) AS auth_user latest(Authentication.action) AS auth_action FROM datamodel=Authentication WHERE nodename=Authentication earliest=-24h@h latest=now BY Authentication.src
     | rename Authentication.src AS cim_dest ]
| where like(lower(change_object), "%clusterrole%") OR like(lower(change_object), "%clusterrolebinding%")
| table cim_dest change_action change_object change_user auth_user auth_action
```

## Visualization

Severity-colored table mirroring the closing SPL projection; timeline of binding_velocity_win by cluster; drilldown from signal_type to raw audit JSON and ocp_rbac_snapshot rows; matrix of bundled_hit roles by cluster for governance reviews.

## Known False Positives

Operator Lifecycle Manager installs and certified partner operators routinely create ClusterRoles with aggregation labels during upgrades; require approved_cluster_roles.csv rows and vendor documentation references before paging teams. OpenShift platform controllers reconcile bundled roles after upgrades; short bursts of update verbs on system roles may be healthy when ClusterVersion history shows an active rollout—join to change calendars. GitOps controllers applying large binding batches can spike binding_velocity_win without malice; suppress when automation_actor metadata matches known Flux or Argo CD service accounts. oc adm policy synchronization by break-glass administrators resembles abuse until tickets arrive; use allowlist exception_expiry_epoch thoughtfully. Hourly identity snapshots lag behind immediate user deletions; tune orphan_subject logic to avoid noise during known directory replication delays. Audit RequestResponse volume or field extraction gaps can hide subjects; validate parsers when orphan_subject fires without oc confirmation. Penetration tests mutate RBAC objects under authorization; ingest pentest windows into lookup suppressions. Duplicate HEC submissions double velocity counters; dedupe on auditID when present. Lab clusters that intentionally mutate bundled roles for training will page unless routed to non-production indexes.

## References

- [OpenShift Documentation — Using RBAC](https://docs.openshift.com/container-platform/latest/authentication/using-rbac.html)
- [OpenShift Documentation — Viewing audit logs](https://docs.openshift.com/container-platform/latest/security/audit-log-view.html)
- [OpenShift Documentation — Understanding authentication](https://docs.openshift.com/container-platform/latest/authentication/understanding-authentication.html)
- [Kubernetes Documentation — Using RBAC Authorization](https://kubernetes.io/docs/reference/access-authn-authz/rbac/)
- [Kubernetes Documentation — RBAC Good Practices](https://kubernetes.io/docs/concepts/security/rbac-good-practices/)
- [OpenShift API Reference — package rbac v1](https://github.com/openshift/api/blob/master/rbac/v1/doc.go)
- [Kubernetes API Reference — ClusterRoleBinding v1](https://kubernetes.io/docs/reference/kubernetes-api/authorization-resources/cluster-role-binding-v1/)
- [Red Hat Documentation Portal — OpenShift Container Platform](https://docs.redhat.com/en/documentation/openshift_container_platform/)
