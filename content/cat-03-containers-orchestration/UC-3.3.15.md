<!-- AUTO-GENERATED from UC-3.3.15.json — DO NOT EDIT -->

---
id: "3.3.15"
title: "OpenShift etcd Member Replacement Workflow, Operator-Managed Backup Health, and Quorum Loss Recovery Readiness"
status: "verified"
criticality: "critical"
splunkPillar: "Observability"
---

# UC-3.3.15 · OpenShift etcd Member Replacement Workflow, Operator-Managed Backup Health, and Quorum Loss Recovery Readiness

> **Criticality:** Critical &middot; **Difficulty:** Expert &middot; **Pillar:** Observability &middot; **Type:** Reliability, Availability &middot; **Wave:** Run &middot; **Status:** Verified

*We watch the automated caretakers that keep the cluster control database healthy, backed up on schedule, and ready for careful member repairs. When backups fall behind, a member starts failing, or the repair workflow shows warning signs, we raise a clear signal so engineers act before a small fault becomes a full outage.*

---

## Description

Correlates the OpenShift cluster-etcd-operator operand plane for disaster recovery readiness: Etcd cluster custom resource conditions such as EtcdMembersAvailable, EtcdMembersDegraded, MemberControllerDegraded, BootstrapTeardownDegraded, and ScriptControllerDegraded, operator-managed EtcdBackup schedule and last successful backup timestamps, Kubernetes events for member replacement and backup lifecycle reasons, audit churn involving cluster-etcd-operator reconciliation, cluster-etcd-operator and etcd static pod restart counters, etcd_server_has_leader and etcd_server_leader_changes_seen_total stability signals with coarse etcd_disk_backend_commit_duration_seconds_bucket tail hints, and etcd ClusterOperator rows strictly as corroboration against generic platform operator analytics.

## Value

Platform and reliability leaders gain a continuous ledger that answers whether a scrambled-quorum or control-plane restore remains realistic this week, not only whether etcd answered a health check in the last minute. Risk and audit stakeholders receive defensible evidence that scheduled and on-demand backups kept pace with change velocity, that member replacement ceremonies left an observable trail, and that operator degradation tied to ConfigMap drift or CEO instability was triaged before it collided with storage faults. The analytic shortens mean time to innocence by separating OpenShift-specific operator lifecycle signals from vanilla etcd raft metrics owned by UC-3.2.26 and deep histogram performance forensics owned by UC-3.2.8.

## Implementation

Land ocp_etcd_cr, ocp_etcdbackup, ocp_clusteroperator etcd rows, ocp_events, ocp_audit, optional ocp_etcd_audit, ocp_etcd_pod summaries, and prometheus etcd series into governed indexes with consistent cluster labels; normalize condition and backup status fields in props; save openshift_uc_3_3_15_etcd_operator_dr_readiness on a fifteen minute cadence over earliest=-6h@h; route page and warn severities to platform etcd on-call through the Splunk OpenShift App; archive weekly CSV exports for backup and restore governance reviews.

## Evidence

Saved search openshift_uc_3_3_15_etcd_operator_dr_readiness with fifteen minute schedule; Splunk OpenShift App dashboard drilldowns on ocp_etcd_cr, ocp_etcdbackup, ocp_clusteroperator etcd, ocp_events, ocp_audit, ocp_metrics lanes; weekly CSV exports to a restricted evidence index with change_ticket_id correlation.

## Control test

### Positive scenario

In a lab OpenShift cluster, ingest ocp_etcd_cr snapshots where EtcdMembersDegraded=True with message text referencing member health, add ocp_etcdbackup rows with a lastBackupTime older than twenty-six hours, add ocp_events with reason BackupFailed, and confirm openshift_uc_3_3_15_etcd_operator_dr_readiness returns page with non-null recommended_action within the scheduled window.

### Negative scenario

After recovery when oc get etcd cluster shows healthy member conditions, a fresh successful EtcdBackup within policy, clean member event reasons, etcd_server_has_leader samples at one, and stable cluster-etcd-operator pods, confirm severities return to info and the alert wrapper emits zero rows when filtering to page and warn only.

## Detailed Implementation

### Step 1 — Prerequisites

Head of Platform owns this control with the OpenShift control-plane engineering lead, the storage team that provisions control-plane node disks and etcd backup PersistentVolumeClaims, and the observability engineers who operate HTTP Event Collector tokens plus OpenTelemetry Collector agents that federate OpenShift Monitoring into Splunk. This use case isolates the cluster-etcd-operator plane on OpenShift 4: the operator.openshift.io Etcd custom resource named cluster, the operator-managed etcd backup workflow that materializes EtcdBackup objects under the etcd backup API group, the openshift-etcd static pod membership surface that administrators validate with oc -n openshift-etcd get pods -l app=etcd, and the disaster-recovery posture signals that determine whether a scrambled-quorum or full control-plane restore remains feasible within policy windows. UC-3.2.26 remains the vanilla Kubernetes etcd operational-quorum axis: raft leader visibility, learner posture, proposal pressure, and membership drift inferred primarily from per-member scrapes without interpreting OpenShift-specific Etcd CR conditions or operator-managed backup schedules. UC-3.2.8 remains deep etcd performance analytics on histogram commit latency, WAL fsync depth, and throughput saturation rather than operator lifecycle storytelling. UC-3.3.6 remains generic ClusterOperator reconciliation health across the fleet of platform operators; this UC drills into the etcd ClusterOperator operand, the Etcd CR status.conditions family, and backup history rather than repeating the full ClusterOperator matrix analytic. UC-3.3.15 deliberately consumes etcd ClusterOperator rows only as a corroborating lane so a silent Etcd CR exporter outage does not hide a genuinely degraded etcd operator reported through config.openshift.io.

RBAC and safety land before parsers. Collectors that export oc get etcd cluster -o json, oc get etcdbackup -A -o json, and oc get clusteroperator etcd -o json must use a dedicated ServiceAccount with get and list on Etcd and EtcdBackup resources plus get on clusteroperators.config.openshift.io, not personal cluster-admin kubeconfig files on laptops. Forwarders that ship control-plane audit paths via oc adm node-logs --role=master --path=audit/audit.log during investigations must run under break-glass procedures with read-only node access and explicit legal approval when request bodies could contain sensitive object fields. Prometheus federation scrapers should bind to metrics readers rather than kubeadmin. Legal review should confirm internal node names, peer DNS names, and certificate subjects referenced in Etcd condition messages are acceptable in Splunk retention tiers.

Index design: designate index=ocp_metrics for structured API snapshots with sourcetype=ocp_etcd_cr and sourcetype=ocp_etcdbackup when your exporter emits one JSON event per poll interval, plus sourcetype=ocp_clusteroperator rows filtered to metadata.name=etcd when you reuse the UC-3.3.6 snapshot pipeline with a name filter at ingest or in SPL. Land federated prometheus lines with sourcetype=prometheus:metrics or sourcetype=prometheus:ocp preserving __name__, le, instance, pod, namespace, and job labels for etcd_server_has_leader, etcd_server_leader_changes_seen_total, etcd_member_status when exposed, and etcd_disk_backend_commit_duration_seconds_bucket histogram series used here only as a coarse recovery-readiness correlate rather than a performance deep-dive. Designate index=ocp_events for Kubernetes events with sourcetype=ocp_events or sourcetype=k8s_events. Designate index=ocp_audit for Kubernetes API audit JSON with sourcetype=ocp_audit and optional sourcetype=ocp_etcd_audit when you split cluster-etcd-operator reconcile narratives into a dedicated sourcetype. Many teams also land etcd pod readiness snapshots with sourcetype=ocp_etcd_pod when a scripted input wraps oc -n openshift-etcd get pods -l app=etcd -o json and emits counts of Ready containers versus expected voting members for three-node and five-node control-plane topologies.

Field normalization expectations: flatten Etcd.status.conditions[] into parallel fields or child events with stable ordering; map types such as EtcdMembersAvailable, EtcdMembersDegraded, MemberControllerDegraded, BootstrapTeardownDegraded, and ScriptControllerDegraded into condition_type and condition_status columns; preserve lastTransitionTime per type; concatenate condition.message into etcd_cond_msg with length caps for storage economics. For EtcdBackup resources, map spec.schedule into backup_schedule_cron when present, map status.lastBackupTime into last_backup_epoch after strptime normalization, map status.completion or completion-equivalent fields into backup_completed_flag depending on your OpenShift minor exporter vocabulary, and retain involved PVC names when the operator documents BackupVar volume binding. Cluster identity must appear on every event as cluster, openshift_cluster, or cluster_name drawn from management-cluster context or external_labels on Prometheus scrapes.

Risk briefing: Progressing=True on the etcd ClusterOperator is normal during upgrades, certificate rotations, and brief static pod revision churn; alerts must pair Progressing with dwell thresholds, heartbeat age, and corroborating Etcd CR conditions rather than paging on every transient flip. EtcdMembersDegraded=True may appear during approved control-plane scaling ceremonies when converting topology or during staged etcd member replacement workflows; require multi-lane corroboration with events, backup posture, and CEO pod stability before executive escalation. BackupSucceeded spikes are healthy noise during scheduled CronJob windows; BackupFailed requires immediate correlation with PVC capacity, IO errors, and etcd quorum stability. MemberRemoved and MemberAdded events occur during documented replacement ceremonies; MemberFlapping and MemberFailed warrant faster response. A backup older than twenty-four hours is treated as a critical disaster-recovery posture warning in this UC because restore feasibility and change collision windows compound quickly on active clusters; tune the hour threshold per regulatory policy if counsel requires a shorter window.

Differentiation recap: cluster-etcd-operator Etcd CR semantics, operator-managed EtcdBackup posture, member replacement ceremony signals, CEO reconcile audit churn, etcd pod readiness versus quorum math, and DR readiness time-to-last-backup, not vanilla etcd histogram performance forensics alone, not generic ClusterOperator storytelling for non-etcd operators, not vanilla Kubernetes etcd scrape-only quorum analytics without OpenShift operator context.

Operational posture: stamp change_ticket_id onto HTTP Event Collector payloads when maintenance touches Etcd, EtcdBackup, ConfigMaps in openshift-etcd-operator, or control-plane node membership. When Splunk shows ScriptControllerDegraded with message hints about config mismatch, compare cluster-etcd-operator-config to documented platform defaults under vendor guidance before ad hoc edits. When bootstrap teardown windows run after install, expect short-lived BootstrapTeardownDegraded transitions that clear when the operator completes cleanup; pair with installation runbooks rather than assuming datastore corruption.

### Step 2 — Configure data collection

Stand up seven complementary lanes Splunk multisearch can fuse: periodic Etcd cluster API snapshots, periodic EtcdBackup snapshots including scheduled and on-demand objects, filtered etcd ClusterOperator snapshots or prometheus cluster_operator_conditions corroboration, Kubernetes events carrying member lifecycle and backup reasons, audit narratives for cluster-etcd-operator and etcd.operator.openshift.io writes, prometheus etcd member stability series including leader churn and coarse commit histogram buckets, and optional ocp_etcd_pod readiness summaries derived from oc get pod JSON.

Etcd CR snapshot lane: schedule a Python or Go utility every five minutes from a management host with kubeconfig authentication. The utility should run oc get etcd cluster -o json, flatten status.conditions into fields etcd_members_available, etcd_members_degraded, member_controller_degraded, bootstrap_teardown_degraded, script_controller_degraded with true or false tokens, preserve message and reason text, include generation and observedGeneration when present, and emit HTTP Event Collector JSON with sourcetype=ocp_etcd_cr and source=oc_get_etcd_cluster. Hash canonical JSON without volatile resourceVersion when tamper evidence is required.

EtcdBackup snapshot lane: extend the same utility or a sibling job to run oc get etcdbackup -A -o json on clusters where the etcd backup custom resource is enabled, capturing spec.schedule, spec PVC hints, status.lastBackupTime, status completion fields, and failure messages when operators populate them. Use sourcetype=ocp_etcdbackup. Separate scheduled backups from on-demand objects using metadata.labels or name patterns your platform standardizes so Splunk can tune noise.

ClusterOperator corroboration lane: reuse the UC-3.3.6 exporter with a name filter for etcd or add a lightweight oc get clusteroperator etcd -o json poller that copies Available, Progressing, Degraded, Upgradeable condition tuples into sourcetype=ocp_clusteroperator rows. This UC treats etcd ClusterOperator Degraded as an amplifier when Etcd CR lanes disagree with API snapshots, not as a replacement for Etcd condition semantics.

Events lane: forward Kubernetes events into index=ocp_events with sourcetype=ocp_events using Splunk Add-on for Kubernetes patterns or an OpenTelemetry k8s_events receiver. Retain reason, message, involvedObject.kind, involvedObject.name, involvedObject.namespace, type, count, and lastTimestamp. Ensure reasons such as MemberRemoved, MemberAdded, MemberFailed, MemberFlapping, BackupSucceeded, BackupFailed, EtcdRecovery, and BootstrapTeardown are not dropped at forwarder filters.

Audit lane: ship Kubernetes apiserver audit JSON into index=ocp_audit with sourcetype=ocp_audit at Metadata or RequestResponse levels consistent with volume policy. Extract verbs, user.username, objectRef.apiGroup, objectRef.resource, objectRef.name, and objectRef.namespace. For investigations, operators pull oc adm node-logs --role=master --path=audit/audit.log samples and compare UTC timestamps to Splunk _time. When volume allows, route high-signal cluster-etcd-operator reconcile bursts into sourcetype=ocp_etcd_audit using ingest-time routing rules matching userAgent or objectRef patterns.

Prometheus lane: federate etcd metrics from in-cluster monitoring targets into index=ocp_metrics with sourcetype=prometheus:metrics. Preserve labels needed to compute per-cluster aggregates. Validate instant queries in the OpenShift console for etcd_server_has_leader and etcd_server_leader_changes_seen_total before Splunk paging goes live. When histogram volume is costly, precompute recording rules for p95 commit duration per cluster and forward the recording series instead of raw buckets.

Etcd pod readiness lane: optional scripted input runs oc -n openshift-etcd get pods -l app=etcd -o json, counts Ready containers versus expected voting members for three or five node HA, emits sourcetype=ocp_etcd_pod with fields etcd_ready_cnt, etcd_desired_cnt, and quorum_needed computed as floor(desired/2)+1.

Example oc verification operators run during design reviews:

```bash
oc get etcd cluster -o yaml
oc get etcdbackup -A -o yaml
oc get clusteroperator etcd -o wide
oc -n openshift-etcd get pods -l app=etcd -o wide
oc -n openshift-etcd-operator get pods -l name=cluster-etcd-operator -o wide
oc adm node-logs --role=master --path=audit/audit.log | tail -n 50
```

props.conf guidance: TRUNCATE sufficiently large for JSON, TIMESTAMP_FIELDS respected when HTTP Event Collector time is authoritative, LINE_BREAKER rules for prometheus exposition when multiplexed with syslog headers, FIELDALIAS maps from dotted API paths to underscore fields used in SPL coalesce ladders.

Pre-save validation: index=ocp_events sourcetype=ocp_etcd_cr earliest=-1h must return events after the first poll; ocp_etcdbackup should appear when backups exist; ocp_events should show backup reasons during intentional on-demand backup tests; prometheus:metrics should include etcd_server_has_leader after scrape start; ocp_audit should show administrative verbs during controlled etcd object edits in lab.

Dashboards: the Splunk OpenShift App should host a severity-colored table keyed on cluster with drilldowns to raw Etcd JSON, EtcdBackup JSON, etcd ClusterOperator rows, event text, audit rows, and prometheus samples. Splunk ITSI users may bind KPIs to backup_age_h and etcd_cr_deg for platform service entities.

### Step 3 — Create the search and alert

Save the SPL as openshift_uc_3_3_15_etcd_operator_dr_readiness with a fifteen minute schedule during steady-state production, dispatch earliest=-6h@h, dispatch latest=now, and alert when severity is page or warn. Throttle duplicate cluster rows for thirty minutes unless severity escalates from warn to page. Include recommended_action, backup_age_h, leader_chg_delta, and ceo_etcd_rst in pager descriptions so incident commanders open etcd backup and member replacement runbooks without rerunning ad hoc searches.

Pipeline narrative for reviewers: multisearch fans Etcd CR condition arms, EtcdBackup posture arms, etcd ClusterOperator corroboration arms, member and backup event arms, optional CEO-focused audit churn arms, cluster-etcd-operator and etcd pod restart counters from prometheus, and prometheus etcd stability arms with streamstats deltas on leader change counters so a silent single sourcetype outage does not hide genuine degradation. coalesce() absorbs field naming drift across exporters. streamstats measures short-window leader election churn deltas per cluster after bucketed stats. eventstats adds fleet context such as percentile backup ages across clusters for executive heatmaps. case() maps critical combinations of EtcdMembersDegraded, stale backups beyond twenty-four hours, missing leader gauges, high CEO or etcd pod restart sums, and MemberFailed style event reasons into page versus warn versus info tiers. recommended_action encodes the next mechanical steps including oc get etcd cluster, oc get etcdbackup, review of openshift-etcd-operator logs, and correlation with OpenShift documentation procedures for replacing unhealthy etcd members and restoring cluster state, without pretending Splunk replaces etcdctl or platform support guidance.

Fenced SPL must match the spl JSON field exactly:

```spl
`comment("UC-3.3.15 cluster-etcd-operator Etcd CR, EtcdBackup posture, etcd ClusterOperator corroboration, member or backup events, CEO and etcd pod restarts, etcd leader churn. Required anchor lane: (index=ocp_audit OR index=ocp_events) sourcetype=ocp_clusteroperator OR sourcetype=ocp_etcd_cr OR sourcetype=ocp_etcdbackup OR sourcetype=ocp_etcd_pod OR sourcetype=ocp_etcd_audit OR sourcetype=k8s_events reason=MemberRemoved OR reason=MemberAdded OR reason=MemberFailed OR reason=BackupSucceeded OR reason=BackupFailed OR reason=EtcdRecovery OR reason=BootstrapTeardown. Supplement: mstats on etcd_server_has_leader plus raw prometheus etcd_disk_backend_commit_duration_seconds_bucket. Tunables: backup_page_h=24 backup_warn_h=12 ceo_rst_page=15 ceo_rst_warn=5 earliest=-6h@h latest=now")`
| multisearch
    [ search (index=ocp_audit OR index=ocp_events OR index=ocp_metrics) sourcetype=ocp_etcd_cr earliest=-6h@h latest=now
      | eval cluster=lower(trim(toString(coalesce(cluster, openshift_cluster, cluster_name, cluster_id, ""))))
      | eval dg=lower(trim(toString(coalesce(etcd_members_degraded, degraded, conditions_degraded, degraded_flag, ""))))
      | eval mem_deg_f=if(match(dg,"true|1"),1,0)
      | eval ma=tonumber(trim(toString(coalesce(etcd_members_available, members_available, ""))),10)
      | eval mt=tonumber(trim(toString(coalesce(etcd_members_total, members_total, ""))),10)
      | eval cond_msg=substr(trim(toString(coalesce(status_message, message, etcd_cond_msg, ""))),1,220)
      | stats latest(_time) AS last_cr_t max(mem_deg_f) AS etcd_cr_deg latest(ma) AS mem_avail latest(mt) AS mem_tot values(cond_msg) AS cr_msg_mv BY cluster ]
    [ search (index=ocp_audit OR index=ocp_events OR index=ocp_metrics) sourcetype=ocp_etcdbackup earliest=-6h@h latest=now
      | eval cluster=lower(trim(toString(coalesce(cluster, openshift_cluster, cluster_name, ""))))
      | eval lbu=trim(toString(coalesce(lastBackupTime, last_backup_time, status_lastBackupTime, "")))
      | eval last_bu_epoch=if(match(lbu,"^[0-9]{4}-"), strptime(lbu,"%Y-%m-%dT%H:%M:%SZ"), null())
      | eval comp=lower(trim(toString(coalesce(completed, status_completed, backup_completed, ""))))
      | eval bu_ok=if(match(comp,"true|complete|succeeded|success"),1,0)
      | stats latest(_time) AS last_bak_t max(bu_ok) AS bu_ok latest(last_bu_epoch) AS last_bu_epoch BY cluster ]
    [ search (index=ocp_audit OR index=ocp_events OR index=ocp_metrics) sourcetype=ocp_clusteroperator earliest=-6h@h latest=now
      | eval cluster=lower(trim(toString(coalesce(cluster, openshift_cluster, cluster_name, ""))))
      | eval op=lower(trim(toString(coalesce(name, operator, metadata_name, ""))))
      | where op="etcd"
      | eval co_deg=if(match(lower(toString(coalesce(degraded, conditions_degraded, ""))),"true|1"),1,0)
      | eval co_prog=if(match(lower(toString(coalesce(progressing, conditions_progressing, ""))),"true|1"),1,0)
      | stats latest(_time) AS last_co_t max(co_deg) AS co_deg max(co_prog) AS co_prog BY cluster ]
    [ search (index=ocp_audit OR index=ocp_events) (sourcetype=ocp_events OR sourcetype=k8s_events OR sourcetype=ocp_etcd_pod OR sourcetype=ocp_etcd_audit OR sourcetype=ocp_audit) earliest=-6h@h latest=now
      | eval cluster=lower(trim(toString(coalesce(cluster, openshift_cluster, cluster_name, ""))))
      | eval reason=trim(toString(coalesce(reason, Reason, "")))
      | eval msg=lower(toString(coalesce(message, Message, _raw, "")))
      | where reason="MemberRemoved" OR reason="MemberAdded" OR reason="MemberFailed" OR reason="MemberFlapping" OR reason="BackupSucceeded" OR reason="BackupFailed" OR reason="EtcdRecovery" OR reason="BootstrapTeardown" OR match(msg,"memberremoved|memberadded|memberfailed|memberflapping|backupsucceeded|backupfailed|etcdrecovery|bootstrapteardown")
      | stats latest(_time) AS last_evt_t values(reason) AS evt_reasons count AS evt_cnt BY cluster ]
    [ search index=ocp_metrics (sourcetype=prometheus:metrics OR sourcetype=prometheus:ocp OR sourcetype=ocp_etcd_pod) earliest=-6h@h latest=now
      | eval cluster=lower(trim(toString(coalesce(cluster, openshift_cluster, cluster_name, k8s_cluster_name, ""))))
      | eval ns=lower(trim(toString(coalesce(namespace, k8s_namespace, ""))))
      | eval pod=lower(trim(toString(coalesce(pod, pod_name, ""))))
      | eval mn=lower(trim(toString(coalesce(__name__, metric_name, name, ""))))
      | eval mv=tonumber(tostring(coalesce(value, metric_value, Value, "0")),10)
      | where match(mn,"kube_pod_container_status_restarts_total|container_restart_count")
      | where (match(ns,"openshift-etcd-operator") AND match(pod,"cluster-etcd-operator")) OR (match(ns,"openshift-etcd") AND match(pod,"^etcd"))
      | stats sum(mv) AS ceo_etcd_rst latest(_time) AS last_rst_t BY cluster ]
    [ search index=ocp_metrics (sourcetype=prometheus:metrics OR sourcetype=prometheus:ocp) earliest=-6h@h latest=now
      | eval cluster=lower(trim(toString(coalesce(cluster, openshift_cluster, cluster_name, k8s_cluster_name, ""))))
      | eval mn=lower(trim(toString(coalesce(__name__, metric_name, name, ""))))
      | eval mv=tonumber(tostring(coalesce(value, metric_value, Value, "0")),10)
      | where mn="etcd_server_has_leader" OR mn="etcd_server_leader_changes_seen_total" OR mn="etcd_disk_backend_commit_duration_seconds_bucket"
      | eval le_lab=trim(toString(coalesce(le, le_label, "")))
      | eval is_inf=if(match(le_lab,"^\\+Inf$") OR match(le_lab,"^\\\\+Inf$"),1,0)
      | bucket _time span=15m
      | stats max(eval(if(mn=="etcd_server_has_leader",mv,null()))) AS has_leader_max max(eval(if(mn=="etcd_server_leader_changes_seen_total",mv,null()))) AS leader_chg_hi max(eval(if(mn=="etcd_disk_backend_commit_duration_seconds_bucket" AND is_inf==1,mv,null()))) AS commit_hist_inf BY cluster _time
      | sort 0 cluster - _time
      | streamstats window=2 current=t global=f last(leader_chg_hi) AS prev_lc BY cluster
      | eval leader_chg_delta=max(0, coalesce(leader_chg_hi,0)-coalesce(prev_lc,0))
      | stats max(leader_chg_delta) AS leader_chg_delta min(has_leader_max) AS cluster_min_leader max(commit_hist_inf) AS commit_hist_inf latest(_time) AS last_prom_t BY cluster ]
    [ | mstats prestats=t avg(_value) AS mv WHERE index=ocp_metrics metric_name="etcd_server_has_leader" span=15m BY cluster
      | eval cluster=lower(trim(toString(coalesce(cluster, openshift_cluster, cluster_name, ""))))
      | stats latest(mv) AS mstats_leader_avg latest(_time) AS last_mstats_t BY cluster ]
| stats max(last_cr_t) AS last_cr_t max(etcd_cr_deg) AS etcd_cr_deg max(mem_avail) AS mem_avail max(mem_tot) AS mem_tot max(last_bak_t) AS last_bak_t max(bu_ok) AS bu_ok max(last_bu_epoch) AS last_bu_epoch max(last_co_t) AS last_co_t max(co_deg) AS co_deg max(co_prog) AS co_prog max(last_evt_t) AS last_evt_t values(evt_reasons) AS evt_reasons sum(eval(coalesce(evt_cnt,0))) AS evt_cnt max(ceo_etcd_rst) AS ceo_etcd_rst max(last_rst_t) AS last_rst_t max(leader_chg_delta) AS leader_chg_delta min(cluster_min_leader) AS cluster_min_leader max(commit_hist_inf) AS commit_hist_inf max(last_prom_t) AS last_prom_t max(mstats_leader_avg) AS mstats_leader_avg max(last_mstats_t) AS last_mstats_t values(cr_msg_mv) AS cr_msg_mv BY cluster
| eval cr_msg=substr(trim(toString(mvindex(mvdedup(cr_msg_mv),0))),1,180)
| eval backup_age_h=if(isnotnull(last_bu_epoch) AND last_bu_epoch>0, round((now()-last_bu_epoch)/3600,3), null())
| eval evt_blob=lower(trim(toString(mvjoin(mvdedup(evt_reasons), "|"))))
| eval member_fail_f=if(match(evt_blob,"memberfailed"),1,0)
| eval backup_fail_f=if(match(evt_blob,"backupfailed"),1,0)
| eval no_leader=if(isnotnull(cluster_min_leader) AND cluster_min_leader<1,1,0)
| eventstats perc90(backup_age_h) AS fleet_backup_age_p90
| eval severity=case(
    member_fail_f==1 OR backup_fail_f==1, "page",
    no_leader==1, "page",
    coalesce(backup_age_h,0)>24, "page",
    coalesce(ceo_etcd_rst,0)>=15, "page",
    etcd_cr_deg==1 AND co_deg==1, "page",
    etcd_cr_deg==1 OR co_deg==1, "warn",
    coalesce(backup_age_h,0)>12, "warn",
    leader_chg_delta>=4 OR coalesce(ceo_etcd_rst,0)>=5, "warn",
    leader_chg_delta>=2 OR coalesce(commit_hist_inf,0)>0, "warn",
    true(), "info")
| eval recommended_action=case(
    member_fail_f==1, "open_replace_unhealthy_etcd_member_runbook_and_gather_must_gather",
    backup_fail_f==1, "inspect_etcdbackup_pvc_and_operator_logs_confirm_write_path",
    no_leader==1, "verify_etcd_metrics_endpoints_and_oc_get_pods_app_etcd",
    coalesce(backup_age_h,0)>24, "execute_on_demand_backup_or_fix_scheduled_etcd_backup_job",
    etcd_cr_deg==1 OR co_deg==1, "oc_describe_etcd_cluster_and_correlate_ceo_conditions",
    coalesce(ceo_etcd_rst,0)>=5, "collect_cluster_etcd_operator_logs_and_review_configmap_drift",
    leader_chg_delta>=2, "check_control_plane_disk_latency_and_ntp_then_correlate_uc_3_2_26",
    true(), "refresh_etcd_cr_etcdbackup_snapshots_and_validate_prometheus_etcd_metrics")
| join type=left max=0 cluster
    [| inputlookup openshift_cluster_inventory.csv
     | fields cluster, cluster_tier, owner_team, environment]
| eval cluster_tier=coalesce(cluster_tier, "unrated"),
       owner_team=coalesce(owner_team, "unowned"),
       environment=coalesce(environment, "unknown")
| table cluster etcd_cr_deg mem_avail mem_tot backup_age_h bu_ok co_deg co_prog evt_reasons ceo_etcd_rst leader_chg_delta cluster_min_leader mstats_leader_avg commit_hist_inf backup_fail_f member_fail_f fleet_backup_age_p90 severity recommended_action last_co_t last_bak_t last_prom_t cr_msg last_cr_t last_mstats_t cluster_tier owner_team environment
```

savedsearches.conf sketch:

```ini
[openshift_uc_3_3_15_etcd_operator_dr_readiness_alert]
cron_schedule = */15 * * * *
dispatch.earliest_time = -6h@h
dispatch.latest_time = now
enableSched = 1
action.email = 1
action.email.to = openshift-platform@example.com
action.email.subject = OCP etcd CEO DR readiness $result.severity$ $result.cluster$
counttype = number of events
relation = greater than
quantity = 0
search = | savedsearch openshift_uc_3_3_15_etcd_operator_dr_readiness | where severity IN ("page","warn")
```

Performance: if Job Inspector shows multisearch queue time above internal service level objectives, materialize ocp_etcd_cr and ocp_etcdbackup snapshots hourly into a summary index keyed on cluster, widen alert searches to earliest=-2h@h on the summary, and retain this full search for investigations.

For Splunk ITSI optional deployments, bind KPIs to backup_age_h and to maximum leader_chg_delta per cluster, opening episodes when two consecutive windows remain non-info for production entities.

### Step 4 — Validate

Ground truth always starts on-cluster. Run oc get etcd cluster -o yaml and compare EtcdMembersAvailable, EtcdMembersDegraded, MemberControllerDegraded, BootstrapTeardownDegraded, and ScriptControllerDegraded transitions to Splunk rows inside the last snapshot window. When statuses disagree, verify resourceVersion freshness, indexer clock skew, and duplicate cluster labels across regions before blaming parsers.

EtcdBackup validation: run oc get etcdbackup -A -o yaml and compare status.lastBackupTime and completion fields to Splunk last_bu_epoch and bu_ok hints. Induce a lab on-demand backup where policy permits and confirm BackupSucceeded reasons appear in ocp_events within the expected interval.

ClusterOperator validation: run oc get clusteroperator etcd -o wide and compare AVAILABLE, PROGRESSING, and DEGRADED columns to Splunk co_deg and co_prog hints. Escalate to UC-3.3.6 owners if etcd is healthy on the API but other operators drive fleet-wide degradation unrelated to this UC.

Pod and quorum validation: run oc -n openshift-etcd get pods -l app=etcd and confirm three or five Ready etcd pods for HA topologies. Compare counts to Splunk mem_avail and mem_tot fields when your exporter includes them, or to ocp_etcd_pod summaries when enabled.

Prometheus validation: in the OpenShift console monitoring stack, validate etcd_server_has_leader and etcd_server_leader_changes_seen_total for the same cluster labels Splunk indexes. When metrics disagree with events, suspect scrape gaps, TLS target drift, or label collisions between management clusters.

Synthetic negative test: on a cluster with fresh successful backup, clean Etcd conditions, stable CEO pods, and low leader churn, confirm the alert wrapper returns zero rows when filtering to page and warn only.

Synthetic positive test: in lab under vendor guidance, simulate a backup failure by pointing a test EtcdBackup PVC to an intentionally full volume class or by revoking write permissions on the backup mount, observe BackupFailed reasons, and confirm openshift_uc_3_3_15_etcd_operator_dr_readiness returns warn or page with non-null recommended_action. Roll back and confirm recovery.

Runbook linkage: document expected member replacement ceremonies so validators do not treat MemberRemoved plus MemberAdded sequences as incidents when change tickets authorize the workflow.

### Step 5 — Operationalize & Troubleshoot

Case 1 — EtcdMembersDegraded with healthy static pods: read Etcd condition messages for revision or static pod mismatch hints, gather cluster-etcd-operator logs, compare latest installer revision objects to running static pod revisions, and engage support before manual etcdctl intervention.

Case 2 — ScriptControllerDegraded citing config map mismatch: compare cluster-etcd-operator-config to documented defaults, review recent GitOps or manual ConfigMap edits, roll back under change control, and restart only per vendor guidance.

Case 3 — BootstrapTeardownDegraded during install cleanup: pair with installation troubleshooting documentation, confirm bootstrap node removal milestones, and avoid paging production leadership for short windows that clear when teardown completes.

Case 4 — BackupFailed with PVC volume binding errors: describe the etcd-backup PVC events, verify storage class quotas, confirm zone or topology selectors, and expand capacity or fix binding before quorum stress accumulates.

Case 5 — Backup age beyond twenty-four hours during change freeze: if freeze policy intentionally pauses automated backups, document compensating controls and temporary suppressions with ticket identifiers on HTTP Event Collector payloads; otherwise treat as critical DR posture debt.

Case 6 — MemberFailed events without a change ticket: treat as high priority, verify member health endpoints, review recent control-plane node hardware faults, and prepare for documented replacement workflow.

Case 7 — MemberFlapping during network maintenance: correlate switch or load balancer work, capture peer latency metrics, and distinguish transient partitions from persistent member corruption using operator messages and support must-gather.

Case 8 — cluster-etcd-operator pod restart storm: inspect operator logs for watch failures, verify kube-apiserver and etcd reachability from the operator pod, check for admission webhook stalls that block writes, and correlate with UC-3.3.6 only for cross-operator context.

Case 9 — etcd pod restarts with rising leader_chg_delta: suspect disk latency or clock skew on a subset of control-plane nodes; engage storage and NTP teams; escalate to UC-3.2.8 owners when sustained histogram regression requires performance forensics beyond this UC.

Case 10 — Scrambled-quorum rehearsal calendar drift: governance teams track restore test runs outside Splunk; when calendar evidence slips, raise risk through process channels even if metrics look healthy, because procedural readiness is part of DR posture.

Case 11 — Duplicate telemetry from redundant exporters: dedupe on cluster and snapshot_generation in summary indexes when cost matters; validate that throttling does not hide legitimate rapid condition flips.

Case 12 — Fleet-wide info severities only: weekly spot-check Splunk rows against oc get etcd cluster and oc get etcdbackup on every production cluster to confirm parsers, tokens, and cluster labels remain aligned after OpenShift minor upgrades.

Closing checklist: multisearch lists Etcd CR, EtcdBackup, etcd ClusterOperator, event, audit, pod restart, and prometheus etcd stability arms; coalesce normalizes cluster fields; streamstats quantifies leader churn deltas; eventstats adds fleet context; case() implements severity tiers; closing table includes cluster, etcd_cr_deg, mem_avail, mem_tot, backup_age_h, bu_ok, co_deg, co_prog, evt_reasons, ceo_etcd_rst, leader_chg_delta, cluster_min_leader, mstats_leader_avg, commit_hist_inf, fleet_backup_age_p90, severity, recommended_action, last_co_t, last_bak_t, last_prom_t, cr_msg, last_cr_t, and last_mstats_t for analyst review.


## SPL

```spl
`comment("UC-3.3.15 cluster-etcd-operator Etcd CR, EtcdBackup posture, etcd ClusterOperator corroboration, member or backup events, CEO and etcd pod restarts, etcd leader churn. Required anchor lane: (index=ocp_audit OR index=ocp_events) sourcetype=ocp_clusteroperator OR sourcetype=ocp_etcd_cr OR sourcetype=ocp_etcdbackup OR sourcetype=ocp_etcd_pod OR sourcetype=ocp_etcd_audit OR sourcetype=k8s_events reason=MemberRemoved OR reason=MemberAdded OR reason=MemberFailed OR reason=BackupSucceeded OR reason=BackupFailed OR reason=EtcdRecovery OR reason=BootstrapTeardown. Supplement: mstats on etcd_server_has_leader plus raw prometheus etcd_disk_backend_commit_duration_seconds_bucket. Tunables: backup_page_h=24 backup_warn_h=12 ceo_rst_page=15 ceo_rst_warn=5 earliest=-6h@h latest=now")`
| multisearch
    [ search (index=ocp_audit OR index=ocp_events OR index=ocp_metrics) sourcetype=ocp_etcd_cr earliest=-6h@h latest=now
      | eval cluster=lower(trim(toString(coalesce(cluster, openshift_cluster, cluster_name, cluster_id, ""))))
      | eval dg=lower(trim(toString(coalesce(etcd_members_degraded, degraded, conditions_degraded, degraded_flag, ""))))
      | eval mem_deg_f=if(match(dg,"true|1"),1,0)
      | eval ma=tonumber(trim(toString(coalesce(etcd_members_available, members_available, ""))),10)
      | eval mt=tonumber(trim(toString(coalesce(etcd_members_total, members_total, ""))),10)
      | eval cond_msg=substr(trim(toString(coalesce(status_message, message, etcd_cond_msg, ""))),1,220)
      | stats latest(_time) AS last_cr_t max(mem_deg_f) AS etcd_cr_deg latest(ma) AS mem_avail latest(mt) AS mem_tot values(cond_msg) AS cr_msg_mv BY cluster ]
    [ search (index=ocp_audit OR index=ocp_events OR index=ocp_metrics) sourcetype=ocp_etcdbackup earliest=-6h@h latest=now
      | eval cluster=lower(trim(toString(coalesce(cluster, openshift_cluster, cluster_name, ""))))
      | eval lbu=trim(toString(coalesce(lastBackupTime, last_backup_time, status_lastBackupTime, "")))
      | eval last_bu_epoch=if(match(lbu,"^[0-9]{4}-"), strptime(lbu,"%Y-%m-%dT%H:%M:%SZ"), null())
      | eval comp=lower(trim(toString(coalesce(completed, status_completed, backup_completed, ""))))
      | eval bu_ok=if(match(comp,"true|complete|succeeded|success"),1,0)
      | stats latest(_time) AS last_bak_t max(bu_ok) AS bu_ok latest(last_bu_epoch) AS last_bu_epoch BY cluster ]
    [ search (index=ocp_audit OR index=ocp_events OR index=ocp_metrics) sourcetype=ocp_clusteroperator earliest=-6h@h latest=now
      | eval cluster=lower(trim(toString(coalesce(cluster, openshift_cluster, cluster_name, ""))))
      | eval op=lower(trim(toString(coalesce(name, operator, metadata_name, ""))))
      | where op="etcd"
      | eval co_deg=if(match(lower(toString(coalesce(degraded, conditions_degraded, ""))),"true|1"),1,0)
      | eval co_prog=if(match(lower(toString(coalesce(progressing, conditions_progressing, ""))),"true|1"),1,0)
      | stats latest(_time) AS last_co_t max(co_deg) AS co_deg max(co_prog) AS co_prog BY cluster ]
    [ search (index=ocp_audit OR index=ocp_events) (sourcetype=ocp_events OR sourcetype=k8s_events OR sourcetype=ocp_etcd_pod OR sourcetype=ocp_etcd_audit OR sourcetype=ocp_audit) earliest=-6h@h latest=now
      | eval cluster=lower(trim(toString(coalesce(cluster, openshift_cluster, cluster_name, ""))))
      | eval reason=trim(toString(coalesce(reason, Reason, "")))
      | eval msg=lower(toString(coalesce(message, Message, _raw, "")))
      | where reason="MemberRemoved" OR reason="MemberAdded" OR reason="MemberFailed" OR reason="MemberFlapping" OR reason="BackupSucceeded" OR reason="BackupFailed" OR reason="EtcdRecovery" OR reason="BootstrapTeardown" OR match(msg,"memberremoved|memberadded|memberfailed|memberflapping|backupsucceeded|backupfailed|etcdrecovery|bootstrapteardown")
      | stats latest(_time) AS last_evt_t values(reason) AS evt_reasons count AS evt_cnt BY cluster ]
    [ search index=ocp_metrics (sourcetype=prometheus:metrics OR sourcetype=prometheus:ocp OR sourcetype=ocp_etcd_pod) earliest=-6h@h latest=now
      | eval cluster=lower(trim(toString(coalesce(cluster, openshift_cluster, cluster_name, k8s_cluster_name, ""))))
      | eval ns=lower(trim(toString(coalesce(namespace, k8s_namespace, ""))))
      | eval pod=lower(trim(toString(coalesce(pod, pod_name, ""))))
      | eval mn=lower(trim(toString(coalesce(__name__, metric_name, name, ""))))
      | eval mv=tonumber(tostring(coalesce(value, metric_value, Value, "0")),10)
      | where match(mn,"kube_pod_container_status_restarts_total|container_restart_count")
      | where (match(ns,"openshift-etcd-operator") AND match(pod,"cluster-etcd-operator")) OR (match(ns,"openshift-etcd") AND match(pod,"^etcd"))
      | stats sum(mv) AS ceo_etcd_rst latest(_time) AS last_rst_t BY cluster ]
    [ search index=ocp_metrics (sourcetype=prometheus:metrics OR sourcetype=prometheus:ocp) earliest=-6h@h latest=now
      | eval cluster=lower(trim(toString(coalesce(cluster, openshift_cluster, cluster_name, k8s_cluster_name, ""))))
      | eval mn=lower(trim(toString(coalesce(__name__, metric_name, name, ""))))
      | eval mv=tonumber(tostring(coalesce(value, metric_value, Value, "0")),10)
      | where mn="etcd_server_has_leader" OR mn="etcd_server_leader_changes_seen_total" OR mn="etcd_disk_backend_commit_duration_seconds_bucket"
      | eval le_lab=trim(toString(coalesce(le, le_label, "")))
      | eval is_inf=if(match(le_lab,"^\\+Inf$") OR match(le_lab,"^\\\\+Inf$"),1,0)
      | bucket _time span=15m
      | stats max(eval(if(mn=="etcd_server_has_leader",mv,null()))) AS has_leader_max max(eval(if(mn=="etcd_server_leader_changes_seen_total",mv,null()))) AS leader_chg_hi max(eval(if(mn=="etcd_disk_backend_commit_duration_seconds_bucket" AND is_inf==1,mv,null()))) AS commit_hist_inf BY cluster _time
      | sort 0 cluster - _time
      | streamstats window=2 current=t global=f last(leader_chg_hi) AS prev_lc BY cluster
      | eval leader_chg_delta=max(0, coalesce(leader_chg_hi,0)-coalesce(prev_lc,0))
      | stats max(leader_chg_delta) AS leader_chg_delta min(has_leader_max) AS cluster_min_leader max(commit_hist_inf) AS commit_hist_inf latest(_time) AS last_prom_t BY cluster ]
    [ | mstats prestats=t avg(_value) AS mv WHERE index=ocp_metrics metric_name="etcd_server_has_leader" span=15m BY cluster
      | eval cluster=lower(trim(toString(coalesce(cluster, openshift_cluster, cluster_name, ""))))
      | stats latest(mv) AS mstats_leader_avg latest(_time) AS last_mstats_t BY cluster ]
| stats max(last_cr_t) AS last_cr_t max(etcd_cr_deg) AS etcd_cr_deg max(mem_avail) AS mem_avail max(mem_tot) AS mem_tot max(last_bak_t) AS last_bak_t max(bu_ok) AS bu_ok max(last_bu_epoch) AS last_bu_epoch max(last_co_t) AS last_co_t max(co_deg) AS co_deg max(co_prog) AS co_prog max(last_evt_t) AS last_evt_t values(evt_reasons) AS evt_reasons sum(eval(coalesce(evt_cnt,0))) AS evt_cnt max(ceo_etcd_rst) AS ceo_etcd_rst max(last_rst_t) AS last_rst_t max(leader_chg_delta) AS leader_chg_delta min(cluster_min_leader) AS cluster_min_leader max(commit_hist_inf) AS commit_hist_inf max(last_prom_t) AS last_prom_t max(mstats_leader_avg) AS mstats_leader_avg max(last_mstats_t) AS last_mstats_t values(cr_msg_mv) AS cr_msg_mv BY cluster
| eval cr_msg=substr(trim(toString(mvindex(mvdedup(cr_msg_mv),0))),1,180)
| eval backup_age_h=if(isnotnull(last_bu_epoch) AND last_bu_epoch>0, round((now()-last_bu_epoch)/3600,3), null())
| eval evt_blob=lower(trim(toString(mvjoin(mvdedup(evt_reasons), "|"))))
| eval member_fail_f=if(match(evt_blob,"memberfailed"),1,0)
| eval backup_fail_f=if(match(evt_blob,"backupfailed"),1,0)
| eval no_leader=if(isnotnull(cluster_min_leader) AND cluster_min_leader<1,1,0)
| eventstats perc90(backup_age_h) AS fleet_backup_age_p90
| eval severity=case(
    member_fail_f==1 OR backup_fail_f==1, "page",
    no_leader==1, "page",
    coalesce(backup_age_h,0)>24, "page",
    coalesce(ceo_etcd_rst,0)>=15, "page",
    etcd_cr_deg==1 AND co_deg==1, "page",
    etcd_cr_deg==1 OR co_deg==1, "warn",
    coalesce(backup_age_h,0)>12, "warn",
    leader_chg_delta>=4 OR coalesce(ceo_etcd_rst,0)>=5, "warn",
    leader_chg_delta>=2 OR coalesce(commit_hist_inf,0)>0, "warn",
    true(), "info")
| eval recommended_action=case(
    member_fail_f==1, "open_replace_unhealthy_etcd_member_runbook_and_gather_must_gather",
    backup_fail_f==1, "inspect_etcdbackup_pvc_and_operator_logs_confirm_write_path",
    no_leader==1, "verify_etcd_metrics_endpoints_and_oc_get_pods_app_etcd",
    coalesce(backup_age_h,0)>24, "execute_on_demand_backup_or_fix_scheduled_etcd_backup_job",
    etcd_cr_deg==1 OR co_deg==1, "oc_describe_etcd_cluster_and_correlate_ceo_conditions",
    coalesce(ceo_etcd_rst,0)>=5, "collect_cluster_etcd_operator_logs_and_review_configmap_drift",
    leader_chg_delta>=2, "check_control_plane_disk_latency_and_ntp_then_correlate_uc_3_2_26",
    true(), "refresh_etcd_cr_etcdbackup_snapshots_and_validate_prometheus_etcd_metrics")
| join type=left max=0 cluster
    [| inputlookup openshift_cluster_inventory.csv
     | fields cluster, cluster_tier, owner_team, environment]
| eval cluster_tier=coalesce(cluster_tier, "unrated"),
       owner_team=coalesce(owner_team, "unowned"),
       environment=coalesce(environment, "unknown")
| table cluster etcd_cr_deg mem_avail mem_tot backup_age_h bu_ok co_deg co_prog evt_reasons ceo_etcd_rst leader_chg_delta cluster_min_leader mstats_leader_avg commit_hist_inf backup_fail_f member_fail_f fleet_backup_age_p90 severity recommended_action last_co_t last_bak_t last_prom_t cr_msg last_cr_t last_mstats_t cluster_tier owner_team environment
```

## CIM SPL

```spl
| tstats summariesonly=t latest(Inventory.vendor_product) AS vendor_product latest(Inventory.version) AS inv_version FROM datamodel=Inventory WHERE nodename=Inventory earliest=-24h@h latest=now BY Inventory.dest
| rename Inventory.dest AS inv_dest
| join type=left max=0 inv_dest
    [| tstats summariesonly=t latest(Application_State.state) AS app_state latest(Application_State.info) AS app_info FROM datamodel=Application_State WHERE nodename=Application_State earliest=-24h@h latest=now BY Application_State.dest
     | rename Application_State.dest AS inv_dest ]
| where like(lower(vendor_product), "%openshift%") OR like(lower(app_info), "%etcd%") OR like(lower(app_info), "%openshift%operator%")
| table inv_dest vendor_product inv_version app_state app_info
```

## Visualization

Severity-colored table by cluster with drilldowns to ocp_etcd_cr JSON, ocp_etcdbackup JSON, etcd ClusterOperator rows, ocp_events text, ocp_audit and ocp_etcd_audit rows, prometheus etcd metric lines, and optional ocp_etcd_pod readiness tiles; timeline of backup_age_h; single-value tiles for leader_chg_delta and ceo_etcd_rst.

## Known False Positives

Deliberate change-freeze policies sometimes pause scheduled etcd backups when storage maintenance forbids snapshot IO; stamp change_ticket_id onto HTTP Event Collector payloads and document compensating manual backup runs before muting pages. Rolling reboots of control-plane nodes during kernel upgrades can elevate cluster-etcd-operator and etcd pod restart counters without backup posture regression; require dwell thresholds and ticket correlation. Planned oc adm cluster restore rehearsals and disaster-recovery game days intentionally emit EtcdRecovery or BootstrapTeardown adjacent signals; route those windows through lookup suppressions tied to calendar artifacts. ConfigMap rotations for cluster-etcd-operator-config can briefly surface Progressing=True on the etcd ClusterOperator while revisions settle; pair with short dwell before treating as incident. Transient EtcdMembersDegraded during approved control-plane scaling from three to five nodes may track single-master conversion work; validate against migration runbooks rather than assuming datastore corruption. BackupSucceeded bursts during CronJob overlap windows can look noisy in low-volume indexes; dedupe on involvedObject.uid when present. Duplicate forwarders can double event counts; dedupe on audit auditID or equivalent correlation identifiers. Some managed offerings restrict etcd metric cardinality or redact certain event reasons; expect metric-heavy firing and validate ground truth with oc commands during incidents. Vendor extensions that push snapshots to object storage may lag Splunk visibility until the transfer job completes; corroborate with object store lifecycle metrics outside this UC before declaring backup success. Penetration tests that simulate API denial against etcd backup namespaces may trip backup failure logic; ingest pentest authorization lookups with start and end epochs.

## References

- [OpenShift Documentation — Backing up etcd](https://docs.openshift.com/container-platform/latest/backup_and_restore/control_plane_backup_and_restore/backing-up-etcd.html)
- [OpenShift Documentation — Replacing an unhealthy etcd member](https://docs.openshift.com/container-platform/latest/backup_and_restore/control_plane_backup_and_restore/replacing-unhealthy-etcd-member.html)
- [OpenShift Documentation — Restoring to a previous cluster state (scenario 2)](https://docs.openshift.com/container-platform/latest/backup_and_restore/control_plane_backup_and_restore/disaster_recovery/scenario-2-restoring-cluster-state.html)
- [OpenShift Documentation — Cluster etcd Operator](https://docs.openshift.com/container-platform/latest/nodes/cluster-etcd-operator.html)
- [OpenShift Documentation — Troubleshooting installations](https://docs.openshift.com/container-platform/latest/support/troubleshooting/troubleshooting-installations.html)
- [OpenShift REST API Reference — Etcd [operator.openshift.io/v1]](https://docs.openshift.com/container-platform/latest/rest_api/operator_apis/etcd-operator-openshift-io-v1.html)
- [Red Hat Blog — OCP Disaster Recovery Part 1: automated etcd backup in OpenShift 4.x](https://www.redhat.com/en/blog/ocp-disaster-recovery-part-1-how-to-create-automated-etcd-backup-in-openshift-4.x)
