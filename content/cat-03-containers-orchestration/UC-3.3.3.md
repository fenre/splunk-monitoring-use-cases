<!-- AUTO-GENERATED from UC-3.3.3.json — DO NOT EDIT -->

---
id: "3.3.3"
title: "OpenShift Pipelines (Tekton) PipelineRun and TaskRun Reliability: EventListener Delivery, Chains Signing, and Resolver Drift"
status: "verified"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-3.3.3 · OpenShift Pipelines (Tekton) PipelineRun and TaskRun Reliability: EventListener Delivery, Chains Signing, and Resolver Drift

> **Criticality:** Medium &middot; **Difficulty:** Advanced &middot; **Pillar:** Observability &middot; **Type:** Reliability, Availability &middot; **Wave:** Walk &middot; **Status:** Verified

*We watch the automated release assembly line inside OpenShift that runs each step of building and testing software. When webhooks, signing, or individual steps start failing often, we raise a clear signal so teams fix the pipeline before customer releases slow down.*

---

## Description

Correlates OpenShift Pipelines Tekton controller signals across PipelineRun terminal conditions and duration percentiles, TaskRun step failures, EventListener webhook error ratios versus PipelineRun creation hints, Tekton Chains signing and attestation outcomes, and resolver failure tokens spanning cluster git hub and bundle resolution so teams catch CI/CD plane drift before BuildConfig analytics or ImageStream import controls.

## Value

Reliable Tekton CI/CD on OpenShift: pipelines, webhooks, and signing you can trust before release night.

## Implementation

Land ocp_pipelinerun, ocp_taskrun, EventListener access logs, Tekton Chains or controller logs, optional k8s_events, and expected_pipelines.csv lookup into Splunk with cluster labels; normalize Tekton fields in props; save openshift_uc_3_3_3_tekton_pipelines_reliability every fifteen minutes over earliest=-24h@h; route page and warn to platform and CI owners; archive weekly CSV exports with exporter commit hashes.

## Evidence

Saved search openshift_uc_3_3_3_tekton_pipelines_reliability with fifteen minute schedule; Splunk OpenShift App dashboard drilldowns on ocp_pipelinerun, ocp_taskrun, EventListener access logs, chains controller logs, and expected_pipelines.csv join context; alert routing to platform and CI owners; weekly CSV exports archived to a restricted evidence index.

## Control test

### Positive scenario

In a lab OpenShift project, ingest ocp_pipelinerun rows showing Succeeded False with reason ResolutionFailed after a controlled invalid task reference, add matching ocp_tekton_chains or resolver log lines, execute openshift_uc_3_3_3_tekton_pipelines_reliability, and expect warn or page severity with non-null recommended_action within fifteen minutes.

### Negative scenario

After recovery when oc get pipelinerun shows Succeeded True, TaskRun steps show clean exits, webhook error percentages fall below warn thresholds, and Chains annotations appear when policy expects them, confirm severities return to info and the alert wrapper emits zero rows when filtering to page and warn only.

## Detailed Implementation

### Step 1 — Prerequisites

Head of Platform owns this control with the OpenShift platform engineering lead who stewards the OpenShift Pipelines operator in openshift-operators, the developer experience sponsor accountable for continuous integration and continuous delivery service levels, and the observability engineers who operate Splunk HTTP Event Collector tokens plus collectors that export Tekton custom resource state, controller logs, and ingress access lines for EventListener routes. This use case isolates the OpenShift Pipelines product plane built from Tekton Pipelines, Tekton Triggers, Tekton Chains, and the resolver family that ships with the operator, including PipelineRun and TaskRun objects in tekton.dev, TriggerBinding and TriggerTemplate rendering, EventListener Deployments commonly named with an el- prefix, and the chains.tekton.dev signing annotations that should appear after successful attestations when policy demands supply-chain evidence.

Scope boundaries are explicit so reviewers do not confuse planes. UC-3.3.7 remains build.openshift.io Build and BuildConfig orchestration with cluster builder semantics and integrated registry push outcomes. UC-3.3.13 remains image.openshift.io ImageStream import health and image-registry operator storage narratives. UC-3.3.11 remains operators.coreos.com Subscription, InstallPlan, and ClusterServiceVersion health for marketplace operators, including the openshift-pipelines-operator subscription row but not the detailed Tekton reconcile story inside the operand namespaces. UC-3.3.6 remains config.openshift.io ClusterOperator fleet dashboards without becoming the primary home for PipelineRun condition analytics. UC-3.2.14 remains kubelet ImagePullBackOff on unrelated workload Pods when no TaskRun reason ties the symptom to Tekton steps. Splunk becomes the reconciliation ledger that joins structured PipelineRun exports, TaskRun step exit telemetry, EventListener access error rates, Tekton Chains controller messages, and resolver failure tokens so platform teams detect trigger delivery drift and pipeline-plane regressions before release managers discover them through manual oc describe loops.

RBAC and safety: exporters that run oc get pipelinerun, oc get taskrun, oc get eventlistener, or watches on tekton.dev must use dedicated ServiceAccounts with get list watch scoped to CI namespaces plus openshift-pipelines or your configured targetNamespace, not personal cluster-admin kubeconfig files on laptops. Collectors that scrape openshift-operators for Subscription and ClusterServiceVersion health should remain read-only and must not mutate InstallPlan approvals from Splunk automation. Legal and privacy reviews should confirm repository URLs, branch names, and pull request identifiers in messages are acceptable in the analytics tier; redact proprietary repository paths when counsel requires minimal disclosure.

Index design: designate index=ocp_events for sourcetype=ocp_pipelinerun, sourcetype=ocp_taskrun, sourcetype=ocp_tekton_el_access or sourcetype=access_combined lines stamped with cluster labels, sourcetype=ocp_tekton_chains or kube:container lines filtered to tekton-chains-controller and resolver workloads, and sourcetype=k8s_events for involvedObject kinds PipelineRun and TaskRun when volume allows. Designate index=ocp_audit for ocp_audit records on tekton.dev creates and patches when you need tamper-evident attribution for GitOps controllers. Designate index=ocp_metrics for prometheus:metrics lines federated from openshift-pipelines and openshift-user-facing workloads when your monitoring platform scrapes controller queues. Retention should cover at least fourteen days hot for incident replay on webhook storms, thirty days for monthly pipeline governance reviews, and cold storage aligned to enterprise logging policy.

Field normalization expectations: flatten PipelineRun metadata.namespace into namespace, metadata.name into pr_name, status.conditions where type Succeeded into condition_succeeded with reason and message, status.startTime and status.completionTime into parseable epoch fields startTime_epoch and completionTime_epoch, spec.pipelineRef.name into pipeline_name or labels tekton.dev/pipeline when present, and spec.timeouts nested fields into timeout_pipeline_sec timeout_tasks_sec timeout_finally_sec when exporters flatten JSON. For TaskRun rows, map status.steps[].terminated.exitCode into nonzero_step_exit or max_exit_code across steps, map status.conditions Succeeded into condition_succeeded, and map labels tekton.dev/pipelineRun into parent references when pipeline names are implied. For EventListener ingress, map HTTP status into status, map request path into uri_path, and map namespace hosting the EventListener Service into el_namespace when collectors read Route objects. For Chains and resolver diagnostics, preserve controller log lines without storing private signing keys.

Risk briefing: intentional PipelineRun cancellations during canary drills resemble failures until you read reason PipelineRunCancelled. Unknown phases often appear while controllers reconcile large fan-out pipelines; pair dwell thresholds with repeated snapshots rather than paging on the first Unknown row. Git resolver failures spike during corporate Git maintenance; join maintenance metadata before executive escalation. Keyless signing with Sigstore depends on OIDC token exchange; short-lived identity outages look like Chains errors until identity service health returns. Webhook error percentages can climb when security scanners probe public routes; separate scanner noise from legitimate Git provider delivery failures using source IP allow lists or mutual TLS policy context.

Operational posture: align telemetry with change records by stamping change_ticket_id onto HTTP Event Collector payloads when maintenance touches Trigger objects, TektonConfig, or cluster resolvers. When Splunk shows healthy PipelineRuns but developers report missing runs, pivot to EventListener access logs before assuming Git vendor faults.

Differentiation recap: OpenShift Pipelines Tekton CI/CD plane reliability with explicit coverage of triggers, chains, and resolvers, not BuildConfig assemble failures, not ImageStream import health in isolation, not generic OLM subscription dashboards without Tekton CR context.

### Step 2 — Configure data collection

Stand up six complementary lanes Splunk multisearch can fuse: periodic PipelineRun snapshots or watches, TaskRun snapshots with step exit aggregation, EventListener access logs or proxy lines with path filters, Tekton Chains and resolver controller logs, optional Kubernetes Events involving PipelineRun and TaskRun objects, and optional Subscription or TektonConfig snapshots for operator reconcile context when you want first-class openshift-pipelines-operator health beside workload failures.

PipelineRun snapshot lane: schedule a Python or Go utility every two to five minutes from a management host with kubeconfig authentication. The utility should run oc get pipelinerun -A -o json on estates where policy permits cluster-wide reads, or iterate namespaces from an allow list. Iterate items[], flatten status.conditions for Succeeded with reason tokens such as TasksFailed, PipelineRunCancelled, PipelineRunStopping, CreateRunFailed, ResolutionFailed, FailedToResolveTaskRefs, and GitResolverFailed, flatten start and completion timestamps, flatten spec.timeouts when present, flatten workspace volume claims when you track persistent volume claim bind failures, and emit sourcetype=ocp_pipelinerun with cluster, namespace, pipeline_name, pr_name, condition_succeeded, reason, message, startTime_epoch, completionTime_epoch, duration_seconds, and optional annotation fields such as results summary hashes when policy permits.

TaskRun snapshot lane: on the same cadence run oc get taskrun -A -o json or watch tekton.dev TaskRun objects. Emit sourcetype=ocp_taskrun with cluster, namespace, taskrun_name, parent_pipeline_run labels, condition_succeeded, reason tokens such as TaskRunImagePullFailed, TaskRunValidationFailed, TaskRunResolutionFailed, TaskRunTimeout, TaskRunCancelled, TaskRunStopping, FailedToCreate, and InjectedSidecarsTerminating class messages when your minor surfaces them, plus nonzero_step_exit derived from the maximum non-zero step exit code when any step terminated with failure.

EventListener lane: forward HAProxy, OpenShift Router, or ingress controller access logs into sourcetype=ocp_tekton_el_access or sourcetype=access_combined with cluster, namespace, status, uri_path, bytes_in, bytes_out, and source IP when retention policy allows. Ensure EventListener liveness and readiness paths remain distinguishable from interceptor paths so error budgets separate health checks from user traffic. When you cannot access raw ingress, ship OpenTelemetry spans from the triggers webhook receiver when your service mesh exports HTTP server spans with route names.

Chains and resolver lane: collect openshift-pipelines or openshift-pipelines-resolvers namespace logs from tekton-chains-controller, pipelines-as-code controller if deployed, and resolver Deployments when your distribution separates them. Emit sourcetype=ocp_tekton_chains or sourcetype=kube:container with cluster, namespace, pod, container, and raw message lines suitable for the ResolutionFailed and GitResolverFailed token matches in search time. Avoid indexing private attestation payloads; keep boolean failure flags in structured fields when possible.

Operator lane: optional but valuable for paging discrimination. Export operators.coreos.com Subscription rows for openshift-pipelines-operator with status.currentCSV versus status.installedCSV mismatches, and export operator.tekton.dev TektonConfig readiness conditions plus TektonInstallerSet failure messages when your exporter surfaces them. Land these as sourcetype=ocp_subscription and sourcetype=ocp_tektonconfig in index=ocp_events so sibling UC-3.3.11 dashboards can drill down without duplicating ownership.

Lookup lane: maintain a Splunk lookup expected_pipelines.csv in the search app with columns pipeline_ref, owning_team, and slo_target_sec numeric seconds for ninety-fifth percentile duration budgets per pipeline. The saved search joins this lookup after aggregating PipelineRun latency so severity can breach when p95_dur exceeds slo_target_sec even if failure counts stay low.

PVC hygiene lane: when you track workspace pressure, emit periodic PersistentVolumeClaim listings for CI namespaces with phase Pending or events citing volume bind failures, tagged sourcetype=ocp_pvc_snapshot, so analysts correlate TaskRunValidationFailed messages with storage backlog without waiting for node-level dashboards.

Pre-flight searches operators should run before saving alerts:

index=ocp_events sourcetype=ocp_pipelinerun earliest=-1h latest=now | head 20
index=ocp_events sourcetype=ocp_taskrun earliest=-24h latest=now | head 20
index=ocp_events sourcetype=ocp_tekton_el_access earliest=-24h latest=now | head 20
index=ocp_events sourcetype=ocp_tekton_chains earliest=-24h latest=now | head 20
| inputlookup expected_pipelines.csv | head 20

Zero-result investigations should block production paging until collectors succeed.

props.conf guidance: TRUNCATE sufficiently large for JSON, TIMESTAMP_FIELDS respected when HTTP Event Collector time is authoritative, LINE_BREAKER rules for NDJSON watch streams, FIELDALIAS maps from labels.tekton.dev/pipeline to labels_tekton_dev_pipeline when KV flatteners differ.

Dashboards: Splunk OpenShift App panels should host a matrix by cluster and namespace with color thresholds from severity, drilldowns to raw JSON for each sourcetype, access lines, controller logs, and lookup rows.

### Step 3 — Create the search and alert

Save the SPL as openshift_uc_3_3_3_tekton_pipelines_reliability with a fifteen minute schedule, dispatch earliest=-24h@h, dispatch latest=now, and alert when severity is page or warn. Throttle duplicate cluster, namespace, pipeline_key rows for thirty minutes unless severity escalates from warn to page. Include recommended_action, pr_reason, webhook_err_pct, and chains_miss in pager descriptions so incident commanders open the correct runbook section without rerunning ad hoc searches.

Pipeline narrative for operators: multisearch fans PipelineRun aggregates, TaskRun failure aggregates, EventListener access error summaries, and Chains plus resolver log aggregates so a silent single sourcetype outage does not hide genuine trigger delivery failure. coalesce() absorbs field naming drift between alternate exporters. streamstats ordered by pipeline_key flags short failure streaks that precede full outages. eventstats copies namespace-level webhook error denominators onto each pipeline row for ratio math. case() maps resolver and Git failures, image pull failures, signing gaps, webhook error percentages against low PipelineRun creation hints, and service level breaches into page versus warn versus info tiers. The join wraps inputlookup expected_pipelines.csv to attach owning_team and slo_target_sec for accountable routing.

Fenced SPL must match the spl JSON field exactly:

```spl
`comment("UC-3.3.3 OpenShift Pipelines Tekton reliability — PipelineRun TaskRun EventListener Chains resolvers. Tunables: earliest=-24h@h latest=now webhook_err_warn_pct=8 webhook_err_page_pct=15")`
| multisearch
    [ search index=ocp_events sourcetype="ocp_pipelinerun" earliest=-24h@h latest=now
      | eval cluster=lower(trim(toString(coalesce(cluster, openshift_cluster, cluster_name, cluster_id, ""))))
      | eval namespace=lower(trim(toString(coalesce(namespace, k8s_namespace, metadata_namespace, ""))))
      | eval pipeline_key=lower(trim(toString(coalesce(pipeline_name, labels_tekton_dev_pipeline, spec_pipelineRef_name, metadata_name, ""))))
      | eval pr_succ=lower(trim(toString(coalesce(condition_succeeded, succeeded, status_succeeded, ""))))
      | eval pr_reason=trim(toString(coalesce(reason, failure_reason, status_reason, "")))
      | eval start_e=tonumber(tostring(coalesce(startTime_epoch, start_epoch, "")),10)
      | eval end_e=tonumber(tostring(coalesce(completionTime_epoch, completion_epoch, "")),10)
      | eval duration_sec=if(isnotnull(start_e) AND isnotnull(end_e) AND end_e>start_e, end_e-start_e, tonumber(tostring(coalesce(duration_seconds, dur_sec, "")),10))
      | eval pr_fail=if(match(pr_succ,"false|0") OR match(lower(pr_reason),"tasksfailed|pipelineruncancelled|pipelinerunstopping|createrunfailed|resolutionfailed|failedtoresolvetaskrefs|gitresolverfailed|pipelinecanceled"),1,0)
      | eval lane="pr_lane"
      | stats count AS pr_obs sum(pr_fail) AS pr_fail_cnt latest(pr_reason) AS pr_reason perc50(duration_sec) AS p50_dur perc95(duration_sec) AS p95_dur latest(_time) AS snap_time BY cluster namespace pipeline_key lane ]
    [ search index=ocp_events sourcetype="ocp_taskrun" earliest=-24h@h latest=now
      | eval cluster=lower(trim(toString(coalesce(cluster, openshift_cluster, cluster_name, cluster_id, ""))))
      | eval namespace=lower(trim(toString(coalesce(namespace, k8s_namespace, metadata_namespace, ""))))
      | eval pipeline_key=lower(trim(toString(coalesce(labels_tekton_dev_pipelineRun, parent_pipeline_run, pipeline_run_ref, ""))))
      | eval tr_succ=lower(trim(toString(coalesce(condition_succeeded, succeeded, ""))))
      | eval tr_reason=trim(toString(coalesce(reason, failure_reason, "")))
      | eval step_exit=tonumber(tostring(coalesce(nonzero_step_exit, max_exit_code, "")),10)
      | eval tr_fail=if(match(tr_succ,"false|0") OR match(lower(tr_reason),"taskrunimagepullfailed|taskrunvalidationfailed|taskrunresolutionfailed|taskruntimeout|taskruncancelled|taskrunstopping|failedtocreate|injectedsidcarsterminating|injectedsidecarsterminating"),1,if(step_exit>0,1,0))
      | eval lane="tr_lane"
      | stats sum(tr_fail) AS tr_fail_cnt latest(tr_reason) AS tr_reason max(step_exit) AS worst_step_exit latest(_time) AS snap_time BY cluster namespace pipeline_key lane ]
    [ search index=ocp_events (sourcetype="ocp_tekton_el_access" OR sourcetype="ocp_haproxy" OR sourcetype="access_combined") earliest=-24h@h latest=now
      | eval cluster=lower(trim(toString(coalesce(cluster, openshift_cluster, cluster_name, cluster_id, ""))))
      | eval namespace=lower(trim(toString(coalesce(namespace, k8s_namespace, el_namespace, ""))))
      | eval sc=tonumber(tostring(coalesce(status, http_status, response_code, "")),10)
      | eval path_l=lower(toString(coalesce(uri, uri_path, request_uri, "")))
      | eval is_el=if(match(path_l,"eventlistener|tekton/triggers|/live|/ready|/intercept"),1,0)
      | eval wh_err=if(is_el==1 AND isnotnull(sc) AND sc>=400,1,0)
      | eval pr_create=if(match(lower(_raw),"pipelinerun") AND match(lower(_raw),"create"),1,0)
      | eval lane="el_lane"
      | eval pipeline_key="_webhook_plane_"
      | stats count AS el_req sum(wh_err) AS wh_sum sum(pr_create) AS pr_create_hint latest(_time) AS snap_time BY cluster namespace pipeline_key lane ]
    [ search index=ocp_events (sourcetype="ocp_tekton_chains" OR sourcetype="kube:container" OR sourcetype="ocp_events") earliest=-24h@h latest=now
      | eval cluster=lower(trim(toString(coalesce(cluster, openshift_cluster, cluster_name, cluster_id, ""))))
      | eval namespace=lower(trim(toString(coalesce(namespace, k8s_namespace, ""))))
      | eval rl=lower(_raw)
      | eval chains_miss=if((match(rl,"tekton chains") OR match(rl,"chains-controller")) AND match(rl,"signed|cosign|rekor|attestation|upload|failed|unsigned"),1,0)
      | eval resv_fail=if(match(rl,"resolutionfailed|failedtoresolvetaskrefs|clusterresolver|gitresolverfailed|could not clone|bundle.*pull|manifest unknown|unauthorized"),1,0)
      | eval lane="cr_lane"
      | eval pipeline_key="_chains_resolver_"
      | stats sum(chains_miss) AS chains_miss sum(resv_fail) AS resv_fail count AS cr_obs latest(_time) AS snap_time BY cluster namespace pipeline_key lane ]
| stats
    sum(eval(if(lane=="pr_lane",pr_obs,0))) AS pr_obs
    sum(eval(if(lane=="pr_lane",pr_fail_cnt,0))) AS pr_fail_cnt
    first(eval(if(lane=="pr_lane",pr_reason,null()))) AS pr_reason
    max(eval(if(lane=="pr_lane",p50_dur,null()))) AS p50_dur
    max(eval(if(lane=="pr_lane",p95_dur,null()))) AS p95_dur
    sum(eval(if(lane=="tr_lane",tr_fail_cnt,0))) AS tr_fail_cnt
    first(eval(if(lane=="tr_lane",tr_reason,null()))) AS tr_reason
    max(eval(if(lane=="tr_lane",worst_step_exit,null()))) AS worst_step_exit
    max(eval(if(lane=="el_lane",el_req,null()))) AS el_req
    max(eval(if(lane=="el_lane",wh_sum,null()))) AS wh_sum
    max(eval(if(lane=="el_lane",pr_create_hint,null()))) AS pr_create_hint
    max(eval(if(lane=="cr_lane",chains_miss,null()))) AS chains_miss
    max(eval(if(lane=="cr_lane",resv_fail,null()))) AS resv_fail
    max(eval(if(lane=="cr_lane",cr_obs,null()))) AS cr_obs
    max(snap_time) AS last_seen
  BY cluster namespace pipeline_key
| join type=left max=0 pipeline_key
    [ | inputlookup expected_pipelines.csv
      | eval pipeline_key=lower(trim(toString(coalesce(pipeline_ref, pipeline_name, pipeline_key, ""))))
      | fields pipeline_key owning_team slo_target_sec ]
| streamstats window=20000 current=t global=f last(pr_fail_cnt) AS prev_pr_fail BY cluster namespace pipeline_key
| eval pr_fail_streak=if(pr_fail_cnt>0 AND prev_pr_fail>0,1,pr_fail_cnt)
| eventstats perc95(p95_dur) AS fleet_pr_p95 sum(eval(if(pipeline_key=="_webhook_plane_",wh_sum,null()))) AS ns_wh sum(eval(if(pipeline_key=="_webhook_plane_",el_req,null()))) AS ns_elreq sum(eval(if(pipeline_key=="_webhook_plane_",pr_create_hint,null()))) AS ns_prhint BY cluster namespace
| eval webhook_err_pct=if(isnotnull(ns_elreq) AND ns_elreq>0, round(100.0*coalesce(ns_wh,0)/ns_elreq,2), null())
| eval slo_tgt=tonumber(tostring(slo_target_sec),10)
| eval slo_breach=if(isnotnull(slo_tgt) AND slo_tgt>0 AND isnotnull(p95_dur) AND p95_dur>slo_tgt,1,0)
| eval severity=case(
    coalesce(pr_fail_cnt,0)>=5 AND match(lower(pr_reason),"resolutionfailed|gitresolverfailed|createrunfailed"), "page",
    coalesce(tr_fail_cnt,0)>=10 AND match(lower(tr_reason),"taskrunimagepullfailed|failedtocreate"), "page",
    coalesce(chains_miss,0)>=5 OR coalesce(resv_fail,0)>=8, "page",
    isnotnull(webhook_err_pct) AND webhook_err_pct>=15 AND coalesce(ns_prhint,0)<2, "page",
    coalesce(pr_fail_cnt,0)>=2 OR pr_fail_streak>=2, "warn",
    isnotnull(webhook_err_pct) AND webhook_err_pct>=8, "warn",
    slo_breach==1, "warn",
    coalesce(worst_step_exit,0)>0 AND coalesce(tr_fail_cnt,0)>=4, "warn",
    true(), "info")
| eval recommended_action=case(
    match(lower(pr_reason),"gitresolverfailed|resolutionfailed"), "repair_git_resolver_auth_and_bundle_refs",
    match(lower(tr_reason),"taskrunimagepullfailed"), "fix_pull_secrets_image_policy_and_mirrors",
    coalesce(chains_miss,0)>=1, "tekton_chains_cosign_oidc_rekor_and_secret_sync",
    coalesce(resv_fail,0)>=3, "validate_hub_cluster_bundle_resolvers_and_rbac",
    isnotnull(webhook_err_pct) AND webhook_err_pct>=8, "tekton_triggers_interceptors_el_routes_and_tokens",
    true(), "oc_describe_pipelinerun_taskrun_and_controller_logs")
| table cluster namespace pipeline_key pr_obs pr_fail_cnt pr_reason p50_dur p95_dur fleet_pr_p95 tr_fail_cnt tr_reason worst_step_exit webhook_err_pct ns_prhint chains_miss resv_fail owning_team slo_target_sec slo_breach severity recommended_action last_seen
```

savedsearches.conf sketch:

```ini
[openshift_uc_3_3_3_tekton_pipelines_reliability_alert]
cron_schedule = */15 * * * *
dispatch.earliest_time = -24h@h
dispatch.latest_time = now
enableSched = 1
action.email = 1
action.email.to = openshift-platform@example.com
action.email.subject = OCP Tekton Pipelines $result.severity$ $result.cluster$ $result.namespace$ $result.pipeline_key$
counttype = number of events
relation = greater than
quantity = 0
search = | savedsearch openshift_uc_3_3_3_tekton_pipelines_reliability | where severity IN ("page","warn")
```

Performance: if Job Inspector shows multisearch queue time above internal service levels, materialize hourly ocp_pipelinerun summaries keyed on cluster, namespace, and pipeline_name into a summary index, widen alert searches to earliest=-6h@h on the summary, and retain this full search for investigations.

### Step 4 — Validate

Ground truth always starts on-cluster. Run oc get pipelinerun -n target-namespace, oc describe pipelinerun name -n target-namespace, and oc get taskrun -n target-namespace, then compare condition reasons and completion timestamps to Splunk rows for the same cluster inside the last snapshot window. When statuses disagree, verify resourceVersion freshness, indexer clock skew, and duplicate cluster labels across regions before blaming parsers.

Deep dive with kubectl or oc get yaml for PipelineRun spec.timeouts and workspace stanzas, confirming exporter flattening matches live objects when you alert on timeout breaches inferred from reason tokens.

EventListener truth: oc get route -n namespace or oc get eventlistener -n namespace should mirror the hostnames and Services you see in access logs. Compare HTTP status histograms from Splunk to short curl probes against /live endpoints during maintenance windows.

Chains truth: inspect TaskRun annotations for chains.tekton.dev/signed after successful tasks when policy expects signing. When annotations remain absent while tasks succeeded, confirm Tekton Chains configuration for artifacts storage and verify OIDC secret bindings for keyless flows.

Resolver truth: reproduce cluster resolver lookups with oc get tasks -n tekton-pipelines when using bundled cluster references, and validate git resolver credentials against private repository access from resolver pods.

Synthetic validation: in a lab namespace, introduce a deliberate bad git revision or unreachable bundle reference under change control, ingest telemetry, and confirm openshift_uc_3_3_3_tekton_pipelines_reliability surfaces warn or page with repair_git_resolver_auth_and_bundle_refs or validate_hub_cluster_bundle_resolvers_and_rbac recommended_action text. Restore a healthy reference, watch PipelineRun reach Succeeded, and confirm severity returns to info.

Negative test: on a cluster where pipelines succeed, webhooks return two hundred responses, and Chains annotations appear when enabled, confirm the alert wrapper returns zero rows for page and warn filters after maintenance windows settle.

Lookup validation: ensure expected_pipelines.csv includes every production pipeline_ref you page on, with realistic slo_target_sec values derived from historical p95_dur, and verify the join keys are lower-case trimmed strings.

### Step 5 — Operationalize & Troubleshoot

Case 1 — PipelineRun reason ResolutionFailed across many namespaces: trigger when pr_reason matches resolver tokens and pr_fail_cnt rises across pipelines in one cluster. Investigate openshift-pipelines-resolvers logs, hub and bundle credentials, and cluster role bindings for remote resolution. Involve the platform engineering lead for OpenShift Pipelines and the CI owner for affected repositories. Remediate by fixing bundle pull secrets, restoring catalog connectivity, or pinning task references to known digests. Validate by rerunning a canary PipelineRun and confirming Succeeded=True within expected duration.

Case 2 — GitResolverFailed with private repository errors: trigger when pr_reason or controller logs cite GitResolverFailed or clone failures. Investigate git-credential secrets, network egress, and deep clone timeouts against large monorepos. Involve the developer platform team and network engineering when corporate proxies change. Remediate by rotating credentials, widening resolver timeouts under vendor guidance, or switching to bundle references for stable digests. Validate by executing a trimmed fetch PipelineRun and confirming resolver logs show clean clone completion.

Case 3 — TaskRunImagePullFailed concentrated on builder images: trigger when tr_reason matches image pull tokens and worst_step_exit is non-zero. Investigate image pull secrets on the TaskRun ServiceAccount, cluster image policy, and registry mirrors. Involve the container registry team when UC-3.3.13 import health is green but runtime pulls still fail. Remediate by attaching pull secrets, relaxing policy exceptions under security review, or retagging known-good builder digests. Validate by rerunning the TaskRun and confirming kubelet events clear.

Case 4 — InjectedSidecarsTerminating or sidecar stuck narratives: trigger when tr_reason or messages reference sidecar termination stalls. Investigate pod logs for injected sidecars, node pressure, and cgroup teardown delays. Involve Kubernetes platform site reliability engineers when nodes show repeated teardown latency. Remediate by upgrading Tekton Pipelines patch releases per Red Hat guidance, tuning step timeouts, or draining noisy nodes after cordon. Validate by repeating the pipeline and confirming step completion without manual pod deletion.

Case 5 — EventListener webhook_err_pct high with low pr_create_hint: trigger when access logs show four hundred or five hundred responses on interceptor paths while PipelineRun creation hints stay flat. Investigate TriggerBinding parameter mismatches, CEL interceptor exceptions, and GitHub or GitLab secret tokens for missing-secret errors. Involve the application CI team that owns the Repository CR or webhook configuration. Remediate by fixing interceptor expressions, restoring secrets, or correcting route TLS. Validate by sending a test webhook payload and confirming a PipelineRun appears within seconds.

Case 6 — Tekton Chains signing gaps after successful tasks: trigger when chains_miss counts climb and tasks completed without chains.tekton.dev/signed annotations. Investigate tekton-chains-controller configuration, Sigstore endpoints, Rekor reachability, and workload identity tokens. Involve security engineering for supply-chain policy and identity platform owners for OIDC. Remediate by repairing cosign keyless configuration, fixing Rekor upload paths, or rotating signing secrets when not keyless. Validate by running an attested pipeline and confirming provenance artifacts land in the configured storage.

Case 7 — PVC workspace bind failures implied by TaskRunValidationFailed: trigger when messages cite missing volumes or unbound claims. Investigate PersistentVolumeClaims referenced by PipelineRuns, storage classes, and namespace quotas. Involve storage platform teams when bind delays cluster-wide. Remediate by fixing storage class defaults, expanding quotas, or cleaning orphaned claims from prior runs. Validate by creating a test PipelineRun using the same workspace and confirming the claim reaches Bound.

Case 8 — PipelineRun timeout breaches on spec.timeouts fields: trigger when reasons reference timeout semantics or durations exceed slo_target_sec without terminal failure reasons yet. Investigate heavy integration test suites, resource starvation, and step retries. Involve service owners for the pipeline definition. Remediate by splitting pipelines, raising timeouts under change control, or scaling build nodes. Validate by comparing p50_dur and p95_dur trends before and after the change.

Case 9 — openshift-pipelines-operator subscription drift: trigger when sibling subscription snapshots show currentCSV not matching installedCSV for long dwell. Investigate InstallPlan status, catalog health, and ClusterServiceVersion messages. Involve the operator lifecycle team per UC-3.3.11 runbooks. Remediate by approving installs, fixing catalog mirrors, or rolling back a bad channel pin. Validate by confirming the operator reports AtLatestKnown and TektonConfig Ready=True.

Case 10 — Namespace PVC pressure from pruner backlog: trigger when many Terminal PipelineRuns retain claims and cleanup jobs lag. Investigate Tekton pruner CronJobs or custom garbage collection controllers. Involve platform automation owners. Remediate by scheduling prunes, tightening retention labels, or expanding storage. Validate by observing claim counts fall and PipelineRun scheduling return to normal.

Case 11 — Fleet-wide info severities only: trigger on scheduled governance cadence rather than paging. Investigate drift between Splunk fields and oc get outputs quarterly. Involve observability engineers. Remediate by updating FIELDALIAS maps and exporter versions. Validate by rerunning pre-flight searches and confirming sample parity across regions.

## SPL

```spl
`comment("UC-3.3.3 OpenShift Pipelines Tekton reliability — PipelineRun TaskRun EventListener Chains resolvers. Tunables: earliest=-24h@h latest=now webhook_err_warn_pct=8 webhook_err_page_pct=15")`
| multisearch
    [ search index=ocp_events sourcetype="ocp_pipelinerun" earliest=-24h@h latest=now
      | eval cluster=lower(trim(toString(coalesce(cluster, openshift_cluster, cluster_name, cluster_id, ""))))
      | eval namespace=lower(trim(toString(coalesce(namespace, k8s_namespace, metadata_namespace, ""))))
      | eval pipeline_key=lower(trim(toString(coalesce(pipeline_name, labels_tekton_dev_pipeline, spec_pipelineRef_name, metadata_name, ""))))
      | eval pr_succ=lower(trim(toString(coalesce(condition_succeeded, succeeded, status_succeeded, ""))))
      | eval pr_reason=trim(toString(coalesce(reason, failure_reason, status_reason, "")))
      | eval start_e=tonumber(tostring(coalesce(startTime_epoch, start_epoch, "")),10)
      | eval end_e=tonumber(tostring(coalesce(completionTime_epoch, completion_epoch, "")),10)
      | eval duration_sec=if(isnotnull(start_e) AND isnotnull(end_e) AND end_e>start_e, end_e-start_e, tonumber(tostring(coalesce(duration_seconds, dur_sec, "")),10))
      | eval pr_fail=if(match(pr_succ,"false|0") OR match(lower(pr_reason),"tasksfailed|pipelineruncancelled|pipelinerunstopping|createrunfailed|resolutionfailed|failedtoresolvetaskrefs|gitresolverfailed|pipelinecanceled"),1,0)
      | eval lane="pr_lane"
      | stats count AS pr_obs sum(pr_fail) AS pr_fail_cnt latest(pr_reason) AS pr_reason perc50(duration_sec) AS p50_dur perc95(duration_sec) AS p95_dur latest(_time) AS snap_time BY cluster namespace pipeline_key lane ]
    [ search index=ocp_events sourcetype="ocp_taskrun" earliest=-24h@h latest=now
      | eval cluster=lower(trim(toString(coalesce(cluster, openshift_cluster, cluster_name, cluster_id, ""))))
      | eval namespace=lower(trim(toString(coalesce(namespace, k8s_namespace, metadata_namespace, ""))))
      | eval pipeline_key=lower(trim(toString(coalesce(labels_tekton_dev_pipelineRun, parent_pipeline_run, pipeline_run_ref, ""))))
      | eval tr_succ=lower(trim(toString(coalesce(condition_succeeded, succeeded, ""))))
      | eval tr_reason=trim(toString(coalesce(reason, failure_reason, "")))
      | eval step_exit=tonumber(tostring(coalesce(nonzero_step_exit, max_exit_code, "")),10)
      | eval tr_fail=if(match(tr_succ,"false|0") OR match(lower(tr_reason),"taskrunimagepullfailed|taskrunvalidationfailed|taskrunresolutionfailed|taskruntimeout|taskruncancelled|taskrunstopping|failedtocreate|injectedsidcarsterminating|injectedsidecarsterminating"),1,if(step_exit>0,1,0))
      | eval lane="tr_lane"
      | stats sum(tr_fail) AS tr_fail_cnt latest(tr_reason) AS tr_reason max(step_exit) AS worst_step_exit latest(_time) AS snap_time BY cluster namespace pipeline_key lane ]
    [ search index=ocp_events (sourcetype="ocp_tekton_el_access" OR sourcetype="ocp_haproxy" OR sourcetype="access_combined") earliest=-24h@h latest=now
      | eval cluster=lower(trim(toString(coalesce(cluster, openshift_cluster, cluster_name, cluster_id, ""))))
      | eval namespace=lower(trim(toString(coalesce(namespace, k8s_namespace, el_namespace, ""))))
      | eval sc=tonumber(tostring(coalesce(status, http_status, response_code, "")),10)
      | eval path_l=lower(toString(coalesce(uri, uri_path, request_uri, "")))
      | eval is_el=if(match(path_l,"eventlistener|tekton/triggers|/live|/ready|/intercept"),1,0)
      | eval wh_err=if(is_el==1 AND isnotnull(sc) AND sc>=400,1,0)
      | eval pr_create=if(match(lower(_raw),"pipelinerun") AND match(lower(_raw),"create"),1,0)
      | eval lane="el_lane"
      | eval pipeline_key="_webhook_plane_"
      | stats count AS el_req sum(wh_err) AS wh_sum sum(pr_create) AS pr_create_hint latest(_time) AS snap_time BY cluster namespace pipeline_key lane ]
    [ search index=ocp_events (sourcetype="ocp_tekton_chains" OR sourcetype="kube:container" OR sourcetype="ocp_events") earliest=-24h@h latest=now
      | eval cluster=lower(trim(toString(coalesce(cluster, openshift_cluster, cluster_name, cluster_id, ""))))
      | eval namespace=lower(trim(toString(coalesce(namespace, k8s_namespace, ""))))
      | eval rl=lower(_raw)
      | eval chains_miss=if((match(rl,"tekton chains") OR match(rl,"chains-controller")) AND match(rl,"signed|cosign|rekor|attestation|upload|failed|unsigned"),1,0)
      | eval resv_fail=if(match(rl,"resolutionfailed|failedtoresolvetaskrefs|clusterresolver|gitresolverfailed|could not clone|bundle.*pull|manifest unknown|unauthorized"),1,0)
      | eval lane="cr_lane"
      | eval pipeline_key="_chains_resolver_"
      | stats sum(chains_miss) AS chains_miss sum(resv_fail) AS resv_fail count AS cr_obs latest(_time) AS snap_time BY cluster namespace pipeline_key lane ]
| stats
    sum(eval(if(lane=="pr_lane",pr_obs,0))) AS pr_obs
    sum(eval(if(lane=="pr_lane",pr_fail_cnt,0))) AS pr_fail_cnt
    first(eval(if(lane=="pr_lane",pr_reason,null()))) AS pr_reason
    max(eval(if(lane=="pr_lane",p50_dur,null()))) AS p50_dur
    max(eval(if(lane=="pr_lane",p95_dur,null()))) AS p95_dur
    sum(eval(if(lane=="tr_lane",tr_fail_cnt,0))) AS tr_fail_cnt
    first(eval(if(lane=="tr_lane",tr_reason,null()))) AS tr_reason
    max(eval(if(lane=="tr_lane",worst_step_exit,null()))) AS worst_step_exit
    max(eval(if(lane=="el_lane",el_req,null()))) AS el_req
    max(eval(if(lane=="el_lane",wh_sum,null()))) AS wh_sum
    max(eval(if(lane=="el_lane",pr_create_hint,null()))) AS pr_create_hint
    max(eval(if(lane=="cr_lane",chains_miss,null()))) AS chains_miss
    max(eval(if(lane=="cr_lane",resv_fail,null()))) AS resv_fail
    max(eval(if(lane=="cr_lane",cr_obs,null()))) AS cr_obs
    max(snap_time) AS last_seen
  BY cluster namespace pipeline_key
| join type=left max=0 pipeline_key
    [ | inputlookup expected_pipelines.csv
      | eval pipeline_key=lower(trim(toString(coalesce(pipeline_ref, pipeline_name, pipeline_key, ""))))
      | fields pipeline_key owning_team slo_target_sec ]
| streamstats window=20000 current=t global=f last(pr_fail_cnt) AS prev_pr_fail BY cluster namespace pipeline_key
| eval pr_fail_streak=if(pr_fail_cnt>0 AND prev_pr_fail>0,1,pr_fail_cnt)
| eventstats perc95(p95_dur) AS fleet_pr_p95 sum(eval(if(pipeline_key=="_webhook_plane_",wh_sum,null()))) AS ns_wh sum(eval(if(pipeline_key=="_webhook_plane_",el_req,null()))) AS ns_elreq sum(eval(if(pipeline_key=="_webhook_plane_",pr_create_hint,null()))) AS ns_prhint BY cluster namespace
| eval webhook_err_pct=if(isnotnull(ns_elreq) AND ns_elreq>0, round(100.0*coalesce(ns_wh,0)/ns_elreq,2), null())
| eval slo_tgt=tonumber(tostring(slo_target_sec),10)
| eval slo_breach=if(isnotnull(slo_tgt) AND slo_tgt>0 AND isnotnull(p95_dur) AND p95_dur>slo_tgt,1,0)
| eval severity=case(
    coalesce(pr_fail_cnt,0)>=5 AND match(lower(pr_reason),"resolutionfailed|gitresolverfailed|createrunfailed"), "page",
    coalesce(tr_fail_cnt,0)>=10 AND match(lower(tr_reason),"taskrunimagepullfailed|failedtocreate"), "page",
    coalesce(chains_miss,0)>=5 OR coalesce(resv_fail,0)>=8, "page",
    isnotnull(webhook_err_pct) AND webhook_err_pct>=15 AND coalesce(ns_prhint,0)<2, "page",
    coalesce(pr_fail_cnt,0)>=2 OR pr_fail_streak>=2, "warn",
    isnotnull(webhook_err_pct) AND webhook_err_pct>=8, "warn",
    slo_breach==1, "warn",
    coalesce(worst_step_exit,0)>0 AND coalesce(tr_fail_cnt,0)>=4, "warn",
    true(), "info")
| eval recommended_action=case(
    match(lower(pr_reason),"gitresolverfailed|resolutionfailed"), "repair_git_resolver_auth_and_bundle_refs",
    match(lower(tr_reason),"taskrunimagepullfailed"), "fix_pull_secrets_image_policy_and_mirrors",
    coalesce(chains_miss,0)>=1, "tekton_chains_cosign_oidc_rekor_and_secret_sync",
    coalesce(resv_fail,0)>=3, "validate_hub_cluster_bundle_resolvers_and_rbac",
    isnotnull(webhook_err_pct) AND webhook_err_pct>=8, "tekton_triggers_interceptors_el_routes_and_tokens",
    true(), "oc_describe_pipelinerun_taskrun_and_controller_logs")
| table cluster namespace pipeline_key pr_obs pr_fail_cnt pr_reason p50_dur p95_dur fleet_pr_p95 tr_fail_cnt tr_reason worst_step_exit webhook_err_pct ns_prhint chains_miss resv_fail owning_team slo_target_sec slo_breach severity recommended_action last_seen
```

## CIM SPL

```spl
| tstats summariesonly=t latest(Change.action) AS change_action latest(Change.object) AS change_object latest(Change.user) AS change_user FROM datamodel=Change WHERE nodename=Change earliest=-24h@h latest=now BY Change.dest
| rename Change.dest AS cim_dest
| join type=left max=0 cim_dest
    [| tstats summariesonly=t latest(Application_State.state) AS app_state latest(Application_State.info) AS app_info FROM datamodel=Application_State WHERE nodename=Application_State earliest=-24h@h latest=now BY Application_State.dest
     | rename Application_State.dest AS cim_dest ]
| where like(lower(change_object), "%pipelinerun%") OR like(lower(change_object), "%taskrun%") OR like(lower(app_info), "%tekton%pipeline%")
| table cim_dest change_action change_object change_user app_state app_info
```

## Visualization

Severity-colored table by cluster namespace pipeline_key with drilldowns to ocp_pipelinerun JSON, ocp_taskrun JSON, access logs, chains controller lines, and k8s_events; timeline of p50_dur versus p95_dur; single-value tiles for webhook_err_pct and chains_miss.

## Known False Positives

Canary PipelineRun cancellations during controlled rollouts resemble incidents until reason equals PipelineRunCancelled and change metadata confirms intent. Vendor maintenance on Git providers can spike GitResolverFailed rows that self-resolve when mirrors catch up; require consecutive windows before paging executives. Security scanners that hammer public EventListener routes inflate webhook_err_pct without blocking real Git deliveries; segment traffic using authenticated routes or allow lists when policy permits. Long-running integration pipelines legitimately approach timeout thresholds during quarter-end batch windows; pair slo_target_sec with calendar metadata. Disconnected clusters may pause Chains uploads while still building images; distinguish air-gap policy from misconfiguration using identity and Rekor reachability checks. Lab namespaces that continuously break builds for testing will page unless routed to non-production indexes. Duplicate HTTP Event Collector submissions from redundant exporters can double pr_obs counts until dedupe logic lands in summary indexes. Prometheus scrape gaps from user-workload monitoring outages can hide controller signals even while API snapshots remain healthy; repair federation before muting the analytic entirely. Resolver metric renames between OpenShift Pipelines patch releases can alter field extraction until props updates ship; validate extractor tests quarterly.

## References

- [OpenShift Pipelines — Understanding OpenShift Pipelines](https://docs.openshift.com/pipelines/latest/about/understanding-openshift-pipelines.html)
- [Red Hat Documentation — About OpenShift Pipelines](https://docs.redhat.com/en/documentation/red_hat_openshift_pipelines/1.14/html/about_openshift_pipelines/index)
- [Tekton Pipelines — PipelineRuns](https://tekton.dev/docs/pipelines/pipelineruns/)
- [Tekton Triggers — EventListeners](https://tekton.dev/docs/triggers/eventlisteners/)
- [tektoncd/pipeline — PipelineRun documentation](https://github.com/tektoncd/pipeline/blob/main/docs/pipelineruns.md)
- [tektoncd/triggers — EventListener documentation](https://github.com/tektoncd/triggers/blob/main/docs/eventlisteners.md)
- [tektoncd/chains — Tekton Chains documentation](https://github.com/tektoncd/chains/blob/main/docs/README.md)
- [Red Hat Blog — Introducing the Operator Framework](https://www.redhat.com/en/blog/introducing-operator-framework-building-apps-kubernetes)
