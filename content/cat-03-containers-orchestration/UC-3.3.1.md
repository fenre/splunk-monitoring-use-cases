<!-- AUTO-GENERATED from UC-3.3.1.json — DO NOT EDIT -->

---
id: "3.3.1"
title: "OpenShift ClusterVersion Upgrade Progress and CVO Stuck Detection (Z- and Y-stream lifecycle)"
status: "verified"
criticality: "high"
splunkPillar: "Observability"
---

# UC-3.3.1 · OpenShift ClusterVersion Upgrade Progress and CVO Stuck Detection (Z- and Y-stream lifecycle)

> **Criticality:** High &middot; **Difficulty:** Advanced &middot; **Pillar:** Observability &middot; **Type:** Reliability, Availability &middot; **Wave:** Walk &middot; **Status:** Verified

*We watch the one master switch that tells an OpenShift cluster which software version it is moving toward and whether that move finished cleanly. If it stays stuck too long or cannot reach the vendor’s update catalog, we raise a clear signal so engineers fix the upgrade path before applications ride on a half-finished platform change.*

---

## Description

Detects stalled or unhealthy OpenShift cluster upgrades by treating the single cluster-scoped ClusterVersion custom resource in config.openshift.io/v1 as the authoritative ledger for desired channel, desired release, condition truth, and history outcomes owned by the Cluster Version Operator. The analytic correlates condition dwell time against Z-stream versus Y-stream duration expectations, compares spec versus status desired versions, surfaces upstream and channel drift, flags RetrievedUpdates=False graph reachability failures toward api.openshift.com upgrade metadata, and supplements API state with cluster_version Prometheus counters, audit mutations on clusterversions/cluster, and CVO pod narratives so platform teams see a cluster-wide upgrade pipeline story rather than per-operator reconciliation noise.

## Value

Executive and platform stakeholders lose credibility when upgrades appear green in a console tile yet the ClusterVersion history shows Partial entries or Progressing=True for half a day without movement. A tamper-resistant Splunk narrative ties the same object administrators inspect with oc get clusterversion and oc adm upgrade to metrics, audit, and operator logs, which shortens debates about whether a pause is normal operator churn versus a broken graph fetch through a corporate proxy. Risk and audit reviewers receive defensible evidence that outbound upgrade-graph reachability, channel policy, and history completion states are continuously reviewed, not only captured in screenshots during post-incident reviews.

## Implementation

Land ocp_clusterversion JSON snapshots, prometheus:cluster_version cluster_version{type="completed"} samples, ocp_audit rows for clusterversions/cluster verbs, and ocp_logs from openshift-cluster-version pods into ocp_metrics, ocp_audit, and ocp_logs with consistent cluster labels; normalize condition and history fields in props; save openshift_uc_3_3_1_clusterversion_cvo_upgrade on a fifteen minute cadence over earliest=-6h@h; route page and warn severities to platform on-call; archive weekly CSV exports for lifecycle governance reviews.

## Evidence

Saved search openshift_uc_3_3_1_clusterversion_cvo_upgrade with fifteen minute schedule; dashboard drilldowns on ocp_clusterversion, prometheus:cluster_version, ocp_audit, and ocp_logs; alert stanza with platform routing keys; weekly CSV exports to a restricted evidence index.

## Control test

### Positive scenario

In a lab OpenShift cluster, simulate a prolonged Progressing=True state on ClusterVersion with a documented delayed rollout or inject a lab-only proxy deny to api.openshift.com so RetrievedUpdates transitions to False, ingest matching ocp_clusterversion snapshots and ocp_logs errors, and confirm openshift_uc_3_3_1_clusterversion_cvo_upgrade returns page or warn with a graph or reconciliation focused recommended_action within fifteen minutes.

### Negative scenario

After completing a healthy upgrade where oc get clusterversion shows Available=True, Progressing=False, history Completed for the target version, and RetrievedUpdates=True, confirm severities return to info and the alert wrapper emits zero rows when filtering to page and warn only.

## Detailed Implementation

### Step 1 — Prerequisites

Head of Platform owns this control with the OpenShift lifecycle engineering lead who operates ClusterVersion objects, the network and egress team that approves reachability to api.openshift.com upgrade-graph endpoints, and the observability engineers who steward Splunk HTTP Event Collector tokens plus OpenTelemetry Collector agents that federate in-cluster Prometheus. This use case isolates the ClusterVersion API surface in the config.openshift.io/v1 group: a single cluster-scoped custom resource named cluster that encodes the desired update channel, optional spec.upstream mirror of Cincinnati graph location, spec.desiredUpdate version and image references, optional spec.overrides that pin or exclude payload components, governance-oriented pause hints when present in your OpenShift minor, and status that reports observed desired version, condition set, and ordered status.history entries documenting each upgrade attempt with state, version, startedTime, completionTime, and verification metadata. The Cluster Version Operator, running in openshift-cluster-version, reconciles that object against release signatures, operator manifests, and the upgrade graph; it also reports clusteroperator/version as its own ClusterOperator heartbeat. UC-3.3.6 remains the matrix of roughly thirty ClusterOperator Available, Progressing, Degraded, and Upgradeable conditions for individual platform controllers, not the cluster-wide ClusterVersion ledger. UC-3.3.17 remains MachineConfigPool degradation on the Machine Configuration Operator plane with per-pool machine counts and paused pools, not CVO graph or history semantics. UC-3.3.20 remains operator-managed internal public key infrastructure expiry inventories. UC-3.2.13 remains vanilla Kubernetes certificate age analytics without OpenShift ClusterVersion coupling. Splunk becomes the reconciliation ledger that fuses periodic ClusterVersion exports, cluster_version Prometheus counters, audit JSON for administrative ClusterVersion mutations, and CVO pod logs that cite payload retrieval, signature verification, or upgrade-graph client errors.

Index and permission design land before field extraction. Designate index=ocp_metrics for structured ClusterVersion snapshots with sourcetype=ocp_clusterversion and for federated Prometheus lines with sourcetype=prometheus:cluster_version when your collector splits OpenShift Monitoring scrapes, or sourcetype=prometheus:metrics with reliable __name__ filtering when you retain a unified metrics stream. Designate index=ocp_audit for Kubernetes apiserver audit or equivalent OpenShift-forwarded JSON with sourcetype=ocp_audit. Designate index=ocp_logs for pod log pipelines with sourcetype=ocp_logs capturing openshift-cluster-version namespace workloads. Issue distinct HEC tokens per index with least privilege: platform site reliability roles may search all sourcetypes; application teams receive filtered views that redact requestObject bodies when counsel requires minimization. Retention should cover at least fourteen days hot for incident replay on stuck Progressing windows, thirty days for post-upgrade forensic review of history arrays, and align cold storage with enterprise observability policy. Legal review should confirm internal release image digests and proxy hostnames referenced in messages are acceptable in Splunk.

RBAC and safety: the exporter that runs oc get clusterversion cluster -o json or watches config.openshift.io ClusterVersion must use a dedicated ServiceAccount with get on clusterversions.resource and subresource access scoped to what your collector RBAC policy permits, not cluster-admin on employee laptops. Run collectors from a hardened management host or continuous integration worker with short-lived kubeconfigs. When you supplement with Prometheus federation from in-cluster monitoring, use a read-only bearer token bound to a metrics scraper identity rather than kubeadmin.

Field normalization expectations: flatten metadata.name into cv_name, map spec.channel into channel, spec.desiredUpdate.version into spec_version, status.desired.version into status_version, spec.upstream into spec_upstream, emit boolean or string flags for overrides_present and paused_present from spec fields your minor exposes, flatten each status.conditions[type] into progressing_flag, failing_flag, available_flag, upgradeable_flag, retrieved_updates_flag with paired lastTransitionTime and message fields, and flatten the latest or all status.history entries into hist_state, hist_version, hist_started, hist_completed for Splunk-friendly keys. If you ingest raw JSON without KV extraction, add props.conf INDEXED_EXTRACTIONS=json and FIELDALIAS rules so coalesce() ladders in the saved search still resolve. Cluster identity must appear on every event as cluster, openshift_cluster, or cluster_name drawn from management-cluster context or external_labels on Prometheus scrapes.

Risk briefing: Progressing=True is normal during both Z-stream and Y-stream upgrades; alerts must measure dwell time in hours, pair with Failing=True or history Partial and Failed rows, and compare against internal service-level expectations rather than treating any Progressing flip as an incident. RetrievedUpdates=False may appear during brief corporate proxy failovers or certificate rotations on egress appliances; combine with sustained duration and CVO log errors before executive escalation. spec.overrides during vendor-guided hotfixes are deliberate; join alerts to change tickets or HEC metadata so approved pin operations do not page as rogue drift. Channel changes during maintenance windows can look like drift when someone moves from stable to fast temporarily; verify intent with the lifecycle team before auto-remediation stories.

Differentiation recap: ClusterVersion condition semantics, history outcomes, desired version reconciliation, upgrade-graph reachability, and CVO pod narratives on the config.openshift.io plane, not per-operator ClusterOperator degradation analytics, not MachineConfigPool counts, not internal service certificate inventories, not vanilla Kubernetes apiserver serving certificate age alone.

Operational posture: align telemetry with your change board by stamping change_ticket_id onto HEC events when maintenance touches ClusterVersion or release image mirrors. When Splunk shows spec_version ahead of status_version for longer than expected, suspect blocked payload retrieval or signature verification failures visible in CVO logs rather than assuming benign lag. Capture approved oc adm upgrade --to executions in a lookup keyed on cluster so future searches can annotate operator-driven jumps mid-flight without mislabeling them as malicious drift.

### Step 2 — Configure data collection

Stand up four complementary lanes Splunk multisearch can fuse: periodic ClusterVersion API snapshots, Prometheus cluster_version metrics including type=completed counters, audit narratives for administrative changes to clusterversions/cluster, and CVO pod logs from openshift-cluster-version.

ClusterVersion snapshot lane: schedule a Python or Go utility every three to five minutes from a management host with kubeconfig authentication. The utility should run oc get clusterversion cluster -o json, flatten status.conditions into progressing_flag and related fields, extract the latest history element or emit parallel events per history row depending on volume policy, and include generation, observedGeneration, spec.channel, spec.desiredUpdate, spec.upstream, and override summaries. Set sourcetype=ocp_clusterversion and source=oc_get_clusterversion. Include a sha256 hash of the canonical JSON body without volatile resourceVersion if you want tamper-evident auditing in regulated environments.

Prometheus lane: enable platform monitoring federation per OpenShift documentation, scrape targets that expose cluster_version including labels such as type, version, from_version, channel, and cluster, and forward lines into index=ocp_metrics. When your OpenTelemetry prometheus receiver stamps a dedicated sourcetype for openshift-state-metrics style cluster version scrapes, use sourcetype=prometheus:cluster_version; otherwise land in sourcetype=prometheus:metrics and rely on __name__ filters in SPL. Preserve labels that identify channel and semantic version. Validate instant queries in the OpenShift console monitoring UI for cluster_version before Splunk paging goes live.

Audit lane: ship Kubernetes apiserver audit logs into index=ocp_audit with sourcetype=ocp_audit. Ensure verbs, users, userGroups, objectRef.apiGroup, objectRef.resource, objectRef.name, objectRef.namespace, and responseStatus code are extracted. Retain RequestResponse level for patch and update on clusterversions only when policy mandates; many teams use Metadata for high-volume resources and RequestResponse for cluster-scoped ClusterVersion mutations.

Logs lane: collect Cluster Version Operator pod logs from namespace openshift-cluster-version using Splunk OpenShift App log collection patterns, OpenTelemetry filelog or container log receivers, or cluster logging forwarders. Set sourcetype=ocp_logs, include cluster, namespace, pod, container, and stream fields when available, and preserve stack traces or Cincinnati client errors referencing https://api.openshift.com/api/upgrades_info/v1/graph style paths without logging secrets.

Optional synthetic graph reachability lane: some teams run a short curl or openshift-cli based probe from a management host that records HTTP result codes against the public upgrade graph endpoint for the active channel and lands sourcetype=ocp_clusterversion with graph_probe_http_code and graph_probe_ok boolean fields. If you adopt this, document proxy authentication headers are never written to Splunk.

Example oc verification operators run during design reviews:

```bash
oc get clusterversion -o json | jq '.items[0].status.history[0]'
oc adm upgrade
oc get clusteroperator version -o json | jq '.status.conditions'
```

Example audit filter during controlled changes: search ocp_audit for objectRef.resource=clusterversions and objectRef.name=cluster to replay administrative version bumps.

props.conf guidance: TRUNCATE sufficiently large for JSON, TIMESTAMP_FIELDS respected when HEC time is authoritative, LINE_BREAKER rules for prometheus exposition when multiplexed with syslog headers.

Pre-save validation: index=ocp_metrics sourcetype=ocp_clusterversion earliest=-1h must return non-zero event counts after the first collection interval; prometheus lines must include cluster_version after scrape begins; ocp_audit should show cluster-scoped mutations during intentional test channel edits in lab; ocp_logs should include CVO leader messages during upgrades.

Collector hardening: run forwarders with TLS to Splunk, rotate HEC tokens quarterly, and document which management cluster forwards development versus production to prevent label collisions. When multiple regions share one Splunk tenant, include region and cloud_account on every HEC event.

Dashboards: the Splunk OpenShift App should host a timeline visualization keyed on hist_state and progressing dwell, plus drilldowns to raw ocp_clusterversion JSON, prometheus lines, audit rows, and CVO logs. Splunk ITSI users can bind the saved search to a service entity per cluster with KPIs for history failures and graph reachability.

### Step 3 — Create the search and alert

Save the SPL as openshift_uc_3_3_1_clusterversion_cvo_upgrade with a fifteen minute schedule, dispatch earliest=-6h@h, dispatch latest=now, and alert when severity is page or warn. Throttle duplicate cluster rows for thirty minutes unless severity escalates from warn to page. Include recommended_action, prog_dwell_h, and retrieved_updates_flag in pager descriptions so incident commanders open the correct runbook section without re-running ad hoc searches.

Pipeline narrative for operators: multisearch fans ClusterVersion snapshots, Prometheus cluster_version counters, audit activity on clusterversions/cluster, and CVO log hints so a silent metrics outage does not hide a genuinely Failing ClusterVersion condition. coalesce() absorbs field naming drift between exporters. streamstats measures short-term Progressing dwell by cluster. eventstats adds fleet context such as count of clusters with RetrievedUpdates=False. case() maps Failing=True, sustained Progressing beyond Z-stream or Y-stream hour thresholds, RetrievedUpdates=False with corroborating log hints, spec versus status version divergence beyond grace windows, and history Partial or Failed rows into page versus warn versus info tiers. recommended_action encodes the next mechanical step without pretending Splunk replaces oc adm upgrade clear or must-gather.

Fenced SPL must match the spl JSON field exactly:

```spl
`comment("UC-3.3.1 ClusterVersion CVO upgrade — ocp_clusterversion + prometheus:cluster_version + ocp_audit + ocp_logs. Tunables: z_stream_prog_page_h=6 y_stream_prog_page_h=10 retrieved_warn_h=2 earliest=-6h@h latest=now")`
| multisearch
    [ search (index=ocp_metrics OR index=ocp_audit) sourcetype=ocp_clusterversion earliest=-6h@h latest=now
      | eval cluster=lower(trim(toString(coalesce(cluster, openshift_cluster, cluster_name, cluster_id, ""))))
      | eval channel=lower(trim(toString(coalesce(spec_channel, channel, status_channel, desired_channel, ""))))
      | eval spec_version=trim(toString(coalesce(spec_desired_version, desired_version_spec, spec_desiredUpdate_version, "")))
      | eval status_version=trim(toString(coalesce(status_desired_version, desired_version_status, observed_version, "")))
      | eval spec_upstream=trim(toString(coalesce(spec_upstream, upstream, "")))
      | eval overrides_present=tonumber(tostring(coalesce(overrides_count, overrides_present, "0")),10)
      | eval paused_hint=lower(trim(toString(coalesce(paused_flag, spec_paused, paused, ""))))
      | eval prog_st=lower(trim(toString(coalesce(conditions_progressing_status, progressing_status, progressing, ""))))
      | eval fail_st=lower(trim(toString(coalesce(conditions_failing_status, failing_status, failing, ""))))
      | eval avail_st=lower(trim(toString(coalesce(conditions_available_status, available_status, available, ""))))
      | eval upg_st=lower(trim(toString(coalesce(conditions_upgradeable_status, upgradeable_status, upgradeable, ""))))
      | eval retr_st=lower(trim(toString(coalesce(conditions_retrievedupdates_status, retrievedupdates_status, retrieved_updates, ""))))
      | eval prog_flag=if(match(prog_st,"true|1"),1,0)
      | eval fail_flag=if(match(fail_st,"true|1"),1,0)
      | eval avail_flag=if(match(avail_st,"false|0"),1,0)
      | eval upgradeable_warn=if(match(upg_st,"false|0"),1,0)
      | eval retrieved_ok=if(match(retr_st,"false|0"),0,1)
      | eval hist_state=lower(trim(toString(coalesce(history_state, hist_state, last_history_state, ""))))
      | eval hist_version=trim(toString(coalesce(history_version, hist_version, last_history_version, "")))
      | eval graph_reach_flag=tonumber(tostring(coalesce(graph_probe_ok, graph_reachable, "1")),10)
      | eval cond_msg=trim(toString(coalesce(conditions_progressing_message, progressing_message, cv_message, "")))
      | eval ltt_p=trim(toString(coalesce(ltt_progressing, last_transition_progressing, "")))
      | eval ltt_epoch=if(len(ltt_p)>0 AND match(ltt_p,"^[0-9]{4}-"), strptime(ltt_p, "%Y-%m-%dT%H:%M:%SZ"), null())
      | sort 0 + cluster - _time
      | streamstats window=2 current=t global=f last(_time) AS prev_ts last(prog_flag) AS prev_prog BY cluster
      | eval prog_dwell_h=if(prog_flag==1 AND prev_prog==1 AND isnotnull(prev_ts), round((_time - prev_ts)/3600, 3), if(prog_flag==1, round((now()-_time)/3600, 3), 0))
      | eval lane="cv_snap"
      | fields _time cluster channel spec_version status_version spec_upstream overrides_present paused_hint prog_flag fail_flag avail_flag upgradeable_warn retrieved_ok hist_state hist_version graph_reach_flag cond_msg prog_dwell_h lane ltt_epoch ]
    [ search index=ocp_metrics (sourcetype=prometheus:cluster_version OR sourcetype=prometheus:metrics) earliest=-6h@h latest=now
      | eval cluster=lower(trim(toString(coalesce(cluster, openshift_cluster, cluster_name, k8s_cluster_name, ""))))
      | eval mn=lower(trim(toString(coalesce(__name__, metric_name, name, ""))))
      | eval mv=tonumber(tostring(coalesce(value, metric_value, Value, "")), 10)
      | where match(mn,"^cluster_version$")
      | eval ctype=lower(trim(toString(coalesce(type, label_type, ""))))
      | eval cver=trim(toString(coalesce(version, label_version, "")))
      | eval lane="cv_prom"
      | stats latest(_time) AS last_prom_t sum(eval(if(ctype=="completed", mv, 0))) AS cv_completed_sum latest(ctype) AS prom_type latest(cver) AS prom_version BY cluster lane ]
    [ search index=ocp_audit sourcetype=ocp_audit earliest=-6h@h latest=now
      | eval cluster=lower(trim(toString(coalesce(cluster, openshift_cluster, cluster_name, ""))))
      | eval res=lower(trim(toString(coalesce(objectRef_resource, resource, ""))))
      | eval cname=lower(trim(toString(coalesce(objectRef_name, object_name, ""))))
      | eval verb=lower(trim(toString(coalesce(verb, request_verb, ""))))
      | where match(res,"clusterversions") AND match(cname,"^cluster$") AND match(verb,"patch|update|create")
      | eval actor=trim(toString(coalesce(user_username, user, requestUser_username, "")))
      | eval lane="cv_aud"
      | stats latest(_time) AS last_aud_t values(verb) AS audit_verbs latest(actor) AS audit_actor count AS aud_mut_cnt BY cluster lane ]
    [ search index=ocp_logs sourcetype=ocp_logs earliest=-6h@h latest=now
      | eval cluster=lower(trim(toString(coalesce(cluster, openshift_cluster, cluster_name, ""))))
      | eval ns=lower(trim(toString(coalesce(namespace, k8s_namespace, ""))))
      | where match(ns,"openshift-cluster-version") OR match(lower(_raw),"cluster-version-operator|cincinnati|upgrades_info")
      | eval log_hint=if(match(lower(_raw),"upgrades_info|api\\.openshift\\.com|proxy|timeout|signature|verify"),1,0)
      | eval lane="cvo_log"
      | stats latest(_time) AS last_log_t max(log_hint) AS cvo_log_hint latest(_raw) AS cvo_log_sample BY cluster lane ]
| eval cluster=lower(trim(coalesce(cluster, "unknown_cluster")))
| stats max(_time) AS last_seen first(channel) AS channel max(spec_version) AS spec_version max(status_version) AS status_version first(spec_upstream) AS spec_upstream max(overrides_present) AS overrides_present values(paused_hint) AS paused_vals max(prog_flag) AS prog_flag max(fail_flag) AS fail_flag max(avail_flag) AS avail_flag max(upgradeable_warn) AS upgradeable_warn min(retrieved_ok) AS retrieved_ok first(hist_state) AS hist_state first(hist_version) AS hist_version min(graph_reach_flag) AS graph_reach_flag values(cond_msg) AS cmv max(prog_dwell_h) AS prog_dwell_h max(last_prom_t) AS last_prom_t max(cv_completed_sum) AS cv_completed_sum first(prom_type) AS prom_type first(prom_version) AS prom_version max(last_aud_t) AS last_aud_t first(audit_verbs) AS audit_verbs first(audit_actor) AS audit_actor max(aud_mut_cnt) AS aud_mut_cnt max(last_log_t) AS last_log_t max(cvo_log_hint) AS cvo_log_hint first(cvo_log_sample) AS cvo_log_sample BY cluster
| eval cond_msg=trim(toString(mvindex(mvdedup(cmv),0)))
| eval paused_hint=lower(trim(toString(mvindex(mvdedup(paused_vals),0))))
| eval spec_status_gap=if(len(spec_version)>0 AND len(status_version)>0 AND spec_version!=status_version,1,0)
| eval y_stream_hint=if(match(channel,"eus|stable|candidate|fast") AND match(spec_version,"^[0-9]+\\.[0-9]+\\.0$"),1,0)
| eval prog_page_h=if(y_stream_hint==1,10,6)
| eval retrieved_streak=if(retrieved_ok==0,1,0)
| eventstats sum(retrieved_streak) AS fleet_retrieve_fail_cnt BY cluster
| eventstats max(prog_dwell_h) AS fleet_max_prog_dwell BY cluster
| eval severity=case(
    fail_flag==1, "page",
    match(hist_state,"partial|failed"), "page",
    prog_flag==1 AND prog_dwell_h>=prog_page_h, "page",
    retrieved_ok==0 AND cvo_log_hint==1, "page",
    spec_status_gap==1 AND prog_flag==1 AND prog_dwell_h>=2, "warn",
    prog_flag==1 AND prog_dwell_h>=4, "warn",
    retrieved_ok==0, "warn",
    upgradeable_warn==1 AND prog_flag==1, "warn",
    avail_flag==1, "warn",
    true(), "info")
| eval recommended_action=case(
    fail_flag==1 OR match(hist_state,"failed"), "oc_adm_upgrade_and_gather_cvo_logs_must_gather",
    match(hist_state,"partial"), "review_clusterversion_history_and_operator_payload_errors",
    retrieved_ok==0, "verify_egress_proxy_and_tls_to_api_openshift_graph",
    spec_status_gap==1, "confirm_image_mirror_and_signature_config_then_oc_describe_clusterversion",
    upgradeable_warn==1, "read_upgradeable_false_message_and_gates_before_forcing_upgrade",
    prog_flag==1 AND prog_dwell_h>=prog_page_h, "inspect_machine_config_and_cvo_events_for_stuck_reconciliation",
    cvo_log_hint==1, "trace_cincinnati_client_errors_in_openshift_cluster_version_namespace",
    true(), "refresh_oc_get_clusterversion_snapshot_and_prometheus_cluster_version")
| join type=left max=0 cluster
    [| inputlookup openshift_cluster_inventory.csv
     | fields cluster, cluster_tier, owner_team, environment]
| eval cluster_tier=coalesce(cluster_tier, "unrated"),
       owner_team=coalesce(owner_team, "unowned"),
       environment=coalesce(environment, "unknown")
| table cluster channel spec_version status_version spec_status_gap prog_flag prog_dwell_h fail_flag hist_state retrieved_ok graph_reach_flag cvo_log_hint upgradeable_warn audit_actor severity recommended_action last_seen prom_version aud_mut_cnt cv_completed_sum paused_hint cond_msg cluster_tier owner_team environment
```

savedsearches.conf sketch:

```ini
[openshift_uc_3_3_1_clusterversion_cvo_upgrade_alert]
cron_schedule = */15 * * * *
dispatch.earliest_time = -6h@h
dispatch.latest_time = now
enableSched = 1
action.email = 1
action.email.to = openshift-platform@example.com
action.email.subject = OCP ClusterVersion $result.severity$ $result.cluster$ prog_h=$result.prog_dwell_h$
counttype = number of events
relation = greater than
quantity = 0
search = | savedsearch openshift_uc_3_3_1_clusterversion_cvo_upgrade | where severity IN ("page","warn")
```

Performance: if Job Inspector shows multisearch queue time above your SLA, materialize ocp_clusterversion snapshots hourly into a summary index keyed on cluster, widen alert searches to earliest=-2h@h on the summary, and keep this full search for investigations.

For Splunk ITSI optional deployments, bind KPIs to prog_dwell_h and to retrieved_ok minima per cluster, attaching episode policies when two consecutive windows stay non-info for mission-tier entities.

### Step 4 — Validate

Ground truth always starts on-cluster. Run oc get clusterversion -o wide and compare CHANNEL, VERSION, AVAILABLE, PROGRESSING, and SINCE columns to the Splunk row for the same cluster inside the last snapshot window. When statuses disagree, first verify resourceVersion freshness and indexer clock skew before blaming Splunk parsing.

Deep dive with oc describe clusterversion cluster to read condition messages, history rows, desired update blocks, and any override lists. Splunk should mirror Progressing=True and Failing=True transitions within one collection interval; if not, tighten scripted input frequency or fix token expiration on the management host.

Prometheus cross-check: in the OpenShift console monitoring stack or via oc get --raw against Thanos querier routes, validate cluster_version series for type=completed and version labels that align with status.history entries. When metrics show monotonic counters while API history stalls, suspect stale snapshots or dual-cluster label collisions; reconcile external_labels on scrapers.

Audit correlation: replay a controlled oc patch clusterversion or channel change in lab and confirm ocp_audit rows include verbs, actors, and object names without indexing sensitive request bodies beyond policy.

Logs correlation: during validation, oc logs -n openshift-cluster-version deploy/cluster-version-operator --tail=200 should surface messages that Splunk cvo_log_sample rows capture when log shipper sampling permits.

Graph reachability: from a management host with the same proxy chain production clusters use, curl the documented upgrade graph URL pattern for your channel and compare TLS failures to RetrievedUpdates=False windows in Splunk.

Synthetic validation: in a lab cluster, apply a documented delayed upgrade or pause semantics under vendor guidance, observe Progressing=True, and confirm openshift_uc_3_3_1_clusterversion_cvo_upgrade surfaces warn or info with non-null recommended_action until completion. Roll forward, watch recovery, and confirm severity returns to info.

Negative test: on a healthy cluster after upgrade completion with history Completed and Progressing=False, confirm the alert wrapper returns zero rows for page and warn filters.

Runbook linkage: document expected dwell times during Z-stream versus Y-stream upgrades so validators do not open false defects against the saved search when internal service-level agreements allow longer master pool reboot phases. Compare Splunk cluster labels to infrastructure cluster identifiers when multiple labs share one Splunk tenant.

### Step 5 — Operationalize & Troubleshoot

Case 1 — Progressing=True for several hours during a Z-stream patch with steady operator payload advancement: treat as normal until prog_dwell_h exceeds your Z-stream threshold; pair with oc adm upgrade and history startedTime before paging.

Case 2 — Progressing=True beyond the Y-stream window with machine-config master pool reboots underway: correlate UC-3.3.17 sibling analytics only for node-config symptoms without conflating MCP timelines as ClusterVersion root cause; CVO may still own the overall history row.

Case 3 — RetrievedUpdates=False with proxy CONNECT errors in CVO logs: engage network teams on corporate egress allow lists for api.openshift.com and intermediate certificate stores; verify global proxy TrustedCA ConfigMaps.

Case 4 — spec.desiredUpdate.version differs from status.desired.version during mirror delays: validate ImageContentSourcePolicy and oc adm release info paths before declaring failure; mirror sync jobs often explain short gaps.

Case 5 — history state Failed immediately after oc adm upgrade --to override: capture audit_actor and audit_verbs; operator-driven jumps can produce benign Failed rows superseded by newer attempts.

Case 6 — Failing=True with signature verification messages: inspect cluster version operator ConfigMaps for trusted keys and verify release image signatures against vendor documentation before forcing overrides.

Case 7 — Upgradeable=False during scheduled upgrade gates: join to change calendars; many gates are intentional risk controls rather than telemetry faults.

Case 8 — spec.overrides present during hotfix pins: confirm change tickets; Splunk should downgrade noise when override_authorized metadata appears on HEC events.

Case 9 — clusteroperator/version reports Degraded while ClusterVersion remains Available: triage with UC-3.3.6 patterns for the version operator heartbeat without merging the entire ClusterOperator matrix into this saved search.

Case 10 — Graph probe lane absent but RetrievedUpdates=True: do not invent reachability failures; treat missing optional probes as unknown graph state and rely on conditions.

Case 11 — Duplicate ClusterVersion snapshots from redundant collectors: dedupe on cluster and snapshot_generation in summary indexes when cost matters.

Case 12 — Fleet-wide healthy clusters with info severities only: use as a control test that telemetry, parsers, and tokens work; spot-check weekly that Splunk rows still match oc get clusterversion for every production cluster.

Closing checklist: multisearch lists four lanes; coalesce normalizes cluster fields; streamstats and eventstats quantify dwell and fleet RetrievedUpdates context; case() implements severity tiers; closing table includes cluster, channel, spec_version, status_version, spec_status_gap, prog_flag, prog_dwell_h, fail_flag, hist_state, retrieved_ok, graph_reach_flag, cvo_log_hint, upgradeable_warn, audit_actor, severity, recommended_action, last_seen, prom_version, aud_mut_cnt, cv_completed_sum, paused_hint, cond_msg for twenty-one analyst-visible columns.

## SPL

```spl
`comment("UC-3.3.1 ClusterVersion CVO upgrade — ocp_clusterversion + prometheus:cluster_version + ocp_audit + ocp_logs. Tunables: z_stream_prog_page_h=6 y_stream_prog_page_h=10 retrieved_warn_h=2 earliest=-6h@h latest=now")`
| multisearch
    [ search (index=ocp_metrics OR index=ocp_audit) sourcetype=ocp_clusterversion earliest=-6h@h latest=now
      | eval cluster=lower(trim(toString(coalesce(cluster, openshift_cluster, cluster_name, cluster_id, ""))))
      | eval channel=lower(trim(toString(coalesce(spec_channel, channel, status_channel, desired_channel, ""))))
      | eval spec_version=trim(toString(coalesce(spec_desired_version, desired_version_spec, spec_desiredUpdate_version, "")))
      | eval status_version=trim(toString(coalesce(status_desired_version, desired_version_status, observed_version, "")))
      | eval spec_upstream=trim(toString(coalesce(spec_upstream, upstream, "")))
      | eval overrides_present=tonumber(tostring(coalesce(overrides_count, overrides_present, "0")),10)
      | eval paused_hint=lower(trim(toString(coalesce(paused_flag, spec_paused, paused, ""))))
      | eval prog_st=lower(trim(toString(coalesce(conditions_progressing_status, progressing_status, progressing, ""))))
      | eval fail_st=lower(trim(toString(coalesce(conditions_failing_status, failing_status, failing, ""))))
      | eval avail_st=lower(trim(toString(coalesce(conditions_available_status, available_status, available, ""))))
      | eval upg_st=lower(trim(toString(coalesce(conditions_upgradeable_status, upgradeable_status, upgradeable, ""))))
      | eval retr_st=lower(trim(toString(coalesce(conditions_retrievedupdates_status, retrievedupdates_status, retrieved_updates, ""))))
      | eval prog_flag=if(match(prog_st,"true|1"),1,0)
      | eval fail_flag=if(match(fail_st,"true|1"),1,0)
      | eval avail_flag=if(match(avail_st,"false|0"),1,0)
      | eval upgradeable_warn=if(match(upg_st,"false|0"),1,0)
      | eval retrieved_ok=if(match(retr_st,"false|0"),0,1)
      | eval hist_state=lower(trim(toString(coalesce(history_state, hist_state, last_history_state, ""))))
      | eval hist_version=trim(toString(coalesce(history_version, hist_version, last_history_version, "")))
      | eval graph_reach_flag=tonumber(tostring(coalesce(graph_probe_ok, graph_reachable, "1")),10)
      | eval cond_msg=trim(toString(coalesce(conditions_progressing_message, progressing_message, cv_message, "")))
      | eval ltt_p=trim(toString(coalesce(ltt_progressing, last_transition_progressing, "")))
      | eval ltt_epoch=if(len(ltt_p)>0 AND match(ltt_p,"^[0-9]{4}-"), strptime(ltt_p, "%Y-%m-%dT%H:%M:%SZ"), null())
      | sort 0 + cluster - _time
      | streamstats window=2 current=t global=f last(_time) AS prev_ts last(prog_flag) AS prev_prog BY cluster
      | eval prog_dwell_h=if(prog_flag==1 AND prev_prog==1 AND isnotnull(prev_ts), round((_time - prev_ts)/3600, 3), if(prog_flag==1, round((now()-_time)/3600, 3), 0))
      | eval lane="cv_snap"
      | fields _time cluster channel spec_version status_version spec_upstream overrides_present paused_hint prog_flag fail_flag avail_flag upgradeable_warn retrieved_ok hist_state hist_version graph_reach_flag cond_msg prog_dwell_h lane ltt_epoch ]
    [ search index=ocp_metrics (sourcetype=prometheus:cluster_version OR sourcetype=prometheus:metrics) earliest=-6h@h latest=now
      | eval cluster=lower(trim(toString(coalesce(cluster, openshift_cluster, cluster_name, k8s_cluster_name, ""))))
      | eval mn=lower(trim(toString(coalesce(__name__, metric_name, name, ""))))
      | eval mv=tonumber(tostring(coalesce(value, metric_value, Value, "")), 10)
      | where match(mn,"^cluster_version$")
      | eval ctype=lower(trim(toString(coalesce(type, label_type, ""))))
      | eval cver=trim(toString(coalesce(version, label_version, "")))
      | eval lane="cv_prom"
      | stats latest(_time) AS last_prom_t sum(eval(if(ctype=="completed", mv, 0))) AS cv_completed_sum latest(ctype) AS prom_type latest(cver) AS prom_version BY cluster lane ]
    [ search index=ocp_audit sourcetype=ocp_audit earliest=-6h@h latest=now
      | eval cluster=lower(trim(toString(coalesce(cluster, openshift_cluster, cluster_name, ""))))
      | eval res=lower(trim(toString(coalesce(objectRef_resource, resource, ""))))
      | eval cname=lower(trim(toString(coalesce(objectRef_name, object_name, ""))))
      | eval verb=lower(trim(toString(coalesce(verb, request_verb, ""))))
      | where match(res,"clusterversions") AND match(cname,"^cluster$") AND match(verb,"patch|update|create")
      | eval actor=trim(toString(coalesce(user_username, user, requestUser_username, "")))
      | eval lane="cv_aud"
      | stats latest(_time) AS last_aud_t values(verb) AS audit_verbs latest(actor) AS audit_actor count AS aud_mut_cnt BY cluster lane ]
    [ search index=ocp_logs sourcetype=ocp_logs earliest=-6h@h latest=now
      | eval cluster=lower(trim(toString(coalesce(cluster, openshift_cluster, cluster_name, ""))))
      | eval ns=lower(trim(toString(coalesce(namespace, k8s_namespace, ""))))
      | where match(ns,"openshift-cluster-version") OR match(lower(_raw),"cluster-version-operator|cincinnati|upgrades_info")
      | eval log_hint=if(match(lower(_raw),"upgrades_info|api\\.openshift\\.com|proxy|timeout|signature|verify"),1,0)
      | eval lane="cvo_log"
      | stats latest(_time) AS last_log_t max(log_hint) AS cvo_log_hint latest(_raw) AS cvo_log_sample BY cluster lane ]
| eval cluster=lower(trim(coalesce(cluster, "unknown_cluster")))
| stats max(_time) AS last_seen first(channel) AS channel max(spec_version) AS spec_version max(status_version) AS status_version first(spec_upstream) AS spec_upstream max(overrides_present) AS overrides_present values(paused_hint) AS paused_vals max(prog_flag) AS prog_flag max(fail_flag) AS fail_flag max(avail_flag) AS avail_flag max(upgradeable_warn) AS upgradeable_warn min(retrieved_ok) AS retrieved_ok first(hist_state) AS hist_state first(hist_version) AS hist_version min(graph_reach_flag) AS graph_reach_flag values(cond_msg) AS cmv max(prog_dwell_h) AS prog_dwell_h max(last_prom_t) AS last_prom_t max(cv_completed_sum) AS cv_completed_sum first(prom_type) AS prom_type first(prom_version) AS prom_version max(last_aud_t) AS last_aud_t first(audit_verbs) AS audit_verbs first(audit_actor) AS audit_actor max(aud_mut_cnt) AS aud_mut_cnt max(last_log_t) AS last_log_t max(cvo_log_hint) AS cvo_log_hint first(cvo_log_sample) AS cvo_log_sample BY cluster
| eval cond_msg=trim(toString(mvindex(mvdedup(cmv),0)))
| eval paused_hint=lower(trim(toString(mvindex(mvdedup(paused_vals),0))))
| eval spec_status_gap=if(len(spec_version)>0 AND len(status_version)>0 AND spec_version!=status_version,1,0)
| eval y_stream_hint=if(match(channel,"eus|stable|candidate|fast") AND match(spec_version,"^[0-9]+\\.[0-9]+\\.0$"),1,0)
| eval prog_page_h=if(y_stream_hint==1,10,6)
| eval retrieved_streak=if(retrieved_ok==0,1,0)
| eventstats sum(retrieved_streak) AS fleet_retrieve_fail_cnt BY cluster
| eventstats max(prog_dwell_h) AS fleet_max_prog_dwell BY cluster
| eval severity=case(
    fail_flag==1, "page",
    match(hist_state,"partial|failed"), "page",
    prog_flag==1 AND prog_dwell_h>=prog_page_h, "page",
    retrieved_ok==0 AND cvo_log_hint==1, "page",
    spec_status_gap==1 AND prog_flag==1 AND prog_dwell_h>=2, "warn",
    prog_flag==1 AND prog_dwell_h>=4, "warn",
    retrieved_ok==0, "warn",
    upgradeable_warn==1 AND prog_flag==1, "warn",
    avail_flag==1, "warn",
    true(), "info")
| eval recommended_action=case(
    fail_flag==1 OR match(hist_state,"failed"), "oc_adm_upgrade_and_gather_cvo_logs_must_gather",
    match(hist_state,"partial"), "review_clusterversion_history_and_operator_payload_errors",
    retrieved_ok==0, "verify_egress_proxy_and_tls_to_api_openshift_graph",
    spec_status_gap==1, "confirm_image_mirror_and_signature_config_then_oc_describe_clusterversion",
    upgradeable_warn==1, "read_upgradeable_false_message_and_gates_before_forcing_upgrade",
    prog_flag==1 AND prog_dwell_h>=prog_page_h, "inspect_machine_config_and_cvo_events_for_stuck_reconciliation",
    cvo_log_hint==1, "trace_cincinnati_client_errors_in_openshift_cluster_version_namespace",
    true(), "refresh_oc_get_clusterversion_snapshot_and_prometheus_cluster_version")
| join type=left max=0 cluster
    [| inputlookup openshift_cluster_inventory.csv
     | fields cluster, cluster_tier, owner_team, environment]
| eval cluster_tier=coalesce(cluster_tier, "unrated"),
       owner_team=coalesce(owner_team, "unowned"),
       environment=coalesce(environment, "unknown")
| table cluster channel spec_version status_version spec_status_gap prog_flag prog_dwell_h fail_flag hist_state retrieved_ok graph_reach_flag cvo_log_hint upgradeable_warn audit_actor severity recommended_action last_seen prom_version aud_mut_cnt cv_completed_sum paused_hint cond_msg cluster_tier owner_team environment
```

## CIM SPL

```spl
| tstats summariesonly=true latest(Change.action) AS change_action latest(Change.object) AS change_object latest(Change.user) AS change_user FROM datamodel=Change WHERE nodename=Change earliest=-24h@h latest=now BY Change.dest
| rename Change.dest AS cim_dest
| join type=left max=0 cim_dest
    [| tstats summariesonly=true latest(Application_State.state) AS app_state latest(Application_State.info) AS app_info FROM datamodel=Application_State WHERE nodename=Application_State earliest=-24h@h latest=now BY Application_State.dest
     | rename Application_State.dest AS cim_dest ]
| where like(lower(change_object), "%clusterversion%") OR like(lower(app_info), "%openshift%cluster%version%")
| table cim_dest change_action change_object change_user app_state app_info
```

## Visualization

Severity-colored table by cluster with drilldowns to raw ocp_clusterversion JSON, prometheus:cluster_version lines, ocp_audit rows, and ocp_logs stack traces; timeline of prog_dwell_h against history state; single-value tiles for RetrievedUpdates false counts per fleet.

## Known False Positives

Operator teams routinely invoke oc adm upgrade with explicit --to targets during vendor-guided recovery; audit rows and short-lived history Failed or Partial entries can precede a healthy Completed row without indicating a stuck cluster. Z-stream patches often hold Progressing=True for several hours while machine-config reboots serialize across control-plane nodes; tune prog_page_h to your internal service-level expectation before paging leadership. RetrievedUpdates=False may appear briefly during scheduled proxy maintenance or transitive certificate rotations on outbound inspection appliances; require cvo_log_hint corroboration or sustained duration across multiple snapshot intervals before treating reachability as broken. Paused upgrades during enterprise change-freeze windows, including financial institution cutoff periods, are deliberate; join alerts to change calendars or HEC metadata so governance freezes do not present as incidents. CVO pods may restart during master pool rollouts and emit noisy log lines without changing ClusterVersion conditions; compare message timestamps to history startedTime. Image mirror synchronization lag can widen spec versus status desired version gaps while pulls still succeed; verify mirror freshness before blaming signature faults. Duplicate telemetry from redundant collectors can inflate aud_mut_cnt; dedupe on audit auditID when present. Lab clusters that constantly churn channels generate noisy warn tiers unless routed to non-production indexes.

## References

- [OpenShift Documentation — Introduction to OpenShift updates](https://docs.openshift.com/container-platform/latest/updating/understanding_updates/intro-to-updates.html)
- [OpenShift Documentation — Updating a cluster using the CLI](https://docs.openshift.com/container-platform/latest/updating/updating_a_cluster/updating-cluster-cli.html)
- [OpenShift Documentation — Understanding upgrade channels](https://docs.openshift.com/container-platform/latest/updating/understanding_updates/understanding-upgrade-channels-release.html)
- [OpenShift REST API Reference — ClusterVersion](https://docs.openshift.com/container-platform/latest/rest_api/config_apis/clusterversion-config-openshift-io-v1.html)
- [OpenShift Documentation — Architecture (Cluster Version Operator context)](https://docs.openshift.com/container-platform/latest/architecture/architecture.html)
- [OpenShift Documentation — Gathering data about your cluster](https://docs.openshift.com/container-platform/latest/support/gathering-cluster-data.html)
- [Red Hat Blog — The Ultimate Guide to OpenShift Update for Cluster Administrators](https://www.redhat.com/en/blog/the-ultimate-guide-to-openshift-update-for-cluster-administrators)
