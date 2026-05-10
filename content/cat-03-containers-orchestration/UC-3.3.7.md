<!-- AUTO-GENERATED from UC-3.3.7.json — DO NOT EDIT -->

---
id: "3.3.7"
title: "OpenShift BuildConfig and S2I or Docker Build Failure Detection"
status: "verified"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-3.3.7 · OpenShift BuildConfig and S2I or Docker Build Failure Detection

> **Criticality:** Medium &middot; **Difficulty:** Advanced &middot; **Pillar:** Observability &middot; **Type:** Reliability, Performance &middot; **Wave:** Walk &middot; **Status:** Verified

*We watch the automated assembly line that turns source code into runnable images inside OpenShift. When that line keeps stopping—fetch errors, push errors, or broken test hooks—we notice early so teams fix the pipeline before releases stall.*

---

## Description

Correlates OpenShift Build objects created by the BuildConfig controller across S2I Source strategy, Docker strategy, and JenkinsPipeline strategy builds: phase transitions from New through Pending and Running into Complete versus Failed versus Cancelled versus Error, controller reason codes that explain fetch, assemble, post-commit, registry push, and builder-image retrieval faults, per-BuildConfig failure rates versus successful completions inside a rolling window, and build duration distributions that creep before CI/CD regressions become release-blocking. The analytic intentionally targets build.openshift.io primitives that vanilla Kubernetes does not ship, including history limit fields on BuildConfig that prune retained Build rows and in-cluster image-registry push steps that surface as PushImageToRegistryFailed. Splunk multisearch joins structured Build snapshots, BuildConfig audit context, Kubernetes Events on Build involved objects, optional openshift_build_total style Prometheus counters, and registry-adjacent hints so analysts distinguish orchestration failure from image pull coverage (UC-3.1.26), image layer bloat (UC-3.1.15), cache efficiency (UC-3.1.18), vulnerability triage (UC-3.1.10), scanning coverage SLAs (UC-3.1.5), ImageStream digest drift (UC-3.3.10 reserved), and DeploymentConfig rollout analytics (UC-3.3.16 reserved).

## Value

Platform and developer productivity leaders regain predictable release cadence when OpenShift build orchestration is monitored as a first-class CI/CD plane rather than a sequence of ad hoc oc describe commands: repeated FetchSourceFailed rows after Git maintenance, PushImageToRegistryFailed spikes during registry rate-limit mornings, PostCommitHookFailed after test harness changes, and FailedRetrieveBuilder surges when cluster image policy blocks a refreshed S2I builder all show up in one Splunk table with severity, recommended_action verbs, and fleet percentile context. FinOps and SRE teams quantify how often failing builds burn elastic compute on retry storms, while audit stakeholders retain tamper-evident telemetry tying API object phases to audit identities without conflating the signal with runtime pod ImagePullBackOff (UC-3.2.14). Steering committees receive evidence that BuildConfig governance knobs such as failedBuildsHistoryLimit are paired with observability so pruned history does not hide failure trends.

## Implementation

Land ocp_build, ocp_buildconfig, k8s_events for Build involved objects, and ocp_audit for build.openshift.io API activity into ocp_events or ocp_audit indexes with cluster labels. Normalize openshift.io/build-config.name and strategy fields in props. Save openshift_uc_3_3_7_buildconfig_failure_regression every fifteen minutes over earliest=-24h@h, join optional prometheus:metrics openshift_build counters by cluster, route page and warn to platform and CI owners, and archive weekly CSV exports with exporter commit hashes.

## Evidence

Saved search openshift_uc_3_3_7_buildconfig_failure_regression with fifteen minute schedule; versioned exporter manifests in git with commit hash captured in weekly CSV exports; dashboard drilldowns on ocp_build, ocp_buildconfig, k8s_events, ocp_audit, and prometheus:metrics; alert stanza with platform and CI routing keys.

## Control test

### Positive scenario

In a lab OpenShift project, apply a BuildConfig whose Git source URI references a non-existent branch, run oc start-build, wait until the Build reaches Failed with reason FetchSourceFailed, ingest ocp_build and k8s_events rows, execute openshift_uc_3_3_7_buildconfig_failure_regression, and expect warn or page severity with validate_git_connectivity_credentials_and_webhook_secret or correlate_builder_pod_logs_and_events recommended_action text.

### Negative scenario

Restore the Git reference to a valid branch, rerun builds until phase reaches Complete with fail_obs at zero for the rolling window, and confirm severity returns to info while the alert wrapper filtered to page and warn emits zero qualifying rows.

## Detailed Implementation

### Step 1 — Prerequisites

Head of Platform owns this control with the OpenShift platform engineering lead who administers the build.openshift.io API, the developer experience sponsor accountable for CI/CD SLOs, and the observability engineers who operate Splunk HTTP Event Collector tokens plus collectors that receive OpenShift API watch streams, audit feeds, and federated Prometheus scrapes. This use case isolates the OpenShift BuildConfig controller contract: BuildConfig objects declare source inputs, output ImageStream targets, strategy (Source for S2I including assemble and save-artifacts hooks, Docker for Dockerfile builds inside cluster builders, JenkinsPipeline for integration with external Jenkins), triggers that materialize Build children, and history retention via spec.failedBuildsHistoryLimit and spec.successfulBuildsHistoryLimit. Each trigger or manual instantiation creates a Build with metadata.labels openshift.io/build-config.name pointing back to the parent BuildConfig. The Build status reports phases New, Pending, Running, Complete, Failed, Cancelled, and Error, with reason tokens such as FetchSourceFailed when Git or binary inputs cannot be retrieved, PushImageToRegistryFailed when the integrated registry or external registry rejects a layer push, PostCommitHookFailed when the optional postCommit hook exits non-zero, and FailedRetrieveBuilder when the nominated builder image cannot be pulled or is rejected by policy. Admission and controller events may surface as FailedCreate or FailedSync style messages on BuildConfig or Build objects when resource quotas, security constraints, or validating admission webhooks block reconciliation.

UC-3.1.18 remains Docker BuildKit cache hit ratio and CI runner throughput outside the OpenShift Build controller ledger. UC-3.1.15 remains image layer size analytics after an image exists. UC-3.1.10 and UC-3.1.5 remain vulnerability findings and scanning governance rather than build orchestration outcomes. UC-3.1.26 and UC-3.2.14 remain pull-side registry connectivity and runtime ImagePullBackOff symptoms rather than Build status reasons on the assemble and push path. UC-3.3.10 remains reserved for ImageStream digest drift. UC-3.3.16 remains reserved for DeploymentConfig rollout behavior. Splunk becomes the reconciliation narrative that ties structured Build snapshots, BuildConfig API audit context, Kubernetes Events with Build involvedObject.kind, optional openshift_build_total counters, and analyst-friendly severity tiers without pretending oc logs replacement for individual builder Pods.

Index and permission design land before parsers. Designate index=ocp_events for ocp_build structured events emitted by oc get builds -A -o json jobs or informers, ocp_buildconfig snapshots if you export BuildConfig objects separately, k8s_events forwarded from the API server with Build involved objects, and prometheus:metrics lines scraped from monitoring targets that expose build controller metrics. Designate index=ocp_audit for ocp_audit JSON or LEEF style records from the Kubernetes API audit log pipeline, filtered or enriched to highlight build.openshift.io groups. Issue distinct HEC tokens per environment with least privilege: platform engineering may search all sourcetypes, application teams receive filtered views by namespace allow lists, and security operations receives audit indexes under tighter ACLs. Retention should cover at least fourteen days hot for incident replay on retry storms, thirty days for monthly CI/CD governance reviews, and align cold storage with enterprise logging policy.

RBAC and safety: exporters must use dedicated ServiceAccounts with get list watch on builds.build.openshift.io and buildconfigs.build.openshift.io in scoped namespaces, not cluster-admin credentials on employee laptops. Run collectors from hardened management hosts or CI workers with short-lived kubeconfig files. Legal and privacy reviews should confirm repository URLs, branch names, and builder image references in messages are acceptable in Splunk; redact proprietary repository paths when counsel requires minimal disclosure.

Field normalization expectations: flatten metadata.namespace into namespace, metadata.name into build_name, metadata.labels openshift.io/build-config.name into bc_name, spec.strategy.type into strategy, status.phase into phase, status.reason into reason, status.message into msg, status.startTimestamp and status.completionTimestamp into parseable epoch seconds build_start_epoch and build_end_epoch, and cluster identity into cluster or openshift_cluster from management-cluster context. If you ingest raw JSON without KV extraction, add props.conf INDEXED_EXTRACTIONS=json and FIELDALIAS rules so downstream coalesce() ladders still resolve. For openshift_build_total metrics, map __name__, phase label, strategy label, and numeric counter into mn, phase_label, strategy_label, and mv.

Risk briefing: spec.failedBuildsHistoryLimit pruning can remove older Failed builds from etcd while Splunk still retains history—treat absent API rows as possible pruning, not proof of health. Cancelled builds often reflect user intent or redundant webhook deliveries and must not always page like FetchSourceFailed. JenkinsPipeline strategy builds may spend most wall time in external Jenkins; cluster-side phases can look idle while external systems work, so combine Splunk rows with Jenkins telemetry when strategy is JenkinsPipeline. S2I assemble failures may present as generic non-zero exits unless reason normalization maps log snippets into status.reason—keep raw message text for search.

Differentiation recap: OpenShift Build and BuildConfig orchestration with cluster builder and integrated registry push semantics, not vanilla Kubernetes Pod logs alone, not Docker cache ratio analytics, not CVE dashboards, and not runtime image pull backoff without Build context.

### Step 2 — Configure data collection

Stand up four complementary lanes Splunk multisearch can fuse: periodic Build API snapshots or watches, BuildConfig exports for history limit governance context, Kubernetes Events involving Build objects, and optional Prometheus counters from the build metric surfaces OpenShift exposes when enabled on your minor version.

Build snapshot lane: schedule a Python or Go utility every two to five minutes from a management host with kubeconfig authentication. The utility should run oc get builds -A -o json, iterate items[], and emit one HEC JSON event per Build with sourcetype=ocp_build, fields cluster, namespace, build_name, bc_name, strategy, phase, reason, msg, build_start_epoch, build_end_epoch, duration_seconds computed when both timestamps exist, generation, resourceVersion, and optional builder_pod name from status if present. Include a sha256 hash of the canonical JSON body without volatile resourceVersion when you need tamper-evident auditing. For high-volume namespaces, filter to production allow lists or sample canary namespaces during pilot phases.

BuildConfig snapshot lane: on a matching cadence run oc get buildconfigs -A -o json and emit sourcetype=ocp_buildconfig events with namespace, bc_name, failedBuildsHistoryLimit, successfulBuildsHistoryLimit, output_to_kind, output_to_name, strategy, and lastVersion if you flatten status.lastVersion. These rows help analysts interpret sudden failure rate spikes after teams tighten history limits and inadvertently truncate visible Kubernetes rows.

Kubernetes Events lane: forward events with sourcetype=k8s_events using the Splunk OpenShift App event collection patterns or an OpenTelemetry Collector k8s_events receiver. Preserve involvedObject.kind, involvedObject.name, involvedObject.namespace, reason, message, firstTimestamp, lastTimestamp, count, and cluster. Filter at the collector for involvedObject.kind=Build when volume requires, but retain BuildConfig events in a parallel input if you track FailedCreate on BuildConfig during admission incidents.

Audit lane: ship Kubernetes API audit logs into index=ocp_audit with sourcetype=ocp_audit. Ensure objectRef.resource resolves builds and buildconfigs, verb captures create update patch delete, user.username or audit annotations identify CI service accounts, and responseStatus.code captures forbidden or conflict failures. Truncate large requestObject bodies at the collector while retaining objectRef.name and namespace.

Prometheus lane: enable platform monitoring federation per OpenShift documentation, scrape series matching openshift_build_total or similarly named build counters when present on your version, and forward lines into index=ocp_events with sourcetype=prometheus:metrics using an OpenTelemetry Collector prometheus receiver. Preserve labels for phase and strategy when exporters provide them. If your cluster only exposes histograms or alternate names, widen regex in the SPL comment macro after validating oc get --raw against the metrics endpoint documentation for your minor version.

props.conf guidance: TRUNCATE sufficiently large for JSON, TIMESTAMP_FIELDS respected when HEC time is authoritative, LINE_BREAKER for NDJSON watch streams, and FIELDALIAS copying labels.buildconfig into bc_name when your forwarder flattens label maps differently.

Pre-flight searches operators should run before saving alerts:

index=ocp_events sourcetype=ocp_build earliest=-1h latest=now | head 20
index=ocp_events sourcetype=ocp_buildconfig earliest=-24h latest=now | head 20
index=ocp_events sourcetype=k8s_events involvedObject_kind=Build earliest=-24h latest=now | head 20
index=ocp_audit sourcetype=ocp_audit objectRef_resource=buildconfigs earliest=-24h latest=now | head 20
index=ocp_events sourcetype=prometheus:metrics openshift_build earliest=-24h latest=now | head 20

Zero-result investigations should block production paging until collectors succeed.

Implementation note: align exporter timestamps with NTP on management hosts; duration creep detection is sensitive to skew between builder start and completion times recorded by the API.

### Step 3 — Create the search and alert

Save the SPL as openshift_uc_3_3_7_buildconfig_failure_regression with a fifteen minute schedule, dispatch earliest=-24h@h, dispatch latest=now, and alert when severity is page or warn. Throttle duplicate cluster, namespace, bc_name rows for thirty minutes unless severity escalates from warn to page. Include recommended_action, fail_rate_24h, and median_duration_sec in pager descriptions so incident commanders open the correct runbook section without rerunning ad hoc searches.

Pipeline narrative for operators: multisearch fans Build snapshots, BuildConfig governance rows, Kubernetes Events on Build objects with bc_name derived from default OpenShift build naming patterns, and ocp_audit rows filtered to build.openshift.io resources so FailedCreate and forbidden responses surface beside controller reasons. A follow-on join adds openshift_build_total style counters summed by cluster when prometheus:metrics lines exist, so a silent metrics outage does not hide a genuine FetchSourceFailed surge. coalesce() ladders absorb field naming drift from alternate exporters. eventstats computes fleet percentile context for failure rates and durations by cluster. streamstats ordered by bc_name carries strategy multivalue context for dashboards. case() maps high failure rates, critical reason tokens, duration regression multiples, and admission style hints into page versus warn versus info tiers. recommended_action encodes concise verbs referencing oc describe build, oc logs build pod, registry secret rotation, Git server reachability checks, and BuildConfig trigger hygiene.

Fenced SPL must match the spl JSON field exactly:

```spl
`comment("UC-3.3.7 OpenShift BuildConfig and Build lifecycle reliability. Tunables: idx_events=ocp_events idx_audit=ocp_audit; earliest=-24h@h latest=now; fail_rate_page_pct=35 fail_rate_warn_pct=15; dur_ratio_warn=1.5 dur_ratio_page=2.5; prom_match=openshift_build")`
| multisearch
    [ search index=ocp_events sourcetype="ocp_build" earliest=-24h@h latest=now
      | eval cluster=lower(trim(toString(coalesce(cluster, openshift_cluster, cluster_name, cluster_id, ""))))
      | eval namespace=lower(trim(toString(coalesce(namespace, k8s_namespace, metadata_namespace, object_namespace, ""))))
      | eval build_name=lower(trim(toString(coalesce(build_name, name, metadata_name, object_name, ""))))
      | eval bc_name=lower(trim(toString(coalesce(bc_name, build_config, openshift_build_config_name, labels_openshift_io_build_config_name, label_buildconfig, ""))))
      | eval strategy=lower(trim(toString(coalesce(strategy, spec_strategy_type, build_strategy, type_strategy, ""))))
      | eval phase=lower(trim(toString(coalesce(phase, status_phase, status_phase_lower, ""))))
      | eval reason=trim(toString(coalesce(reason, status_reason, failure_reason, "")))
      | eval msg=trim(toString(coalesce(msg, status_message, message, log_message, "")))
      | eval start_epoch=tonumber(tostring(coalesce(build_start_epoch, start_epoch, start_ts_epoch, "")),10)
      | eval end_epoch=tonumber(tostring(coalesce(build_end_epoch, completion_epoch, end_ts_epoch, "")),10)
      | eval duration_seconds=tonumber(tostring(coalesce(duration_seconds, build_duration_sec, dur_sec, "")),10)
      | eval duration_seconds=if(isnull(duration_seconds) AND isnotnull(start_epoch) AND isnotnull(end_epoch) AND end_epoch>start_epoch, end_epoch - start_epoch, duration_seconds)
      | eval is_fail=if(match(phase,"failed|error") OR match(lower(reason),"failed|error|fetch|push|hook|builder"),1,0)
      | eval lane="build_snapshot"
      | fields _time cluster namespace build_name bc_name strategy phase reason msg duration_seconds is_fail lane ]
    [ search index=ocp_events sourcetype="ocp_buildconfig" earliest=-24h@h latest=now
      | eval cluster=lower(trim(toString(coalesce(cluster, openshift_cluster, cluster_name, cluster_id, ""))))
      | eval namespace=lower(trim(toString(coalesce(namespace, k8s_namespace, metadata_namespace, ""))))
      | eval bc_name=lower(trim(toString(coalesce(bc_name, name, metadata_name, buildconfig_name, ""))))
      | eval failed_hist=tonumber(tostring(coalesce(failedBuildsHistoryLimit, failed_builds_history_limit, "")),10)
      | eval success_hist=tonumber(tostring(coalesce(successfulBuildsHistoryLimit, successful_builds_history_limit, "")),10)
      | eval lane="bc_snapshot"
      | fields _time cluster namespace bc_name failed_hist success_hist lane ]
    [ search index=ocp_events (sourcetype="k8s_events" OR sourcetype="ocp_events") earliest=-24h@h latest=now
      | eval cluster=lower(trim(toString(coalesce(cluster, openshift_cluster, cluster_name, cluster_id, ""))))
      | eval kind=lower(trim(toString(coalesce(involvedObject_kind, involved_kind, object_kind, ""))))
      | where kind="build"
      | eval namespace=lower(trim(toString(coalesce(involvedObject_namespace, involved_namespace, object_namespace, namespace, ""))))
      | eval build_name=lower(trim(toString(coalesce(involvedObject_name, involved_name, object_name, ""))))
      | rex field=build_name "(?<bc_derived>.*)-(?<build_seq>[0-9]+)$"
      | eval bc_name=lower(trim(coalesce(bc_derived, build_name)))
      | eval evt_reason=trim(toString(coalesce(reason, Reason, event_reason, "")))
      | eval evt_msg=trim(toString(coalesce(message, Message, event_message, "")))
      | eval lane="build_event"
      | stats latest(_time) AS last_evt_time latest(evt_reason) AS evt_reason latest(evt_msg) AS evt_msg BY cluster namespace bc_name lane ]
    [ search index=ocp_audit sourcetype="ocp_audit" earliest=-24h@h latest=now
      | eval cluster=lower(trim(toString(coalesce(cluster, openshift_cluster, cluster_name, cluster_id, ""))))
      | eval res=lower(trim(toString(coalesce(objectRef_resource, objectRef_kind, resource, ""))))
      | where res="buildconfigs" OR res="builds" OR match(res,"build")
      | eval namespace=lower(trim(toString(coalesce(objectRef_namespace, object_namespace, namespace, ""))))
      | eval obj_name=lower(trim(toString(coalesce(objectRef_name, object_name, metadata_name, ""))))
      | eval bc_name=if(res=="buildconfigs", obj_name, null())
      | rex field=obj_name "(?<bc_from_build>.*)-(?<build_digits>[0-9]+)$"
      | eval bc_name=lower(trim(coalesce(bc_name, bc_from_build, obj_name)))
      | eval audit_msg=trim(toString(coalesce(responseStatus_message, responseReason, message, msg, "")))
      | eval audit_code=tonumber(tostring(coalesce(responseStatus_code, status_code, http_status, "")),10)
      | eval lane="audit_lane"
      | stats latest(_time) AS last_audit_time latest(audit_msg) AS audit_msg max(audit_code) AS audit_code BY cluster namespace bc_name lane ]
| stats
    sum(eval(if(lane="build_snapshot",1,0))) AS build_obs
    sum(eval(if(lane="build_snapshot",is_fail,0))) AS fail_obs
    median(eval(if(lane="build_snapshot",duration_seconds,null()))) AS median_duration_sec
    perc90(eval(if(lane="build_snapshot",duration_seconds,null()))) AS p90_duration_sec
    latest(eval(if(lane="build_snapshot",reason,null()))) AS last_reason
    latest(eval(if(lane="build_snapshot",msg,null()))) AS last_msg
    values(eval(if(lane="build_snapshot",strategy,null()))) AS strategies_seen
    max(eval(if(lane="build_event",last_evt_time,null()))) AS last_evt_time
    max(eval(if(lane="build_event",evt_reason,null()))) AS evt_reason
    max(eval(if(lane="build_event",evt_msg,null()))) AS evt_msg
    max(eval(if(lane="bc_snapshot",failed_hist,null()))) AS failed_hist
    max(eval(if(lane="bc_snapshot",success_hist,null()))) AS success_hist
    max(eval(if(lane="audit_lane",last_audit_time,null()))) AS last_audit_time
    max(eval(if(lane="audit_lane",audit_msg,null()))) AS audit_msg
    max(eval(if(lane="audit_lane",audit_code,null()))) AS audit_code
  BY cluster namespace bc_name
| join type=left max=0 cluster
    [ search index=ocp_events sourcetype="prometheus:metrics" earliest=-24h@h latest=now
      | eval cluster=lower(trim(toString(coalesce(cluster, openshift_cluster, cluster_name, k8s_cluster_name, ""))))
      | eval mn=lower(trim(toString(coalesce(__name__, metric_name, name, ""))))
      | where match(mn,"openshift_build")
      | eval mv=tonumber(tostring(coalesce(value, metric_value, Value, "")),10)
      | stats sum(mv) AS prom_build_counter BY cluster ]
| eventstats sum(build_obs) AS cluster_build_obs sum(fail_obs) AS cluster_fail_obs BY cluster
| eval cluster_fail_rate=if(cluster_build_obs>0, round(100.0*cluster_fail_obs/cluster_build_obs,2), null())
| sort cluster namespace bc_name
| streamstats window=20000 current=t global=f values(strategies_seen) AS strat_mv BY cluster namespace bc_name
| eval strategy=mvindex(strat_mv,0)
| eval fail_rate=if(build_obs>0, round(100.0*fail_obs/build_obs,2), 0.0)
| eventstats median(median_duration_sec) AS cluster_med_dur BY cluster
| eval dur_ratio=if(isnotnull(cluster_med_dur) AND cluster_med_dur>0 AND isnotnull(median_duration_sec), round(median_duration_sec/cluster_med_dur,3), null())
| eval critical_reason=if(match(lower(last_reason),"fetchsourcefailed|pushimagetoregistryfailed|failedretrievebuilder|postcommithookfailed"),1,0)
| eval admission_hint=if(
    match(lower(evt_msg),"failedcreate|failedsync|denied|forbidden|quota") OR match(lower(evt_reason),"failedcreate|failedsync") OR match(lower(audit_msg),"forbidden|denied|quota|failedcreate|failedsync") OR (isnotnull(audit_code) AND audit_code>=400),
    1, 0)
| eval severity=case(
    fail_rate>=35 OR (fail_obs>=5 AND critical_reason==1), "page",
    fail_rate>=15 OR critical_reason==1 OR admission_hint==1, "warn",
    isnotnull(dur_ratio) AND dur_ratio>=2.5 AND fail_rate>=5, "warn",
    isnotnull(dur_ratio) AND dur_ratio>=1.5 AND fail_rate>=10, "warn",
    true(), "info")
| eval recommended_action=case(
    match(lower(last_reason),"fetchsourcefailed"), "validate_git_connectivity_credentials_and_webhook_secret",
    match(lower(last_reason),"pushimagetoregistryfailed"), "check_integrated_registry_routes_pullsecret_and_storage",
    match(lower(last_reason),"failedretrievebuilder"), "verify_builder_image_policy_and_imagestream_tags",
    match(lower(last_reason),"postcommithookfailed"), "inspect_postcommit_command_and_unit_test_logs",
    admission_hint==1, "review_buildconfig_admission_quota_and_scc_events",
    fail_rate>=15 AND fail_rate<35, "triage_repeat_failures_per_bc_and_compare_triggers",
    true(), "correlate_builder_pod_logs_and_events")
| join type=left max=0 cluster
    [| inputlookup openshift_cluster_inventory.csv
     | fields cluster, cluster_tier, owner_team, environment]
| eval cluster_tier=coalesce(cluster_tier, "unrated"),
       owner_team=coalesce(owner_team, "unowned"),
       environment=coalesce(environment, "unknown")
| table cluster namespace bc_name build_obs fail_obs fail_rate cluster_fail_rate median_duration_sec p90_duration_sec dur_ratio last_reason evt_reason last_audit_time audit_code prom_build_counter severity recommended_action failed_hist success_hist last_msg cluster_tier owner_team environment
```

savedsearches.conf sketch for CI and platform paging:

```ini
[openshift_uc_3_3_7_buildconfig_failure_regression_alert]
cron_schedule = */15 * * * *
dispatch.earliest_time = -24h@h
dispatch.latest_time = now
enableSched = 1
action.email = 1
action.email.to = openshift-build-ci@example.com
action.email.subject = OCP BuildConfig reliability $result.severity$ $result.cluster$ $result.namespace$/$result.bc_name$
counttype = number of events
relation = greater than
quantity = 0
search = | savedsearch openshift_uc_3_3_7_buildconfig_failure_regression | where severity IN ("page","warn")
```

Performance: if Job Inspector shows multisearch queue time above internal SLA, materialize hourly ocp_build summaries keyed on cluster, namespace, and bc_name into a summary index, widen alert searches to earliest=-6h@h on the summary, and retain this full search for investigations.

### Step 4 — Validate

Ground truth always starts on-cluster. Run oc get builds -A -o wide and compare namespace, name, phase, and age columns to Splunk rows for the same cluster inside the last snapshot window. When phases disagree, first verify resourceVersion freshness and indexer clock skew before blaming Splunk parsing.

Deep dive with oc describe build <name> -n <namespace> to read events, reason, message, builder pod name, and duration hints. Splunk should mirror Failed or Error phases within one collection interval; if not, tighten scripted input frequency or fix token expiration on the management host.

BuildConfig truth: run oc describe buildconfig <name> -n <namespace> to read failedBuildsHistoryLimit, successfulBuildsHistoryLimit, triggers, output target ImageStream, and strategy details. Confirm Splunk ocp_buildconfig rows carry the same limits after GitOps updates.

Kubernetes Events cross-check: oc get events -n <namespace> --field-selector involvedObject.kind=Build should show BuildFailed, BuildStarted, or BuildCancelled reasons that map to k8s_events rows.

Audit cross-check: sample ocp_audit rows during a controlled oc start-build and confirm user.username matches the CI service account, objectRef.resource equals builds, and verbs are create or update as expected.

Prometheus cross-check: when openshift_build_total lines exist in ocp_events, compare summed counters by phase_label to coarse counts from ocp_build snapshots for the same interval; mismatches often indicate label cardinality drops or scrape gaps rather than benign CI health.

Synthetic validation: in a lab namespace, introduce a BuildConfig that points at an invalid Git reference to force FetchSourceFailed, ingest telemetry, and confirm openshift_uc_3_3_7_buildconfig_failure_regression surfaces warn or page with the expected recommended_action. Roll back the BuildConfig, watch builds return to Complete, and confirm severity returns to info. Negative test: cancel a running build with oc cancel-build and confirm Cancelled phases do not page when fail_rate thresholds treat cancellation separately from fetch failures.

### Step 5 — Operationalize & Troubleshoot

Publish a dashboard with one row per cluster, namespace, and BuildConfig using the closing table columns, color severity with UI thresholds where page is red, warn is amber, and info is blue, and add drilldowns to raw ocp_build JSON, ocp_buildconfig JSON, k8s_events text, ocp_audit excerpts, and prometheus metric lines. Archive weekly CSV exports of the alert table to a restricted evidence index with the git commit hash of your exporter manifests for pipeline governance packs.

Wire alert actions to platform on-call, optional Splunk ITSI episodes keyed on cluster and bc_name entities, and ticketing systems with recommended_action, fail_rate, and direct links to internal runbooks covering Git credential rotation, registry storage exhaustion, S2I builder image bumps, JenkinsPipeline plugin drift, and resource quota planning.

Case 1 — FetchSourceFailed after Git maintenance: validate corporate Git load balancers, compare repository allow lists on the builder network path, rotate source secrets bound to BuildConfig spec.source, and replay oc start-build after fixing DNS or firewall drift.

Case 2 — PushImageToRegistryFailed during cold CI mornings: inspect integrated registry PVC or object storage saturation, review image-pruner jobs, validate namespace imagestreams, and confirm routes and TLS secrets for the internal registry still match builder trust bundles.

Case 3 — FailedRetrieveBuilder after cluster image policy updates: compare builder image ImageStream tags with policy exceptions, verify ImageContentSourcePolicy mirrors for air-gapped registries, and unblock pulls only after security review when scanners gate new digests.

Case 4 — PostCommitHookFailed after test dependency upgrades: open builder pod logs for the postCommit container, align hook commands with language toolchain versions, and treat repeated hook failures as merge-blocking even when assemble succeeded.

Case 5 — JenkinsPipeline strategy idle cluster phases with external failures: correlate OpenShift Build rows with Jenkins stage logs and controller connectivity, then fix agent labels or credential bindings rather than restarting cluster operators first.

Case 6 — Admission FailedCreate on BuildConfig after quota tightening: raise namespace ResourceQuota limits under change control or move builds to dedicated CI namespaces instrumented with the same Splunk panels.

Case 7 — Cancelled builds from duplicate webhooks: deduplicate GitHub or GitLab webhook configurations, introduce short-lived trigger secrets, and tune alert logic to emphasize fail_rate on terminal Failed rather than transient Cancelled noise.

Case 8 — History limit pruning masks etcd-visible failures: lower failedBuildsHistoryLimit only with Splunk retention compensating governance reviews, and document that API object lists may look cleaner while Splunk still shows regressions.

Case 9 — Duration creep without reason changes: compare median_duration_sec to p90_duration_sec, inspect node CPU pressure on build nodes, and evaluate PVC performance for layered Docker strategy builds.

Case 10 — Prometheus openshift_build_total scrape gaps: confirm ServiceMonitor or platform monitoring targets for build metrics, validate DNS from scraper to target, and fall back to ocp_build snapshots for severity until metrics return.

Case 11 — Air-gapped mirror lag causing intermittent FetchSourceFailed: align mirror sync schedules with developer working hours and add maintenance windows annotations to suppress paging when mirrors intentionally pause.

Case 12 — Healthy control test with low fail_rate and stable dur_ratio: use as quarterly evidence that telemetry, tokens, and parsers remain aligned with oc get builds across production clusters.

## SPL

```spl
`comment("UC-3.3.7 OpenShift BuildConfig and Build lifecycle reliability. Tunables: idx_events=ocp_events idx_audit=ocp_audit; earliest=-24h@h latest=now; fail_rate_page_pct=35 fail_rate_warn_pct=15; dur_ratio_warn=1.5 dur_ratio_page=2.5; prom_match=openshift_build")`
| multisearch
    [ search index=ocp_events sourcetype="ocp_build" earliest=-24h@h latest=now
      | eval cluster=lower(trim(toString(coalesce(cluster, openshift_cluster, cluster_name, cluster_id, ""))))
      | eval namespace=lower(trim(toString(coalesce(namespace, k8s_namespace, metadata_namespace, object_namespace, ""))))
      | eval build_name=lower(trim(toString(coalesce(build_name, name, metadata_name, object_name, ""))))
      | eval bc_name=lower(trim(toString(coalesce(bc_name, build_config, openshift_build_config_name, labels_openshift_io_build_config_name, label_buildconfig, ""))))
      | eval strategy=lower(trim(toString(coalesce(strategy, spec_strategy_type, build_strategy, type_strategy, ""))))
      | eval phase=lower(trim(toString(coalesce(phase, status_phase, status_phase_lower, ""))))
      | eval reason=trim(toString(coalesce(reason, status_reason, failure_reason, "")))
      | eval msg=trim(toString(coalesce(msg, status_message, message, log_message, "")))
      | eval start_epoch=tonumber(tostring(coalesce(build_start_epoch, start_epoch, start_ts_epoch, "")),10)
      | eval end_epoch=tonumber(tostring(coalesce(build_end_epoch, completion_epoch, end_ts_epoch, "")),10)
      | eval duration_seconds=tonumber(tostring(coalesce(duration_seconds, build_duration_sec, dur_sec, "")),10)
      | eval duration_seconds=if(isnull(duration_seconds) AND isnotnull(start_epoch) AND isnotnull(end_epoch) AND end_epoch>start_epoch, end_epoch - start_epoch, duration_seconds)
      | eval is_fail=if(match(phase,"failed|error") OR match(lower(reason),"failed|error|fetch|push|hook|builder"),1,0)
      | eval lane="build_snapshot"
      | fields _time cluster namespace build_name bc_name strategy phase reason msg duration_seconds is_fail lane ]
    [ search index=ocp_events sourcetype="ocp_buildconfig" earliest=-24h@h latest=now
      | eval cluster=lower(trim(toString(coalesce(cluster, openshift_cluster, cluster_name, cluster_id, ""))))
      | eval namespace=lower(trim(toString(coalesce(namespace, k8s_namespace, metadata_namespace, ""))))
      | eval bc_name=lower(trim(toString(coalesce(bc_name, name, metadata_name, buildconfig_name, ""))))
      | eval failed_hist=tonumber(tostring(coalesce(failedBuildsHistoryLimit, failed_builds_history_limit, "")),10)
      | eval success_hist=tonumber(tostring(coalesce(successfulBuildsHistoryLimit, successful_builds_history_limit, "")),10)
      | eval lane="bc_snapshot"
      | fields _time cluster namespace bc_name failed_hist success_hist lane ]
    [ search index=ocp_events (sourcetype="k8s_events" OR sourcetype="ocp_events") earliest=-24h@h latest=now
      | eval cluster=lower(trim(toString(coalesce(cluster, openshift_cluster, cluster_name, cluster_id, ""))))
      | eval kind=lower(trim(toString(coalesce(involvedObject_kind, involved_kind, object_kind, ""))))
      | where kind="build"
      | eval namespace=lower(trim(toString(coalesce(involvedObject_namespace, involved_namespace, object_namespace, namespace, ""))))
      | eval build_name=lower(trim(toString(coalesce(involvedObject_name, involved_name, object_name, ""))))
      | rex field=build_name "(?<bc_derived>.*)-(?<build_seq>[0-9]+)$"
      | eval bc_name=lower(trim(coalesce(bc_derived, build_name)))
      | eval evt_reason=trim(toString(coalesce(reason, Reason, event_reason, "")))
      | eval evt_msg=trim(toString(coalesce(message, Message, event_message, "")))
      | eval lane="build_event"
      | stats latest(_time) AS last_evt_time latest(evt_reason) AS evt_reason latest(evt_msg) AS evt_msg BY cluster namespace bc_name lane ]
    [ search index=ocp_audit sourcetype="ocp_audit" earliest=-24h@h latest=now
      | eval cluster=lower(trim(toString(coalesce(cluster, openshift_cluster, cluster_name, cluster_id, ""))))
      | eval res=lower(trim(toString(coalesce(objectRef_resource, objectRef_kind, resource, ""))))
      | where res="buildconfigs" OR res="builds" OR match(res,"build")
      | eval namespace=lower(trim(toString(coalesce(objectRef_namespace, object_namespace, namespace, ""))))
      | eval obj_name=lower(trim(toString(coalesce(objectRef_name, object_name, metadata_name, ""))))
      | eval bc_name=if(res=="buildconfigs", obj_name, null())
      | rex field=obj_name "(?<bc_from_build>.*)-(?<build_digits>[0-9]+)$"
      | eval bc_name=lower(trim(coalesce(bc_name, bc_from_build, obj_name)))
      | eval audit_msg=trim(toString(coalesce(responseStatus_message, responseReason, message, msg, "")))
      | eval audit_code=tonumber(tostring(coalesce(responseStatus_code, status_code, http_status, "")),10)
      | eval lane="audit_lane"
      | stats latest(_time) AS last_audit_time latest(audit_msg) AS audit_msg max(audit_code) AS audit_code BY cluster namespace bc_name lane ]
| stats
    sum(eval(if(lane="build_snapshot",1,0))) AS build_obs
    sum(eval(if(lane="build_snapshot",is_fail,0))) AS fail_obs
    median(eval(if(lane="build_snapshot",duration_seconds,null()))) AS median_duration_sec
    perc90(eval(if(lane="build_snapshot",duration_seconds,null()))) AS p90_duration_sec
    latest(eval(if(lane="build_snapshot",reason,null()))) AS last_reason
    latest(eval(if(lane="build_snapshot",msg,null()))) AS last_msg
    values(eval(if(lane="build_snapshot",strategy,null()))) AS strategies_seen
    max(eval(if(lane="build_event",last_evt_time,null()))) AS last_evt_time
    max(eval(if(lane="build_event",evt_reason,null()))) AS evt_reason
    max(eval(if(lane="build_event",evt_msg,null()))) AS evt_msg
    max(eval(if(lane="bc_snapshot",failed_hist,null()))) AS failed_hist
    max(eval(if(lane="bc_snapshot",success_hist,null()))) AS success_hist
    max(eval(if(lane="audit_lane",last_audit_time,null()))) AS last_audit_time
    max(eval(if(lane="audit_lane",audit_msg,null()))) AS audit_msg
    max(eval(if(lane="audit_lane",audit_code,null()))) AS audit_code
  BY cluster namespace bc_name
| join type=left max=0 cluster
    [ search index=ocp_events sourcetype="prometheus:metrics" earliest=-24h@h latest=now
      | eval cluster=lower(trim(toString(coalesce(cluster, openshift_cluster, cluster_name, k8s_cluster_name, ""))))
      | eval mn=lower(trim(toString(coalesce(__name__, metric_name, name, ""))))
      | where match(mn,"openshift_build")
      | eval mv=tonumber(tostring(coalesce(value, metric_value, Value, "")),10)
      | stats sum(mv) AS prom_build_counter BY cluster ]
| eventstats sum(build_obs) AS cluster_build_obs sum(fail_obs) AS cluster_fail_obs BY cluster
| eval cluster_fail_rate=if(cluster_build_obs>0, round(100.0*cluster_fail_obs/cluster_build_obs,2), null())
| sort cluster namespace bc_name
| streamstats window=20000 current=t global=f values(strategies_seen) AS strat_mv BY cluster namespace bc_name
| eval strategy=mvindex(strat_mv,0)
| eval fail_rate=if(build_obs>0, round(100.0*fail_obs/build_obs,2), 0.0)
| eventstats median(median_duration_sec) AS cluster_med_dur BY cluster
| eval dur_ratio=if(isnotnull(cluster_med_dur) AND cluster_med_dur>0 AND isnotnull(median_duration_sec), round(median_duration_sec/cluster_med_dur,3), null())
| eval critical_reason=if(match(lower(last_reason),"fetchsourcefailed|pushimagetoregistryfailed|failedretrievebuilder|postcommithookfailed"),1,0)
| eval admission_hint=if(
    match(lower(evt_msg),"failedcreate|failedsync|denied|forbidden|quota") OR match(lower(evt_reason),"failedcreate|failedsync") OR match(lower(audit_msg),"forbidden|denied|quota|failedcreate|failedsync") OR (isnotnull(audit_code) AND audit_code>=400),
    1, 0)
| eval severity=case(
    fail_rate>=35 OR (fail_obs>=5 AND critical_reason==1), "page",
    fail_rate>=15 OR critical_reason==1 OR admission_hint==1, "warn",
    isnotnull(dur_ratio) AND dur_ratio>=2.5 AND fail_rate>=5, "warn",
    isnotnull(dur_ratio) AND dur_ratio>=1.5 AND fail_rate>=10, "warn",
    true(), "info")
| eval recommended_action=case(
    match(lower(last_reason),"fetchsourcefailed"), "validate_git_connectivity_credentials_and_webhook_secret",
    match(lower(last_reason),"pushimagetoregistryfailed"), "check_integrated_registry_routes_pullsecret_and_storage",
    match(lower(last_reason),"failedretrievebuilder"), "verify_builder_image_policy_and_imagestream_tags",
    match(lower(last_reason),"postcommithookfailed"), "inspect_postcommit_command_and_unit_test_logs",
    admission_hint==1, "review_buildconfig_admission_quota_and_scc_events",
    fail_rate>=15 AND fail_rate<35, "triage_repeat_failures_per_bc_and_compare_triggers",
    true(), "correlate_builder_pod_logs_and_events")
| join type=left max=0 cluster
    [| inputlookup openshift_cluster_inventory.csv
     | fields cluster, cluster_tier, owner_team, environment]
| eval cluster_tier=coalesce(cluster_tier, "unrated"),
       owner_team=coalesce(owner_team, "unowned"),
       environment=coalesce(environment, "unknown")
| table cluster namespace bc_name build_obs fail_obs fail_rate cluster_fail_rate median_duration_sec p90_duration_sec dur_ratio last_reason evt_reason last_audit_time audit_code prom_build_counter severity recommended_action failed_hist success_hist last_msg cluster_tier owner_team environment
```

## CIM SPL

```spl
| tstats summariesonly=t latest(Change.action) AS change_action latest(Change.object) AS change_object latest(Change.user) AS change_user FROM datamodel=Change WHERE nodename=Change earliest=-24h@h latest=now BY Change.dest
| rename Change.dest AS cim_dest
| join type=left max=0 cim_dest
    [| tstats summariesonly=t latest(Application_State.state) AS app_state latest(Application_State.info) AS app_info FROM datamodel=Application_State WHERE nodename=Application_State earliest=-24h@h latest=now BY Application_State.dest
     | rename Application_State.dest AS cim_dest ]
| where like(lower(change_object), "%build%") OR like(lower(app_info), "%build%")
| table cim_dest change_action change_object change_user app_state app_info
```

## Visualization

Severity-colored table by cluster, namespace, and bc_name with drilldowns to ocp_build JSON, ocp_buildconfig JSON, k8s_events, ocp_audit excerpts, and prometheus metric lines; timechart of fail_rate and cluster_fail_rate; timeline of median_duration_sec versus p90_duration_sec; single-value tiles for page severity counts.

## Known False Positives

Developers routinely push intentionally broken commits to feature branches that drive short-lived Failed builds; scope production paging to namespaces tied to protected branches or add lookup-driven branch tiering before interpreting fail_rate. S2I builder ImageStream tags can churn during vendor patch weeks when maintainers merge refreshed builder images; expect clustered FailedRetrieveBuilder rows that clear after mirrors sync rather than signaling misconfiguration. Corporate registry rate limits during cold CI mornings can manifest as PushImageToRegistryFailed bursts that self-resolve when traffic spreads; corroborate with registry dashboards before executive escalation. JenkinsPipeline strategy builds may fail entirely inside external Jenkins while OpenShift Build phases remain Pending; pairing this control with Jenkins telemetry avoids false reassurance from quiet cluster rows. Transient FetchSourceFailed events during planned Git server reboots resemble incidents until maintenance calendars annotate the window; suppress or downgrade severity using scheduled maintenance metadata on HEC events. User-initiated oc cancel-build and duplicate webhook deliveries inflate Cancelled counts that should not be treated like fetch failures unless your governance treats cancels as SLA breaches. Admission controllers that temporarily deny creates during etcd compaction can emit FailedCreate hints without sustained build faults; require repeated admission_hint rows across intervals. Prometheus openshift_build_total series rename between minor OpenShift releases can null prom_counter joins for one scrape rotation; rely on ocp_build snapshots when metrics cardinality shifts. Pruned Build history from aggressive failedBuildsHistoryLimit values reduces visible Kubernetes rows while Splunk still shows historical failure spikes; teach reviewers that API cleanliness differs from log retention. Penetration-test namespaces that continuously break compiles will page unless marked non-production in a lookup table. Webhook secret rotation without Git-side updates causes authentication failures that look like source fetch faults until credentials align on both sides.

## References

- [OpenShift Documentation — Understanding image builds](https://docs.openshift.com/container-platform/latest/cicd/builds/understanding-image-builds.html)
- [OpenShift Documentation — Understanding build configurations](https://docs.openshift.com/container-platform/latest/cicd/builds/understanding-buildconfigs.html)
- [OpenShift Documentation — Managing build output](https://docs.openshift.com/container-platform/latest/cicd/builds/managing-build-output.html)
- [OpenShift REST API Reference — Build [build.openshift.io/v1]](https://docs.openshift.com/container-platform/latest/rest_api/build_apis/build-build-openshift-io-v1.html)
- [OpenShift Documentation — Performing basic builds](https://docs.openshift.com/container-platform/latest/cicd/builds/basic-build-operations.html)
- [OpenShift Documentation — Build strategies](https://docs.openshift.com/container-platform/latest/cicd/builds/build-strategies.html)
- [Red Hat Developer — Source-to-Image (S2I) toolkit for creating images](https://developers.redhat.com/blog/2019/09/24/new-features-s2i-red-hat-openshift-4)
