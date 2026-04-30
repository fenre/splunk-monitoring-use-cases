<!-- AUTO-GENERATED from UC-3.3.11.json — DO NOT EDIT -->

---
id: "3.3.11"
title: "OpenShift Operator Lifecycle Manager (OLM) Subscription Health and InstallPlan / CSV Reconcile Failure Detection"
status: "verified"
criticality: "high"
splunkPillar: "Observability"
---

# UC-3.3.11 · OpenShift Operator Lifecycle Manager (OLM) Subscription Health and InstallPlan / CSV Reconcile Failure Detection

> **Criticality:** High &middot; **Difficulty:** Advanced &middot; **Pillar:** Observability &middot; **Type:** Reliability, Availability &middot; **Wave:** Walk &middot; **Status:** Verified

*We watch the backstage process that installs optional cluster add-ons from software catalogs. When that process gets stuck, refuses to approve the next step, or cannot reach its catalog, we raise a clear signal so teams fix it before important tools stop updating.*

---

## Description

Detects Operator Lifecycle Manager reconciliation failures on the add-on operator plane: Subscription state drift away from AtLatestKnown, failing Subscription conditions, InstallPlan phases stuck in Planning, RequiresApproval, Installing, or Failed, ClusterServiceVersion phases that never reach Succeeded, CatalogSource connection states that stay in TRANSIENT_FAILURE or CONNECTING, manual-approval InstallPlans that exceed governance dwell windows, and elevated restart counts on OLM control-plane pods. The analytic correlates API-shaped telemetry and Kubernetes-style events with optional Prometheus operator metrics. It deliberately excludes Cluster Version Operator upgrade storytelling, platform ClusterOperator health, MachineConfigPool convergence, generic Deployment rollout failures, and admission webhook failure modes covered by sibling use cases.

## Value

Platform and shared-services teams lose visibility when marketplace-style operators stall silently: a Subscription that never resolves strands security patches for compliance tooling, a CSV stuck in Failed blocks GitOps controllers from assuming healthy dependencies, and a CatalogSource in TRANSIENT_FAILURE during a disconnected mirror refresh can masquerade as a vendor outage. A consolidated ledger in the analytics tier shortens mean time to innocence by joining Subscription, InstallPlan, CSV, and CatalogSource state with event reasons such as InstallFailed or ResolutionFailed and with OLM pod stability signals. Risk and engineering leaders receive defensible evidence that add-on operator supply chains stayed observable across change windows, mirror syncs, and governance pauses.

## Implementation

Land ocp_subscription, ocp_installplan, ocp_csv, ocp_catalogsource, and k8s_events into ocp_audit or ocp_events with cluster and namespace labels; federate subscription_sync_total, csv_succeeded, and OLM pod restart metrics into ocp_metrics; normalize operators.coreos.com field aliases in props; save openshift_uc_3_3_11_olm_subscription_health on a fifteen minute schedule over earliest=-6h@h; route page and warn rows to platform on-call via the Splunk OpenShift App alert workflow; archive weekly exports for catalog governance reviews.

## Evidence

Saved search openshift_uc_3_3_11_olm_subscription_health with fifteen minute schedule; Splunk OpenShift App dashboard drilldowns on ocp_subscription, ocp_installplan, ocp_csv, ocp_catalogsource, k8s_events, and prometheus metric lines; alert routing to platform on-call; weekly CSV exports archived to a restricted evidence index.

## Control test

### Positive scenario

In a lab OpenShift cluster, ingest ocp_subscription rows showing a true ResolutionFailed or CatalogSourcesUnhealthy condition, matching ocp_catalogsource TRANSIENT_FAILURE snapshots, and k8s_events with reason ResolutionFailed; confirm openshift_uc_3_3_11_olm_subscription_health returns page or warn with non-null recommended_action within fifteen minutes.

### Negative scenario

After recovery when oc get sub shows AtLatestKnown without failing conditions, oc get csv shows Succeeded, oc get catsrc shows READY, and events quiet, confirm severities return to info and the alert wrapper emits zero rows when filtering to page and warn only.

## Detailed Implementation

### Step 1 — Prerequisites

Head of Platform owns this control with the OpenShift platform engineering lead, the operators and automation team that curates CatalogSource mirrors and Subscription channels, and the observability engineers who operate HTTP Event Collector tokens plus OpenTelemetry Collector agents on management clusters. This use case isolates the Operator Lifecycle Manager state machine that ships add-on operators through Subscription, InstallPlan, ClusterServiceVersion, and CatalogSource objects in the operators.coreos.com v1alpha1 API group. Examples include community and Red Hat-provided operators for observability, service mesh, GitOps, compliance, logging, and ingress controllers that are not the roughly thirty platform ClusterOperator resources reconciled by the Cluster Version Operator.

Scope boundaries are strict. UC-3.3.1 remains the Cluster Version Operator and overall platform upgrade progression narrative. UC-3.3.6 remains ClusterOperator Available, Progressing, Degraded, and Upgradeable semantics for platform components such as kube-apiserver, dns, monitoring, and ingress ClusterOperator rows, not CSV lifecycle for add-on operators installed through OLM. UC-3.3.17 remains MachineConfigPool ledger degradation on the Machine Configuration Operator axis. UC-3.2.6 remains vanilla Kubernetes Deployment rollout failures without interpreting CSV or Subscription conditions. UC-3.2.40 remains admission webhook timeout and failure modes at the admission review layer, not operator bundle unpack or catalog resolution errors. This UC does not replace oc get clusterversion diagnostics, etcd health drills, or generic workload pod crash analytics.

RBAC and safety: collectors that run oc get subscription, oc get installplan, oc get clusterserviceversion, and oc get catalogsource across all namespaces must use a dedicated ServiceAccount with get and list on those resources, not personal cluster-admin kubeconfig files on laptops. Run exporters from a hardened management host or CI worker with short-lived credentials. When you stream Kubernetes events, ensure involvedObject references and messages are acceptable under your data minimization policy. Legal review should confirm operator package names, pull spec digests referenced in messages, and internal registry hostnames are permitted in the analytics tier.

Index design: designate index=ocp_audit for API audit JSON if you dual-write operator object watches there, index=ocp_events for normalized object snapshots and Kubernetes events, and index=ocp_metrics for Prometheus exposition including subscription_sync_total, csv_succeeded, and kube_pod_container_status_restarts_total style series when your platform monitoring scrapes OLM namespaces. Many teams land structured object snapshots under ocp_events with discrete sourcetypes per kind. Retention should cover at least fourteen days hot for incident replay on stuck InstallPlan windows, thirty days for forensic review after catalog migrations, and cold storage aligned to observability policy.

Field normalization expectations: flatten Subscription.metadata.namespace and .name, Subscription.status.state into sub_state, map InstallPlan.status.phase into ip_phase and InstallPlan.spec.approval into ip_approval, map ClusterServiceVersion.status.phase into csv_phase, map CatalogSource.status.connectionState.lastObservedState into catsrc_conn, and expand status.conditions[] into parallel fields or child events with condition_type and condition_status. Preserve installPlanRef.name on Subscription rows for joins. If you ingest raw JSON without KV extraction, add props.conf INDEXED_EXTRACTIONS=json and FIELDALIAS rules so coalesce() ladders in the saved search still resolve. Cluster identity must appear on every event as cluster, openshift_cluster, or cluster_name.

Risk briefing: UpgradePending on a Subscription can be legitimate while a cluster administrator deliberately defers a minor bump during a change freeze. RequiresApproval InstallPlans may wait for ticketed approvals longer than engineering comfort but still within governance policy. CatalogSourcesUnhealthy spikes often coincide with scheduled mirror sync jobs in disconnected estates. CSV phase Replacing is a normal transition window between versions. The OperatorHub community catalog pod can restart during control-plane maintenance and emit short CONNECTING states. Alerts must combine dwell time, severity case tiers, and optional lookup-driven suppressions tied to change tickets rather than paging on every non-AtLatestKnown row.

Collector posture: stamp change_ticket_id onto HTTP Event Collector payloads when maintenance touches CatalogSource or Subscription objects. When Splunk shows ResolutionFailed but GitOps repositories show no drift, suspect manual oc edit operations or emergency hotfixes that bypassed the pipeline. Maintain a lookup keyed on cluster and operator package channel to downgrade severity for lab clusters or vendor-approved long-running approval policies.

### Step 2 — Configure data collection

Stand up five complementary lanes the multisearch fans together: structured Subscription, InstallPlan, CSV, and CatalogSource snapshots; Kubernetes events with OLM reasons; Prometheus operator metrics; optional audit records for administrative verbs on operators.coreos.com resources; and kube-state-metrics or cAdvisor style restart counters for OLM pods in openshift-operator-lifecycle-manager.

Object snapshot lane: schedule a Python or Go utility every five minutes from a management host. The utility should run oc get subscription -A -o json, oc get installplan -A -o json, oc get csv -A -o json, and oc get catalogsource -A -o json, then emit HTTP Event Collector JSON per object or batched arrays. Set sourcetype=ocp_subscription, sourcetype=ocp_installplan, sourcetype=ocp_csv, and sourcetype=ocp_catalogsource respectively. Include uid, resourceVersion, generation, and status fields needed for drift detection. Hash canonical JSON bodies without volatile resourceVersion when you need tamper-evident auditing.

Events lane: forward Kubernetes events into index=ocp_events with sourcetype=k8s_events or sourcetype=ocp_events using the Splunk Add-on for Kubernetes patterns or an OpenTelemetry Collector k8s_events receiver. Retain reason, message, involvedObject.kind, involvedObject.name, involvedObject.namespace, and firstTimestamp or lastTimestamp. Filter at forwarder or ingest processor level if volume requires, but retain InstallSucceeded, InstallFailed, ResolutionFailed, NeedsReinstall, and BundleUnpackFailed class reasons for this UC.

Metrics lane: federate in-cluster Prometheus targets that expose subscription_sync_total counters and csv_succeeded gauges from the operator lifecycle manager metric endpoints as documented for your OpenShift minor. Land lines in index=ocp_metrics with sourcetype=prometheus:metrics. Preserve labels for exported_namespace, name, phase, or package when present. Add a secondary scrape or recording rule export for kube_pod_container_status_restarts_total or equivalent restart counters limited to namespace openshift-operator-lifecycle-manager and workloads catalog-operator, olm-operator, package-server-manager.

Audit lane: optional but valuable for governance. Ship Kubernetes API audit JSON into index=ocp_audit with sourcetype=ocp_audit. Extract objectRef.resource, objectRef.namespace, objectRef.name, verb, user.username, and responseStatus.code for operators.coreos.com resources. Use Metadata level for high-volume reads if RequestResponse is prohibited.

Example jq helpers operators can use during design reviews to list Subscriptions not at latest:

```bash
oc get subscription -A -o json | jq -r '.items[] | select(.status.state!="AtLatestKnown") | [.metadata.namespace,.metadata.name,.status.state] | @tsv'
```

Example InstallPlan approval backlog:

```bash
oc get installplan -A -o json | jq -r '.items[] | select(.status.phase=="RequiresApproval") | [.metadata.namespace,.metadata.name,.spec.approval] | @tsv'
```

props.conf guidance: TRUNCATE sufficiently large for JSON bodies, TIMESTAMP_FIELDS respected when event time is authoritative, LINE_BREAKER rules for prometheus exposition when multiplexed with syslog headers, and FIELDALIAS maps from status.conditions[].type to condition_type when flattening.

Pre-save validation: index=ocp_events sourcetype=ocp_subscription earliest=-1h must return events after the first interval; ocp_installplan and ocp_csv sourcetypes should appear in the same window; k8s_events should show operator reasons during test installs; prometheus:metrics should include subscription_sync_total after scrape start; restart counters should move when you deliberately roll catalog-operator under lab change control.

Dashboards: the Splunk OpenShift App should host a matrix by cluster and namespace with color thresholds from severity, drilldowns to raw JSON, event text, metric lines, and audit rows. Splunk ITSI users can bind KPIs to counts of page severity rows per cluster and open episodes when two consecutive windows remain non-info for production entities.

### Step 3 — Create the search and alert

Save the SPL as openshift_uc_3_3_11_olm_subscription_health with a fifteen minute schedule, dispatch earliest=-6h@h, dispatch latest=now, and alert when severity is page or warn. Throttle duplicate cluster, namespace, package_key rows for thirty minutes unless severity escalates. Include recommended_action, ip_approval_age_h, and csv_phase in pager descriptions so incident commanders open the correct runbook section without re-running ad hoc searches.

Pipeline narrative: multisearch fans Subscription, InstallPlan, CSV, CatalogSource, event, metrics, and OLM pod restart arms so a silent single sourcetype outage does not hide genuine reconcile failures. coalesce() absorbs field naming drift between exporters. streamstats measures dwell for repeated bad phases per package key. eventstats adds cluster-level context such as count of Failed CSV rows. case() maps ResolutionFailed conditions, Failed InstallPlan phases, CSV Failed phases, long manual approvals, unhealthy catalogs, and high OLM pod restarts into page versus warn versus info tiers. recommended_action encodes the next mechanical step without pretending search replaces oc describe subscription.

Fenced SPL must match the spl JSON field exactly:

```spl
`comment("UC-3.3.11 OLM Subscription InstallPlan CSV CatalogSource health — ocp_subscription ocp_installplan ocp_csv ocp_catalogsource k8s_events prometheus OLM pods. Tunables: ip_appr_warn_h=24 ip_appr_page_h=72 olm_restarts_warn=20 earliest=-6h@h latest=now")`
| multisearch
    [ search (index=ocp_audit OR index=ocp_events) sourcetype=ocp_subscription earliest=-6h@h latest=now
      | eval cluster=lower(trim(toString(coalesce(cluster, openshift_cluster, cluster_name, cluster_id, ""))))
      | eval olm_ns=lower(trim(toString(coalesce(namespace, k8s_namespace, metadata_namespace, ""))))
      | eval sub_name=lower(trim(toString(coalesce(name, subscription_name, metadata_name, ""))))
      | eval pkg_key=lower(trim(toString(coalesce(packageName, package, spec_name, sub_name, ""))))
      | eval sub_state=lower(trim(toString(coalesce(status_state, state, phase, ""))))
      | eval cond_t=lower(trim(toString(coalesce(condition_type, cond_type, type, ""))))
      | eval cond_s=lower(trim(toString(coalesce(condition_status, cond_status, status, ""))))
      | eval cond_bad=if(match(cond_t,"resolutionfailed|installplanmissing|installplanpending|catalogsourcesunhealthy|bundleunpackfailed") AND match(cond_s,"true"),1,0)
      | eval ip_ref=lower(trim(toString(coalesce(installPlanRef_name, installplan, status_installPlanRef, ""))))
      | sort 0 + cluster + olm_ns + pkg_key - _time
      | streamstats window=3 current=t global=f last(sub_state) AS prev_sub last(_time) AS prev_ts BY cluster olm_ns pkg_key
      | eval sub_state_dwell_m=if(isnotnull(prev_ts), round((_time-prev_ts)/60,2), 0)
      | stats latest(_time) AS last_sub_t latest(sub_state) AS sub_state max(cond_bad) AS sub_cond_bad values(cond_t) AS sub_cond_types latest(ip_ref) AS ip_ref latest(sub_state_dwell_m) AS sub_state_dwell_m BY cluster olm_ns pkg_key ]
    [ search (index=ocp_audit OR index=ocp_events) sourcetype=ocp_installplan earliest=-6h@h latest=now
      | eval cluster=lower(trim(toString(coalesce(cluster, openshift_cluster, cluster_name, ""))))
      | eval olm_ns=lower(trim(toString(coalesce(namespace, k8s_namespace, ""))))
      | eval ip_name=lower(trim(toString(coalesce(name, installplan_name, metadata_name, ""))))
      | eval pkg_key=lower(trim(toString(coalesce(packageName, package, csvName, ""))))
      | eval ip_phase=lower(trim(toString(coalesce(phase, status_phase, ""))))
      | eval ip_approval=lower(trim(toString(coalesce(approval, spec_approval, ""))))
      | eval ip_start=strptime(trim(toString(coalesce(metadata_creationTimestamp, creationTimestamp, ""))),"%Y-%m-%dT%H:%M:%SZ")
      | stats latest(_time) AS last_ip_t latest(ip_phase) AS ip_phase latest(ip_approval) AS ip_approval earliest(ip_start) AS ip_start latest(pkg_key) AS pkg_key BY cluster olm_ns ip_name ]
    [ search (index=ocp_audit OR index=ocp_events) sourcetype=ocp_csv earliest=-6h@h latest=now
      | eval cluster=lower(trim(toString(coalesce(cluster, openshift_cluster, cluster_name, ""))))
      | eval olm_ns=lower(trim(toString(coalesce(namespace, k8s_namespace, ""))))
      | eval csv_name=lower(trim(toString(coalesce(name, csv, metadata_name, ""))))
      | eval pkg_key=lower(trim(toString(coalesce(packageName, displayName, csv_name, ""))))
      | eval csv_phase=lower(trim(toString(coalesce(phase, status_phase, ""))))
      | stats latest(_time) AS last_csv_t latest(csv_phase) AS csv_phase latest(pkg_key) AS pkg_key BY cluster olm_ns csv_name ]
    [ search (index=ocp_audit OR index=ocp_events) sourcetype=ocp_catalogsource earliest=-6h@h latest=now
      | eval cluster=lower(trim(toString(coalesce(cluster, openshift_cluster, cluster_name, ""))))
      | eval olm_ns=lower(trim(toString(coalesce(namespace, k8s_namespace, ""))))
      | eval catsrc_name=lower(trim(toString(coalesce(name, catalogsource_name, metadata_name, ""))))
      | eval catsrc_conn=upper(trim(toString(coalesce(connection_lastObservedState, lastObservedState, conn_state, ""))))
      | stats latest(_time) AS last_cs_t latest(catsrc_conn) AS catsrc_conn BY cluster olm_ns catsrc_name ]
    [ search (index=ocp_audit OR index=ocp_events) (sourcetype=k8s_events OR sourcetype=ocp_events) earliest=-6h@h latest=now
      | eval cluster=lower(trim(toString(coalesce(cluster, openshift_cluster, cluster_name, ""))))
      | eval olm_ns=lower(trim(toString(coalesce(involvedObject_namespace, namespace, k8s_namespace, ""))))
      | eval pkg_key=lower(trim(toString(coalesce(involvedObject_name, package, subscription, ""))))
      | eval reason=trim(toString(coalesce(reason, Reason, "")))
      | eval msg=trim(toString(coalesce(message, Message, "")))
      | where match(lower(reason),"installsucceeded|installfailed|resolutionfailed|needsreinstall|bundleunpackfailed") OR match(lower(msg),"installsucceeded|installfailed|resolutionfailed|needsreinstall|bundleunpackfailed")
      | eval evt_lane="k8s_olm"
      | stats latest(_time) AS last_evt_t latest(reason) AS evt_reason latest(msg) AS evt_msg BY cluster olm_ns pkg_key ]
    [ search index=ocp_metrics sourcetype=prometheus:metrics earliest=-6h@h latest=now
      | eval cluster=lower(trim(toString(coalesce(cluster, openshift_cluster, cluster_name, k8s_cluster_name, ""))))
      | eval mn=lower(trim(toString(coalesce(__name__, metric_name, name, ""))))
      | eval mv=tonumber(tostring(coalesce(value, metric_value, Value, "0")),10)
      | where match(mn,"subscription_sync_total|csv_succeeded")
      | eval olm_ns=lower(trim(toString(coalesce(namespace, exported_namespace, k8s_namespace, "olm_metrics"))))
      | eval pkg_key=lower(trim(toString(coalesce(name, package, pod, "aggregate"))))
      | stats latest(_time) AS last_prom_t latest(mv) AS prom_val latest(mn) AS prom_name BY cluster olm_ns pkg_key ]
    [ search index=ocp_metrics sourcetype=prometheus:metrics earliest=-6h@h latest=now
      | eval cluster=lower(trim(toString(coalesce(cluster, openshift_cluster, cluster_name, k8s_cluster_name, ""))))
      | eval mn=lower(trim(toString(coalesce(__name__, metric_name, name, ""))))
      | eval mv=tonumber(tostring(coalesce(value, metric_value, Value, "0")),10)
      | eval pod=lower(trim(toString(coalesce(pod, pod_name, ""))))
      | eval ns=lower(trim(toString(coalesce(namespace, k8s_namespace, ""))))
      | where match(ns,"openshift-operator-lifecycle-manager") AND match(pod,"catalog-operator|olm-operator|package-server")
      | where match(mn,"kube_pod_container_status_restarts_total|container_restart_count")
      | stats sum(mv) AS olm_restarts latest(_time) AS last_olm_pod_t BY cluster ]
| eval pkg_key=lower(trim(coalesce(pkg_key, "unknown_pkg")))
| eval olm_ns=lower(trim(coalesce(olm_ns, "unknown_ns")))
| stats max(last_sub_t) AS last_sub_t first(sub_state) AS sub_state max(sub_cond_bad) AS sub_cond_bad values(sub_cond_types) AS sub_cond_types max(last_ip_t) AS last_ip_t first(ip_phase) AS ip_phase first(ip_approval) AS ip_approval min(ip_start) AS ip_start max(last_csv_t) AS last_csv_t first(csv_phase) AS csv_phase max(last_cs_t) AS last_cs_t first(catsrc_conn) AS catsrc_conn max(last_evt_t) AS last_evt_t first(evt_reason) AS evt_reason first(evt_msg) AS evt_msg max(last_prom_t) AS last_prom_t max(prom_val) AS prom_val first(prom_name) AS prom_name max(last_olm_pod_t) AS last_olm_pod_t max(olm_restarts) AS olm_restarts max(sub_state_dwell_m) AS sub_state_dwell_m values(ip_ref) AS ipref_mv values(csv_name) AS csv_mv values(catsrc_name) AS cs_mv BY cluster olm_ns pkg_key
| eval ip_ref=trim(toString(mvindex(mvdedup(ipref_mv),0)))
| eval csv_name=trim(toString(mvindex(mvdedup(csv_mv),0)))
| eval catsrc_name=trim(toString(mvindex(mvdedup(cs_mv),0)))
| eval ip_approval_age_h=if(match(ip_approval,"manual") AND match(ip_phase,"requiresapproval") AND isnotnull(ip_start) AND ip_start>0, round((now()-ip_start)/3600,3), null())
| eval catsrc_bad=if(match(catsrc_conn,"TRANSIENT_FAILURE|CONNECTING") AND isnotnull(catsrc_conn),1,0)
| eval csv_bad=if(match(csv_phase,"failed|unknown"),1,0)
| eval ip_bad=if(match(ip_phase,"failed"),1,0)
| eventstats sum(csv_bad) AS cluster_csv_fail_cnt sum(ip_bad) AS cluster_ip_fail_cnt BY cluster
| eval severity=case(
    sub_cond_bad==1 AND match(pkg_key,"compliance|gitops|servicemesh|logging|monitoring|etcd|ingress"), "page",
    sub_cond_bad==1, "warn",
    csv_bad==1 AND match(pkg_key,"compliance|gitops|servicemesh|logging|monitoring"), "page",
    csv_bad==1, "warn",
    ip_bad==1, "page",
    match(lower(evt_reason),"installfailed|resolutionfailed|needsreinstall|bundleunpackfailed"), "page",
    isnotnull(ip_approval_age_h) AND ip_approval_age_h>=72, "page",
    isnotnull(ip_approval_age_h) AND ip_approval_age_h>=24, "warn",
    catsrc_bad==1 AND cluster_csv_fail_cnt>=1, "warn",
    coalesce(olm_restarts,0)>=50, "page",
    coalesce(olm_restarts,0)>=20, "warn",
    match(sub_state,"upgradepending|upgradeavailable") AND coalesce(sub_state_dwell_m,0)>=360, "warn",
    true(), "info")
| eval recommended_action=case(
    sub_cond_bad==1 AND match(sub_cond_types,"resolutionfailed"), "inspect_catalogsource_and_operatorhub_connectivity_then_oc_describe_sub",
    sub_cond_bad==1 AND match(sub_cond_types,"catalogsourcesunhealthy"), "verify_catalogsource_pods_and_mirror_sync_job",
    sub_cond_bad==1 AND match(sub_cond_types,"bundleunpackfailed"), "check_cluster_operator_registry_and_image_pull_secrets_for_bundle",
    csv_bad==1, "oc_describe_csv_and_review_operand_deployment_conditions",
    ip_bad==1, "oc_describe_installplan_and_review_step_status",
    match(ip_phase,"requiresapproval"), "governance_review_manual_installplan_then_oc_patch_approval",
    catsrc_bad==1, "validate_grpc_catalog_endpoint_and_tls_for_catalogsource",
    coalesce(olm_restarts,0)>=20, "collect_olm_namespace_logs_and_roll_catalog_operator_under_change_control",
    match(lower(evt_reason),"installfailed"), "correlate_event_message_with_csv_and_subscription_conditions",
    true(), "refresh_olm_object_snapshots_and_compare_with_console_operator_hub")
| join type=left max=0 cluster
    [| inputlookup openshift_cluster_inventory.csv
     | fields cluster, cluster_tier, owner_team, environment]
| eval cluster_tier=coalesce(cluster_tier, "unrated"),
       owner_team=coalesce(owner_team, "unowned"),
       environment=coalesce(environment, "unknown")
| table cluster olm_ns pkg_key sub_state sub_cond_bad sub_cond_types ip_ref ip_phase ip_approval ip_approval_age_h csv_name csv_phase catsrc_name catsrc_conn evt_reason evt_msg prom_name prom_val olm_restarts severity recommended_action last_sub_t cluster_tier owner_team environment
```

savedsearches.conf sketch:

```ini
[openshift_uc_3_3_11_olm_subscription_health_alert]
cron_schedule = */15 * * * *
dispatch.earliest_time = -6h@h
dispatch.latest_time = now
enableSched = 1
action.email = 1
action.email.to = openshift-platform@example.com
action.email.subject = OCP OLM $result.severity$ $result.cluster$ $result.olm_ns$ $result.pkg_key$
counttype = number of events
relation = greater than
quantity = 0
search = | savedsearch openshift_uc_3_3_11_olm_subscription_health | where severity IN ("page","warn")
```

Performance: if Job Inspector shows multisearch queue time above your SLA, materialize ocp_subscription and ocp_csv snapshots hourly into a summary index keyed on cluster, olm_ns, and pkg_key, widen alert searches to earliest=-2h@h on the summary, and retain this full search for investigations.

### Step 4 — Validate

Ground truth always starts on-cluster. Run oc get sub -A, oc get ip -A, oc get csv -A, and oc get catsrc -A, then compare states to Splunk rows for the same cluster, namespace, and names inside the last snapshot window. When states disagree, verify resourceVersion freshness, indexer clock skew, and duplicate cluster labels across regions before blaming parsers.

Deep dive with oc describe subscription, oc describe installplan, oc describe csv, and oc describe catalogsource to read condition messages, step statuses, and connection errors. Splunk should mirror transitions within one collection interval; if not, tighten scripted input frequency or fix kubeconfig expiration on the management host.

Event correlation: during validation, run oc get events -n openshift-operators and per-add-on namespaces, then confirm k8s_events rows capture the same reason and message text you see live.

Metrics cross-check: in the OpenShift console monitoring stack or via oc get --raw against Prometheus endpoints, validate subscription_sync_total increments during healthy reconciles and csv_succeeded tracks CSV success labels consistent with ocp_csv snapshots. When metrics disappear while API snapshots look healthy, suspect scrape misconfiguration or label collisions.

Synthetic validation: in a lab namespace, install a small test operator from a known CatalogSource, approve InstallPlans if manual approval is enabled, wait for Succeeded CSV, then confirm openshift_uc_3_3_11_olm_subscription_health returns info severity for that package key. Introduce a deliberate bad CatalogSource endpoint under vendor guidance, observe ResolutionFailed or connection errors, and confirm warn or page severity with non-null recommended_action. Roll back and confirm recovery.

Negative test: on a cluster where all watched Subscriptions report AtLatestKnown, CSV phases are Succeeded or Replacing within short dwell, and CatalogSources report READY, confirm the alert wrapper returns zero rows for page and warn filters after upgrade completion windows settle.

Runbook linkage: document expected UpgradePending durations during channel bumps and mirror syncs so validators do not file false defects when change calendars show an approved deferral.

### Step 5 — Operationalize & Troubleshoot

Case 1 — ResolutionFailed on Subscription after catalog migration: verify CatalogSource pods, grpc connectivity, and ImageContentSourcePolicy mirrors; re-index the catalog if bundle tags moved; confirm oc-mirror job logs before escalating to vendor support.

Case 2 — InstallPlan stuck in RequiresApproval beyond policy: confirm governance workflow tickets, compare approval SLA to ip_approval_age_h, and patch approval only after security review of the embedded CSV version.

Case 3 — CSV phase Failed with operand Deployment errors: oc describe csv for message hints, then inspect operator-owned Deployments and ServiceAccounts; distinguish bundle install failures from workload runtime failures using events.

Case 4 — CatalogSource lastObservedState TRANSIENT_FAILURE during scheduled mirror sync: attach to the mirror automation window, validate temporary DNS or registry outages, and suppress paging when change_ticket_id matches the sync job.

Case 5 — BundleUnpackFailed tied to pull secrets or registry rate limits: verify global pull secret, image registry OperatorHub config, and proxy settings; correlate with cluster image-registry health without conflating UC-3.3.6 platform operator rows.

Case 6 — Subscription state UpgradePending during operator-team pause: confirm deliberate channel pin or paused approval policy in GitOps; treat long dwell as governance signal, not always outage.

Case 7 — CSV phase Replacing during z-stream bump: expect short overlap windows; page only when Replacing dwell exceeds documented thresholds or pairs with Failed.

Case 8 — Community OperatorHub catalog pod restarts after node reboot: short CONNECTING states are common; combine catsrc_bad with cluster_csv_fail_cnt before paging leadership.

Case 9 — catalog-operator restart storm: gather openshift-operator-lifecycle-manager logs, check etcd and API latency, and review validating webhooks that might stall OLM writes without duplicating UC-3.2.40 webhook analytics.

Case 10 — subscription_sync_total flatline with active oc apply loops: indicates metrics scrape failure or label drift; repair ServiceMonitor federation before muting the UC.

Case 11 — Audit shows emergency oc delete csv during incident: pair human actions with evt_reason timelines before blaming autonomous reconcile loops.

Case 12 — Fleet-wide info severities only: weekly spot-check Splunk rows against oc get sub -A on every production cluster to confirm parsers, tokens, and cluster labels remain aligned.

Closing checklist: multisearch lists object, event, metrics, and OLM pod restart arms; coalesce normalizes cluster and namespace fields; streamstats supports dwell hints; eventstats adds cluster failure counts; case() implements severity tiers; closing table includes cluster, olm_ns, pkg_key, sub_state, sub_cond_bad, sub_cond_types, ip_ref, ip_phase, ip_approval, ip_approval_age_h, csv_name, csv_phase, catsrc_name, catsrc_conn, evt_reason, evt_msg, prom_name, prom_val, olm_restarts, severity, recommended_action, and last_sub_t for twenty-one analyst-visible columns.

## SPL

```spl
`comment("UC-3.3.11 OLM Subscription InstallPlan CSV CatalogSource health — ocp_subscription ocp_installplan ocp_csv ocp_catalogsource k8s_events prometheus OLM pods. Tunables: ip_appr_warn_h=24 ip_appr_page_h=72 olm_restarts_warn=20 earliest=-6h@h latest=now")`
| multisearch
    [ search (index=ocp_audit OR index=ocp_events) sourcetype=ocp_subscription earliest=-6h@h latest=now
      | eval cluster=lower(trim(toString(coalesce(cluster, openshift_cluster, cluster_name, cluster_id, ""))))
      | eval olm_ns=lower(trim(toString(coalesce(namespace, k8s_namespace, metadata_namespace, ""))))
      | eval sub_name=lower(trim(toString(coalesce(name, subscription_name, metadata_name, ""))))
      | eval pkg_key=lower(trim(toString(coalesce(packageName, package, spec_name, sub_name, ""))))
      | eval sub_state=lower(trim(toString(coalesce(status_state, state, phase, ""))))
      | eval cond_t=lower(trim(toString(coalesce(condition_type, cond_type, type, ""))))
      | eval cond_s=lower(trim(toString(coalesce(condition_status, cond_status, status, ""))))
      | eval cond_bad=if(match(cond_t,"resolutionfailed|installplanmissing|installplanpending|catalogsourcesunhealthy|bundleunpackfailed") AND match(cond_s,"true"),1,0)
      | eval ip_ref=lower(trim(toString(coalesce(installPlanRef_name, installplan, status_installPlanRef, ""))))
      | sort 0 + cluster + olm_ns + pkg_key - _time
      | streamstats window=3 current=t global=f last(sub_state) AS prev_sub last(_time) AS prev_ts BY cluster olm_ns pkg_key
      | eval sub_state_dwell_m=if(isnotnull(prev_ts), round((_time-prev_ts)/60,2), 0)
      | stats latest(_time) AS last_sub_t latest(sub_state) AS sub_state max(cond_bad) AS sub_cond_bad values(cond_t) AS sub_cond_types latest(ip_ref) AS ip_ref latest(sub_state_dwell_m) AS sub_state_dwell_m BY cluster olm_ns pkg_key ]
    [ search (index=ocp_audit OR index=ocp_events) sourcetype=ocp_installplan earliest=-6h@h latest=now
      | eval cluster=lower(trim(toString(coalesce(cluster, openshift_cluster, cluster_name, ""))))
      | eval olm_ns=lower(trim(toString(coalesce(namespace, k8s_namespace, ""))))
      | eval ip_name=lower(trim(toString(coalesce(name, installplan_name, metadata_name, ""))))
      | eval pkg_key=lower(trim(toString(coalesce(packageName, package, csvName, ""))))
      | eval ip_phase=lower(trim(toString(coalesce(phase, status_phase, ""))))
      | eval ip_approval=lower(trim(toString(coalesce(approval, spec_approval, ""))))
      | eval ip_start=strptime(trim(toString(coalesce(metadata_creationTimestamp, creationTimestamp, ""))),"%Y-%m-%dT%H:%M:%SZ")
      | stats latest(_time) AS last_ip_t latest(ip_phase) AS ip_phase latest(ip_approval) AS ip_approval earliest(ip_start) AS ip_start latest(pkg_key) AS pkg_key BY cluster olm_ns ip_name ]
    [ search (index=ocp_audit OR index=ocp_events) sourcetype=ocp_csv earliest=-6h@h latest=now
      | eval cluster=lower(trim(toString(coalesce(cluster, openshift_cluster, cluster_name, ""))))
      | eval olm_ns=lower(trim(toString(coalesce(namespace, k8s_namespace, ""))))
      | eval csv_name=lower(trim(toString(coalesce(name, csv, metadata_name, ""))))
      | eval pkg_key=lower(trim(toString(coalesce(packageName, displayName, csv_name, ""))))
      | eval csv_phase=lower(trim(toString(coalesce(phase, status_phase, ""))))
      | stats latest(_time) AS last_csv_t latest(csv_phase) AS csv_phase latest(pkg_key) AS pkg_key BY cluster olm_ns csv_name ]
    [ search (index=ocp_audit OR index=ocp_events) sourcetype=ocp_catalogsource earliest=-6h@h latest=now
      | eval cluster=lower(trim(toString(coalesce(cluster, openshift_cluster, cluster_name, ""))))
      | eval olm_ns=lower(trim(toString(coalesce(namespace, k8s_namespace, ""))))
      | eval catsrc_name=lower(trim(toString(coalesce(name, catalogsource_name, metadata_name, ""))))
      | eval catsrc_conn=upper(trim(toString(coalesce(connection_lastObservedState, lastObservedState, conn_state, ""))))
      | stats latest(_time) AS last_cs_t latest(catsrc_conn) AS catsrc_conn BY cluster olm_ns catsrc_name ]
    [ search (index=ocp_audit OR index=ocp_events) (sourcetype=k8s_events OR sourcetype=ocp_events) earliest=-6h@h latest=now
      | eval cluster=lower(trim(toString(coalesce(cluster, openshift_cluster, cluster_name, ""))))
      | eval olm_ns=lower(trim(toString(coalesce(involvedObject_namespace, namespace, k8s_namespace, ""))))
      | eval pkg_key=lower(trim(toString(coalesce(involvedObject_name, package, subscription, ""))))
      | eval reason=trim(toString(coalesce(reason, Reason, "")))
      | eval msg=trim(toString(coalesce(message, Message, "")))
      | where match(lower(reason),"installsucceeded|installfailed|resolutionfailed|needsreinstall|bundleunpackfailed") OR match(lower(msg),"installsucceeded|installfailed|resolutionfailed|needsreinstall|bundleunpackfailed")
      | eval evt_lane="k8s_olm"
      | stats latest(_time) AS last_evt_t latest(reason) AS evt_reason latest(msg) AS evt_msg BY cluster olm_ns pkg_key ]
    [ search index=ocp_metrics sourcetype=prometheus:metrics earliest=-6h@h latest=now
      | eval cluster=lower(trim(toString(coalesce(cluster, openshift_cluster, cluster_name, k8s_cluster_name, ""))))
      | eval mn=lower(trim(toString(coalesce(__name__, metric_name, name, ""))))
      | eval mv=tonumber(tostring(coalesce(value, metric_value, Value, "0")),10)
      | where match(mn,"subscription_sync_total|csv_succeeded")
      | eval olm_ns=lower(trim(toString(coalesce(namespace, exported_namespace, k8s_namespace, "olm_metrics"))))
      | eval pkg_key=lower(trim(toString(coalesce(name, package, pod, "aggregate"))))
      | stats latest(_time) AS last_prom_t latest(mv) AS prom_val latest(mn) AS prom_name BY cluster olm_ns pkg_key ]
    [ search index=ocp_metrics sourcetype=prometheus:metrics earliest=-6h@h latest=now
      | eval cluster=lower(trim(toString(coalesce(cluster, openshift_cluster, cluster_name, k8s_cluster_name, ""))))
      | eval mn=lower(trim(toString(coalesce(__name__, metric_name, name, ""))))
      | eval mv=tonumber(tostring(coalesce(value, metric_value, Value, "0")),10)
      | eval pod=lower(trim(toString(coalesce(pod, pod_name, ""))))
      | eval ns=lower(trim(toString(coalesce(namespace, k8s_namespace, ""))))
      | where match(ns,"openshift-operator-lifecycle-manager") AND match(pod,"catalog-operator|olm-operator|package-server")
      | where match(mn,"kube_pod_container_status_restarts_total|container_restart_count")
      | stats sum(mv) AS olm_restarts latest(_time) AS last_olm_pod_t BY cluster ]
| eval pkg_key=lower(trim(coalesce(pkg_key, "unknown_pkg")))
| eval olm_ns=lower(trim(coalesce(olm_ns, "unknown_ns")))
| stats max(last_sub_t) AS last_sub_t first(sub_state) AS sub_state max(sub_cond_bad) AS sub_cond_bad values(sub_cond_types) AS sub_cond_types max(last_ip_t) AS last_ip_t first(ip_phase) AS ip_phase first(ip_approval) AS ip_approval min(ip_start) AS ip_start max(last_csv_t) AS last_csv_t first(csv_phase) AS csv_phase max(last_cs_t) AS last_cs_t first(catsrc_conn) AS catsrc_conn max(last_evt_t) AS last_evt_t first(evt_reason) AS evt_reason first(evt_msg) AS evt_msg max(last_prom_t) AS last_prom_t max(prom_val) AS prom_val first(prom_name) AS prom_name max(last_olm_pod_t) AS last_olm_pod_t max(olm_restarts) AS olm_restarts max(sub_state_dwell_m) AS sub_state_dwell_m values(ip_ref) AS ipref_mv values(csv_name) AS csv_mv values(catsrc_name) AS cs_mv BY cluster olm_ns pkg_key
| eval ip_ref=trim(toString(mvindex(mvdedup(ipref_mv),0)))
| eval csv_name=trim(toString(mvindex(mvdedup(csv_mv),0)))
| eval catsrc_name=trim(toString(mvindex(mvdedup(cs_mv),0)))
| eval ip_approval_age_h=if(match(ip_approval,"manual") AND match(ip_phase,"requiresapproval") AND isnotnull(ip_start) AND ip_start>0, round((now()-ip_start)/3600,3), null())
| eval catsrc_bad=if(match(catsrc_conn,"TRANSIENT_FAILURE|CONNECTING") AND isnotnull(catsrc_conn),1,0)
| eval csv_bad=if(match(csv_phase,"failed|unknown"),1,0)
| eval ip_bad=if(match(ip_phase,"failed"),1,0)
| eventstats sum(csv_bad) AS cluster_csv_fail_cnt sum(ip_bad) AS cluster_ip_fail_cnt BY cluster
| eval severity=case(
    sub_cond_bad==1 AND match(pkg_key,"compliance|gitops|servicemesh|logging|monitoring|etcd|ingress"), "page",
    sub_cond_bad==1, "warn",
    csv_bad==1 AND match(pkg_key,"compliance|gitops|servicemesh|logging|monitoring"), "page",
    csv_bad==1, "warn",
    ip_bad==1, "page",
    match(lower(evt_reason),"installfailed|resolutionfailed|needsreinstall|bundleunpackfailed"), "page",
    isnotnull(ip_approval_age_h) AND ip_approval_age_h>=72, "page",
    isnotnull(ip_approval_age_h) AND ip_approval_age_h>=24, "warn",
    catsrc_bad==1 AND cluster_csv_fail_cnt>=1, "warn",
    coalesce(olm_restarts,0)>=50, "page",
    coalesce(olm_restarts,0)>=20, "warn",
    match(sub_state,"upgradepending|upgradeavailable") AND coalesce(sub_state_dwell_m,0)>=360, "warn",
    true(), "info")
| eval recommended_action=case(
    sub_cond_bad==1 AND match(sub_cond_types,"resolutionfailed"), "inspect_catalogsource_and_operatorhub_connectivity_then_oc_describe_sub",
    sub_cond_bad==1 AND match(sub_cond_types,"catalogsourcesunhealthy"), "verify_catalogsource_pods_and_mirror_sync_job",
    sub_cond_bad==1 AND match(sub_cond_types,"bundleunpackfailed"), "check_cluster_operator_registry_and_image_pull_secrets_for_bundle",
    csv_bad==1, "oc_describe_csv_and_review_operand_deployment_conditions",
    ip_bad==1, "oc_describe_installplan_and_review_step_status",
    match(ip_phase,"requiresapproval"), "governance_review_manual_installplan_then_oc_patch_approval",
    catsrc_bad==1, "validate_grpc_catalog_endpoint_and_tls_for_catalogsource",
    coalesce(olm_restarts,0)>=20, "collect_olm_namespace_logs_and_roll_catalog_operator_under_change_control",
    match(lower(evt_reason),"installfailed"), "correlate_event_message_with_csv_and_subscription_conditions",
    true(), "refresh_olm_object_snapshots_and_compare_with_console_operator_hub")
| join type=left max=0 cluster
    [| inputlookup openshift_cluster_inventory.csv
     | fields cluster, cluster_tier, owner_team, environment]
| eval cluster_tier=coalesce(cluster_tier, "unrated"),
       owner_team=coalesce(owner_team, "unowned"),
       environment=coalesce(environment, "unknown")
| table cluster olm_ns pkg_key sub_state sub_cond_bad sub_cond_types ip_ref ip_phase ip_approval ip_approval_age_h csv_name csv_phase catsrc_name catsrc_conn evt_reason evt_msg prom_name prom_val olm_restarts severity recommended_action last_sub_t cluster_tier owner_team environment
```

## CIM SPL

```spl
| tstats summariesonly=true latest(Inventory.vendor_product) AS vendor_product latest(Inventory.version) AS inv_version FROM datamodel=Inventory WHERE nodename=Inventory earliest=-24h@h latest=now BY Inventory.dest
| rename Inventory.dest AS inv_dest
| join type=left max=0 inv_dest
    [| tstats summariesonly=true latest(Application_State.state) AS app_state latest(Application_State.info) AS app_info FROM datamodel=Application_State WHERE nodename=Application_State earliest=-24h@h latest=now BY Application_State.dest
     | rename Application_State.dest AS inv_dest ]
| where like(lower(vendor_product), "%openshift%") OR like(lower(app_info), "%operator%")
| table inv_dest vendor_product inv_version app_state app_info
```

## Visualization

Severity-colored table by cluster, olm_ns, and pkg_key with drilldowns to raw ocp_subscription, ocp_installplan, ocp_csv, ocp_catalogsource JSON, k8s_events text, prometheus metric lines, and optional ocp_audit rows; single-value tiles for cluster_csv_fail_cnt; timeline of ip_approval_age_h for manual approvals; matrix panel of CatalogSource connection states.

## Known False Positives

Subscription status UpgradePending often reflects an intentional wait for manual InstallPlan approval or a vendor channel that lags behind the latest catalog graph; pair alerts with governance metadata before paging. CatalogSourcesUnhealthy or CatalogSource connection states of CONNECTING and TRANSIENT_FAILURE appear during scheduled disconnected-mirror syncs, temporary registry rate limits, or DNS blips while grpc catalog pods restart; require sustained dwell and corroborating CSV failures. Vendor catalog rebuilds that bump bundle digests can briefly surface ResolutionFailed until the cluster re-resolves; treat single-interval spikes as noise when oc describe shows recovery. Deliberately paused operator upgrades during enterprise change-freeze windows keep Subscriptions off AtLatestKnown without indicating breakage; suppress when change tickets authorize the freeze. CSV phase Replacing is a normal transition between versions during upgrades; escalate only when Replacing persists beyond vendor guidance or coexists with Failed steps on the InstallPlan. The default OperatorHub catalog can bounce after control-plane reboots or etcd compaction windows; combine CatalogSource errors with cluster_csv_fail_cnt before executive escalation. Manual approval policies may leave InstallPlans in RequiresApproval longer than engineering comfort; tune ip_approval_age_h thresholds to match risk policy, not only developer impatience. Lab clusters that constantly churn test operators will generate warn noise unless routed to non-production indexes. Prometheus scrape gaps can flatline subscription_sync_total while API snapshots remain healthy; repair federation before muting the analytic. Duplicate HTTP Event Collector submissions from redundant exporters can inflate olm_restarts or duplicate rows until dedupe logic lands in summary indexes.

## References

- [OpenShift Documentation — OLM overview](https://docs.openshift.com/container-platform/latest/operators/understanding/olm/olm-understanding-olm.html)
- [OpenShift Documentation — Managing operators with Operator Lifecycle Manager](https://docs.openshift.com/container-platform/latest/operators/admin/olm-managing-operators.html)
- [OpenShift Documentation — Viewing Operator status](https://docs.openshift.com/container-platform/latest/operators/admin/olm-status.html)
- [OpenShift Documentation — Adding Operators to a cluster](https://docs.openshift.com/container-platform/latest/operators/admin/olm-adding-operators-to-cluster.html)
- [OpenShift Documentation — Troubleshooting Operator issues](https://docs.openshift.com/container-platform/latest/operators/admin/olm-troubleshooting.html)
- [OpenShift REST API Reference — Subscription (operators.coreos.com)](https://docs.openshift.com/container-platform/latest/rest_api/operator_apis/subscription-operators-coreos-com-v1alpha1.html)
- [Red Hat Blog — Introducing the Operator Framework (OLM foundations)](https://www.redhat.com/en/blog/introducing-operator-framework-building-apps-kubernetes)
